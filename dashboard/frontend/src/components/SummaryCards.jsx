import { useEffect, useState } from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const COLORS = ['#27AE60', '#F4D03F', '#E74C3C']

export default function SummaryCards() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch('/api/stats').then(r => r.json()).then(setStats)
  }, [])

  if (!stats) return (
    <div className="text-gray-400 text-xs animate-pulse">Loading stats…</div>
  )

  const z = stats.risk_zones
  const cards = [
    { label: 'Low Risk',    value: z.low,    count: z.low_count,    color: '#27AE60' },
    { label: 'Medium Risk', value: z.medium, count: z.medium_count, color: '#F4D03F' },
    { label: 'High Risk',   value: z.high,   count: z.high_count,   color: '#E74C3C' },
  ]
  const pieData = cards.map(c => ({ name: c.label, value: c.count }))

  return (
    <div className="space-y-3">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
        Risk Zone Breakdown
      </h2>

      {/* Cards */}
      <div className="flex gap-2">
        {cards.map(c => (
          <div
            key={c.label}
            className="flex-1 rounded-lg p-2 text-center"
            style={{ background: c.color + '22', border: `1px solid ${c.color}` }}
          >
            <div className="text-xl font-bold" style={{ color: c.color }}>
              {c.value}%
            </div>
            <div className="text-[10px] text-gray-300 mt-0.5 leading-tight">{c.label}</div>
            <div className="text-[10px] text-gray-500">{c.count} pts</div>
          </div>
        ))}
      </div>

      {/* Pie chart */}
      <ResponsiveContainer width="100%" height={90}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            innerRadius={30}
            outerRadius={50}
            dataKey="value"
            strokeWidth={0}
          >
            {pieData.map((_, i) => (
              <Cell key={i} fill={COLORS[i]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: '#1f2937', border: 'none', fontSize: 11, color: '#fff' }}
            formatter={(v, n) => [v + ' pts', n]}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
