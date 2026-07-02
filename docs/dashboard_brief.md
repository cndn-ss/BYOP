# TerraSense — Complete Dashboard Brief for T2

## Project Name

**TerraSense** — Landslide Susceptibility Mapping Platform
Study Area: Garhwal Himalaya (Tehri, Rudraprayag, Chamoli, Joshimath)

## Files T2 Needs

These files will be shared once the ML notebooks finish running.
T2 can build everything with dummy data until then.

```
outputs/susceptibility_points.csv    main data file for map
outputs/feature_importance.png       chart for right panel
outputs/confusion_matrix.png         optional detail view
outputs/roc_curve.png                optional detail view
data/processed/landslide_labels.csv  for black triangle overlay
```

---

## Tech Stack

```
Frontend  : React + react-leaflet (Leaflet.js)
Charts    : Recharts or Chart.js
Styling   : Tailwind CSS
Backend   : Flask (Python)
Chatbot   : Anthropic API (claude-sonnet-4-6)
```

Install commands:

```bash
# Frontend
npm create vite@latest terrasense-frontend -- --template react
cd terrasense-frontend
npm install leaflet react-leaflet recharts tailwindcss

# Backend
pip install flask flask-cors pandas anthropic
```

---

## Application Structure

```
terrasense/
├── backend/
│   ├── app.py
│   ├── data/
│   │   ├── susceptibility_points.csv
│   │   └── landslide_labels.csv
│   └── outputs/
│       ├── feature_importance.png
│       ├── confusion_matrix.png
│       └── roc_curve.png
└── frontend/
    └── src/
        ├── App.jsx
        ├── components/
        │   ├── Map.jsx
        │   ├── SummaryCards.jsx
        │   ├── FeatureImportance.jsx
        │   ├── ModelMetrics.jsx
        │   └── Chatbot.jsx
        └── index.css
```

---

## Page 1 — Main Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  TerraSense                    [Dashboard] [About] [Chatbot]     │
│  Landslide Susceptibility Mapping — Garhwal Himalaya             │
├───────────────────────────┬──────────────────────────────────────┤
│                           │  RISK SUMMARY CARDS                  │
│                           │  ┌─────────┐┌─────────┐┌─────────┐  │
│                           │  │   LOW   ││ MEDIUM  ││  HIGH   │  │
│   INTERACTIVE MAP         │  │  XX%    ││  XX%    ││  XX%    │  │
│                           │  │ of area ││ of area ││ of area │  │
│   Leaflet map centered    │  └─────────┘└─────────┘└─────────┘  │
│   on Garhwal Himalaya     ├──────────────────────────────────────┤
│                           │  FEATURE IMPORTANCE                  │
│   Green  = Low risk       │                                      │
│   Yellow = Medium risk    │  slope         ████████████  0.XX   │
│   Red    = High risk      │  rainfall      ███████████   0.XX   │
│   Black▲ = Real landslide │  competency    ██████        0.XX   │
│                           │  NDVI          █████         0.XX   │
│   Click point → popup     │  elevation     ████          0.XX   │
│                           │  aspect        ███           0.XX   │
│   Layer controls:         │  curvature     ██            0.XX   │
│   ☑ Risk Points           ├──────────────────────────────────────┤
│   ☑ Landslide Sites       │  MODEL PERFORMANCE                   │
│   ○ Satellite  ● Terrain  │                                      │
│                           │  Model      : XGBoost                │
│                           │  Accuracy   : XX%                    │
│                           │  F1 Score   : XX                     │
│                           │  ROC-AUC    : XX                     │
│                           │  Spatial CV : XX ± XX                │
│                           │  Baseline   : XX (surface only)      │
│                           │  Improvement: +XX over baseline      │
└───────────────────────────┴──────────────────────────────────────┘
```

---

## Map Detail — Click Popup

When user clicks any colored point on the map this popup appears:

```
┌──────────────────────────┐
│  RISK ASSESSMENT         │
│  ● HIGH RISK             │
│  Score: 0.73             │
├──────────────────────────┤
│  Slope       : 42.3°     │
│  NDVI        : 0.21      │
│  Rainfall    : 1840 mm   │
│  Competency  : 0.28      │
│  Elevation   : 2341 m    │
└──────────────────────────┘
```

Color of the popup header matches risk level:

- Red header = High risk
- Yellow header = Medium risk
- Green header = Low risk

---

## Flask Backend — All Endpoints

T2 builds these 5 endpoints in `backend/app.py`:

```python
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import anthropic
import json
import os

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────
# ENDPOINT 1 — Susceptibility Points
# Returns all risk points as GeoJSON
# Used by: Map.jsx to color the points
# ─────────────────────────────────────────
@app.route('/api/points', methods=['GET'])
def get_points():
    df = pd.read_csv('data/susceptibility_points.csv')

    features = []
    for _, row in df.iterrows():
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [row['lon'], row['lat']]
            },
            'properties': {
                'risk_score'       : round(float(row['risk_score']), 3),
                'risk_level'       : row['risk_level'],
                'slope'            : round(float(row['slope']), 2),
                'NDVI'             : round(float(row['NDVI']), 3),
                'rainfall'         : round(float(row['rainfall']), 1),
                'competency_index' : round(float(row['competency_index']), 3),
                'elevation'        : round(float(row['elevation']), 1)
            }
        })

    return jsonify({'type': 'FeatureCollection', 'features': features})


