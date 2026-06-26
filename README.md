# BYOP
structure:

BYOP/
│
├── data/
│   ├── raw/                        ← original downloaded files, never modified
│   │   ├── force2020/              ← FORCE 2020 well log files (T3 downloads)
│   │   ├── uttarakhand_geology.shp ← GSI Bhukosh shapefile (T4 downloads)
│   │   └── nasa_landslide.csv      ← NASA landslide catalog (T2 downloads)
│   │
│   └── processed/                  ← cleaned files ready for model
│       ├── surface_features_clean.csv   ← YOUR FILE — goes here
│       ├── competency_map.tif           ← T4's output — goes here
│       ├── landslide_labels.csv         ← T2/T3's output — goes here
│       └── master_features.csv          ← fusion output — goes here later
│
├── notebooks/
│   ├── 01_well_log_competency_model.ipynb   ← T3's notebook
│   ├── 02_lithology_mapping.ipynb           ← T4's notebook
│   ├── 03_GEE_surface_features.js           ← YOUR GEE script
│   ├── 04_feature_fusion.ipynb              ← YOUR notebook
│   └── 05_model_training.ipynb              ← YOUR notebook
│
├── outputs/
│   ├── susceptibility_map.png       ← final map image
│   ├── susceptibility_map.tif       ← final map raster
│   ├── feature_importance.png       ← model chart
│   ├── confusion_matrix.png         ← model chart
│   └── roc_curve.png                ← model chart
│
├── models/
│   ├── competency_model.pkl         ← T3's trained model
│   └── final_model.pkl              ← your trained classifier
│
├── dashboard/                       ← T2's folder
│   ├── frontend/                    ← React app
│   └── backend/                     ← Flask API
│
├── .gitignore
└── README.md