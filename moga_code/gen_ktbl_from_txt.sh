#!/bin/bash

csv2sdds sabia_kicktable.txt -pipe=out \
    -columnData=name=x,type=double,units=m \
    -columnData=name=y,type=double,units=m \
    '-columnData=name=xpFactor,type=double,units=\(T*m\)$a2$n' \
    '-columnData=name=ypFactor,type=double,units=\(T*m\)$a2$n' \
    -separator=" " | \
    sddssort -pipe=in sabia_kicktable.sdds \
    -column=y,increasing -column=x,increasing
