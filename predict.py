#!/usr/bin/env python

from __future__ import print_function, division
from argparse import ArgumentParser,SUPPRESS
import os, shutil, sys
from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession, Row
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
import random as rn
from random import random, randint, sample, randrange
from collections import Counter 
from pyspark.sql import functions as F
import pandas as pd
import numpy as np

def compute_accuracy(predictions_list,file_mean):
    right_predictions = 0.0
    correct_pure_predic = 0.0
    for line in predictions_list:
        for f_mean in file_mean:
            if (line[2]==line[3] and line[0]==f_mean[0]):
                if (f_mean[1] not in (0,1)):
                    correct_pure_predic += 1
        if (line[2]==line[3]):
            right_predictions += 1
    acc = right_predictions / len(predictions_list)
    pure_acc = correct_pure_predic / len(predictions_list)
    return (acc,pure_acc)

def sens_spec(predictions_list):
    TP=TN=FP=FN = 0
    for line in predictions_list:
        if (line[2]==line[3]):
            if (line[3]==1):
                TP += 1
            else:
                TN += 1
        elif (line[3]==1):
            FP += 1
        else : 
            FN += 1
    all_positive = TP+FN
    all_negative = TN+FP
    if all_positive == 0:
        sens = None
    else:
        sens = TP/all_positive
    if all_negative == 0:
        spec = None
    else:
        spec = TN/all_negative
    return(sens, spec)

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
        if line[3] > max_file_id:
            max_file_id = line[3]
    return max_col_id + 1, max_file_id + 1

def get_number_of_files_to_training(n_files ,n_subject, training_ratio, n_last_file, sampling_method): 
    for i in range(0, n_subject):
        if sampling_method == "RFNU":
            a = 0
            if training_ratio <= 0.5:
                if(rn.random() <= 2*training_ratio):
                    n_last_file[i] = rn.randrange(0, n_files, 1)
                else:
                    n_last_file[i] = 0
            else:
                n_last_file[i] = rn.randrange(int(round(2*training_ratio*n_files))-n_files, n_files, 1)
            
        elif sampling_method == "RFNT-S":
            if training_ratio >= 1/3.0:
                if training_ratio >= 2/3.0:
                    b= n_files
                    a =0
                    if  rn.uniform(0,1) <= 3 * (1-training_ratio): #with probability 3(1-alpha)
                        n_last_file[i] = np.random.triangular(a, b, n_files)
                    else:
                        n_last_file[i] = n_files
                else:
                    b = n_files*((3*training_ratio)-1)
                    a = 0
                    n_last_file[i] = np.random.triangular(a,b,n_files)
            else:
                a = 0
                b = 0
                if rn.uniform(0,1) <= 3 * training_ratio: #with probability 3(alpha)
                    n_last_file[i] = np.random.triangular(a, b, n_files)
                else: 
                    n_last_file[i] = 0
        
        else: #sampling_method == "RFNT-L"
	    if training_ratio >= 1/3.0:
                a = (n_files*((3 * training_ratio)-1))/2
                b = a
                n_last_file[i] = np.random.triangular(a, b, n_files)
            else:
                a = 0
                b = 0
                if rn.uniform(0,1) <= 3 * training_ratio: #with probability 3(alpha)
                    n_last_file[i] = np.random.triangular(a, b, n_files)
                else:
                    n_last_file[i] = 0
            
    return n_last_file , a

def put_files_into_training(n_last_file, lines,shuffled_subject,training, training_matrix):
    for i in range (1,len(shuffled_subject)):
        for line in lines:
            if line[3] <= n_last_file[i-1] and line[1] == shuffled_subject[i]:
                if line not in training:
                    training.append(line)
                    write_matrix(line,training_matrix)

