import { useState } from 'react'
import MapView        from './components/MapView'
import ModelPanel     from './components/ModelPanel'
import AnalyticsPanel from './components/AnalyticsPanel'
import Chatbot        from './components/Chatbot'

// Navbar height in px — used to offset every floating panel
const NAV_H = 48

export default function App() {
  const [chatOpen, setChatOpen] = useState(false)

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-slate-100">

      {/* ── MAP — full bleed ─────────────────────────────────── */}
      <div className="absolute inset-0">
        <MapView navHeight={NAV_H} />
      </div>

      {/* ── NAVBAR ───────────────────────────────────────────── */}
      <header
        className="absolute top-0 left-0 right-0 z-[1200] flex justify-between items-center px-4"
        style={{
          height: NAV_H,
          background: 'rgba(255,255,255,0.88)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(0,0,0,0.07)',
          boxShadow: '0 2px 16px rgba(0,0,0,0.07)',
        }}
      >
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-lg bg-emerald-500 flex items-center justify-center">
            <span className="text-white text-xs font-bold">G</span>
          </div>
          <div>
            <span className="text-sm font-bold text-gray-900">GeoSentinel+</span>
            <span className="ml-2 text-[10px] text-gray-400">Garhwal Himalaya · Landslide Risk Platform</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          
          <button
            onClick={() => setChatOpen(v => !v)}
            className="flex items-center gap-1.5 bg-emerald-500 hover:bg-emerald-600
                       text-white text-xs font-medium px-3 py-1.5 rounded-lg
                       shadow-sm transition-colors"
          >
            ✦ Ask AI
          </button>
        </div>
      </header>

      {/* ── PANEL 1: Feature Importance + Model — TOP LEFT ──── */}
      <div
        className="glass absolute z-[1100]"
        style={{
          top: NAV_H + 10,
          left: 12,
          width: 420,   /* wide enough for all feature label text */
        }}
      >
        <ModelPanel />
      </div>

      {/* ── PANEL 2: Risk Zone Breakdown — BOTTOM RIGHT ──────── */}
      <div
        className="glass absolute z-[1100]"
        style={{
          bottom: 24,
          right: 12,
          width: 236,
        }}
      >
        <AnalyticsPanel />
      </div>

      {/* ── CHATBOT — center bottom, rectangular ─────────────── */}
      {chatOpen && (
        <Chatbot onClose={() => setChatOpen(false)} />
      )}
    </div>
  )
}
