#!/usr/bin/env python

from __future__ import print_function
from argparse import ArgumentParser
import os, shutil, sys
if sys.version >= '3':
    long = int
from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession, Row
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from random import random, randint, sample, randrange
from math import tan
import pandas as pd
def compute_accuracy(predictions_list):
    right_predictions = 0.0
    for line in predictions_list:
        if(line[2]==line[3]):
            right_predictions += 1
    return right_predictions / len(predictions_list)

def compute_accuracy_dummy(line_list):
    number_of_ones = 0.1
    for line in line_list:
        if(int(line[2])==1):
            number_of_ones += 1
    ratio_of_ones = number_of_ones / len(line_list)
    return max(ratio_of_ones, 1-ratio_of_ones)

def is_binary_matrix(lines):
    for line in lines:
        if line[2]!=0 and line[2]!=1:
            return False
    return True

def round_values(line_list):
    return [ [x[0], x[1], x[2], int(round(x[3]))] for x in line_list]

def create_dataframe_from_line_list(sc, ss, line_list, mode):
    if mode == True: #training dataframe
        rdd=sc.parallelize(line_list).map(lambda line:Row(ordered_file_id=long(line[3]),subject=long(line[1]), val=long(line[2]), row_file_index=long(line[0])))
    else: #test dataframe # there is a prediction on the 3rd column
        rdd=sc.parallelize(line_list).map(lambda line:Row(ordered_file_id=long(line[0]), subject=long(line[1]), val=long(line[2]), prediction=float(line[3])))
    return ss.createDataFrame(rdd)
def write_matrix(line,matrix_name):
    for i in range (0,len(line)):
        matrix_name.write(str(line[i]))
        if i != len(line)-1:
            matrix_name.write(";")
    matrix_name.write("\n")
# Find the max number of conditions and files
def n_columns_files(line_list):
    max_col_id = 0
    max_file_id = 0
    for line in line_list:
        if line[1] > max_col_id:
            max_col_id = line[1]
        if line[0] > max_file_id:
            max_file_id = line[0]
    return max_col_id + 1, max_file_id + 1

def count_occurrences(file_id, line_list):
    return len([line for line in line_list if line[0] == file_id])

def get_number_of_files_to_training(n_files ,n_subject, training_ratio, n_last_file): # in linear and exponential methods to calculate the num of reading files for the subject 
    pointer = 0
    c=1
    Nf , Ns = n_files-1, n_subject-1
    T = n_files * n_subject * training_ratio
    T_prime = T -(Ns + n_files)# first subject's file and first file of all subjects are removed in this matrix
    print ("training : ", T_prime)
    r_prime = (T_prime)/(Nf * Ns)# training ratio for the first half of the submatrix
    print ("ratio-half: ", r_prime)

    #training_ratio_subMatrix = (Nf * Ns * training_ratio)/(n_files * n_subject) # first subject's file and first file of all subjects are removed in this matrix
    #n_files_prime = int(round( 2 * Nf * (1-training_ratio_subMatrix)))
    #n_files_prime = (Nf * Ns - ((n_subject * n_files)*(1-training_ratio_subMatrix) -(n_files+Ns))) * 2 / Ns 
    # while start point   
    si = T_prime / Nf
    while c <= Ns:
        if si > Ns/2: # Trapezoid shape
            y=((2*T_prime)/Ns)-Nf
            if c <= (Ns/2)-1:
                n_last_file[pointer] = (2*(Nf-y)*c)/Ns
                c+=1
                pointer+=1
            else: # Symmetrical time
                n_last_file[c] = n_last_file[pointer]
                pointer -=1
                c+=1
        else: # Triangular shape (ratio line passed or touched the border)
            if c <= (Ns/2)-1 :
                if c < si:
                    n_last_file[pointer] = (Nf*c)/si
                c+=1
                pointer +=1
            else:
                n_last_file[c] = n_last_file[pointer]
                pointer -=1
    return n_last_file

   # c=1
   # while c <= Ns:
   #     if c <= Ns/2: 
   #         n_get_file= (2 * n_files_prime * c)/ Ns
   #         if n_get_file >= Nf: #line passed or touched the border
   #             n_last_file[pointer]= 0
   #         else:
   #             n_last_file[pointer]= n_get_file
   #         if c != Ns/2:
   #             pointer +=1
   #     else: #symetrical time
   #         n_last_file[c] = n_last_file[pointer]
   #         pointer -= 1
   #     c+=1
   # return n_last_file 