def random_split_2D(lines, training_ratio, max_diff, sampling_method, dataset, approach):
    training = [] # this will contain the training set
    test = [] # this will contain the test set
    n_subject, n_files = n_columns_files(lines)
    training_matrix = open(sampling_method+"_"+dataset+"_"+approach+"_"+str(training_ratio)+"_training_matrix.txt","w+")
    # Random selection of a subject (column) in advance then
    # pick that subject for every file of the condition, put it in training
    # and also pick first file for every subject, put it in training
    ran_subject_order = list(range(0,n_subject))
    shuffled_subject = rn.sample(ran_subject_order,n_subject)
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
    # used in RS sampling method in the while loop below
    next_file = []
    n_last_file = [] # in RFNU mode records the number of selected files for the subject according to the formula (to be used for semetrycal purpose
    p=0
    for c in range(0,n_subject):
        n_last_file.append(0)
    print ("n_files: ", n_files,"n_subject:", n_subject) 
    for i in range(0, n_subject):
        next_file.append(1)
    while(len(training) < target_training_size):
        n_line_add = 0 
        assert(sampling_method in ["random-unreal", "columns", "rows", "RS", "RFNU", "RFNT-L", "RFNT-S"]), "Unknown sampling method: {0}".format(sampling_method)

        if sampling_method in {"RFNU", "RFNT-L", "RFNT-S"}:
            n_last_file , a = get_number_of_files_to_training (n_files, n_subject, training_ratio, n_last_file, sampling_method)
            put_files_into_training (n_last_file, lines, shuffled_subject,training,training_matrix)
            break
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
        elif sampling_method == "RS":
            subject_id = randrange(1, n_subject)
            if next_file[subject_id] <= n_files:
                file_index = next_file[subject_id]
                next_file[subject_id] +=1
            else:
                print("Subject id {0} is already fully sampled, looking for another one".format(subject_id))

        if (file_index < n_files and subject_id < n_subject):
             assert(file_index < n_files and subject_id < n_subject), "File index or subject index is out of bound!" # This should never happen
        for line in lines:
            if line[3] == file_index and line[1] == shuffled_subject[subject_id]:
               # assert(line not in training), "File {0} of subject {1} is already in the training set".format(line[1], line[4]) # something wrong happened with the determination of subject_id and file_index
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
    if (sampling_method not in  ("RFNU", "RFNT-L", "RFNT-S")):
        assert(abs(effective_training_ratio-training_ratio)<max_diff), "Effective and target training ratios differed by more than {0}".format(max_diff) # TODO: think about this threshold
    else: # To keep the max difference of effective and target training ratios to 0.01
        subjects_in_training = []
        subjects_in_training = list(set(map(lambda s: s[1],training)))
        applicable_subjects_in_training = []
        applicable_subjects_in_training = subjects_in_training
        applicable_subjects_in_training.remove(first_ran_subject)
        if abs(effective_training_ratio-training_ratio)> max_diff and sampling_method == "RFNT-L":
            if effective_training_ratio > training_ratio:  # downsizing the training set
                while len(training) > target_training_size:
                    last_sub_fileid, ran_subject = balance_training (training, applicable_subjects_in_training)
                    if last_sub_fileid == a: #to respect the largest-a it is not allowed to remove those files which file-id is less than the minimum required for each subject
                        last_sub_fileid, ran_subject = balance_training (training, applicable_subjects_in_training)
                    else:
                        target_sub = filter(lambda x: x[3]==last_sub_fileid,filter(lambda y: y[1] == ran_subject[0],training))
                        test.append(target_sub[0])
                	training.remove(target_sub[0])
            else: #oversampling the training set
                oversampling_training(training,test,target_training_size,lines,n_subject)

        elif effective_training_ratio > training_ratio: # downsizing the training set 
            while len(training) > target_training_size:
                last_sub_fileid, ran_subject = balance_training (training, applicable_subjects_in_training)
                if last_sub_fileid == min(map(lambda x: x[3], filter(lambda y: y[1] == ran_subject[0], lines))):# To respect the fact of having at least one file for each subject
                    last_sub_fileid, ran_subject = balance_training (training, applicable_subjects_in_training)
                else:
                    target_sub = filter(lambda x: x[3]==last_sub_fileid,filter(lambda y: y[1] == ran_subject[0],training))
                    test.append(target_sub[0])
                    training.remove(target_sub[0])
        elif effective_training_ratio < training_ratio:  #oversampling the training set
            oversampling_training(training,test,target_training_size,lines,n_subject)
        final_effective_training_ratio = len(training)/(float(len(lines)))
        print ("Modified_effective_training_ratio: ",final_effective_training_ratio)
        print("Updated training size is {0}".format(len(training)))
    return training, test

