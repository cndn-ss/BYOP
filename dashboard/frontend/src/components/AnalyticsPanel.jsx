import { useEffect, useState } from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const COLORS = ['#22c55e', '#f59e0b', '#ef4444']

export default function AnalyticsPanel() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch('/api/stats').then(r => r.json()).then(setStats).catch(console.error)
  }, [])

  if (!stats) {
    return (
      <div className="p-3 space-y-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-2 bg-gray-100 rounded animate-pulse" />
        ))}
      </div>
    )
  }

  const z = stats.risk_zones
  const cards = [
    { label: 'Low',    pct: z.low,    count: z.low_count,    color: '#22c55e', bg: '#f0fdf4', border: '#bbf7d0' },
    { label: 'Medium', pct: z.medium, count: z.medium_count, color: '#f59e0b', bg: '#fffbeb', border: '#fde68a' },
    { label: 'High',   pct: z.high,   count: z.high_count,   color: '#ef4444', bg: '#fef2f2', border: '#fecaca' },
  ]
  const pieData = cards.map(c => ({ name: c.label + ' Risk', value: c.count }))

  return (
    <div className="p-3 space-y-3">
      <p className="text-[9px] font-bold uppercase tracking-widest text-gray-400">
        Risk Zone Breakdown
      </p>

      {/* Stat cards */}
      <div className="flex gap-1.5">
        {cards.map(c => (
          <div
            key={c.label}
            className="flex-1 rounded-xl p-2 text-center"
            style={{ background: c.bg, border: `1px solid ${c.border}` }}
          >
            <div className="text-base font-bold" style={{ color: c.color }}>{c.pct}%</div>
            <div className="text-[9px] font-medium mt-0.5" style={{ color: c.color }}>{c.label}</div>
            <div className="text-[9px] text-gray-400">{c.count} pts</div>
          </div>
        ))}
      </div>

      {/* Donut */}
      <ResponsiveContainer width="100%" height={90}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%" cy="50%"
            innerRadius={26} outerRadius={40}
            dataKey="value"
            strokeWidth={0}
            paddingAngle={2}
          >
            {pieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
          </Pie>
          <Tooltip
            contentStyle={{
              background: 'rgba(255,255,255,0.97)',
              border: '1px solid rgba(0,0,0,0.08)',
              borderRadius: 8, fontSize: 11,
            }}
            formatter={(v, n) => [v + ' points', n]}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
