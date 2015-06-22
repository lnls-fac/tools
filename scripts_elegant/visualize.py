#!/usr/bin/env python3

import subprocess as sub

def usage():
    print('Prints the main results of the optimization and plot the twiss parameters:'
         '\n\n Usage: visualize [rootName]')

def visualize(lattice_name):
    if lattice_name in ('-h', '--help'):
       usage()
       return

    sub.call(['plotTwiss','-fileRoot',lattice_name])

    p = sub.getoutput('sdds2stream -par=ex0 ' + lattice_name + '.twi')
    print('\nEmittance [pm.rad] = {0:8.4f}'.format(float(p) * 1e12))
    p = sub.getoutput('sdds2stream -par=nux ' + lattice_name + '.twi')
    print('Tunex              = {0:8.4f}'.format(float(p)))
    p = sub.getoutput('sdds2stream -par=nuy ' + lattice_name + '.twi')
    print('Tuney              = {0:8.4f}'.format(float(p)))
    p = sub.getoutput('sdds2stream -par=betaxMax ' + lattice_name + '.twi')
    print('Maximo Betax       = {0:8.4f}'.format(float(p)))
    p = sub.getoutput('sdds2stream -par=betayMax ' + lattice_name + '.twi')
    print('Maximo Betay       = {0:8.4f}'.format(float(p)))
    p = sub.getoutput('sdds2stream -col=ElementName,betax,betay,etax ' + lattice_name + '.twi')
    indmi  = p.index('MIB')
    indend = p.index('\n',indmi)
    miLine = p[indmi:indend].split()
    print('Betax @ MIB        = {0:8.4f}'.format(float(miLine[1])))
    print('Betay @ MIB        = {0:8.4f}'.format(float(miLine[2])))
    print('Etax @ MIB         = {0:8.4f}'.format(float(miLine[3])))
    indmi  = p.index('MIA')
    indend = p.index('\n',indmi)
    miLine = p[indmi:indend].split()
    print('Betax @ MIA        = {0:8.4f}'.format(float(miLine[1])))
    print('Betay @ MIA        = {0:8.4f}'.format(float(miLine[2])))
    print('Etax @ MIA         = {0:8.4f}'.format(float(miLine[3])))
    

try:
    visualize(lattice_name=sub.sys.argv[1])
except IndexError:
    usage()

