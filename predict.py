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
from random import random, randint

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

def create_dataframe_from_line_list(sc, ss, line_list):
    assert(len(line_list[0])==3 or len(line_list[1])==4)
    if(len(line_list[0])==3):
        rdd=sc.parallelize(line_list).map(lambda line:Row(subjectFile=long(line[0]), conPair=long(line[1]), val=long(line[2])))
    else:
        rdd=sc.parallelize(line_list).map(lambda line:Row(subjectFile=long(line[0]), conPair=long(line[1]), val=long(line[2]), prediction=float(line[3])))
    return ss.createDataFrame(rdd)

def n_conditions_files(line_list):
    max_cond_id = 0
    max_file_id = 0
    for line in line_list:
        if line[1] > max_cond_id:
            max_cond_id = line[1]
        if line[0] > max_file_id:
            max_file_id = line[0]
    return max_cond_id + 1, max_file_id + 1

def count_occurrences(file_id, line_list):
    return len([line for line in line_list if line[0] == file_id])

def random_split(lines, training_ratio, max_diff):
    training = []
    test = []
    n_cond, n_files = n_conditions_files(lines)
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
            lines.append([int(elements[0]), int(elements[1]), int(elements[2])])
    return lines

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
    results = parser.parse_args() if args is None else parser.parse_args(args)          
    assert(results.training_ratio <=1 and results.training_ratio >=0), "Training ratio has to be in [0,1]."

    # matrix file path, split fraction, all the ALS parameters (with default values)
    # see sim package on github
  
    conf = SparkConf().setAppName("predict").setMaster("local")
    sc = SparkContext(conf=conf)

    spark = SparkSession.builder.appName("ALS_session").getOrCreate()

    lines = parse_file(results.matrix_file)
    assert(len(lines) > 0), "Matrix file is empty"

    training, test = random_split(lines, results.training_ratio, results.random_ratio_error)

    training_df = create_dataframe_from_line_list(sc,spark,training)
    test_df = create_dataframe_from_line_list(sc,spark,test)

    als = ALS(maxIter=5, regParam=0.01, userCol="subjectFile", itemCol="conPair", ratingCol="val")
    model = als.fit(training_df)  
    predictions = model.transform(test_df)
    
    if is_binary_matrix(lines):
        # prediction will be rounded to closest integer
        # TODO: check how the rounding can be done directly with the dataframe, to avoid converting to list
        predictions_list = predictions.rdd.map(lambda row: [ row.subjectFile, row.conPair,
                                                             row.val, row.prediction]).collect()
        predictions_list = round_values(predictions_list)
        accuracy = compute_accuracy(predictions_list)
        print("Accuracy = " + str(accuracy))
        print("Accuracy of dummy classifier = " + str(compute_accuracy_dummy(lines)))
        predictions = create_dataframe_from_line_list(sc, spark, predictions_list)
    else:
        evaluator = RegressionEvaluator(metricName="rmse", labelCol="val", predictionCol="prediction")
        rmse = evaluator.evaluate(predictions)
        print("RMSE = " + str(rmse))
        
    if results.predictions:
        write_dataframe_to_text_file(predictions, results.predictions)   

   
if __name__ =='__main__':
       main() 