# ─────────────────────────────────────────
# ENDPOINT 2 — Landslide Inventory Points
# Returns confirmed landslide locations
# Used by: Map.jsx for black triangle overlay
# ─────────────────────────────────────────
@app.route('/api/labels', methods=['GET'])
def get_labels():
    df = pd.read_csv('data/landslide_labels.csv')
    landslides = df[df['label'] == 1]

    features = []
    for _, row in landslides.iterrows():
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [row['lon'], row['lat']]
            },
            'properties': {'type': 'confirmed_landslide'}
        })

    return jsonify({'type': 'FeatureCollection', 'features': features})


# ─────────────────────────────────────────
# ENDPOINT 3 — Risk Zone Statistics
# Returns percentage breakdown and model metrics
# Used by: SummaryCards.jsx and ModelMetrics.jsx
# ─────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
def get_stats():
    df = pd.read_csv('data/susceptibility_points.csv')
    total = len(df)

    low    = (df['risk_level'] == 'Low').sum()
    medium = (df['risk_level'] == 'Medium').sum()
    high   = (df['risk_level'] == 'High').sum()

    return jsonify({
        'risk_zones': {
            'low'    : round(low    / total * 100, 1),
            'medium' : round(medium / total * 100, 1),
            'high'   : round(high   / total * 100, 1)
        },
        'model_metrics': {
            'model'       : 'XGBoost',
            'accuracy'    : 'FILL FROM CELL 15',
            'f1_score'    : 'FILL FROM CELL 15',
            'roc_auc'     : 'FILL FROM CELL 15',
            'spatial_cv'  : 'FILL FROM CELL 15',
            'baseline_auc': 'FILL FROM CELL 15',
            'improvement' : 'FILL FROM CELL 15',
            'train_points': 242
        }
    })


# ─────────────────────────────────────────
# ENDPOINT 4 — Feature Importance Image
# Returns the PNG chart directly
# Used by: FeatureImportance.jsx as img src
# ─────────────────────────────────────────
@app.route('/api/importance', methods=['GET'])
def get_importance():
    return send_file('outputs/feature_importance.png',
                     mimetype='image/png')


# ─────────────────────────────────────────
# ENDPOINT 5 — Chatbot
# Takes user message, returns AI response
# Used by: Chatbot.jsx
# ─────────────────────────────────────────

SYSTEM_PROMPT = """
You are GeoSentinel+ Assistant, an AI built into a landslide
susceptibility mapping platform for the Garhwal Himalaya region
in Uttarakhand, India. The study area covers Tehri, Rudraprayag,
Chamoli and Joshimath districts.

Project context:
- Platform name    : GeoSentinel Plus
- Study area       : 78.2 to 80.0 longitude, 30.0 to 31.0 latitude
- Districts covered: Tehri Garhwal, Rudraprayag, Chamoli, Joshimath
- Model used       : XGBoost binary classifier
- Features used    : slope, aspect, curvature, NDVI, rainfall,
                     competency_index, elevation
- Training points  : 242 (121 landslide, 121 stable)
- Novel approach   : Lithological Proxy Transfer Framework —
                     subsurface rock competency derived from
                     well log data (GR, RHOB, NPHI from FORCE 2020)
                     mapped onto Himalayan rock types via GSI Bhukosh
- Risk zones       : Low (score < 0.35), Medium (0.35-0.65),
                     High (> 0.65)
- Geology          : MCT zone, phyllites and schists dominate,
                     competency scores range 0.10 to 0.68

You can answer questions about:
- Why a specific area is high or low risk
- What each feature (slope, NDVI, rainfall etc.) means
- What the competency index represents
- How the ML model works
- What landslide susceptibility mapping is
- The geology of Garhwal Himalaya
- What the MCT zone is
- How to interpret the map colors

Keep answers under 4 sentences. Use simple language.
Do not make up specific risk scores for locations not in the data.
"""

@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

    response = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{'role': 'user', 'content': user_message}]
    )

    return jsonify({'response': response.content[0].text})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## React Frontend Components

### App.jsx — Main Layout

