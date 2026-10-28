"""
bench_mapreduce.py - Step 8: the SAME benchmark job, done the MapReduce way

MapReduce = 4 phases:
    SPLIT   cut the big file into pieces (byte ranges)
    MAP     every worker reads its own piece and, for each row,
            emits  (platform -> impressions, clicks, spend, conversions, revenue)
            (a small "combiner" adds up rows inside the worker first)
    SHUFFLE collect everything with the same key (platform) together
    REDUCE  add up each platform's numbers -> final answer

Usage:
    py src/bench_mapreduce.py
"""
import csv
import os
from collections import defaultdict
from multiprocessing import Pool

from bench_utils import measure

FILES = {
    "10K": "data/sample_10k.csv",
    "100K": "data/ads_100k.csv",
    "1M": "data/ads_1m.csv",
    "10M": "data/ads_10m.csv",
}


# ---------------- SPLIT ----------------
def split_file(path, n_pieces):
    size = os.path.getsize(path)
    step = max(size // n_pieces, 1)
    return [(path, s, min(s + step, size)) for s in range(0, size, step)]


# ---------------- MAP (+ combiner) ----------------
def map_piece(piece):
    path, start, end = piece
    local = {}                                   # combiner: totals inside this worker
    with open(path, "rb") as f:
        if start == 0:
            f.readline()                         # skip the header line
        else:
            f.seek(start - 1)
            f.readline()                         # skip the half line (it belongs to the previous piece)
        while f.tell() < end:
            line = f.readline()
            if not line:
                break
            p = line.split(b",", 8)
            key = p[2]                                            # platform
            vals = (int(p[3]), int(p[4]), float(p[5]), int(p[6]), float(p[7]))   # emitted value
            acc = local.get(key)
            if acc is None:
                local[key] = list(vals)
            else:
                acc[0] += vals[0]
                acc[1] += vals[1]
                acc[2] += vals[2]
                acc[3] += vals[3]
                acc[4] += vals[4]
    return local


# ---------------- SHUFFLE ----------------
def shuffle(mapper_outputs):
    groups = defaultdict(list)
    for out in mapper_outputs:
        for key, vals in out.items():
            groups[key].append(vals)
    return groups


# ---------------- REDUCE ----------------
def reduce_key(key, list_of_vals):
    totals = [sum(col) for col in zip(*list_of_vals)]
    impressions, clicks, spend, conversions, revenue = totals
    return key.decode(), {"impressions": impressions, "clicks": clicks, "spend": spend,
                          "conversions": conversions, "revenue": revenue,
                          "ROAS": revenue / spend}


def job_mapreduce(path):
    workers = os.cpu_count() or 2
    pieces = split_file(path, workers * 4)
    with Pool(workers) as pool:
        mapped = pool.map(map_piece, pieces)             # MAP phase, in parallel
    groups = shuffle(mapped)                              # SHUFFLE phase
    return dict(reduce_key(k, v) for k, v in groups.items())   # REDUCE phase


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    rows = []
    for size, path in FILES.items():
        result, seconds, mb = measure(job_mapreduce, path)
        check = sum(v["revenue"] for v in result.values())
        rows.append({"size": size, "tool": "MapReduce", "seconds": round(seconds, 2),
                     "extra_memory_MB": round(mb), "total_revenue_check": round(check, 2)})
        print(f"{size:>4} | MapReduce | {seconds:7.2f} s | {mb:8.0f} MB")

    with open("results/benchmark_mapreduce.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("\nSaved results/benchmark_mapreduce.csv")
    for r in rows:
        print(r)