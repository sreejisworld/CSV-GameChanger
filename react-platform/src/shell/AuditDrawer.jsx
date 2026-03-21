/**
 * AuditDrawer — slide-in right panel showing live audit trail feed.
 *
 * • Opens via the clock icon in TopHeader or keyboard shortcut A
 * • Polls GET /audit/recent every 5 s while open
 * • Color-codes rows by severity: error=red, warning=amber,
 *   success=lime, info=blue
 * • Rows show: agent badge | action | logic (truncated) | hash stub
 */
import { useEffect, useRef, useState } from 'react'
import { useAppStore } from '../store/useAppStore.js'

const API_BASE = 'http://localhost:8000'
const POLL_MS  = 5000

// Severity → Tailwind/CSS-var colour tokens
const SEV = {
  error:   { dot: '#ef4444', bg: 'rgba(239,68,68,0.08)',   border: 'rgba(239,68,68,0.2)',   text: '#ef4444' },
  warning: { dot: '#f59e0b', bg: 'rgba(245,158,11,0.08)',  border: 'rgba(245,158,11,0.2)',  text: '#f59e0b' },
  success: { dot: '#32CD32', bg: 'rgba(50,205,50,0.06)',   border: 'rgba(50,205,50,0.18)',  text: '#32CD32' },
  info:    { dot: '#007FFF', bg: 'rgba(0,127,255,0.06)',   border: 'rgba(0,127,255,0.18)',  text: '#007FFF' },
}

function fmt(ts) {
  if (!ts) return '—'
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ts.slice(11, 19) || ts
  }
}

function AgentBadge({ agent }) {
  const short = agent.replace('Agent', '').replace('Controller', '').trim()
  return (
    <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded
                     bg-blue-dim border border-blue-DEFAULT/20
                     text-blue-DEFAULT shrink-0 whitespace-nowrap">
      {short}
    </span>
  )
}

