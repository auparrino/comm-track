import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { Company, Valuation } from '../types'

interface CompanyRow extends Company {
  vals: Valuation[]
}

interface Props {
  commodityId: string
}

// Rol en español
const ROLE_LABEL: Record<string, string> = {
  miner:     'Minera',
  producer:  'Productora',
  trader:    'Trader',
  processor: 'Procesadora',
  refiner:   'Refinadora',
}
const ROLE_COLOR: Record<string, string> = {
  miner:     '#7c3aed',
  producer:  '#0891b2',
  trader:    '#059669',
  processor: '#d97706',
  refiner:   '#dc2626',
}

export function CompanyValuationPanel({ commodityId }: Props) {
  const [rows, setRows]       = useState<CompanyRow[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    setExpanded(null)
    api.companies
      .list(commodityId)
      .then(async (companies) => {
        const withVals = await Promise.all(
          companies.map(async (c) => {
            if (!c.ticker) return { ...c, vals: [] }
            try {
              // 20 días para poder calcular Δ1W (5 ruedas) y tener margen
              const v = await api.companies.valuations(c.id, 20)
              return { ...c, vals: v }
            } catch {
              return { ...c, vals: [] }
            }
          })
        )
        setRows(withVals)
      })
      .catch(() => setRows([]))
      .finally(() => setLoading(false))
  }, [commodityId])

  const color = T.colors[commodityId] ?? T.blue

  return (
    <div
      style={{
        background:   T.surface,
        border:       `1px solid ${T.hairline}`,
        borderTop:    `3px solid ${color}`,
        borderRadius: 8,
        padding:      '20px 24px',
      }}
    >
      <div
        style={{
          color: T.text, fontWeight: 600, fontSize: 15,
          marginBottom: 16, letterSpacing: '-0.01em',
        }}
      >
        Empresas vinculadas
      </div>

      {loading ? (
        <div style={{ color: T.faint, fontSize: 13 }}>Cargando…</div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr
                style={{
                  color: T.muted, borderBottom: `1px solid ${T.hairline}`,
                  fontSize: 11, fontWeight: 600, letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}
              >
                <th style={thStyle}>Empresa</th>
                <th style={thStyle}>Rol</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Precio</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Δ 1S</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Mkt Cap</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => {
                const latest  = r.vals.length > 0 ? r.vals[r.vals.length - 1] : null
                const week1   = r.vals.length >= 6 ? r.vals[r.vals.length - 6] : (r.vals.length > 1 ? r.vals[0] : null)
                const delta1w = computeDelta(latest, week1)
                const isOpen  = expanded === r.id

                return (
                  <>
                    <tr
                      key={r.id}
                      onClick={() => setExpanded(isOpen ? null : r.id)}
                      style={{
                        borderBottom: `1px solid ${T.hairline}`,
                        background:   i % 2 === 1 ? T.bg : 'transparent',
                        cursor:       r.notes ? 'pointer' : 'default',
                        transition:   'background 0.1s',
                      }}
                      onMouseEnter={e => { if (r.notes) e.currentTarget.style.background = T.surface2 }}
                      onMouseLeave={e => { e.currentTarget.style.background = i % 2 === 1 ? T.bg : 'transparent' }}
                    >
                      {/* Empresa */}
                      <td style={tdStyle}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div>
                            <div style={{ fontWeight: 500, color: T.text, display: 'flex', alignItems: 'center', gap: 5 }}>
                              {r.name}
                              {r.notes && (
                                <span style={{ fontSize: 10, color: T.faint }}>{isOpen ? '▲' : '▼'}</span>
                              )}
                            </div>
                            {r.project_name && (
                              <div style={{ color: T.faint, fontSize: 11, marginTop: 1 }}>
                                📍 {r.province_ar ? `${r.province_ar} · ` : ''}{r.project_name}
                              </div>
                            )}
                          </div>
                          {r.ticker ? (
                            <span
                              style={{
                                background: `${color}14`, color, borderRadius: 4,
                                padding: '2px 6px', fontFamily: T.mono,
                                fontSize: 11, fontWeight: 600, marginLeft: 'auto', flexShrink: 0,
                              }}
                            >
                              {r.ticker}
                            </span>
                          ) : (
                            <span style={{ color: T.faint, fontSize: 10, marginLeft: 'auto' }}>privada</span>
                          )}
                        </div>
                      </td>

                      {/* Rol */}
                      <td style={tdStyle}>
                        <span
                          style={{
                            fontSize: 10, fontWeight: 600,
                            color: ROLE_COLOR[r.role] ?? T.muted,
                            background: `${ROLE_COLOR[r.role] ?? T.muted}14`,
                            borderRadius: 3, padding: '2px 6px',
                            letterSpacing: '0.03em',
                          }}
                        >
                          {ROLE_LABEL[r.role] ?? r.role}
                        </span>
                        {r.is_ar_actor ? (
                          <span style={{ color: T.positive, fontSize: 11, marginLeft: 4 }}>✓AR</span>
                        ) : null}
                      </td>

                      {/* Precio */}
                      <td style={{ ...tdStyle, textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontFamily: T.mono }}>
                        {latest?.close_price != null ? (
                          <>
                            <span style={{ color: T.text, fontWeight: 600 }}>
                              ${latest.close_price.toFixed(2)}
                            </span>
                            <span style={{ color: T.faint, marginLeft: 3, fontSize: 10 }}>
                              {latest.currency}
                            </span>
                          </>
                        ) : <span style={{ color: T.faint }}>—</span>}
                      </td>

                      {/* Δ 1 semana */}
                      <td style={{ ...tdStyle, textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontFamily: T.mono }}>
                        {delta1w !== null ? (
                          <span
                            style={{
                              fontWeight: 600, fontSize: 12,
                              color: delta1w >= 0 ? T.positive : T.negative,
                            }}
                          >
                            {delta1w >= 0 ? '+' : ''}{delta1w.toFixed(1)}%
                          </span>
                        ) : <span style={{ color: T.faint }}>—</span>}
                      </td>

                      {/* Market cap */}
                      <td style={{ ...tdStyle, textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontFamily: T.mono, color: T.muted }}>
                        {latest?.market_cap_usd != null
                          ? `$${formatBillions(latest.market_cap_usd)}`
                          : <span style={{ color: T.faint }}>—</span>}
                      </td>
                    </tr>

                    {/* Fila expandible: notas de la empresa */}
                    {isOpen && r.notes && (
                      <tr key={`${r.id}-notes`} style={{ background: `${color}08` }}>
                        <td colSpan={5} style={{ padding: '10px 14px 12px', borderBottom: `1px solid ${T.hairline}` }}>
                          <div style={{ fontSize: 12, color: T.muted, lineHeight: 1.55, fontStyle: 'italic' }}>
                            {r.notes}
                          </div>
                          {r.vals.length > 1 && (
                            <div style={{ display: 'flex', gap: 20, marginTop: 8, fontSize: 11, color: T.faint }}>
                              <span>52S máx: <strong style={{ color: T.text }}>{formatPrice(Math.max(...r.vals.map(v => v.close_price ?? 0)))}</strong></span>
                              <span>52S mín: <strong style={{ color: T.text }}>{formatPrice(Math.min(...r.vals.filter(v => v.close_price != null).map(v => v.close_price!)))}</strong></span>
                              <span>Últ. precio: <strong style={{ color: T.text }}>{r.vals[r.vals.length-1]?.date?.slice(0,10)}</strong></span>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ marginTop: 10, fontSize: 11, color: T.faint }}>
        Hacé click en una empresa para ver descripción · Δ1S = variación última semana
      </div>
    </div>
  )
}

function computeDelta(latest: Valuation | null, prev: Valuation | null): number | null {
  if (!latest?.close_price || !prev?.close_price || prev.close_price === 0) return null
  return ((latest.close_price - prev.close_price) / prev.close_price) * 100
}

function formatBillions(n: number): string {
  if (n >= 1e12) return `${(n / 1e12).toFixed(1)}T`
  if (n >= 1e9)  return `${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6)  return `${(n / 1e6).toFixed(0)}M`
  return n.toLocaleString()
}

function formatPrice(n: number): string {
  return n >= 100 ? n.toFixed(0) : n.toFixed(2)
}

const thStyle: React.CSSProperties = {
  padding: '8px 12px', textAlign: 'left', fontWeight: 600,
}

const tdStyle: React.CSSProperties = {
  padding: '9px 12px', verticalAlign: 'middle',
}
