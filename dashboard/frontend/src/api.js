// In dev: Vite proxy forwards /api/* to localhost:8000
// In production: set VITE_API_URL=https://your-render-backend.onrender.com
const BASE = import.meta.env.VITE_API_URL || ''

export const API = {
  points:     `${BASE}/api/points`,
  labels:     `${BASE}/api/labels`,
  stats:      `${BASE}/api/stats`,
  importance: `${BASE}/api/importance`,
  predict:    `${BASE}/api/predict`,
  chat:       `${BASE}/api/chat`,
}
