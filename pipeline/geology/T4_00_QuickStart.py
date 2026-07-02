# %% T4_00 — Environment Check
# Run this first to confirm all packages are installed.

import sys
print(f"Python {sys.version}")

# %%
packages = ["numpy","pandas","geopandas","rasterio","shapely",
            "matplotlib","scipy","sklearn","joblib","openpyxl","fiona"]
missing = []
for p in packages:
    try:
        mod = __import__(p)
        print(f"  ✓ {p} {getattr(mod,'__version__','ok')}")
    except ImportError:
        print(f"  ✗ {p} MISSING")
        missing.append(p)

if missing:
    print(f"\nInstall missing: pip install {' '.join(missing)}")
else:
    print("\nAll packages ready.")

# %%
import os
from pathlib import Path
import fiona

# Resolved relative to this script's location — no manual path editing needed
BASE_DIR = Path(__file__).parent

GDB_PATH = BASE_DIR / "data" / "raw" / "LiMW_GIS 2015.gdb"
XLS_PATH = BASE_DIR / "data" / "raw" / "Global_Landslide_Catalog_Export_rows.xls"

print("GDB  found:", os.path.exists(GDB_PATH))
print("XLS  found:", os.path.exists(XLS_PATH))

# %%
# Show layers inside the GDB
if os.path.exists(GDB_PATH):
    for i, name in enumerate(fiona.listlayers(GDB_PATH)):
        with fiona.open(GDB_PATH, layer=i) as src:
            print(f"Layer {i}: '{name}' | {src.schema['geometry']} | {len(src)} records")

# %%
# Study area constants — must match T1's GEE export exactly
WEST, SOUTH, EAST, NORTH = 78.2, 30.0, 80.0, 31.0
PIXEL_SIZE = 0.000277
WIDTH  = int((EAST  - WEST)  / PIXEL_SIZE)
HEIGHT = int((NORTH - SOUTH) / PIXEL_SIZE)
print(f"Grid: {WIDTH} × {HEIGHT} pixels  |  "
      f"{(EAST-WEST)*111:.0f} km × {(NORTH-SOUTH)*111:.0f} km")
