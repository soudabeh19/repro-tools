# Pipelines Error Detection Script (PEDS)

The aim of "PEDS" is clustering processes and creating a graph model representation for the all processes which introduce errors in the pipeline
based on the reprozip trace file (trace.sqlite3) and matrix-file from repro-tools that defines pipeline output files with defferences.

##Prerequisites:
Python 2.7.5, graphviz module 

##Running the script:

1) peds13-2.py [-db: database file from reprozip trace] [-ofile: matrix-file from repro-tools]

*Note: The output would be a dot format file which requiers to create appropriate representing file formats such as: svg, png and etc.

2) dot -Tpng Graphmodel.dot -o Figure.png
