"""
generate_data.py  -  Simulated digital-advertising data (Project 2)

Usage:
    python src/generate_data.py --rows 10000 --out data/sample_10k.csv

Each row = one campaign, on one day, for one audience segment
(age + gender + city + device).
"""
import argparse
import numpy as np
import pandas as pd

# ---------------------------------------------------------------
# 1. PLATFORM "PERSONALITIES"
#    cpm  = Rs per 1000 impressions      ctr = clicks / impressions
#    cvr  = conversions / clicks         aov = Rs per order
#    beta = diminishing returns (lower = saturates faster)
# ---------------------------------------------------------------
PLATFORMS = {
    "Facebook":  dict(code="FB",  share=0.24, cpm=250, ctr=0.011, cvr=0.012, aov=4500, beta=0.85,
                      age=[.15, .30, .25, .18, .12], gender=[.50, .50], device=[.85, .12, .03]),
    "Instagram": dict(code="IG",  share=0.22, cpm=320, ctr=0.010, cvr=0.014, aov=5200, beta=0.80,
                      age=[.30, .38, .20, .08, .04], gender=[.40, .60], device=[.93, .05, .02]),
    "Google":    dict(code="GGL", share=0.26, cpm=900, ctr=0.030, cvr=0.018, aov=5500, beta=0.70,
                      age=[.15, .32, .28, .15, .10], gender=[.55, .45], device=[.68, .28, .04]),
    "TikTok":    dict(code="TT",  share=0.16, cpm=150, ctr=0.016, cvr=0.004, aov=3800, beta=0.92,
                      age=[.50, .32, .12, .04, .02], gender=[.45, .55], device=[.97, .02, .01]),
    "YouTube":   dict(code="YT",  share=0.12, cpm=200, ctr=0.006, cvr=0.010, aov=5000, beta=0.88,
                      age=[.25, .30, .22, .13, .10], gender=[.62, .38], device=[.75, .15, .10]),
}

# Campaign themes: (ctr multiplier, conversion multiplier)
THEMES = {
    "Brand_Awareness":  (1.3, 0.5),
    "Retargeting":      (0.9, 1.8),
    "New_Arrivals":     (1.1, 1.0),
    "Summer_Clearance": (1.2, 1.1),
    "Back_to_School":   (1.0, 0.9),
    "Winter_Collection": (1.0, 1.0),
    "Flash_Sale":       (1.3, 1.2),
    "Eid_Collection":   (1.1, 1.3),
}

# ---------------------------------------------------------------
# 2. AUDIENCE SEGMENTS
# ---------------------------------------------------------------
AGES = np.array(["18-24", "25-34", "35-44", "45-54", "55+"])
AGE_CVR = np.array([0.80, 1.10, 1.20, 1.10, 0.90])   # who converts better
AGE_AOV = np.array([0.70, 1.00, 1.20, 1.20, 1.10])   # who spends more per order

GENDERS = np.array(["Male", "Female"])

CITIES = np.array(["Karachi", "Lahore", "Islamabad", "Rawalpindi",
                   "Faisalabad", "Multan", "Peshawar", "Quetta"])
CITY_P = [.28, .26, .10, .08, .09, .07, .08, .04]
CITY_AOV = np.array([1.00, 1.05, 1.25, 1.00, 0.90, 0.85, 0.85, 0.80])

DEVICES = np.array(["Mobile", "Desktop", "Tablet"])
DEVICE_CVR = np.array([0.95, 1.25, 1.00])

# ---------------------------------------------------------------
# 3. SEASONS (dates are approximate): start, end, spend x, conversion x
# ---------------------------------------------------------------
SEASONS = [
    ("2025-03-01", "2025-03-29", 1.25, 1.15),   # Ramadan
    ("2025-03-24", "2025-03-31", 1.50, 1.40),   # Eid ul Fitr sale
    ("2025-06-01", "2025-06-07", 1.40, 1.30),   # Eid ul Adha sale
    ("2025-08-08", "2025-08-14", 1.20, 1.20),   # Independence Day sale
    ("2025-11-08", "2025-11-11", 1.50, 1.40),   # 11.11 sale
    ("2025-11-24", "2025-11-30", 1.60, 1.50),   # Black Friday
    ("2025-12-10", "2025-12-12", 1.40, 1.30),   # 12.12 sale
]

