"""
compare.py - Step 11: put the three tools side by side

Reads the three benchmark files, checks that every tool found the SAME
answer, prints the comparison tables and saves two charts.

Usage:
    py src/compare.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROWS = {"10K": 10_000, "100K": 100_000, "1M": 1_000_000, "10M": 10_000_000}
COLORS = {"Pandas": "#8c8c8c", "Pandas (optimized)": "#2ca02c",
          "MapReduce": "#1f77b4", "Spark": "#e25a1c"}

plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold"})

df = pd.concat([pd.read_csv("results/benchmark_pandas.csv"),
                pd.read_csv("results/benchmark_mapreduce.csv"),
                pd.read_csv("results/benchmark_spark.csv")], ignore_index=True)
df["rows"] = df["size"].map(ROWS)
df.to_csv("results/benchmark_all.csv", index=False)

# ---- 1) did every tool find the same answer? ----
print("=== CORRECTNESS CHECK (total revenue found by each tool) ===")
all_ok = True
for size in ROWS:
    vals = df[df["size"] == size]["total_revenue_check"]
    spread = (vals.max() - vals.min()) / vals.max()
    ok = spread < 1e-9
    all_ok &= ok
    print(f"{size:>4}: {'same answer' if ok else 'DIFFERENT'}  (difference {spread:.1e})")
print("ALL TOOLS AGREE" if all_ok else "WARNING: some tools disagree")

# ---- 2) tables ----
order = ["Pandas", "Pandas (optimized)", "MapReduce", "Spark"]
time_t = df.pivot(index="tool", columns="size", values="seconds").loc[order, list(ROWS)]
mem_t = df.pivot(index="tool", columns="size", values="extra_memory_MB").loc[order, list(ROWS)]
print("\n=== TIME (seconds) ===")
print(time_t)
print("\n=== EXTRA MEMORY (MB) ===")
print(mem_t)
print("\n=== FASTEST TOOL PER SIZE ===")
for size in ROWS:
    print(f"{size:>4}: {time_t[size].idxmin()} ({time_t[size].min():.2f} s)")


# ---- 3) charts ----
def line_chart(table, ylabel, title, name, note=None):
    fig, ax = plt.subplots(figsize=(8.5, 5))
    for tool in order:
        ax.plot([ROWS[s] for s in ROWS], table.loc[tool].clip(lower=1 if "MB" in ylabel else 0.01),
                marker="o", linewidth=2, label=tool, color=COLORS[tool])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(list(ROWS.values()), list(ROWS))
    ax.set_xlabel("Number of rows")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    if note:
        fig.text(0.01, 0.01, note, fontsize=8, color="grey")
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    plt.savefig(f"charts/{name}.png", dpi=150)
    plt.close()
    print("saved charts/" + name + ".png")


print()
line_chart(time_t, "Seconds (log scale)", "Time to run the same job: Pandas vs MapReduce vs Spark",
           "06_benchmark_time")
line_chart(mem_t, "Extra memory in MB (log scale)", "Extra memory used while running the job",
           "07_benchmark_memory",
           note="Spark's engine memory (started before the job) is not included in its line.")