export default function AuditDrawer({ open, onClose }) {
  const [rows,    setRows]    = useState([])
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)
  const [filter,  setFilter]  = useState('all')   // all | error | warning | success | info
  const intervalRef = useRef(null)
  const listRef     = useRef(null)
  const [autoScroll, setAutoScroll] = useState(true)

  const fetchRows = async () => {
    try {
      const sev = filter !== 'all' ? `&severity=${filter}` : ''
      const res = await fetch(`${API_BASE}/audit/recent?limit=100${sev}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setRows(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Start/stop polling when drawer opens/closes
  useEffect(() => {
    if (open) {
      setLoading(true)
      fetchRows()
      intervalRef.current = setInterval(fetchRows, POLL_MS)
    } else {
      clearInterval(intervalRef.current)
    }
    return () => clearInterval(intervalRef.current)
  }, [open, filter])

  // Auto-scroll to top (newest first) when new rows arrive
  useEffect(() => {
    if (autoScroll && listRef.current) {
      listRef.current.scrollTop = 0
    }
  }, [rows])

  // `A` key to close (same key used to open in TopHeader)
  useEffect(() => {
    if (!open) return
    const handler = e => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  const FILTERS = ['all', 'error', 'warning', 'success', 'info']

  return (
    <>
      {/* Backdrop — only on small screens to avoid blocking the app */}
      {open && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* ── Drawer panel ─────────────────────────────────── */}
      <div
        className="fixed top-0 right-0 h-screen z-40
                   flex flex-col bg-bg-surface border-l border-border-base
                   shadow-[−8px_0_32px_rgba(0,0,0,0.4)]"
        style={{
          width:     '380px',
          transform: open ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.24s cubic-bezier(0.4,0,0.2,1)',
        }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3
                        border-b border-border-base shrink-0">
          <svg width="14" height="14" viewBox="0 0 14 14" className="text-blue-DEFAULT shrink-0">
            <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.5" fill="none"/>
            <polyline points="7,4 7,7 9.5,9.5" stroke="currentColor"
                      strokeWidth="1.5" strokeLinecap="round" fill="none"/>
          </svg>
          <span className="text-xs font-semibold text-text-primary flex-1">
            Audit Trail
          </span>

          {/* Live indicator */}
          <span className="flex items-center gap-1.5 text-[9px] text-lime-DEFAULT">
            <span className="w-1.5 h-1.5 rounded-full bg-lime-DEFAULT animate-pulse" />
            LIVE
          </span>

          {/* Close */}
          <button
            onClick={onClose}
            className="w-6 h-6 rounded flex items-center justify-center
                       text-text-muted hover:text-text-primary
                       hover:bg-bg-hover transition-colors text-sm"
          >
            ×
          </button>
        </div>

        {/* Severity filter pills */}
        <div className="flex gap-1.5 px-4 py-2 border-b border-border-base
                        shrink-0 overflow-x-auto">
          {FILTERS.map(f => {
            const c    = f !== 'all' ? SEV[f] : null
            const active = filter === f
            return (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className="text-[9px] px-2 py-1 rounded-full border
                           capitalize shrink-0 transition-colors"
                style={{
                  background: active
                    ? (c?.bg ?? 'rgba(0,127,255,0.12)')
                    : 'transparent',
                  borderColor: active
                    ? (c?.border ?? 'rgba(0,127,255,0.3)')
                    : 'var(--border-base)',
                  color: active
                    ? (c?.text ?? '#007FFF')
                    : 'var(--text-muted)',
                }}
              >
                {f === 'all' ? 'All' : f}
              </button>
            )
          })}
          <label className="ml-auto flex items-center gap-1 text-[9px]
                             text-text-muted cursor-pointer shrink-0">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={e => setAutoScroll(e.target.checked)}
              className="w-3 h-3"
            />
            Auto-scroll
          </label>
        </div>

        {/* Row count */}
        <div className="px-4 py-1.5 text-[9px] text-text-muted shrink-0">
          {loading ? 'Loading…' : error
            ? <span className="text-red-400">Error: {error}</span>
            : `${rows.length} events · refreshes every 5 s`
          }
        </div>

        {/* Event list */}
        <div
          ref={listRef}
          className="flex-1 overflow-y-auto px-3 pb-4 space-y-1.5"
        >
          {rows.length === 0 && !loading && !error && (
            <p className="text-text-muted text-xs text-center py-12">
              No audit events found.
            </p>
          )}

          {rows.map((row, i) => {
            const c = SEV[row.severity] ?? SEV.info
            return (
              <div
                key={`${row.hash}-${i}`}
                className="rounded-lg px-3 py-2.5 border"
                style={{
                  background:   c.bg,
                  borderColor:  c.border,
                }}
              >
                {/* Top row: time + agent badge */}
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-[9px] text-text-muted font-mono shrink-0">
                    {fmt(row.timestamp)}
                  </span>
                  <AgentBadge agent={row.agent} />
                  <span
                    className="w-1.5 h-1.5 rounded-full shrink-0 ml-auto"
                    style={{ background: c.dot }}
                    title={row.severity}
                  />
                </div>

                {/* Action */}
                <p className="text-[11px] font-semibold text-text-primary
                               leading-tight truncate mb-1">
                  {row.action.replace(/_/g, ' ')}
                </p>

                {/* Logic (truncated) */}
                {row.logic && (
                  <p className="text-[10px] text-text-muted leading-snug
                                 line-clamp-2">
                    {row.logic}
                  </p>
                )}

                {/* Footer: impact + hash */}
                <div className="flex items-center gap-2 mt-1.5">
                  <span
                    className="text-[9px] font-medium"
                    style={{ color: c.text }}
                  >
                    {row.impact}
                  </span>
                  <span className="ml-auto text-[8px] text-text-muted
                                   font-mono opacity-50">
                    #{row.hash}
                  </span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer */}
        <div className="border-t border-border-base px-4 py-2 shrink-0">
          <p className="text-[9px] text-text-muted text-center">
            21 CFR Part 11 · Append-only · Tamper-evident SHA-256
          </p>
        </div>
      </div>
    </>
  )
}
