import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// ── Risk colours ────────────────────────────────────────────────
const riskColor = (level) => {
  if (level === 'High')   return '#ef4444'
  if (level === 'Medium') return '#f59e0b'
  return '#22c55e'
}

// ── Score → RGBA for heatmap ────────────────────────────────────
// green (0) → yellow (0.5) → red (1)
function scoreToRgba(score, alpha = 0.55) {
  const s = Math.max(0, Math.min(1, score))
  let r, g, b
  if (s < 0.5) {
    // green → yellow
    const t = s / 0.5
    r = Math.round(34  + t * (251 - 34))
    g = Math.round(197 + t * (191 - 197))
    b = Math.round(94  + t * (36  - 94))
  } else {
    // yellow → red
    const t = (s - 0.5) / 0.5
    r = Math.round(251 + t * (239 - 251))
    g = Math.round(191 + t * (68  - 191))
    b = Math.round(36  + t * (68  - 36))
  }
  return `rgba(${r},${g},${b},${alpha})`
}

export default function MapView({ navHeight = 48 }) {
  const mapRef    = useRef(null)
  const mapObjRef = useRef(null)

  useEffect(() => {
    if (mapObjRef.current) return

    const map = L.map(mapRef.current, {
      center: [30.5, 79.1],
      zoom: 9,
      zoomControl: false,
    })
    mapObjRef.current = map

    /* ── Base layers ──────────────────────────────────────── */
    const terrain = L.tileLayer(
      'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
      { attribution: '© OpenTopoMap', maxZoom: 17 }
    )
    const satellite = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { attribution: '© Esri', maxZoom: 19 }
    )
    const street = L.tileLayer(
      'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      { attribution: '© OpenStreetMap', maxZoom: 19 }
    )
    terrain.addTo(map)

    /* ── Overlay layers ───────────────────────────────────── */
    const riskLayer   = L.layerGroup().addTo(map)
    const labelLayer  = L.layerGroup().addTo(map)
    const heatmapLayer = L.layerGroup()   // off by default

    /* ── Layer control ────────────────────────────────────── */
    const layerCtrl = L.control.layers(
      { Terrain: terrain, Satellite: satellite, Street: street },
      {
        'Risk Points':         riskLayer,
        'Confirmed Landslides': labelLayer,
        'Risk Heatmap':        heatmapLayer,
      },
      { position: 'topright', collapsed: true }
    ).addTo(map)

    // push layer control below navbar
    layerCtrl.getContainer().style.marginTop = (navHeight + 8) + 'px'

    /* ── Legend + zoom row — bottom left ──────────────────── */
    const bottomCtrl = L.control({ position: 'bottomleft' })
    bottomCtrl.onAdd = () => {
      const wrap = L.DomUtil.create('div', '')
      wrap.style.cssText = 'display:flex;align-items:flex-end;gap:8px;'

      const legend = L.DomUtil.create('div', '', wrap)
      legend.style.cssText = `
        background:rgba(255,255,255,0.88);
        backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
        border:1px solid rgba(0,0,0,0.09);border-radius:12px;
        padding:10px 14px;font-size:11px;font-family:system-ui,sans-serif;
        color:#374151;line-height:1.9;box-shadow:0 4px 20px rgba(0,0,0,0.10);
      `
      legend.innerHTML = `
        <div style="color:#9ca3af;font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px">Legend</div>
        <div style="display:flex;align-items:center;gap:7px"><span style="background:#22c55e;width:9px;height:9px;border-radius:50%;display:inline-block;flex-shrink:0"></span>Low risk</div>
        <div style="display:flex;align-items:center;gap:7px"><span style="background:#f59e0b;width:9px;height:9px;border-radius:50%;display:inline-block;flex-shrink:0"></span>Medium risk</div>
        <div style="display:flex;align-items:center;gap:7px"><span style="background:#ef4444;width:9px;height:9px;border-radius:50%;display:inline-block;flex-shrink:0"></span>High risk</div>
        <div style="display:flex;align-items:center;gap:7px"><span style="font-size:11px;color:#374151;flex-shrink:0">▲</span>Confirmed landslide</div>
      `

      const zoomWrap = L.DomUtil.create('div', 'ts-zoom-wrap', wrap)

      const zoomIn  = L.DomUtil.create('button', 'ts-zoom-btn', zoomWrap)
      zoomIn.innerHTML  = '+'
      zoomIn.title      = 'Zoom in'
      L.DomEvent.on(zoomIn,  'click', e => { L.DomEvent.stop(e); map.zoomIn() })

      const zoomOut = L.DomUtil.create('button', 'ts-zoom-btn', zoomWrap)
      zoomOut.innerHTML = '−'
      zoomOut.title     = 'Zoom out'
      L.DomEvent.on(zoomOut, 'click', e => { L.DomEvent.stop(e); map.zoomOut() })

      L.DomEvent.disableClickPropagation(wrap)
      L.DomEvent.disableScrollPropagation(wrap)
      return wrap
    }
    bottomCtrl.addTo(map)

    /* ── Build popup HTML ─────────────────────────────────── */
    const buildPopup = (p, col) => `
      <div style="font-family:system-ui;font-size:12px;min-width:190px">
        <div style="background:${col};color:white;font-weight:700;padding:5px 10px;
                    border-radius:7px;margin-bottom:8px">
          ${p.risk_level.toUpperCase()} RISK &nbsp;·&nbsp; Score: ${p.risk_score}
        </div>
        <table style="width:100%;border-collapse:collapse">
          ${[
            ['Slope',             `${p.slope}°`],
            ['NDVI',               p.NDVI],
            ['Rainfall',          `${p.rainfall} mm/yr`],
            ['Competency',         p.competency_index],
            ['Elevation',         `${p.elevation} m`],
            ['Factor of Safety',   p.FS],
          ].map(([k,v]) => `
            <tr style="border-bottom:1px solid #f3f4f6">
              <td style="padding:3px 10px 3px 0;color:#6b7280;font-size:11px">${k}</td>
              <td style="padding:3px 0;font-weight:600;font-size:11px">${v}</td>
            </tr>`).join('')}
        </table>
      </div>`

    /* ── Fetch & render risk points ───────────────────────── */
    fetch('/api/points')
      .then(r => r.json())
      .then(data => {
        const features = data.features || []
        features.forEach(f => {
          const p   = f.properties
          const lat = f.geometry.coordinates[1]
          const lon = f.geometry.coordinates[0]
          const col = riskColor(p.risk_level)

          // ── Circle marker — popup opens ABOVE the point ──
          L.circleMarker([lat, lon], {
            radius: 5, fillColor: col,
            color: 'white', weight: 0.8, fillOpacity: 0.88,
          })
            .bindPopup(buildPopup(p, col), {
              offset: L.point(0, -8),   // shift popup up above the dot
              autoPan: true,
            })
            .addTo(riskLayer)

          // ── Heatmap tile: filled circle, no border, translucent ──
          L.circleMarker([lat, lon], {
            radius:      18,
            fillColor:   scoreToRgba(p.risk_score, 0.55),
            color:       'transparent',
            weight:      0,
            fillOpacity: 1,
          })
            .bindPopup(buildPopup(p, col), { offset: L.point(0, -18) })
            .addTo(heatmapLayer)
        })
      })
      .catch(console.error)

    /* ── Fetch & render landslide labels ──────────────────── */
    fetch('/api/labels')
      .then(r => r.json())
      .then(data => {
        const icon = L.divIcon({
          html: '<span style="font-size:13px;color:#1e293b;line-height:1">▲</span>',
          className: '', iconSize: [13,13], iconAnchor: [6,6],
        })
        ;(data.features || []).forEach(f => {
          const [lon, lat] = f.geometry.coordinates
          L.marker([lat, lon], { icon })
            .bindPopup(
              '<span style="font-size:12px;font-weight:600">Confirmed Landslide Site</span>',
              { offset: L.point(0, -8) }
            )
            .addTo(labelLayer)
        })
      })
      .catch(console.error)

    return () => { map.remove(); mapObjRef.current = null }
  }, [])

  return <div ref={mapRef} style={{ height: '100%', width: '100%' }} />
}