def random_split_2D(lines, training_ratio, max_diff, sampling_method):
    training = [] # this will contain the training set
    test = [] # this will contain the test set
    n_subject, n_files = n_columns_files(lines)
    training_matrix = open(sampling_method+"_"+str(training_ratio)+"_training_matrix.txt","w+")
    # Random selection of a subject (column) in advance then
    # pick that subject for every file of the condition, put it in training
    # and also pick first file for every subject, put it in training
    ran_subject_order = list(range(0,n_subject))
    shuffled_subject = sample(ran_subject_order,n_subject)
    first_ran_subject = shuffled_subject[0]
    print(" shuffled list of subjects:", shuffled_subject) 
   
    target_training_size = training_ratio * len(lines)
    for line in lines: # add the lines corresponding to the first file or the first subject
        if line[3] == 0 or line[1] == first_ran_subject: 
            assert(line not in training) # something wrong happened with the determination of subject_id and file_index
            training.append(line)
            write_matrix(line, training_matrix)
    subject_id = 1
    file_index = 0

    # used in random-real sampling method in the while loop below
    next_file = []
    n_last_file = [] # in linear mode records the number of selected files for the subject according to the formula (to be used for semetrycal purpose
    p=0
    for c in range(0,n_subject):
        n_last_file.append(0)
    print ("n_files: ", n_files,"n_subject:", n_subject) 
    for i in range(0, n_subject):
        next_file.append(1)
    while(len(training) < target_training_size):
        n_line_add = 0 
        assert(sampling_method in ["random-unreal", "columns", "rows", "random-real", "linear"]), "Unknown sampling method: {0}".format(sampling_method)

        if sampling_method == "linear":
            get_number_of_files_to_training (n_files, n_subject, training_ratio, n_last_file)
            p+=1
            if (p >= 243):
                print (n_last_file)
                break
           # for j in range (0, last_selected_file_subject_id):
               # file_index+=1
               # put_line_into_training (file_index,subject_id)
           # subject_id +=1
           # counter +=1

#            n_files_prime = n_files * ((2 * training_ratio) - 1)
#            # n_files_prime < 0  ratio makes the triangle passed or reached the matrix borders
#            # n_files_prime > 0  triangle (selected training set) is still in the matrix
#            
#            if subject_id <= n_subject/2 :#half_training_size is not completed 
#                calcul_file = int (round (subject_id * 2 * abs(n_files - n_files_prime) / n_subject))
#                print ("calcul_file: ", calcul_file)
#                if calcul_file < n_files : # still in the matrix
#                    n_last_file [c] = n_files - calcul_file
#                    last_selected_file_subject_id = n_last_file [c]
#                c += 1
#            else:  #half_training_size is completed (symetrical time)
#                if c != 0:
#                    c -= 1
#                last_selected_file_subject_id = n_last_file [c]
#            for j in range (0, last_selected_file_subject_id):
#                file_index += 1
#            if subject_id <n_subject:    
#                subject_id += 1
#            print (n_last_file)
#            print ("n_line_add", n_line_add)
#            print (subject_id)
#
        elif sampling_method == "random-unreal":
             subject_id = randrange(0, n_subject)
             file_index = randrange(0, n_files)
        elif sampling_method == "columns":
            file_index += 1
            if file_index == n_files:
                subject_id += 1
                file_index = 1
        elif sampling_method == "rows":
            subject_id += 1
            if subject_id == n_subject:
                file_index +=1
                subject_id = 1
        elif sampling_method == "random-real":
            subject_id = randrange(1, n_subject)
            if next_file[subject_id] <= n_files:
                file_index = next_file[subject_id]
                next_file[subject_id] +=1
            else:
                print("Subject id {0} is already fully sampled, looking for another one".format(subject_id))

        if (file_index < n_files and subject_id < n_subject):
       #     print ("File index or subject index is out of bound!")
       #     print (file_index, n_files, subject_id, n_subject)
             assert(file_index < n_files and subject_id < n_subject), "File index or subject index is out of bound!" # This should never happen
        for line in lines:
            if line[3] == file_index and line[1] == shuffled_subject[subject_id]:
              #  assert(line not in training), "File {0} of subject {1} is already in the training set".format(line[1], line[4]) # something wrong happened with the determination of subject_id and file_index
                if line not in training:
                    training.append(line)
                    write_matrix (line, training_matrix)
                break
    print("Training size is {0}".format(len(training)))

    # Every line which is not in training should go to test
    for line in lines:
        if line not in training:
            test.append(line)

    effective_training_ratio = len(training)/(float(len(lines)))
    print("Training ratio:\n  * Target: {0}\n  * Effective: {1}".format(training_ratio, effective_training_ratio))
    assert(abs(effective_training_ratio-training_ratio)<max_diff), "Effective and target training ratios differed by more than {0}".format(max_diff) # TODO: think about this threshold
    return training, test

def random_split(lines, training_ratio, max_diff):
    training = []
    test = []
    n_cond, n_files = n_columns_files(lines)
    n_overrides = 0 

    # pick one condition for every file, put it in training
    picked_conditions = {}
    for file_id in range(0, n_files):
        picked_conditions[file_id] = randint(0, n_cond-1)
    for line in lines:
        file_id = line[0]
        condition_id = line[1]
        if picked_conditions[file_id] == condition_id:
            training.append(line)

    # training now has n_files elements
    updated_training_ratio = (training_ratio*len(lines)-n_files)/(float(len(lines)-n_files))
    print("updated_training_ratio=", updated_training_ratio)
    assert(updated_training_ratio >= 0), "Training ratio is too small."

    # do the random sampling using new_ratio
    for line in lines:
        if line in training:
            continue
        file_id, cond_id, value = line[0], line[1], line[2]
        if random() < updated_training_ratio:
            training.append(line)
        else:
            test.append(line)
    effective_training_ratio = len(training)/(float(len(lines)))
    print("Training ratio:\n  * Target: {0}\n  * Effective: {1}".format(training_ratio, effective_training_ratio))
    assert(abs(effective_training_ratio-training_ratio)<max_diff), "Effective and target training ratios differed by more than {0}".format(max_diff) # TODO: think about this threshold
    return training, test

