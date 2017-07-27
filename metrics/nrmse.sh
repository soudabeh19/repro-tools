#!/bin/bash

set -e
set -u

if [ $# != 2 ]
then
    echo "Usage: $0 <im1> <im2>"
    exit 1
fi

im1=$1
im2=$2

diff=`mktemp diff-XXXX.nii.gz`
sqr=`mktemp sqr-XXXX.nii.gz`

# Get the min and max intensities in image1
minmax=$(fslstats ${im1} -R)
min=$(echo ${minmax} | awk '{print $1}')
max=$(echo ${minmax} | awk '{print $2}')

# Compute the mean square difference
fslmaths ${im1} -sub ${im2} -sqr ${diff}
meandiff=$(fslstats ${diff} -m)

echo "scale=10; sqrt(${meandiff})/(${max}-(${min}))"  |bc

\rm ${diff} ${sqr}