def balance_training (training, applicable_subjects_in_training ): #Get the maximum file-id for the random selected subject in the current training set
    random_subject = rn.sample(applicable_subjects_in_training,1)
    last_sub_fileid = max(map(lambda x: x[3], filter(lambda y: y[1] == random_subject[0], training)))
    return(last_sub_fileid, random_subject)

def oversampling_training (training,test,target_training_size,lines,n_subject):
    while len (training) < target_training_size:
        ran_subject_id = randrange(1, n_subject)
        last_sub_fileid = max(map(lambda x: x[3], filter(lambda y: y[1] == ran_subject_id, training)))
        next_sub_fileid = last_sub_fileid + 1
        if next_sub_fileid < max(map(lambda x: x[3], filter(lambda y: y[1] == ran_subject_id, lines))):
            target_sub = filter(lambda x: x[3]==next_sub_fileid,filter(lambda y: y[1] == ran_subject_id,lines))
            training.append(target_sub[0])
            test.remove(target_sub[0])
    return test,training

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

def latentFactors(model, sampling_method, dataset, approach, training_ratio):
    labels = ['id','feature']
    df_userFactors = pd.DataFrame.from_records(model.userFactors.orderBy("id").collect(), columns=labels)
    df_itemFactors = pd.DataFrame.from_records(model.itemFactors.orderBy("id").collect(), columns=labels)
    df_userFactors.to_csv(sampling_method+"_"+dataset+"_"+approach+"_"+str(training_ratio)+'userFactors.csv', sep='\t')
    df_itemFactors.to_csv(sampling_method+"_"+dataset+"_"+approach+"_"+str(training_ratio)+'itemFactors.csv', sep='\t')

