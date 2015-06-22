#!/usr/bin/env python3

import subprocess as sub

lattice_name=sub.sys.argv[1]

path = ('/home/fac_files/data/sirius/si/beam_dynamics/calcs/' +
        'v07/study.new.lattice/scripts/templates/')

p = sub.getoutput('elegant '+path+'matchEmittance.ele -macro=lattice=' + lattice_name)

star = p.index('Initial value for')
en = p.index('Starting',star)
print(p[star:en])

star = p.index('Terms of equation:')
en = p.index('statistics:    ET: ',star)
print(p[star:en])

sub.call(['visualize',lattice_name + 'Emit'])
