import { useEffect, useState } from 'react'

export default function ModelPanel() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch('/api/stats').then(r => r.json()).then(setStats).catch(console.error)
  }, [])

  const m = stats?.model_metrics

  return (
    <div className="p-3 space-y-3">

      {/* ── Feature Importance ─────────────────────────────── */}
      <div>
        <p className="text-[9px] font-bold uppercase tracking-widest text-gray-400 mb-1.5">
          Feature Importance
        </p>
        <img
          src="/api/importance"
          alt="Feature Importance"
          className="w-full rounded-lg"
          style={{ display: 'block' }}
          onError={e => { e.target.style.display = 'none' }}
        />
      </div>

      {/* divider */}
      <div className="border-t border-gray-100" />

      {/* ── Model Performance ──────────────────────────────── */}
      <div>
        <p className="text-[9px] font-bold uppercase tracking-widest text-gray-400 mb-1.5">
          Model Performance
        </p>

        {m ? (
          <>
            {/* Model badge */}
            <div className="mb-2 inline-flex items-center gap-1.5 bg-violet-50 border border-violet-200 rounded-full px-2 py-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
              <span className="text-[10px] text-violet-600 font-semibold">{m.model}</span>
            </div>

            <table className="w-full">
              <tbody>
                {[
                  ['Accuracy',     m.accuracy,     '#7c3aed'],
                  ['F1 Score',     m.f1_score,     '#7c3aed'],
                  ['ROC-AUC',      m.roc_auc,      '#7c3aed'],
                  ['Spatial CV',   m.spatial_cv,   null],
                  ['Baseline AUC', m.baseline_auc, null],
                  ['Improvement',  m.improvement,  '#16a34a'],
                  ['Train Points', m.train_points, null],
                ].map(([k, v, color]) => (
                  <tr key={k} className="border-b border-gray-50">
                    <td className="py-0.5 text-[11px] text-gray-400">{k}</td>
                    <td
                      className="py-0.5 text-right text-[11px] font-semibold"
                      style={{ color: color || '#111827' }}
                    >
                      {v}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <div className="space-y-1.5">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-2 bg-gray-100 rounded animate-pulse" />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
