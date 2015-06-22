#!/usr/bin/env python3

import subprocess as sub

lattice_name=sub.sys.argv[1]

path = ('/home/fac_files/data/sirius/si/beam_dynamics/calcs/' +
        'v07/study.new.lattice/scripts/templates/')

p = sub.getoutput('elegant '+path+'matchEmittance.ele -macro=lattice=' + lattice_name)

print(p)

nux = float(sub.getoutput('sdds2stream -par=nux ' + lattice_name + '.twi'))
print(nux)
if 0.05 < nux % 0.1 < 0.099:
    if nux % 0.1 > 0.075:
        nux = round(nux,1) + 0.026
    else:
        nux = round(nux,1) - 0.1 + 0.026

nuy = float(sub.getoutput('sdds2stream -par=nuy ' + lattice_name + '.twi'))
print(nuy)
if 0.05 < nuy % 0.1 < 0.099:
    if nuy % 0.1 > 0.075:
        nuy = round(nuy,1) + 0.020
    else:
        nuy = round(nuy,1) - 0.1 + 0.020
print(nux, nuy)

p = sub.getoutput('elegant '+path+'matchTune.ele -macro=tunex=' + str(nux) + ',tuney=' + str(nuy) + ',lattice=' + lattice_name)
