import { useEffect, useState } from 'react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { Price } from '../types'

const PRIMARY_PRICE_TYPE: Record<string, string> = {
  gold:    'futures',
  soy:     'futures',
  lithium: 'etf',
  copper:  'futures',
  natgas:  'futures',
  wheat:   'futures',
  corn:    'futures',
}

const RANGES = [
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '6M', days: 180 },
  { label: '1A', days: 365 },
]

interface Props {
  commodityId: string
  nameEs: string
  unit: string
}

export function PriceChart({ commodityId, nameEs, unit }: Props) {
  const [data, setData]       = useState<Price[]>([])
  const [days, setDays]       = useState(90)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.prices
      .history(commodityId, days, PRIMARY_PRICE_TYPE[commodityId] ?? 'futures')
      .then(setData)
      .catch(() => setData([]))
      .finally(() => setLoading(false))
  }, [commodityId, days])

  const color     = T.colors[commodityId] ?? T.blue
  const chartData = data.map((p) => ({ date: p.date, price: p.price }))

  // Ticks homogéneos: primer día de cada mes (o cada 2 semanas para 30d)
  const tickDates = computeTicks(chartData.map(d => d.date), days)

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
      {/* Header */}
      <div
        style={{
          display:        'flex',
          justifyContent: 'space-between',
          alignItems:     'center',
          marginBottom:   18,
        }}
      >
        <div>
          <span style={{ color: T.text, fontWeight: 600, fontSize: 15 }}>
            {nameEs}
          </span>
          <span
            style={{
              color:      T.faint,
              fontSize:   11,
              marginLeft: 8,
              fontFamily: T.mono,
            }}
          >
            {unit}
          </span>
        </div>

        {/* Range selector */}
        <div
          style={{
            display:      'flex',
            gap:          4,
            background:   T.bg,
            borderRadius: 6,
            padding:      3,
          }}
        >
          {RANGES.map((r) => (
            <button
              key={r.days}
              onClick={() => setDays(r.days)}
              style={{
                background:   days === r.days ? T.text : 'transparent',
                color:        days === r.days ? '#fff' : T.muted,
                border:       'none',
                borderRadius: 4,
                padding:      '4px 10px',
                fontSize:     12,
                fontWeight:   600,
                cursor:       'pointer',
                transition:   'background 0.15s',
              }}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      {loading ? (
        <div style={{ color: T.faint, fontSize: 13, textAlign: 'center', padding: 40 }}>
          Cargando…
        </div>
      ) : chartData.length === 0 ? (
        <div style={{ color: T.faint, fontSize: 13, textAlign: 'center', padding: 40 }}>
          Sin datos para este período
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id={`grad-${commodityId}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={color} stopOpacity={0.18} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(0,48,73,0.07)"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              ticks={tickDates}
              tickFormatter={formatTickDate}
              tick={{ fill: T.muted, fontSize: 11, fontFamily: T.mono }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: T.muted, fontSize: 11, fontFamily: T.mono }}
              tickFormatter={(v: number) =>
                v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v)
              }
              width={50}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background:   T.surface,
                border:       `1px solid ${T.hairline}`,
                borderRadius: 6,
                color:        T.text,
                fontSize:     12,
                boxShadow:    '0 4px 16px rgba(0,48,73,0.10)',
              }}
              labelStyle={{ color: T.muted, marginBottom: 4 }}
              formatter={(v: number) => [
                v.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                }),
                unit,
              ]}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke={color}
              strokeWidth={2}
              fill={`url(#grad-${commodityId})`}
              dot={false}
              activeDot={{ r: 4, fill: color, stroke: T.surface, strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

// ─── Helpers de ticks ────────────────────────────────────────────────────────

const MONTHS_ES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

/**
 * Devuelve las fechas exactas del dataset que corresponden al primer dato
 * de cada mes (o cada ~2 semanas si days ≤ 45). Así los ticks son homogéneos
 * y siempre caen sobre puntos reales del gráfico.
 */
function computeTicks(dates: string[], days: number): string[] {
  if (dates.length === 0) return []

  if (days <= 45) {
    // Cada ~7 días: primer dato de cada semana ISO
    const seen = new Set<string>()
    return dates.filter(d => {
      const week = getISOWeek(d)
      if (seen.has(week)) return false
      seen.add(week)
      return true
    })
  }

  // Mensual: primer dato disponible de cada mes
  const seen = new Set<string>()
  return dates.filter(d => {
    const ym = d.slice(0, 7)   // 'YYYY-MM'
    if (seen.has(ym)) return false
    seen.add(ym)
    return true
  })
}

function getISOWeek(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00')
  const jan4 = new Date(d.getFullYear(), 0, 4)
  const startOfWeek1 = new Date(jan4)
  startOfWeek1.setDate(jan4.getDate() - ((jan4.getDay() + 6) % 7))
  const diff = d.getTime() - startOfWeek1.getTime()
  const week = Math.floor(diff / (7 * 86_400_000)) + 1
  return `${d.getFullYear()}-W${week}`
}

function formatTickDate(dateStr: string): string {
  const [y, m] = dateStr.split('-')
  const month = MONTHS_ES[parseInt(m) - 1] ?? m
  return `${month} ${y.slice(2)}`
}
