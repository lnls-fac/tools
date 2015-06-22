#!/usr/bin/env python3

import subprocess as sub

def usage():
    print('\nUsage: matchNonLinear [old_lattice] [new_lattice]')
    print('old_lattice must have the extension and new_lattice must not.')

def matchNonLinear(lattice_old, lattice_new):
    path = ('/home/fac_files/data/sirius/si/beam_dynamics/calcs/' +
            'v07/study.new.lattice/scripts/templates/')
    p = sub.getoutput('elegant '+path+'matchNonLinear.ele -macro='+
                      'lattice_old=' + lattice_old +
                      ',lattice_new=' + lattice_new)

    try:
        star = p.index('Initial value for')
        en = p.index('Starting',star)
        print(p[star:en])

        star = p.index('Terms of equation:')
        en = p.index('statistics:    ET: ',star)
        print(p[star:en])
    except ValueError:
        print(p)

    #sub.call(['visualize',lattice_name + 'NonLinear'])


try:
    lattice_old = sub.sys.argv[1]
    lattice_new = sub.sys.argv[2]
    matchNonLinear(lattice_old,lattice_new)
except IndexError:
    usage()
