# ================================================================
# GeoSentinel+ — Susceptibility Map Generation
# notebooks/06_susceptibility_map.ipynb
# ================================================================
# Run each cell in order.
# Before running this notebook make sure you have:
#   data/processed/master_features.csv
#   data/processed/surface_features_clean.csv
#   data/processed/competency_map.tif
#   data/processed/landslide_labels.csv
#   models/final_model.pkl
#   models/feature_cols.pkl
# ================================================================

# ----------------------------------------------------------------
# CELL 1 — Imports
# ----------------------------------------------------------------

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import rasterio
from rasterio.transform import from_bounds
import joblib
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Paths resolved relative to this script — works from any working directory
BASE_DIR        = Path(__file__).parent
MODELS_DIR      = BASE_DIR.parent / "notebooks" / "models"
DATA_PROCESSED  = BASE_DIR.parent / "data" / "processed"
OUTPUTS_DIR     = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

print("All libraries imported successfully")

# ----------------------------------------------------------------
# CELL 2 — Load Model and Feature Columns
# ----------------------------------------------------------------

final_model  = joblib.load(MODELS_DIR / "final_model.pkl")
feature_cols = joblib.load(MODELS_DIR / "feature_cols.pkl")

print("Model loaded       :", type(final_model).__name__)
print("Features expected  :", feature_cols)

# ----------------------------------------------------------------
# CELL 3 — Load All Data Sources
# ----------------------------------------------------------------

# Surface features — your GEE output
surface = pd.read_csv(DATA_PROCESSED / "surface_features_clean.csv")
print("Surface features   :", surface.shape)

labels = pd.read_csv(DATA_PROCESSED / "landslide_labels.csv")
print("Landslide labels   :", labels.shape)
print("Label distribution :")
print(labels['label'].value_counts())

COMPETENCY_PATH = DATA_PROCESSED / "competency_map.tif"
print()
print("Competency map loaded from:", COMPETENCY_PATH)

# ----------------------------------------------------------------
# CELL 4 — Define Study Area Grid
# ----------------------------------------------------------------

# These must exactly match your GEE bounding box
WEST  = 78.2
SOUTH = 30.0
EAST  = 80.0
NORTH = 31.0

# Pixel size — 30m resolution in degrees
PIXEL_SIZE = 0.000277

# Calculate grid dimensions
WIDTH  = int((EAST  - WEST)  / PIXEL_SIZE)
HEIGHT = int((NORTH - SOUTH) / PIXEL_SIZE)

print("Study area grid:")
print(f"  West  : {WEST}, South : {SOUTH}")
print(f"  East  : {EAST}, North : {NORTH}")
print(f"  Width : {WIDTH} pixels")
print(f"  Height: {HEIGHT} pixels")
print(f"  Total : {WIDTH * HEIGHT:,} pixels")
print()
print("NOTE: Full resolution map takes a long time to generate.")
print("We will use a downsampled grid (scale factor = 10) for speed.")
print("This gives 300m resolution which is fine for visualization.")

# ----------------------------------------------------------------
# CELL 5 — Create Downsampled Pixel Grid
# ----------------------------------------------------------------

# Scale factor — increase for faster run, decrease for sharper map
# 10 = 300m resolution (fast, good for visualization)
# 5  = 150m resolution (slower, sharper)
# 1  = 30m resolution  (very slow, use only if time allows)
SCALE = 10

width_ds  = WIDTH  // SCALE
height_ds = HEIGHT // SCALE
pixel_ds  = PIXEL_SIZE * SCALE

print(f"Downsampled grid at scale factor {SCALE}x:")
print(f"  Width  : {width_ds} pixels")
print(f"  Height : {height_ds} pixels")
print(f"  Total  : {width_ds * height_ds:,} pixels")
print()

# Generate lat/lon for every pixel center in the downsampled grid
lons = np.linspace(WEST  + pixel_ds/2, EAST  - pixel_ds/2, width_ds)
lats = np.linspace(NORTH - pixel_ds/2, SOUTH + pixel_ds/2, height_ds)

