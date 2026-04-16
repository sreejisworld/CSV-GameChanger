/**
 * Portfolio — Enterprise system registry with QA Head and CTO views.
 *
 * Shows all GxP and non-GxP systems across sites with RAG status,
 * validation lifecycle stage, risk level, and actionable filters.
 * All data is self-contained sample data — no API calls needed.
 */
import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { SYSTEMS } from '../data/systems.js'
import { useAppStore } from '../store/useAppStore.js'

// ── Register System Modal ──────────────────────────────────────────
const GAMP_OPTIONS = [1, 3, 4, 5]
const GXP_OPTIONS  = ['GxP Direct', 'GxP Indirect', 'Non-GxP']
const PHASE_OPTIONS = [
  'Plan', 'Requirements', 'Risk', 'Design',
  'Verify', 'Released', 'Monitor', 'Retire',
]
const RISK_OPTIONS = ['High', 'Medium', 'Low']
const REG_OPTIONS  = [
  '21 CFR Part 11',
  '21 CFR Part 820 (QMSR)',
  'GMP Annex 11',
  'EU GMP',
  'GLP',
  'ISO 17025',
  'ISO 13485',
  'GDPR',
  'FDA PCCP Guidance Aug 2025',
]

const EMPTY_FORM = {
  name: '', gampCategory: 4, gxpStatus: 'GxP Direct',
  phase: 'Plan', risk: 'High', site: '', owner: '',
  regulations: [], notes: '', dueDate: '',
}

