/**
 * Monitor — Lifecycle Phase 7: Operations & Monitoring
 *
 * React-native page with three tabs:
 *  - Audit Trail  : live viewer for output/audit_trail.csv
 *  - Deviations   : log and track deviations / CAPAs
 *  - System Health: project lifecycle status dashboard
 */
import { useState, useEffect, useCallback } from 'react'
import { useAppStore } from '../store/useAppStore.js'

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

const API = 'http://localhost:8000'

// ── Helpers ───────────────────────────────────────────────────────
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

function ActionBadge({ action }) {
  const cfg = ACTION_COLORS[action] ?? {
    bg: 'rgba(100,116,139,0.12)', text: '#64748b',
  }
  const short = action.replace(/_/g, ' ')
  return (
    <span
      className="text-[9px] font-semibold px-1.5 py-0.5 rounded whitespace-nowrap"
      style={{ background: cfg.bg, color: cfg.text }}
    >
      {short}
    </span>
  )
}

// ── Tab: Audit Trail ──────────────────────────────────────────────
function AuditTrailTab() {
  const [rows,    setRows]    = useState([])
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')
  const [filter,  setFilter]  = useState('')
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
      {/* Controls */}
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
                     text-text-muted hover:text-text-secondary hover:border-border-bright
                     transition-colors"
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
            const headers = [
              'timestamp', 'agent_name', 'action', 'user_id',
              'decision_logic', 'compliance_impact', 'reasoning_hash',
            ]
            downloadCSV(
              `audit-trail-${new Date()
                .toISOString().slice(0,10)}.csv`,
              headers,
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

      {/* Table */}
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
                {['Timestamp', 'Agent', 'Action', 'User', 'Decision Logic',
                  'Compliance Impact', 'Hash'].map(h => (
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

// ── Tab: Deviations ───────────────────────────────────────────────
const DEVIATION_TYPES  = ['Deviation', 'CAPA', 'Change Control', 'Incident']
const SEVERITY_OPTIONS = ['Critical', 'Major', 'Minor']
const STATUS_OPTIONS   = ['Open', 'Under Review', 'Resolved', 'Closed']

const SEVERITY_COLORS = {
  Critical: { bg: 'rgba(239,68,68,0.12)',  text: '#ef4444' },
  Major:    { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b' },
  Minor:    { bg: 'rgba(100,116,139,0.12)',text: '#64748b' },
}
const STATUS_COLORS = {
  Open:          { bg: 'rgba(239,68,68,0.10)',  text: '#ef4444' },
  'Under Review':{ bg: 'rgba(245,158,11,0.10)', text: '#f59e0b' },
  Resolved:      { bg: 'rgba(50,205,50,0.10)',  text: '#32CD32' },
  Closed:        { bg: 'rgba(100,116,139,0.10)',text: '#64748b' },
}

let _devId = 1

function DeviationsTab() {
  const [deviations, setDeviations] = useState([])
  const [form, setForm] = useState({
    type: DEVIATION_TYPES[0], title: '', description: '',
    severity: SEVERITY_OPTIONS[1], status: STATUS_OPTIONS[0],
    affectedReq: '',
  })
  const [showForm, setShowForm] = useState(false)

  const addDeviation = () => {
    if (!form.title.trim()) return
    setDeviations(prev => [{
      id:          `DEV-${String(_devId++).padStart(3, '0')}`,
      loggedAt:    new Date().toISOString(),
      ...form,
    }, ...prev])
    setForm({
      type: DEVIATION_TYPES[0], title: '', description: '',
      severity: SEVERITY_OPTIONS[1], status: STATUS_OPTIONS[0],
      affectedReq: '',
    })
    setShowForm(false)
  }

  const updateStatus = (id, status) =>
    setDeviations(prev =>
      prev.map(d => d.id === id ? { ...d, status } : d)
    )

  return (
    <div className="flex flex-col h-full">
      {/* Controls */}
      <div className="flex items-center gap-3 pb-3 shrink-0">
        <button
          onClick={() => setShowForm(v => !v)}
          className="px-3 py-1.5 text-xs rounded bg-blue-dim border
                     border-blue-DEFAULT/30 text-blue-DEFAULT
                     hover:opacity-90 transition-opacity"
        >
          {showForm ? '✕ Cancel' : '+ Log Deviation'}
        </button>
        <span className="ml-auto text-[10px] text-text-muted">
          {deviations.length} record{deviations.length !== 1 ? 's' : ''}
          {' · '}
          {deviations.filter(d => d.status === 'Open').length} open
        </span>
      </div>

      {/* Form */}
      {showForm && (
        <div className="mb-4 p-4 rounded-lg border border-border-base
                        bg-bg-card space-y-3 shrink-0">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-text-muted">Type</label>
              <select value={form.type}
                onChange={e => setForm(f => ({ ...f, type: e.target.value }))}
                className="evolv-input evolv-select text-xs px-2 py-1.5">
                {DEVIATION_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-text-muted">Severity</label>
              <select value={form.severity}
                onChange={e => setForm(f => ({ ...f, severity: e.target.value }))}
                className="evolv-input evolv-select text-xs px-2 py-1.5">
                {SEVERITY_OPTIONS.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-text-muted">Title</label>
            <input value={form.title}
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
              placeholder="Brief description of the deviation…"
              className="evolv-input text-xs px-2 py-1.5" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-text-muted">
              Details / Root Cause
            </label>
            <textarea value={form.description}
              onChange={e => setForm(f => ({
                ...f, description: e.target.value,
              }))}
              rows={2}
              placeholder="Root cause, impact, and proposed CAPA…"
              className="evolv-input text-xs px-2 py-1.5 resize-none" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-text-muted">
              Affected Requirement
            </label>
            <input value={form.affectedReq}
              onChange={e => setForm(f => ({
                ...f, affectedReq: e.target.value,
              }))}
              placeholder="e.g. UR-1, FR-3…"
              className="evolv-input text-xs px-2 py-1.5 w-40" />
          </div>
          <button
            onClick={addDeviation}
            className="px-4 py-1.5 text-xs rounded bg-blue-DEFAULT text-white
                       font-semibold hover:opacity-90 transition-opacity"
          >
            Log Deviation
          </button>
        </div>
      )}

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {deviations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full
                          text-text-muted gap-2">
            <span className="text-2xl opacity-30">✅</span>
            <p className="text-xs">No deviations logged.</p>
          </div>
        ) : (
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border-base">
                {['ID', 'Type', 'Title', 'Severity', 'Req', 'Status',
                  'Logged'].map(h => (
                  <th key={h}
                    className="text-left text-[10px] font-semibold
                               text-text-muted uppercase tracking-wide
                               py-2 pr-4 whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {deviations.map(d => {
                const sevCfg = SEVERITY_COLORS[d.severity]
                const stsCfg = STATUS_COLORS[d.status]
                return (
                  <tr key={d.id}
                    className="border-b border-border-base
                               hover:bg-bg-hover/30 transition-colors">
                    <td className="py-2.5 pr-4 font-mono text-text-muted
                                   text-[10px] whitespace-nowrap">
                      {d.id}
                    </td>
                    <td className="py-2.5 pr-4 text-text-muted text-[10px]
                                   whitespace-nowrap">
                      {d.type}
                    </td>
                    <td className="py-2.5 pr-4 text-text-secondary text-[11px]
                                   max-w-[180px]">
                      <span className="line-clamp-2">{d.title}</span>
                    </td>
                    <td className="py-2.5 pr-4">
                      <span className="text-[9px] font-semibold px-1.5 py-0.5
                                       rounded"
                        style={{ background: sevCfg.bg, color: sevCfg.text }}>
                        {d.severity}
                      </span>
                    </td>
                    <td className="py-2.5 pr-4 font-mono text-[10px]
                                   text-text-muted">
                      {d.affectedReq || '—'}
                    </td>
                    <td className="py-2.5 pr-4">
                      <select
                        value={d.status}
                        onChange={e => updateStatus(d.id, e.target.value)}
                        className="evolv-input evolv-select text-[10px] py-0.5
                                   px-1.5 h-6"
                        style={{ color: stsCfg.text }}
                      >
                        {STATUS_OPTIONS.map(s =>
                          <option key={s}>{s}</option>)}
                      </select>
                    </td>
                    <td className="py-2.5 font-mono text-[9px] text-text-muted
                                   whitespace-nowrap">
                      {new Date(d.loggedAt).toLocaleDateString()}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

// ── Tab: System Health ────────────────────────────────────────────
function SystemHealthTab() {
  const {
    phaseCompletion, planData, releaseData,
    testRuns, activeRunId, riskData,
  } = useAppStore()

  const run      = activeRunId ? testRuns[activeRunId] : null
  const riskRows = Object.values(riskData)

  const phases = [
    { id: 'plan',         label: 'Plan',         emoji: '📋' },
    { id: 'requirements', label: 'Requirements',  emoji: '📝' },
    { id: 'risk',         label: 'Risk',          emoji: '⚖️' },
    { id: 'design',       label: 'Design',        emoji: '🔒', locked: true },
    { id: 'verify',       label: 'Verify',        emoji: '🏭' },
    { id: 'release',      label: 'Release',       emoji: '📄' },
    { id: 'monitor',      label: 'Monitor',       emoji: '📡' },
    { id: 'retire',       label: 'Retire',        emoji: '🔒', locked: true },
  ]

  const metrics = [
    {
      label: 'Project',
      value: planData.projectName || 'Not set',
      sub:   planData.gampCategory
        ? `GAMP 5 Cat ${planData.gampCategory}`
        : 'Category not set',
      color: planData.projectName ? '#32CD32' : '#64748b',
    },
    {
      label: 'Phases Complete',
      value: `${Object.values(phaseCompletion).filter(Boolean).length} / 8`,
      sub:   'Lifecycle progress',
      color: '#007FFF',
    },
    {
      label: 'Test Status',
      value: run?.status === 'locked'
        ? 'Signed Off'
        : run ? 'In Progress' : 'Not Started',
      sub: run?.signerName ? `Signed by ${run.signerName}` : '',
      color: run?.status === 'locked' ? '#32CD32'
           : run ? '#f59e0b' : '#64748b',
    },
    {
      label: 'Approvals',
      value: `${releaseData.approvals.length} signed`,
      sub:   releaseData.released ? 'System Released ✓' : 'Pending release',
      color: releaseData.released ? '#32CD32'
           : releaseData.approvals.length > 0 ? '#f59e0b' : '#64748b',
    },
    {
      label: 'Requirements',
      value: `${riskRows.length} assessed`,
      sub:   `${riskRows.filter(r => r.impact && r.implMethod).length} fully profiled`,
      color: '#007FFF',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Metric cards */}
      <div className="grid grid-cols-3 gap-3">
        {metrics.map(m => (
          <div key={m.label}
            className="p-4 rounded-lg border border-border-base bg-bg-card">
            <p className="text-[10px] text-text-muted uppercase tracking-wide mb-1">
              {m.label}
            </p>
            <p className="text-lg font-bold" style={{ color: m.color }}>
              {m.value}
            </p>
            {m.sub && (
              <p className="text-[10px] text-text-muted mt-0.5">{m.sub}</p>
            )}
          </div>
        ))}
      </div>

      {/* Lifecycle phase grid */}
      <div>
        <h3 className="text-[10px] font-semibold text-text-muted uppercase
                       tracking-widest mb-3">
          Lifecycle Status
        </h3>
        <div className="grid grid-cols-4 gap-2">
          {phases.map(p => {
            const done   = !p.locked && phaseCompletion[p.id]
            const locked = p.locked
            return (
              <div key={p.id}
                className={`
                  p-3 rounded-lg border text-center transition-colors
                  ${locked
                    ? 'border-border-base bg-bg-base opacity-40'
                    : done
                      ? 'border-lime-DEFAULT/30 bg-lime-DEFAULT/5'
                      : 'border-border-base bg-bg-card'}
                `}>
                <div className="text-xl mb-1">{p.emoji}</div>
                <p className={`text-[10px] font-medium ${
                  locked ? 'text-text-muted'
                         : done ? 'text-lime-DEFAULT' : 'text-text-secondary'
                }`}>
                  {p.label}
                </p>
                <p className="text-[9px] mt-0.5" style={{
                  color: locked ? '#334155'
                       : done ? '#32CD32' : '#475569',
                }}>
                  {locked ? 'Locked' : done ? '✓ Complete' : '○ Pending'}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── Main Monitor page ─────────────────────────────────────────────
export default function Monitor() {
  const { setPhaseComplete } = useAppStore()
  const [activeTab, setActiveTab] = useState('health')

  // Mark monitor phase visited on first render
  useEffect(() => { setPhaseComplete('monitor') }, [setPhaseComplete])

  const tabs = [
    { id: 'health',    label: '📊 System Health' },
    { id: 'audit',     label: '🔍 Audit Trail'   },
    { id: 'deviations',label: '⚠️ Deviations'    },
  ]

  return (
    <div className="flex flex-col h-full bg-bg-base overflow-hidden">

      {/* ── Header strip ─────────────────────────────────── */}
      <div className="flex items-center gap-3 px-6 py-2.5
                      bg-blue-dim border-b border-blue-DEFAULT/20 shrink-0">
        <span className="text-xs font-semibold text-blue-DEFAULT">
          Monitor
        </span>
        <span className="text-text-muted text-xs">
          Operations &amp; Monitoring
        </span>
        <div className="ml-auto flex gap-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                px-3 py-1 text-[11px] rounded transition-colors
                ${activeTab === tab.id
                  ? 'bg-blue-DEFAULT/20 text-blue-DEFAULT'
                  : 'text-text-muted hover:text-text-secondary'}
              `}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Tab content ──────────────────────────────────── */}
      <div className="flex-1 overflow-hidden px-6 py-4 flex flex-col">
        {activeTab === 'health'     && <SystemHealthTab />}
        {activeTab === 'audit'      && <AuditTrailTab />}
        {activeTab === 'deviations' && <DeviationsTab />}
      </div>
    </div>
  )
}