# Create meshgrid — every combination of lat and lon
lon_grid, lat_grid = np.meshgrid(lons, lats)

# Flatten to a list of points
lon_flat = lon_grid.flatten()
lat_flat = lat_grid.flatten()

print(f"Total pixel points to predict: {len(lon_flat):,}")

# ----------------------------------------------------------------
# CELL 6 — Extract Surface Features at Every Pixel
# ----------------------------------------------------------------

# We cannot run GEE for every pixel in the map generation step.
# Instead we use spatial interpolation from your 4524 GEE points
# to estimate feature values at every pixel in the grid.
# This is nearest-neighbor interpolation — each grid pixel gets
# the feature values of the nearest GEE sample point.

from sklearn.neighbors import BallTree

print("Building spatial index on surface feature points...")

surface_coords = np.radians(surface[['lat', 'lon']].values)
grid_coords    = np.radians(np.column_stack([lat_flat, lon_flat]))

tree = BallTree(surface_coords, metric='haversine')
distances, indices = tree.query(grid_coords, k=1)

print("Nearest neighbor matching complete")
print(f"Max distance to nearest point: {distances.max() * 6371:.2f} km")

# Assign surface feature values to each grid pixel
surface_features_needed = ['elevation', 'slope', 'aspect',
                            'curvature', 'NDVI', 'rainfall']

grid_df = surface.iloc[indices.flatten()][surface_features_needed].reset_index(drop=True)
grid_df['lat'] = lat_flat
grid_df['lon'] = lon_flat

print(f"Grid dataframe shape: {grid_df.shape}")
print(grid_df.head(3))

# ----------------------------------------------------------------
# CELL 7 — Sample Competency Values at Every Pixel
# ----------------------------------------------------------------

print("Sampling competency values at all grid pixels...")

with rasterio.open(COMPETENCY_PATH) as src:
    raster_data = src.read(1)
    nodata_val  = src.nodata
    competency_vals = []

    for _, row in grid_df.iterrows():
        try:
            r, c = src.index(row['lon'], row['lat'])
            if (0 <= r < raster_data.shape[0] and
                0 <= c < raster_data.shape[1]):
                val = raster_data[r, c]
                if nodata_val is not None and val == nodata_val:
                    competency_vals.append(np.nan)
                else:
                    competency_vals.append(float(val))
            else:
                competency_vals.append(np.nan)
        except:
            competency_vals.append(np.nan)

grid_df['competency_index'] = competency_vals

null_count = grid_df['competency_index'].isna().sum()
print(f"Null competency pixels : {null_count:,}")
print(f"Valid competency pixels: {grid_df['competency_index'].notna().sum():,}")

# Fill null competency with regional mean
# so we still get a prediction for those pixels
regional_mean = grid_df['competency_index'].mean()
grid_df['competency_index'] = grid_df['competency_index'].fillna(regional_mean)
print(f"Filled nulls with regional mean: {regional_mean:.3f}")

# ----------------------------------------------------------------
# CELL 8 — Calculate Factor of Safety at Every Pixel
# ----------------------------------------------------------------

def factor_of_safety(row):
    c         = row['competency_index'] * 20.0
    gamma     = 20.0
    gamma_w   = 9.81
    m         = min(row['rainfall'] / 3000.0, 1.0)
    z         = 2.0
    beta      = np.radians(row['slope'])
    phi       = np.radians(30.0 + row['competency_index'] * 10.0)

    sin_b = np.sin(beta)
    cos_b = np.cos(beta)

    denominator = gamma * z * sin_b * cos_b
    if abs(denominator) < 1e-9:
        return 10.0

    numerator = (c + (gamma - gamma_w * m) * z
                 * (cos_b ** 2) * np.tan(phi))

    fs = numerator / denominator
    return float(np.clip(fs, 0.0, 10.0))

print("Calculating Factor of Safety for all pixels...")
grid_df['FS'] = grid_df.apply(factor_of_safety, axis=1)
print("Done")
print(f"FS range: {grid_df['FS'].min():.3f} to {grid_df['FS'].max():.3f}")

# ----------------------------------------------------------------
# CELL 9 — Run Model on Every Pixel
# ----------------------------------------------------------------

