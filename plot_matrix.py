#!/usr/bin/env python

import numpy as np
import csv
import argparse
import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser(description = "Plots a difference matrix.")
    parser.add_argument("matrix", help = "Matrix file to plot. Each row should be in the following format: <ignored> <subject_id> <binary_difference> <ignored> <file_id>. File ids should be ordered according to their latest modification time.")
    parser.add_argument("output_file", help = "Output file where the plot will be saved. File type is determined from extension.")
    args=parser.parse_args()

    a = []
    b = []
    c = []

    with open(args.matrix, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            assert(len(row) >= 3)
            a.append(int(row[3]))
            b.append(int(row[1]))
            c.append(int(row[2]))

    n = np.zeros(shape=(max(a)+1,max(b)+1))
    for i, x in enumerate(c):
        n[a[i],b[i]] = c[i]
    
    plt.imshow(n, cmap='hot', interpolation='none', aspect='auto')
    plt.colorbar()
    plt.savefig(args.output_file)

if __name__=='__main__':
    main()

