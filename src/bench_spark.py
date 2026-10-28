"""
bench_spark.py - Step 10: the SAME benchmark job, run with Spark

Usage:
    py src/bench_spark.py
"""
import csv
import os
import sys
import time

import psutil

os.environ["PYSPARK_PYTHON"] = sys.executable    # Windows fix

from pyspark.sql import SparkSession, functions as F

from bench_utils import measure

SUM_COLS = ["impressions", "clicks", "spend", "conversions", "revenue"]

FILES = {
    "10K": "data/sample_10k.csv",
    "100K": "data/ads_100k.csv",
    "1M": "data/ads_1m.csv",
    "10M": "data/ads_10m.csv",
}

# telling Spark the column types up front saves it a slow extra pass over the file
SCHEMA = ("date string, campaign string, platform string, impressions int, clicks int, "
          "spend double, conversions int, revenue double, age string, gender string, "
          "city string, device string")


def job_spark(spark, path):
    df = spark.read.csv(path, header=True, schema=SCHEMA)
    g = df.groupBy("platform").agg(*[F.sum(c).alias(c) for c in SUM_COLS])
    g = g.withColumn("ROAS", F.col("revenue") / F.col("spend"))
    return g.collect()


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)

    t0 = time.perf_counter()
    spark = (SparkSession.builder.master("local[*]").appName("bench")
             .config("spark.ui.enabled", "false").getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    startup = time.perf_counter() - t0
    me = psutil.Process()
    engine_mb = me.memory_info().rss
    for child in me.children(recursive=True):
        try:
            engine_mb += child.memory_info().rss
        except psutil.Error:
            pass
    print(f"Spark engine started in {startup:.1f} s using {engine_mb / 1024 / 1024:.0f} MB "
          f"(both NOT counted in the timings below)")

    job_spark(spark, FILES["10K"])               # warm-up run, not recorded

    rows = []
    for size, path in FILES.items():
        result, seconds, mb = measure(job_spark, spark, path)
        check = sum(r["revenue"] for r in result)
        rows.append({"size": size, "tool": "Spark", "seconds": round(seconds, 2),
                     "extra_memory_MB": round(mb), "total_revenue_check": round(check, 2)})
        print(f"{size:>4} | Spark | {seconds:7.2f} s | {mb:8.0f} MB")
    spark.stop()

    with open("results/benchmark_spark.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("\nSaved results/benchmark_spark.csv")
    for r in rows:
        print(r)