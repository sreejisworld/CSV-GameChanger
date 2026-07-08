/**
 * AuditTrail.jsx — Sprint 19 Audit Trail Inspection Viewer.
 *
 * A standalone app (Tools group, sidebar entry "Audit Trail") that
 * exposes the entire EVOLV audit_trail.csv to a reviewer with:
 *
 *   1. Sortable / filterable table over `output/audit_trail.csv`
 *      (free-text search, phase, agent, severity, action prefix,
 *      date-range, sort by column).
 *   2. Per-row drill-down drawer that fetches the matching
 *      logic-archive JSON from `/audit/archive/{hash}` and shows
 *      the full AI reasoning chain (inputs / steps / outputs).
 *   3. Lifecycle Timeline tab — visual phase breakdown built from
 *      `/audit/timeline` (custom SVG bars, no Mermaid runtime
 *      required; the API still returns Mermaid source for textual
 *      copy-paste).
 *   4. Filtered slice → signed PDF export (POST /audit/export-pdf)
 *      using the same downloadPDF helper as the VP/DS/VSR pack.
 *
 * Read-only: this app never writes to the audit trail.
 *
 * @requirement URS-2.1   - 21 CFR Part 11 audit trail.
 * @requirement URS-27.1  - JSON API for audit rows.
 * @requirement URS-27.2  - Logic-archive drill-down.
 * @requirement URS-27.3  - Lifecycle timeline.
 * @requirement URS-27.4  - Signed audit-export PDF.
 */
import { useEffect, useMemo, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '../store/useAppStore.js'
import { API_BASE } from '../config.js'
import { downloadPDF, slugify } from '../utils/downloadPDF.js'

// ── Visual config ─────────────────────────────────────────────────

const SEVERITY_TONE = {
  error:   { bg: 'rgba(239,68,68,0.12)',  text: '#ef4444', label: 'Error'   },
  warning: { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b', label: 'Warning' },
  success: { bg: 'rgba(50,205,50,0.12)',  text: '#32CD32', label: 'OK'      },
  info:    { bg: 'rgba(0,127,255,0.12)',  text: '#007FFF', label: 'Info'    },
}

const PHASE_TONE = {
  Plan:         { bg: 'rgba(0,127,255,0.12)',  text: '#007FFF' },
  Requirements: { bg: 'rgba(168,85,247,0.12)', text: '#a855f7' },
  Risk:         { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b' },
  Design:       { bg: 'rgba(168,85,247,0.12)', text: '#a855f7' },
  Verify:       { bg: 'rgba(50,205,50,0.12)',  text: '#32CD32' },
  Release:      { bg: 'rgba(50,205,50,0.18)',  text: '#32CD32' },
  Monitor:      { bg: 'rgba(0,127,255,0.12)',  text: '#007FFF' },
  Other:        { bg: 'rgba(100,116,139,0.12)', text: '#64748b' },
}

const PHASE_ORDER = [
  'Plan', 'Requirements', 'Risk', 'Design',
  'Verify', 'Release', 'Monitor', 'Other',
]

// ── Tiny presentational helpers ───────────────────────────────────

function Pill({ tone, children, title }) {
  return (
    <span
      className="text-[9px] font-semibold px-1.5 py-0.5 rounded
                 whitespace-nowrap uppercase tracking-wide"
      style={{ background: tone?.bg, color: tone?.text }}
      title={title}
    >
      {children}
    </span>
  )
}

function fmtTimestamp(iso) {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.valueOf())) return iso
    return d.toLocaleString()
  } catch {
    return iso
  }
}

// ── Lifecycle Timeline (custom SVG) ───────────────────────────────

