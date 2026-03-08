import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

function formatMetric(value, label) {
  if (typeof value !== 'number') return value

  if (label?.toLowerCase().includes('price')) {
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}m`
    if (value >= 1_000) return `$${Math.round(value / 1_000)}k`
    return `$${value}`
  }

  if (label?.includes('%')) {
    return `${value}%`
  }

  return value.toString()
}

export default function TrendChart({
  data = [],
  dataKey = 'value',
  color = '#2563eb',
  sparkline = false,
  label = 'Value',
  height,
}) {
  const chartHeight = height ?? (sparkline ? 72 : 260)

  if (!data.length) {
    return (
      <div
        className="flex items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-400"
        style={{ height: chartHeight }}
      >
        No trend data available
      </div>
    )
  }

  return (
    <div style={{ width: '100%', height: chartHeight }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={sparkline ? { top: 8, right: 4, bottom: 8, left: 4 } : { top: 8, right: 16, bottom: 8, left: 4 }}>
          {!sparkline && <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />}
          <XAxis
            dataKey="week"
            hide={sparkline}
            tick={{ fontSize: 12, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            hide={sparkline}
            tickFormatter={(value) => formatMetric(value, label)}
            tick={{ fontSize: 12, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
            width={72}
          />
          {!sparkline && (
            <Tooltip
              formatter={(value) => formatMetric(value, label)}
              contentStyle={{
                borderRadius: '12px',
                borderColor: '#dbeafe',
                boxShadow: '0 10px 30px rgba(15, 23, 42, 0.08)',
              }}
            />
          )}
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={sparkline ? 2.5 : 3}
            dot={sparkline ? false : { r: 3 }}
            activeDot={sparkline ? false : { r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
