"""
metrics.py - Step 4: calculate the marketing metrics

Usage:
    py src/metrics.py --data data/sample_10k.csv
"""
import argparse
import os
import numpy as np
import pandas as pd

SUM_COLS = ["impressions", "clicks", "spend", "conversions", "revenue"]


def add_ratios(g):
    """g holds SUMMED columns. Ratios are always computed from the sums."""
    g["CTR_%"] = g["clicks"] / g["impressions"] * 100           # click-through rate
    g["CPC"] = g["spend"] / g["clicks"]                          # cost per click
    g["CPA"] = g["spend"] / g["conversions"].replace(0, np.nan)  # cost per acquisition
    g["CVR_%"] = g["conversions"] / g["clicks"] * 100            # conversion rate
    g["ROAS"] = g["revenue"] / g["spend"]                        # return on ad spend
    g["profit"] = g["revenue"] - g["spend"]                      # revenue minus ad cost
    return g


def summarize(df, by):
    g = df.groupby(by)[SUM_COLS].sum()
    return add_ratios(g)


def rate_campaigns(g):
    g["performance"] = pd.cut(g["ROAS"], [-np.inf, 1, 2, 3, np.inf],
                              labels=["Losing money", "Weak", "Good", "Excellent"],
                              right=False)
    return g


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/sample_10k.csv")
    args = ap.parse_args()

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)

    df = pd.read_csv(args.data)
    os.makedirs("results", exist_ok=True)

    # 1) whole company
    total = add_ratios(df[SUM_COLS].sum().to_frame().T)
    print("=== OVERALL ===")
    print(total.round(2).to_string(index=False))

    # 2) by platform
    plat = summarize(df, "platform").sort_values("ROAS", ascending=False)
    print("\n=== BY PLATFORM ===")
    print(plat.round(2))
    plat.round(2).to_csv("results/platform_metrics.csv")

    # 3) by campaign
    camp = rate_campaigns(summarize(df, "campaign")).sort_values("ROAS", ascending=False)
    cols = ["spend", "revenue", "CPA", "ROAS", "performance"]
    print("\n=== TOP 5 CAMPAIGNS (by ROAS) ===")
    print(camp[cols].head(5).round(2))
    print("\n=== BOTTOM 5 CAMPAIGNS ===")
    print(camp[cols].tail(5).round(2))
    print("\nCampaigns per rating:")
    print(camp["performance"].value_counts())
    camp.round(2).to_csv("results/campaign_performance.csv")

    print("\nSaved: results/platform_metrics.csv and results/campaign_performance.csv")