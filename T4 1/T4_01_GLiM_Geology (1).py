# %% T4_01 — GLiM Geology (LiMW_GIS 2015.gdb)
# Loads the global lithological map, clips to study area, saves for Notebook 05.

import os
import geopandas as gpd
import fiona
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from shapely.geometry import box

# ── CHANGE THIS ───────────────────────────────────────────────────────────
BASE_DIR = r"T4 1"
# ─────────────────────────────────────────────────────────────────────────

GDB_PATH_CANDIDATES = [
    os.path.join(BASE_DIR, "data", "raw", "LiMW_GIS 2015.gdb"),
    os.path.join(BASE_DIR, "Data", "Raw", "LiMW_GIS 2015.gdb"),
]
GDB_PATH = next((p for p in GDB_PATH_CANDIDATES if os.path.exists(p)), GDB_PATH_CANDIDATES[0])
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_DIR    = os.path.join(BASE_DIR, "data", "outputs")
CLIPPED_OUT   = os.path.join(PROCESSED_DIR, "glim_study_area.gpkg")
SUMMARY_OUT   = os.path.join(PROCESSED_DIR, "rock_type_summary.csv")

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR,    exist_ok=True)

WEST, SOUTH, EAST, NORTH = 78.2, 30.0, 80.0, 31.0

# %%
# --- Identify the available layers and use the real layer name ---
available_layers = fiona.listlayers(GDB_PATH)
if not available_layers:
    raise ValueError(f"No layers found in geodatabase: {GDB_PATH}")

print("GDB layers:")
for name in available_layers:
    with fiona.open(GDB_PATH, layer=name) as src:
        print(f"  '{name}' | {len(src)} records | {src.schema['geometry']}")

# %%
# --- Load the lithology polygon layer ---
LAYER_NAME = available_layers[0]
print("Loading GLiM (may take 1–2 minutes for the global dataset)...")
gdf = gpd.read_file(GDB_PATH, layer=LAYER_NAME)
print(f"Loaded: {len(gdf):,} polygons | CRS: {gdf.crs}")
print("Columns:", gdf.columns.tolist())

# %%
# --- Reproject to EPSG:4326 if needed ---
if gdf.crs is None:
    gdf = gdf.set_crs("EPSG:4326")
elif gdf.crs.to_epsg() != 4326:
    print(f"Reprojecting from {gdf.crs} ...")
    gdf = gdf.to_crs("EPSG:4326")
print(f"CRS confirmed: {gdf.crs}")

# %%
# --- Identify the rock type column (GLiM uses 'xx') ---
VALID_CODES = {'mt','pa','pb','pi','va','vb','vi','sc','sm','ss','su','ev','wb','nd','ig','ds'}
ROCK_COL = None
for col in gdf.select_dtypes("object").columns:
    if col == "geometry":
        continue
    if len(set(gdf[col].dropna().unique()) & VALID_CODES) >= 3:
        ROCK_COL = col
        print(f"Rock type column detected: '{ROCK_COL}'")
        break
if ROCK_COL is None:
    ROCK_COL = "xx"
    print(f"Using default column name: '{ROCK_COL}'")

# %%
# --- Clip to study area ---
study_box   = box(WEST, SOUTH, EAST, NORTH)
gdf_pre     = gdf.cx[WEST-0.1 : EAST+0.1, SOUTH-0.1 : NORTH+0.1]
gdf_clipped = gdf_pre.clip(study_box)
gdf_clipped = gdf_clipped[~gdf_clipped.is_empty].reset_index(drop=True)
print(f"Polygons in study area: {len(gdf_clipped)}")

# %%
# --- Print rock codes found ---
GLIM_NAMES = {
    'mt':'Metamorphics','pi':'Acid/Int. Plutonics','pb':'Basic Plutonics',
    'ss':'Siliciclastic Sed.','sc':'Carbonate Sed.','sm':'Mixed Sed.',
    'su':'Unconsolidated','va':'Acid Volcanics','vb':'Basic Volcanics',
    'vi':'Int. Volcanics','pa':'Pyroclastics','ev':'Evaporites',
    'wb':'Water','nd':'No Data','ig':'Ice/Glaciers','ds':'Dunes'
}
counts = gdf_clipped[ROCK_COL].value_counts()
print("\nRock codes in study area:")
for code, n in counts.items():
    print(f"  [{code}] {GLIM_NAMES.get(str(code), 'Unknown'):30s} {n} polygons")

# %%
# --- Save clipped geology ---
gdf_clipped.to_file(CLIPPED_OUT, driver="GPKG")
print(f"Saved: {CLIPPED_OUT}")

summary = counts.reset_index()
summary.columns = ["rock_code", "polygon_count"]
summary["meaning"] = summary["rock_code"].map(GLIM_NAMES).fillna("Unknown")
summary.to_csv(SUMMARY_OUT, index=False)
print(f"Saved: {SUMMARY_OUT}")

# %%
# --- Visualise ---
ROCK_COLORS = {
    'mt':'#8B6914','pi':'#FF69B4','pb':'#4B0082','ss':'#F4A460',
    'sc':'#90EE90','sm':'#DEB887','su':'#87CEEB','va':'#FF4500',
    'vb':'#2E8B57','vi':'#FF6347','wb':'#1E90FF','ig':'#E0E0E0',
    'nd':'#808080','ev':'#FFD700','pa':'#FF1493','ds':'#F5DEB3'
}

fig, ax = plt.subplots(figsize=(10, 9))
for code in gdf_clipped[ROCK_COL].unique():
    subset = gdf_clipped[gdf_clipped[ROCK_COL] == code]
    subset.plot(ax=ax, color=ROCK_COLORS.get(str(code),"#CCCCCC"),
                edgecolor="black", linewidth=0.3, alpha=0.85)

legend_patches = [
    mpatches.Patch(color=ROCK_COLORS.get(str(c),"#CCCCCC"),
                   label=f"[{c}] {GLIM_NAMES.get(str(c),c)}")
    for c in gdf_clipped[ROCK_COL].unique()
]
ax.legend(handles=legend_patches, loc="upper left", fontsize=8)
ax.scatter([79.568],[30.556], color="red", s=120, marker="*", zorder=5, label="Joshimath")
ax.set_xlim(WEST-0.02, EAST+0.02)
ax.set_ylim(SOUTH-0.02, NORTH+0.02)
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
ax.set_title("GLiM Rock Types — Study Area\n(Hartmann & Moosdorf 2012)")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "geology_map.png"), dpi=150, bbox_inches="tight")
plt.show()
print("Map saved.")
