#!/bin/sh
# \
exec oagtclsh "$0" "$@"

# Script processJob1
# Purpose: post-process jobs for genetic optimization of dynamic aperture and Touschek lifetime
# M. Borland, ANL, 6/2010

set auto_path [linsert $auto_path 0  $env(OAG_TOP_DIR)/oag/apps/lib/$env(HOST_ARCH)]
APSStandardSetup

set usage {usage: computeLifetime -rootname <string> -deltaLimit <relative> -current <mA> -bunches <number> -coupling <relative> -sigmas <mm> -sectors <number>}

set rootname ""
set deltaLimit 6e-2
set coupling .01
set current 500.0
set bunches 864
set sigmas 3.5
set sectors 10
set args $argv
if {[APSStrictParseArguments {rootname deltaLimit current bunches coupling sigmas sectors}] || \
    ![string length $rootname] } {
    return -code error "$usage"
}

proc calcLifetime {args} {

    set usage {usage: calcLifetime -rootname <string> [-current <mA>(100)] [-bunches <number>(24)] [-coupling <value>(0.01) [-sigmas <mm>(3.5) [-deltaLimit <%>(2.35)}
    set rootname ""
    set coupling .01
    set current 500.0
    set bunches 864
    set sigmas 3.5
    set sectors 10
    set deltaLimit 6.0e-2
    if {[APSStrictParseArguments {rootname current bunches coupling sigmas sectors deltaLimit}] || ![string length $rootname]} {
        return -code error "$usage"
    }

    if ![file exists ${rootname}.mmap] {
        puts stderr "not found: ${rootname}.mmap"
    }
    if ![file exists ${rootname}.twi] {
        puts stderr "not found: ${rootname}.twi"
    }

    # Figure out how many sectors are covered by the LMA data
    set circumference 518.396
    set lsector [expr (1.0*$circumference)/$sectors]

    # Compute bunch length using experimental curve for length (in mm) vs current (in mA) for APS
    set bunchCurrent [expr $current/(1.0*$bunches)]
    set charge [expr $bunchCurrent*($circumference/2.9979e8)*1e6]

    exec sddssplit ${rootname}.mmap -extension=mmap1
    exec sddssplit ${rootname}.twi -extension=twi
    set nsteps [eval exec ls [glob *.mmap1] | wc -l]
    set nomes []
    for {set ii 1} {$ii <= $nsteps} {incr ii} {
        set i [format "%03d" $ii]

        set ex0 [exec sdds2stream -parameter=ex0 ${rootname}$i.twi]
        set Sdelta0 [exec sdds2stream -parameter=Sdelta0 ${rootname}$i.twi]

        # para evitar loops infinitos do touschekLifetime quando a máquina for instável
        exec sddsprocess ${rootname}$i.mmap1 -pipe=out "-redefine=col,deltaPositive,deltaPositive 0.001 < ? 0.001 : deltaPositive $ ,units=m" \
           | sddsprocess -pipe=in ${rootname}$i.mmap1  "-redefine=col,deltaNegative,deltaNegative -0.001 > ? -0.001 : deltaNegative $ ,units=m"
        #
        exec sddssort ${rootname}$i.mmap1 -pipe=out -column=s,decreasing \
        | sddsprocess -pipe=in ${rootname}$i.mmap2 "-redefine=col,s,$lsector s -"
        exec sddscombine ${rootname}$i.mmap1 ${rootname}$i.mmap2 ${rootname}$i.mmap -merge

        set sMax [exec sddsprocess ${rootname}$i.mmap -pipe=out -process=s,max,sMax | sdds2stream -pipe -page=1 -parameter=sMax]
        set msectors [expr int($sMax/$lsector+0.5)]
        set number [expr int((1.0*$sectors)/$msectors+0.5)]

        eval exec sddscombine [APSReplicateItem -item ${rootname}$i.mmap -number $number] -pipe=out \
        | sddsprocess -pipe "{-redefine=col,s,s i_page 1 - $sMax $sectors / * $msectors * +,units=m}" \
        | sddscombine -pipe -merge \
        | sddsprocess -pipe=in ${rootname}$i.mmapxt -filter=col,s,0,$sMax
        # $rootname.mmapxt now contains the LMA for the full ring, created by replicating the data for $msectors sectors
        # a sufficient number of times
        set mmapFile ${rootname}$i.mmapxt
        set extension "mmapxt"

        exec touschekLifetime ${rootname}$i.ltime -twiss=${rootname}$i.twi \
              -aperture=${rootname}$i.$extension \
              -coupling=$coupling -charge=$charge -length=$sigmas \
              -deltaLimit=$deltaLimit -ignoreMismatch

        lappend nomes ${rootname}$i.ltime
        file delete {*}[glob ${rootname}$i.{mmap{,1,2,xt},twi}]
    }

    eval exec sddscombine -overWrite $nomes $rootname.ltime
    file delete {*}[glob ${rootname}???.ltime]

    set aveLT [eval exec sddscollapse $rootname.ltime -pipe=out \
                | sddsprocess -pipe -process=tLifetime,ave,tLifetime \
                | sdds2stream -pipe=in -par=tLifetime]
    set stdLT [eval exec sddscollapse $rootname.ltime -pipe=out \
                | sddsprocess -pipe -process=tLifetime,stand,tLifetime \
                | sdds2stream -pipe=in -par=tLifetime]
    return [list $aveLT $stdLT]
}


if {[file exists ${rootname}01.aper]} {
    foreach ext {mmap aper twi cod scor cor erl mag} {
        eval exec sddscombine [glob $rootname\[0-9\]\[0-9\].$ext] \
                              $rootname.$ext
        file delete {*}[glob ${rootname}??.$ext]
    }

    file delete {*}[glob $rootname??.{param2,param3,MAdone,out}]
}


# Compute the maximum stable momentum deviation by looking at
# tunes vs momentum.  This is simply to avoid major resonance
# crossings that might be stable (e.g., due to large tune shift
# with amplitude), but that make me nervous.

if {[file exists $rootname.w1] && [file exists $rootname.fin]} {
    exec sddscollapse $rootname.fin $rootname.finc

    # First, look for cases where the particle is lost and find the minimum
    # |delta|
    if [catch {exec sddsprocess $rootname.finc -pipe=out -nowarning \
                 "-define=col,deltaAbs,MALIN.DP abs" \
                 -filter=column,Transmission,1,1,! \
                 -process=deltaAbs,min,%sMin \
                 | sdds2stream -pipe -parameter=deltaAbsMin} result] {
        exit 1
    }
    puts stdout "Delta limit 1 : $result"
    if {![string match *e+308 $result] && [expr $result<$deltaLimit]} {
        set deltaLimit $result
    }

    # Second, look for undefined tunes
    if [catch {exec sddsnaff $rootname.w1 -pipe=out \
                 -column=Pass -pair=Cx,Cxp -pair=Cy,Cyp -terminate=frequencies=1 \
                 | sddscombine -pipe -merge \
                 | sddsxref -pipe $rootname.finc -take=MALIN.DP \
                 | sddsprocess -pipe "-define=column,deltaAbs,MALIN.DP abs" \
             -filter=col,deltaAbs,1e-3,1 \
                 | sddssort -pipe -column=deltaAbs \
                 | sddsprocess -nowarning -pipe=in $rootname.naff \
                 -process=C*Frequency,first,%s0 } result] {
        exit 1
    }
    puts stdout "Delta limit 2: $result"
    if {![string match *e+308 $result] && [expr $result<$deltaLimit]} {
        set deltaLimit $result
    }

    if [catch {exec sddsprocess -nowarning $rootname.naff -pipe=out \
                 -filter=col,CxFrequency,-1,-1,CyFrequency,-1,-1,|  \
                 -process=deltaAbs,min,%sMin \
                 | sdds2stream -pipe -parameter=deltaAbsMin} result] {
        exit 1
    }
    puts stdout "Delta limit 3: $result"
    if {![string match *e+308 $result] && [expr $result<$deltaLimit]} {
        set deltaLimit $result
    }

    # Look for integer or half-integer crossings
    foreach plane {x y} {
        if [catch {exec sddsprocess $rootname.naff -pipe=out -nowarning \
                     "-define=column,badTune,C${plane}Frequency 2 * int C${plane}Frequency0 2 * int - abs" \
                     -filter=col,badTune,1,1 \
                     -process=deltaAbs,min,%sMin \
                     | sdds2stream -pipe -parameter=deltaAbsMin} result] {
            exit 1
        }

        puts stdout "Delta limit 3 ($plane): $result"
        if {![string match *e+308 $result] && [expr $result<$deltaLimit]} {
            set deltaLimit $result
        }
    }
    puts stdout "New delta limit: $deltaLimit"
}

# Compute the Touschek lifetime for 100 mA in 864 bunches.
# The local momentum aperture is capped at the value we just computed usig the -deltaLimit option
puts stdout "Computing Lifetime for:\n"
puts stdout [format "Current    = %7.2f mA" $current]
puts stdout [format "Coupling   = %7.2f %%" [expr $coupling*100]]
puts stdout [format "Long. Size = %7.3f mm" $sigmas]
puts stdout [format "# bunches  = %7d" $bunches]
set LTime [calcLifetime -rootname $rootname -current $current -bunches $bunches \
             -coupling $coupling -sigmas $sigmas \
             -deltaLimit [expr 100*$deltaLimit] -sectors $sectors]
puts stdout [format "Lifetime   = %7.4f \u00B1 %7.4f h\n" \
                      [lindex $LTime 0] [lindex $LTime 1]]
puts stdout "Lifetime done"

exit 0
