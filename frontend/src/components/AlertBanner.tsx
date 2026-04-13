import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { Alert } from '../types'

interface Props {
  commodityId: string
}

const SEVERITY_STYLE: Record<string, { bg: string; border: string; dot: string }> = {
  high:   { bg: '#FFF3CD', border: '#F59E0B', dot: '#D97706' },
  medium: { bg: '#EFF6FF', border: '#93C5FD', dot: '#3B82F6' },
}

export function AlertBanner({ commodityId }: Props) {
  const [alerts, setAlerts] = useState<Alert[]>([])

  useEffect(() => {
    api.alerts
      .list(commodityId, true)
      .then(setAlerts)
      .catch(() => setAlerts([]))
  }, [commodityId])

  if (alerts.length === 0) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
      {alerts.map((alert) => {
        const style = SEVERITY_STYLE[alert.severity] ?? SEVERITY_STYLE.medium
        return (
          <div
            key={alert.id}
            style={{
              background: style.bg,
              border: `1px solid ${style.border}`,
              borderLeft: `4px solid ${style.dot}`,
              borderRadius: 6,
              padding: '10px 14px',
              display: 'flex',
              gap: 10,
              alignItems: 'flex-start',
            }}
          >
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: style.dot,
                flexShrink: 0,
                marginTop: 5,
              }}
            />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: T.text,
                  marginBottom: 2,
                }}
              >
                {alert.title}
              </div>
              {alert.description && (
                <div style={{ fontSize: 12, color: T.muted, lineHeight: 1.5 }}>
                  {alert.description}
                </div>
              )}
            </div>
            {alert.signal_type && (
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 600,
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                  color: style.dot,
                  flexShrink: 0,
                  marginTop: 2,
                }}
              >
                {alert.signal_type}
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}
