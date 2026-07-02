"""
Surface Features Preprocessing
Reads the raw GEE export CSV, extracts lat/lon from the .geo column,
and saves a clean version to data/processed/.

Run from the pipeline/surface/ directory or from anywhere —
paths are resolved relative to this script's location.
"""

import json
from pathlib import Path
import pandas as pd

BASE_DIR    = Path(__file__).parent.parent.parent   # repo root
RAW_CSV     = BASE_DIR / "data" / "raw" / "surface_features_Garhwal-Himalaya.csv"
OUT_CSV     = BASE_DIR / "data" / "processed" / "surface_features_clean.csv"

df = pd.read_csv(RAW_CSV)
print("Loaded:", df.shape)

df['lon'] = df['.geo'].apply(lambda x: json.loads(x)['coordinates'][0])
df['lat'] = df['.geo'].apply(lambda x: json.loads(x)['coordinates'][1])

df = df.drop(columns=['.geo', 'system:index'], errors='ignore')
df = df[['lat', 'lon', 'elevation', 'slope', 'aspect', 'curvature', 'NDVI', 'rainfall']]

print("Nulls before drop:\n", df.isnull().sum())
df = df.dropna()

print(f"Final rows  : {len(df)}")
print(f"NDVI range  : {df['NDVI'].min():.3f} to {df['NDVI'].max():.3f}")
print(f"Nulls remain: {df.isnull().sum().sum()}")

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_CSV, index=False)
print(f"Saved: {OUT_CSV}")
