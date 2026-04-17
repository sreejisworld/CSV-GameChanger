import { useState, useEffect, useCallback } from 'react'
import { API_BASE } from '../../config.js'

const API = API_BASE

const ACTION_COLORS = {
  FILE_EDITED:              { bg: 'rgba(100,116,139,0.12)', text: '#64748b' },
  FILE_WRITTEN:             { bg: 'rgba(100,116,139,0.12)', text: '#64748b' },
  URS_GENERATED:            { bg: 'rgba(0,127,255,0.12)',   text: '#007FFF' },
  URS_VERIFIED:             { bg: 'rgba(50,205,50,0.12)',   text: '#32CD32' },
  COMPLIANCE_EXCEPTION:     { bg: 'rgba(239,68,68,0.12)',   text: '#ef4444' },
  RISK_ASSESSMENT_COMPLETED:{ bg: 'rgba(245,158,11,0.12)', text: '#f59e0b' },
  TEST_RUN_SIGNED_OFF:      { bg: 'rgba(50,205,50,0.12)',   text: '#32CD32' },
  RELEASE_APPROVAL_SIGNED:  { bg: 'rgba(50,205,50,0.12)',   text: '#32CD32' },
  RELEASE_APPROVED:         { bg: 'rgba(50,205,50,0.15)',   text: '#32CD32' },
}

function downloadCSV(filename, headers, rows) {
  const escape = v =>
    `"${String(v ?? '').replace(/"/g, '""')}"`
  const lines = [
    headers.join(','),
    ...rows.map(r => headers.map(h => escape(r[h])).join(',')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

function ActionBadge({ action }) {
  const cfg = ACTION_COLORS[action] ?? {
    bg: 'rgba(100,116,139,0.12)', text: '#64748b',
  }
  return (
    <span
      className="text-[9px] font-semibold px-1.5 py-0.5 rounded whitespace-nowrap"
      style={{ background: cfg.bg, color: cfg.text }}
    >
      {action.replace(/_/g, ' ')}
    </span>
  )
}

export default function AuditTrailTab() {
  const [rows,        setRows]        = useState([])
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState('')
  const [filter,      setFilter]      = useState('')
  const [autoRefresh, setAutoRefresh] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API}/audit-trail`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setRows(data.records ?? [])
    } catch (err) {
      setError(
        `Could not load audit trail: ${err.message}. ` +
        'Ensure FastAPI is running on port 8000.'
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!autoRefresh) return
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [autoRefresh, load])

  const filtered = rows.filter(r =>
    !filter || JSON.stringify(r).toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 pb-3 shrink-0">
        <input
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="Filter records…"
          className="evolv-input text-xs px-2 py-1.5 w-56"
        />
        <button
          onClick={load}
          disabled={loading}
          className="px-3 py-1.5 text-xs rounded border border-border-base
                     text-text-muted hover:text-text-secondary
                     hover:border-border-bright transition-colors"
        >
          {loading ? 'Loading…' : '↻ Refresh'}
        </button>
        <label className="flex items-center gap-1.5 text-[11px] text-text-muted
                          cursor-pointer select-none">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={e => setAutoRefresh(e.target.checked)}
            className="w-3 h-3"
          />
          Auto-refresh (5s)
        </label>
        <button
          onClick={() => {
            downloadCSV(
              `audit-trail-${new Date().toISOString().slice(0, 10)}.csv`,
              ['timestamp', 'agent_name', 'action', 'user_id',
               'decision_logic', 'compliance_impact', 'reasoning_hash'],
              filtered,
            )
          }}
          className="px-3 py-1.5 text-xs rounded border border-border-base
                     text-text-muted hover:text-text-secondary
                     hover:border-border-bright transition-colors"
        >
          📥 Export CSV
        </button>
        <span className="ml-auto text-[10px] text-text-muted">
          {filtered.length} record{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {error && (
        <div className="mb-3 px-4 py-2 rounded border border-red-500/30
                        bg-red-500/10 text-[11px] text-red-400 shrink-0">
          {error}
          <div className="mt-2 text-[10px] opacity-70">
            Fallback: showing dev audit trail from this session.
          </div>
        </div>
      )}

      <div className="flex-1 overflow-auto">
        {filtered.length === 0 && !loading ? (
          <div className="flex flex-col items-center justify-center h-full
                          text-text-muted gap-2">
            <span className="text-2xl opacity-30">📋</span>
            <p className="text-xs">No audit records found.</p>
            <p className="text-[10px]">
              Run through the lifecycle to generate records.
            </p>
          </div>
        ) : (
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border-base">
                {['Timestamp', 'Agent', 'Action', 'User',
                  'Decision Logic', 'Compliance Impact', 'Hash'].map(h => (
                  <th key={h}
                    className="text-left text-[10px] font-semibold text-text-muted
                               uppercase tracking-wide py-2 pr-4 whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, i) => (
                <tr key={i}
                  className="border-b border-border-base hover:bg-bg-hover/30
                             transition-colors">
                  <td className="py-2 pr-4 font-mono text-[10px] text-text-muted
                                 whitespace-nowrap">
                    {row.timestamp
                      ? new Date(row.timestamp).toLocaleString()
                      : '—'}
                  </td>
                  <td className="py-2 pr-4 text-text-secondary text-[11px]
                                 whitespace-nowrap">
                    {row.agent_name ?? '—'}
                  </td>
                  <td className="py-2 pr-4">
                    <ActionBadge action={row.action ?? ''} />
                  </td>
                  <td className="py-2 pr-4 text-text-muted text-[10px]
                                 whitespace-nowrap">
                    {row.user_id ?? '—'}
                  </td>
                  <td className="py-2 pr-4 text-text-muted text-[11px]
                                 max-w-[200px]">
                    <span className="line-clamp-2">
                      {row.decision_logic ?? '—'}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-[10px] whitespace-nowrap">
                    <span className={`
                      px-1.5 py-0.5 rounded text-[9px]
                      ${row.compliance_impact === 'Electronic Signature'
                        ? 'bg-lime-DEFAULT/10 text-lime-DEFAULT'
                        : row.compliance_impact === 'Release Authorization'
                          ? 'bg-blue-dim text-blue-DEFAULT'
                          : 'text-text-muted'}
                    `}>
                      {row.compliance_impact ?? '—'}
                    </span>
                  </td>
                  <td className="py-2 font-mono text-[9px] text-text-muted
                                 max-w-[80px]">
                    <span className="truncate block" title={row.reasoning_hash}>
                      {row.reasoning_hash
                        ? row.reasoning_hash.slice(0, 12) + '…'
                        : '—'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
