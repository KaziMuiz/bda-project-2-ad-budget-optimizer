"""
bench_pandas.py - Step 7: the benchmark job, run with Pandas

THE JOB (identical for every tool we compare):
    read the CSV file -> for each platform add up impressions, clicks,
    spend, conversions, revenue -> calculate ROAS

Usage:
    py src/bench_pandas.py
"""
import os
import pandas as pd

from bench_utils import measure

SUM_COLS = ["impressions", "clicks", "spend", "conversions", "revenue"]

FILES = {
    "10K": "data/sample_10k.csv",
    "100K": "data/ads_100k.csv",
    "1M": "data/ads_1m.csv",
    "10M": "data/ads_10m.csv",
}


def job_pandas(path):
    """Plain Pandas: read every column, then group."""
    df = pd.read_csv(path)
    g = df.groupby("platform")[SUM_COLS].sum()
    g["ROAS"] = g["revenue"] / g["spend"]
    return g


def job_pandas_optimized(path):
    """Smarter Pandas: read only the 6 columns we need, with small data types."""
    dtypes = {"platform": "category", "impressions": "int32", "clicks": "int32",
              "conversions": "int32", "spend": "float64", "revenue": "float64"}
    df = pd.read_csv(path, usecols=list(dtypes), dtype=dtypes)
    g = df.groupby("platform", observed=True)[SUM_COLS].sum()
    g["ROAS"] = g["revenue"] / g["spend"]
    return g


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for size, path in FILES.items():
        for name, job in [("Pandas", job_pandas), ("Pandas (optimized)", job_pandas_optimized)]:
            result, seconds, mb = measure(job, path)
            check = result["revenue"].sum()
            rows.append({"size": size, "tool": name, "seconds": round(seconds, 2),
                         "extra_memory_MB": round(mb), "total_revenue_check": round(check, 2)})
            print(f"{size:>4} | {name:<20} | {seconds:7.2f} s | {mb:8.0f} MB")

    out = pd.DataFrame(rows)
    out.to_csv("results/benchmark_pandas.csv", index=False)
    print("\nSaved results/benchmark_pandas.csv")
    print(out.to_string(index=False))