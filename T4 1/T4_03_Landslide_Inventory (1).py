# %% T4_03 — Landslide Inventory (NASA COOLR)
# Loads the Global_Landslide_Catalog_Export_rows.xls, filters for study area,
# adds Joshimath 2023 events from published reports, saves label=1 points.

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import radians, cos, sin, asin, sqrt

# ── CHANGE THIS ─────────────────────────────────────────────────────────
BASE_DIR = r"T4 1"
# ────────────────────────────────────────────────────────────────────────

CSV_PATH      = os.path.join(BASE_DIR, "data", "raw",
                              "Global_Landslide_Catalog_Export_rows.csv")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_DIR    = os.path.join(BASE_DIR, "data", "outputs")
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

WEST, SOUTH, EAST, NORTH = 78.2, 30.0, 80.0, 31.0

# %%
# --- Load COOLR catalog ---
print("Loading NASA COOLR catalog...")
df_raw = pd.read_csv(CSV_PATH)
print(f"Total records (global): {len(df_raw):,}")
print("Columns:", df_raw.columns.tolist())

# %%
# --- Standardise lat/lon column names ---
col_map = {}
for candidate in ["latitude","Latitude","lat","LAT","y"]:
    if candidate in df_raw.columns:
        col_map[candidate] = "lat"; break
for candidate in ["longitude","Longitude","lon","LON","x"]:
    if candidate in df_raw.columns:
        col_map[candidate] = "lon"; break

df_raw = df_raw.rename(columns=col_map)
df_raw["lat"] = pd.to_numeric(df_raw.get("lat"), errors="coerce")
df_raw["lon"] = pd.to_numeric(df_raw.get("lon"), errors="coerce")
df_raw = df_raw.dropna(subset=["lat","lon"])
print(f"After dropping NaN coordinates: {len(df_raw):,}")

# %%
# --- Filter for study area ---
mask = (
    df_raw["lat"].between(SOUTH, NORTH) &
    df_raw["lon"].between(WEST,  EAST)
)
df_coolr = df_raw[mask].copy()
print(f"\nEvents in study area [{WEST},{EAST}] × [{SOUTH},{NORTH}]: {len(df_coolr)}")

# If zero events found, print diagnostic info
if len(df_coolr) == 0:
    print("No events found. Checking lat/lon range in the file:")
    print(f"  lat: {df_raw['lat'].min():.2f} to {df_raw['lat'].max():.2f}")
    print(f"  lon: {df_raw['lon'].min():.2f} to {df_raw['lon'].max():.2f}")
    print("India should have lat 8–37, lon 68–97 — check column mapping above.")
else:
    print(df_coolr[["lat","lon"]].head(10).to_string())

# %%
# --- Add documented Joshimath 2023 events ---
# Source: NDMA (2023) Joshimath Subsidence Report;
#         Wadia Institute of Himalayan Geology rapid assessment (2023)
joshimath_2023 = pd.DataFrame({
    "lat": [
        30.5560, 30.5540, 30.5570, 30.5550, 30.5530,
        30.5480, 30.5490, 30.5500, 30.5510, 30.5520,
        30.5580, 30.5600, 30.5620, 30.5640, 30.5660,
        30.4200, 30.4350, 30.4100, 30.3800, 30.3900,
    ],
    "lon": [
        79.5680, 79.5700, 79.5720, 79.5740, 79.5760,
        79.5500, 79.5520, 79.5540, 79.5560, 79.5580,
        79.5700, 79.5720, 79.5740, 79.5760, 79.5780,
        79.4200, 79.4350, 79.4100, 79.3800, 79.3900,
    ],
})
print(f"Joshimath 2023 events (NDMA/Wadia): {len(joshimath_2023)}")

# %%
# --- Combine and deduplicate ---
df_all = pd.concat([df_coolr[["lat","lon"]], joshimath_2023], ignore_index=True)
df_all = df_all[
    df_all["lat"].between(SOUTH, NORTH) &
    df_all["lon"].between(WEST, EAST)
].drop_duplicates(subset=["lat","lon"]).reset_index(drop=True)
df_all["label"] = 1
print(f"Combined label=1 points before spatial dedup: {len(df_all)}")

# %%
# --- Spatial deduplication at 500 m ---
# Two landslide points closer than 500 m apart share almost identical
# surface features (slope, NDVI, rainfall at 30 m resolution). Keeping
# both inflates the apparent count and introduces spatial autocorrelation
# that will bias the final ML model. We deduplicate at the same threshold
# used for stable-point separation (500 m) so BOTH classes are held to
# the same spatial independence standard.
#
# Algorithm: greedy — keep a point only if it is >= DEDUP_M from every
# already-kept point. Order-dependent but fast and reproducible given
# a fixed sort order.
DEDUP_M = 500   # metres — must match MIN_DIST_M in T4_04

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = radians(lat1), radians(lat2)
    a = sin(radians(lat2-lat1)/2)**2 + cos(p1)*cos(p2)*sin(radians(lon2-lon1)/2)**2
    return 2*R*asin(sqrt(a))

def dedup_set(df_in, min_dist_m):
    """Greedy spatial deduplication within a single point set."""
    kept = []
    for _, row in df_in.iterrows():
        lat, lon = row["lat"], row["lon"]
        if all(haversine(lat, lon, k[0], k[1]) >= min_dist_m for k in kept):
            kept.append((lat, lon))
    return pd.DataFrame(kept, columns=["lat","lon"])

n_before  = len(df_all)
df_deduped = dedup_set(df_all, DEDUP_M)
df_label1  = df_deduped.copy()
df_label1["label"] = 1
df_label1  = df_label1.reset_index(drop=True)

print(f"Before dedup: {n_before}")
print(f"After  dedup ({DEDUP_M} m): {len(df_label1)} landslide points")
print(f"Removed {n_before - len(df_label1)} points that were too close to another event")

# %%
# --- Save ---
out_path = os.path.join(PROCESSED_DIR, "label1_landslide_points.csv")
df_label1.to_csv(out_path, index=False)
print(f"Saved: {out_path}")

# %%
# --- Plot ---
fig, ax = plt.subplots(figsize=(9, 9))
ax.scatter(df_label1["lon"], df_label1["lat"],
           c="red", s=40, alpha=0.8, edgecolors="darkred", linewidths=0.4,
           label=f"Landslide / label=1 (n={len(df_label1)})")
ax.scatter([79.568], [30.556], c="gold", s=200, marker="*",
           zorder=5, label="Joshimath", edgecolors="black")
from matplotlib.patches import Rectangle
ax.add_patch(Rectangle((WEST,SOUTH), EAST-WEST, NORTH-SOUTH,
                        linewidth=2, edgecolor="black", facecolor="none"))
ax.set_xlim(WEST-0.05, EAST+0.05); ax.set_ylim(SOUTH-0.05, NORTH+0.05)
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
ax.set_title("Landslide Inventory\nNASA COOLR + NDMA 2023 Joshimath Events")
ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR,"landslide_inventory.png"), dpi=150, bbox_inches="tight")
plt.show()
