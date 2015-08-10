#!/usr/bin/env python3

import subprocess as sub
import os

if sub.sys.argv[1] is None or sub.sys.argv[1] in ('-h', '--help'):
    print('Takes a lattice file and show the main results: ' +
          '\n\n Usage: simple_calc [lattice_name]')

lattice_name = sub.sys.argv[1].partition('.')[0]
extension    = sub.sys.argv[1].partition('.')[2]

path = '/'.join((os.path.dirname(os.path.realpath(__file__)),'templates',''))

p = sub.getoutput('elegant '+path+'sirius.ele -macro=lattice='
                   + lattice_name + ',extension=' + extension)

sub.call(['visualize.py',lattice_name])
