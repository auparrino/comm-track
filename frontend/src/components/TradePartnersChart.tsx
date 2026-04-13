import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { TradePartner } from '../types'

interface Props {
  commodityId: string
  nameEs: string
}

const YEARS = [2026, 2025, 2024, 2023, 2022, 2021, 2020]

function fmt(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}bn`
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`
  return `$${(v / 1e3).toFixed(0)}K`
}

export function TradePartnersChart({ commodityId, nameEs }: Props) {
  const [data, setData]     = useState<TradePartner[]>([])
  const [year, setYear]     = useState(2025)
  const [flow, setFlow]     = useState<'export' | 'import'>('export')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.trade_partners
      .list({ commodity: commodityId, year, flow, top: 10 })
      .then(setData)
      .catch(() => setData([]))
      .finally(() => setLoading(false))
  }, [commodityId, year, flow])

  const accentColor = T.colors[commodityId] ?? T.blue

  const btnStyle = (active: boolean) => ({
    padding: '4px 10px',
    fontSize: 12,
    borderRadius: 99,
    border: 'none',
    cursor: 'pointer',
    background: active ? T.text : 'transparent',
    color: active ? T.surface : T.muted,
    fontWeight: active ? 600 : 400,
  })

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
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 14,
          flexWrap: 'wrap',
          gap: 8,
        }}
      >
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: T.muted,
          }}
        >
          Socios comerciales · {nameEs}
        </div>

        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {/* Flow toggle */}
          <div
            style={{
              display: 'flex',
              background: T.bg,
              borderRadius: 99,
              padding: 2,
              border: `1px solid ${T.hairline}`,
            }}
          >
            {(['export', 'import'] as const).map((f) => (
              <button key={f} style={btnStyle(flow === f)} onClick={() => setFlow(f)}>
                {f === 'export' ? 'Exporta' : 'Importa'}
              </button>
            ))}
          </div>

          {/* Year selector */}
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            style={{
              fontSize: 12,
              border: `1px solid ${T.hairline}`,
              borderRadius: 6,
              padding: '4px 8px',
              background: T.surface,
              color: T.text,
              cursor: 'pointer',
            }}
          >
            {YEARS.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <div style={{ color: T.faint, fontSize: 13, height: 200, display: 'flex', alignItems: 'center' }}>
          Cargando…
        </div>
      )}

      {!loading && data.length === 0 && (
        <div style={{ color: T.faint, fontSize: 13, height: 200, display: 'flex', alignItems: 'center' }}>
          Sin datos para {year}. Ejecutar pipeline comex_bilateral.
        </div>
      )}

      {!loading && data.length > 0 && (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 0, right: 50, left: 0, bottom: 0 }}
          >
            <XAxis
              type="number"
              tickFormatter={fmt}
              tick={{ fontSize: 10, fill: T.muted }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="country"
              width={100}
              tick={{ fontSize: 11, fill: T.text }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={(v: number) => [fmt(v), flow === 'export' ? 'Exporta a' : 'Importa de']}
              contentStyle={{
                background: T.surface,
                border: `1px solid ${T.hairline}`,
                borderRadius: 6,
                fontSize: 12,
              }}
            />
            <Bar dataKey="total_usd" radius={[0, 3, 3, 0]} maxBarSize={18}>
              {data.map((_, i) => (
                <Cell
                  key={i}
                  fill={accentColor}
                  fillOpacity={1 - i * 0.06}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
