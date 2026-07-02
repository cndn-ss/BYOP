import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.heat'
import { API } from '../api'

const riskColor = (level) => {
  if (level === 'High')   return '#ef4444'
  if (level === 'Medium') return '#f59e0b'
  return '#22c55e'
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
    street.addTo(map)

    /* ── Overlay layer groups ─────────────────────────────── */
    const riskLayer  = L.layerGroup().addTo(map)
    const labelLayer = L.layerGroup().addTo(map)

    // Real heatmap using leaflet.heat — proper KDE blur
    // [lat, lng, intensity] — intensity = risk_score (0–1)
    const heatLayer = L.heatLayer([], {
      radius:  28,      // blur radius in px — controls spread
      blur:    22,      // blur amount — higher = smoother
      maxZoom: 12,      // stops intensifying beyond this zoom
      max:     1.0,     // max intensity value
      // green → yellow → red gradient matching risk colours
      gradient: {
        0.0:  '#22c55e',   // low
        0.35: '#22c55e',
        0.5:  '#f59e0b',   // medium
        0.65: '#f59e0b',
        0.8:  '#ef4444',   // high
        1.0:  '#ef4444',
      },
    }).addTo(map)

    /* ── Layer control ────────────────────────────────────── */
    const layerCtrl = L.control.layers(
      { Terrain: terrain, Satellite: satellite, Street: street },
      {
        'Risk Points':          riskLayer,
        'Confirmed Landslides': labelLayer,
        'Risk Heatmap':         heatLayer,
      },
      { position: 'topright', collapsed: true }
    ).addTo(map)

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
      const zoomIn   = L.DomUtil.create('button', 'ts-zoom-btn', zoomWrap)
      zoomIn.innerHTML = '+'
      zoomIn.title     = 'Zoom in'
      L.DomEvent.on(zoomIn, 'click', e => { L.DomEvent.stop(e); map.zoomIn() })

      const zoomOut = L.DomUtil.create('button', 'ts-zoom-btn', zoomWrap)
      zoomOut.innerHTML = '−'
      zoomOut.title     = 'Zoom out'
      L.DomEvent.on(zoomOut, 'click', e => { L.DomEvent.stop(e); map.zoomOut() })

      L.DomEvent.disableClickPropagation(wrap)
      L.DomEvent.disableScrollPropagation(wrap)
      return wrap
    }
    bottomCtrl.addTo(map)

    /* ── Popup builder ────────────────────────────────────── */
    const buildPopup = (p, col) => `
      <div style="font-family:system-ui;font-size:12px;min-width:190px">
        <div style="background:${col};color:white;font-weight:700;padding:5px 10px;
                    border-radius:7px;margin-bottom:8px">
          ${p.risk_level.toUpperCase()} RISK &nbsp;·&nbsp; Score: ${p.risk_score}
        </div>
        <table style="width:100%;border-collapse:collapse">
          ${[
            ['Slope',           `${p.slope}°`],
            ['NDVI',             p.NDVI],
            ['Rainfall',        `${p.rainfall} mm/yr`],
            ['Competency',       p.competency_index],
            ['Elevation',       `${p.elevation} m`],
            ['Factor of Safety', p.FS],
          ].map(([k, v]) => `
            <tr style="border-bottom:1px solid #f3f4f6">
              <td style="padding:3px 10px 3px 0;color:#6b7280;font-size:11px">${k}</td>
              <td style="padding:3px 0;font-weight:600;font-size:11px">${v}</td>
            </tr>`).join('')}
        </table>
      </div>`

    /* ── Fetch risk points → circles + heatmap ────────────── */
    fetch(API.points)
      .then(r => r.json())
      .then(data => {
        const features  = data.features || []
        const heatPoints = []

        features.forEach(f => {
          const p   = f.properties
          const lat = f.geometry.coordinates[1]
          const lon = f.geometry.coordinates[0]
          const col = riskColor(p.risk_level)

          // circle marker for clicking
          L.circleMarker([lat, lon], {
            radius: 5, fillColor: col,
            color: 'white', weight: 0.8, fillOpacity: 0.88,
          })
            .bindPopup(buildPopup(p, col), { offset: L.point(0, -8), autoPan: true })
            .addTo(riskLayer)

          // feed into heatmap — [lat, lng, intensity]
          heatPoints.push([lat, lon, p.risk_score])
        })

        // set all points at once for best performance
        heatLayer.setLatLngs(heatPoints)
      })
      .catch(console.error)

    /* ── Fetch landslide labels ───────────────────────────── */
    fetch(API.labels)
      .then(r => r.json())
      .then(data => {
        const icon = L.divIcon({
          html: '<span style="font-size:13px;color:#1e293b;line-height:1">▲</span>',
          className: '', iconSize: [13, 13], iconAnchor: [6, 6],
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
