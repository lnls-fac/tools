#!/usr/bin/env python3

import subprocess as sub
import os
import shutil as sh
import math

def usage():
    print('\nUsage: evalLattice [fileName] [nturns] [nsteps]')
    print('fileName must have the extension.\n' +
          'Parameters nturns and nsteps are optional.')

def evalLatt(lattice, nturns=1000,nsteps=20, nproc =1):

    if nproc > nsteps:
        nproc = nsteps

    rootname = lattice.partition('.')[0]

    if not os.path.isdir(rootname):
        os.mkdir(rootname)

    os.chdir(rootname)
    sh.copyfile('../' + lattice, lattice)

    path = ('/home/fac_files/data/sirius/si/beam_dynamics/calcs/' +
           'v07/study.new.lattice/scripts/templates/')

    steps_per_proc = int(math.modf(nsteps/nproc)[1])
    left_steps = nsteps - nproc*steps_per_proc

    for i in range(1,nproc+1):
        if i <= left_steps:
            submit_steps = steps_per_proc + 1
        else:
            submit_steps = steps_per_proc

        rootnamei = rootname+'{0:02d}'.format(i)
        with open(rootnamei+'.out', mode='w') as fi:
            proc = sub.Popen(['/usr/local/epics_oag/oag/apps/bin/linux-x86_64/'+
                          'elegant',path+'evalTemplate.ele',
                          '-macro=lattice='+lattice+
                          ',rootname='+rootnamei+
                          ',nturns='+str(nturns)+
                          ',nsteps='+'{0:d}'.format(submit_steps)+
                          ',seed='+'{0:d}'.format(i*777)],
                         stdout=fi,stderr=sub.STDOUT,start_new_session=True)

try:
    lattice=sub.sys.argv[1]
    nturns = int(sub.sys.argv[2])
    nsteps = int(sub.sys.argv[3])
    nproc  = int(sub.sys.argv[4])
    evalLatt(lattice,nturns,nsteps, nproc)

except IndexError:
    usage()
