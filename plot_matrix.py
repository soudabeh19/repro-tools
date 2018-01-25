#!/usr/bin/env python

import numpy as np
import csv
import argparse
import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser(description = "Plots a difference matrix.")
   # parser.add_argument("matrix", help = "Matrix file to plot. Each row should be in the following format: <ignored> <subject_id> <binary_difference> <file_id>. File ids should be ordered according to their latest modification time.")# plotting training (row_index, subject, binary_difference, ordered_file_id)

    parser.add_argument("matrix-predict", help = "Matrix file to plot. Each row should be in the following format: <file_id> <subject_id> <ignored> <predic_value>. File ids should be ordered according to their latest modification time.")# plotting test (ordered_file_id, subject, binary_difference, predict_value)
    parser.add_argument("output_file", help = "Output file where the plot will be saved. File type is determined from extension.")
    args=parser.parse_args()

    a = []
    b = []
    c = []

    with open(args.matrix-predict, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            assert(len(row) >= 3)
            #a.append(int(row[3]))#ordered_file
            #b.append(int(row[1]))#subject_id
            #c.append(int(row[2]))#differnce-value 
            a.append(int(row[0]))#ordered_file_id
            b.append(int(row[1]))#subject_id
            c.append(int(row[3]))#predict-value 
    n = np.zeros(shape=(max(a)+1,max(b)+1))
    for i, x in enumerate(c):
        n[a[i],b[i]] = 1 #c[i]
    
    plt.imshow(n, cmap='Reds', interpolation='none', aspect='auto')
    plt.colorbar()
    plt.savefig(args.output_file)

if __name__=='__main__':
    main()

