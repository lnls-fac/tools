#!/usr/bin/env python3

import subprocess as sub

if sub.sys.argv[1] is None or sub.sys.argv[1] in ('-h', '--help'):
    print('Takes a lattice file and show the main results: ' +
          '\n\n Usage: simple_calc [lattice_name]')

lattice_name = sub.sys.argv[1].partition('.')[0]
extension    = sub.sys.argv[1].partition('.')[2]

path = ('/home/fac_files/data/sirius/si/beam_dynamics/calcs/' +
        'v07/study.new.lattice/scripts/templates/')

p = sub.getoutput('elegant '+path+'sirius.ele -macro=lattice='
                   + lattice_name + ',extension=' + extension)

sub.call(['visualize.py',lattice_name])
