[![CircleCI](https://circleci.com/gh/big-data-lab-team/repro-tools.svg?style=svg)](https://circleci.com/gh/big-data-lab-team/repro-tools)
[![codecov](https://codecov.io/gh/big-data-lab-team/repro-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/big-data-lab-team/repro-tools)

# repro-tools
A set of tools to evaluate the reproducibility of computations.

## verifyFiles

verifyFiles.py compares the output files produced by pipelines in different conditions. It identifies the files that are common to all conditions, and for these files, it compares them based on their checksums and other metrics configurable by file type.

### Prerequisites

Python 2.7.5

## Running the verifyFiles.py script

```
usage:verifyFiles.py result_base_name [-h] [-c CHECKSUMFILE] [-d FILEDIFF] [-m METRICSFILE] [-e EXCLUDEITEMS] [-k CHECKCORRUPTION] [-s SQLITEFILE] [-x EXECFILE] [-t TRACKPROCESSES]
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
>pytest --cov=./ ./test_verifyFiles.py
## plot_matrix

`plot_matrix.py` plot heatmaps of difference matrices produced by
`verifyFiles.py`. For instance, `./plot_matrix.py
test/test_differences_plot.txt output.png` will produce the following
plot:

![Alt text](./test/test_differences_plot.png?raw=true "Title")

## Pipelines Error Detection Script (PEDS)

The aim of `PEDS` is clustering processes and creating a graph model representation for the all processes which introduce errors in the pipeline
based on the reprozip trace file (trace.sqlite3) and matrix-file created by `veryfyFiles.py` that specify the pipeline output files with defferences.

### Prerequisites:

Python 2.7.5, graphviz module

### Running the script:

  * `peds.py [-db: database file from reprozip trace] [-ofile: the matrix-file from veryfyFiles.py]`

    *Note: The output would be a dot format file which requiers to create appropriate representing file formats such as: svg, png and etc.

  * `dot -Tpng Graphmodel.dot -o Figure.png`


