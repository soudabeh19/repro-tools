#!/bin/bash
#myfslinstaller1.sh

set -e
set -u
set -o errexit
set -o pipefail
set -o nounset

# input args (with defaults):
# * version
# * os (centos 5 to 7)
# * install dir
# * download dir

#myfslinstaller1 function takes the parameters and downloads the corresponding file of fsl installer from the server 
#with the help of os and version parameters
if [[ $# -eq 0 ]] ; then
    echo 'No parameters are passed, taking default values'
fi

version=${1:-5.0.6}
os=${2:-CentOS7}
user=$USER
installDir=${3:-'/home/user/fsl'}
downloadDir=${4:-'/home/user/downloads'}

function myFslInstaller {
echo "###----FSL INSTALLER---###"
echo "$version"
echo "$os"
echo "$user"
echo "$installDir"
echo "$downloadDir"

if [[ ! ("$version" =~ ^[0-9].+$) ]]; then 

    echo 'Please pass a number that corresponds to an existing version of FSL'
    exit 1
fi

url=$(getDownloadURL "$version" "$os")

valid=$(validURL "$url")
echo "Valid: $valid"
if [[ "$valid" == true ]]; then
 echo "wget $url"
else
 echo "File doesn't exist in server"
fi

}

#Parameters: Version and OS
function getDownloadURL {
echo version="$1"
os="$2"
os="${os,,}"
echo "$os"
if [[ ( "$version" == "5.0.6" && "$os" == "centos7" ) || ( "$version" == "5.0.6" && "$os" == "centos6" ) ]]; then
	echo  'http://fsl.fmrib.ox.ac.uk/fsldownloads/oldversions/fsl-5.0.6-centos6_64.tar.gz'
elif [[ ( "$version" == "5.0.6" && "$os" == "centos5" ) ]]; then
        echo 'http://fsl.fmrib.ox.ac.uk/fsldownloads/oldversions/fsl-5.0.6-centos5_64.tar.gz'
elif [[ ( "$version" == "5.0.7" && "$os" == "centos6" ) || ( "$version" == "5.0.7" && "$os" == "centos7" ) ]]; then
        echo 'http://fsl.fmrib.ox.ac.uk/fsldownloads/oldversions/fsl-5.0.7-centos6_64.tar.gz'
elif [[ ( "$version" == "5.0.7" && "$os" == "centos5" ) ]]; then
        echo 'http://fsl.fmrib.ox.ac.uk/fsldownloads/oldversions/fsl-5.0.7-centos5_64.tar.gz'
elif [[ ( "$version" == "5.0.8" && "$os" == "centos6" ) || ( "$version" == "5.0.8" && "$os" == "centos7" ) ]]; then        
	echo 'http://fsl.fmrib.ox.ac.uk/fsldownloads/oldversions/fsl-5.0.8-centos6_64.tar.gz'
elif [[ ( "$version" == "5.0.8" && "$os" == "centos5" ) ]]; then
        echo 'http://fsl.fmrib.ox.ac.uk/fsldownloads/oldversions/fsl-5.0.8-centos5_64.tar.gz'
else
 echo 'Invalid parameters. Check the input parameters and try again'
 exit 1
fi
}

#Parameter:Download URL
function validURL {
if [[ `wget -S --spider $1  2>&1 | grep 'HTTP/1.1 200 OK'` ]]; then echo "true"; fi
}

#Function call
myFslInstaller

# Download FSL in download dir

# check md5sum

# unpack in install dir and install

# set the environment (check in the installer)
# # Set environment variables (run export not needed)
#export FSLDIR=install_dir
#export PATH=$PATH:${FSLDIR}/bin
#. ${FSLDIR}/etc/fslconf/fsl.sh
