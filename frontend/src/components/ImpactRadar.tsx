/**
 * ImpactRadar — Panel de variables macroeconómicas y de contexto
 *
 * Muestra las variables de impacto relevantes para el commodity seleccionado:
 *   - Fed Funds Rate (FRED)
 *   - DXY / Broad Dollar Index (FRED)
 *   - Tipo de cambio oficial ARS/USD (BCRA)
 *   - ENSO/ONI (NOAA)  — especialmente relevante para soja
 *   - Retenciones AR (AFIP/decreto) — específicas por commodity
 */
import React, { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { ImpactVariable } from '../types'

interface Props {
  commodityId: string
}

// ─── Metadatos de cada variable ─────────────────────────────────────────────

interface VarMeta {
  label: string
  format: (v: number) => string
  description: string
  /** Para colorear tendencia: 'up_bad' = subir es negativo, 'up_good' = subir es positivo */
  direction: 'up_bad' | 'up_good' | 'neutral'
  /** Si la variable es el ENSO, aplicar coloreo especial por umbral */
  isEnso?: true
}

const VARIABLE_META: Record<string, VarMeta> = {
  fed_funds_rate: {
    label: 'Tasa Fed',
    format: (v) => `${v.toFixed(2)}%`,
    description: 'Federal Funds Rate — tasa de referencia de la Fed (FRED)',
    direction: 'up_bad',
  },
  broad_dollar_idx: {
    label: 'Dólar (DXY)',
    format: (v) => v.toFixed(1),
    description: 'Broad Dollar Index — índice ponderado del USD (FRED)',
    direction: 'up_bad',
  },
  tc_oficial_usd_ars: {
    label: 'TC Oficial',
    format: (v) => `$${v.toFixed(0)} ARS`,
    description: 'Tipo de cambio oficial USD/ARS (BCRA)',
    direction: 'neutral',
  },
  enso_oni: {
    label: 'ENSO / ONI',
    format: (v) => (v >= 0 ? `+${v.toFixed(2)}` : v.toFixed(2)),
    description: 'Oceanic Niño Index (NOAA) — +0.5 = El Niño · −0.5 = La Niña',
    direction: 'neutral',
    isEnso: true,
  },
  retenciones_soja: {
    label: 'Retenc. Soja',
    format: (v) => `${v.toFixed(1)}%`,
    description: 'Derechos de exportación — porotos de soja (Argentina)',
    direction: 'up_bad',
  },
  retenciones_oro: {
    label: 'Retenc. Oro',
    format: (v) => `${v.toFixed(1)}%`,
    description: 'Derechos de exportación — oro en bruto (Argentina)',
    direction: 'up_bad',
  },
  retenciones_litio: {
    label: 'Retenc. Litio',
    format: (v) => `${v.toFixed(1)}%`,
    description: 'Derechos de exportación — carbonato/hidróxido de litio (Argentina)',
    direction: 'up_bad',
  },
  retenciones_cobre: {
    label: 'Retenc. Cobre',
    format: (v) => `${v.toFixed(1)}%`,
    description: 'Derechos de exportación — cobre y sus manufacturas (Argentina)',
    direction: 'up_bad',
  },
  retenciones_trigo: {
    label: 'Retenc. Trigo',
    format: (v) => `${v.toFixed(1)}%`,
    description: 'Derechos de exportación — trigo (Argentina)',
    direction: 'up_bad',
  },
  retenciones_gas: {
    label: 'Retenc. Gas',
    format: (v) => `${v.toFixed(1)}%`,
    description: 'Derechos de exportación — gas natural (Argentina)',
    direction: 'up_bad',
  },
  retenciones_maiz: {
    label: 'Retenc. Maíz',
    format: (v) => `${v.toFixed(1)}%`,
    description: 'Derechos de exportación — maíz (Decreto 230/2020)',
    direction: 'up_bad',
  },
}

// Variables a mostrar por commodity (orden de aparición)
const COMMODITY_VARS: Record<string, string[]> = {
  gold:    ['fed_funds_rate', 'broad_dollar_idx', 'tc_oficial_usd_ars', 'enso_oni', 'retenciones_oro'],
  soy:     ['fed_funds_rate', 'broad_dollar_idx', 'tc_oficial_usd_ars', 'enso_oni', 'retenciones_soja'],
  lithium: ['fed_funds_rate', 'broad_dollar_idx', 'tc_oficial_usd_ars', 'enso_oni', 'retenciones_litio'],
  copper:  ['fed_funds_rate', 'broad_dollar_idx', 'tc_oficial_usd_ars', 'enso_oni', 'retenciones_cobre'],
  natgas:  ['fed_funds_rate', 'broad_dollar_idx', 'tc_oficial_usd_ars', 'enso_oni', 'retenciones_gas'],
  wheat:   ['fed_funds_rate', 'broad_dollar_idx', 'tc_oficial_usd_ars', 'enso_oni', 'retenciones_trigo'],
  corn:    ['fed_funds_rate', 'broad_dollar_idx', 'tc_oficial_usd_ars', 'enso_oni', 'retenciones_maiz'],
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function ensoColor(v: number): string {
  if (v >= 1.5)  return '#b45309'  // El Niño fuerte — amber
  if (v >= 0.5)  return '#ca8a04'  // El Niño moderado — yellow
  if (v <= -1.5) return '#1d4ed8'  // La Niña fuerte — blue
  if (v <= -0.5) return '#2563eb'  // La Niña moderada — blue suave
  return T.muted                   // Neutro
}

function ensoLabel(v: number): string {
  if (v >= 1.5)  return 'El Niño fuerte'
  if (v >= 0.5)  return 'El Niño'
  if (v <= -1.5) return 'La Niña fuerte'
  if (v <= -0.5) return 'La Niña'
  return 'Neutro'
}

// ─── Componente principal ────────────────────────────────────────────────────

export function ImpactRadar({ commodityId }: Props) {
  const [vars, setVars] = useState<ImpactVariable[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    // Traemos todas las variables (commodity=null + commodity-específicas)
    // El endpoint /latest devuelve el último valor de cada variable
    Promise.all([
      api.variables.latest(),           // globales (fed_rate, dxy, tc, enso)
      api.variables.latest(commodityId), // commodity-específicas (retenciones)
    ])
      .then(([global, specific]) => {
        // Unir y deduplicar (specific puede repetir globales si tiene mismo nombre)
        const merged = new Map<string, ImpactVariable>()
        for (const v of [...global, ...specific]) {
          merged.set(v.variable_name, v)
        }
        setVars([...merged.values()])
      })
      .catch(() => setVars([]))
      .finally(() => setLoading(false))
  }, [commodityId])

  const varKeys = COMMODITY_VARS[commodityId] ?? Object.keys(VARIABLE_META)
  const varMap = Object.fromEntries(vars.map((v) => [v.variable_name, v]))

  return (
    <div
      style={{
        background: T.surface,
        border: `1px solid ${T.hairline}`,
        borderRadius: 10,
        padding: '18px 20px',
      }}
    >
      {/* Título */}
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: 8,
          marginBottom: 16,
          paddingBottom: 10,
          borderBottom: `1px solid ${T.hairline}`,
        }}
      >
        <span style={{ fontWeight: 700, fontSize: 13, color: T.text }}>
          Variables de Contexto
        </span>
        <span style={{ fontSize: 11, color: T.faint }}>
          Fed · DXY · TC · ENSO · Retenciones AR
        </span>
      </div>

      {/* Grid de cards */}
      {loading ? (
        <div style={{ color: T.faint, fontSize: 12, padding: '8px 0' }}>Cargando…</div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
            gap: 10,
          }}
        >
          {varKeys.map((key) => {
            const meta = VARIABLE_META[key]
            const entry = varMap[key]
            if (!meta) return null

            const value = entry?.value ?? null
            const isEnso = meta.isEnso === true

            return (
              <VarCard
                key={key}
                label={meta.label}
                value={value}
                prevValue={entry?.prev_value}
                format={meta.format}
                description={meta.description}
                isEnso={isEnso}
                direction={meta.direction}
                date={entry?.date}
                source={entry?.source}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}

// ─── VarCard ─────────────────────────────────────────────────────────────────

interface VarCardProps {
  label: string
  value: number | null
  prevValue?: number | null
  format: (v: number) => string
  description: string
  isEnso: boolean
  direction: 'up_bad' | 'up_good' | 'neutral'
  date?: string
  source?: string
}

function VarCard({ label, value, prevValue, format, description, isEnso, direction, date, source }: VarCardProps) {
  const [hovered, setHovered] = useState(false)

  const displayValue = value !== null ? format(value) : '—'

  let valueColor = T.text
  if (isEnso && value !== null) valueColor = ensoColor(value)

  // Tendencia
  let deltaEl: React.ReactNode = null
  if (value !== null && prevValue !== null && prevValue !== undefined) {
    const delta = value - prevValue
    const absDelta = Math.abs(delta)
    const pct = prevValue !== 0 ? (delta / prevValue) * 100 : 0
    const rising = delta > 0
    const trendColor =
      direction === 'neutral'  ? T.muted
      : direction === 'up_bad'  ? (rising ? T.negative : T.positive)
      : /* up_good */             (rising ? T.positive : T.negative)

    const arrow = rising ? '▲' : '▼'
    const fmt = absDelta < 0.01 ? absDelta.toFixed(4)
              : absDelta < 1    ? absDelta.toFixed(2)
              : absDelta < 10   ? absDelta.toFixed(1)
              : absDelta.toFixed(0)

    deltaEl = (
      <span style={{ fontSize: 10, color: trendColor, fontWeight: 600, marginLeft: 5 }}>
        {arrow} {fmt} ({pct > 0 ? '+' : ''}{pct.toFixed(1)}%)
      </span>
    )
  }

  const dateLabel = date
    ? new Date(date + 'T12:00:00').toLocaleDateString('es-AR', { month: 'short', year: '2-digit' })
    : null

  return (
    <div
      title={description}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? T.surface2 : T.bg,
        border: `1px solid ${T.hairline}`,
        borderRadius: 8,
        padding: '12px 14px',
        cursor: 'default',
        transition: 'background 0.15s',
      }}
    >
      <div style={{ fontSize: 11, color: T.muted, marginBottom: 5, fontWeight: 500 }}>
        {label}
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          flexWrap: 'wrap',
          gap: 0,
        }}
      >
        <span
          style={{
            fontSize: 18,
            fontWeight: 700,
            fontFamily: T.mono,
            color: valueColor,
            lineHeight: 1.1,
          }}
        >
          {displayValue}
        </span>
        {deltaEl}
      </div>
      {isEnso && value !== null && (
        <div style={{ fontSize: 10, color: valueColor, marginTop: 3, fontWeight: 500 }}>
          {ensoLabel(value)}
        </div>
      )}
      {dateLabel && (
        <div style={{ fontSize: 10, color: T.faint, marginTop: 4 }}>
          {dateLabel}{source ? ` · ${source.replace('_', ' ')}` : ''}
        </div>
      )}
    </div>
  )
}