print("Running model predictions on all grid pixels...")

X_grid = grid_df[feature_cols]

# Check for any remaining nulls
null_check = X_grid.isnull().sum().sum()
if null_check > 0:
    print(f"Found {null_check} nulls — filling with column means")
    X_grid = X_grid.fillna(X_grid.mean())

# Predict risk probability for each pixel
risk_scores = final_model.predict_proba(X_grid)[:, 1]

grid_df['risk_score'] = risk_scores

print("Predictions complete")
print(f"Risk score range : {risk_scores.min():.3f} to {risk_scores.max():.3f}")
print(f"Risk score mean  : {risk_scores.mean():.3f}")
print()

# Risk level classification
def classify_risk(score):
    if score < 0.35:
        return 'Low'
    elif score < 0.65:
        return 'Medium'
    else:
        return 'High'

grid_df['risk_level'] = grid_df['risk_score'].apply(classify_risk)
print("Risk level distribution:")
print(grid_df['risk_level'].value_counts())

# ----------------------------------------------------------------
# CELL 10 — Reshape Risk Scores to 2D Grid
# ----------------------------------------------------------------

# Reshape flat array back into 2D image
risk_grid = risk_scores.reshape(height_ds, width_ds)

print("Risk grid shape:", risk_grid.shape)
print("Ready for map generation")

# ----------------------------------------------------------------
# CELL 11 — Generate the Susceptibility Map (Main Output)
# ----------------------------------------------------------------

fig, ax = plt.subplots(figsize=(14, 8))

# Custom colormap: green (low) → yellow (medium) → red (high)
colors_list = ['#27AE60', '#F4D03F', '#E74C3C']
cmap = mcolors.LinearSegmentedColormap.from_list(
    'susceptibility', colors_list, N=256)

# Plot the risk raster
img = ax.imshow(
    risk_grid,
    extent=[WEST, EAST, SOUTH, NORTH],
    cmap=cmap,
    vmin=0,
    vmax=1,
    origin='upper',
    aspect='auto',
    alpha=0.85
)

# Colorbar
cbar = plt.colorbar(img, ax=ax, fraction=0.03, pad=0.02)
cbar.set_label('Landslide Risk Score', fontsize=11)
cbar.set_ticks([0.0, 0.175, 0.35, 0.50, 0.65, 0.825, 1.0])
cbar.set_ticklabels(['0.0\n(Very Low)', '0.175', '0.35\n(Low→Med)',
                     '0.50', '0.65\n(Med→High)', '0.825', '1.0\n(Very High)'])

# Overlay ACTUAL landslide points (label 1) as black dots
landslide_pts = labels[labels['label'] == 1]
ax.scatter(landslide_pts['lon'], landslide_pts['lat'],
           c='black', s=20, marker='^', zorder=5,
           label=f'Confirmed Landslides (n={len(landslide_pts)})',
           alpha=0.8)

# Overlay stable points (label 0) as white dots
stable_pts = labels[labels['label'] == 0]
ax.scatter(stable_pts['lon'], stable_pts['lat'],
           c='white', s=10, marker='o', zorder=5,
           label=f'Stable Points (n={len(stable_pts)})',
           alpha=0.6, edgecolors='gray', linewidths=0.5)

# Legend for risk zones
low_patch    = mpatches.Patch(color='#27AE60', label='Low Risk (< 0.35)')
medium_patch = mpatches.Patch(color='#F4D03F', label='Medium Risk (0.35–0.65)')
high_patch   = mpatches.Patch(color='#E74C3C', label='High Risk (> 0.65)')

handles, existing_labels = ax.get_legend_handles_labels()
ax.legend(
    handles=handles + [low_patch, medium_patch, high_patch],
    loc='lower left',
    fontsize=8,
    framealpha=0.9
)

# Labels and title
ax.set_xlabel('Longitude', fontsize=11)
ax.set_ylabel('Latitude', fontsize=11)
ax.set_title(
    'GeoSentinel+ — Landslide Susceptibility Map\n'
    'Garhwal Himalaya (Tehri · Rudraprayag · Chamoli · Joshimath)',
    fontsize=13, fontweight='bold'
)

