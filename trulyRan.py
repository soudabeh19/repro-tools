
from __future__ import print_function
import os
import sys
if sys.version >= '3':
    long = int

from pyspark.sql import SparkSession
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark.sql import Row


if __name__ == "__main__":

    # Use argparse to get arguments of your script:
    # matrix file path, split fraction, all the ALS parameters (with default values)
    # see sim package on github

    spark = SparkSession\
        .builder\
        .appName("ALS_session")\
        .getOrCreate()
    
    spark = SparkSession.builder.appName("ALS_session").getOrCreate()
#    example_file_path = "/home/soudabeh/Documents/Bigdatateam/repro-tools/matrix-nonsense.txt"
    example_file_path = "/home/soudabeh/Documents/Bigdatateam/repro-tools/matrix.txt"

    # Matrix parsing 
    lines = spark.read.text("file://"+example_file_path).rdd
    parts = lines.map(lambda row: row.value.split(";"))    
#   differneceRDD=parts.map(lambda p:Row(subjectFile=long(p[0]), con1=long(p[1]), con2=long(p[2]), con3=long(p[3])))
    differenceRDD=parts.map(lambda p:Row(subjectFile=long(p[0]), conPair=long(p[1]), val=long(p[2])))
    differences=spark.createDataFrame(differenceRDD)

    print("# differences")
    differences.show(differences.count())

  
    (training, test) = differences.randomSplit([0.95, 0.05])
    print ("# training")
    training.show()#training.count())
    print("# testing")
    test.show()#test.count())

#    als = ALS(maxIter=5, regParam=0.01, userCol="con1", itemCol="con2", ratingCol="con3")    
    als = ALS(maxIter=5, regParam=0.01, userCol="subjectFile", itemCol="conPair", ratingCol="val")
    model = als.fit(training)
    
    
    predictions = model.transform(test)
    print("# predictions =  ",predictions.count())
    predictions.show()#predictions.count())
    
    #    evaluator = RegressionEvaluator(metricName="rmse", labelCol="con3", predictionCol="prediction")
    evaluator = RegressionEvaluator(metricName="rmse", labelCol="val", predictionCol="prediction")
    rmse = evaluator.evaluate(predictions)
    print("RMSE = " + str(rmse))
   
    spark.stop()
