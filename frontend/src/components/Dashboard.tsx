import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { Commodity } from '../types'
import { CommodityCard } from './CommodityCard'
import { PriceChart } from './PriceChart'
import { TradeFlowChart } from './TradeFlowChart'
import { CompanyValuationPanel } from './CompanyValuationPanel'
import { NewsPanel } from './NewsPanel'
import { ImpactRadar } from './ImpactRadar'
import { WeeklySummary } from './WeeklySummary'
import { AlertBanner } from './AlertBanner'
import { TradePartnersChart } from './TradePartnersChart'
import { AdminPanel } from './AdminPanel'

function useIsMobile(breakpoint = 768): boolean {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < breakpoint)
  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < breakpoint)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [breakpoint])
  return isMobile
}

export function Dashboard() {
  const [commodities, setCommodities] = useState<Commodity[]>([])
  const [selected, setSelected] = useState<string>('gold')
  const [showAdmin, setShowAdmin] = useState(false)
  const isMobile = useIsMobile()

  useEffect(() => {
    api.commodities.list().then((data) => {
      setCommodities(data)
      if (data.length > 0 && !data.find((c) => c.id === selected)) {
        setSelected(data[0].id)
      }
    })
  }, [])

  const current = commodities.find((c) => c.id === selected)

  const cols2 = isMobile ? '1fr' : '1fr 1fr'
  const padH  = isMobile ? 16 : 32

  return (
    <div
      style={{
        minHeight: '100vh',
        background: T.bg,
        fontFamily: T.sans,
        color: T.text,
      }}
    >
      {/* Header */}
      <header
        style={{
          background: T.surface,
          borderBottom: `1px solid ${T.hairline}`,
          padding: `14px ${padH}px`,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
        }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 8,
            background: T.blue,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 17,
            flexShrink: 0,
          }}
        >
          ⛏
        </div>
        <div>
          <div
            style={{
              fontWeight: 700,
              fontSize: 17,
              letterSpacing: '-0.02em',
              color: T.text,
            }}
          >
            Comm-Track
          </div>
          <div style={{ color: T.muted, fontSize: 12 }}>
            Monitor de Commodities · Argentina
          </div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ color: T.faint, fontSize: 12 }}>
            {new Date().toLocaleDateString('es-AR', { dateStyle: 'long' })}
          </div>
          <button
            onClick={() => setShowAdmin(true)}
            style={{
              padding: '5px 12px',
              fontSize: 12,
              fontWeight: 600,
              borderRadius: 6,
              border: `1px solid ${T.hairline}`,
              background: T.surface2,
              color: T.muted,
              cursor: 'pointer',
              fontFamily: T.sans,
              letterSpacing: '0.01em',
            }}
          >
            Admin
          </button>
        </div>
      </header>

      {showAdmin && <AdminPanel onClose={() => setShowAdmin(false)} />}

      <main style={{ padding: `28px ${padH}px`, maxWidth: 1280, margin: '0 auto' }}>

        {/* Commodity selector */}
        <div
          style={{
            display: 'flex',
            gap: 12,
            flexWrap: 'wrap',
            marginBottom: 24,
          }}
        >
          {commodities.map((c) => (
            <CommodityCard
              key={c.id}
              commodityId={c.id}
              nameEs={c.name_es}
              unit={c.unit}
              selected={selected === c.id}
              onClick={() => setSelected(c.id)}
            />
          ))}
        </div>

        {/* Alertas activas */}
        {current && <AlertBanner commodityId={current.id} />}

        {/* Gráfico de precios + exportaciones */}
        {current && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: cols2,
              gap: 20,
              marginBottom: 20,
            }}
          >
            <PriceChart
              commodityId={current.id}
              nameEs={current.name_es}
              unit={current.unit}
            />
            <TradeFlowChart
              commodityId={current.id}
              nameEs={current.name_es}
            />
          </div>
        )}

        {/* Resumen semanal LLM + Socios comerciales */}
        {current && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: cols2,
              gap: 20,
              marginBottom: 20,
            }}
          >
            <WeeklySummary commodityId={current.id} />
            <TradePartnersChart
              commodityId={current.id}
              nameEs={current.name_es}
            />
          </div>
        )}

        {/* Variables de contexto (full width) */}
        {current && (
          <div style={{ marginBottom: 20 }}>
            <ImpactRadar commodityId={current.id} />
          </div>
        )}

        {/* 2 columnas: empresas + noticias */}
        {current && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: cols2,
              gap: 20,
              alignItems: 'start',
            }}
          >
            <CompanyValuationPanel commodityId={current.id} />
            <NewsPanel commodityId={current.id} />
          </div>
        )}
      </main>
    </div>
  )
}
