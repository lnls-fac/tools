#!/bin/bash

# Script para plotar vários gráficos de	abertura dinamica e de momentum

plotDA="sddsplot -same -sever=xGap=0.006 -graph=line,vary "
plotMA="sddsplot -same -sever=xGap=15 -graph=line,vary "

for ii in "$@"; do
    plotDA="${plotDA} -col=x,y -leg=spec=${ii} ${ii}.aper";
    plotMA="${plotMA} -col=s,delta????tive -leg=spec=${ii} ${ii}.mmap";
done

eval $plotDA
eval $plotMA
