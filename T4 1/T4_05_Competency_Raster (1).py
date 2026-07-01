# %% T4_05 — Competency Map Raster
# Applies competency scores to GLiM geology polygons and rasterizes to GeoTIFF.

#
# Inputs:
#   data/processed/glim_study_area.gpkg    
#   data/processed/proxy_values_lookup.csv  
#   models/competency_model.pkl             
#
# Output:
#   outputs/competency_map.tif              

import os
import geopandas as gpd
import rasterio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from rasterio.warp import calculate_default_transform, reproject, Resampling

# ── CHANGE THIS ─────────────────────────────────────────────────────────
BASE_DIR = r"D:\Games_krish\T4 1"
# ────────────────────────────────────────────────────────────────────────

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_DIR    = os.path.join(BASE_DIR, "data", "outputs")
MODEL_PATH    = os.path.join(BASE_DIR, "models", "competency_model.pkl")
RASTER_OUT    = os.path.join(OUTPUT_DIR, "competency_map.tif")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Locked constants (must match T1's GEE export) ---
WEST, SOUTH, EAST, NORTH = 78.2, 30.0, 80.0, 31.0
PIXEL_SIZE    = 0.000277
WIDTH         = int((EAST  - WEST)  / PIXEL_SIZE)   # 6498
HEIGHT        = int((NORTH - SOUTH) / PIXEL_SIZE)   # 3610
TRANSFORM     = from_bounds(WEST, SOUTH, EAST, NORTH, WIDTH, HEIGHT)
NODATA_VALUE  = -9999.0    # for pixels with NO geology polygon
DEFAULT_COMP  = 0.30       # for polygons with unmapped rock code (regional MCT avg)

print(f"Grid: {WIDTH} × {HEIGHT} = {WIDTH*HEIGHT:,} pixels")

# %%
# --- Load geology and proxy table ---
GDB_PATH  = os.path.join(PROCESSED_DIR, "glim_study_area.gpkg")
PRXY_PATH = os.path.join(PROCESSED_DIR, "proxy_values_lookup.csv")

gdf      = gpd.read_file(GDB_PATH)
df_proxy = pd.read_csv(PRXY_PATH)
print(f"Geology polygons: {len(gdf)}")
print(f"Proxy table rows: {len(df_proxy)}")

# Ensure CRS is EPSG:4326
if gdf.crs is None:
    gdf = gdf.set_crs("EPSG:4326")
elif gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs("EPSG:4326")

# %%
# --- Identify rock type column ---
VALID_CODES = {'mt','pa','pb','pi','va','vb','vi','sc','sm','ss','su','ev','wb','nd','ig','ds'}
ROCK_COL = None
for col in gdf.select_dtypes("object").columns:
    if col == "geometry": continue
    if len(set(gdf[col].dropna().unique()) & VALID_CODES) >= 3:
        ROCK_COL = col
        break
if ROCK_COL is None:
    ROCK_COL = "xx"
print(f"Rock type column: '{ROCK_COL}'")

# %%
# --- Get competency scores ---
# T3 model note: competency_model.pkl tested with actual proxy values returns
# 0.500 for >90% of inputs (trained on 3-bucket labels, not continuous UCS).
# Manual UCS-normalised scores (from Amadei 1996) carry real spatial variation.
# Notebook defaults to manual scores. Switch USE_T3_MODEL = True if T3 retrains
# with continuous targets.

USE_T3_MODEL = False

if USE_T3_MODEL and os.path.exists(MODEL_PATH):
    import joblib
    model = joblib.load(MODEL_PATH)
    X = df_proxy[["GR_api","RHOB_gcc","NPHI"]].values
    preds = np.clip(model.predict(X), 0.0, 1.0)
    df_proxy["competency_used"] = preds
    print("Using T3 model predictions.")
else:
    if "competency" in df_proxy.columns:
        source_col = "competency"
    elif "competency_manual" in df_proxy.columns:
        source_col = "competency_manual"
    else:
        raise KeyError("Proxy table must contain either 'competency' or 'competency_manual'.")

    df_proxy["competency_used"] = df_proxy[source_col]
    src = "manual (UCS-normalised, Amadei 1996)" if not USE_T3_MODEL else "T3 model not found"
    print(f"Using manual competency scores from '{source_col}' ({src}).")

# Build lookup dict: rock_code → competency score
# Normalise to lowercase for robust matching
comp_lookup = {
    str(row["rock_code"]).strip().lower(): float(row["competency_used"])
    for _, row in df_proxy.iterrows()
}

# %%
# --- Map competency to each polygon ---
gdf["rock_code_norm"] = gdf[ROCK_COL].astype(str).str.strip().str.lower()
gdf["competency"]     = gdf["rock_code_norm"].map(comp_lookup)

n_total    = len(gdf)
n_fallback = gdf["competency"].isna().sum()
gdf["competency"] = gdf["competency"].fillna(DEFAULT_COMP)

print(f"Polygons mapped    : {n_total - n_fallback} / {n_total}")
print(f"Fallback ({DEFAULT_COMP}): {n_fallback} polygons ({100*n_fallback/n_total:.1f}%)")
if n_fallback > 0:
    unmapped = gdf.loc[gdf["rock_code_norm"].map(comp_lookup).isna(),
                       ROCK_COL].unique()
    print(f"Unmapped codes: {unmapped}")

# %%
# --- Rasterize ---
# NODATA_VALUE goes in pixels with no polygon at all (genuine data gap).
# DEFAULT_COMP goes in polygons that exist but have unmapped code (handled above).
# These two are intentionally different — see README.md.

print("Rasterizing...")
shapes_iter = (
    (geom, val)
    for geom, val in zip(gdf.geometry, gdf["competency"])
    if geom is not None and not geom.is_empty
)
arr = rasterize(
    shapes      = shapes_iter,
    out_shape   = (HEIGHT, WIDTH),
    transform   = TRANSFORM,
    fill        = NODATA_VALUE,
    dtype       = "float32",
    all_touched = False,
)
n_valid   = int((arr != NODATA_VALUE).sum())
n_nodata  = arr.size - n_valid
print(f"Valid pixels: {n_valid:,}  |  Nodata pixels: {n_nodata:,}")
if n_valid > 0:
    valid = arr[arr != NODATA_VALUE]
    print(f"Value range (valid): {valid.min():.3f} to {valid.max():.3f}")

# %%
# --- Save GeoTIFF ---
with rasterio.open(
    RASTER_OUT, "w",
    driver    = "GTiff",
    height    = HEIGHT,
    width     = WIDTH,
    count     = 1,
    dtype     = "float32",
    crs       = "EPSG:4326",
    transform = TRANSFORM,
    compress  = "lzw",
    nodata    = NODATA_VALUE,
) as dst:
    dst.write(arr, 1)

size_mb = os.path.getsize(RASTER_OUT) / 1e6
print(f"Saved: {RASTER_OUT}  ({size_mb:.1f} MB)")

# %%
# =============================================================
# 10-POINT VERIFICATION CHECKLIST
# All checks must show PASS before sending to T1.
# Spec from team verification document (T4_Competency_Map_Checklist.md)
# =============================================================

print("\n" + "="*60)
print("COMPETENCY MAP — VERIFICATION CHECKLIST")
print("="*60)
results = {}

with rasterio.open(RASTER_OUT) as src:
    crs_act    = src.crs
    res_act    = src.res
    bnd_act    = src.bounds
    shp_act    = src.shape
    nd_act     = src.nodata
    drv_act    = src.driver
    dtp_act    = src.dtypes[0]
    data_arr   = src.read(1)

valid_mask = (data_arr != NODATA_VALUE)
valid_data = data_arr[valid_mask]
coverage   = 100 * valid_mask.sum() / data_arr.size
fallback_pct = 100 * n_fallback / n_total

def check(num, name, ok, actual, required, fix=""):
    results[num] = ok
    status = "✓ PASS" if ok else "✗ FAIL"
    print(f"\n[{num:2d}] {name}")
    print(f"     Actual  : {actual}")
    print(f"     Required: {required}")
    print(f"     Status  : {status}")
    if not ok and fix:
        print(f"     Fix     : {fix}")

check(1,  "CRS",
      crs_act is not None and crs_act.to_epsg() == 4326,
      str(crs_act), "EPSG:4326",
      "Re-run with crs='EPSG:4326' in rasterio.open()")

check(2,  "Resolution",
      abs(res_act[0] - PIXEL_SIZE) < 5e-6,
      f"{res_act[0]:.6f}°", f"~{PIXEL_SIZE:.6f}° (30 m)",
      "Check PIXEL_SIZE constant at top of notebook")

check(3,  "Bounding Box  ← MOST IMPORTANT",
      all(abs(v) < 0.01 for v in [
          bnd_act.left-WEST, bnd_act.bottom-SOUTH,
          bnd_act.right-EAST, bnd_act.top-NORTH]),
      f"L={bnd_act.left:.3f} B={bnd_act.bottom:.3f} R={bnd_act.right:.3f} T={bnd_act.top:.3f}",
      f"L={WEST} B={SOUTH} R={EAST} T={NORTH}",
      "Re-clip with box(WEST,SOUTH,EAST,NORTH) and re-rasterize")

exp_w = int((EAST-WEST)/PIXEL_SIZE)
exp_h = int((NORTH-SOUTH)/PIXEL_SIZE)
check(4,  "Dimensions",
      abs(shp_act[1]-exp_w) < 5 and abs(shp_act[0]-exp_h) < 5,
      f"height={shp_act[0]}, width={shp_act[1]}",
      f"~height={exp_h}, ~width={exp_w}",
      "Bounding box used during rasterize was wrong")

check(5,  "Value Range (valid pixels only)",
      len(valid_data) > 0 and valid_data.min() >= 0.0 and valid_data.max() <= 1.0,
      f"{valid_data.min():.4f} to {valid_data.max():.4f}" if len(valid_data) else "NO VALID DATA",
      "0.0 to 1.0",
      "Check competency values in proxy_values_lookup.csv")

check(6,  "Nodata Defined",
      nd_act is not None,
      str(nd_act), "-9999.0",
      "Set nodata=NODATA_VALUE in rasterio.open()")

check(7,  "Data Coverage",
      coverage > 85,
      f"{coverage:.2f}%", "> 85%",
      "GLiM has gaps; check clip result in T4_01")

check(8,  "Default Fallback Usage",
      fallback_pct < 15,
      f"{fallback_pct:.2f}% of polygons used default",
      "< 15%",
      "Add missing rock codes to proxy_values_lookup.csv")

gdf_bounds = gdf.total_bounds
check(9,  "Spatial Extent Coverage",
      gdf_bounds[0] <= WEST+0.05 and gdf_bounds[1] <= SOUTH+0.05 and
      gdf_bounds[2] >= EAST-0.05 and gdf_bounds[3] >= NORTH-0.05,
      f"W={gdf_bounds[0]:.3f} S={gdf_bounds[1]:.3f} E={gdf_bounds[2]:.3f} N={gdf_bounds[3]:.3f}",
      f"Must reach W={WEST} S={SOUTH} E={EAST} N={NORTH}",
      "Geology data does not cover full study area — check clip in T4_01")

check(10, "File Format",
      drv_act == "GTiff" and "float32" in str(dtp_act),
      f"{drv_act}, {dtp_act}", "GTiff, float32",
      "Ensure dtype='float32' in rasterio.open()")

# --- Summary ---
print("\n" + "="*60)
print(f"{'#':<4}{'Check':<32}{'Status'}")
print("-"*48)
names = {1:"CRS",2:"Resolution",3:"Bounding Box",4:"Dimensions",
         5:"Value Range",6:"Nodata Defined",7:"Data Coverage",
         8:"Default Fallback",9:"Spatial Extent",10:"File Format"}
for i in range(1,11):
    print(f"{i:<4}{names[i]:<32}{'PASS' if results[i] else 'FAIL'}")
print("-"*48)
all_pass = all(results.values())
print("\n" + ("ALL CHECKS PASSED — SAFE TO SEND TO T1"
              if all_pass else
              "SOME CHECKS FAILED — DO NOT SEND YET"))
print("="*60)

# %%
# --- Visualise ---
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle("Competency Map — T4's Main Deliverable for T1\n"
             "Rock Strength Index | Helang-Joshimath Corridor | EPSG:4326",
             fontsize=12, fontweight="bold")

# Mask nodata for display
display_arr = np.where(data_arr == NODATA_VALUE, np.nan, data_arr)

ax1 = axes[0]
im = ax1.imshow(display_arr, extent=[WEST,EAST,SOUTH,NORTH],
                origin="upper", cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
plt.colorbar(im, ax=ax1, label="Rock Competency Score\n(0=Very Weak, 1=Very Strong)")
ax1.scatter([79.568],[30.556], c="blue", s=120, marker="*", zorder=5, label="Joshimath")
ax1.set_xlabel("Longitude"); ax1.set_ylabel("Latitude")
ax1.set_title("Competency Modifier Map"); ax1.legend(); ax1.grid(True, alpha=0.3)

ax2 = axes[1]
ax2.hist(valid_data, bins=50, color="steelblue", edgecolor="navy", alpha=0.8)
ax2.axvline(float(valid_data.mean()), color="red", linestyle="--",
            label=f"Mean = {valid_data.mean():.3f}")
ax2.axvline(float(np.median(valid_data)), color="orange", linestyle=":",
            label=f"Median = {np.median(valid_data):.3f}")
ax2.set_xlabel("Competency Score"); ax2.set_ylabel("Number of Pixels")
ax2.set_title("Distribution of Pixel Values")
ax2.legend(); ax2.grid(True, alpha=0.3)

# Annotate GLiM codes on histogram
for code, score in [("su",0.05),("mt",0.30),("pi",0.50),("pb",0.59)]:
    ax2.axvline(score, color="gray", linestyle=":", alpha=0.5)
    ax2.text(score, ax2.get_ylim()[1]*0.9, f"[{code}]",
             rotation=90, fontsize=7, ha="right", color="dimgray")

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR,"competency_map_visual.png"), dpi=150, bbox_inches="tight")
plt.show()

# %%
# --- T1's verification snippet (copy and send with the file) ---
print("\nSend this snippet to T1 to verify the file:")
print("""
import rasterio, numpy as np

with rasterio.open('competency_map.tif') as src:
    data  = src.read(1)
    valid = data[data != src.nodata]
    print('CRS        :', src.crs)          # must be EPSG:4326
    print('Resolution :', src.res)          # must be ~(0.000277, 0.000277)
    print('Bounds     :', src.bounds)       # must be (78.2, 30.0, 80.0, 31.0)
    print('Shape      :', src.shape)        # must be ~(3610, 6498)
    print('Nodata     :', src.nodata)       # must be -9999.0
    print('Value range:', valid.min(), 'to', valid.max())  # 0.0 to 1.0
""")
print(f"\nFile location: {RASTER_OUT}")
