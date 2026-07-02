# GeoSentinel+

**Landslide Susceptibility Mapping Platform — Garhwal Himalaya**
BYOP 2026 · Hamrock Society · IIT Roorkee

---

## What This Project Does

GeoSentinel+ predicts landslide susceptibility across the Garhwal Himalaya (Tehri, Rudraprayag, Chamoli, Joshimath) using a novel **Lithological Proxy Transfer Framework**. It combines:

- Satellite terrain + vegetation features (GEE/SRTM) — elevation, slope, aspect, curvature, NDVI, rainfall
- Rock competency index — derived from wireline well logs (FORCE 2020) and mapped to Himalayan geology (GSI Bhukosh / GLiM)
- Physics-informed Factor of Safety (Infinite Slope Equation)
- XGBoost binary classifier (ROC-AUC 0.775)

The dashboard visualises the susceptibility map interactively with a Leaflet map, floating glass panels, a probability heatmap layer, and a Groq-powered AI chatbot.

---

## Repository Structure

```
geosentinel-plus/
├── data/
│   ├── raw/                        # Raw inputs (not tracked by git)
│   └── processed/
│       ├── master_features.csv
│       └── surface_features_clean.csv
│
├── pipeline/
│   ├── geology/                    # Geology & competency scripts
│   │   ├── T4_00_QuickStart.py
│   │   ├── T4_01_GLiM_Geology.py
│   │   ├── T4_02_Proxy_Values.py
│   │   ├── T4_03_Landslide_Inventory.py
│   │   ├── T4_04_Stable_Points.py
│   │   ├── T4_05_Competency_Raster.py
│   │   └── PROXY_VALUES_README.md
│   ├── surface/
│   │   └── surface_features.py
│   ├── notebooks/
│   │   ├── GEE_surfacefeatures.js
│   │   ├── feature_fusion.ipynb
│   │   └── model_train.ipynb
│   └── 06_susceptibility_map.py
│
├── notebooks/
│   ├── models/                     # final_model.pkl, baseline_model.pkl, feature_cols.pkl
│   └── outputs/                    # feature_importance.png, confusion_matrix.png, roc_curve.png
│
├── dashboard/
│   ├── backend/                    # FastAPI server
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── render.yaml
│   │   ├── data/                   # CSVs served by the API
│   │   └── outputs/                # Chart PNGs served by the API
│   └── frontend/                   # React + Vite + Tailwind
│       ├── vercel.json
│       └── src/
│           ├── api.js              # Centralised API URL config
│           ├── App.jsx
│           └── components/
│
├── requirements.txt                # Full Python dependencies
└── docs/
```

---

## Quick Start (Run Locally)

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the backend

```bash
cd dashboard/backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Add your Groq API key (free at https://console.groq.com)
echo "GROQ_API_KEY=your_key_here" > .env

uvicorn main:app --reload --port 8000
```

### 3. Start the frontend

```bash
cd dashboard/frontend
npm install
npm run dev
```

Open **http://localhost:5173**

---

## Reproducing the ML Pipeline from Scratch

Follow stages 1–5 to regenerate all data and models from raw inputs.

### Stage 1 — Surface Features (GEE)

1. Open [Google Earth Engine Code Editor](https://code.earthengine.google.com)
2. Run `pipeline/notebooks/GEE_surfacefeatures.js`
3. Export the table to Google Drive as `surface_features_Garhwal-Himalaya.csv`, place in `data/raw/`
4. Run:

```bash
python pipeline/surface/surface_features.py
# → data/processed/surface_features_clean.csv
```

### Stage 2 — Geology & Competency Map

Place in `pipeline/geology/data/raw/`:
- `LiMW_GIS 2015.gdb` — [GLiM global lithology](https://www.geo.uni-hamburg.de/en/geologie/forschung/aquifer/glim.html)
- `Global_Landslide_Catalog_Export_rows.csv` — [NASA COOLR](https://catalog.data.gov/dataset/global-landslide-catalog-export)

```bash
cd pipeline/geology
python T4_00_QuickStart.py
python T4_01_GLiM_Geology.py
python T4_02_Proxy_Values.py
python T4_03_Landslide_Inventory.py
python T4_04_Stable_Points.py
python T4_05_Competency_Raster.py
```

Copy `data/outputs/competency_map.tif` and `data/processed/landslide_labels.csv` to `data/processed/`.

### Stage 3 — Feature Fusion

Run all cells in `pipeline/notebooks/feature_fusion.ipynb`.
Output: `data/processed/master_features.csv`

### Stage 4 — Model Training

Run all cells in `pipeline/notebooks/model_train.ipynb`.
Outputs → `notebooks/models/` and `notebooks/outputs/`.

**Model metrics:**

| Metric | Value |
|---|---|
| Accuracy | 69.4% |
| F1 Score | 0.706 |
| ROC-AUC | 0.775 |
| Spatial CV | 0.620 ± 0.089 |
| Baseline AUC | 0.732 (surface only) |
| Improvement | +0.043 over baseline |

### Stage 5 — Full Susceptibility Map (optional)

```bash
python pipeline/06_susceptibility_map.py
# → pipeline/outputs/susceptibility_map.png + susceptibility_points.csv
```

---

## Deployment

### Backend → Render

1. Go to [render.com](https://render.com) → **New Web Service**
2. Connect your GitHub repo
3. Set **Root Directory** to `dashboard/backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variable: `GROQ_API_KEY` = your key
7. Deploy — note your Render URL (e.g. `https://geosentinel-backend.onrender.com`)

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Import your GitHub repo
3. Set **Root Directory** to `dashboard/frontend`
4. Framework preset: **Vite**
5. Add environment variable: `VITE_API_URL` = your Render backend URL
6. Deploy

> The `vercel.json` in `dashboard/frontend/` already configures the rewrite rules for `/api/*` to your backend.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/points` | All risk points as GeoJSON |
| GET | `/api/labels` | Confirmed landslide sites as GeoJSON |
| GET | `/api/stats` | Risk zone breakdown + model metrics |
| GET | `/api/importance` | Feature importance PNG |
| POST | `/api/predict` | `{"lat": float, "lon": float}` → risk score |
| POST | `/api/chat` | `{"message": str}` → AI response (Groq) |

Interactive docs: `http://localhost:8000/docs`

---

## Novel Contribution

Standard landslide models rely solely on surface features (slope, NDVI, rainfall). GeoSentinel+ introduces the **Lithological Proxy Transfer Framework**:

1. Train a rock competency regressor on wireline well logs (FORCE 2020 — GR, RHOB, NPHI)
2. Assign proxy values to Himalayan rock types via literature (Amadei 1996, Doveton 2017)
3. Rasterize competency from GLiM / GSI Bhukosh geology at 30 m resolution
4. Add a physics-derived Factor of Safety (Infinite Slope Equation) as a feature

This provides subsurface geological context that pure remote sensing cannot capture.

---

## Study Area

- Bounding box: **78.2°E – 80.0°E, 30.0°N – 31.0°N**
- Districts: Tehri Garhwal, Rudraprayag, Chamoli, Joshimath (MCT zone)
- Resolution: 30 m (GEE), downsampled to 300 m for map generation

---

*GeoSentinel+ · BYOP 2026 · Hamrock Society · IIT Roorkee*
