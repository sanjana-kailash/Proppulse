import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import SuburbCard from '../components/SuburbCard'

const API = ''

const SENTIMENT_STYLES = {
  positive: { bg: 'bg-green-100', text: 'text-green-800', dot: 'bg-green-500' },
  negative: { bg: 'bg-red-100', text: 'text-red-800', dot: 'bg-red-500' },
  neutral: { bg: 'bg-gray-100', text: 'text-gray-700', dot: 'bg-gray-400' },
}

function Spinner() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

function SentimentBadge({ sentiment }) {
  const style = SENTIMENT_STYLES[sentiment] ?? SENTIMENT_STYLES.neutral
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${style.bg} ${style.text}`}>
      <span className={`h-2 w-2 rounded-full ${style.dot}`} />
      {sentiment?.charAt(0).toUpperCase() + sentiment?.slice(1)} market sentiment
    </span>
  )
}

function buildTrend(baseValue, drift = 0.01) {
  if (typeof baseValue !== 'number') return []

  return Array.from({ length: 8 }, (_, index) => {
    const multiplier = 1 + (index - 7) * drift
    return {
      week: `W${index + 1}`,
      value: Math.round(baseValue * multiplier),
    }
  })
}

function StatCard({ label, items, color }) {
  if (!items?.length) return null

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-500">{label}</h3>
      <div className="flex flex-wrap gap-2">
        {items.slice(0, 8).map((item, index) => (
          <span key={index} className={`rounded-md px-2.5 py-1 text-sm font-mono font-medium ${color}`}>
            {typeof item === 'number' ? `$${item.toLocaleString()}` : item}
          </span>
        ))}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [toast, setToast] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    axios.get(`${API}/api/dashboard`)
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.detail ?? 'Could not reach the API. Is the backend running?'))
      .finally(() => setLoading(false))
  }, [])

  async function handleGenerate() {
    setGenerating(true)
    setToast(null)

    try {
      await axios.post(`${API}/api/generate-brief`)
      setToast({ type: 'success', msg: 'Brief generated. Redirecting...' })
      setTimeout(() => navigate('/brief'), 1200)
    } catch (err) {
      setToast({ type: 'error', msg: err.response?.data?.detail ?? 'Generation failed. Check the backend console.' })
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <Spinner />

  if (error) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
        <div className="max-w-md rounded-xl border border-red-200 bg-red-50 p-8">
          <p className="mb-1 font-medium text-red-700">Could not load dashboard</p>
          <p className="text-sm text-red-500">{error}</p>
          <p className="mt-4 text-xs text-gray-400">
            Make sure the backend is running:
            <code className="ml-1 rounded bg-gray-100 px-1">uvicorn main:app --reload</code>
          </p>
        </div>
      </div>
    )
  }

  const stats = data?.key_statistics ?? {}
  const suburbs = (data?.suburbs ?? []).map((suburb) => ({
    ...suburb,
    trend: buildTrend(suburb.median_house_price, 0.012),
  }))

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Market Dashboard</h1>
          <p className="mt-0.5 text-sm text-gray-500">
            {data?.week ?? '-'} | {data?.sources_scraped ?? 0} sources | {data?.total_content_blocks ?? 0} content blocks
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          {data?.sentiment && <SentimentBadge sentiment={data.sentiment} />}
        </div>
      </div>

      {toast && (
        <div className={`rounded-lg border px-4 py-3 text-sm font-medium ${
          toast.type === 'success'
            ? 'border-green-200 bg-green-50 text-green-800'
            : 'border-red-200 bg-red-50 text-red-800'
        }`}>
          {toast.msg}
        </div>
      )}

      {data?.top_themes?.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
            Top Themes This Week
          </h2>
          <div className="flex flex-wrap gap-2">
            {data.top_themes.map((theme, index) => (
              <span key={index} className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700">
                {theme}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <StatCard label="Price Figures Mentioned" items={stats.prices} color="bg-emerald-50 text-emerald-800" />
        <StatCard label="Percentages Mentioned" items={stats.percentages} color="bg-violet-50 text-violet-800" />
        <StatCard label="Rate Mentions" items={stats.rates} color="bg-amber-50 text-amber-800" />
      </div>

      {suburbs.length > 0 && (
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Portfolio Suburbs</h2>
            <p className="text-sm text-gray-500">Open a suburb card for deeper metrics, local context, and chat.</p>
          </div>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {suburbs.map((suburb) => (
              <SuburbCard
                key={suburb.slug}
                suburb={suburb}
                onClick={() => navigate(`/suburb/${suburb.slug}`)}
              />
            ))}
          </div>
        </div>
      )}

      <div className="pt-2">
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-8 py-3 font-semibold text-white shadow-sm transition-colors hover:bg-blue-700 disabled:bg-blue-400 sm:w-auto"
        >
          {generating ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Generating brief - this takes about 30 seconds...
            </>
          ) : (
            'Generate New Brief'
          )}
        </button>
        {generating && (
          <p className="mt-2 text-xs text-gray-400">
            Scraping sources, running NLP, then calling Groq AI. Check the backend console for live progress.
          </p>
        )}
      </div>
    </div>
  )
}
