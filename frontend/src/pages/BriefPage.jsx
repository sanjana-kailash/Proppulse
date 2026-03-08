import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

const API = ''

// Map section keys (from parsed brief JSON) to display labels and accent colours
const SECTION_CONFIG = {
  market_snapshot:  { label: 'Market Snapshot',    accent: 'border-blue-500',   badge: 'bg-blue-50 text-blue-700'   },
  weekly_narrative: { label: 'Weekly Narrative',   accent: 'border-emerald-500', badge: 'bg-emerald-50 text-emerald-700' },
  top_themes:       { label: 'Top Themes',         accent: 'border-violet-500', badge: 'bg-violet-50 text-violet-700' },
  agent_outlook:    { label: 'Agent Outlook',      accent: 'border-amber-500',  badge: 'bg-amber-50 text-amber-700'  },
}

function Spinner() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

function SectionCard({ sectionKey, content }) {
  const config = SECTION_CONFIG[sectionKey] ?? {
    label: sectionKey,
    accent: 'border-gray-300',
    badge: 'bg-gray-100 text-gray-600',
  }

  // Render bullet lines (lines starting with •) as styled list items
  const lines = content.split('\n').filter(l => l.trim())

  return (
    <div className={`bg-white rounded-xl border border-gray-200 border-l-4 ${config.accent} p-6 shadow-sm`}>
      <div className="flex items-center gap-2 mb-4">
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full uppercase tracking-wide ${config.badge}`}>
          {config.label}
        </span>
      </div>
      <div className="space-y-2 text-gray-700 text-sm leading-relaxed">
        {lines.map((line, i) => {
          const isBullet = line.trim().startsWith('•') || line.trim().startsWith('-')
          const isNumbered = /^\d+\./.test(line.trim())
          if (isBullet || isNumbered) {
            return (
              <div key={i} className="flex gap-2">
                <span className="text-blue-400 flex-shrink-0 mt-0.5">
                  {isBullet ? '•' : line.trim().match(/^\d+\./)?.[0]}
                </span>
                <span>{line.trim().replace(/^[•\-]|\d+\./, '').trim()}</span>
              </div>
            )
          }
          return <p key={i}>{line}</p>
        })}
      </div>
    </div>
  )
}

function FallbackFullText({ text }) {
  // If section parsing fails, split on ## headers and render each as a card
  const parts = text.split(/\n##\s+/).filter(Boolean)
  return (
    <div className="space-y-4">
      {parts.map((part, i) => {
        const [header, ...body] = part.split('\n')
        return (
          <div key={i} className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h2 className="font-bold text-gray-900 text-lg mb-3">{header}</h2>
            <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-line">
              {body.join('\n').trim()}
            </p>
          </div>
        )
      })}
    </div>
  )
}

export default function BriefPage() {
  const [brief, setBrief] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    axios.get(`${API}/api/brief/latest`)
      .then(res => setBrief(res.data))
      .catch(err => setError(err.response?.data?.detail ?? 'No brief found.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  if (error) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 max-w-md">
        <p className="text-gray-700 font-medium mb-2">No brief available yet</p>
        <p className="text-gray-500 text-sm mb-5">{error}</p>
        <Link
          to="/"
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm"
        >
          Go to Dashboard to Generate One
        </Link>
      </div>
    </div>
  )

  const sections = brief?.sections ?? {}
  const hasParsedSections = Object.values(sections).some(v => v?.trim())

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Weekly Market Brief</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            {brief?.week ?? '—'} · Generated {brief?.generated_at ? new Date(brief.generated_at).toLocaleString('en-AU') : ''}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {brief?.sentiment && (
            <span className="text-xs text-gray-500 bg-gray-100 px-3 py-1.5 rounded-full capitalize">
              {brief.sentiment} sentiment
            </span>
          )}
          <button
            onClick={() => window.print()}
            className="text-sm text-gray-600 hover:text-gray-900 border border-gray-200 hover:border-gray-400 px-4 py-2 rounded-lg transition-colors"
          >
            Print / Export
          </button>
        </div>
      </div>

      {/* Brief sections */}
      {hasParsedSections ? (
        <div className="space-y-4">
          {Object.entries(SECTION_CONFIG).map(([key]) =>
            sections[key]?.trim() ? (
              <SectionCard key={key} sectionKey={key} content={sections[key]} />
            ) : null
          )}
        </div>
      ) : (
        brief?.full_text && <FallbackFullText text={brief.full_text} />
      )}

      {/* Data sources footer */}
      {brief?.data_sources && (
        <p className="text-xs text-gray-400 pt-2 border-t border-gray-100">
          Sources: {brief.data_sources}
        </p>
      )}

    </div>
  )
}
