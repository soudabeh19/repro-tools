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
    echo "Usage: $0 image1.nii.gz image2.nii.gz"
    exit 1
fi

im1=$(convert $1)
im2=$(convert $2)

diff=$(mktemp diff-XXXXX.nii.gz)
fslmaths ${im1} -sub ${im2} ${diff}
nim1=$(fslstats ${im1} -v | awk '{print $1}')
nim2=$(fslstats ${im2} -v | awk '{print $1}')
n_diff=$(fslstats ${diff} -V | awk '{print $1}')
echo "scale=10 ; (${nim1}+${nim2}-2*${n_diff})/(${nim1}+${nim2})" | bc
\rm ${diff}
if [ "${im1}" != "$1" ]
then # image was converted
  \rm -f ${im1} 
fi
if [ "${im2}" != "$2" ]
then # image was converted
  \rm -f ${im2}
fi

