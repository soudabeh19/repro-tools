# repro-tools
A set of tools to evaluate the reproducibility of computations.


## Getting Started

verifyFiles.py is a Python Script which will produce an output containging the details regarding the common files and files that are not common, based on timestamp, checksum and distance between the output files.

### Prerequisites

Python 2.7.5

## Running the script

```
usage: verifyFiles.py [-h] [-c] [-d FILEDIFF] [-m METRICSFILE] [-e EXCLUDEITEMS] [-k CHECKCORRUPTION] file_in

file_in,                                   Mandatory parameter.Directory path to the file containing the conditions.
-h, --help                                 Show this help message and exit
-c, --checksumFile                         Reads checksum from files. Doesn't compute checksums locally if this parameter is set.
-d FILEDIFF, --fileDiff FILEDIFF           Writes the difference matrix into a file.
-m METRICSFILE, --metricsFile METRICSFILE  CSV file containing metrics definition. Every line contains 4 elements: metric_name,file_extension,command_to_run,output_file_name
-e EXCLUDEFOLDERS, --excludeFolders        The path to the file containing the folders and files that should be excluded from creating checksums.
-k CHECKCORRUPTION, --checkCorruption      The script verifies if any files are corrupted ,when this flag is set as true
-s SQLITEFILE,      --sqLiteFile           The path to the SQLITE file,having the reprozip trace details.
-x EXECFILE ,       --execFile             Writes the executable details to a file.
```

### Test Cases

To be updated


## Authors

* **Big Data Lab Team - Concordia University**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details