# Add key district labels on the map
district_labels = {
    'Tehri\nGarhwal'  : (78.5, 30.4),
    'Rudraprayag'     : (79.0, 30.5),
    'Chamoli'         : (79.5, 30.6),
    'Joshimath\n(MCT)': (79.6, 30.3),
}
for name, (lon, lat) in district_labels.items():
    ax.text(lon, lat, name, fontsize=7, color='white',
            fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2',
                      facecolor='black', alpha=0.5))

# Grid lines
ax.grid(alpha=0.3, linestyle='--', linewidth=0.5)

plt.tight_layout()
plt.savefig(OUTPUTS_DIR / 'susceptibility_map.png',
            dpi=200, bbox_inches='tight')
plt.show()
print("Susceptibility map saved to outputs/susceptibility_map.png")

# ----------------------------------------------------------------
# CELL 12 — Save GeoTIFF Version of the Map
# ----------------------------------------------------------------

# GeoTIFF allows the map to be opened in QGIS and used in
# the dashboard as a proper georeferenced layer

transform = from_bounds(WEST, SOUTH, EAST, NORTH,
                        width_ds, height_ds)

with rasterio.open(
    OUTPUTS_DIR / 'susceptibility_map.tif',
    'w',
    driver='GTiff',
    height=height_ds,
    width=width_ds,
    count=1,
    dtype='float32',
    crs='EPSG:4326',
    transform=transform
) as dst:
    dst.write(risk_grid.astype('float32'), 1)

print("GeoTIFF saved to outputs/susceptibility_map.tif")
print("You can open this in QGIS for higher quality visualization")

# ----------------------------------------------------------------
# CELL 13 — Risk Zone Statistics
# ----------------------------------------------------------------

# Count pixels in each risk zone
total_pixels = risk_grid.size
low_pixels    = (risk_grid < 0.35).sum()
medium_pixels = ((risk_grid >= 0.35) & (risk_grid < 0.65)).sum()
high_pixels   = (risk_grid >= 0.65).sum()

print("=== RISK ZONE STATISTICS ===")
print()
print(f"Total area analyzed : {total_pixels:,} pixels")
print()
print(f"Low Risk    (<0.35) : {low_pixels:,} pixels  "
      f"({low_pixels/total_pixels*100:.1f}%)")
print(f"Medium Risk (0.35-0.65): {medium_pixels:,} pixels  "
      f"({medium_pixels/total_pixels*100:.1f}%)")
print(f"High Risk   (>0.65) : {high_pixels:,} pixels  "
      f"({high_pixels/total_pixels*100:.1f}%)")
print()

# Validation check — do high risk zones contain actual landslides?
print("=== VALIDATION CHECK ===")
print("Do confirmed landslide points fall in high risk zones?")
print()

validation_results = []
for _, pt in landslide_pts.iterrows():
    # Find which risk zone this landslide point falls in
    col_idx = int((pt['lon'] - WEST)  / pixel_ds)
    row_idx = int((NORTH - pt['lat']) / pixel_ds)

    if (0 <= row_idx < height_ds and 0 <= col_idx < width_ds):
        score = risk_grid[row_idx, col_idx]
        level = classify_risk(score)
        validation_results.append({'score': score, 'level': level})

val_df = pd.DataFrame(validation_results)
if len(val_df) > 0:
    print("Risk level of confirmed landslide locations:")
    print(val_df['level'].value_counts())
    print()
    high_pct = (val_df['level'] == 'High').mean() * 100
    med_pct  = (val_df['level'] == 'Medium').mean() * 100
    low_pct  = (val_df['level'] == 'Low').mean() * 100
    print(f"  High risk zone   : {high_pct:.1f}% of actual landslides")
    print(f"  Medium risk zone : {med_pct:.1f}% of actual landslides")
    print(f"  Low risk zone    : {low_pct:.1f}% of actual landslides")
    print()
    print(f"Ideally 70%+ of confirmed landslides should fall in")
    print(f"high or medium risk zones. Your result: "
          f"{high_pct + med_pct:.1f}%")

