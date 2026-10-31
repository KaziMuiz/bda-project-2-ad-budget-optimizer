"""
engine.py - Step 13: the Marketing Budget Recommendation Engine

Question: "Where should we spend the next Rs. 1 million?"

1. Learn how each platform reacts to more money (curves from Step 12)
2. Check that the curves can predict months they have not seen
3. Search for the split that earns the most revenue
4. Compare it with two simple plans (equal split, split by ROAS)

Usage:
    py src/engine.py --budget 1000000
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from response_curves import fit_platform

COLORS = {"Equal split": "#b0b0b0", "Split by ROAS": "#6c8ebf", "Engine (optimized)": "#2e9e5b"}


def expected_revenue(S, a, beta, n):
    """n ad sets share the platform budget S. Each gets S/n and earns a*(S/n)^beta."""
    return n * a * (S / n) ** beta


def learn_curves(df):
    curves = {}
    for platform, g in df.groupby("platform"):
        _, beta, a, _ = fit_platform(g)
        curves[platform] = dict(a=a, beta=beta, n=len(g) / 12)    # n = ad sets per month
    return pd.DataFrame(curves).T


def model_check(df):
    """Learn from Jan-Aug only, then predict the revenue of Sep-Dec."""
    train, test = df[df["date"] < "2025-09-01"], df[df["date"] >= "2025-09-01"]
    curves = learn_curves(train)
    rows = []
    for p, g in test.groupby("platform"):
        predicted = (curves.loc[p, "a"] * g["spend"] ** curves.loc[p, "beta"]).sum()
        actual = g["revenue"].sum()
        rows.append({"platform": p, "predicted_revenue": round(predicted),
                     "actual_revenue": round(actual),
                     "error_%": round((predicted - actual) / actual * 100, 1)})
    return pd.DataFrame(rows)


def find_best_split(budget, a, beta, n, lo, hi):
    k = len(a)
    f = lambda x: -expected_revenue(x * budget, a, beta, n).sum() / budget
    res = minimize(f, np.full(k, 1 / k), method="SLSQP", bounds=[(lo, hi)] * k,
                   constraints={"type": "eq", "fun": lambda x: x.sum() - 1})
    return res.x


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/sample_10k.csv")
    ap.add_argument("--budget", type=float, default=1_000_000)
    ap.add_argument("--min_share", type=float, default=0.05, help="every platform gets at least this share")
    ap.add_argument("--max_share", type=float, default=0.50, help="no platform gets more than this share")
    args = ap.parse_args()

    os.makedirs("results", exist_ok=True)
    df = pd.read_csv(args.data)
    B = args.budget

    # ---- 1) learn ----
    curves = learn_curves(df)
    platforms = list(curves.index)
    a, beta, n = (curves[c].values.astype(float) for c in ("a", "beta", "n"))
    hist = df.groupby("platform")[["spend", "revenue"]].sum()
    hist_roas = (hist["revenue"] / hist["spend"]).loc[platforms].values

    # ---- 2) can the curves predict unseen months? ----
    print("=== MODEL CHECK: learn from Jan-Aug, predict Sep-Dec ===")
    print(model_check(df).to_string(index=False))
    print("(Sep-Dec include Black Friday and other sales, and YouTube has the fewest rows, so some error is expected)\n")

    # ---- 3) search for the best split ----
    best = find_best_split(B, a, beta, n, args.min_share, args.max_share)
    plans = {
        "Equal split": np.full(len(platforms), 1 / len(platforms)),
        "Split by ROAS": hist_roas / hist_roas.sum(),
        "Engine (optimized)": best,
    }

    # ---- 4) compare ----
    summary, split_table = [], pd.DataFrame(index=platforms)
    for name, share in plans.items():
        rev = expected_revenue(share * B, a, beta, n).sum()
        summary.append({"plan": name, "expected_revenue": round(rev), "expected_ROAS": round(rev / B, 2)})
        split_table[name] = (share * 100).round(1)
    summary = pd.DataFrame(summary)

    print(f"=== RECOMMENDATION FOR Rs. {B:,.0f} (one month) ===")
    print("Share of the budget in % per plan:")
    print(split_table.to_string())
    print("\nExpected result of each plan:")
    print(summary.to_string(index=False))

    base = summary.loc[summary["plan"] == "Equal split", "expected_revenue"].iloc[0]
    eng = summary.loc[summary["plan"] == "Engine (optimized)", "expected_revenue"].iloc[0]
    print(f"\nEngine vs equal split: {(eng / base - 1) * 100:+.1f}% revenue")

    # ---- 5) why is this split best? ----
    S = best * B
    marginal = a * beta * (S / n) ** (beta - 1)
    per_set = S / n
    q02, q98 = df["spend"].quantile([0.02, 0.98])
    detail = pd.DataFrame({"budget_Rs": S.round(), "share_%": (best * 100).round(1),
                           "extra_revenue_per_extra_Rs": marginal.round(2),
                           "budget_per_ad_set_Rs": per_set.round()}, index=platforms)
    print("\n=== WHY THIS SPLIT ===")
    print(detail.to_string())
    print("Platforms that are not at the 5% / 50% limits earn about the same from the NEXT rupee.")
    if ((per_set < q02) | (per_set > q98)).any():
        print(f"WARNING: some per-ad-set budgets are outside the range seen in the data "
              f"(Rs. {q02:,.0f} to {q98:,.0f}), so treat those numbers with care.")

    # ---- 6) save + chart ----
    out = split_table.copy()
    out["recommended_budget_Rs"] = S.round()
    out.to_csv("results/recommendation.csv")
    summary.to_csv("results/plan_comparison.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
    x = np.arange(len(platforms))
    w = 0.27
    for i, name in enumerate(plans):
        axes[0].bar(x + (i - 1) * w, split_table[name], w, label=name, color=COLORS[name])
    axes[0].set_xticks(x, platforms)
    axes[0].set_ylabel("Share of budget (%)")
    axes[0].set_title(f"How to split Rs. {B / 1e6:g} million")
    axes[0].legend()
    axes[1].bar(summary["plan"], summary["expected_revenue"] / 1e6,
                color=[COLORS[p] for p in summary["plan"]])
    axes[1].set_ylabel("Expected revenue (Rs. million)")
    axes[1].set_title("Expected revenue of each plan")
    axes[1].tick_params(axis="x", rotation=15)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig("charts/09_recommendation.png", dpi=150)
    print("\nsaved charts/09_recommendation.png, results/recommendation.csv, results/plan_comparison.csv")