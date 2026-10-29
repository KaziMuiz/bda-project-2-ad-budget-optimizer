"""
response_curves.py - Step 12: learn how each platform reacts to MORE money

Question: if one ad set gets a bigger budget, does it earn proportionally more?
We fit, for every platform, the curve
        revenue = a * spend ^ beta
beta = 1    -> double the money, double the revenue (no slowdown)
beta < 1    -> double the money, LESS than double the revenue (diminishing returns)

Usage:
    py src/response_curves.py --data data/sample_10k.csv
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from generate_data import PLATFORMS      # only used to compare with the hidden rules we planted

COLORS = {"Google": "#34A853", "Facebook": "#1877F2", "Instagram": "#E1306C",
          "TikTok": "#111111", "YouTube": "#FF0000"}
N_BINS = 10

plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold"})


def fit_platform(g):
    """Group the ad sets into 10 spend sizes (small to big), average each group,
    then draw the best straight line through log(spend) vs log(revenue)."""
    g = g.copy()
    g["size_group"] = pd.qcut(g["spend"], N_BINS, duplicates="drop")
    b = g.groupby("size_group", observed=True)[["spend", "revenue"]].mean()
    x, y = np.log(b["spend"]), np.log(b["revenue"])
    beta, log_a = np.polyfit(x, y, 1)
    r2 = 1 - ((y - (beta * x + log_a)) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return b, beta, np.exp(log_a), r2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/sample_10k.csv")
    args = ap.parse_args()

    os.makedirs("results", exist_ok=True)
    df = pd.read_csv(args.data)

    rows, fits = [], {}
    for platform, g in df.groupby("platform"):
        b, beta, a, r2 = fit_platform(g)
        fits[platform] = (b, beta, a)
        rows.append({"platform": platform, "beta": round(beta, 3), "a": a,
                     "fit_quality_R2": round(r2, 3),
                     "ad_sets_per_month": round(len(g) / 12),
                     "planted_beta": PLATFORMS[platform]["beta"]})
    out = pd.DataFrame(rows).sort_values("beta")
    out.to_csv("results/response_curves.csv", index=False)

    print("=== HOW EACH PLATFORM REACTS TO MORE MONEY ===")
    print("beta close to 1 = keeps paying well when you spend more")
    print("beta lower      = saturates quickly (extra rupees earn less and less)\n")
    print(out.to_string(index=False))

    # chart: ROAS of one ad set vs the size of its budget
    fig, ax = plt.subplots(figsize=(8.5, 5))
    xs = np.logspace(np.log10(df["spend"].quantile(0.02)), np.log10(df["spend"].quantile(0.98)), 50)
    for platform, (b, beta, a) in fits.items():
        ax.scatter(b["spend"], b["revenue"] / b["spend"], color=COLORS[platform], s=25)
        ax.plot(xs, a * xs ** (beta - 1), color=COLORS[platform], linewidth=2, label=platform)
    ax.set_xscale("log")
    ax.set_xlabel("Budget of one ad set (Rs., log scale)")
    ax.set_ylabel("ROAS of that ad set")
    ax.set_title("Bigger budget in one ad set means a lower ROAS")
    ax.legend()
    plt.tight_layout()
    plt.savefig("charts/08_diminishing_returns.png", dpi=150)
    print("\nsaved charts/08_diminishing_returns.png and results/response_curves.csv")