
from __future__ import print_function
from argparse import ArgumentParser
import os, shutil, sys
if sys.version >= '3':
    long = int
import findspark
findspark.init()
from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession, Row
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from random import random, randint
from predict import random_split,parse_file
from predict import compute_accuracy
from predict import compute_accuracy_dummy

def  test_random_split():
   training,test=random_split(parse_file_lines(),.6,"test/test_matrix.txt")
   print(training,test) 

def parse_file_lines():
    return parse_file([[0,0,1],[1,0,1],[2,0,0],[3,1,0],[4,1,1],[5,1,0],[6,2,0],[7,2,1],[8,2,1]])#"test/matrix.txt")

#def test_run():
 # command_line_string ="predict.py test/matrix.txt o.6"
#  return_value,output = commands.getstatusoutput(command_line_string)
 # assert not filecmp.cmp("test/fileDiff_differences_subject_total.txt","test/differences-ref.txt")
