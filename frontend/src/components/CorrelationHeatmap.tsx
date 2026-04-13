import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { T } from '../utils/theme'

interface CorrelationEntry {
  c1: string
  c2: string
  r: number | null
  n: number
}

interface CorrelationData {
  window: number
  commodities: string[]
  matrix: CorrelationEntry[]
}

const WINDOWS = [
  { label: '30d',  days: 30  },
  { label: '90d',  days: 90  },
  { label: '180d', days: 180 },
]

const NAMES: Record<string, string> = {
  gold:    'Oro',
  soy:     'Soja',
  lithium: 'Litio',
  copper:  'Cobre',
  natgas:  'Gas',
  wheat:   'Trigo',
  corn:    'Maíz',
}

/** Interpola entre dos colores hex en función de t ∈ [0,1] */
function lerp(a: number, b: number, t: number) {
  return Math.round(a + (b - a) * t)
}

function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

/** Mapea r ∈ [-1, 1] → color.
 *  -1 = rojo  |  0 = crema (fondo)  |  +1 = verde */
function correlationColor(r: number | null): string {
  if (r === null) return T.bg
  const neg = hexToRgb('#c0392b')  // rojo
  const mid = hexToRgb('#FDF0D5')  // crema (T.bg)
  const pos = hexToRgb('#1a7a4a')  // verde
  const [from, to, t] = r >= 0
    ? [mid, pos, r]
    : [neg, mid, 1 + r]
  const rgb = [0, 1, 2].map(i => lerp(from[i], to[i], t))
  return `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`
}

function textColor(r: number | null): string {
  if (r === null) return T.faint
  return Math.abs(r) > 0.4 ? '#fff' : T.text
}

export function CorrelationHeatmap() {
  const [data, setData]       = useState<CorrelationData | null>(null)
  const [window, setWindow]   = useState(90)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.prices
      .correlations(window)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [window])

  const commodities = data?.commodities ?? []

  // Construye lookup r[c1][c2]
  const lookup: Record<string, Record<string, number | null>> = {}
  data?.matrix.forEach(({ c1, c2, r }) => {
    if (!lookup[c1]) lookup[c1] = {}
    lookup[c1][c2] = r
  })

  const CELL = 56  // px por celda
  const LABEL_W = 52

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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
        <div>
          <span style={{ color: T.text, fontWeight: 600, fontSize: 15 }}>
            Correlaciones de precios
          </span>
          <span style={{ color: T.faint, fontSize: 11, marginLeft: 8, fontFamily: T.mono }}>
            Pearson · ventana {window}d
          </span>
        </div>

        {/* Window selector */}
        <div style={{ display: 'flex', gap: 4, background: T.bg, borderRadius: 6, padding: 3 }}>
          {WINDOWS.map((w) => (
            <button
              key={w.days}
              onClick={() => setWindow(w.days)}
              style={{
                background:   window === w.days ? T.text : 'transparent',
                color:        window === w.days ? '#fff' : T.muted,
                border:       'none',
                borderRadius: 4,
                padding:      '4px 10px',
                fontSize:     12,
                fontWeight:   600,
                cursor:       'pointer',
                transition:   'background 0.15s',
                fontFamily:   T.sans,
              }}
            >
              {w.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ color: T.faint, fontSize: 13, textAlign: 'center', padding: 40 }}>
          Calculando…
        </div>
      ) : !data || commodities.length === 0 ? (
        <div style={{ color: T.faint, fontSize: 13, textAlign: 'center', padding: 40 }}>
          Sin datos suficientes
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ borderCollapse: 'collapse', tableLayout: 'fixed' }}>
            <thead>
              <tr>
                {/* Esquina vacía */}
                <th style={{ width: LABEL_W, minWidth: LABEL_W }} />
                {commodities.map((c) => (
                  <th
                    key={c}
                    style={{
                      width:      CELL,
                      minWidth:   CELL,
                      fontSize:   11,
                      fontWeight: 600,
                      color:      T.colors[c] ?? T.blue,
                      textAlign:  'center',
                      paddingBottom: 8,
                      fontFamily: T.sans,
                    }}
                  >
                    {NAMES[c] ?? c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {commodities.map((row) => (
                <tr key={row}>
                  {/* Etiqueta de fila */}
                  <td
                    style={{
                      fontSize:   11,
                      fontWeight: 600,
                      color:      T.colors[row] ?? T.blue,
                      paddingRight: 8,
                      whiteSpace: 'nowrap',
                      fontFamily: T.sans,
                    }}
                  >
                    {NAMES[row] ?? row}
                  </td>
                  {commodities.map((col) => {
                    const r = lookup[row]?.[col] ?? null
                    const isdiag = row === col
                    return (
                      <td
                        key={col}
                        title={r !== null ? `${NAMES[row] ?? row} / ${NAMES[col] ?? col}: r = ${r}` : 'Sin datos'}
                        style={{
                          width:     CELL,
                          height:    CELL,
                          background: correlationColor(r),
                          textAlign: 'center',
                          verticalAlign: 'middle',
                          fontSize:  isdiag ? 10 : 12,
                          fontWeight: 700,
                          color:     isdiag ? T.muted : textColor(r),
                          fontFamily: T.mono,
                          border:    `1px solid ${T.hairline}`,
                          borderRadius: 3,
                          cursor:    'default',
                          transition: 'opacity 0.15s',
                          userSelect: 'none',
                        }}
                      >
                        {isdiag ? '—' : r !== null ? r.toFixed(2) : 'N/A'}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>

          {/* Leyenda */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 14 }}>
            <span style={{ fontSize: 10, color: T.faint, fontFamily: T.mono }}>−1</span>
            <div style={{
              width: 140,
              height: 8,
              borderRadius: 4,
              background: 'linear-gradient(to right, #c0392b, #FDF0D5, #1a7a4a)',
              border: `1px solid ${T.hairline}`,
            }} />
            <span style={{ fontSize: 10, color: T.faint, fontFamily: T.mono }}>+1</span>
            <span style={{ fontSize: 10, color: T.faint, marginLeft: 8 }}>
              correlación de precios spot · {window} días
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
