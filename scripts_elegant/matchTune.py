#!/usr/bin/env python3

import subprocess as sub

def usage():
    print('\nUsage: matchTune [old_lattice] [new_lattice] [tunex] [tuney]')
    print('old_lattice must have the extension\n' +
          'new_lattice must not have the extension\n'+
          'tunex and tuney are the cell tunes\n')

def matchTune(lattice_old, lattice_new, nux, nuy):

    path = '/'.join((os.path.dirname(os.path.realpath(__file__)),'templates',''))

    p = sub.getoutput('elegant '+path+'matchTune.ele -macro=tunex='+nux+',tuney=' +nuy+
                      ',lattice_old='+lattice_old+',lattice_new='+ lattice_new)

    try:
        star = p.index('Initial value for')
        en = p.index('Starting',star)
        print(p[star:en])
        star = p.index('Terms of equation:')
        en = p.index('statistics:    ET: ',star)
        print(p[star:en])
    except ValueError:
        print(p)

    with open(lattice_new+'.out','w+',encoding='utf8',newline='\r\n') as fout:
        fout.write(p)


    #sub.call(['visualize',lattice_name + 'Tune'])


try:
    lattice_old=sub.sys.argv[1]
    lattice_new=sub.sys.argv[2]
    nux = sub.sys.argv[3]
    nuy = sub.sys.argv[4]
    matchTune(lattice_old, lattice_new, nux, nuy)
except IndexError:
    usage()
