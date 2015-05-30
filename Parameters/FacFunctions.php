<?php

# Constants
$light_speed = 299792458; # [m/s] - definition
$vacuum_permeability = 4*pi()*1e-7; # [T.m/A] - definition
$elementary_charge = 1.602176565e-19; # [C] - 2014-06-11
$electron_mass = 9.10938291e-31; # [Kg] - 2014-06-11
$electron_rest_energy = $electron_mass * pow($light_speed,2); # [Kg.m^2/s^2] - derived
$vacuum_permitticity = 1.0/($vacuum_permeability * pow($light_speed,2)); # [V.s/(A.m)] - derived
$electron_radius = pow($elementary_charge,2)/(4*pi()*$vacuum_permitticity*$electron_rest_energy); # [m] - derived
$joule_2_eV = 1.0 / $elementary_charge;
$reduced_planck_constant = 1.054571726e-34; # [J.s] - 2014-07-22
$rad_cgamma = 4*pi()*$electron_radius/pow($electron_rest_energy/$elementary_charge/1e9,3)/3; # [m]/[GeV]^3 - derived
$Cq = (55.0/(32*sqrt(3.0))) * ($reduced_planck_constant) * $light_speed / $electron_rest_energy; # [m] - derived
$Ca = $electron_radius*$light_speed / (3*pow($electron_rest_energy*$joule_2_eV/1.0e9, 3)); # [m^2/(s.GeV^3)] - derived

function joule_2_ev($value_j)
{
    global $joule_2_eV;
    return $joule_2_eV*$value_j;
}

function gamma($energy)
{
    /* Gamma from energy[GeV] */
    global $electron_rest_energy;

    return $energy * 1.0e9 / joule_2_ev($electron_rest_energy);
}

function beta($gamma)
{
    /* Beta factor from gamma */
    return sqrt((($gamma + 1.0)/$gamma)*(($gamma - 1.0)/$gamma));
}

function velocity($beta)
{
    /* Velocity [m/s] from ebeam beta factor */
    global $light_speed;

    return $beta * $light_speed;
}

function brho($energy, $beta)
{
    /* Magnetic rigidity [T.m] from ebeam energy [GeV] and beta factor */
    global $light_speed;

    return $beta * ($energy * 1e9) / $light_speed;
}

function rho($brho, $field)
{
    /* Bending radius [m] from magnetic rigidity [T.m] */
    return $brho / $field;
}

function critical_energy($gamma, $rho)
{
    /* Critical energy [keV] from ebeam gamma factor and bending radius [m] */
    global $reduced_planck_constant;
    global $light_speed;

    return (3 * joule_2_ev($reduced_planck_constant) * $light_speed *
        pow($gamma, 3)/ (2.0 * $rho)) / 1000;
}

function U0($energy, $I2)
{
    /* Energy loss U0 [keV] from ebeam energy [GeV] and I2[1/m] */
    global $rad_cgamma;

    return 1e6 * $rad_cgamma * pow($energy, 4) * $I2 / 2.0 / pi();
}

function sync_phase($q)
{
    /* Synchronous phase [deg] from overvoltage */
    return 180.0 - rad2deg(asin(1.0/$q));
}

function rf_energy_acceptance($q, $energy, $U0, $h, $alpha)
{
    /*
     * RF energy acceptance [%] from overvoltage, ebeam energy [GeV],
     * energy loss U0 per turn [keV], harmonic number h and linear compaction
     * factor alpha
     */

    $Fq = 0.0;

    if ($q > 1.0)
        $Fq = 2.0*(sqrt($q*$q-1.0) - acos(1.0/$q));

    $energy_accpt = (sqrt((1.0/pi()/$alpha/$h) * ($U0/($energy*1e6))*$Fq));

    return 100 * $energy_accpt;
}

function natural_emittance($gamma, $Jx, $I2, $I5)
{
    /*
     * Natural emittance [nm·rad] from ebeam gamma factor, damping partitio
     * number Jx, I2[1/m] and I5 [1/m]
     */
    global $Cq;

    $emitt = $Cq * $gamma*$gamma*$I5/($Jx*$I2) * 1e9;
    return $emitt;
}

function energy_spread($gamma, $I2, $I3, $I4)
{
    /*
     * Natural energy spread from ebeam gamma factor, I2[1/m], I3[1/m^2] and
     * I4[1/m]
     */
    global $Cq;

    $sigmae = sqrt($Cq * $gamma * $gamma * $I3 / (2*$I2 + $I4));
    return 100 * $sigmae;
}