```jsx
import Map from "./components/Map";
import SummaryCards from "./components/SummaryCards";
import FeatureImportance from "./components/FeatureImportance";
import ModelMetrics from "./components/ModelMetrics";
import Chatbot from "./components/Chatbot";
import { useState } from "react";

export default function App() {
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      {/* Navbar */}
      <nav className="bg-gray-800 px-6 py-3 flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-green-400">TerraSense</h1>
          <p className="text-xs text-gray-400">
            Landslide Susceptibility Mapping — Garhwal Himalaya
          </p>
        </div>
        <button
          onClick={() => setChatOpen(true)}
          className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded text-sm"
        >
          Ask TerraSense AI
        </button>
      </nav>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Map — Left Side */}
        <div className="flex-1">
          <Map />
        </div>

        {/* Right Panel */}
        <div className="w-80 bg-gray-800 overflow-y-auto flex flex-col gap-4 p-4">
          <SummaryCards />
          <FeatureImportance />
          <ModelMetrics />
        </div>
      </div>

      {/* Chatbot Panel */}
      {chatOpen && <Chatbot onClose={() => setChatOpen(false)} />}
    </div>
  );
}
```

---

### Map.jsx — Interactive Leaflet Map

```jsx
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Marker,
  Popup,
  LayersControl,
} from "react-leaflet";
import { useEffect, useState } from "react";
import L from "leaflet";

const riskColor = (level) => {
  if (level === "High") return "#E74C3C";
  if (level === "Medium") return "#F4D03F";
  return "#27AE60";
};

const triangleIcon = L.divIcon({
  html: "▲",
  className: "text-black text-xs font-bold",
  iconSize: [12, 12],
});

export default function Map() {
  const [points, setPoints] = useState([]);
  const [labels, setLabels] = useState([]);

  useEffect(() => {
    fetch("http://localhost:5000/api/points")
      .then((r) => r.json())
      .then((data) => setPoints(data.features));

    fetch("http://localhost:5000/api/labels")
      .then((r) => r.json())
      .then((data) => setLabels(data.features));
  }, []);

  return (
    <MapContainer
      center={[30.5, 79.1]}
      zoom={9}
      style={{ height: "100%", width: "100%" }}
    >
      <LayersControl position="topright">
        {/* Base layers */}
        <LayersControl.BaseLayer checked name="Terrain">
          <TileLayer url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png" />
        </LayersControl.BaseLayer>

        <LayersControl.BaseLayer name="Satellite">
          <TileLayer url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" />
        </LayersControl.BaseLayer>

        {/* Risk Points Overlay */}
        <LayersControl.Overlay checked name="Risk Points">
          <>
            {points.map((f, i) => (
              <CircleMarker
                key={i}
                center={[f.geometry.coordinates[1], f.geometry.coordinates[0]]}
                radius={4}
                fillColor={riskColor(f.properties.risk_level)}
                color="white"
                weight={0.5}
                fillOpacity={0.8}
              >
                <Popup>
                  <div className="text-sm">
                    <div
                      style={{
                        background: riskColor(f.properties.risk_level),
                        padding: "4px 8px",
                        borderRadius: "4px",
                        marginBottom: "6px",
                        color: "white",
                        fontWeight: "bold",
                      }}
                    >
                      {f.properties.risk_level.toUpperCase()} RISK — Score:{" "}
                      {f.properties.risk_score}
                    </div>
                    <table>
                      <tbody>
                        {[
                          ["Slope", `${f.properties.slope}°`],
                          ["NDVI", f.properties.NDVI],
                          ["Rainfall", `${f.properties.rainfall} mm/yr`],
                          ["Competency", f.properties.competency_index],
                          ["Elevation", `${f.properties.elevation} m`],
                        ].map(([k, v]) => (
                          <tr key={k}>
                            <td className="pr-3 text-gray-500">{k}</td>
                            <td className="font-medium">{v}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </>
        </LayersControl.Overlay>

        {/* Confirmed Landslide Sites */}
        <LayersControl.Overlay checked name="Confirmed Landslides">
          <>
            {labels.map((f, i) => (
              <Marker
                key={i}
                position={[
                  f.geometry.coordinates[1],
                  f.geometry.coordinates[0],
                ]}
                icon={triangleIcon}
              >
                <Popup>Confirmed Landslide Site</Popup>
              </Marker>
            ))}
          </>
        </LayersControl.Overlay>
      </LayersControl>
    </MapContainer>
  );
}
```

---

### SummaryCards.jsx

