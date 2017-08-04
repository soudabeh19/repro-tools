# Metrics

A set of scripts that take two files as argument and return a number on their standard output.

* `dice.sh`: returns the Dice coefficient between images. Requires `fslmaths`, `fslstats` and Freesurfer's `mri_convert` (environment variable FREESURFER_HOME should be set to a directory containing a valid Freesurfer license in `license.txt`).
* `nrmse.sh`: returns the root mean square error, normalized by the amplitude of the image (max intensity - min intensity).