# ----------------------------------------------------------------
# CELL 14 — Risk Distribution Histogram
# ----------------------------------------------------------------

fig, axes = plt.subplots(1, 2, figsize=(13, 4))

# Left — histogram of all risk scores
axes[0].hist(risk_scores, bins=50, color='#2E86C1',
             edgecolor='white', alpha=0.8)
axes[0].axvline(0.35, color='orange', linestyle='--',
                linewidth=2, label='Low/Medium boundary')
axes[0].axvline(0.65, color='red', linestyle='--',
                linewidth=2, label='Medium/High boundary')
axes[0].set_xlabel('Risk Score', fontsize=11)
axes[0].set_ylabel('Number of Pixels', fontsize=11)
axes[0].set_title('Distribution of Risk Scores\nAcross Study Area',
                  fontsize=11, fontweight='bold')
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3)

# Right — pie chart of risk zones
zone_counts = [low_pixels, medium_pixels, high_pixels]
zone_labels = [f'Low\n{low_pixels/total_pixels*100:.1f}%',
               f'Medium\n{medium_pixels/total_pixels*100:.1f}%',
               f'High\n{high_pixels/total_pixels*100:.1f}%']
zone_colors = ['#27AE60', '#F4D03F', '#E74C3C']

axes[1].pie(zone_counts, labels=zone_labels, colors=zone_colors,
            startangle=90, autopct='', pctdistance=0.6,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2})
axes[1].set_title('Risk Zone Coverage\nof Study Area',
                  fontsize=11, fontweight='bold')

plt.suptitle('GeoSentinel+ — Risk Score Analysis',
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUTS_DIR / 'risk_distribution.png',
            dpi=150, bbox_inches='tight')
plt.show()
print("Risk distribution chart saved to outputs/risk_distribution.png")

# ----------------------------------------------------------------
# CELL 15 — Export Prediction Points as CSV for Dashboard
# ----------------------------------------------------------------

# T2 needs this CSV to display colored points on the
# React dashboard map

dashboard_export = grid_df[['lat', 'lon', 'risk_score',
                              'risk_level', 'slope', 'NDVI',
                              'rainfall', 'competency_index',
                              'FS']].copy()

# Round for smaller file size
for col in ['risk_score', 'slope', 'NDVI',
            'rainfall', 'competency_index', 'FS']:
    dashboard_export[col] = dashboard_export[col].round(4)

dashboard_export.to_csv(OUTPUTS_DIR / 'susceptibility_points.csv', index=False)
print(f"Dashboard CSV saved: outputs/susceptibility_points.csv")
print(f"Shape: {dashboard_export.shape}")
print()
print("Share this file with T2 for the dashboard.")

# ----------------------------------------------------------------
# CELL 16 — Final Summary
# ----------------------------------------------------------------

print()
print("=" * 60)
print("SUSCEPTIBILITY MAP — COMPLETE")
print("=" * 60)
print()
print("Files saved to outputs/:")
print("  susceptibility_map.png     — main visual for proposal")
print("  susceptibility_map.tif     — georeferenced for QGIS/dashboard")
print("  risk_distribution.png      — supporting chart for proposal")
print("  susceptibility_points.csv  — share with T2 for dashboard")
print()
print("Risk zone breakdown:")
print(f"  Low    : {low_pixels/total_pixels*100:.1f}%")
print(f"  Medium : {medium_pixels/total_pixels*100:.1f}%")
print(f"  High   : {high_pixels/total_pixels*100:.1f}%")
print()
if len(val_df) > 0:
    print(f"Validation: {high_pct + med_pct:.1f}% of confirmed")
    print(f"landslides fall in medium or high risk zones.")
print()
print("YOUR PART OF THE PROJECT IS COMPLETE.")
print()
print("Next steps:")
print("  → Push all outputs/ to GitHub")
print("  → Share susceptibility_points.csv with T2")
print("  → Share susceptibility_map.tif with T2")
print("  → Tell T3 and T4 to finalize proposal sections")
print("=" * 60)
