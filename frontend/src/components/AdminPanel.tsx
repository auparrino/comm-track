import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../utils/api'
import { T } from '../utils/theme'
import type { PipelineStatus } from '../types'

const STATUS_COLOR: Record<string, string> = {
  success:   T.positive,
  error:     T.negative,
  running:   '#CA8A04',   // amber
  never_run: T.faint,
}

const STATUS_LABEL: Record<string, string> = {
  success:   'OK',
  error:     'ERROR',
  running:   'CORRIENDO',
  never_run: 'SIN EJECUTAR',
}

function fmt(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso + (iso.endsWith('Z') ? '' : 'Z'))
  return d.toLocaleString('es-AR', {
    day:    '2-digit',
    month:  '2-digit',
    hour:   '2-digit',
    minute: '2-digit',
  })
}

interface RowProps {
  p: PipelineStatus
  onRun: (name: string) => void
  triggering: boolean
}

function PipelineRow({ p, onRun, triggering }: RowProps) {
  const statusColor = STATUS_COLOR[p.status] ?? T.faint
  const statusLabel = STATUS_LABEL[p.status] ?? p.status

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '160px 1fr auto auto',
        gap: 16,
        alignItems: 'center',
        padding: '12px 0',
        borderBottom: `1px solid ${T.hairline}`,
      }}
    >
      {/* Nombre + descripción */}
      <div>
        <div style={{ fontFamily: T.mono, fontSize: 13, fontWeight: 600, color: T.text }}>
          {p.pipeline_name}
        </div>
        <div style={{ fontSize: 11, color: T.muted, marginTop: 2 }}>{p.description}</div>
      </div>

      {/* Último run + error */}
      <div>
        <div style={{ fontSize: 12, color: T.muted }}>
          Último run: <span style={{ color: T.text }}>{fmt(p.last_run)}</span>
        </div>
        {p.status === 'success' && (
          <div style={{ fontSize: 11, color: T.faint, marginTop: 2 }}>
            {p.records_processed} procesados · {p.records_skipped} saltados
          </div>
        )}
        {p.error_message && (
          <div
            style={{
              fontSize: 11,
              color: T.negative,
              marginTop: 2,
              fontFamily: T.mono,
              maxWidth: 380,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={p.error_message}
          >
            {p.error_message}
          </div>
        )}
      </div>

      {/* Badge de estado */}
      <div
        style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: '0.06em',
          color: statusColor,
          background: `${statusColor}18`,
          border: `1px solid ${statusColor}40`,
          borderRadius: 4,
          padding: '2px 7px',
          whiteSpace: 'nowrap',
        }}
      >
        {statusLabel}
      </div>

      {/* Botón Run */}
      <button
        onClick={() => onRun(p.pipeline_name)}
        disabled={triggering || p.status === 'running'}
        style={{
          padding: '6px 14px',
          fontSize: 12,
          fontWeight: 600,
          borderRadius: 6,
          border: `1px solid ${T.blue}`,
          background: triggering ? T.surface2 : T.blue,
          color: triggering ? T.muted : '#fff',
          cursor: triggering ? 'not-allowed' : 'pointer',
          transition: 'opacity .15s',
          fontFamily: T.sans,
          whiteSpace: 'nowrap',
        }}
      >
        {triggering ? 'Ejecutando…' : '▶ Run'}
      </button>
    </div>
  )
}

interface Props {
  onClose: () => void
}

export function AdminPanel({ onClose }: Props) {
  const [pipelines, setPipelines]   = useState<PipelineStatus[]>([])
  const [loading, setLoading]       = useState(true)
  const [triggering, setTriggering] = useState<Record<string, boolean>>({})
  const [toast, setToast]           = useState<string | null>(null)
  const intervalRef                 = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchStatus = useCallback(() => {
    api.admin.pipelines()
      .then(setPipelines)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchStatus()
    intervalRef.current = setInterval(fetchStatus, 5000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [fetchStatus])

  const handleRun = async (name: string) => {
    setTriggering((t) => ({ ...t, [name]: true }))
    try {
      await api.admin.run(name)
      setToast(`Pipeline "${name}" iniciado`)
      setTimeout(() => setToast(null), 3500)
      setTimeout(fetchStatus, 1000)
    } catch (e) {
      setToast(`Error al disparar "${name}"`)
      setTimeout(() => setToast(null), 3500)
    } finally {
      setTriggering((t) => ({ ...t, [name]: false }))
    }
  }

  return (
    <>
      {/* Overlay de fondo */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,.35)',
          zIndex: 100,
        }}
      />

      {/* Panel deslizante */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: 'min(680px, 100vw)',
          background: T.surface,
          borderLeft: `1px solid ${T.hairline}`,
          zIndex: 101,
          overflowY: 'auto',
          fontFamily: T.sans,
          color: T.text,
        }}
      >
        {/* Header del panel */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '18px 24px',
            borderBottom: `1px solid ${T.hairline}`,
            position: 'sticky',
            top: 0,
            background: T.surface,
            zIndex: 1,
          }}
        >
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>Administración de Pipelines</div>
            <div style={{ color: T.muted, fontSize: 12, marginTop: 2 }}>
              Estado en tiempo real · refresca cada 5 s
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: 20,
              color: T.muted,
              lineHeight: 1,
              padding: 4,
            }}
          >
            ✕
          </button>
        </div>

        {/* Cuerpo */}
        <div style={{ padding: '8px 24px 32px' }}>
          {loading ? (
            <div style={{ color: T.muted, padding: '32px 0', textAlign: 'center' }}>
              Cargando…
            </div>
          ) : (
            pipelines.map((p) => (
              <PipelineRow
                key={p.pipeline_name}
                p={p}
                onRun={handleRun}
                triggering={!!triggering[p.pipeline_name]}
              />
            ))
          )}
        </div>
      </div>

      {/* Toast de confirmación */}
      {toast && (
        <div
          style={{
            position: 'fixed',
            bottom: 28,
            left: '50%',
            transform: 'translateX(-50%)',
            background: T.text,
            color: T.surface,
            padding: '10px 20px',
            borderRadius: 8,
            fontSize: 13,
            zIndex: 200,
            fontFamily: T.sans,
            pointerEvents: 'none',
          }}
        >
          {toast}
        </div>
      )}
    </>
  )
}
