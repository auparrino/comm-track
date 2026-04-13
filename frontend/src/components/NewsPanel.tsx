import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { NewsItem } from '../types'

const SENTIMENT_COLOR: Record<string, string> = {
  positive: T.positive,
  negative: T.negative,
  neutral:  T.neutral,
}

const SENTIMENT_LABEL: Record<string, string> = {
  positive: 'Positiva',
  negative: 'Negativa',
  neutral:  'Neutral',
}

const IMPACT_COLOR: Record<string, string> = {
  bullish: T.positive,
  bearish: T.negative,
  neutral: T.neutral,
}

const IMPACT_LABEL: Record<string, string> = {
  bullish: '▲ Alcista',
  bearish: '▼ Bajista',
  neutral: '— Neutral',
}

const SIGNAL_LABEL: Record<string, string> = {
  regulatory:   'Regulatorio',
  geopolitical: 'Geopolítico',
  supply:       'Oferta',
  demand:       'Demanda',
  climate:      'Clima',
  technology:   'Tecnología',
  price:        'Precio',
  other:        'Otro',
}

interface Props {
  commodityId: string
}

export function NewsPanel({ commodityId }: Props) {
  const [items, setItems]         = useState<NewsItem[]>([])
  const [loading, setLoading]     = useState(true)
  const [sentiment, setSentiment] = useState<string>('')
  const [days, setDays]           = useState(14)

  useEffect(() => {
    setLoading(true)
    api.news
      .list({
        commodity:  commodityId,
        days,
        sentiment:  sentiment || undefined,
        limit:      30,
      })
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [commodityId, days, sentiment])

  const DAYS_OPTIONS = [7, 14, 30]
  const SENTIMENTS   = ['', 'positive', 'negative', 'neutral']

  return (
    <div
      style={{
        background:   T.surface,
        border:       `1px solid ${T.hairline}`,
        borderTop:    `3px solid ${T.blue}`,
        borderRadius: 8,
        padding:      '20px 24px',
      }}
    >
      {/* Header */}
      <div
        style={{
          display:        'flex',
          justifyContent: 'space-between',
          alignItems:     'center',
          marginBottom:   16,
          flexWrap:       'wrap',
          gap:            10,
        }}
      >
        <span style={{ color: T.text, fontWeight: 600, fontSize: 15 }}>
          Noticias
        </span>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {/* Filtro días */}
          <div
            style={{
              display:      'flex',
              gap:          3,
              background:   T.bg,
              borderRadius: 6,
              padding:      2,
            }}
          >
            {DAYS_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                style={{
                  background:   days === d ? T.text : 'transparent',
                  color:        days === d ? '#fff' : T.muted,
                  border:       'none',
                  borderRadius: 4,
                  padding:      '3px 9px',
                  fontSize:     11,
                  fontWeight:   700,
                  cursor:       'pointer',
                  transition:   'background 0.15s',
                }}
              >
                {d}d
              </button>
            ))}
          </div>

          {/* Filtro sentimiento */}
          <div
            style={{
              display:      'flex',
              gap:          3,
              background:   T.bg,
              borderRadius: 6,
              padding:      2,
            }}
          >
            {SENTIMENTS.map((s) => {
              const active = sentiment === s
              const col    = s === '' ? T.text : SENTIMENT_COLOR[s]
              return (
                <button
                  key={s}
                  onClick={() => setSentiment(s)}
                  style={{
                    background:   active ? (s === '' ? T.text : col) : 'transparent',
                    color:        active ? '#fff' : T.muted,
                    border:       'none',
                    borderRadius: 4,
                    padding:      '3px 9px',
                    fontSize:     11,
                    fontWeight:   700,
                    cursor:       'pointer',
                    transition:   'background 0.15s',
                  }}
                >
                  {s === '' ? 'Todas' : SENTIMENT_LABEL[s]}
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div style={{ color: T.faint, fontSize: 13, textAlign: 'center', padding: 40 }}>
          Cargando…
        </div>
      ) : items.length === 0 ? (
        <div style={{ color: T.muted, fontSize: 13, textAlign: 'center', padding: 40 }}>
          Sin noticias para este período.
          <br />
          <span style={{ fontSize: 12, marginTop: 8, display: 'block', color: T.faint }}>
            Corré el pipeline:{' '}
            <code
              style={{
                background:   T.bg,
                border:       `1px solid ${T.hairline}`,
                padding:      '2px 6px',
                borderRadius: 4,
                fontFamily:   T.mono,
                fontSize:     11,
              }}
            >
              python -m backend.pipelines.news
            </code>
          </span>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {items.map((item) => (
            <NewsCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}

function NewsCard({ item }: { item: NewsItem }) {
  const color = item.commodity_id ? (T.colors[item.commodity_id] ?? T.blue) : T.blue

  const formatDate = (s: string | null) => {
    if (!s) return ''
    return new Date(s).toLocaleDateString('es-AR', {
      day: '2-digit', month: 'short', year: 'numeric',
    })
  }

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        display:        'block',
        background:     T.surface,
        border:         `1px solid ${T.hairline}`,
        borderLeft:     `3px solid ${color}`,
        borderRadius:   6,
        padding:        '12px 14px',
        textDecoration: 'none',
        transition:     'box-shadow 0.15s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = `0 2px 10px ${color}20`
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      {/* Badges */}
      <div
        style={{
          display:    'flex',
          gap:        5,
          marginBottom: 7,
          flexWrap:   'wrap',
          alignItems: 'center',
        }}
      >
        {item.sentiment && (
          <span
            style={{
              fontSize:    10,
              fontWeight:  700,
              color:       SENTIMENT_COLOR[item.sentiment],
              background:  `${SENTIMENT_COLOR[item.sentiment]}18`,
              padding:     '2px 7px',
              borderRadius: 3,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            {SENTIMENT_LABEL[item.sentiment]}
          </span>
        )}
        {item.impact_direction && (
          <span
            style={{
              fontSize:    10,
              fontWeight:  700,
              color:       IMPACT_COLOR[item.impact_direction],
              background:  `${IMPACT_COLOR[item.impact_direction]}18`,
              padding:     '2px 7px',
              borderRadius: 3,
              letterSpacing: '0.04em',
            }}
          >
            {IMPACT_LABEL[item.impact_direction]}
          </span>
        )}
        {item.signal_type && (
          <span
            style={{
              fontSize:    10,
              color:        T.muted,
              background:   T.bg,
              border:       `1px solid ${T.hairline}`,
              padding:      '2px 7px',
              borderRadius: 3,
            }}
          >
            {SIGNAL_LABEL[item.signal_type] ?? item.signal_type}
          </span>
        )}
        {item.relevance_score != null && (
          <span
            style={{
              fontSize:   10,
              color:      item.relevance_score >= 0.7 ? T.colors.gold : T.faint,
              marginLeft: 'auto',
              fontFamily: T.mono,
            }}
          >
            {(item.relevance_score * 100).toFixed(0)}%
          </span>
        )}
      </div>

      {/* Título */}
      <div
        style={{
          color:      T.text,
          fontSize:   13,
          fontWeight: 600,
          lineHeight: 1.4,
          marginBottom: 5,
        }}
      >
        {item.title}
      </div>

      {/* Resumen LLM o snippet */}
      {(item.summary_es || item.snippet) && (
        <div
          style={{
            color:      T.muted,
            fontSize:   12,
            lineHeight: 1.5,
            marginBottom: 8,
          }}
        >
          {item.summary_es ?? item.snippet}
        </div>
      )}

      {/* Footer */}
      <div
        style={{
          display:        'flex',
          justifyContent: 'space-between',
          alignItems:     'center',
        }}
      >
        <span style={{ fontSize: 11, color: T.faint }}>{item.source}</span>
        <span style={{ fontSize: 11, color: T.faint, fontFamily: T.mono }}>
          {formatDate(item.published_at)}
        </span>
      </div>
    </a>
  )
}
