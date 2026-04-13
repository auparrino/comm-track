import { useEffect, useState } from 'react'
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

const LABELS: Record<string, string> = {
  lithium: 'LITIO',
  gold:    'ORO',
  soy:     'SOJA',
}

interface Props {
  commodityId: string
  nameEs: string
  unit: string
  selected: boolean
  onClick: () => void
}

export function CommodityCard({ commodityId, nameEs, unit, selected, onClick }: Props) {
  const [price, setPrice]   = useState<Price | null>(null)
  const [prev, setPrev]     = useState<Price | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.prices.latest(commodityId),
      api.prices.history(commodityId, 2, PRIMARY_PRICE_TYPE[commodityId] ?? 'futures'),
    ])
      .then(([latest, history]) => {
        setPrice(latest)
        if (history.length >= 2) setPrev(history[history.length - 2])
      })
      .catch(() => setPrice(null))
      .finally(() => setLoading(false))
  }, [commodityId])

  const color  = T.colors[commodityId] ?? T.blue
  const change = price && prev ? ((price.price - prev.price) / prev.price) * 100 : null
  const up     = change !== null && change >= 0

  return (
    <button
      onClick={onClick}
      style={{
        background:   T.surface,
        border:       `1px solid ${selected ? color : T.hairline}`,
        borderLeft:   `3px solid ${selected ? color : 'transparent'}`,
        borderRadius: 8,
        padding:      '16px 20px',
        cursor:       'pointer',
        textAlign:    'left',
        transition:   'border-color 0.15s, box-shadow 0.15s',
        flex:         '1 1 180px',
        minWidth:     170,
        boxShadow:    selected ? `0 2px 12px ${color}22` : 'none',
      }}
    >
      {/* Label */}
      <div
        style={{
          fontSize:      11,
          fontWeight:    700,
          letterSpacing: '0.08em',
          color:         selected ? color : T.muted,
          marginBottom:  10,
        }}
      >
        {LABELS[commodityId] ?? nameEs.toUpperCase()}
      </div>

      {loading ? (
        <div style={{ color: T.faint, fontSize: 13 }}>Cargando…</div>
      ) : price ? (
        <>
          <div
            style={{
              color:       T.text,
              fontSize:    26,
              fontWeight:  700,
              lineHeight:  1,
              fontFamily:  T.mono,
              letterSpacing: '-0.02em',
            }}
          >
            {price.price.toLocaleString('en-US', {
              minimumFractionDigits:  2,
              maximumFractionDigits:  2,
            })}
          </div>
          <div style={{ color: T.faint, fontSize: 11, marginTop: 3 }}>{unit}</div>

          {change !== null && (
            <div
              style={{
                marginTop:  10,
                fontSize:   12,
                fontWeight: 700,
                color:      up ? T.positive : T.negative,
                display:    'flex',
                alignItems: 'center',
                gap:        3,
              }}
            >
              <span style={{ fontSize: 10 }}>{up ? '▲' : '▼'}</span>
              {Math.abs(change).toFixed(2)}%
            </div>
          )}
        </>
      ) : (
        <div style={{ color: T.faint, fontSize: 13 }}>Sin datos</div>
      )}
    </button>
  )
}
