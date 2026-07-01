# GeoSentinel+ — Teammate 4 (T4) Repository
## GSI Lithology · Proxy Values · Competency Raster · Landslide Inventory

---

## Role in the Pipeline

```
T3 competency_model.pkl ──┐
GLiM geology (vector) ─────┤──► T4 ──► competency_map.tif ──► T1 (fusion)
NASA COOLR catalog ─────────┘       └──► landslide_labels.csv ──► T1 (labels)
```

T4 produces two deliverables for T1:
- `outputs/competency_map.tif` — rock strength raster, EPSG:4326, 30 m
- `data/processed/landslide_labels.csv` — lat/lon/label (1=landslide, 0=stable)

---

## Study Area (locked — must match T1's GEE export exactly)

```
WEST  = 78.2    EAST  = 80.0
SOUTH = 30.0    NORTH = 31.0
PIXEL_SIZE = 0.000277 degrees (~30 m)
WIDTH  = int((80.0 - 78.2) / 0.000277) = 6498 pixels
HEIGHT = int((31.0 - 30.0) / 0.000277) = 3610 pixels
```

---

## Data Sources

| File | Source | URL |
|------|--------|-----|
| `LiMW_GIS 2015.gdb` | GLiM v1.1, Hartmann & Moosdorf (2012) | Dropbox/CSDMS |
| `Global_Landslide_Catalog_Export_rows.xls` | NASA COOLR | gpm.nasa.gov |

Place both files in `data/raw/` before running notebooks.

---

## Setup

```bash
pip install geopandas rasterio shapely numpy pandas matplotlib scipy scikit-learn joblib openpyxl fiona
```

---

## Notebook Run Order

```
Phase 1 — Independent (run now):
  T4_00_QuickStart.py          environment check
  T4_01_GLiM_Geology.py        load GLiM GDB, clip, explore
  T4_02_Proxy_Values.py        build GR/RHOB/NPHI/competency table
  T4_03_Landslide_Inventory.py filter NASA COOLR for study area
  T4_04_Stable_Points.py       generate label=0 points → landslide_labels.csv ← send to T1

Phase 2 — After T3 sends competency_model.pkl:
  T4_05_Competency_Raster.py   apply model → rasterize → 10-point verify → competency_map.tif ← send to T1
```

---

## Deliverable Specs

### competency_map.tif
| Check | Required |
|-------|---------|
| CRS | EPSG:4326 |
| Resolution | 0.000277° (~30 m) |
| Bounds | left=78.2, bottom=30.0, right=80.0, top=31.0 |
| Dimensions | ~6498 × 3610 pixels |
| Value range | 0.0 – 1.0 (valid pixels only) |
| Nodata | -9999.0 |
| Coverage | >85% valid pixels |
| Format | GTiff, float32 |

### landslide_labels.csv
| Column | Description |
|--------|-------------|
| point_id | integer ID |
| lat | decimal degrees, EPSG:4326 |
| lon | decimal degrees, EPSG:4326 |
| label | 1 = landslide, 0 = stable |

---

## Proxy Values

See `PROXY_VALUES_README.md` for the full derivation of GR/RHOB/NPHI values,
UCS-based competency normalization, and all citations.

---

## Key Design Decisions

**Why GLiM instead of GSI Bhukosh?**
GSI Bhukosh was inaccessible for 48+ hours across multiple attempts. GLiM is the
best publicly available global lithology dataset (1.2 million polygons, built from
92 national geological maps). Noted as a limitation; GLiM classifies all MCT
metamorphics as code `mt` rather than distinguishing phyllite from quartzite.

**Why manual competency scores instead of T3's model?**
Testing T3's `competency_model.pkl` with actual proxy values showed the model
collapses >90% of inputs to 0.500 (trained on 3-bucket labels, not continuous
UCS values). Manual UCS-normalized scores carry real spatial variation and are
fully cited. Notebook 05 switches to T3's model automatically when it returns
differentiating predictions.

**Why 500 m minimum distance for stable points?**
Prevents label leakage: a stable point placed immediately adjacent to a known
landslide would expose the ML model to identical terrain features with opposite
labels. 500 m ≈ 18 pixels at 30 m resolution.
