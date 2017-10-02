#!/bin/bash

set -e
set -u


function convert {
    local image=$1
    local ext=$(echo ${image} | awk -F '.' '{print $NF}')
    if [ "${ext}" == "mgz" ]
    then
	local name=$(mktemp image-XXXXXX.nii.gz)
	mri_convert ${image} ${name} &>/dev/null
	echo ${name}
    else
	echo ${image}
    fi
}

if [ $# != 2 ]
then
    echo "Usage: $0 <im1> <im2>"
    exit 1
fi

im1=$(convert $1)
im2=$(convert $2)

diff=`mktemp diff-XXXX.nii.gz`

# Get the min and max intensities in image1
minmax=$(fslstats ${im1} -R)
min=$(echo ${minmax} | awk '{print $1}')
max=$(echo ${minmax} | awk '{print $2}')

# Compute the mean square difference
fslmaths ${im1} -sub ${im2} -sqr ${diff}
meandiff=$(fslstats ${diff} -m)

echo "scale=10; sqrt(${meandiff})/(${max}-(${min}))"  |bc

\rm ${diff}
if [ "${im1}" != "$1" ]
then # image was converted
  \rm -f ${im1} 
fi
if [ "${im2}" != "$2" ]
then # image was converted
  \rm -f ${im2}
fi

