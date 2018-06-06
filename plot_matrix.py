#!/usr/bin/env python

import numpy as np
import csv
import argparse
import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def parse_matrix(csv_file_name, is_original):
    with open(csv_file_name, 'rt') as csv_file:
        reader_test = csv.reader(csv_file, delimiter=';')
        matrix = {}
        for row in reader_test:
            assert(len(row) >= 3)
            if is_original:
                file_id = int(row[3]) # file_id
                subject_id = int(row[1]) #subject_id
                prediction = int(row[2]) #binary_difference
            else:
                file_id = int(row[0]) # file_id
                subject_id = int(row[1]) #subject_id
                prediction = int(row[3]) #predict_value
            if not matrix.get(file_id):
                matrix[file_id] = {}
            matrix[file_id][subject_id] = prediction
    print("number of files: ",len(matrix))
    print("number of subjects: ",len(matrix[0]))
    return matrix

def main():
    parser=argparse.ArgumentParser(description = "Plots a difference matrix.")

    parser.add_argument("original_matrix", help = "Matrix file to plot. Each row should be in the following format: <ignored> <subject_id> <binary_difference> <file_id>. File ids should be ordered according to their latest modification time.")# plotting original-matrix (row_index, subject, binary_difference, ordered_file_id)

    parser.add_argument("--test_matrix","-t", help = "Matrix file to plot. Each row should be in the following format: <file_id> <subject_id> <ignored> <predic_value>. File ids should be ordered according to their latest modification time.")# plotting test (ordered_file_id, subject, binary_difference, predict_value)

    parser.add_argument("output_file", help = "Output file where the plot will be saved. File type is determined from extension.")
    args=parser.parse_args()
    original_matrix = parse_matrix(args.original_matrix, True)
    if args.test_matrix is not None:
        test_matrix = parse_matrix(args.test_matrix, False)
    assert(original_matrix.get(0))
    n = np.zeros(shape=(len(original_matrix), len(original_matrix[0])), dtype=int)
    for file_id in original_matrix.keys():
        subject_dict = original_matrix[file_id]
        for subject_id in subject_dict.keys():
            original_value = subject_dict[subject_id]
            n[file_id, subject_id] = original_value
            if args.test_matrix is not None:
                if test_matrix.get(file_id) == None or test_matrix[file_id].get(subject_id) == None: # file and subject are in the test set
                        continue
                if test_matrix[file_id][subject_id] == original_value: # no difference
                    if test_matrix[file_id][subject_id] == 1:
                        n[file_id, subject_id] = 2
                    else:
                        n[file_id, subject_id] = 3
                else: # there is a difference
                    if test_matrix[file_id][subject_id] == 1:
                        n[file_id, subject_id] = 5
                    elif test_matrix[file_id][subject_id] == -1:
                        n[file_id, subject_id] = 6
                    else:
                        n[file_id, subject_id] = 4
            #print (file_id,subject_id,original_value,test_matrix[file_id][subject_id], n[file_id, subject_id])
    if args.test_matrix is not None:
        colors = ['#000000','#FFFFFF', '#4BFC4B','#777777','#FFFF00','#FF0000','#275EDD']
        d = np.unique(n)
        mapping = np.arange(d.size)
        index = np.digitize(n.ravel(), d, right=True)
        n = mapping[index].reshape(n.shape)
        colors = np.take(colors, d)
        #print(colors)
        cmap = matplotlib.colors.ListedColormap(colors)
    else:
        cmap = matplotlib.colors.ListedColormap(['#000000','#FFFFFF'])
    plt.matshow(n, interpolation='nearest', aspect='auto', cmap=cmap)
    black = mpatches.Patch(color='#000000')
    white = mpatches.Patch(color='#FFFFFF')
    green = mpatches.Patch(color='#4BFC4B')
    gray = mpatches.Patch(color='#777777')
    yellow = mpatches.Patch(color='#FFFF00')
    red = mpatches.Patch(color='#FF0000')
    blue = mpatches.Patch(color='#275EDD')
    if args.test_matrix is not None:
        plt.legend([black,white,green,gray,yellow,red,blue],["Negative","Positive","True Positive","True Negative","False Negative","False Positive","Invalid"],bbox_to_anchor=(0.,1.06, 1. , .102), loc=1, ncol=3, mode="expand", borderaxespad=0., fontsize='x-small')
    else:
        plt.legend([black,white],["Negative","Positive"],bbox_to_anchor=(0.,1.06 , 1., .102), loc=1, ncol=2, mode="expand", borderaxespad=0., fontsize='x-small')
    plt.xlabel('Subject')
    plt.ylabel('File-id')
    plt.savefig(args.output_file)

if __name__=='__main__':
    main()