function RegisterSystemModal({ onClose, onSave }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [error, setError] = useState('')

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const toggleReg = reg => setForm(f => ({
    ...f,
    regulations: f.regulations.includes(reg)
      ? f.regulations.filter(r => r !== reg)
      : [...f.regulations, reg],
  }))

  const submit = () => {
    if (!form.name.trim()) { setError('System name is required.'); return }
    if (!form.site.trim()) { setError('Site is required.'); return }
    if (!form.owner.trim()) { setError('Owner is required.'); return }
    const today = new Date().toISOString().slice(0, 10)
    onSave({
      ...form,
      id: `CUST-${Date.now()}`,
      lastAction: today,
      dueDate: form.dueDate || null,
      _registered: true,
    })
    onClose()
  }

  const field = 'bg-bg-base border border-border-base rounded-lg px-3 py-2 ' +
    'text-xs text-text-primary placeholder:text-text-muted w-full ' +
    'focus:outline-none focus:border-blue-DEFAULT/60'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center
                    bg-black/60 backdrop-blur-sm p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96 }}
        transition={{ duration: 0.18 }}
        className="bg-bg-card border border-border-base rounded-2xl
                   shadow-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4
                        border-b border-border-base">
          <div>
            <h2 className="text-sm font-bold text-text-primary">
              Register System
            </h2>
            <p className="text-[11px] text-text-muted mt-0.5">
              Add a system to your EVOLV Portfolio
            </p>
          </div>
          <button onClick={onClose}
            className="text-text-muted hover:text-text-primary text-lg
                       leading-none transition-colors">
            ✕
          </button>
        </div>

        {/* Form */}
        <div className="px-5 py-4 space-y-4">

          {/* Name */}
          <div>
            <label className="text-[11px] text-text-muted uppercase
                              tracking-wider block mb-1">
              System Name <span className="text-red-400">*</span>
            </label>
            <input className={field} placeholder="e.g. LabVantage LIMS"
              value={form.name} onChange={e => set('name', e.target.value)} />
          </div>

          {/* Row: GAMP + GxP */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] text-text-muted uppercase
                                tracking-wider block mb-1">
                GAMP Category
              </label>
              <select className={field} value={form.gampCategory}
                onChange={e => set('gampCategory', Number(e.target.value))}>
                {GAMP_OPTIONS.map(c => (
                  <option key={c} value={c}>Category {c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[11px] text-text-muted uppercase
                                tracking-wider block mb-1">
                GxP Status
              </label>
              <select className={field} value={form.gxpStatus}
                onChange={e => set('gxpStatus', e.target.value)}>
                {GXP_OPTIONS.map(g => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Row: Phase + Risk */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] text-text-muted uppercase
                                tracking-wider block mb-1">
                Current Phase
              </label>
              <select className={field} value={form.phase}
                onChange={e => set('phase', e.target.value)}>
                {PHASE_OPTIONS.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[11px] text-text-muted uppercase
                                tracking-wider block mb-1">
                Risk Level
              </label>
              <select className={field} value={form.risk}
                onChange={e => set('risk', e.target.value)}>
                {RISK_OPTIONS.map(r => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Row: Site + Owner */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] text-text-muted uppercase
                                tracking-wider block mb-1">
                Site <span className="text-red-400">*</span>
              </label>
              <input className={field} placeholder="e.g. Basel, CH"
                value={form.site} onChange={e => set('site', e.target.value)} />
            </div>
            <div>
              <label className="text-[11px] text-text-muted uppercase
                                tracking-wider block mb-1">
                Owner <span className="text-red-400">*</span>
              </label>
              <input className={field} placeholder="e.g. J. Smith"
                value={form.owner} onChange={e => set('owner', e.target.value)} />
            </div>
          </div>

          {/* Due Date */}
          <div>
            <label className="text-[11px] text-text-muted uppercase
                              tracking-wider block mb-1">
              Due Date (optional)
            </label>
            <input type="date" className={field}
              value={form.dueDate} onChange={e => set('dueDate', e.target.value)} />
          </div>

          {/* Regulations */}
          <div>
            <label className="text-[11px] text-text-muted uppercase
                              tracking-wider block mb-2">
              Applicable Regulations
            </label>
            <div className="flex flex-wrap gap-2">
              {REG_OPTIONS.map(reg => {
                const on = form.regulations.includes(reg)
                return (
                  <button key={reg} onClick={() => toggleReg(reg)}
                    className={`text-[10px] px-2 py-1 rounded-lg border
                      transition-all ${on
                        ? 'bg-blue-DEFAULT/20 border-blue-DEFAULT/50 text-blue-DEFAULT'
                        : 'border-border-base text-text-muted hover:border-blue-DEFAULT/30'
                      }`}>
                    {reg}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="text-[11px] text-text-muted uppercase
                              tracking-wider block mb-1">
              Notes
            </label>
            <textarea className={field + ' resize-none'} rows={2}
              placeholder="Validation scope, context, open items…"
              value={form.notes} onChange={e => set('notes', e.target.value)} />
          </div>

          {error && (
            <p className="text-xs text-red-400">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-5 py-4
                        border-t border-border-base">
          <button onClick={onClose}
            className="px-4 py-1.5 text-xs text-text-muted rounded-lg
                       hover:text-text-primary transition-colors">
            Cancel
          </button>
          <button onClick={submit}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg
                       bg-blue-DEFAULT text-white hover:bg-blue-DEFAULT/90
                       transition-colors">
            Register System
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// ── RAG logic ─────────────────────────────────────────────────────
const ACTIVE_PHASES = ['Plan', 'Requirements', 'Risk', 'Design', 'Verify']

function getRAG(sys) {
  if (sys.risk === 'High' && ACTIVE_PHASES.includes(sys.phase))
    return 'red'
  if (sys.risk === 'Medium' && ACTIVE_PHASES.includes(sys.phase))
    return 'amber'
  if (sys.phase === 'Released' || sys.phase === 'Monitor')
    return 'green'
  return 'amber'
}

const RAG_STYLE = {
  red:   { dot: 'bg-red-500',           text: 'text-red-400',    label: 'Action Required',  border: 'border-red-500/30',   bg: 'bg-red-500/10'   },
  amber: { dot: 'bg-amber-DEFAULT',     text: 'text-amber-DEFAULT', label: 'In Progress',   border: 'border-amber-DEFAULT/30', bg: 'bg-amber-DEFAULT/10' },
  green: { dot: 'bg-lime-DEFAULT',      text: 'text-lime-DEFAULT', label: 'Compliant',      border: 'border-lime-DEFAULT/30', bg: 'bg-lime-DEFAULT/10' },
}

const PHASE_ORDER = [
  'Plan', 'Requirements', 'Risk', 'Design',
  'Verify', 'Released', 'Monitor', 'Retire',
]

const PHASE_COLOR = {
  Plan:         'text-blue-DEFAULT',
  Requirements: 'text-blue-DEFAULT',
  Risk:         'text-amber-DEFAULT',
  Design:       'text-purple-400',
  Verify:       'text-lime-DEFAULT',
  Released:     'text-lime-DEFAULT',
  Monitor:      'text-blue-DEFAULT',
  Retire:       'text-text-muted',
}

const RISK_COLOR = {
  High:   'text-red-400',
  Medium: 'text-amber-DEFAULT',
  Low:    'text-lime-DEFAULT',
}

const GXP_COLOR = {
  'GxP Direct':   'text-red-400',
  'GxP Indirect': 'text-amber-DEFAULT',
  'Non-GxP':      'text-text-muted',
}

// ── Utility ───────────────────────────────────────────────────────
const unique = (arr, key) => [...new Set(arr.map(x => x[key]))]

// ── Sub-components ────────────────────────────────────────────────
function KpiCard({ label, value, sub, color, icon }) {
  return (
    <div className="glass rounded-xl p-4 flex items-start gap-3">
      <div className="text-2xl shrink-0">{icon}</div>
      <div className="min-w-0">
        <p className="text-[10px] text-text-muted uppercase tracking-widest mb-0.5">
          {label}
        </p>
        <p className="text-2xl font-bold leading-none" style={{ color }}>
          {value}
        </p>
        {sub && (
          <p className="text-[10px] text-text-muted mt-1">{sub}</p>
        )}
      </div>
    </div>
  )
}

function RagDot({ rag, pulse }) {
  const s = RAG_STYLE[rag]
  return (
    <span className={`
      inline-block w-2 h-2 rounded-full shrink-0 ${s.dot}
      ${pulse && rag === 'red' ? 'animate-pulse' : ''}
    `} />
  )
}

function RagBadge({ rag }) {
  const s = RAG_STYLE[rag]
  return (
    <span className={`
      inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px]
      font-medium border ${s.border} ${s.bg} ${s.text}
    `}>
      <RagDot rag={rag} pulse />
      {s.label}
    </span>
  )
}

// ── QA Head view ──────────────────────────────────────────────────
function QAHeadView({ systems }) {
  const [siteFilter, setSiteFilter] = useState('All')
  const [gxpFilter,  setGxpFilter]  = useState('All')
  const [riskFilter, setRiskFilter] = useState('All')
  const [phaseFilter,setPhaseFilter]= useState('All')
  const [selected,   setSelected]   = useState(null)

  const sites  = ['All', ...unique(systems, 'site')]
  const gxps   = ['All', 'GxP Direct', 'GxP Indirect', 'Non-GxP']
  const risks  = ['All', 'High', 'Medium', 'Low']
  const phases = ['All', ...PHASE_ORDER]

  const filtered = useMemo(() => systems.filter(s => {
    if (siteFilter  !== 'All' && s.site      !== siteFilter)  return false
    if (gxpFilter   !== 'All' && s.gxpStatus !== gxpFilter)   return false
    if (riskFilter  !== 'All' && s.risk       !== riskFilter)  return false
    if (phaseFilter !== 'All' && s.phase      !== phaseFilter) return false
    return true
  }), [systems, siteFilter, gxpFilter, riskFilter, phaseFilter])

  const sel = selected ? systems.find(s => s.id === selected) : null

  return (
    <div className="flex gap-4 h-full min-h-0">
      {/* ── Main table panel ───────────────────────────── */}
      <div className="flex-1 min-w-0 flex flex-col gap-3">

        {/* Filter bar */}
        <div className="flex flex-wrap gap-2">
          {[
            { label: 'Site',   val: siteFilter,  set: setSiteFilter,  opts: sites  },
            { label: 'GxP',    val: gxpFilter,   set: setGxpFilter,   opts: gxps   },
            { label: 'Risk',   val: riskFilter,  set: setRiskFilter,  opts: risks  },
            { label: 'Phase',  val: phaseFilter, set: setPhaseFilter, opts: phases },
          ].map(({ label, val, set, opts }) => (
            <div key={label} className="flex items-center gap-1.5">
              <span className="text-[10px] text-text-muted uppercase tracking-wider">
                {label}
              </span>
              <select
                value={val}
                onChange={e => set(e.target.value)}
                className="evolv-select text-xs px-2 py-1 rounded"
              >
                {opts.map(o => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>
            </div>
          ))}
          <span className="ml-auto text-[10px] text-text-muted self-center">
            {filtered.length} of {systems.length} systems
          </span>
        </div>

        {/* Table */}
        <div className="glass rounded-xl overflow-auto flex-1">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border-base">
                {[
                  'Status', 'System', 'GAMP', 'GxP',
                  'Site', 'Phase', 'Risk', 'Owner', 'Due',
                ].map(h => (
                  <th key={h}
                    className="text-left px-3 py-2.5 text-[10px] text-text-muted
                               uppercase tracking-wider font-semibold whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(sys => {
                const rag = getRAG(sys)
                const isSelected = selected === sys.id
                return (
                  <tr
                    key={sys.id}
                    onClick={() => setSelected(isSelected ? null : sys.id)}
                    className={`
                      border-b border-border-base/50 cursor-pointer
                      transition-colors hover:bg-bg-hover
                      ${isSelected ? 'bg-blue-dim' : ''}
                    `}
                  >
                    <td className="px-3 py-2.5">
                      <RagDot rag={rag} pulse />
                    </td>
                    <td className="px-3 py-2.5 font-medium text-text-primary
                                   whitespace-nowrap">
                      {sys.name}
                    </td>
                    <td className="px-3 py-2.5 text-text-secondary">
                      Cat {sys.gampCategory}
                    </td>
                    <td className={`px-3 py-2.5 whitespace-nowrap
                                    ${GXP_COLOR[sys.gxpStatus]}`}>
                      {sys.gxpStatus}
                    </td>
                    <td className="px-3 py-2.5 text-text-secondary whitespace-nowrap">
                      {sys.site}
                    </td>
                    <td className={`px-3 py-2.5 whitespace-nowrap font-medium
                                    ${PHASE_COLOR[sys.phase] ?? 'text-text-secondary'}`}>
                      {sys.phase}
                    </td>
                    <td className={`px-3 py-2.5 font-semibold
                                    ${RISK_COLOR[sys.risk]}`}>
                      {sys.risk}
                    </td>
                    <td className="px-3 py-2.5 text-text-secondary whitespace-nowrap">
                      {sys.owner}
                    </td>
                    <td className="px-3 py-2.5 text-text-muted whitespace-nowrap">
                      {sys.dueDate ?? '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Detail panel ───────────────────────────────── */}
      {sel ? (
        <div className="w-72 shrink-0 glass rounded-xl p-4 flex flex-col gap-4
                        overflow-y-auto">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[10px] text-text-muted uppercase tracking-wider mb-1">
                {sel.id}
              </p>
              <h3 className="text-sm font-bold text-text-primary leading-snug">
                {sel.name}
              </h3>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-text-muted hover:text-text-secondary text-lg leading-none"
            >×</button>
          </div>

          <RagBadge rag={getRAG(sel)} />

          <div className="space-y-2 text-xs">
            {[
              ['GAMP Category', `Category ${sel.gampCategory}`],
              ['GxP Status',    sel.gxpStatus],
              ['Site',          sel.site],
              ['Phase',         sel.phase],
              ['Risk Level',    sel.risk],
              ['Owner',         sel.owner],
              ['Last Action',   sel.lastAction],
              ['Due Date',      sel.dueDate ?? 'No deadline'],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-2">
                <span className="text-text-muted">{k}</span>
                <span className="text-text-primary font-medium text-right">
                  {v}
                </span>
              </div>
            ))}
          </div>

          <div>
            <p className="text-[10px] text-text-muted uppercase tracking-wider mb-1.5">
              Regulations
            </p>
            <div className="flex flex-wrap gap-1">
              {sel.regulations.map(r => (
                <span key={r}
                  className="text-[9px] px-1.5 py-0.5 rounded border
                             border-border-base text-text-muted">
                  {r}
                </span>
              ))}
            </div>
          </div>

          <div>
            <p className="text-[10px] text-text-muted uppercase tracking-wider mb-1.5">
              Notes
            </p>
            <p className="text-xs text-text-secondary leading-relaxed">
              {sel.notes}
            </p>
          </div>
        </div>
      ) : (
        <div className="w-72 shrink-0 glass rounded-xl p-4 flex items-center
                        justify-center text-center">
          <p className="text-text-muted text-xs leading-relaxed">
            Click any row to see<br />system details
          </p>
        </div>
      )}
    </div>
  )
}

// ── CTO Executive view ────────────────────────────────────────────
function CTOView({ systems }) {
  const red   = systems.filter(s => getRAG(s) === 'red')
  const amber = systems.filter(s => getRAG(s) === 'amber')
  const green = systems.filter(s => getRAG(s) === 'green')

  const gxpDirect   = systems.filter(s => s.gxpStatus === 'GxP Direct')
  const gxpIndirect = systems.filter(s => s.gxpStatus === 'GxP Indirect')
  const nonGxp      = systems.filter(s => s.gxpStatus === 'Non-GxP')
  const inValidation= systems.filter(s => ACTIVE_PHASES.includes(s.phase))
  const released    = systems.filter(s => s.phase === 'Released' || s.phase === 'Monitor')

  // Site breakdown
  const siteNames = [...new Set(systems.map(s => s.site))].filter(s => s !== 'All Sites')
  const siteData  = siteNames.map(site => {
    const sysSite = systems.filter(s => s.site === site || s.site === 'All Sites')
    const r = sysSite.filter(s => getRAG(s) === 'red').length
    const a = sysSite.filter(s => getRAG(s) === 'amber').length
    const g = sysSite.filter(s => getRAG(s) === 'green').length
    return { site, total: sysSite.length, red: r, amber: a, green: g }
  })

  // Compliance rate
  const complianceRate = Math.round((green.length / systems.length) * 100)

  // Systems needing attention
  const attention = [...red, ...amber].sort((a, b) => {
    if (getRAG(a) === 'red' && getRAG(b) !== 'red') return -1
    if (getRAG(b) === 'red' && getRAG(a) !== 'red') return 1
    return 0
  })

  return (
    <div className="space-y-5">
      {/* ── Executive KPI row ────────────────────────── */}
      <div className="grid grid-cols-4 gap-3">
        <KpiCard
          label="Total Systems"
          value={systems.length}
          sub={`Across 25 sites · ${gxpDirect.length} GxP Direct`}
          color="#007FFF"
          icon="🏢"
        />
        <KpiCard
          label="Action Required"
          value={red.length}
          sub={`${amber.length} in progress · ${green.length} compliant`}
          color={red.length > 0 ? '#ef4444' : '#32CD32'}
          icon="⚠️"
        />
        <KpiCard
          label="In Validation"
          value={inValidation.length}
          sub={`${released.length} validated & released`}
          color="#f59e0b"
          icon="🏭"
        />
        <KpiCard
          label="Compliance Rate"
          value={`${complianceRate}%`}
          sub={`${green.length} of ${systems.length} systems compliant`}
          color={complianceRate >= 80 ? '#32CD32' : '#f59e0b'}
          icon="✅"
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* ── Portfolio breakdown ──────────────────────── */}
        <div className="glass rounded-xl p-4 col-span-1">
          <p className="text-[10px] text-text-muted uppercase tracking-widest
                        mb-3 font-semibold">
            Portfolio Breakdown
          </p>
          <div className="space-y-2.5">
            {[
              { label: 'GxP Direct',   count: gxpDirect.length,   color: '#ef4444' },
              { label: 'GxP Indirect', count: gxpIndirect.length, color: '#f59e0b' },
              { label: 'Non-GxP',      count: nonGxp.length,      color: '#64748b' },
            ].map(({ label, count, color }) => {
              const pct = Math.round((count / systems.length) * 100)
              return (
                <div key={label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-text-secondary">{label}</span>
                    <span className="text-text-muted">{count} systems</span>
                  </div>
                  <div className="h-1.5 bg-bg-hover rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, backgroundColor: color }}
                    />
                  </div>
                </div>
              )
            })}
          </div>

          <div className="neon-sep my-4" />

          <p className="text-[10px] text-text-muted uppercase tracking-widest
                        mb-3 font-semibold">
            Validation Status
          </p>
          <div className="space-y-2">
            {[
              { label: 'Action Required', count: red.length,    color: '#ef4444' },
              { label: 'In Validation',   count: amber.length,  color: '#f59e0b' },
              { label: 'Validated',       count: green.length,  color: '#32CD32' },
            ].map(({ label, count, color }) => (
              <div key={label} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-text-secondary">{label}</span>
                </div>
                <span className="font-semibold" style={{ color }}>
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Site breakdown ───────────────────────────── */}
        <div className="glass rounded-xl p-4 col-span-1">
          <p className="text-[10px] text-text-muted uppercase tracking-widest
                        mb-3 font-semibold">
            Site Overview
          </p>
          <div className="space-y-3">
            {siteData.map(({ site, total, red: r, amber: a, green: g }) => (
              <div key={site}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs text-text-secondary">{site}</span>
                  <span className="text-[10px] text-text-muted">{total} systems</span>
                </div>
                <div className="flex h-1.5 rounded-full overflow-hidden gap-px">
                  {r > 0 && (
                    <div
                      className="bg-red-500"
                      style={{ width: `${(r / total) * 100}%` }}
                      title={`${r} action required`}
                    />
                  )}
                  {a > 0 && (
                    <div
                      className="bg-amber-DEFAULT"
                      style={{ width: `${(a / total) * 100}%` }}
                      title={`${a} in progress`}
                    />
                  )}
                  {g > 0 && (
                    <div
                      className="bg-lime-DEFAULT"
                      style={{ width: `${(g / total) * 100}%` }}
                      title={`${g} compliant`}
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-text-muted mt-4">
            Showing 4 key sites of 25 total
          </p>
        </div>

        {/* ── Action required ──────────────────────────── */}
        <div className="glass rounded-xl p-4 col-span-1 flex flex-col">
          <p className="text-[10px] text-text-muted uppercase tracking-widest
                        mb-3 font-semibold">
            Needs Attention
          </p>
          <div className="flex-1 space-y-2 overflow-y-auto">
            {attention.length === 0 ? (
              <p className="text-xs text-text-muted">All systems compliant.</p>
            ) : (
              attention.map(sys => {
                const rag = getRAG(sys)
                const s   = RAG_STYLE[rag]
                return (
                  <div
                    key={sys.id}
                    className={`rounded-lg p-2.5 border ${s.border} ${s.bg}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <RagDot rag={rag} pulse />
                      <span className={`text-xs font-semibold ${s.text}`}>
                        {sys.name}
                      </span>
                    </div>
                    <p className="text-[10px] text-text-muted leading-relaxed">
                      {sys.site} · {sys.phase} · Risk {sys.risk}
                    </p>
                    {sys.dueDate && (
                      <p className="text-[10px] text-amber-DEFAULT mt-0.5">
                        Due {sys.dueDate}
                      </p>
                    )}
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────
export default function Portfolio() {
  const customSystems  = useAppStore(s => s.customSystems)
  const addCustomSystem = useAppStore(s => s.addCustomSystem)
  const allSystems     = useMemo(
    () => [...SYSTEMS, ...customSystems],
    [customSystems],
  )
  const [view,         setView]         = useState('qa')
  const [showRegister, setShowRegister] = useState(false)

  const systems = useMemo(() =>
    allSystems.map(s => ({ ...s, rag: getRAG(s) })),
    [allSystems],
  )

  const red   = systems.filter(s => s.rag === 'red').length
  const amber = systems.filter(s => s.rag === 'amber').length
  const green = systems.filter(s => s.rag === 'green').length

  return (
    <>
    <AnimatePresence>
      {showRegister && (
        <RegisterSystemModal
          onClose={() => setShowRegister(false)}
          onSave={system => { addCustomSystem(system); setShowRegister(false) }}
        />
      )}
    </AnimatePresence>
    <div className="h-full overflow-y-auto bg-bg-base">
      <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col gap-5 min-h-full">

        {/* ── Header ─────────────────────────────────────── */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white">
                System Portfolio
              </h1>
              <span className="text-[10px] px-2 py-0.5 rounded border
                               border-blue-DEFAULT/30 bg-blue-dim text-blue-DEFAULT
                               font-semibold uppercase tracking-wider">
                150 Systems · 25 Sites
              </span>
            </div>

            <div className="flex items-center gap-2">
              {/* Register System button */}
              <button
                onClick={() => setShowRegister(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                           text-xs font-semibold border border-blue-DEFAULT/40
                           text-blue-DEFAULT bg-blue-DEFAULT/10
                           hover:bg-blue-DEFAULT/20 transition-colors"
              >
                + Register System
              </button>

              {/* View toggle */}
              <div className="flex items-center gap-1 p-0.5 rounded-lg
                              bg-bg-card border border-border-base">
                {[
                  { id: 'qa',  label: 'QA Head View' },
                  { id: 'cto', label: 'CTO View' },
                ].map(v => (
                  <button
                    key={v.id}
                    onClick={() => setView(v.id)}
                    className={`
                      px-3 py-1.5 rounded text-xs font-semibold transition-colors
                      ${view === v.id
                        ? 'bg-blue-DEFAULT text-white'
                        : 'text-text-muted hover:text-text-secondary'}
                    `}
                  >
                    {v.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <p className="text-text-muted text-xs">
            GAMP 5 · 21 CFR Part 11 · GMP Annex 11 · ISO 13485
            · GDPR — enterprise compliance posture
          </p>
          <div className="neon-sep mt-3" />
        </div>

        {/* ── RAG summary strip ──────────────────────────── */}
        <div className="flex items-center gap-4 px-4 py-2.5 glass rounded-xl">
          <span className="text-[10px] text-text-muted uppercase tracking-widest
                           font-semibold">
            Portfolio Health
          </span>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-xs text-red-400 font-semibold">{red}</span>
            <span className="text-xs text-text-muted">Action Required</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-DEFAULT" />
            <span className="text-xs text-amber-DEFAULT font-semibold">{amber}</span>
            <span className="text-xs text-text-muted">In Progress</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-lime-DEFAULT" />
            <span className="text-xs text-lime-DEFAULT font-semibold">{green}</span>
            <span className="text-xs text-text-muted">Compliant</span>
          </div>
          <span className="ml-auto text-[10px] text-text-muted">
            {customSystems.length > 0
              ? `${allSystems.length} systems · ${customSystems.length} registered`
              : `Showing ${SYSTEMS.length} sample systems`
            }
          </span>
        </div>

        {/* ── Active view ────────────────────────────────── */}
        <div className="flex-1 min-h-0">
          {view === 'qa'
            ? <QAHeadView systems={systems} />
            : <CTOView    systems={systems} />
          }
        </div>

        <p className="text-center text-text-muted text-xs pb-2">
          Powered by EVOLV | WingstarTech Inc. — AI-assisted, human-approved.
        </p>
      </div>
    </div>
    </>
  )
}
