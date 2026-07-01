# %% T4_04 — Stable Points (label=0) Generation
# Generates spatially-constrained stable points and produces the
# final landslide_labels.csv deliverable for T1.
#
# Design:
#   - Random sampling within study area
#   - Minimum 500 m from any known landslide point (prevents label leakage)
#   - Balanced 50/50 with label=1 count
#   - Shuffled and saved as landslide_labels.csv

import os
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# ── CHANGE THIS ─────────────────────────────────────────────────────────
BASE_DIR = r"D:\Games_krish\T4 1"
# ────────────────────────────────────────────────────────────────────────

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_DIR    = os.path.join(BASE_DIR, "data", "outputs")
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

WEST, SOUTH, EAST, NORTH = 78.2, 30.0, 80.0, 31.0
MIN_DIST_M   = 500    # metres — minimum distance from any landslide
TARGET       = 500    # target stable points (will be capped to label=1 count)
RANDOM_SEED  = 42
np.random.seed(RANDOM_SEED)

# %%
# --- Load label=1 points ---
label1_path = os.path.join(PROCESSED_DIR, "label1_landslide_points.csv")
if not os.path.exists(label1_path):
    raise FileNotFoundError("Run T4_03 first to create label1_landslide_points.csv")

df_ls = pd.read_csv(label1_path)
print(f"Landslide (label=1) points loaded: {len(df_ls)}")

# %%
# --- Distance helper (shared by both dedup steps below) ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = radians(lat1), radians(lat2)
    a = sin(radians(lat2-lat1)/2)**2 + cos(p1)*cos(p2)*sin(radians(lon2-lon1)/2)**2
    return 2*R*asin(sqrt(a))

# %%
# --- Step 1: Deduplicate landslide points AGAINST EACH OTHER at 500 m ---
# This is the fix for a real bug:
# T4_03 produced label=1 points but only removed exact duplicates.
# Two distinct landslide events can be <500 m apart (e.g. separate slope
# failures on the same hillside). At 30 m GEE resolution these points see
# nearly identical feature values but are counted as independent training
# samples — this is spatial autocorrelation that will overfit the model.
#
# We apply the SAME 500 m rule to the label=1 set as to the label=0 set.
# Both classes must satisfy the same spatial independence criterion.

def dedup_within_set(df_in, min_dist_m):
    """
    Greedy deduplication: keep a point only if it is >= min_dist_m
    from all already-kept points. Reproducible given fixed input order.
    """
    kept = []
    for _, row in df_in.iterrows():
        lat, lon = row["lat"], row["lon"]
        if all(haversine(lat, lon, k[0], k[1]) >= min_dist_m for k in kept):
            kept.append((lat, lon))
    return pd.DataFrame(kept, columns=["lat","lon"])

n_before = len(df_ls)
df_ls    = dedup_within_set(df_ls, MIN_DIST_M)
df_ls["label"] = 1
df_ls    = df_ls.reset_index(drop=True)
print(f"After landslide-to-landslide dedup ({MIN_DIST_M} m): {len(df_ls)}")
print(f"Removed {n_before - len(df_ls)} label=1 points that were too close to each other")

# Build reference coords for stable-point checking
ls_coords = list(zip(df_ls["lat"], df_ls["lon"]))

def min_dist_to_ls(lat, lon):
    """Minimum distance from (lat,lon) to any landslide point."""
    return min(haversine(lat, lon, ll, lo) for ll, lo in ls_coords)

# %%
# --- Generate and filter stable candidates ---
N_CANDIDATES = TARGET * 20   # large pool; will filter down
cand_lats = np.random.uniform(SOUTH, NORTH, N_CANDIDATES)
cand_lons = np.random.uniform(WEST,  EAST,  N_CANDIDATES)

print(f"Checking {N_CANDIDATES:,} candidates (>{MIN_DIST_M}m from landslides)...")
valid_lats, valid_lons = [], []
report_every = N_CANDIDATES // 10

for i, (lat, lon) in enumerate(zip(cand_lats, cand_lons)):
    if i % report_every == 0:
        print(f"  {i:,}/{N_CANDIDATES:,} — valid so far: {len(valid_lats)}")
    if min_dist_to_ls(lat, lon) >= MIN_DIST_M:
        valid_lats.append(lat)
        valid_lons.append(lon)

print(f"Valid stable candidates: {len(valid_lats)}")

# %%
# --- Sample and balance ---
n_use = min(len(valid_lats), len(df_ls), TARGET)
idx = np.random.choice(len(valid_lats), size=n_use, replace=False)

df_stable = pd.DataFrame({
    "lat":   [valid_lats[i] for i in idx],
    "lon":   [valid_lons[i] for i in idx],
    "label": 0,
})

df_ls_bal = df_ls[["lat","lon"]].copy()
df_ls_bal["label"] = 1
df_ls_bal = df_ls_bal.sample(n=n_use, random_state=RANDOM_SEED)

print(f"Balanced: {n_use} landslide + {n_use} stable = {2*n_use} total")

# %%
# --- Merge, shuffle, add point_id ---
df_labels = pd.concat([df_ls_bal, df_stable], ignore_index=True)
df_labels = df_labels.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
df_labels.insert(0, "point_id", range(len(df_labels)))

print("Class distribution:")
print(df_labels["label"].value_counts().to_string())

# %%
# --- Verify no stable point is too close to a landslide ---
violations = 0
for _, row in df_labels[df_labels["label"]==0].iterrows():
    if min_dist_to_ls(row["lat"], row["lon"]) < MIN_DIST_M:
        violations += 1
print(f"Distance constraint violations: {violations}  (must be 0)")

# %%
# --- Save deliverable ---
out_path = os.path.join(PROCESSED_DIR, "landslide_labels.csv")
df_labels.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print("This is T4 Deliverable 1 — send to T1.")
print("Columns: point_id, lat, lon, label (1=landslide, 0=stable)")

# %%
# --- Plot ---
fig, axes = plt.subplots(1, 2, figsize=(15, 7))
fig.suptitle(f"GeoSentinel+ Training Points — {n_use} Landslide + {n_use} Stable = {2*n_use} Total",
             fontsize=12, fontweight="bold")

for ax, title, xlim, ylim in [
    (axes[0], "Full Study Area",       (WEST-0.02, EAST+0.02),   (SOUTH-0.02, NORTH+0.02)),
    (axes[1], "Joshimath Town Zoom",   (79.50, 79.62),            (30.52, 30.60)),
]:
    stable = df_labels[df_labels["label"]==0]
    ls_pts = df_labels[df_labels["label"]==1]
    ax.scatter(stable["lon"], stable["lat"],
               c="steelblue", s=20, alpha=0.6, label=f"Stable / label=0 (n={len(stable)})")
    ax.scatter(ls_pts["lon"], ls_pts["lat"],
               c="crimson", s=35, alpha=0.85, label=f"Landslide / label=1 (n={len(ls_pts)})")
    ax.scatter([79.568], [30.556], c="gold", s=200, marker="*",
               zorder=6, label="Joshimath", edgecolors="black")
    if title == "Full Study Area":
        ax.scatter([79.543], [30.541], c="yellow", s=150, marker="*",
                   zorder=6, label="Helang", edgecolors="black")
        ax.add_patch(Rectangle((WEST,SOUTH), EAST-WEST, NORTH-SOUTH,
                               linewidth=2, edgecolor="black", facecolor="none"))
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.set_title(title); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR,"training_points_map.png"), dpi=150, bbox_inches="tight")
plt.show()
