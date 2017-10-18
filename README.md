[![CircleCI](https://circleci.com/gh/big-data-lab-team/repro-tools.svg?style=svg)](https://circleci.com/gh/big-data-lab-team/repro-tools)
[![codecov](https://codecov.io/gh/big-data-lab-team/repro-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/big-data-lab-team/repro-tools)

# repro-tools
A set of tools to evaluate the reproducibility of computations.
The provided tools are:

* verifyFiles.py 	 
* predict.py 		 

## Getting Started with verifyFile.py

verifyFiles.py is a Python Script which will produce an output containging the details regarding the common files and files that are not common, based on timestamp, checksum and distance between the output files.

### Prerequisites

Python 2.7.5

## Running the verifyFiles.py script

```
usage:verifyFiles.py [-h] [-c CHECKSUMFILE] [-d FILEDIFF] [-m METRICSFILE] [-e EXCLUDEITEMS] [-k CHECKCORRUPTION] [-s SQLITEFILE] [-x EXECFILE]  [-b BINARYMATRIX] [-t TRACKPROCESSES]
                     [-i FILEWISEMETRICVALUE] file_in

file_in,                                          Mandatory parameter.Directory path to the file containing the conditions.
results_base_name,                                Base name to use in output file names.
-c,CHECKSUM FILE,       --checksumFile            Reads checksum from files. Doesn't compute checksums locally if this parameter is set.
-m METRICSFILE,         --metricsFile             CSV file containing metrics definition. Every line contains 4 elements: metric_name,file_extension,command_to_run,output_file_name
-e EXCLUDEITEMS,        --excludeItems            The path to the file containing the folders and files that should be excluded from creating checksums.
-k CHECKCORRUPTION,     --checkCorruption         The script verifies if any files are corrupted ,when this flag is set as true
-s SQLITEFILE,          --sqLiteFile              The path to the SQLITE file,having the reprozip trace details.
-x EXECFILE ,           --execFile                Writes the executable details to a file.
-t TRACK PROCESSES,     --trackProcesses          If this flag is set, it traces all the processes using reprozip to record the details and writes it into a csv with with the given name
-i FILEWISEMETRICVALUE, --filewiseMetricValue     Folder name on to which the individual filewise metric values are written to a csv file
```
### Test Cases
__Pytest syntax__
> pytest --cov=./ ./test_verifyFiles.py

## Getting Started with predict.py
predict.py is a Python Script which 
provides to predict specific values of the input matrix, according to the user defined training ratio. 


### Prerequisites

Python 2.7.5
Spark 2.1.0

## Running the predict.py script

```
usage:predict.py [-p][-r] matrix_file  training_ratio

matrix_file					  Mandatory parameter.Directory path to the file containing the matrix.
training_ratio					  The ratio of matrix elements that will be added to the training set. Has to be in [0,1].
[-p]			--predictions		  Text file where the predictions will be stored.
[-r]			--random-ratio-error	  Maximum acceptable difference between target and effective training ratio. Defaults to 0.01 .
```

### Test Cases
__Pytest syntax__
> pytest --cov=./ ./test_predict.py

## Authors

* **Big Data Lab Team - Concordia University**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details



