import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import axios from 'axios'
import ChatAssistant from '../components/ChatAssistant'
import TrendChart from '../components/TrendChart'

const API = ''

function formatCurrency(value) {
  if (typeof value !== 'number') return 'N/A'
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}m`
  return `$${Math.round(value / 1_000).toLocaleString()}k`
}

function buildSeries(baseValue, steps, changePerStep) {
  if (typeof baseValue !== 'number') return []

  return Array.from({ length: steps }, (_, index) => {
    const offset = steps - index - 1
    return {
      week: `W${index + 1}`,
      value: Number((baseValue * (1 - offset * changePerStep)).toFixed(1)),
    }
  })
}

function MetricCard({ label, value, tone = 'bg-gray-50 text-gray-900' }) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
      <p className={`mt-2 inline-flex rounded-full px-3 py-1.5 text-sm font-semibold ${tone}`}>
        {value}
      </p>
    </div>
  )
}

export default function SuburbPage() {
  const { name } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)

    axios.get(`${API}/api/suburb/${name}`)
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.detail ?? 'Could not load suburb data.'))
      .finally(() => setLoading(false))
  }, [name])

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
        <p className="text-lg font-semibold text-red-800">Could not load suburb page</p>
        <p className="mt-2 text-sm text-red-600">{error}</p>
        <Link to="/" className="mt-5 inline-flex rounded-xl bg-red-600 px-4 py-2 text-sm font-semibold text-white">
          Back to dashboard
        </Link>
      </div>
    )
  }

  const metrics = data?.metrics ?? {}
  const marketContext = data?.market_context ?? {}
  const priceTrend = buildSeries(metrics.median_house_price, 8, 0.012)
  const clearanceTrend = buildSeries(metrics.clearance_rate, 8, 0.008)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to="/" className="text-sm font-medium text-blue-600 hover:text-blue-700">
            Back to dashboard
          </Link>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">{data?.suburb}</h1>
          <p className="mt-1 text-sm text-gray-500">
            Postcode {data?.postcode} | {data?.week} | {marketContext.sentiment ?? 'neutral'} sentiment
          </p>
        </div>
        <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-800">
          {marketContext.top_themes?.slice(0, 2).join(' | ')}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Median house price" value={formatCurrency(metrics.median_house_price)} tone="bg-emerald-100 text-emerald-800" />
        <MetricCard label="Median unit price" value={formatCurrency(metrics.median_unit_price)} tone="bg-sky-100 text-sky-800" />
        <MetricCard label="Clearance rate" value={typeof metrics.clearance_rate === 'number' ? `${metrics.clearance_rate}%` : 'N/A'} tone="bg-amber-100 text-amber-800" />
        <MetricCard label="Quarterly growth" value={typeof metrics.quarterly_growth === 'number' ? `${metrics.quarterly_growth}%` : 'N/A'} tone="bg-violet-100 text-violet-800" />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <div className="space-y-6">
          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Median house price trend</h2>
              <p className="text-sm text-gray-500">Indicative weekly trend derived from the saved suburb benchmark.</p>
            </div>
            <TrendChart data={priceTrend} label="Median price" color="#0f766e" />
          </section>

          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Clearance rate trend</h2>
              <p className="text-sm text-gray-500">Short-run auction momentum view for this suburb.</p>
            </div>
            <TrendChart data={clearanceTrend} label="Clearance %" color="#d97706" />
          </section>

          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Local themes</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {(marketContext.top_themes ?? []).map((theme) => (
                <span key={theme} className="rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700">
                  {theme}
                </span>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Recent market content</h2>
            <div className="mt-4 space-y-3">
              {(data?.relevant_content ?? []).map((item, index) => (
                <article key={`${index}-${item.slice(0, 24)}`} className="rounded-xl bg-gray-50 p-4">
                  <p className="text-sm leading-relaxed text-gray-700">{item}</p>
                </article>
              ))}
            </div>
          </section>
        </div>

        <div>
          <ChatAssistant suburb={data?.suburb_slug ?? name} />
        </div>
      </div>
    </div>
  )
}
