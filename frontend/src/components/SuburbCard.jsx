import TrendChart from './TrendChart'

function formatCurrency(value) {
  if (typeof value !== 'number') return 'N/A'
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}m`
  return `$${Math.round(value / 1_000).toLocaleString()}k`
}

function formatPercent(value) {
  return typeof value === 'number' ? `${value.toFixed(1)}%` : 'N/A'
}

function formatDays(value) {
  return typeof value === 'number' ? `${value} days` : 'N/A'
}

function clearanceTone(value) {
  if (typeof value !== 'number') return 'bg-gray-100 text-gray-700'
  if (value >= 70) return 'bg-emerald-100 text-emerald-800'
  if (value < 55) return 'bg-rose-100 text-rose-800'
  return 'bg-amber-100 text-amber-800'
}

export default function SuburbCard({ suburb, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-2xl border border-gray-200 bg-white p-5 text-left shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-lg font-semibold text-gray-900">{suburb.name}</p>
          <p className="text-sm text-gray-500">{suburb.postcode}</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${clearanceTone(suburb.clearance_rate)}`}>
          {suburb.sentiment ?? 'neutral'}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-2 text-sm text-gray-700 sm:grid-cols-3">
        <div className="rounded-xl bg-gray-50 px-3 py-2">
          <p className="text-xs uppercase tracking-wide text-gray-500">House</p>
          <p className="mt-1 font-semibold text-gray-900">{formatCurrency(suburb.median_house_price)}</p>
        </div>
        <div className="rounded-xl bg-gray-50 px-3 py-2">
          <p className="text-xs uppercase tracking-wide text-gray-500">Clearance</p>
          <p className="mt-1 font-semibold text-gray-900">{formatPercent(suburb.clearance_rate)}</p>
        </div>
        <div className="rounded-xl bg-gray-50 px-3 py-2">
          <p className="text-xs uppercase tracking-wide text-gray-500">Days on market</p>
          <p className="mt-1 font-semibold text-gray-900">{formatDays(suburb.median_days_on_market)}</p>
        </div>
      </div>

      <div className="mt-4">
        <TrendChart
          data={suburb.trend ?? []}
          sparkline
          label="Median price"
          color="#0f766e"
        />
      </div>
    </button>
  )
}
