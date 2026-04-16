/**
 * Monitor — Lifecycle Phase 7: Operations & Monitoring
 *
 * React-native page with three tabs:
 *  - Audit Trail  : live viewer for output/audit_trail.csv
 *  - Deviations   : log and track deviations / CAPAs
 *  - System Health: project lifecycle status dashboard
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '../store/useAppStore.js'
import { SYSTEMS, AI_MODELS } from '../data/systems.js'
import { API_BASE } from '../config.js'

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

const API = API_BASE

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

// ── Tab: AI Models ────────────────────────────────────────────────

const AI_SCENARIOS = [
  {
    label: 'Architecture Upgrade', icon: '🏗️', color: '#ef4444',
    model: 'Drug Interaction Predictor',
    change_type: 'architecture_change',
    description: 'Upgrade from PyTorch 1.13 → PyTorch 2.1 with new attention layers',
    new_version: 'v2.2-rc1',
  },
  {
    label: 'New Training Data', icon: '📊', color: '#f59e0b',
    model: 'QC Defect Classifier',
    change_type: 'new_training_data',
    description: 'Retrained on 50,000 additional defect images from Frankfurt line',
    new_version: 'v1.4-rc1',
  },
  {
    label: 'Drift Correction', icon: '📉', color: '#007FFF',
    model: 'Drug Interaction Predictor',
    change_type: 'drift_correction',
    description: 'Minor weight recalibration — performance drift detected in monitoring',
    new_version: 'v2.1.1',
  },
  {
    label: 'Non-GxP Update', icon: '🔧', color: '#32CD32',
    model: 'Demand Forecasting Model',
    change_type: 'hyperparameter_tuning',
    description: 'Seasonal adjustment — updated learning rate for Q2 forecasting',
    new_version: 'v4.1',
  },
]

const AI_CHANGE_PROFILES = {
  architecture_change: {
    label: 'Architecture Change',
    risk_level: 'High',
    pccp_category: 'Locked Change — Full Revalidation Required',
    rationale: 'Architecture changes alter model decision boundaries fundamentally. Per FDA PCCP Guidance (Aug 2025), modifications outside the authorized Description of Modifications require a new marketing submission and full revalidation cycle.',
    required_evidence: [
      'IQ — Environment qualification (new framework version)',
      'OQ — Functional regression testing across all decision paths',
      'UAT — Clinical acceptance testing with domain experts',
      'Performance benchmarking vs. previous version (pre-defined acceptance criteria)',
      'Bias & fairness assessment on holdout dataset',
    ],
    governance_required: true,
    fda_ref: 'FDA PCCP Guidance Aug 18, 2025 — §V, §VI.C (21 U.S.C. 360e-4)',
  },
  new_training_data: {
    label: 'New Training Data',
    risk_level: 'Medium',
    pccp_category: 'Adaptive Change — Abbreviated Testing',
    rationale: 'New training data may shift model decision boundaries. Per FDA PCCP Guidance (Aug 2025), the Modification Protocol must include pre-defined acceptance criteria for re-training. If criteria are not met, the modification must not be implemented and the failure must be recorded.',
    required_evidence: [
      'Training data validation report (source, completeness, bias check)',
      'Tuning data evaluation report (independent from training set)',
      'Performance benchmarking — accuracy, AUC, precision/recall vs. pre-defined thresholds',
      'Bias & fairness delta report',
      'Data lineage audit record (21 CFR Part 820 QMSR / ISO 13485:2016 §4.2.5)',
    ],
    governance_required: true,
    fda_ref: 'FDA PCCP Guidance Aug 18, 2025 — §VII.B(2)(3) Re-training & Performance Evaluation',
  },
  drift_correction: {
    label: 'Drift Correction',
    risk_level: 'Low',
    pccp_category: 'Pre-Approved Change — Monitoring Evidence Sufficient',
    rationale: 'Minor recalibration within PCCP-authorized bounds. Per FDA PCCP Guidance (Aug 2025), modifications specified in and implemented per an authorized PCCP do not require a new marketing submission. Post-market monitoring evidence is sufficient if delta is within pre-specified thresholds.',
    required_evidence: [
      'Performance monitoring report (pre/post comparison)',
      'Drift analysis log with threshold confirmation',
      'Post-market surveillance record (21 CFR Part 820 QMSR / ISO 13485:2016 §8.2.1)',
      'Audit record of change (21 CFR Part 820 QMSR / ISO 13485:2016 §4.2.5)',
    ],
    governance_required: false,
    fda_ref: 'FDA PCCP Guidance Aug 18, 2025 — §V (Authorized PCCP), §VII.B(4) Post-Market Monitoring',
  },
  hyperparameter_tuning: {
    label: 'Hyperparameter Tuning',
    risk_level: 'Low',
    pccp_category: 'Non-GxP — Standard IT Change Management',
    rationale: 'Non-GxP system. No regulatory validation required. Standard IT change management and performance verification apply.',
    required_evidence: [
      'Unit tests passing',
      'Performance comparison report (MAPE, RMSE)',
    ],
    governance_required: false,
    fda_ref: 'N/A — Non-GxP system',
  },
}

const AI_RISK_COLORS = { High: '#ef4444', Medium: '#f59e0b', Low: '#32CD32' }
const AI_RISK_BG     = {
  High: 'rgba(239,68,68,0.12)', Medium: 'rgba(245,158,11,0.12)',
  Low: 'rgba(50,205,50,0.12)',
}

function ModelCard({ model }) {
  const m = model.modelMeta
  const gxpCol = model.gxpStatus === 'GxP Direct'   ? '#ef4444'
               : model.gxpStatus === 'GxP Indirect' ? '#f59e0b' : '#6b7280'
  return (
    <div className="glass rounded-xl p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-white text-[11px] font-semibold">{model.name}</p>
          <p className="text-text-muted text-[9px] font-mono mt-0.5">
            {m.version} · {m.framework}
          </p>
        </div>
        <span className="text-[9px] px-1.5 py-0.5 rounded font-medium"
          style={{ color: gxpCol, backgroundColor: gxpCol+'18',
                   border: `1px solid ${gxpCol}30` }}>
          {model.gxpStatus}
        </span>
      </div>
      <div className="space-y-1">
        {Object.entries(m.performance).map(([k, v]) => (
          <div key={k} className="flex justify-between text-[9px]">
            <span className="text-text-muted capitalize">{k}</span>
            <span className="font-mono text-text-secondary">
              {typeof v === 'number' && v < 1 ? (v * 100).toFixed(1) + '%' : v}
            </span>
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <span
          className={`text-[9px] px-1.5 py-0.5 rounded font-medium ${
            m.pccpApproved
              ? 'text-lime-DEFAULT bg-lime-DEFAULT/10 border border-lime-DEFAULT/30'
              : 'text-amber-400 bg-amber-400/10 border border-amber-400/30'
          }`}
        >
          {m.pccpApproved ? '✓ PCCP Approved' : '⚠ PCCP Pending'}
        </span>
        <span className="text-[9px] text-text-muted truncate">{model.site}</span>
      </div>
      {m.validationRef && (
        <p className="text-[9px] font-mono text-text-muted/60">{m.validationRef}</p>
      )}
    </div>
  )
}

function AIModelsTab({ openTab }) {
  const addAIGovernanceItem   = useAppStore(s => s.addAIGovernanceItem)
  const setStatusBadge        = useAppStore(s => s.setStatusBadge)

  const [form, setForm] = useState({
    model: '', change_type: 'architecture_change',
    description: '', new_version: '',
  })
  const [loading,    setLoading]    = useState(false)
  const [result,     setResult]     = useState(null)
  const [auditFeed,  setAuditFeed]  = useState([])
  const [activeScen, setActiveScen] = useState(null)
  const [sentToGov,  setSentToGov]  = useState(false)

  const selectedModel = AI_MODELS.find(m => m.name === form.model) ?? null

  const applyScenario = useCallback(scen => {
    setActiveScen(scen.label)
    setResult(null)
    setAuditFeed([])
    setSentToGov(false)
    setForm({
      model: scen.model, change_type: scen.change_type,
      description: scen.description, new_version: scen.new_version,
    })
  }, [])

  const assess = useCallback(() => {
    if (!form.model || !form.description) return
    setLoading(true)
    setResult(null)
    setAuditFeed([])
    setSentToGov(false)

    setTimeout(() => {
      const profile = AI_CHANGE_PROFILES[form.change_type]
        ?? AI_CHANGE_PROFILES.drift_correction
      const t0 = new Date().toISOString()
      const hash = btoa(`${form.model}:${form.change_type}:${form.new_version}`)
        .slice(0, 16).replace(/[+/=]/g, 'x')

      setResult({ profile, model: selectedModel, form: { ...form }, hash, t0 })
      setAuditFeed([
        {
          event: 'MODEL_CHANGE_RECEIVED', time: t0,
          detail: `${form.model} — ${profile.label} (${form.new_version})`,
          color: '#007FFF',
        },
        {
          event: 'PCCP_ASSESSMENT_COMPLETED', time: new Date().toISOString(),
          detail: `Risk: ${profile.risk_level} | Category: ${profile.pccp_category}`,
          color: profile.risk_level === 'High' ? '#ef4444'
               : profile.risk_level === 'Medium' ? '#f59e0b' : '#32CD32',
        },
      ])
      setLoading(false)
    }, 800)
  }, [form, selectedModel])

  const sendToGovernance = useCallback(() => {
    if (!result) return
    const item = {
      id: `AI-GOV-${Date.now()}`,
      type: 'AI_MODEL_CHANGE',
      status: 'pending',
      created_at: new Date().toISOString(),
      model_name: result.form.model,
      change_type: result.profile.label,
      new_version: result.form.new_version,
      risk_level: result.profile.risk_level,
      pccp_category: result.profile.pccp_category,
      description: result.form.description,
      required_evidence: result.profile.required_evidence,
      fda_ref: result.profile.fda_ref,
      reasoning_hash: result.hash,
    }
    addAIGovernanceItem(item)
    setStatusBadge('governance', { type: 'warning', label: 'Review needed' })
    setSentToGov(true)
    setAuditFeed(prev => [...prev, {
      event: 'SENT_TO_GOVERNANCE_HUB', time: new Date().toISOString(),
      detail: `Awaiting HITL review — ${result.profile.risk_level} risk change`,
      color: '#a78bfa',
    }])
  }, [result, addAIGovernanceItem, setStatusBadge])

  const rl    = result?.profile?.risk_level
  const rCol  = AI_RISK_COLORS[rl] ?? '#888'
  const rBg   = AI_RISK_BG[rl]    ?? 'rgba(128,128,128,0.1)'

  return (
    <div className="space-y-5 overflow-y-auto h-full pr-1">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-white font-semibold text-sm flex items-center gap-2 mb-1">
            🤖 AI Model Change Control
            <span className="text-[9px] px-1.5 py-0.5 rounded border font-medium"
              style={{ color:'#a78bfa', borderColor:'rgba(167,139,250,0.3)',
                       backgroundColor:'rgba(167,139,250,0.1)' }}>
              FDA PCCP Guidance Aug 2025
            </span>
          </h2>
          <p className="text-text-secondary text-xs">
            Validated AI models are GAMP Cat 5 assets. Every change is assessed
            against the Predetermined Change Control Plan (PCCP) and routed for
            HITL approval when required.
          </p>
        </div>
      </div>

      {/* Model registry */}
      <div>
        <p className="text-text-muted text-[10px] mb-2 uppercase tracking-wider">
          Validated model registry
        </p>
        <div className="grid grid-cols-3 gap-3">
          {AI_MODELS.map(m => <ModelCard key={m.id} model={m} />)}
        </div>
      </div>

      {/* Scenario presets */}
      <div>
        <p className="text-text-muted text-[10px] mb-2 uppercase tracking-wider">
          Quick-fire scenarios
        </p>
        <div className="grid grid-cols-4 gap-2">
          {AI_SCENARIOS.map(s => (
            <button key={s.label} onClick={() => applyScenario(s)}
              className={`p-3 rounded-xl border text-left transition-all
                ${activeScen === s.label
                  ? 'bg-bg-hover' : 'hover:bg-bg-hover border-border-base'}`}
              style={activeScen === s.label
                ? { borderColor: s.color+'60', boxShadow: `0 0 16px ${s.color}22` } : {}}
            >
              <div className="text-xl mb-1.5">{s.icon}</div>
              <p className="text-white text-[11px] font-semibold leading-tight">
                {s.label}
              </p>
              <p className="text-text-muted text-[9px] mt-0.5">{s.model}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Form + result */}
      <div className="grid grid-cols-2 gap-5">

        {/* Left: change form */}
        <div className="glass rounded-xl p-5 space-y-4">
          <p className="text-text-muted text-[10px] uppercase tracking-wider">
            Model Change Request
          </p>

          <div>
            <label className="text-[10px] text-text-muted block mb-1">
              Model
            </label>
            <select value={form.model}
              onChange={e => setForm(f => ({ ...f, model: e.target.value }))}
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors"
            >
              <option value="">— Select a model —</option>
              {AI_MODELS.map(m => (
                <option key={m.id} value={m.name}>
                  {m.name} ({m.modelMeta.version} · {m.gxpStatus})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[10px] text-text-muted block mb-1">
              Change Type
            </label>
            <div className="grid grid-cols-2 gap-1.5">
              {Object.entries(AI_CHANGE_PROFILES).map(([k, v]) => (
                <button key={k}
                  onClick={() => setForm(f => ({ ...f, change_type: k }))}
                  className={`py-2 px-2 rounded-lg text-[9px] font-medium border
                    transition-all text-left
                    ${form.change_type === k
                      ? 'border-blue-DEFAULT bg-blue-dim text-blue-DEFAULT'
                      : 'border-border-base text-text-muted hover:text-text-secondary'}`}
                >
                  {v.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-text-muted block mb-1">
                New Version
              </label>
              <input value={form.new_version}
                onChange={e => setForm(f => ({ ...f, new_version: e.target.value }))}
                placeholder="e.g. v2.2-rc1"
                className="w-full bg-bg-base border border-border-base rounded-lg
                           px-3 py-2 text-xs font-mono text-text-primary outline-none
                           focus:border-border-blue transition-colors"
              />
            </div>
            <div className="flex flex-col justify-end">
              {selectedModel && (
                <p className="text-[9px] text-text-muted">
                  Current: <span className="font-mono text-text-secondary">
                    {selectedModel.modelMeta.version}
                  </span>
                </p>
              )}
            </div>
          </div>

          <div>
            <label className="text-[10px] text-text-muted block mb-1">
              Description
            </label>
            <textarea value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              rows={3} placeholder="Describe the model change…"
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors resize-none"
            />
          </div>

          <button onClick={assess}
            disabled={loading || !form.model || !form.description}
            className="w-full flex items-center justify-center gap-2
                       px-4 py-3 rounded-xl text-sm font-bold
                       bg-blue-DEFAULT text-white hover:brightness-110
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all shadow-[0_0_24px_rgba(0,127,255,0.35)]"
          >
            {loading
              ? <><span className="animate-spin">⏳</span> Assessing PCCP…</>
              : '⚡ Assess Change'}
          </button>
        </div>

        {/* Right: result + audit */}
        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div key="result"
                initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }}
                exit={{ opacity:0, y:-8 }} transition={{ duration:0.22 }}
                className="glass rounded-xl p-5 space-y-4"
              >
                {/* Risk badge */}
                <div className="rounded-xl p-4 flex flex-col items-center gap-1"
                  style={{ backgroundColor: rBg, border: `1px solid ${rCol}40` }}>
                  <p className="text-[10px] text-text-muted uppercase tracking-widest">
                    PCCP Risk Level
                  </p>
                  <p className="text-4xl font-black tracking-wider"
                    style={{ color: rCol, textShadow: `0 0 24px ${rCol}88` }}>
                    {rl?.toUpperCase()}
                  </p>
                  <p className="text-[10px] text-center font-mono mt-1"
                    style={{ color: rCol+'cc' }}>
                    {result.profile.pccp_category}
                  </p>
                </div>

                {/* Rationale */}
                <div className="rounded-lg bg-bg-hover p-3">
                  <p className="text-[9px] text-text-muted uppercase tracking-wider mb-1">
                    FDA Regulatory Basis
                  </p>
                  <p className="text-[10px] text-text-secondary leading-relaxed">
                    {result.profile.rationale}
                  </p>
                  <p className="text-[9px] text-blue-DEFAULT/70 mt-2 italic">
                    {result.profile.fda_ref}
                  </p>
                </div>

                {/* Required evidence checklist */}
                <div>
                  <p className="text-[9px] text-text-muted uppercase tracking-wider mb-2">
                    Required Evidence
                  </p>
                  <div className="space-y-1">
                    {result.profile.required_evidence.map((ev, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className="text-[10px] mt-0.5"
                          style={{ color: rCol }}>☐</span>
                        <p className="text-[10px] text-text-secondary">{ev}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Send to Governance / monitoring note */}
                {result.profile.governance_required ? (
                  sentToGov ? (
                    <div className="rounded-xl p-3 flex items-center gap-3
                                    bg-purple-500/10 border border-purple-500/30">
                      <span className="text-base">✓</span>
                      <div>
                        <p className="text-[11px] text-purple-300 font-semibold">
                          Sent to AI Governance Hub
                        </p>
                        <button
                          onClick={() => openTab?.('governance')}
                          className="text-[10px] text-purple-400 hover:underline"
                        >
                          View in Decision Queue →
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button onClick={sendToGovernance}
                      className="w-full flex items-center justify-center gap-2
                                 py-2.5 rounded-xl text-xs font-bold
                                 border border-purple-500/40 text-purple-300
                                 bg-purple-500/10 hover:bg-purple-500/20
                                 transition-all"
                    >
                      🏛️ Send to AI Governance Hub for HITL Approval
                    </button>
                  )
                ) : (
                  <div className="rounded-xl p-3 bg-lime-DEFAULT/5
                                  border border-lime-DEFAULT/20">
                    <p className="text-[10px] text-lime-DEFAULT font-semibold">
                      ✓ Pre-Approved Change
                    </p>
                    <p className="text-[9px] text-text-muted mt-0.5">
                      Within PCCP bounds — log monitoring evidence and proceed.
                      No governance approval required.
                    </p>
                  </div>
                )}

                <div className="text-[9px] text-text-muted font-mono text-right">
                  Hash: {result.hash}
                </div>
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{ opacity:0 }} animate={{ opacity:1 }}
                className="glass rounded-xl p-8 flex flex-col items-center
                           justify-center gap-3 min-h-[200px]">
                <p className="text-4xl">🤖</p>
                <p className="text-text-muted text-xs text-center">
                  Select a scenario and click<br />
                  <span className="text-blue-DEFAULT">Assess Change</span>
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Audit feed */}
          <AnimatePresence>
            {auditFeed.length > 0 && (
              <motion.div key="audit"
                initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }}
                transition={{ delay:0.15 }}
                className="glass rounded-xl p-4 space-y-2"
              >
                <p className="text-[10px] text-text-muted uppercase tracking-wider
                              flex items-center gap-1.5 mb-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-lime-DEFAULT
                                   animate-pulse-lime inline-block" />
                  21 CFR Part 11 Audit Trail
                </p>
                {auditFeed.map((ev, i) => (
                  <motion.div key={ev.event + i}
                    initial={{ opacity:0, x:-8 }} animate={{ opacity:1, x:0 }}
                    transition={{ delay: i * 0.15 }}
                    className="flex gap-3 items-start"
                  >
                    <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0"
                      style={{ backgroundColor: ev.color }} />
                    <div className="min-w-0">
                      <p className="text-[10px] font-semibold font-mono"
                        style={{ color: ev.color }}>{ev.event}</p>
                      <p className="text-[9px] text-text-muted">{ev.detail}</p>
                      <p className="text-[9px] text-text-muted/60 font-mono">
                        {ev.time?.slice(0,19).replace('T',' ')} UTC
                      </p>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Bottom explainer */}
      <div className="glass rounded-xl p-4 grid grid-cols-4 gap-4 text-center">
        {[
          { icon:'🤖', label:'GAMP Cat 5 Asset',
            desc:'Every validated AI model is registered as a software asset with version history' },
          { icon:'📋', label:'PCCP Framework',
            desc:'Predetermined Change Control Plan pre-specifies locked vs adaptive changes' },
          { icon:'⚖️', label:'FDA PCCP Guidance',
            desc:'Risk logic aligned to FDA final guidance (Aug 18, 2025) on AI-enabled device software functions' },
          { icon:'🏛️', label:'HITL Governance',
            desc:'High and medium risk changes route to the AI Governance Hub for human approval' },
        ].map(item => (
          <div key={item.label} className="space-y-1">
            <p className="text-2xl">{item.icon}</p>
            <p className="text-white text-[11px] font-semibold">{item.label}</p>
            <p className="text-text-muted text-[10px] leading-relaxed">{item.desc}</p>
          </div>
        ))}
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

// ── Tab: Change Control ───────────────────────────────────────────

const CC_API = API_BASE

const SN_SCENARIOS = [
  { label:'Emergency Patch',    icon:'🚨', color:'#ef4444',
    cr_id:'CR-2024-0891', description:'Critical security patch — production LIMS',
    system_criticality:'critical', change_type:'emergency',
    system_name:'LabVantage LIMS' },
  { label:'Normal Upgrade',     icon:'🔼', color:'#f59e0b',
    cr_id:'CR-2024-0892', description:'ServiceNow v8.2 platform upgrade',
    system_criticality:'high',     change_type:'normal',
    system_name:'ServiceNow ITSM' },
  { label:'Config Change',      icon:'⚙️', color:'#007FFF',
    cr_id:'CR-2024-0893', description:'Update change approval workflow',
    system_criticality:'medium',   change_type:'standard',
    system_name:'SharePoint DMS' },
  { label:'Routine Maintenance',icon:'🔧', color:'#32CD32',
    cr_id:'CR-2024-0894', description:'Quarterly password rotation',
    system_criticality:'low',      change_type:'routine',
    system_name:'Salesforce CRM' },
]

const CC_SEV_MAP = {
  critical:'HIGH', high:'HIGH', medium:'MEDIUM',
  moderate:'MEDIUM', low:'LOW', minor:'LOW',
}
const CC_OCC_MAP = {
  emergency:'FREQUENT', expedited:'FREQUENT',
  normal:'OCCASIONAL', standard:'RARE', routine:'RARE',
}
const CC_SCALE = {
  HIGH:3, MEDIUM:2, LOW:1, FREQUENT:3, OCCASIONAL:2, RARE:1,
}
const CC_GAMP_DETECT = { 5:'LOW', 4:'MEDIUM', 3:'HIGH' }
const CC_ACTIVE_PHASES = new Set([
  'Plan','Requirements','Risk','Design','Verify',
])
const GXP_COLORS = {
  'GxP Direct':   { text:'#ef4444', bg:'rgba(239,68,68,0.12)',   border:'rgba(239,68,68,0.3)'   },
  'GxP Indirect': { text:'#f59e0b', bg:'rgba(245,158,11,0.12)',  border:'rgba(245,158,11,0.3)'  },
  'Non-GxP':      { text:'#6b7280', bg:'rgba(107,114,128,0.12)', border:'rgba(107,114,128,0.3)' },
}
const CC_FLAG_COLORS = {
  high:    { text:'#ef4444', bg:'rgba(239,68,68,0.1)',   icon:'⚠' },
  warning: { text:'#f59e0b', bg:'rgba(245,158,11,0.1)',  icon:'⚡' },
  none:    { text:'#6b7280', bg:'rgba(107,114,128,0.1)', icon:'✓' },
}
const RISK_COLORS = { High:'#ef4444', Medium:'#f59e0b', Low:'#32CD32' }
const RISK_BG     = {
  High:'rgba(239,68,68,0.12)', Medium:'rgba(245,158,11,0.12)',
  Low:'rgba(50,205,50,0.12)',
}

function ccBuildSystemContext(system) {
  if (!system) return null
  const isNonGxP = system.gxpStatus === 'Non-GxP'
  const isDirect = system.gxpStatus === 'GxP Direct'
  const inActive = CC_ACTIVE_PHASES.has(system.phase)
  const validated = system.phase === 'Released' || system.phase === 'Monitor'
  let revalidationFlag = null
  if (isNonGxP) {
    revalidationFlag = {
      level:'none',
      message:'Non-GxP system — validation not required for this change',
    }
  } else if (inActive) {
    revalidationFlag = {
      level:'warning',
      message:`Change during active ${system.phase} phase — impact assessment required`,
    }
  } else if (validated) {
    revalidationFlag = {
      level:'high',
      message:`Validated system in ${system.phase} — revalidation scope must be determined`,
    }
  }
  return {
    id:system.id, name:system.name, gxpStatus:system.gxpStatus,
    gampCategory:system.gampCategory, phase:system.phase,
    site:system.site, regulations:system.regulations,
    notes:system.notes, isNonGxP, isDirect, revalidationFlag,
  }
}

function ccLocalRisk(cr_id, system_criticality, change_type, system) {
  const ctx = ccBuildSystemContext(system)
  if (ctx?.isNonGxP) {
    const hash = btoa(`${cr_id}:LOW:1`).slice(0,16).replace(/[+/=]/g,'x')
    return {
      status:'assessed', cr_id, timestamp:new Date().toISOString(),
      risk_assessment:{
        severity:'LOW',
        occurrence: CC_OCC_MAP[change_type?.toLowerCase()] ?? 'OCCASIONAL',
        detectability:'HIGH', rpn:1, risk_level:'Low',
        testing_strategy:'No validation required — Non-GxP system',
        patient_safety_override:false,
      },
      _reasoning_hash:hash, _offline:true, _system_context:ctx,
    }
  }
  const severity    = CC_SEV_MAP[system_criticality?.toLowerCase()] ?? 'MEDIUM'
  const occurrence  = CC_OCC_MAP[change_type?.toLowerCase()]        ?? 'OCCASIONAL'
  const detectability = system
    ? (CC_GAMP_DETECT[system.gampCategory] ?? 'MEDIUM')
    : 'MEDIUM'
  const rpn = CC_SCALE[severity] * CC_SCALE[occurrence] * CC_SCALE[detectability]
  const patient_safety_override = severity === 'HIGH' && (ctx?.isDirect ?? true)
  const risk_level =
    patient_safety_override || rpn > 12 ? 'High'
    : rpn >= 5                          ? 'Medium' : 'Low'
  const testing_strategy =
    risk_level === 'High'
      ? (system?.gampCategory === 5
          ? 'Rigorous Scripted Testing — OQ + UAT required (GAMP Cat 5)'
          : 'Rigorous Scripted Testing')
      : risk_level === 'Medium'
        ? 'Hybrid Testing (Scripted + Unscripted)'
        : 'Unscripted Testing'
  const hash = btoa(`${cr_id}:${severity}:${occurrence}:${rpn}`)
    .slice(0,16).replace(/[+/=]/g,'x')
  return {
    status:'assessed', cr_id, timestamp:new Date().toISOString(),
    risk_assessment:{
      severity, occurrence, detectability, rpn,
      risk_level, testing_strategy, patient_safety_override,
    },
    _reasoning_hash:hash, _offline:true, _system_context:ctx,
  }
}

// GxP Classifier questionnaire
const GXP_QUESTIONS = [
  { id:'q1', group:'GxP Status',
    text:'Does this system directly generate, process, or store data used for GxP regulatory decisions?',
    hint:'e.g. batch release, QC lab results, clinical trial data, product quality records' },
  { id:'q2', group:'GxP Status',
    text:'Does a failure in this system have a direct impact on patient safety or product quality?',
    hint:'e.g. dosing calculations, sterility testing, adverse event reporting' },
  { id:'q3', group:'GxP Status',
    text:'Does it support GxP processes but not directly produce GxP records?',
    hint:'e.g. change management, ITSM, training tracking, document storage' },
  { id:'q4', group:'GAMP Category',
    text:'Is this commercially available off-the-shelf (COTS) software, configured but not custom-coded?',
    hint:'e.g. SAP, ServiceNow, Veeva Vault — vendor-supplied, configured for your processes' },
  { id:'q5', group:'GAMP Category',
    text:'Was this system custom-developed or does it contain significant bespoke code?',
    hint:'e.g. in-house built applications, heavily customised platforms with custom modules' },
  { id:'q6', group:'GAMP Category',
    text:'Is this infrastructure or platform software?',
    hint:'e.g. operating systems, middleware, database servers, virtualisation platforms' },
]

function classifyFromAnswers(answers) {
  let gxpStatus = 'Non-GxP'
  if (answers.q1 || answers.q2)      gxpStatus = 'GxP Direct'
  else if (answers.q3)               gxpStatus = 'GxP Indirect'
  let gampCategory = 4
  if (answers.q6)      gampCategory = 3
  else if (answers.q5) gampCategory = 5
  else if (answers.q4) gampCategory = 4
  return { gxpStatus, gampCategory }
}

function GxPClassifier({ systemName, onClassified }) {
  const [answers, setAnswers] = useState({})
  const toggle = (id, val) => setAnswers(a => ({ ...a, [id]: val }))
  const answeredAll  = GXP_QUESTIONS.every(q => answers[q.id] !== undefined)
  const classification = answeredAll ? classifyFromAnswers(answers) : null
  const groups = [...new Set(GXP_QUESTIONS.map(q => q.group))]

  return (
    <motion.div
      initial={{ opacity:0, y:8 }}
      animate={{ opacity:1, y:0 }}
      className="glass rounded-xl p-4 space-y-4"
    >
      <div className="flex items-center gap-2">
        <span className="text-base">🔍</span>
        <div>
          <p className="text-white text-[11px] font-semibold">
            GxP Classification Questionnaire
          </p>
          <p className="text-text-muted text-[9px]">
            Answer 6 questions — EVOLV determines GxP status and GAMP category
          </p>
        </div>
      </div>
      {groups.map((group, gi) => (
        <div key={group} className="space-y-2">
          <p className="text-[9px] text-text-muted uppercase tracking-wider
                         border-b border-border-base pb-1">{group}</p>
          {GXP_QUESTIONS.filter(q => q.group === group).map((q, i) => (
            <div key={q.id}
              className={`rounded-lg p-3 border transition-all
                ${answers[q.id] !== undefined
                  ? answers[q.id]
                    ? 'border-blue-DEFAULT/40 bg-blue-dim'
                    : 'border-border-base bg-bg-base'
                  : 'border-border-base'}`}
            >
              <p className="text-[11px] text-text-primary mb-0.5 leading-snug">
                <span className="text-text-muted mr-1.5 font-mono">
                  {gi === 0 ? i + 1 : i + 4}.
                </span>
                {q.text}
              </p>
              <p className="text-[9px] text-text-muted mb-2">{q.hint}</p>
              <div className="flex gap-2">
                {[{val:true,label:'Yes',col:'#007FFF'},{val:false,label:'No',col:'#6b7280'}].map(opt => (
                  <button key={String(opt.val)}
                    onClick={() => toggle(q.id, opt.val)}
                    className={`px-3 py-1 rounded-lg text-[10px] font-semibold
                      border transition-all
                      ${answers[q.id] === opt.val
                        ? 'text-white' : 'text-text-muted border-border-base hover:text-text-secondary'}`}
                    style={answers[q.id] === opt.val
                      ? { backgroundColor:opt.col, borderColor:opt.col } : {}}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
      <AnimatePresence>
        {classification && (
          <motion.div
            initial={{ opacity:0, scale:0.97 }}
            animate={{ opacity:1, scale:1 }}
            className="rounded-xl p-4 space-y-3"
            style={{
              backgroundColor: GXP_COLORS[classification.gxpStatus]?.bg,
              border: `1px solid ${GXP_COLORS[classification.gxpStatus]?.border}`,
            }}
          >
            <p className="text-[10px] text-text-muted uppercase tracking-wider">
              Classification Result
            </p>
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold"
                style={{ color:GXP_COLORS[classification.gxpStatus]?.text }}>
                {classification.gxpStatus}
              </span>
              <span className="text-text-muted">·</span>
              <span className="text-purple-400 text-sm font-bold">
                GAMP Category {classification.gampCategory}
              </span>
              <span className="text-text-muted">·</span>
              <span className="text-[10px] text-text-muted">
                Detectability: {CC_GAMP_DETECT[classification.gampCategory]}
              </span>
            </div>
            <p className="text-[9px] text-text-muted">
              {classification.gxpStatus === 'GxP Direct'
                ? 'Validation required. All changes must follow GAMP 5 change control procedure.'
                : classification.gxpStatus === 'GxP Indirect'
                  ? 'Abbreviated validation may apply. Change control documentation required.'
                  : 'No validation required. Standard IT change management applies.'}
            </p>
            <button
              onClick={() => onClassified(systemName, classification)}
              className="w-full flex items-center justify-center gap-2
                         py-2 rounded-lg text-xs font-semibold
                         bg-blue-DEFAULT text-white hover:brightness-110
                         transition-all shadow-[0_0_12px_rgba(0,127,255,0.3)]"
            >
              ＋ Add "{systemName || 'New System'}" to EVOLV Portfolio
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function ChangeControlTab() {
  const customSystems   = useAppStore(s => s.customSystems)
  const addCustomSystem = useAppStore(s => s.addCustomSystem)
  const allSystems = useMemo(
    () => [...SYSTEMS, ...customSystems], [customSystems],
  )

  const [form, setForm] = useState({
    cr_id:'', description:'',
    system_criticality:'high', change_type:'normal', system_name:'',
  })
  const [loading,       setLoading]       = useState(false)
  const [result,        setResult]        = useState(null)
  const [apiOnline,     setApiOnline]     = useState(null)
  const [auditFeed,     setAuditFeed]     = useState([])
  const [activeScen,    setActiveScen]    = useState(null)
  const [showClassifier,setShowClassifier] = useState(false)
  const [newSysName,    setNewSysName]    = useState('')

  const matchedSystem = allSystems.find(s => s.name === form.system_name) ?? null

  const applyScenario = useCallback(scen => {
    setActiveScen(scen.label)
    setResult(null)
    setAuditFeed([])
    setShowClassifier(false)
    setForm({
      cr_id:scen.cr_id, description:scen.description,
      system_criticality:scen.system_criticality,
      change_type:scen.change_type, system_name:scen.system_name ?? '',
    })
  }, [])

  const handleClassified = useCallback((name, classification) => {
    const newSystem = {
      id:`SYS-USR-${Date.now()}`,
      name: name || 'New System',
      gampCategory: classification.gampCategory,
      gxpStatus:    classification.gxpStatus,
      site:'User-defined', phase:'Plan',
      risk: classification.gxpStatus === 'GxP Direct' ? 'High' : 'Low',
      owner:'Unassigned',
      lastAction: new Date().toISOString().slice(0,10),
      dueDate:null,
      regulations: classification.gxpStatus !== 'Non-GxP' ? ['21 CFR Part 11'] : [],
      notes:'Classified via GxP Questionnaire — validation not yet started.',
    }
    addCustomSystem(newSystem)
    setForm(f => ({ ...f, system_name: newSystem.name }))
    setShowClassifier(false)
  }, [addCustomSystem])

  function buildAuditFeed(cr_id, data, t0, hash, ctx) {
    const ra = data.risk_assessment
    const feed = [{
      event:'CHANGE_REQUEST_RECEIVED', time:t0,
      detail:`CR ${cr_id} received — system: ${ctx?.name ?? 'unknown'}`,
      color:'#007FFF',
    }]
    if (ctx) feed.push({
      event:'PORTFOLIO_LOOKUP_COMPLETED', time:new Date().toISOString(),
      detail:`${ctx.name} | ${ctx.gxpStatus} | GAMP Cat ${ctx.gampCategory} | Phase: ${ctx.phase}`,
      color:'#a78bfa',
    })
    feed.push({
      event:'RISK_ASSESSMENT_COMPLETED', time:new Date().toISOString(),
      detail:`Risk: ${ra?.risk_level} | RPN: ${ra?.rpn} | Hash: ${hash}`,
      color:'#32CD32',
    })
    return feed
  }

  const submit = useCallback(async () => {
    if (!form.cr_id || !form.description) return
    setLoading(true); setResult(null); setAuditFeed([])
    const t0  = new Date().toISOString()
    const ctx = ccBuildSystemContext(matchedSystem)
    try {
      const res = await fetch(`${CC_API}/webhook/sn-change`, {
        method:'POST',
        headers:{ 'Content-Type':'application/json' },
        body: JSON.stringify({
          cr_id:form.cr_id, description:form.description,
          system_criticality:form.system_criticality,
          change_type:form.change_type,
        }),
        signal: AbortSignal.timeout(5000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setApiOnline(true)
      setResult({ ...data, _offline:false, _system_context:ctx })
      const hash = data._reasoning_hash ?? btoa(form.cr_id).slice(0,16)
      setAuditFeed(buildAuditFeed(form.cr_id, data, t0, hash, ctx))
    } catch {
      setApiOnline(false)
      const fb = ccLocalRisk(form.cr_id, form.system_criticality, form.change_type, matchedSystem)
      setResult(fb)
      setAuditFeed(buildAuditFeed(form.cr_id, fb, t0, fb._reasoning_hash, ctx))
    } finally {
      setLoading(false)
    }
  }, [form, matchedSystem])

  const ra   = result?.risk_assessment
  const rlvl = ra?.risk_level
  const rCol = RISK_COLORS[rlvl] ?? '#888'
  const rBg  = RISK_BG[rlvl]    ?? 'rgba(128,128,128,0.1)'

  return (
    <div className="space-y-5 overflow-y-auto h-full pr-1">

      {/* Header row */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-white font-semibold text-sm flex items-center gap-2 mb-1">
            🔄 Change Control
            <span className="text-[9px] px-1.5 py-0.5 rounded border font-medium"
              style={{ color:'#32CD32', borderColor:'rgba(50,205,50,0.3)',
                       backgroundColor:'rgba(50,205,50,0.1)' }}>
              ServiceNow Webhook
            </span>
          </h2>
          <p className="text-text-secondary text-xs">
            Submit a Change Request — EVOLV cross-references the GAMP 5 system
            registry, assesses risk, and logs a 21 CFR Part 11 audit record.
          </p>
        </div>
        {apiOnline !== null && (
          <span className={`text-[10px] px-2 py-1 rounded-lg border shrink-0 ml-4
            ${apiOnline
              ? 'text-lime-DEFAULT border-lime-DEFAULT/30 bg-lime-dim'
              : 'text-amber-400 border-amber-400/30 bg-amber-400/10'}`}>
            {apiOnline ? '● API Live' : '⚡ Offline Mode'}
          </span>
        )}
      </div>

      {/* Scenario presets */}
      <div>
        <p className="text-text-muted text-[10px] mb-2 uppercase tracking-wider">
          Quick-fire scenarios
        </p>
        <div className="grid grid-cols-4 gap-2">
          {SN_SCENARIOS.map(s => (
            <button key={s.label} onClick={() => applyScenario(s)}
              className={`p-3 rounded-xl border text-left transition-all
                ${activeScen === s.label ? 'bg-bg-hover' : 'hover:bg-bg-hover border-border-base'}`}
              style={activeScen === s.label
                ? { borderColor:s.color+'60', boxShadow:`0 0 16px ${s.color}22` } : {}}
            >
              <div className="text-xl mb-1.5">{s.icon}</div>
              <p className="text-white text-[11px] font-semibold leading-tight">{s.label}</p>
              <p className="text-text-muted text-[9px] mt-0.5">
                {s.change_type} · {s.system_criticality}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* CR form + response */}
      <div className="grid grid-cols-2 gap-5">

        {/* Left: CR form */}
        <div className="glass rounded-xl p-5 space-y-4">
          <p className="text-text-muted text-[10px] uppercase tracking-wider">
            Change Request
          </p>

          {/* System selector */}
          <div>
            <label className="text-[10px] text-text-muted block mb-1">
              System
              <span className="ml-1.5 text-[9px] text-blue-DEFAULT">
                ↗ cross-references EVOLV Portfolio
              </span>
            </label>
            <select value={form.system_name}
              onChange={e => setForm(f => ({ ...f, system_name:e.target.value }))}
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors"
            >
              <option value="">— Unknown / Not in EVOLV registry —</option>
              {allSystems.map(s => (
                <option key={s.id} value={s.name}>
                  {s.name} ({s.gxpStatus}, Cat {s.gampCategory})
                </option>
              ))}
            </select>
            {matchedSystem && (
              <div className="mt-2 rounded-lg px-3 py-2 flex items-center gap-3
                              animate-fade-in text-[10px]"
                style={{
                  backgroundColor: GXP_COLORS[matchedSystem.gxpStatus]?.bg,
                  border:`1px solid ${GXP_COLORS[matchedSystem.gxpStatus]?.border}`,
                }}
              >
                <span className="font-semibold shrink-0"
                  style={{ color:GXP_COLORS[matchedSystem.gxpStatus]?.text }}>
                  {matchedSystem.gxpStatus}
                </span>
                <span className="text-text-muted">·</span>
                <span className="text-text-secondary">GAMP Cat {matchedSystem.gampCategory}</span>
                <span className="text-text-muted">·</span>
                <span className="text-text-secondary">{matchedSystem.phase}</span>
                <span className="text-text-muted">·</span>
                <span className="text-text-muted truncate">{matchedSystem.site}</span>
              </div>
            )}
            {!matchedSystem && form.system_name === '' && (
              <div className="mt-2 rounded-lg px-3 py-2 flex items-center
                              justify-between gap-3 animate-fade-in
                              bg-amber-400/10 border border-amber-400/30">
                <div>
                  <p className="text-[10px] text-amber-400 font-semibold">
                    ⚠ System not in EVOLV registry
                  </p>
                  <p className="text-[9px] text-text-muted">
                    GxP classification unknown — risk assessment will be limited
                  </p>
                </div>
                <button
                  onClick={() => { setShowClassifier(p => !p); setNewSysName('') }}
                  className="shrink-0 text-[10px] px-3 py-1.5 rounded-lg
                             border border-amber-400/40 text-amber-400
                             hover:bg-amber-400/10 transition-all font-semibold whitespace-nowrap"
                >
                  {showClassifier ? '✕ Cancel' : '🔍 Classify System'}
                </button>
              </div>
            )}
          </div>

          {/* Classifier panel */}
          <AnimatePresence>
            {showClassifier && (
              <motion.div
                initial={{ opacity:0, height:0 }}
                animate={{ opacity:1, height:'auto' }}
                exit={{ opacity:0, height:0 }}
                style={{ overflow:'hidden' }}
              >
                <div className="mb-3">
                  <label className="text-[10px] text-text-muted block mb-1">
                    System name to register
                  </label>
                  <input value={newSysName}
                    onChange={e => setNewSysName(e.target.value)}
                    placeholder="e.g. Chromatography Data System"
                    className="w-full bg-bg-base border border-border-base rounded-lg
                               px-3 py-2 text-xs text-text-primary outline-none
                               focus:border-border-blue transition-colors"
                  />
                </div>
                <GxPClassifier systemName={newSysName} onClassified={handleClassified} />
              </motion.div>
            )}
          </AnimatePresence>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-text-muted block mb-1">CR ID</label>
              <input value={form.cr_id}
                onChange={e => setForm(f => ({ ...f, cr_id:e.target.value }))}
                placeholder="CR-2024-0001"
                className="w-full bg-bg-base border border-border-base rounded-lg
                           px-3 py-2 text-xs font-mono text-text-primary outline-none
                           focus:border-border-blue transition-colors"
              />
            </div>
            <div>
              <label className="text-[10px] text-text-muted block mb-1">
                System Criticality
              </label>
              <select value={form.system_criticality}
                onChange={e => setForm(f => ({ ...f, system_criticality:e.target.value }))}
                className="w-full bg-bg-base border border-border-base rounded-lg
                           px-3 py-2 text-xs text-text-primary outline-none
                           focus:border-border-blue transition-colors"
              >
                {['critical','high','medium','low','minor'].map(v => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-[10px] text-text-muted block mb-1">Description</label>
            <textarea value={form.description}
              onChange={e => setForm(f => ({ ...f, description:e.target.value }))}
              rows={3} placeholder="Describe the change…"
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors resize-none"
            />
          </div>

          <div>
            <label className="text-[10px] text-text-muted block mb-1">Change Type</label>
            <div className="grid grid-cols-4 gap-1.5">
              {['emergency','normal','standard','routine'].map(v => (
                <button key={v}
                  onClick={() => setForm(f => ({ ...f, change_type:v }))}
                  className={`py-1.5 rounded-lg text-[10px] font-medium border
                    transition-all capitalize
                    ${form.change_type === v
                      ? 'border-blue-DEFAULT bg-blue-dim text-blue-DEFAULT'
                      : 'border-border-base text-text-muted hover:text-text-secondary'}`}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>

          <button onClick={submit}
            disabled={loading || !form.cr_id}
            className="w-full flex items-center justify-center gap-2
                       px-4 py-3 rounded-xl text-sm font-bold
                       bg-blue-DEFAULT text-white hover:brightness-110
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all shadow-[0_0_24px_rgba(0,127,255,0.35)]"
          >
            {loading
              ? <><span className="animate-spin">⏳</span> Assessing…</>
              : '⚡ Submit to EVOLV'}
          </button>

          {apiOnline === false && (
            <p className="text-amber-400 text-[10px] text-center">
              ⚠ API server offline — showing deterministic fallback
            </p>
          )}
        </div>

        {/* Right: response + audit */}
        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div key="result"
                initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }}
                exit={{ opacity:0, y:-8 }} transition={{ duration:0.22 }}
                className="glass rounded-xl p-5 space-y-4"
              >
                {/* System context card */}
                {result._system_context && (
                  <div className="rounded-xl p-3 space-y-2 animate-fade-in"
                    style={{
                      backgroundColor: GXP_COLORS[result._system_context.gxpStatus]?.bg,
                      border:`1px solid ${GXP_COLORS[result._system_context.gxpStatus]?.border}`,
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-white text-[11px] font-semibold">
                        {result._system_context.name}
                      </p>
                      <span className="text-[9px] font-mono text-text-muted">
                        {result._system_context.id}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {[
                        { label:result._system_context.gxpStatus,
                          col:GXP_COLORS[result._system_context.gxpStatus]?.text },
                        { label:`GAMP Cat ${result._system_context.gampCategory}`, col:'#a78bfa' },
                        { label:result._system_context.phase, col:'#007FFF' },
                        { label:result._system_context.site, col:'#6b7280' },
                      ].map(b => (
                        <span key={b.label} className="text-[9px] px-1.5 py-0.5 rounded font-medium"
                          style={{ color:b.col, backgroundColor:b.col+'18', border:`1px solid ${b.col}30` }}>
                          {b.label}
                        </span>
                      ))}
                    </div>
                    {result._system_context.revalidationFlag && (
                      <div className="rounded-lg px-2 py-1.5 flex items-start gap-1.5"
                        style={{ backgroundColor:CC_FLAG_COLORS[result._system_context.revalidationFlag.level]?.bg }}>
                        <span className="shrink-0 text-[10px]">
                          {CC_FLAG_COLORS[result._system_context.revalidationFlag.level]?.icon}
                        </span>
                        <p className="text-[9px] leading-relaxed"
                          style={{ color:CC_FLAG_COLORS[result._system_context.revalidationFlag.level]?.text }}>
                          {result._system_context.revalidationFlag.message}
                        </p>
                      </div>
                    )}
                    <p className="text-[9px] text-text-muted italic">
                      {result._system_context.notes}
                    </p>
                  </div>
                )}

                {/* Big risk badge */}
                <div className="rounded-xl p-4 flex flex-col items-center gap-1"
                  style={{ backgroundColor:rBg, border:`1px solid ${rCol}40` }}>
                  <p className="text-[10px] text-text-muted uppercase tracking-widest">
                    Risk Level
                  </p>
                  <p className="text-4xl font-black tracking-wider"
                    style={{ color:rCol, textShadow:`0 0 24px ${rCol}88` }}>
                    {rlvl?.toUpperCase()}
                  </p>
                  <p className="text-[10px] font-mono" style={{ color:rCol+'cc' }}>
                    {ra?.testing_strategy}
                  </p>
                  {ra?.patient_safety_override && (
                    <span className="mt-1 text-[9px] px-2 py-0.5 rounded-full
                                     bg-red-500/20 border border-red-500/40 text-red-400 font-semibold">
                      ⚠ PATIENT SAFETY OVERRIDE
                    </span>
                  )}
                </div>

                {/* RPN breakdown */}
                <div className="grid grid-cols-4 gap-2">
                  {[
                    { label:'Severity',      val:ra?.severity },
                    { label:'Occurrence',    val:ra?.occurrence },
                    { label:'Detectability', val:ra?.detectability },
                    { label:'RPN', val:ra?.rpn, highlight:true, col:rCol },
                  ].map(item => (
                    <div key={item.label} className="rounded-lg p-2 text-center"
                      style={item.highlight
                        ? { backgroundColor:rBg, border:`1px solid ${rCol}40` }
                        : { backgroundColor:'rgba(255,255,255,0.04)',
                            border:'1px solid rgba(255,255,255,0.08)' }}
                    >
                      <p className="text-[9px] text-text-muted">{item.label}</p>
                      <p className="text-sm font-bold mt-0.5"
                        style={{ color:item.highlight ? item.col : 'var(--text-primary)' }}>
                        {item.val}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="text-[9px] text-text-muted font-mono text-right">
                  {result.cr_id} · {result.timestamp?.slice(0,19).replace('T',' ')}
                </div>
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{ opacity:0 }} animate={{ opacity:1 }}
                className="glass rounded-xl p-8 flex flex-col items-center
                           justify-center gap-3 min-h-[200px]">
                <p className="text-4xl">🔄</p>
                <p className="text-text-muted text-xs text-center">
                  Select a scenario and click<br />
                  <span className="text-blue-DEFAULT">Submit to EVOLV</span>
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Audit trail feed */}
          <AnimatePresence>
            {auditFeed.length > 0 && (
              <motion.div key="audit"
                initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }}
                transition={{ delay:0.15 }}
                className="glass rounded-xl p-4 space-y-2"
              >
                <p className="text-[10px] text-text-muted uppercase tracking-wider
                              flex items-center gap-1.5 mb-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-lime-DEFAULT
                                   animate-pulse-lime inline-block" />
                  21 CFR Part 11 Audit Trail
                </p>
                {auditFeed.map((ev, i) => (
                  <motion.div key={ev.event}
                    initial={{ opacity:0, x:-8 }} animate={{ opacity:1, x:0 }}
                    transition={{ delay:i * 0.18 }}
                    className="flex gap-3 items-start"
                  >
                    <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0"
                      style={{ backgroundColor:ev.color }} />
                    <div className="min-w-0">
                      <p className="text-[10px] font-semibold font-mono"
                        style={{ color:ev.color }}>{ev.event}</p>
                      <p className="text-[9px] text-text-muted truncate">{ev.detail}</p>
                      <p className="text-[9px] text-text-muted/60 font-mono">
                        {ev.time?.slice(0,19).replace('T',' ')} UTC
                      </p>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Bottom explainer */}
      <div className="glass rounded-xl p-4 grid grid-cols-4 gap-4 text-center">
        {[
          { icon:'📥', label:'Webhook Receiver',
            desc:'POST /webhook/sn-change accepts ServiceNow CR payload' },
          { icon:'🗂️', label:'Portfolio Cross-Reference',
            desc:'EVOLV looks up GxP status + GAMP category — context ServiceNow lacks' },
          { icon:'⚖️', label:'GAMP 5 Risk Engine',
            desc:'Severity × Occurrence × Detectability (by GAMP cat) → RPN → Risk Level' },
          { icon:'📋', label:'21 CFR Part 11 Log',
            desc:'Tamper-evident audit trail with SHA-256 reasoning hash' },
        ].map(item => (
          <div key={item.label} className="space-y-1">
            <p className="text-2xl">{item.icon}</p>
            <p className="text-white text-[11px] font-semibold">{item.label}</p>
            <p className="text-text-muted text-[10px] leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main Monitor page ─────────────────────────────────────────────
export default function Monitor({ openTab }) {
  const { setPhaseComplete } = useAppStore()
  const [activeTab, setActiveTab] = useState('changecontrol')

  // Mark monitor phase visited on first render
  useEffect(() => { setPhaseComplete('monitor') }, [setPhaseComplete])

  const tabs = [
    { id: 'changecontrol', label: '🔄 Change Control' },
    { id: 'aimodels',      label: '🤖 AI Models'      },
    { id: 'health',        label: '📊 System Health'  },
    { id: 'audit',         label: '🔍 Audit Trail'    },
    { id: 'deviations',    label: '⚠️ Deviations'     },
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
        {activeTab === 'changecontrol' && <ChangeControlTab />}
        {activeTab === 'aimodels'      && <AIModelsTab openTab={openTab} />}
        {activeTab === 'health'        && <SystemHealthTab />}
        {activeTab === 'audit'         && <AuditTrailTab />}
        {activeTab === 'deviations'    && <DeviationsTab />}
      </div>
    </div>
  )
}