REF_SPEND = 2000   # typical spend per row (Rs)


def generate(n_rows, seed=42):
    rng = np.random.default_rng(seed)

    # calendar with seasonal boosts
    days = pd.date_range("2025-01-01", "2025-12-31")
    spend_mult = pd.Series(1.0, index=days)
    cvr_mult = pd.Series(1.0, index=days)
    for start, end, s, c in SEASONS:
        spend_mult.loc[start:end] = s
        cvr_mult.loc[start:end] = c

    names = list(PLATFORMS)
    counts = rng.multinomial(n_rows, [PLATFORMS[p]["share"] for p in names])
    parts = []

    for name, n in zip(names, counts):
        P = PLATFORMS[name]

        # 6 campaigns per platform, each with a hidden "quality"
        themes = rng.choice(list(THEMES), size=6, replace=False)
        quality = rng.lognormal(0, 0.15, size=6)
        ci = rng.integers(0, 6, size=n)
        campaign = np.array([f"{P['code']}_{t}" for t in themes])[ci]
        ctr_m = np.array([THEMES[t][0] for t in themes])[ci]
        cvr_m = np.array([THEMES[t][1] for t in themes])[ci] * quality[ci]

        # date + season
        di = rng.integers(0, len(days), size=n)
        s_m = spend_mult.values[di]
        c_m = cvr_mult.values[di]

        # audience
        ai = rng.choice(5, size=n, p=P["age"])
        gi = rng.choice(2, size=n, p=P["gender"])
        yi = rng.choice(8, size=n, p=CITY_P)
        vi = rng.choice(3, size=n, p=P["device"])

        # money funnel: spend -> impressions -> clicks -> conversions -> revenue
        spend = rng.lognormal(np.log(REF_SPEND), 0.9, n) * s_m
        cpm = P["cpm"] * rng.lognormal(0, 0.15, n)
        impressions = (spend / cpm * 1000).astype(np.int64)

        ctr = np.clip(P["ctr"] * ctr_m * rng.lognormal(0, 0.10, n), 0, 0.2)
        clicks = rng.binomial(impressions, ctr)

        saturation = (spend / REF_SPEND) ** (P["beta"] - 1)   # diminishing returns
        p_conv = np.clip(P["cvr"] * cvr_m * c_m * AGE_CVR[ai] * DEVICE_CVR[vi] * saturation, 0, 0.3)
        conversions = rng.binomial(clicks, p_conv)

        revenue = (conversions * P["aov"] * CITY_AOV[yi] * AGE_AOV[ai]
                   * rng.lognormal(0, 0.20, n))

        parts.append(pd.DataFrame({
            "date": days[di],
            "campaign": campaign,
            "platform": name,
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend.round(2),
            "conversions": conversions,
            "revenue": revenue.round(2),
            "age": AGES[ai],
            "gender": GENDERS[gi],
            "city": CITIES[yi],
            "device": DEVICES[vi],
        }))

    df = pd.concat(parts).sort_values("date").reset_index(drop=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df


CHUNK = 1_000_000   # rows made at a time, so a laptop never runs out of memory


def write_csv(n_rows, out, seed=42, chunk=CHUNK):
    """Generate n_rows in chunks and append each chunk to one CSV file."""
    done, part = 0, 0
    while done < n_rows:
        n = min(chunk, n_rows - done)
        df = generate(n, seed + part)
        df.to_csv(out, mode="w" if part == 0 else "a", header=(part == 0), index=False)
        done += n
        part += 1
        print(f"  wrote {done:,} / {n_rows:,} rows")


if __name__ == "__main__":
    import os
    import time

    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=10_000)
    ap.add_argument("--out", default="data/sample_10k.csv")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    start = time.time()
    write_csv(args.rows, args.out, args.seed)
    size_mb = os.path.getsize(args.out) / 1024 / 1024
    print(f"Saved {args.rows:,} rows to {args.out}  ({size_mb:.1f} MB, {time.time() - start:.1f} seconds)")