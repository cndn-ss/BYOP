"""
GeoSentinel+ — FastAPI Backend
Run: uvicorn main:app --reload --port 8000
"""

import os
from pathlib import Path
from typing import Optional

# load .env so GROQ_API_KEY is available
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ── paths ──────────────────────────────────────────────────────
BASE   = Path(__file__).parent
DATA   = BASE / "data"
OUT    = BASE / "outputs"

# ── model + data (loaded once at startup) ──────────────────────
model        = joblib.load(BASE / "final_model.pkl")
feature_cols = joblib.load(BASE / "feature_cols.pkl")
points_df    = pd.read_csv(DATA / "susceptibility_points.csv")
labels_df    = pd.read_csv(DATA / "landslide_labels.csv")
master_df    = pd.read_csv(DATA / "master_features.csv")   # full features for /predict

# ── app ────────────────────────────────────────────────────────
app = FastAPI(title="TerraSense API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── helpers ────────────────────────────────────────────────────
def classify_risk(score: float) -> str:
    if score < 0.35:
        return "Low"
    elif score < 0.65:
        return "Medium"
    return "High"


# ══════════════════════════════════════════════════════════════
# ENDPOINT 1 — Susceptibility Points → GeoJSON
# ══════════════════════════════════════════════════════════════
@app.get("/api/points")
def get_points():
    features = []
    for _, row in points_df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["lon"]), float(row["lat"])],
            },
            "properties": {
                "risk_score":       round(float(row["risk_score"]), 3),
                "risk_level":       str(row["risk_level"]),
                "slope":            round(float(row["slope"]), 2),
                "NDVI":             round(float(row["NDVI"]), 3),
                "rainfall":         round(float(row["rainfall"]), 1),
                "competency_index": round(float(row["competency_index"]), 3),
                "elevation":        round(float(row["elevation"]), 1),
                "FS":               round(float(row["FS"]), 3),
            },
        })
    return {"type": "FeatureCollection", "features": features}


# ══════════════════════════════════════════════════════════════
# ENDPOINT 2 — Confirmed Landslide Labels → GeoJSON
# ══════════════════════════════════════════════════════════════
@app.get("/api/labels")
def get_labels():
    landslides = labels_df[labels_df["label"] == 1]
    features = []
    for _, row in landslides.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["lon"]), float(row["lat"])],
            },
            "properties": {"type": "confirmed_landslide"},
        })
    return {"type": "FeatureCollection", "features": features}


# ══════════════════════════════════════════════════════════════
# ENDPOINT 3 — Stats (risk zone breakdown + model metrics)
# ══════════════════════════════════════════════════════════════
@app.get("/api/stats")
def get_stats():
    total  = len(points_df)
    low    = int((points_df["risk_level"] == "Low").sum())
    medium = int((points_df["risk_level"] == "Medium").sum())
    high   = int((points_df["risk_level"] == "High").sum())

    return {
        "risk_zones": {
            "low":    round(low    / total * 100, 1),
            "medium": round(medium / total * 100, 1),
            "high":   round(high   / total * 100, 1),
            "low_count":    low,
            "medium_count": medium,
            "high_count":   high,
        },
        "model_metrics": {
            "model":        "XGBoost",
            "accuracy":     "69.4%",
            "f1_score":     "0.706",
            "roc_auc":      "0.775",
            "spatial_cv":   "0.620 ± 0.089",
            "baseline_auc": "0.732 (surface only)",
            "improvement":  "+0.043 over baseline",
            "train_points": 193,
        },
    }


# ══════════════════════════════════════════════════════════════
# ENDPOINT 4 — Feature Importance PNG
# ══════════════════════════════════════════════════════════════
@app.get("/api/importance")
def get_importance():
    path = OUT / "feature_importance.png"
    if not path.exists():
        raise HTTPException(404, "feature_importance.png not found")
    return FileResponse(str(path), media_type="image/png")


# ══════════════════════════════════════════════════════════════
# ENDPOINT 5 — Live Predict (lat/lon → risk)
# ══════════════════════════════════════════════════════════════
class PredictRequest(BaseModel):
    lat: float
    lon: float

@app.post("/api/predict")
def predict(req: PredictRequest):
    """
    Find the nearest training point and run model on its features.
    Returns risk score, level, and top-3 contributing features.
    """
    # nearest-neighbor lookup using master_features (has all feature cols)
    dists = np.sqrt(
        (master_df["lat"] - req.lat) ** 2 +
        (master_df["lon"] - req.lon) ** 2
    )
    nearest = master_df.iloc[dists.idxmin()]

    feature_values = {col: float(nearest[col]) for col in feature_cols}
    X = pd.DataFrame([feature_values])
    score = float(model.predict_proba(X)[0][1])

    # top-3 features by importance
    importances = dict(zip(feature_cols, model.feature_importances_))
    top3 = sorted(importances, key=importances.get, reverse=True)[:3]

    return {
        "lat":        req.lat,
        "lon":        req.lon,
        "risk_score": round(score, 3),
        "risk_level": classify_risk(score),
        "features":   feature_values,
        "top_features": top3,
    }


# ══════════════════════════════════════════════════════════════
# ENDPOINT 6 — Chatbot (Anthropic claude-sonnet)
# ══════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """
You are GeoSentinel+ Assistant, an AI built into a landslide
susceptibility mapping platform for the Garhwal Himalaya region
in Uttarakhand, India. The study area covers Tehri, Rudraprayag,
Chamoli and Joshimath districts.

Project context:
- Platform       : GeoSentinel+ (BYOP 2026, IIT Roorkee)
- Study area     : 78.2–80.0 lon, 30.0–31.0 lat
- Model          : XGBoost binary classifier
- Features       : slope, aspect, curvature, NDVI, rainfall,
                   competency_index, elevation, FS
- Training points: 193
- Novel approach : Lithological Proxy Transfer Framework —
                   rock competency from well logs (FORCE 2020)
                   mapped to Himalayan rocks via GSI Bhukosh
- Risk zones     : Low (<0.35), Medium (0.35–0.65), High (>0.65)
- Accuracy       : 69.4%, F1: 0.706, ROC-AUC: 0.775

Answer questions about risk levels, features, geology of Garhwal
Himalaya, the MCT zone, Factor of Safety, and the model.
Keep answers under 4 sentences. Use simple language.
Do not invent specific scores for locations not in the data.
"""

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Empty message")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(500, "GROQ_API_KEY not set in .env")

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": req.message},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── dev entry point ────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
