import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { WeeklySummary } from '../types'

interface Props {
  commodityId: string
}

export function WeeklySummary({ commodityId }: Props) {
  const [summary, setSummary] = useState<WeeklySummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setSummary(null)
    api.summary
      .get(commodityId)
      .then(setSummary)
      .catch(() => setSummary(null))
      .finally(() => setLoading(false))
  }, [commodityId])

  const accentColor = T.colors[commodityId] ?? T.blue

  return (
    <div
      style={{
        background: T.surface,
        border: `1px solid ${T.hairline}`,
        borderLeft: `3px solid ${accentColor}`,
        borderRadius: 6,
        padding: '18px 20px',
      }}
    >
      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: T.muted,
          marginBottom: 10,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <span>Resumen semanal</span>
        {summary && (
          <span style={{ fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
            {new Date(summary.period_end).toLocaleDateString('es-AR', { dateStyle: 'medium' })}
            {summary.llm_provider && (
              <span style={{ marginLeft: 6, color: T.faint }}>· {summary.llm_provider}</span>
            )}
          </span>
        )}
      </div>

      {loading && (
        <div style={{ color: T.faint, fontSize: 13 }}>Cargando resumen…</div>
      )}

      {!loading && !summary && (
        <div style={{ color: T.faint, fontSize: 13 }}>
          Sin resumen disponible. Ejecutar pipeline summary.
        </div>
      )}

      {!loading && summary && (
        <>
          <p
            style={{
              margin: '0 0 14px 0',
              fontSize: 14,
              lineHeight: 1.6,
              color: T.text,
            }}
          >
            {summary.summary_text}
          </p>

          {summary.key_signals && summary.key_signals.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {summary.key_signals.map((signal, i) => (
                <span
                  key={i}
                  style={{
                    background: T.bg,
                    border: `1px solid ${T.hairline}`,
                    borderRadius: 99,
                    padding: '3px 10px',
                    fontSize: 12,
                    color: T.muted,
                  }}
                >
                  {signal}
                </span>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
