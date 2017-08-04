#!/bin/bash

set -e
set -u

if [ $# != 2 ]
then
    echo "Usage: $0 image1.nii.gz image2.nii.gz"
    echo "Image1 and image2 must be binary images"
    exit 1
fi

im1=$1
im2=$2
mul=$(mktemp mul-XXXXX.nii.gz)
fslmaths ${im1} -mul ${im2} ${mul}
inter=$(fslstats ${mul} -V | awk '{print $1}')
nim1=$(fslstats ${im1} -V | awk '{print $1}')
nim2=$(fslstats ${im2} -V | awk '{print $1}')
echo "scale=10 ; 2*${inter}/(${nim1}+${nim2})" | bc
\rm ${mul}

