import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { NewsItem, WeeklySummary } from '../types'

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

// Íconos por signal_type para las señales clave del resumen
const SIGNAL_ICON: Record<string, string> = {
  regulatory:   '⚖️',
  geopolitical: '🌍',
  supply:       '📦',
  demand:       '📈',
  climate:      '🌦️',
  technology:   '💡',
  price:        '💲',
  other:        '📌',
}

interface Props {
  commodityId: string
}

export function NewsPanel({ commodityId }: Props) {
  const [items, setItems]       = useState<NewsItem[]>([])
  const [summary, setSummary]   = useState<WeeklySummary | null>(null)
  const [loading, setLoading]   = useState(true)
  const [sentiment, setSentiment] = useState<string>('')
  const [days, setDays]         = useState(14)
  const [showAll, setShowAll]   = useState(false)

  useEffect(() => {
    setLoading(true)
    setSummary(null)
    setShowAll(false)
    Promise.all([
      api.news.list({ commodity: commodityId, days, sentiment: sentiment || undefined, limit: 30 }),
      api.summary.get(commodityId).catch(() => null),
    ])
      .then(([news, sum]) => {
        setItems(news)
        setSummary(sum)
      })
      .catch(() => { setItems([]); setSummary(null) })
      .finally(() => setLoading(false))
  }, [commodityId, days, sentiment])

  const accentColor = T.colors[commodityId] ?? T.blue
  const DAYS_OPTIONS = [7, 14, 30]
  const SENTIMENTS   = ['', 'positive', 'negative', 'neutral']

  // Separar noticias de alta relevancia
  const topItems  = items.filter(i => (i.relevance_score ?? 0) >= 0.7).slice(0, 3)
  const restItems = items.filter(i => (i.relevance_score ?? 0) < 0.7)
  const visibleRest = showAll ? restItems : restItems.slice(0, 5)

  return (
    <div
      style={{
        background:   T.surface,
        border:       `1px solid ${T.hairline}`,
        borderTop:    `3px solid ${accentColor}`,
        borderRadius: 8,
        padding:      '20px 24px',
        display:      'flex',
        flexDirection:'column',
        gap:          0,
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
          Análisis & Noticias
        </span>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {/* Filtro días */}
          <div style={{ display: 'flex', gap: 3, background: T.bg, borderRadius: 6, padding: 2 }}>
            {DAYS_OPTIONS.map((d) => (
              <button key={d} onClick={() => setDays(d)}
                style={{
                  background:   days === d ? T.text : 'transparent',
                  color:        days === d ? '#fff' : T.muted,
                  border:       'none', borderRadius: 4,
                  padding:      '3px 9px', fontSize: 11, fontWeight: 700,
                  cursor:       'pointer', transition: 'background 0.15s',
                }}
              >{d}d</button>
            ))}
          </div>

          {/* Filtro sentimiento */}
          <div style={{ display: 'flex', gap: 3, background: T.bg, borderRadius: 6, padding: 2 }}>
            {SENTIMENTS.map((s) => {
              const active = sentiment === s
              const col    = s === '' ? T.text : SENTIMENT_COLOR[s]
              return (
                <button key={s} onClick={() => setSentiment(s)}
                  style={{
                    background:   active ? (s === '' ? T.text : col) : 'transparent',
                    color:        active ? '#fff' : T.muted,
                    border:       'none', borderRadius: 4,
                    padding:      '3px 9px', fontSize: 11, fontWeight: 700,
                    cursor:       'pointer', transition: 'background 0.15s',
                  }}
                >
                  {s === '' ? 'Todas' : SENTIMENT_LABEL[s]}
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ color: T.faint, fontSize: 13, textAlign: 'center', padding: 40 }}>
          Cargando…
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* ── Bloque AI Brief ─────────────────────────────────────── */}
          {summary && (
            <div
              style={{
                background:   `${accentColor}09`,
                border:       `1px solid ${accentColor}30`,
                borderLeft:   `3px solid ${accentColor}`,
                borderRadius: 7,
                padding:      '14px 16px',
              }}
            >
              {/* Cabecera del brief */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span
                  style={{
                    fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
                    textTransform: 'uppercase', color: accentColor,
                  }}
                >
                  ✦ Resumen IA
                </span>
                <span style={{ fontSize: 11, color: T.faint }}>
                  · {new Date(summary.period_end + 'T12:00:00').toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })}
                  {summary.llm_provider && ` · ${summary.llm_provider}`}
                </span>
              </div>

              {/* Texto del resumen */}
              <p style={{ margin: '0 0 10px 0', fontSize: 13, lineHeight: 1.65, color: T.text }}>
                {summary.summary_text}
              </p>

              {/* Señales clave */}
              {summary.key_signals && summary.key_signals.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {summary.key_signals.map((sig, i) => {
                    // Intenta matchear la señal con un tipo conocido para darle ícono
                    const matchedType = Object.keys(SIGNAL_ICON).find(k =>
                      sig.toLowerCase().includes(k)
                    )
                    const icon = matchedType ? SIGNAL_ICON[matchedType] : '📌'
                    return (
                      <span key={i}
                        style={{
                          background:   T.surface,
                          border:       `1px solid ${T.hairline}`,
                          borderRadius: 99,
                          padding:      '3px 10px',
                          fontSize:     11,
                          color:        T.muted,
                          display:      'flex',
                          alignItems:   'center',
                          gap:          4,
                        }}
                      >
                        <span>{icon}</span>
                        <span>{sig}</span>
                      </span>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* ── Artículos de alta relevancia ─────────────────────────── */}
          {topItems.length > 0 && (
            <div>
              <div
                style={{
                  fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
                  textTransform: 'uppercase', color: T.muted,
                  marginBottom: 8,
                }}
              >
                Alto impacto
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {topItems.map(item => <NewsCard key={item.id} item={item} compact={false} />)}
              </div>
            </div>
          )}

          {/* ── Otras noticias ───────────────────────────────────────── */}
          {items.length === 0 && !summary ? (
            <div style={{ color: T.muted, fontSize: 13, textAlign: 'center', padding: 40 }}>
              Sin noticias para este período.
              <br />
              <span style={{ fontSize: 12, marginTop: 8, display: 'block', color: T.faint }}>
                Corré:{' '}
                <code style={{ background: T.bg, border: `1px solid ${T.hairline}`, padding: '2px 6px', borderRadius: 4, fontFamily: T.mono, fontSize: 11 }}>
                  python -m backend.pipelines.news
                </code>
              </span>
            </div>
          ) : restItems.length > 0 ? (
            <div>
              {topItems.length > 0 && (
                <div
                  style={{
                    fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
                    textTransform: 'uppercase', color: T.muted,
                    marginBottom: 8,
                  }}
                >
                  Otras noticias
                </div>
              )}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {visibleRest.map(item => <NewsCard key={item.id} item={item} compact={true} />)}
              </div>
              {restItems.length > 5 && (
                <button
                  onClick={() => setShowAll(s => !s)}
                  style={{
                    marginTop:   10,
                    width:       '100%',
                    background:  'transparent',
                    border:      `1px solid ${T.hairline}`,
                    borderRadius: 6,
                    padding:     '6px 0',
                    fontSize:    12,
                    color:       T.muted,
                    cursor:      'pointer',
                    fontFamily:  T.sans,
                  }}
                >
                  {showAll
                    ? `▲ Mostrar menos`
                    : `▼ Ver ${restItems.length - 5} más`}
                </button>
              )}
            </div>
          ) : null}

        </div>
      )}
    </div>
  )
}

// ── NewsCard ──────────────────────────────────────────────────────────────────

function NewsCard({ item, compact }: { item: NewsItem; compact: boolean }) {
  const color = item.commodity_id ? (T.colors[item.commodity_id] ?? T.blue) : T.blue

  const formatDate = (s: string | null) => {
    if (!s) return ''
    const d = new Date(s)
    const now = new Date()
    const diffH = Math.round((now.getTime() - d.getTime()) / 3_600_000)
    if (diffH < 24) return `hace ${diffH}h`
    if (diffH < 48) return 'ayer'
    return d.toLocaleDateString('es-AR', { day: '2-digit', month: 'short' })
  }

  if (compact) {
    // Versión compacta: una sola línea con badges pequeños
    return (
      <a href={item.url} target="_blank" rel="noopener noreferrer"
        style={{
          display:        'flex',
          alignItems:     'flex-start',
          gap:            8,
          padding:        '8px 10px',
          background:     T.surface,
          border:         `1px solid ${T.hairline}`,
          borderLeft:     `2px solid ${color}`,
          borderRadius:   5,
          textDecoration: 'none',
          transition:     'background 0.12s',
        }}
        onMouseEnter={e => (e.currentTarget.style.background = T.bg)}
        onMouseLeave={e => (e.currentTarget.style.background = T.surface)}
      >
        {/* Dot sentimiento */}
        {item.sentiment && (
          <span style={{
            width: 7, height: 7, borderRadius: '50%', flexShrink: 0, marginTop: 4,
            background: SENTIMENT_COLOR[item.sentiment] ?? T.faint,
          }} />
        )}

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 500, color: T.text, lineHeight: 1.4,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {item.title}
          </div>
          <div style={{ fontSize: 10, color: T.faint, marginTop: 2 }}>
            {item.source} · {formatDate(item.published_at)}
            {item.impact_direction && item.impact_direction !== 'neutral' && (
              <span style={{ color: IMPACT_COLOR[item.impact_direction], marginLeft: 6, fontWeight: 600 }}>
                {IMPACT_LABEL[item.impact_direction]}
              </span>
            )}
          </div>
        </div>

        {item.relevance_score != null && (
          <span style={{ fontSize: 10, color: T.faint, fontFamily: T.mono, flexShrink: 0, marginTop: 2 }}>
            {(item.relevance_score * 100).toFixed(0)}%
          </span>
        )}
      </a>
    )
  }

  // Versión completa (alto impacto)
  return (
    <a href={item.url} target="_blank" rel="noopener noreferrer"
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
      onMouseEnter={e => { e.currentTarget.style.boxShadow = `0 2px 10px ${color}20` }}
      onMouseLeave={e => { e.currentTarget.style.boxShadow = 'none' }}
    >
      {/* Badges */}
      <div style={{ display: 'flex', gap: 5, marginBottom: 7, flexWrap: 'wrap', alignItems: 'center' }}>
        {item.sentiment && (
          <span style={{ fontSize: 10, fontWeight: 700, color: SENTIMENT_COLOR[item.sentiment],
            background: `${SENTIMENT_COLOR[item.sentiment]}18`, padding: '2px 7px',
            borderRadius: 3, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            {SENTIMENT_LABEL[item.sentiment]}
          </span>
        )}
        {item.impact_direction && (
          <span style={{ fontSize: 10, fontWeight: 700, color: IMPACT_COLOR[item.impact_direction],
            background: `${IMPACT_COLOR[item.impact_direction]}18`, padding: '2px 7px',
            borderRadius: 3, letterSpacing: '0.04em' }}>
            {IMPACT_LABEL[item.impact_direction]}
          </span>
        )}
        {item.signal_type && (
          <span style={{ fontSize: 10, color: T.muted, background: T.bg,
            border: `1px solid ${T.hairline}`, padding: '2px 7px', borderRadius: 3 }}>
            {SIGNAL_ICON[item.signal_type] ?? ''} {SIGNAL_LABEL[item.signal_type] ?? item.signal_type}
          </span>
        )}
        {item.relevance_score != null && (
          <span style={{ fontSize: 10, color: item.relevance_score >= 0.8 ? accentColor(item) : T.faint,
            marginLeft: 'auto', fontFamily: T.mono }}>
            {(item.relevance_score * 100).toFixed(0)}% rel.
          </span>
        )}
      </div>

      {/* Título */}
      <div style={{ color: T.text, fontSize: 13, fontWeight: 600, lineHeight: 1.4, marginBottom: 5 }}>
        {item.title}
      </div>

      {/* Resumen */}
      {(item.summary_es || item.snippet) && (
        <div style={{ color: T.muted, fontSize: 12, lineHeight: 1.5, marginBottom: 8 }}>
          {item.summary_es ?? item.snippet}
        </div>
      )}

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: T.faint }}>{item.source}</span>
        <span style={{ fontSize: 11, color: T.faint, fontFamily: T.mono }}>
          {formatDate(item.published_at)}
        </span>
      </div>
    </a>
  )
}

function accentColor(item: NewsItem): string {
  return item.commodity_id ? (T.colors[item.commodity_id] ?? T.blue) : T.blue
}
