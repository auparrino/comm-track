import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { Company, Valuation } from '../types'

interface CompanyRow extends Company {
  latestVal: Valuation | null
}

interface Props {
  commodityId: string
}

export function CompanyValuationPanel({ commodityId }: Props) {
  const [rows, setRows]       = useState<CompanyRow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.companies
      .list(commodityId)
      .then(async (companies) => {
        const withVals = await Promise.all(
          companies.map(async (c) => {
            if (!c.ticker) return { ...c, latestVal: null }
            try {
              const vals = await api.companies.valuations(c.id, 5)
              return { ...c, latestVal: vals[vals.length - 1] ?? null }
            } catch {
              return { ...c, latestVal: null }
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
          color:        T.text,
          fontWeight:   600,
          fontSize:     15,
          marginBottom: 16,
          letterSpacing: '-0.01em',
        }}
      >
        Empresas vinculadas
      </div>

      {loading ? (
        <div style={{ color: T.faint, fontSize: 13 }}>Cargando…</div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table
            style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}
          >
            <thead>
              <tr
                style={{
                  color:        T.muted,
                  borderBottom: `1px solid ${T.hairline}`,
                  fontSize:     11,
                  fontWeight:   600,
                  letterSpacing:'0.04em',
                  textTransform:'uppercase',
                }}
              >
                <th style={thStyle}>Empresa</th>
                <th style={thStyle}>Ticker</th>
                <th style={thStyle}>País</th>
                <th style={thStyle}>AR</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Precio</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Mkt Cap</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr
                  key={r.id}
                  style={{
                    borderBottom: `1px solid ${T.hairline}`,
                    background:   i % 2 === 1 ? T.bg : 'transparent',
                  }}
                >
                  <td style={tdStyle}>
                    <div style={{ fontWeight: 500, color: T.text }}>{r.name}</div>
                    {r.project_name && (
                      <div style={{ color: T.faint, fontSize: 11 }}>
                        {r.project_name}
                      </div>
                    )}
                  </td>

                  <td style={tdStyle}>
                    {r.ticker ? (
                      <span
                        style={{
                          background:  `${color}14`,
                          color:        color,
                          borderRadius: 4,
                          padding:     '2px 7px',
                          fontFamily:   T.mono,
                          fontSize:     12,
                          fontWeight:   600,
                        }}
                      >
                        {r.ticker}
                      </span>
                    ) : (
                      <span style={{ color: T.faint, fontSize: 11 }}>privada</span>
                    )}
                  </td>

                  <td style={{ ...tdStyle, color: T.muted }}>{r.country}</td>

                  <td style={tdStyle}>
                    {r.is_ar_actor ? (
                      <span style={{ color: T.positive, fontSize: 13, fontWeight: 700 }}>✓</span>
                    ) : (
                      <span style={{ color: T.faint, fontSize: 13 }}>–</span>
                    )}
                  </td>

                  <td
                    style={{
                      ...tdStyle,
                      textAlign:          'right',
                      fontVariantNumeric: 'tabular-nums',
                      fontFamily:          T.mono,
                    }}
                  >
                    {r.latestVal?.close_price != null ? (
                      <>
                        <span style={{ color: T.text, fontWeight: 600 }}>
                          ${r.latestVal.close_price.toFixed(2)}
                        </span>
                        <span style={{ color: T.faint, marginLeft: 3, fontSize: 11 }}>
                          {r.latestVal.currency}
                        </span>
                      </>
                    ) : (
                      <span style={{ color: T.faint }}>—</span>
                    )}
                  </td>

                  <td
                    style={{
                      ...tdStyle,
                      textAlign:          'right',
                      fontVariantNumeric: 'tabular-nums',
                      fontFamily:          T.mono,
                      color:               T.muted,
                    }}
                  >
                    {r.latestVal?.market_cap_usd != null ? (
                      `$${formatBillions(r.latestVal.market_cap_usd)}`
                    ) : (
                      <span style={{ color: T.faint }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function formatBillions(n: number): string {
  if (n >= 1e12) return `${(n / 1e12).toFixed(1)}T`
  if (n >= 1e9)  return `${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6)  return `${(n / 1e6).toFixed(0)}M`
  return n.toLocaleString()
}

const thStyle: React.CSSProperties = {
  padding:   '8px 12px',
  textAlign: 'left',
  fontWeight: 600,
}

const tdStyle: React.CSSProperties = {
  padding:       '9px 12px',
  verticalAlign: 'middle',
}