function revolution_period($circumference, $velocity)
{
    /* Revolution period [μs] from circumference [m] and velocity[m/s] */
    return 1.0e6 * $circumference / $velocity;
}

function revolution_frequency($revolution_period)
{
    /* Revolution frequency [MHz] from revolution period [μs] */
    return 1.0 / $revolution_period;
}

function rf_frequency($revolution_frequency, $harmonic_number)
{
    /*
     * RF frequency [MHz] from revolution frequency [MHz] and
     * harmonic number
     */
    return $revolution_frequency * $harmonic_number;
}

function number_of_electrons($current, $revolution_period)
{
    /*
     * Number of electrons from beam current [mA] and
     * revolution period [μs]
     */
    global $elementary_charge;

    return ($current/1e3) * ($revolution_period/1e6) / $elementary_charge;
}

function overvoltage($rf_voltage, $U0)
{
    /* Overvoltage from RF voltage [MV] and energy loss U0 per turn [keV] */
    return 1e6*$rf_voltage / (1e3*$U0);
}

function alpha1($I1, $circumference)
{
    /* Linear momentum compaction factor from I1 [m] and circumference [m] */
    return $I1 / $circumference;
}

function Jx($I2, $I4)
{
    /* Horizontal damping partition number from I2 [1/m] and I4 [1/m] */
    return 1 - $I4/$I2;
}

function Js($Jx, $Jy)
{
    /* Longitudinal damping partition number from Jx and Jy */
    return 4.0 - $Jx - $Jy;
}

function frequency_from_tune($revolution_frequency, $tune)
{
    /* Frequency [kHz] from revolution frequency [MHz] and tune */
    return 1000*$revolution_frequency*($tune - floor($tune));
}

function damping_time($energy, $I2, $J, $circumference)
{
    /*
     * Radiation damping time [ms] from beam energy [GeV], radiation integral
     * I2 [1/m], damping partition number and circumference [m]
     */
    global $Ca;

    return 1000 * $circumference / ($Ca*pow($energy, 3)*$I2*$J);
}

function radiation_power($current, $U0)
{
    /*
     * Radiation power [kW] from beam current [mA] and
     * energy loss per turn [keV]
     */
    return $U0 * $current / 1000;
}

function rf_wavelength($frequency)
{
    /* RF wavelength [m] from RF frequency [MHz] */
    global $light_speed;

    return $light_speed / (1e6*$frequency);
}

function slip_factor($alpha, $gamma)
{
    /* Slip factor from momentum compaction factor alpha and gamma */
    return $alpha - 1/pow($gamma, 2);
}

function bunch_length($slip_factor, $energy_spread, $synchrotron_frequency)
{
    /*
     * Natural bunch length [mm] from slip factor, natural energy spread [%],
     * synchrotron frequency [kHz]
     */
    global $light_speed;

    $angular_synchrotron_frequency = 2 * pi() * $synchrotron_frequency;
    return ($light_speed * abs($slip_factor) * $energy_spread/100 /
        (1e3*$angular_synchrotron_frequency)) * 1000;
}

function bunch_duration($bunch_length, $beta)
{
    /* Bunch lenth in time units [ps] from bunch length [mm] and
     * beta factor
     */
    global $light_speed;

    return 1e9 * $bunch_length / $beta / $light_speed;
}

function id_deflection_parameter($field, $period)
{
    /* Insertion device deflection parameter from field [T] and period [mm] */
    global $light_speed;

    return 1e-9 * $period * $field * $light_speed / (joule_2_ev($electron_rest_energy)/1.0e6) / (2*pi());
}

function id_mean_power($energy, $current, $period, $nr_periods, $k)
{
    /*
     * Insertion device mean power from beam energy [GeV], current [mA],
     * ID period [mm], ID nr periods and k.
     *
     * See Handbook of Acc. Physics, eq.(14), pg 189
     */
    global $electron_rest_energy;

    $cst = pi() * 1e9 * $rad_cgamma * pow(joule_2_ev($electron_rest_energy)/1.0e9, 2);
    return ($cst * $energy * $k*$k * $nr_periods / ($period/1000.0))/1000.0;
}

function fac_write($filename, $text)
{
    $f = fopen('/tmp/' . $filename . '.txt', 'a');
    fwrite($f, $text . "\n");
    fclose($f);
}

?>