def write_line_list_to_text_file(line_list, file_name):
    with open(file_name, 'w') as f:
        for line in line_list:
            f.write("{0};{1};{2};{3}\n".format(line[0],line[1],line[2],line[3]))

def write_dataframe_to_text_file(df, file_path, overwrite=True):
    if os.path.exists(file_path) and overwrite:
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
    df.write.format("com.databricks.spark.csv").option("header", "true").save("file://"+os.path.abspath(file_path))

def parse_file(file_path):
    lines = []
    with open(file_path, 'r') as f:
        for line in f:
            elements = line.split(";")
            lines.append([int(elements[0]), int(elements[1]), int(elements[2]), int(elements[3])])
    return lines

# Concatenate the two Test and Training matrices text file to get the whole final predicted matrix 
def prediction_matrix (training_ratio,sampling_method):
    with open('hello-again.txt','wb') as wfd:
        for f in [sampling_method+"_"+training_ratio+'_test_data_matrix.txt', sampling_method+"_"+training_ratio+'_training_matrix.txt']:
            with open(f,'rb') as fd:
                shutil.copyfileobj(fd, wfd, 1024*1024*10)

def main(args=None):
    # Use argparse to get arguments of your script:
    parser = ArgumentParser("predict")
    parser.add_argument("matrix_file", action="store",
                        help="The matrix file produced by verifyFiles. Each line must be formated as '<file_id>;<condition_id>;<value>'.")
    parser.add_argument("training_ratio", action="store", type=float,
                        help="The ratio of matrix elements that will be added to the training set. Has to be in [0,1].")
    parser.add_argument("--predictions", "-p", action="store",
                        help="Text file where the predictions will be stored.")
    parser.add_argument("--random-ratio-error", "-r", action="store", type=float, default=0.01,
                        help="Maximum acceptable difference between target and effective training ratios. Defaults to 0.01.")
    parser.add_argument("sampling_method", action="store", 
                        help="Sampling method to use to build the training set.")
    results = parser.parse_args() if args is None else parser.parse_args(args)          
    assert(results.training_ratio <=1 and results.training_ratio >=0), "Training ratio has to be in [0,1]."
    # matrix file path, split fraction, all the ALS parameters (with default values)
    # see sim package on github
  
    conf = SparkConf().setAppName("predict").setMaster("local")
    sc = SparkContext(conf=conf)

    spark = SparkSession.builder.appName("ALS_session").getOrCreate()

    lines = parse_file(results.matrix_file)
    assert(len(lines) > 0), "Matrix file is empty"
    #training, test = random_split(lines, results.training_ratio, results.random_ratio_error)
    training, test = random_split_2D(lines, results.training_ratio, results.random_ratio_error, results.sampling_method)

    training_df = create_dataframe_from_line_list(sc,spark,training, True)
    test_df = create_dataframe_from_line_list(sc,spark,test, True)
    # Building recommendation model by use of ALS on the training set
    als = ALS(maxIter=5, regParam=0.01, userCol="subject", itemCol="ordered_file_id", ratingCol="val")
    model = als.fit(training_df)  
    # Assess the model 
    predictions = model.transform(test_df)
    if is_binary_matrix(lines): # assess the model
        # prediction will be rounded to closest integer
        # TODO: check how the rounding can be done directly with the dataframe, to avoid converting to list
        predictions_list = predictions.rdd.map(lambda row: [ row.ordered_file_id, row.subject,
                                                             row.val, row.prediction]).collect()
        predictions_list = round_values(predictions_list)
        test_data_matrix = open(results.sampling_method+"_"+str(results.training_ratio)+"_test_data_matrix.txt","w+")
        for i in range (len(predictions_list)):
            write_matrix(predictions_list[i],test_data_matrix)
        accuracy = compute_accuracy(predictions_list)
        print("Accuracy = " + str(accuracy))
        print("Accuracy of dummy classifier = " + str(compute_accuracy_dummy(lines)))
        predictions = create_dataframe_from_line_list(sc, spark, predictions_list, False)
        predictions.show(1000,False)
        print(pd.options.display.max_rows)
    else: # Assess model by use of RMSE on the test data
        evaluator = RegressionEvaluator(metricName="rmse", labelCol="val", predictionCol="prediction")
        rmse = evaluator.evaluate(predictions)
        print("RMSE = " + str(rmse))
        
    if results.predictions:
        write_dataframe_to_text_file(predictions, results.predictions)   
    #prediction_matrix (results.training_ratio,results.sampling_method)
if __name__ =='__main__':
       main() 