def main(args=None):
    # Use argparse to get arguments of your script:
    parser = ArgumentParser("predict")
    parser.add_argument("matrix_file", action="store",
                        help="The matrix file produced by verifyFiles. Each line must be formated as '<file_id>;<condition_id>;<value>'.")
    parser.add_argument("training_ratio", action="store", type=float,
                        help="The ratio of matrix elements that will be added to the training set. Has to be in [0,1].")
    parser.add_argument("approach", action="store", help="Prediction strategy: ALS, ALS-Bias or Bias.")
    parser.add_argument("dataset", action="store", help="Name of the dataset. Just to be used in the name of the output files")
    parser.add_argument("--predictions", "-p", action="store",
                        help="Text file where the predictions will be stored.")
    parser.add_argument("--random-ratio-error", "-r", action="store", type=float, default=0.01,
                        help="Maximum acceptable difference between target and effective training ratios. Defaults to 0.01.")
    parser.add_argument("sampling_method", action="store", 
                        help="Sampling method to use to build the training set.")
    parser.add_argument("--seed_number","-s",
                        help="set seed number")
    results = parser.parse_args() if args is None else parser.parse_args(args)          
    assert(results.training_ratio <=1 and results.training_ratio >=0), "Training ratio has to be in [0,1]."
    assert(results.approach in ["ALS", "ALS-Bias", "Bias"]), "Unknown approach: {0}".format(results.approach)
    # matrix file path, split fraction, all the ALS parameters (with default values)
    # see sim package on github
    try:
       seed = int(results.seed_number)
       rn.seed(seed)
       np.random.seed(seed)
    except:
       print("No seed")

    conf = SparkConf().setAppName("predict").setMaster("local")
    sc = SparkContext(conf = conf)
    spark = SparkSession.builder.appName("ALS_session").getOrCreate()
    lines = parse_file(results.matrix_file)
    assert(len(lines) > 0), "Matrix file is empty"
    training, test = random_split_2D(lines, results.training_ratio, results.random_ratio_error, results.sampling_method, results.dataset, results.approach)
    training_df = create_dataframe_from_line_list(sc,spark,training, True)
    file_mean_training = training_df.groupBy('ordered_file_id').agg(F.avg(training_df.val).alias("file_mean")) #If it's 1 or 0 means that it's constant 1 or zero
    test_df = create_dataframe_from_line_list(sc,spark,test, True)

    if results.approach =='ALS':
        als = ALS(maxIter=5, regParam=0.01, userCol="ordered_file_id", itemCol="subject", ratingCol="val", rank=50, nonnegative=True)
        try:
            als.setSeed(seed)
            model = als.fit(training_df)
        except:
            model = als.fit(training_df)
        latentFactors(model, results.sampling_method, results.dataset, results.approach, results.training_ratio)
      	predictions = model.transform(test_df)

    else:
        subject_mean_training = training_df.groupBy('subject').agg(F.avg(training_df.val).alias("subject_mean"))
        training_fin = training_df.join(subject_mean_training, ['subject']).join(file_mean_training, ['ordered_file_id'])
        global_mean_training = training_df.groupBy().agg(F.avg(training_df.val).alias("global_mean"))
        global_mean = global_mean_training.collect()[0][0]
        print ("global_mean", global_mean)
        training_fin = training_fin.withColumn('interaction', (training_fin['val'] - (training_fin['subject_mean'] + training_fin['file_mean']- global_mean)))
        als = ALS(maxIter=5, regParam=0.01, userCol="ordered_file_id", itemCol="subject", ratingCol="interaction", rank=50, nonnegative=True)
        try:
            als.setSeed(seed)
            model = als.fit(training_fin)
        except:
            model = als.fit(training_fin)
        latentFactors(model, results.sampling_method, results.dataset, results.approach, results.training_ratio)
        predictions = model.transform(test_df)    
        predictions_fin = predictions.join(subject_mean_training, ['subject']).join(file_mean_training, ['ordered_file_id'])
        if  results.approach == 'ALS-Bias':
            predictions_fin = predictions_fin.withColumn('fin_val', predictions_fin['prediction'] + training_fin['subject_mean'] + training_fin['file_mean'] - global_mean)
        else: #Bias
            predictions_fin = predictions_fin.withColumn('fin_val', training_fin['subject_mean'] + training_fin['file_mean'] - global_mean)
    
    if is_binary_matrix(lines): # assess the model    
        # prediction will be rounded to closest integer
        # TODO: check how the rounding can be done directly with the dataframe, to avoid converting to list
        if  results.approach in {'ALS-Bias','Bias'}:
            predictions_list = predictions_fin.rdd.map(lambda row: [ row.ordered_file_id, row.subject, row.val, row.fin_val]).collect()# ALS+BIAS or Just_BIAS
        else: 
            predictions_list = predictions.rdd.map(lambda row: [ row.ordered_file_id, row.subject,row.val, row.prediction]).collect() # ALS
        predictions_list = round_values(predictions_list)
        test_data_matrix = open(results.sampling_method+"_"+results.dataset+"_"+results.approach+"_"+str(results.training_ratio)+"_test_data_matrix.txt","w+")
        for i in range (len(predictions_list)):
            write_matrix(predictions_list[i],test_data_matrix)
        file_mean_list = file_mean_training.rdd.map(lambda row: [row.ordered_file_id, row.file_mean]).collect()
        accuracy, pure_accuracy = compute_accuracy(predictions_list, file_mean_list)
        sensitivity, specificity = sens_spec(predictions_list)
        print("Accuracy = " + str(accuracy))
        print("Accuracy ignores constant files = " + str(pure_accuracy))
        print("Sensitivity = " + str(sensitivity))
        print("Specificity = " + str(specificity))
        print("Accuracy of dummy classifier = " + str(compute_accuracy_dummy(lines)))
        predictions = create_dataframe_from_line_list(sc, spark, predictions_list, False)
        predictions.toPandas().to_csv('prediction.csv')
        if  results.approach in {'ALS-Bias','Bias'}:
            evaluator = RegressionEvaluator(metricName="rmse", labelCol="val", predictionCol="fin_val")
            rmse = evaluator.evaluate(predictions_fin)
        else:
            evaluator = RegressionEvaluator(metricName="rmse", labelCol="val", predictionCol="prediction")
            rmse = evaluator.evaluate(predictions)

        print("RMSE = " + str(rmse))
        
    if results.predictions:
        write_dataframe_to_text_file(predictions, results.predictions)   
if __name__ =='__main__':
       main() 