function LifecycleTimeline({ rows }) {
  // Bucket counts by phase
  const counts = useMemo(() => {
    const out = {}
    for (const r of rows) {
      const ph = r.phase || 'Other'
      out[ph] = (out[ph] || 0) + 1
    }
    return out
  }, [rows])

  const max = Math.max(1, ...PHASE_ORDER.map(p => counts[p] || 0))

  // Last event per phase, for the “last touched” line
  const lastByPhase = useMemo(() => {
    const out = {}
    for (const r of rows) {
      const ph = r.phase || 'Other'
      if (!out[ph] || (r.timestamp || '') > out[ph].timestamp) {
        out[ph] = r
      }
    }
    return out
  }, [rows])

  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-text-primary">
          Lifecycle Audit Journey
        </h3>
        <span className="text-[10px] text-text-muted">
          {rows.length} event(s) bucketed by V-model phase
        </span>
      </div>
      <div className="space-y-1.5">
        {PHASE_ORDER.map(ph => {
          const cnt = counts[ph] || 0
          const pct = (cnt / max) * 100
          const tone = PHASE_TONE[ph] || PHASE_TONE.Other
          const last = lastByPhase[ph]
          return (
            <div
              key={ph}
              className="flex items-center gap-3 text-[11px]"
            >
              <div className="w-24 shrink-0 text-text-secondary
                              text-right pr-1 font-medium">
                {ph}
              </div>
              <div className="flex-1 h-6 rounded-md bg-bg-card/60
                              border border-border-base relative
                              overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 rounded-md
                             transition-all"
                  style={{
                    width:      `${pct}%`,
                    background: tone.bg,
                  }}
                />
                <div className="absolute inset-0 flex items-center
                                px-2 justify-between">
                  <span
                    className="text-[10px] font-semibold"
                    style={{ color: tone.text }}
                  >
                    {cnt} event{cnt === 1 ? '' : 's'}
                  </span>
                  {last && (
                    <span className="text-[9px] text-text-muted
                                     font-mono">
                      last: {fmtTimestamp(last.timestamp)}
                    </span>
                  )}
                </div>
              </div>
              <div className="w-10 shrink-0 text-right text-[10px]
                              text-text-muted font-mono">
                {cnt > 0 ? `${Math.round(pct)}%` : '—'}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Drill-down drawer ─────────────────────────────────────────────

function ArchiveDrawer({ row, onClose }) {
  const [archive, setArchive]   = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error,   setError]     = useState('')

  const hash = row?.reasoning_hash || ''

  useEffect(() => {
    if (!row) return
    if (!hash) {
      setError('This row has no Reasoning Hash.')
      setArchive(null)
      return
    }
    let cancelled = false
    setLoading(true); setError(''); setArchive(null)
    fetch(`${API_BASE}/audit/archive/${hash}`)
      .then(async res => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail ?? `HTTP ${res.status}`)
        }
        return res.json()
      })
      .then(data => { if (!cancelled) setArchive(data) })
      .catch(err  => {
        if (!cancelled) {
          setError(err.message || 'Could not load logic archive.')
        }
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [row, hash])

  if (!row) return null

  const phaseTone = PHASE_TONE[row.phase] || PHASE_TONE.Other
  const sevTone   = SEVERITY_TONE[row.severity] || SEVERITY_TONE.info

  return (
    <AnimatePresence>
      <motion.div
        key="backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{   opacity: 0 }}
        transition={{ duration: 0.18 }}
        className="absolute inset-0 z-30 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.aside
        key="drawer"
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{   x: '100%' }}
        transition={{ duration: 0.22, ease: 'easeOut' }}
        className="absolute top-0 right-0 bottom-0 w-[640px] z-40
                   bg-bg-base border-l border-border-base
                   shadow-[0_0_40px_rgba(0,0,0,0.35)]
                   flex flex-col"
      >
        {/* Header */}
        <div className="px-5 py-4 border-b border-border-base
                        flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <Pill tone={phaseTone}>{row.phase || 'Other'}</Pill>
              <Pill tone={sevTone}>{sevTone.label}</Pill>
            </div>
            <div className="text-sm font-semibold text-text-primary
                            truncate">
              {row.action || 'Untitled action'}
            </div>
            <div className="text-[10px] text-text-muted mt-0.5">
              {row.agent_name || 'Unknown agent'}
              {' · '}
              <span className="font-mono">
                {fmtTimestamp(row.timestamp)}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="px-2 py-1 text-text-muted hover:text-text-primary
                       text-lg leading-none"
            aria-label="Close drawer"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Row metadata */}
          <section>
            <h4 className="text-[10px] font-semibold uppercase
                           tracking-wide text-text-muted mb-2">
              Audit Row
            </h4>
            <dl className="grid grid-cols-[120px_1fr] gap-y-1.5
                           text-[11px]">
              <dt className="text-text-muted">User</dt>
              <dd className="text-text-secondary">
                {row.user_id || 'SYSTEM'}
              </dd>
              <dt className="text-text-muted">Compliance Impact</dt>
              <dd className="text-text-secondary">
                {row.compliance_impact || '—'}
              </dd>
              <dt className="text-text-muted">Reasoning Hash</dt>
              <dd className="text-text-secondary font-mono break-all">
                {row.reasoning_hash || '—'}
              </dd>
              <dt className="text-text-muted">Decision Logic</dt>
              <dd className="text-text-secondary whitespace-pre-wrap">
                {row.decision_logic || '—'}
              </dd>
            </dl>
          </section>

          {/* Logic archive */}
          <section>
            <h4 className="text-[10px] font-semibold uppercase
                           tracking-wide text-text-muted mb-2">
              Logic Archive (AI Reasoning Chain)
            </h4>
            {loading && (
              <div className="text-[11px] text-text-muted">
                Loading reasoning chain…
              </div>
            )}
            {error && !loading && (
              <div className="px-3 py-2 rounded border
                              border-amber-500/30 bg-amber-500/10
                              text-[11px] text-amber-400">
                No archive on disk for this row.
                <div className="mt-1 text-[10px] opacity-80">
                  ({error})
                </div>
                <div className="mt-1 text-[10px] opacity-70">
                  Older actions did not write logic archives;
                  this is expected for legacy rows.
                </div>
              </div>
            )}
            {archive && !loading && (
              <ArchiveBody archive={archive} />
            )}
          </section>
        </div>
      </motion.aside>
    </AnimatePresence>
  )
}

function ArchiveBody({ archive }) {
  const file    = archive.archive_filename || '—'
  const payload = archive.archive || {}
  const inputs  = payload.inputs  || {}
  const steps   = Array.isArray(payload.steps)  ? payload.steps  : []
  const outputs = payload.outputs || {}
  const integ   = payload.integrity || {}

  return (
    <div className="space-y-3 text-[11px]">
      <div className="px-2.5 py-1.5 rounded bg-bg-card border
                      border-border-base text-text-muted font-mono
                      text-[10px] break-all">
        {file}
      </div>

      <details open>
        <summary className="cursor-pointer text-text-secondary
                            font-semibold uppercase text-[10px]
                            tracking-wide">
          Inputs
        </summary>
        <pre className="mt-1.5 p-2.5 rounded bg-bg-card border
                        border-border-base text-[10px] text-text-secondary
                        overflow-x-auto whitespace-pre-wrap break-words">
{JSON.stringify(inputs, null, 2)}
        </pre>
      </details>

      <details open>
        <summary className="cursor-pointer text-text-secondary
                            font-semibold uppercase text-[10px]
                            tracking-wide">
          Reasoning Steps ({steps.length})
        </summary>
        <ol className="mt-1.5 space-y-1 list-decimal list-inside
                       text-text-secondary">
          {steps.length === 0 && (
            <li className="text-text-muted italic">
              No steps recorded.
            </li>
          )}
          {steps.map((s, i) => (
            <li key={i} className="leading-snug">
              {typeof s === 'string'
                ? s
                : <code className="text-[10px]">
                    {JSON.stringify(s)}
                  </code>}
            </li>
          ))}
        </ol>
      </details>

      <details open>
        <summary className="cursor-pointer text-text-secondary
                            font-semibold uppercase text-[10px]
                            tracking-wide">
          Outputs
        </summary>
        <pre className="mt-1.5 p-2.5 rounded bg-bg-card border
                        border-border-base text-[10px] text-text-secondary
                        overflow-x-auto whitespace-pre-wrap break-words">
{JSON.stringify(outputs, null, 2)}
        </pre>
      </details>

      {integ?.archive_hash && (
        <div className="px-2.5 py-1.5 rounded border
                        border-green-500/30 bg-green-500/10
                        text-[10px] text-green-400">
          ✓ Archive integrity hash:&nbsp;
          <span className="font-mono break-all">
            {integ.archive_hash}
          </span>
        </div>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────

export default function AuditTrail() {
  const projectName = useAppStore(s => s.planData.projectName)

  const [rows,        setRows]        = useState([])
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState('')
  const [autoRefresh, setAutoRefresh] = useState(false)

  // Filters
  const [search,    setSearch]    = useState('')
  const [phase,     setPhase]     = useState('')      // '' = all
  const [agent,     setAgent]     = useState('')      // '' = all
  const [severity,  setSeverity]  = useState('')      // '' = all
  const [actionPfx, setActionPfx] = useState('')
  const [since,     setSince]     = useState('')
  const [until,     setUntil]     = useState('')

  // Sort: column key + direction
  const [sortKey, setSortKey] = useState('timestamp')
  const [sortDir, setSortDir] = useState('desc')

  // Tabs: 'table' or 'timeline'
  const [tab, setTab] = useState('table')

  // Drill-down
  const [selected, setSelected] = useState(null)

  // PDF export state
  const [exporter, setExporter] = useState({
    open: false, signer: '', loading: false, error: '',
  })

  // ─── Load rows ──────────────────────────────────────────────
  const load = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const res = await fetch(`${API_BASE}/audit/all`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setRows(Array.isArray(data) ? data : [])
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

  // ─── Derived: distinct agents, applied filtering ────────────
  const agents = useMemo(() => {
    const set = new Set(rows.map(r => r.agent_name).filter(Boolean))
    return Array.from(set).sort()
  }, [rows])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    let out = rows.filter(r => {
      if (phase    && r.phase    !== phase)             return false
      if (agent    && r.agent_name !== agent)           return false
      if (severity && r.severity !== severity)          return false
      if (actionPfx && !(r.action || '')
          .toLowerCase().startsWith(actionPfx.toLowerCase()))
        return false
      if (since && (r.timestamp || '') < since)         return false
      if (until && (r.timestamp || '') > until + 'T23:59:59Z')
        return false
      if (q) {
        const blob = [
          r.timestamp, r.user_id, r.agent_name, r.action,
          r.decision_logic, r.compliance_impact,
          r.reasoning_hash,
        ].join(' ').toLowerCase()
        if (!blob.includes(q)) return false
      }
      return true
    })
    // Sort
    out = [...out].sort((a, b) => {
      const av = String(a[sortKey] ?? '')
      const bv = String(b[sortKey] ?? '')
      if (av === bv) return 0
      const cmp = av < bv ? -1 : 1
      return sortDir === 'asc' ? cmp : -cmp
    })
    return out
  }, [
    rows, search, phase, agent, severity, actionPfx,
    since, until, sortKey, sortDir,
  ])

  const filterSummary = useMemo(() => {
    const parts = []
    if (phase)     parts.push(`Phase=${phase}`)
    if (agent)     parts.push(`Agent=${agent}`)
    if (severity)  parts.push(`Severity=${severity}`)
    if (actionPfx) parts.push(`Action prefix="${actionPfx}"`)
    if (since)     parts.push(`Since=${since}`)
    if (until)     parts.push(`Until=${until}`)
    if (search)    parts.push(`Search="${search}"`)
    return parts.length === 0
      ? 'No filters applied (full audit trail).'
      : parts.join('  |  ')
  }, [phase, agent, severity, actionPfx, since, until, search])

  const handleSort = useCallback(key => {
    setSortKey(prev => {
      if (prev === key) {
        setSortDir(d => d === 'asc' ? 'desc' : 'asc')
        return prev
      }
      setSortDir('desc')
      return key
    })
  }, [])

  const clearFilters = useCallback(() => {
    setSearch(''); setPhase(''); setAgent(''); setSeverity('')
    setActionPfx(''); setSince(''); setUntil('')
  }, [])

  const handleExportPdf = useCallback(async () => {
    if (!exporter.signer.trim()) {
      setExporter(x => ({
        ...x,
        error: 'Please enter a signer name before exporting.',
      }))
      return
    }
    setExporter(x => ({ ...x, loading: true, error: '' }))
    try {
      const proj = projectName || 'Untitled Project'
      await downloadPDF(
        `${API_BASE}/audit/export-pdf`,
        {
          rows:           filtered,
          project_name:   proj,
          signer_name:    exporter.signer.trim(),
          meaning:        'Audit Trail Inspection Export',
          filter_summary: filterSummary,
        },
        `audit-trail-${slugify(proj)}.pdf`,
      )
      setExporter(x => ({ ...x, loading: false, open: false }))
    } catch (err) {
      setExporter(x => ({
        ...x,
        loading: false,
        error: err.message || 'PDF export failed.',
      }))
    }
  }, [exporter.signer, filtered, filterSummary, projectName])

  // ─── Render ────────────────────────────────────────────────
  return (
    <div className="relative flex flex-col h-full
                    bg-bg-base text-text-primary">
      {/* Header */}
      <div className="px-6 pt-5 pb-3 border-b border-border-base
                      shrink-0">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-text-primary">
              Audit Trail Inspection
            </h1>
            <p className="text-[11px] text-text-muted mt-0.5">
              Read-only viewer over <code>output/audit_trail.csv</code>
              {' · '}
              {rows.length} total event(s)
              {filtered.length !== rows.length && (
                <> · {filtered.length} after filters</>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={load}
              disabled={loading}
              className="px-3 py-1.5 text-xs rounded
                         border border-border-base
                         text-text-muted hover:text-text-secondary
                         hover:border-border-bright transition-colors"
            >
              {loading ? 'Loading…' : '↻ Refresh'}
            </button>
            <label className="flex items-center gap-1.5 text-[11px]
                              text-text-muted cursor-pointer
                              select-none px-2 py-1 rounded
                              border border-border-base">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={e => setAutoRefresh(e.target.checked)}
                className="w-3 h-3"
              />
              Auto-refresh (5s)
            </label>
            <button
              onClick={() => setExporter(x => ({
                ...x, open: true, error: '',
              }))}
              disabled={filtered.length === 0}
              className="px-3 py-1.5 text-xs rounded font-semibold
                         text-white bg-blue-DEFAULT hover:bg-blue-bright
                         disabled:opacity-40 disabled:cursor-not-allowed
                         transition-colors"
              title={filtered.length === 0
                ? 'No rows in current filter to export'
                : 'Export the current filtered slice as a signed PDF'}
            >
              📑 Export Signed PDF
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-[1fr_140px_140px_120px_140px_120px_120px_auto]
                        gap-2 mt-4 items-center">
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search any column…"
            className="evolv-input text-xs px-2 py-1.5"
          />
          <select
            value={phase}
            onChange={e => setPhase(e.target.value)}
            className="evolv-input text-xs px-2 py-1.5"
          >
            <option value="">All phases</option>
            {PHASE_ORDER.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <select
            value={agent}
            onChange={e => setAgent(e.target.value)}
            className="evolv-input text-xs px-2 py-1.5"
          >
            <option value="">All agents</option>
            {agents.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          <select
            value={severity}
            onChange={e => setSeverity(e.target.value)}
            className="evolv-input text-xs px-2 py-1.5"
          >
            <option value="">All severities</option>
            <option value="error">Error</option>
            <option value="warning">Warning</option>
            <option value="success">OK</option>
            <option value="info">Info</option>
          </select>
          <input
            value={actionPfx}
            onChange={e => setActionPfx(e.target.value)}
            placeholder="Action prefix…"
            className="evolv-input text-xs px-2 py-1.5"
          />
          <input
            type="date"
            value={since}
            onChange={e => setSince(e.target.value)}
            className="evolv-input text-xs px-2 py-1.5"
            title="Since"
          />
          <input
            type="date"
            value={until}
            onChange={e => setUntil(e.target.value)}
            className="evolv-input text-xs px-2 py-1.5"
            title="Until"
          />
          <button
            onClick={clearFilters}
            className="px-2 py-1.5 text-[11px] rounded
                       border border-border-base text-text-muted
                       hover:text-text-secondary
                       hover:border-border-bright transition-colors"
            title="Clear all filters"
          >
            ✕ Clear
          </button>
        </div>

        {/* Tabs */}
        <div className="mt-4 flex items-center gap-1
                        border-b border-border-base">
          {[
            { id: 'table',    label: 'Records'   },
            { id: 'timeline', label: 'Lifecycle Timeline' },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-3 py-1.5 text-[11px] font-semibold
                          border-b-2 -mb-px transition-colors ${
                tab === t.id
                  ? 'border-blue-DEFAULT text-blue-DEFAULT'
                  : 'border-transparent text-text-muted ' +
                    'hover:text-text-secondary'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-hidden relative">
        {error && (
          <div className="m-6 mb-0 px-4 py-2 rounded
                          border border-red-500/30 bg-red-500/10
                          text-[11px] text-red-400">
            {error}
          </div>
        )}

        {tab === 'table' && (
          <RecordsTable
            rows={filtered}
            loading={loading}
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={handleSort}
            onSelect={setSelected}
          />
        )}

        {tab === 'timeline' && (
          <div className="p-6 overflow-y-auto h-full">
            <LifecycleTimeline rows={filtered} />
          </div>
        )}

        {/* Drill-down drawer */}
        {selected && (
          <ArchiveDrawer
            row={selected}
            onClose={() => setSelected(null)}
          />
        )}

        {/* Export modal */}
        {exporter.open && (
          <ExportModal
            state={exporter}
            count={filtered.length}
            filterSummary={filterSummary}
            projectName={projectName}
            onChange={patch => setExporter(x => ({ ...x, ...patch }))}
            onCancel={() => setExporter(x => ({ ...x, open: false }))}
            onSubmit={handleExportPdf}
          />
        )}
      </div>
    </div>
  )
}

// ── Records table (sortable) ──────────────────────────────────────

function RecordsTable({
  rows, loading, sortKey, sortDir, onSort, onSelect,
}) {
  const cols = [
    { key: 'timestamp',         label: 'Timestamp' },
    { key: 'phase',             label: 'Phase'     },
    { key: 'agent_name',        label: 'Agent'     },
    { key: 'action',            label: 'Action'    },
    { key: 'compliance_impact', label: 'Impact'    },
    { key: 'reasoning_hash',    label: 'Hash'      },
  ]

  if (rows.length === 0 && !loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full
                      text-text-muted gap-2 p-10">
        <span className="text-3xl opacity-30">📋</span>
        <p className="text-xs">No audit records match the active filter.</p>
        <p className="text-[10px]">
          Clear filters or run through the lifecycle to generate events.
        </p>
      </div>
    )
  }

  return (
    <div className="overflow-auto h-full">
      <table className="w-full text-xs border-collapse">
        <thead className="sticky top-0 bg-bg-base z-10">
          <tr className="border-b border-border-base">
            {cols.map(c => (
              <th
                key={c.key}
                onClick={() => onSort(c.key)}
                className="text-left text-[10px] font-semibold
                           text-text-muted uppercase tracking-wide
                           py-2 px-4 whitespace-nowrap cursor-pointer
                           hover:text-text-secondary select-none"
              >
                {c.label}
                {sortKey === c.key && (
                  <span className="ml-1 text-blue-DEFAULT">
                    {sortDir === 'asc' ? '▲' : '▼'}
                  </span>
                )}
              </th>
            ))}
            <th className="text-left text-[10px] font-semibold
                           text-text-muted uppercase tracking-wide
                           py-2 px-4 whitespace-nowrap">
              Decision Logic
            </th>
            <th className="text-right text-[10px] font-semibold
                           text-text-muted uppercase tracking-wide
                           py-2 px-4 whitespace-nowrap">
              Drill
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const phaseTone = PHASE_TONE[row.phase] || PHASE_TONE.Other
            const sevTone   = SEVERITY_TONE[row.severity]
                            || SEVERITY_TONE.info
            return (
              <tr
                key={`${row.reasoning_hash}-${i}`}
                onClick={() => onSelect(row)}
                className="border-b border-border-base
                           hover:bg-bg-hover/40 transition-colors
                           cursor-pointer"
              >
                <td className="py-2 px-4 font-mono text-[10px]
                               text-text-muted whitespace-nowrap">
                  {fmtTimestamp(row.timestamp)}
                </td>
                <td className="py-2 px-4">
                  <Pill tone={phaseTone}>
                    {row.phase || 'Other'}
                  </Pill>
                </td>
                <td className="py-2 px-4 text-text-secondary
                               text-[11px] whitespace-nowrap">
                  {row.agent_name || '—'}
                </td>
                <td className="py-2 px-4 text-[11px]
                               whitespace-nowrap">
                  <span className="font-medium text-text-primary">
                    {row.action || '—'}
                  </span>
                  <span className="ml-2">
                    <Pill tone={sevTone}>
                      {sevTone.label}
                    </Pill>
                  </span>
                </td>
                <td className="py-2 px-4 text-text-muted
                               text-[10px] whitespace-nowrap">
                  {row.compliance_impact || '—'}
                </td>
                <td className="py-2 px-4 font-mono text-[9px]
                               text-text-muted">
                  <span title={row.reasoning_hash}>
                    {row.reasoning_hash
                      ? row.reasoning_hash.slice(0, 12) + '…'
                      : '—'}
                  </span>
                </td>
                <td className="py-2 px-4 text-text-muted text-[11px]
                               max-w-[360px]">
                  <span className="line-clamp-2">
                    {row.decision_logic || '—'}
                  </span>
                </td>
                <td className="py-2 px-4 text-right">
                  <span className="text-blue-DEFAULT text-[11px]
                                   font-semibold">
                    →
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ── Export modal ─────────────────────────────────────────────────

function ExportModal({
  state, count, filterSummary, projectName,
  onChange, onCancel, onSubmit,
}) {
  return (
    <div
      className="absolute inset-0 z-30 flex items-center justify-center
                 bg-black/40 backdrop-blur-sm"
      onClick={onCancel}
    >
      <div
        className="w-[480px] max-w-full bg-bg-card border
                   border-border-base rounded-xl
                   shadow-[0_8px_40px_rgba(0,0,0,0.4)] p-5 space-y-4"
        onClick={e => e.stopPropagation()}
      >
        <div>
          <h3 className="text-base font-semibold text-text-primary">
            Export Filtered Audit Trail
          </h3>
          <p className="text-[11px] text-text-muted mt-0.5">
            Generates a signed PDF with cover page, full row table,
            and Manifestation of Signature
            (21 CFR Part 11 §11.50).
          </p>
        </div>

        <div className="text-[11px] text-text-secondary
                        bg-bg-base px-3 py-2 rounded
                        border border-border-base space-y-1">
          <div>
            <span className="text-text-muted">Project:</span>{' '}
            <span className="font-semibold">
              {projectName || 'Untitled Project'}
            </span>
          </div>
          <div>
            <span className="text-text-muted">Rows to include:</span>{' '}
            <span className="font-semibold">{count}</span>
          </div>
          <div>
            <span className="text-text-muted">Filters:</span>{' '}
            <span className="font-mono text-[10px]">
              {filterSummary}
            </span>
          </div>
        </div>

        <label className="block text-[11px] text-text-secondary">
          Inspector / Signer Name
          <input
            value={state.signer}
            onChange={e => onChange({ signer: e.target.value })}
            placeholder="e.g. Jane Smith, QA Director"
            className="evolv-input mt-1 w-full text-xs px-2 py-1.5"
          />
        </label>

        {state.error && (
          <div className="px-3 py-2 rounded border
                          border-red-500/30 bg-red-500/10
                          text-[11px] text-red-400">
            {state.error}
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-1">
          <button
            onClick={onCancel}
            className="px-3 py-1.5 text-xs rounded
                       border border-border-base text-text-muted
                       hover:text-text-secondary transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onSubmit}
            disabled={state.loading}
            className="px-3 py-1.5 text-xs rounded font-semibold
                       text-white bg-blue-DEFAULT
                       hover:bg-blue-bright
                       disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors"
          >
            {state.loading ? 'Generating…' : '📑 Download PDF'}
          </button>
        </div>
      </div>
    </div>
  )
}
