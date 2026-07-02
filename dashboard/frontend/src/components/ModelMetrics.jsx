import { useEffect, useState } from 'react'

export default function ModelMetrics() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch('/api/stats').then(r => r.json()).then(setStats)
  }, [])

  if (!stats) return null

  const m = stats.model_metrics
  const rows = [
    ['Model',        m.model],
    ['Accuracy',     m.accuracy],
    ['F1 Score',     m.f1_score],
    ['ROC-AUC',      m.roc_auc],
    ['Spatial CV',   m.spatial_cv],
    ['Baseline AUC', m.baseline_auc],
    ['Improvement',  m.improvement],
    ['Train Points', m.train_points],
  ]

  return (
    <div className="space-y-2">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
        Model Performance
      </h2>
      <table className="w-full text-xs">
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
  )
}
