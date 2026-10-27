"""
charts.py - Step 5: make the charts for the README

Usage:
    py src/charts.py --data data/sample_10k.csv
"""
import argparse
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                      # save to files, no pop-up windows
import matplotlib.pyplot as plt

from metrics import summarize, rate_campaigns

COLORS = {"Google": "#4285F4", "Facebook": "#1877F2", "Instagram": "#E1306C",
          "TikTok": "#111111", "YouTube": "#FF0000"}
RATING_COLORS = {"Excellent": "#2e9e5b", "Good": "#8bc34a",
                 "Weak": "#f0a030", "Losing money": "#d9342b"}

plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold"})


def save(name):
    plt.tight_layout()
    plt.savefig(f"charts/{name}.png", dpi=150)
    plt.close()
    print("saved charts/" + name + ".png")


def chart_roas(plat):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(plat.index, plat["ROAS"], color=[COLORS[p] for p in plat.index])
    ax.axhline(1, color="grey", linestyle="--", linewidth=1)
    ax.text(len(plat) - 0.5, 1.05, "break-even (ROAS = 1)", ha="right", color="grey", fontsize=9)
    for b, v in zip(bars, plat["ROAS"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f"{v:.2f}", ha="center", fontweight="bold")
    ax.set_title("ROAS by platform: Rs. earned for every Rs. 1 spent")
    ax.set_ylabel("ROAS")
    save("01_roas_by_platform")


def chart_clicks_vs_sales(plat):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    cols = [COLORS[p] for p in plat.index]
    axes[0].bar(plat.index, plat["CTR_%"], color=cols)
    axes[0].set_title("Click-through rate (CTR %)")
    axes[1].bar(plat.index, plat["CVR_%"], color=cols)
    axes[1].set_title("Conversion rate (CVR %)")
    for ax in axes:
        ax.tick_params(axis="x", rotation=30)
    fig.suptitle("Getting clicks is not the same as getting sales", fontweight="bold")
    save("02_ctr_vs_conversion")


def chart_monthly(df):
    df = df.copy()
    df["month"] = df["date"].str[:7]
    m = summarize(df, "month")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(m.index.str[5:], m["spend"] / 1e6, color="#c9d6ea")
    ax.set_ylabel("Ad spend (Rs. million)")
    ax.set_xlabel("Month of 2025")
    ax2 = ax.twinx()
    ax2.spines["right"].set_visible(True)
    ax2.plot(m.index.str[5:], m["ROAS"], color="#d9342b", marker="o", linewidth=2)
    ax2.set_ylabel("ROAS", color="#d9342b")
    ax2.set_ylim(0, 4)
    ax.set_title("Monthly spend (bars) and ROAS (line): March (Eid) and November peak")
    save("03_monthly_trend")


def chart_campaigns(camp):
    show = pd.concat([camp.head(5), camp.tail(5)])[::-1]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.barh(show.index, show["ROAS"], color=[RATING_COLORS[r] for r in show["performance"]])
    ax.axvline(1, color="grey", linestyle="--", linewidth=1)
    for i, v in enumerate(show["ROAS"]):
        ax.text(v + 0.05, i, f"{v:.2f}", va="center", fontsize=9)
    ax.set_title("5 best and 5 worst campaigns by ROAS")
    ax.set_xlabel("ROAS")
    save("04_best_worst_campaigns")


def chart_heatmap(df):
    g = df.groupby(["city", "platform"])[["spend", "revenue"]].sum()
    h = (g["revenue"] / g["spend"]).unstack()
    h = h.loc[h.mean(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    im = ax.imshow(h.values, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(h.columns)), h.columns)
    ax.set_yticks(range(len(h.index)), h.index)
    for i in range(h.shape[0]):
        for j in range(h.shape[1]):
            ax.text(j, i, f"{h.values[i, j]:.1f}", ha="center", va="center", fontsize=9)
    ax.set_title("ROAS by city and platform")
    fig.colorbar(im, ax=ax, label="ROAS")
    save("05_city_platform_heatmap")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/sample_10k.csv")
    args = ap.parse_args()

    os.makedirs("charts", exist_ok=True)
    df = pd.read_csv(args.data)
    plat = summarize(df, "platform").sort_values("ROAS", ascending=False)
    camp = rate_campaigns(summarize(df, "campaign")).sort_values("ROAS", ascending=False)

    chart_roas(plat)
    chart_clicks_vs_sales(plat)
    chart_monthly(df)
    chart_campaigns(camp)
    chart_heatmap(df)