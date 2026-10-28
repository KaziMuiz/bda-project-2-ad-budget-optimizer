"""
spark_check.py - Step 9: does Spark work on this laptop?
"""
import os
import sys

# Windows fix: make Spark use the same Python that runs this file
os.environ["PYSPARK_PYTHON"] = sys.executable

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.master("local[*]").appName("spark-check").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

df = spark.read.csv("data/sample_10k.csv", header=True, inferSchema=True)
print("rows:", df.count())

df.groupBy("platform").agg(
    F.sum("spend").alias("spend"),
    F.sum("revenue").alias("revenue"),
).show()

spark.stop()