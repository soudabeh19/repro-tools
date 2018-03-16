#!/usr/bin/env python

import numpy as np
import csv
import argparse
import collections
import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt
import pandas as pd
plt.xlabel ("subject-id")
plt.ylabel ("file-id")


def main():
    parser=argparse.ArgumentParser(description = "Plots a difference matrix.")

    parser.add_argument("original_matrix", help = "Matrix file to plot. Each row should be in the following format: <ignored> <subject_id> <binary_difference> <file_id>. File ids should be ordered according to their latest modification time.")# plotting original-matrix (row_index, subject, binary_difference, ordered_file_id)

    parser.add_argument("test_matrix", help = "Matrix file to plot. Each row should be in the following format: <file_id> <subject_id> <ignored> <predic_value>. File ids should be ordered according to their latest modification time.")# plotting test (ordered_file_id, subject, binary_difference, predict_value)

    parser.add_argument("output_file", help = "Output file where the plot will be saved. File type is determined from extension.")
    args=parser.parse_args()

    a = []
    b = []
    c = []
    d =[]
    e =[]
    f =[]
    color = []
    with open(args.test_matrix, 'rb') as csvfile:
        reader_test = csv.reader(csvfile, delimiter=';')
        for row in reader_test:
            assert(len(row) >= 3)
            d.append(int(row[0]))#ordered_file_id
            e.append(int(row[1]))#subject_id
            f.append(int(row[3]))#predict-value 
    with open(args.original_matrix, 'rb') as csvfile:
        reader_origin = csv.reader(csvfile, delimiter=';')
        for row in reader_origin:
            assert(len(row) >= 3)
            a.append(int(row[3]))#ordered_file
            b.append(int(row[1]))#subject_id
            c.append(int(row[2]))#differnce-value
            color.append('N-Test, 0')
    n = np.zeros(shape=(max(a)+1,max(b)+1))
    for i, x in enumerate(c):
        n[a[i],b[i]]= c[i]
        for j, y in enumerate(f):
            if a[i] == d[j] and b[i] == e[j]:
                if c[i] == f[j] and f[j]== 1: # no difference in prediction
                    n[a[i],b[i]] = 2
                    color[i] = 'correct-1' 
                elif c[i] == 1 and f[j] == 0: # false negative
                    n[a[i],b[i]] = 4
                    color[i] = 'wrong-1'
                elif c[i] == f[j] and f[j]== 0:
                    color[i] = 'correct-0'
                    n[a[i],b[i]] = 3
                elif c[i] == 0 and f[j] == 1: #false positive
                    color[i] = 'wrong-0'
                    n[a[i],b[i]] = 5
                else:
                    print ("a[i]:%s,b[i]:%s,c[i]:%s,d[j]:%s,e[j]:%s,f[j]:%s"%(a[i],b[i],c[i],d[j],e[j],f[j]))
                    color[i] = 'missed'
    df= pd.DataFrame(dict(ordered_file_id = a, subject_id = b, color=color))
    fig, ax = plt.subplots()
    colors = {'correct-1':'lawngreen', 'correct-0':'lawngreen', 'wrong-1':'red', 'wrong-0':'red', 'N-Test, 1':'white', 'N-Test, 0':'white', 'missed':'yellow'}
    ax.scatter(df['subject_id'],df['ordered_file_id'],c=df['color'].apply(lambda x: colors[x]),marker='s')
    ax.legend(fontsize='small')
    plt.matshow(n, interpolation = 'nearest', aspect='auto')
    plt.colorbar()
    plt.savefig(args.output_file)

if __name__=='__main__':
    main()