```jsx
import { useEffect, useState } from "react";

export default function SummaryCards() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch("http://localhost:5000/api/stats")
      .then((r) => r.json())
      .then(setStats);
  }, []);

  if (!stats) return <div className="text-gray-400 text-sm">Loading...</div>;

  const cards = [
    { label: "Low Risk", value: stats.risk_zones.low, color: "#27AE60" },
    { label: "Medium Risk", value: stats.risk_zones.medium, color: "#F4D03F" },
    { label: "High Risk", value: stats.risk_zones.high, color: "#E74C3C" },
  ];

  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-300 mb-2">
        RISK ZONE BREAKDOWN
      </h2>
      <div className="flex gap-2">
        {cards.map((c) => (
          <div
            key={c.label}
            className="flex-1 rounded p-3 text-center"
            style={{
              background: c.color + "22",
              border: `1px solid ${c.color}`,
            }}
          >
            <div className="text-2xl font-bold" style={{ color: c.color }}>
              {c.value}%
            </div>
            <div className="text-xs text-gray-300 mt-1">{c.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

### FeatureImportance.jsx

```jsx
export default function FeatureImportance() {
  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-300 mb-2">
        FEATURE IMPORTANCE
      </h2>
      <img
        src="http://localhost:5000/api/importance"
        alt="Feature Importance"
        className="w-full rounded"
      />
    </div>
  );
}
```

---

### ModelMetrics.jsx

```jsx
import { useEffect, useState } from "react";

export default function ModelMetrics() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch("http://localhost:5000/api/stats")
      .then((r) => r.json())
      .then(setStats);
  }, []);

  if (!stats) return null;

  const m = stats.model_metrics;
  const rows = [
    ["Model", m.model],
    ["Accuracy", m.accuracy],
    ["F1 Score", m.f1_score],
    ["ROC-AUC", m.roc_auc],
    ["Spatial CV", m.spatial_cv],
    ["Baseline AUC", m.baseline_auc],
    ["Improvement", m.improvement],
    ["Data Points", m.train_points],
  ];

  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-300 mb-2">
        MODEL PERFORMANCE
      </h2>
      <table className="w-full text-sm">
        <tbody>
          {rows.map(([k, v]) => (
            <tr key={k} className="border-b border-gray-700">
              <td className="py-1 text-gray-400">{k}</td>
              <td className="py-1 text-right font-medium text-white">{v}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

### Chatbot.jsx

```jsx
import { useState } from "react";

export default function Chatbot({ onClose }) {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Hi! I am the TerraSense AI assistant. Ask me anything about the landslide risk map, the geology of Garhwal Himalaya, or how the model works.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:5000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "bot", text: data.response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "Sorry, something went wrong. Please try again." },
      ]);
    }
    setLoading(false);
  };

  return (
    <div
      className="fixed bottom-4 right-4 w-80 bg-gray-800 rounded-xl
                    shadow-2xl flex flex-col border border-gray-700"
      style={{ height: "420px" }}
    >
      {/* Header */}
      <div
        className="bg-green-700 rounded-t-xl px-4 py-3
                      flex justify-between items-center"
      >
        <span className="font-semibold text-white">TerraSense AI</span>
        <button onClick={onClose} className="text-white hover:text-gray-200">
          ✕
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`text-sm px-3 py-2 rounded-lg max-w-xs
              ${
                msg.role === "user"
                  ? "bg-green-700 self-end text-white"
                  : "bg-gray-700 self-start text-gray-100"
              }`}
          >
            {msg.text}
          </div>
        ))}
        {loading && (
          <div
            className="bg-gray-700 self-start text-gray-400
                          text-sm px-3 py-2 rounded-lg"
          >
            Thinking...
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-gray-700 flex gap-2">
        <input
          className="flex-1 bg-gray-700 text-white text-sm rounded
                     px-3 py-2 outline-none"
          placeholder="Ask a question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button
          onClick={sendMessage}
          className="bg-green-600 hover:bg-green-700 text-white
                     text-sm px-3 py-2 rounded"
        >
          Send
        </button>
      </div>
    </div>
  );
}
```

---

## T2 Priority Order

```
Day 1 — Today
  Set up Flask project with all 5 endpoints using dummy data
  Set up React project with Leaflet map centered on Garhwal
  Get map displaying with hardcoded test points in 3 colors
  Build chatbot panel and connect to Anthropic API

Day 2
  Connect /api/points to real susceptibility_points.csv
  Add click popup with feature values
  Build SummaryCards and ModelMetrics components
  Add layer controls (show/hide risk points and landslide sites)

Day 3
  Connect all components to real Flask endpoints
  Fill in actual model metric numbers from ML notebook Cell 15
  Test full flow end to end
  Polish styling

Day 4
  Write README with how to run instructions
  Final testing and bug fixes
```

---

## Environment Variable for Chatbot

T2 should never hardcode the Anthropic API key.
Store it as an environment variable:

```bash
# Windows
set ANTHROPIC_API_KEY=your_key_here

# Mac/Linux
export ANTHROPIC_API_KEY=your_key_here
```

Get the API key from: https://console.anthropic.com

---

_TerraSense | BYOP 2026 | Hamrock Society | IIT Roorkee_
