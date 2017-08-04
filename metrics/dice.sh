#!/bin/bash

set -e
set -u

function convert {
    local image=$1
    local ext=$(echo ${image} | awk -F '.' '{print $NF}')
    if [ "${ext}" == "mgz" ]
    then
	local name=$(basename ${image} ${ext})
	mri_convert ${image} ${name}.nii.gz &>/dev/null
	echo ${name}.nii.gz
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
mul=$(mktemp mul-XXXXX.nii.gz)
fslmaths ${im1} -mul ${im2} ${mul}
inter=$(fslstats ${mul} -V | awk '{print $1}')
nim1=$(fslstats ${im1} -V | awk '{print $1}')
nim2=$(fslstats ${im2} -V | awk '{print $1}')
echo "scale=10 ; 2*${inter}/(${nim1}+${nim2})" | bc
\rm ${mul}

