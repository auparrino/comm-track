import { useEffect, useState } from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { TradeFlow } from '../types'

// Capítulos NCM por commodity y sus etiquetas
const NCM_LABELS: Record<string, Record<string, string>> = {
  soy: {
    '12': 'Semillas (cap.12)',
    '15': 'Aceites (cap.15)',
    '23': 'Harinas (cap.23)',
  },
  gold:    { '71': 'Met. preciosos (cap.71)' },
  lithium: { '28': 'Químicos inorg. (cap.28)' },
  copper:  { '74': 'Cobre y manuf. (cap.74)' },
  natgas:  { '27': 'Combustibles (cap.27)' },
  wheat:   { '10': 'Cereales (cap.10)' },
}

const RANGES = [
  { label: '12M', months: 12 },
  { label: '24M', months: 24 },
  { label: '36M', months: 36 },
]

function fmtUSD(v: number): string {
  if (v >= 1e9)  return `USD ${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6)  return `USD ${(v / 1e6).toFixed(0)}M`
  return `USD ${v.toLocaleString('es-AR')}`
}

function fmtPeriod(p: string): string {
  const [y, m] = p.split('-')
  const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
  return `${months[parseInt(m) - 1]} ${y.slice(2)}`
}

interface Props {
  commodityId: string
  nameEs: string
}

export function TradeFlowChart({ commodityId, nameEs }: Props) {
  const [flows, setFlows]         = useState<TradeFlow[]>([])
  const [months, setMonths]       = useState(24)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(false)

  useEffect(() => {
    setLoading(true)
    setError(false)
    api.trade.flows({ commodity: commodityId, months })
      .then(setFlows)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [commodityId, months])

  // Construir datos para el gráfico: [{ period, ncm_XX: value }, ...]
  const ncmLabels = NCM_LABELS[commodityId] ?? {}
  const ncmCodes  = Object.keys(ncmLabels)

  const byPeriod: Record<string, Record<string, number>> = {}
  for (const f of flows) {
    if (!byPeriod[f.period]) byPeriod[f.period] = {}
    byPeriod[f.period][`ncm_${f.ncm}`] = (f.value_usd ?? 0)
  }

  const chartData = Object.keys(byPeriod).sort().map((period) => ({
    period,
    label: fmtPeriod(period),
    ...byPeriod[period],
  }))

  // Total acumulado en el rango
  const totalUSD = flows.reduce((acc, f) => acc + (f.value_usd ?? 0), 0)

  const accentColor = T.colors[commodityId] ?? T.blue

  const barColors = ncmCodes.length === 1
    ? [accentColor]
    : [accentColor, T.blue, T.muted]

  return (
    <div
      style={{
        background: T.surface,
        border: `1px solid ${T.hairline}`,
        borderLeft: `3px solid ${accentColor}`,
        borderRadius: 8,
        padding: '20px 24px',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: 14, color: T.text }}>
            Exportaciones AR — {nameEs}
          </div>
          <div style={{ color: T.muted, fontSize: 12, marginTop: 2 }}>
            {loading ? 'Cargando...' : error ? 'Sin datos' : `${fmtUSD(totalUSD)} acumulado · cap. NCM 2 dígitos`}
          </div>
        </div>

        {/* Range selector */}
        <div style={{ display: 'flex', gap: 6 }}>
          {RANGES.map((r) => (
            <button
              key={r.months}
              onClick={() => setMonths(r.months)}
              style={{
                padding: '4px 10px',
                borderRadius: 20,
                border: 'none',
                cursor: 'pointer',
                fontSize: 12,
                fontFamily: T.sans,
                background: months === r.months ? T.text : T.bg,
                color:      months === r.months ? T.surface : T.muted,
                fontWeight: months === r.months ? 600 : 400,
                transition: 'all 0.15s',
              }}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      {loading ? (
        <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: T.faint, fontSize: 13 }}>
          Cargando datos...
        </div>
      ) : error || chartData.length === 0 ? (
        <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: T.faint, fontSize: 13 }}>
          Sin datos de comercio exterior
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }} barCategoryGap="20%">
            <CartesianGrid vertical={false} stroke={T.hairline} />
            <XAxis
              dataKey="label"
              tick={{ fill: T.faint, fontSize: 11, fontFamily: T.sans }}
              axisLine={false}
              tickLine={false}
              interval={Math.ceil(chartData.length / 8)}
            />
            <YAxis
              tickFormatter={(v) => v >= 1e9 ? `${(v/1e9).toFixed(1)}B` : `${(v/1e6).toFixed(0)}M`}
              tick={{ fill: T.faint, fontSize: 11, fontFamily: T.mono }}
              axisLine={false}
              tickLine={false}
              width={52}
            />
            <Tooltip
              formatter={(value: number, name: string) => [
                fmtUSD(value),
                ncmLabels[name.replace('ncm_', '')] ?? name,
              ]}
              labelFormatter={(label) => label}
              contentStyle={{
                background: T.surface,
                border: `1px solid ${T.hairline}`,
                borderRadius: 6,
                fontSize: 12,
                fontFamily: T.sans,
                color: T.text,
              }}
            />
            {ncmCodes.length > 1 && (
              <Legend
                formatter={(value) => ncmLabels[value.replace('ncm_', '')] ?? value}
                wrapperStyle={{ fontSize: 11, fontFamily: T.sans, color: T.muted }}
              />
            )}
            {ncmCodes.map((ncm, i) => (
              <Bar
                key={ncm}
                dataKey={`ncm_${ncm}`}
                name={`ncm_${ncm}`}
                stackId="a"
                fill={barColors[i] ?? T.blue}
                radius={i === ncmCodes.length - 1 ? [3, 3, 0, 0] : [0, 0, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      )}

      {/* Nota de fuente */}
      <div style={{ marginTop: 8, fontSize: 11, color: T.faint }}>
        Fuente: INDEC / datos.gob.ar · Datos en USD corrientes · Nota: incluye capítulo NCM completo
      </div>
    </div>
  )
}
