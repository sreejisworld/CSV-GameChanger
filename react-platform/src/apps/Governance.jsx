/**
 * Governance.jsx — EVOLV AI Governance Hub
 *
 * Human-in-the-Loop control centre for AI decisions.
 * Designed for demo to pharma/biotech CTOs and QA/CSV Heads.
 *
 * Tabs:
 *   1. Decision Queue   — AI decisions awaiting human review
 *   2. Override Ledger  — Immutable record of every human override
 *   3. Audit Timeline   — Visual lifecycle trail (AI + Human events)
 *   4. Transparency     — Per-requirement AI reasoning report
 *
 * :requirement: URS-27.1 – Display AI decision queue for HITL review.
 * :requirement: URS-27.2 – Show immutable human override ledger.
 * :requirement: URS-27.3 – Render audit event timeline.
 * :requirement: URS-27.4 – Capture reviewer name, role, reason.
 */
import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '../store/useAppStore'

const API = 'http://localhost:8000'

// ── Colour helpers ────────────────────────────────────────────────
const STATUS_COLOR = {
  pending:   { bg: 'bg-amber-500/10',  border: 'border-amber-500/40',
               text: 'text-amber-400',  dot: 'bg-amber-400' },
  approved:  { bg: 'bg-lime-500/10',   border: 'border-lime-500/40',
               text: 'text-lime-400',   dot: 'bg-lime-400' },
  overridden:{ bg: 'bg-blue-500/10',   border: 'border-blue-500/40',
               text: 'text-blue-400',   dot: 'bg-blue-400' },
  rejected:  { bg: 'bg-red-500/10',    border: 'border-red-500/40',
               text: 'text-red-400',    dot: 'bg-red-400' },
}

const TYPE_LABEL = {
  URS_GENERATION:        'URS Generation',
  RISK_CLASSIFICATION:   'Risk Classification',
  TEST_SCRIPT_GENERATED: 'Test Script',
  URS_VERIFICATION:      'URS Verification',
}

const TYPE_ICON = {
  URS_GENERATION:        '📄',
  RISK_CLASSIFICATION:   '⚖️',
  TEST_SCRIPT_GENERATED: '🧪',
  URS_VERIFICATION:      '✅',
}

function fmtTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('en-GB', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

function ConfidenceBar({ value }) {
  if (value == null) return null
  const pct = Math.round(value * 100)
  const color = pct >= 90 ? '#32CD32' : pct >= 75 ? '#f59e0b' : '#ef4444'
  return (
    <div className='flex items-center gap-2'>
      <span className='text-xs text-[var(--text-muted)]'>Confidence</span>
      <div className='flex-1 h-1.5 rounded-full bg-white/5'>
        <div
          className='h-1.5 rounded-full transition-all'
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className='text-xs font-mono' style={{ color }}>{pct}%</span>
    </div>
  )
}

function StatusPill({ status }) {
  const c = STATUS_COLOR[status] ?? STATUS_COLOR.pending
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5
      rounded-full text-xs font-medium ${c.text} ${c.bg} border ${c.border}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

// ── Tab 1: Decision Queue ─────────────────────────────────────────
function DecisionCard({ decision, onReview }) {
  const [expanded, setExpanded] = useState(false)
  const [overrideOpen, setOverrideOpen] = useState(false)
  const [rejectOpen, setRejectOpen]   = useState(false)
  const [reviewerName, setReviewerName] = useState('')
  const [reviewerRole, setReviewerRole] = useState('')
  const [newValue, setNewValue]   = useState('')
  const [reason, setReason]       = useState('')
  const [submitting, setSubmitting] = useState(false)
  const userProfile = useAppStore(s => s.userProfile)

  // Pre-fill from user profile
  useEffect(() => {
    if (userProfile.name) setReviewerName(userProfile.name)
    if (userProfile.role) setReviewerRole(userProfile.role)
  }, [userProfile])

  const c = STATUS_COLOR[decision.status] ?? STATUS_COLOR.pending
  const isPending = decision.status === 'pending'

  const submit = async (action) => {
    if (!reviewerName || !reviewerRole) {
      alert('Please enter your name and role.')
      return
    }
    if ((action === 'override') && !newValue) {
      alert('Please enter the new value.')
      return
    }
    if ((action === 'override' || action === 'reject') && !reason) {
      alert('Please enter a reason.')
      return
    }
    setSubmitting(true)
    try {
      await onReview(decision.decision_id, {
        action, reviewer_name: reviewerName,
        reviewer_role: reviewerRole,
        new_value: newValue || null,
        reason: reason || null,
      })
      setOverrideOpen(false)
      setRejectOpen(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className={`rounded-xl border ${c.border} ${c.bg} p-4 space-y-3`}
    >
      {/* Card header */}
      <div className='flex items-start justify-between gap-3'>
        <div className='flex items-center gap-2 flex-wrap'>
          <span className='text-lg'>{TYPE_ICON[decision.decision_type] ?? '🤖'}</span>
          <span className='font-semibold text-[var(--text-primary)]'>
            {decision.urs_id}
          </span>
          <span className='text-xs px-2 py-0.5 rounded bg-white/5
            text-[var(--text-muted)] border border-white/10'>
            {TYPE_LABEL[decision.decision_type] ?? decision.decision_type}
          </span>
          <StatusPill status={decision.status} />
        </div>
        <span className='text-xs text-[var(--text-muted)] whitespace-nowrap'>
          {fmtTime(decision.created_at)}
        </span>
      </div>

      {/* AI output summary */}
      <div className='text-sm text-[var(--text-secondary)] space-y-1'>
        {Object.entries(decision.ai_output).map(([k, v]) => (
          <div key={k} className='flex gap-2'>
            <span className='text-[var(--text-muted)] capitalize min-w-[120px]'>
              {k.replace(/_/g, ' ')}
            </span>
            <span className='font-mono text-[var(--text-primary)]'>
              {typeof v === 'object' ? JSON.stringify(v) : String(v)}
            </span>
          </div>
        ))}
      </div>

      {/* Confidence bar */}
      <ConfidenceBar value={decision.confidence} />

      {/* Expand: AI reasoning */}
      <button
        onClick={() => setExpanded(e => !e)}
        className='flex items-center gap-1.5 text-xs text-[var(--text-muted)]
          hover:text-[var(--text-primary)] transition-colors'
      >
        <span className={`transition-transform ${expanded ? 'rotate-90' : ''}`}>▶</span>
        AI Reasoning & GAMP 5 Reference
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className='overflow-hidden'
          >
            <div className='rounded-lg bg-black/20 border border-white/5
              p-3 space-y-2 text-xs'>
              <div>
                <p className='text-[var(--text-muted)] mb-1 uppercase tracking-wide
                  text-[10px]'>AI Reasoning</p>
                <p className='text-[var(--text-secondary)] leading-relaxed'>
                  {decision.ai_reasoning}
                </p>
              </div>
              {decision.gamp5_reference && (
                <div className='border-t border-white/5 pt-2'>
                  <p className='text-[var(--text-muted)] mb-1 uppercase tracking-wide
                    text-[10px]'>GAMP 5 Reference</p>
                  <p className='text-blue-300/80 leading-relaxed italic'>
                    {decision.gamp5_reference}
                  </p>
                </div>
              )}
              {decision.reviewed_by && (
                <div className='border-t border-white/5 pt-2'>
                  <p className='text-[var(--text-muted)] mb-1 uppercase tracking-wide
                    text-[10px]'>Human Review</p>
                  <p className='text-[var(--text-secondary)]'>
                    <span className='font-medium text-[var(--text-primary)]'>
                      {decision.reviewed_by}
                    </span>
                    {decision.reviewer_role && ` (${decision.reviewer_role})`}
                    {' — '}{fmtTime(decision.reviewed_at)}
                  </p>
                  {decision.override_reason && (
                    <p className='mt-1 text-amber-300/80 italic'>
                      "{decision.override_reason}"
                    </p>
                  )}
                  {decision.new_value && (
                    <p className='mt-1'>
                      Changed to:{' '}
                      <span className='font-semibold text-lime-400'>
                        {decision.new_value}
                      </span>
                    </p>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Action buttons — only for pending decisions */}
      {isPending && (
        <div className='pt-1 space-y-2'>
          <div className='flex gap-2'>
            <button
              onClick={() => submit('approve')}
              disabled={submitting || !reviewerName}
              className='flex-1 py-1.5 rounded-lg text-sm font-medium
                bg-lime-500/20 hover:bg-lime-500/30 text-lime-400
                border border-lime-500/30 transition-all disabled:opacity-40'
            >
              ✓ Approve
            </button>
            <button
              onClick={() => {
                setOverrideOpen(o => !o)
                setRejectOpen(false)
              }}
              disabled={submitting}
              className='flex-1 py-1.5 rounded-lg text-sm font-medium
                bg-blue-500/20 hover:bg-blue-500/30 text-blue-400
                border border-blue-500/30 transition-all disabled:opacity-40'
            >
              ✎ Override
            </button>
            <button
              onClick={() => {
                setRejectOpen(r => !r)
                setOverrideOpen(false)
              }}
              disabled={submitting}
              className='flex-1 py-1.5 rounded-lg text-sm font-medium
                bg-red-500/20 hover:bg-red-500/30 text-red-400
                border border-red-500/30 transition-all disabled:opacity-40'
            >
              ✕ Reject
            </button>
          </div>

          {/* Reviewer identity row */}
          <div className='flex gap-2'>
            <input
              value={reviewerName}
              onChange={e => setReviewerName(e.target.value)}
              placeholder='Your name'
              className='evolv-input flex-1 text-xs py-1.5 px-2'
            />
            <input
              value={reviewerRole}
              onChange={e => setReviewerRole(e.target.value)}
              placeholder='Your role (e.g. QA Head)'
              className='evolv-input flex-1 text-xs py-1.5 px-2'
            />
          </div>

          {/* Override form */}
          <AnimatePresence>
            {overrideOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className='overflow-hidden'
              >
                <div className='space-y-2 rounded-lg bg-blue-500/5
                  border border-blue-500/20 p-3'>
                  <p className='text-xs text-blue-400 font-medium'>
                    Override AI Decision
                  </p>
                  <input
                    value={newValue}
                    onChange={e => setNewValue(e.target.value)}
                    placeholder='New value (e.g. High, Medium, Low…)'
                    className='evolv-input w-full text-sm py-1.5 px-2'
                  />
                  <textarea
                    value={reason}
                    onChange={e => setReason(e.target.value)}
                    placeholder='Reason for override (required for audit trail)…'
                    rows={2}
                    className='evolv-input w-full text-sm py-1.5 px-2 resize-none'
                  />
                  <button
                    onClick={() => submit('override')}
                    disabled={submitting}
                    className='w-full py-1.5 rounded-lg text-sm font-medium
                      bg-blue-500/30 hover:bg-blue-500/40 text-blue-300
                      border border-blue-500/40 transition-all disabled:opacity-40'
                  >
                    {submitting ? 'Saving…' : 'Confirm Override'}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Reject form */}
          <AnimatePresence>
            {rejectOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className='overflow-hidden'
              >
                <div className='space-y-2 rounded-lg bg-red-500/5
                  border border-red-500/20 p-3'>
                  <p className='text-xs text-red-400 font-medium'>
                    Reject Decision
                  </p>
                  <textarea
                    value={reason}
                    onChange={e => setReason(e.target.value)}
                    placeholder='Reason for rejection (required)…'
                    rows={2}
                    className='evolv-input w-full text-sm py-1.5 px-2 resize-none'
                  />
                  <button
                    onClick={() => submit('reject')}
                    disabled={submitting}
                    className='w-full py-1.5 rounded-lg text-sm font-medium
                      bg-red-500/30 hover:bg-red-500/40 text-red-300
                      border border-red-500/40 transition-all disabled:opacity-40'
                  >
                    {submitting ? 'Saving…' : 'Confirm Rejection'}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  )
}

function QueueTab({ decisions, onReview }) {
  const [filter, setFilter] = useState('all')
  const filters = ['all', 'pending', 'approved', 'overridden', 'rejected']

  const visible = filter === 'all'
    ? decisions
    : decisions.filter(d => d.status === filter)

  const pendingCount = decisions.filter(d => d.status === 'pending').length

  return (
    <div className='space-y-4'>
      {/* Filter pills */}
      <div className='flex gap-2 flex-wrap'>
        {filters.map(f => {
          const count = f === 'all'
            ? decisions.length
            : decisions.filter(d => d.status === f).length
          return (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-full text-xs font-medium
                transition-all border
                ${filter === f
                  ? 'bg-[var(--accent)] text-white border-[var(--accent)]'
                  : 'text-[var(--text-muted)] border-white/10 hover:border-white/20'
                }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)} ({count})
            </button>
          )
        })}
        {pendingCount > 0 && (
          <span className='ml-auto text-xs text-amber-400 flex items-center gap-1'>
            <span className='w-2 h-2 rounded-full bg-amber-400 animate-pulse' />
            {pendingCount} awaiting your review
          </span>
        )}
      </div>

      {/* Cards */}
      <AnimatePresence mode='popLayout'>
        {visible.length === 0 ? (
          <div className='text-center py-12 text-[var(--text-muted)] text-sm'>
            No decisions in this category.
          </div>
        ) : (
          visible.map(d => (
            <DecisionCard
              key={d.decision_id}
              decision={d}
              onReview={onReview}
            />
          ))
        )}
      </AnimatePresence>
    </div>
  )
}

// ── Tab 2: Override Ledger ────────────────────────────────────────
function LedgerTab({ overrides }) {
  if (overrides.length === 0) {
    return (
      <div className='text-center py-12 text-[var(--text-muted)] text-sm'>
        No human overrides recorded yet.
      </div>
    )
  }

  return (
    <div className='space-y-3'>
      <p className='text-xs text-[var(--text-muted)]'>
        Append-only record. Every row is SHA-256 hashed and
        cross-referenced to the audit trail. Cannot be modified or deleted.
      </p>
      <div className='overflow-x-auto'>
        <table className='w-full text-sm'>
          <thead>
            <tr className='text-left text-xs text-[var(--text-muted)]
              border-b border-white/10'>
              {['URS', 'Type', 'AI Said', 'Changed To', 'By', 'Role',
                'Reason', 'Time', 'Hash'].map(h => (
                <th key={h} className='pb-2 pr-4 font-medium
                  whitespace-nowrap'>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {overrides.map((o, i) => (
              <motion.tr
                key={o.override_id ?? i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.04 }}
                className='border-b border-white/5 hover:bg-white/2
                  transition-colors'
              >
                <td className='py-2.5 pr-4 font-mono text-blue-400
                  text-xs whitespace-nowrap'>{o.urs_id}</td>
                <td className='py-2.5 pr-4 text-xs text-[var(--text-muted)]
                  whitespace-nowrap'>
                  {TYPE_LABEL[o.decision_type] ?? o.decision_type}
                </td>
                <td className='py-2.5 pr-4 text-xs text-[var(--text-secondary)]'>
                  {o.ai_said}
                </td>
                <td className='py-2.5 pr-4'>
                  <span className='px-2 py-0.5 rounded bg-amber-500/15
                    text-amber-400 text-xs font-medium border
                    border-amber-500/30 whitespace-nowrap'>
                    {o.human_changed_to}
                  </span>
                </td>
                <td className='py-2.5 pr-4 text-xs font-medium
                  text-[var(--text-primary)] whitespace-nowrap'>
                  {o.reviewer_name}
                </td>
                <td className='py-2.5 pr-4 text-xs
                  text-[var(--text-muted)] whitespace-nowrap'>
                  {o.reviewer_role}
                </td>
                <td className='py-2.5 pr-4 text-xs text-[var(--text-secondary)]
                  max-w-[220px]'>
                  <span className='line-clamp-2 italic text-amber-200/70'>
                    "{o.reason}"
                  </span>
                </td>
                <td className='py-2.5 pr-4 text-xs text-[var(--text-muted)]
                  whitespace-nowrap font-mono'>{fmtTime(o.reviewed_at)}</td>
                <td className='py-2.5 text-xs font-mono text-lime-400/60
                  whitespace-nowrap'>{o.audit_hash}</td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Tab 3: Audit Timeline ─────────────────────────────────────────
function TimelineEvent({ event, index }) {
  const isAI    = event.actor_type === 'AI'
  const color   = isAI
    ? { line: 'bg-purple-500', dot: 'bg-purple-400 ring-purple-500/40',
        badge: 'text-purple-400 bg-purple-500/10 border-purple-500/30' }
    : STATUS_COLOR[event.status] ?? STATUS_COLOR.approved

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className='flex gap-4'
    >
      {/* Spine */}
      <div className='flex flex-col items-center w-8 flex-shrink-0'>
        <div className={`w-3 h-3 rounded-full ring-4 ring-offset-0
          flex-shrink-0 ${isAI ? 'bg-purple-400 ring-purple-500/30'
          : `${color.dot} ring-lime-500/20`}`} />
        <div className='w-px flex-1 bg-white/10 mt-1' />
      </div>

      {/* Content */}
      <div className='pb-6 flex-1 min-w-0'>
        <div className='flex items-center gap-2 mb-1 flex-wrap'>
          <span className={`text-xs px-2 py-0.5 rounded border
            font-medium ${isAI ? color.badge
            : `${color.text ?? 'text-lime-400'}
               bg-lime-500/10 border-lime-500/30`}`}>
            {isAI ? '🤖 AI' : '👤 Human'}
          </span>
          <span className='text-sm font-medium text-[var(--text-primary)]'>
            {event.label}
          </span>
          <span className='text-xs font-mono text-blue-400'>
            {event.urs_id}
          </span>
        </div>
        <p className='text-xs text-[var(--text-secondary)] mb-1'>
          <span className='font-medium'>{event.actor}</span>
          {event.reviewer_role ? ` (${event.reviewer_role})` : ''}
          {' · '}{fmtTime(event.timestamp)}
        </p>
        {event.detail && (
          <p className='text-xs text-[var(--text-muted)] italic
            leading-relaxed line-clamp-2'>
            {event.detail}
          </p>
        )}
        {event.new_value && (
          <p className='mt-1 text-xs'>
            Changed to:{' '}
            <span className='font-semibold text-amber-400'>
              {event.new_value}
            </span>
          </p>
        )}
      </div>
    </motion.div>
  )
}

function TimelineTab({ events }) {
  const [filter, setFilter] = useState('all')
  const ursList = [...new Set(events.map(e => e.urs_id))].sort()

  const visible = filter === 'all'
    ? events
    : events.filter(e => e.urs_id === filter)

  return (
    <div className='space-y-4'>
      {/* URS filter */}
      <div className='flex gap-2 flex-wrap items-center'>
        <span className='text-xs text-[var(--text-muted)]'>Filter by URS:</span>
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded-full text-xs font-medium
            transition-all border
            ${filter === 'all'
              ? 'bg-[var(--accent)] text-white border-[var(--accent)]'
              : 'text-[var(--text-muted)] border-white/10'}`}
        >
          All
        </button>
        {ursList.map(u => (
          <button
            key={u}
            onClick={() => setFilter(u)}
            className={`px-3 py-1 rounded-full text-xs font-medium
              transition-all border
              ${filter === u
                ? 'bg-[var(--accent)] text-white border-[var(--accent)]'
                : 'text-[var(--text-muted)] border-white/10'}`}
          >
            {u}
          </button>
        ))}
      </div>

      {/* Legend */}
      <div className='flex gap-4 text-xs text-[var(--text-muted)]'>
        <span className='flex items-center gap-1.5'>
          <span className='w-2.5 h-2.5 rounded-full bg-purple-400' />
          AI Action
        </span>
        <span className='flex items-center gap-1.5'>
          <span className='w-2.5 h-2.5 rounded-full bg-lime-400' />
          Human Approved
        </span>
        <span className='flex items-center gap-1.5'>
          <span className='w-2.5 h-2.5 rounded-full bg-blue-400' />
          Human Overridden
        </span>
        <span className='flex items-center gap-1.5'>
          <span className='w-2.5 h-2.5 rounded-full bg-red-400' />
          Human Rejected
        </span>
      </div>

      {/* Timeline */}
      <div className='pt-2'>
        {visible.length === 0 ? (
          <div className='text-center py-12 text-[var(--text-muted)] text-sm'>
            No events found.
          </div>
        ) : (
          visible.map((e, i) => (
            <TimelineEvent key={`${e.decision_id}-${e.event_type}`}
              event={e} index={i} />
          ))
        )}
      </div>
    </div>
  )
}

// ── Tab 4: Transparency Report ────────────────────────────────────
function ReportTab({ decisions }) {
  const [selectedUrs, setSelectedUrs] = useState('')
  const ursList = [...new Set(decisions.map(d => d.urs_id))].sort()

  const chain = decisions.filter(d => d.urs_id === selectedUrs)
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className='space-y-4'>
      {/* URS selector */}
      <div className='flex gap-3 items-end'>
        <div className='flex-1'>
          <label className='block text-xs text-[var(--text-muted)] mb-1'>
            Select URS ID
          </label>
          <select
            value={selectedUrs}
            onChange={e => setSelectedUrs(e.target.value)}
            className='evolv-select w-full'
          >
            <option value=''>— Choose a URS —</option>
            {ursList.map(u => <option key={u} value={u}>{u}</option>)}
          </select>
        </div>
        {selectedUrs && (
          <button
            onClick={handlePrint}
            className='px-4 py-2 rounded-lg text-sm font-medium
              bg-[var(--accent)]/20 hover:bg-[var(--accent)]/30
              text-[var(--accent)] border border-[var(--accent)]/30
              transition-all whitespace-nowrap'
          >
            ↓ Download Report
          </button>
        )}
      </div>

      {/* Report body */}
      {selectedUrs && chain.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className='space-y-4'
        >
          {/* Report header */}
          <div className='rounded-xl border border-white/10 bg-white/2 p-5'>
            <div className='flex items-start justify-between mb-3'>
              <div>
                <h3 className='text-lg font-bold text-[var(--text-primary)]'>
                  AI Transparency Report
                </h3>
                <p className='text-sm text-[var(--text-muted)]'>
                  {selectedUrs} · Generated {fmtTime(new Date().toISOString())}
                </p>
              </div>
              <div className='text-right text-xs text-[var(--text-muted)]'>
                <p className='font-semibold text-[var(--text-primary)]'>EVOLV</p>
                <p>The Validation Factory</p>
                <p>21 CFR Part 11 Compliant</p>
              </div>
            </div>
            <div className='grid grid-cols-3 gap-3 text-center'>
              {[
                { label: 'AI Decisions', value: chain.length, color: 'text-purple-400' },
                { label: 'Human Reviews', value: chain.filter(d => d.reviewed_by).length, color: 'text-lime-400' },
                { label: 'Overrides', value: chain.filter(d => d.status === 'overridden').length, color: 'text-amber-400' },
              ].map(({ label, value, color }) => (
                <div key={label} className='rounded-lg bg-white/3
                  border border-white/8 p-3'>
                  <div className={`text-2xl font-bold ${color}`}>{value}</div>
                  <div className='text-xs text-[var(--text-muted)]'>{label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Decision chain */}
          {chain.map((d, i) => (
            <div
              key={d.decision_id}
              className={`rounded-xl border p-4 space-y-3
                ${STATUS_COLOR[d.status]?.border ?? 'border-white/10'}
                ${STATUS_COLOR[d.status]?.bg ?? 'bg-white/2'}`}
            >
              <div className='flex items-center gap-2'>
                <span className='text-xs font-mono text-[var(--text-muted)]'>
                  Step {i + 1}
                </span>
                <span className='text-sm font-medium text-[var(--text-primary)]'>
                  {TYPE_LABEL[d.decision_type] ?? d.decision_type}
                </span>
                <StatusPill status={d.status} />
              </div>

              <div className='grid grid-cols-2 gap-4 text-xs'>
                <div>
                  <p className='text-[var(--text-muted)] uppercase tracking-wide
                    text-[10px] mb-1'>AI Decision</p>
                  {Object.entries(d.ai_output).map(([k, v]) => (
                    <div key={k} className='flex gap-2 mb-0.5'>
                      <span className='text-[var(--text-muted)] capitalize'>
                        {k.replace(/_/g, ' ')}:
                      </span>
                      <span className='text-[var(--text-secondary)] font-mono'>
                        {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                      </span>
                    </div>
                  ))}
                  <div className='mt-1 flex gap-2'>
                    <span className='text-[var(--text-muted)]'>Agent:</span>
                    <span className='text-purple-400'>{d.agent_name}</span>
                  </div>
                  {d.confidence != null && (
                    <div className='flex gap-2'>
                      <span className='text-[var(--text-muted)]'>Confidence:</span>
                      <span className='text-[var(--text-secondary)]'>
                        {Math.round(d.confidence * 100)}%
                      </span>
                    </div>
                  )}
                </div>
                <div>
                  <p className='text-[var(--text-muted)] uppercase tracking-wide
                    text-[10px] mb-1'>Human Review</p>
                  {d.reviewed_by ? (
                    <>
                      <div className='flex gap-2 mb-0.5'>
                        <span className='text-[var(--text-muted)]'>Reviewer:</span>
                        <span className='text-[var(--text-primary)] font-medium'>
                          {d.reviewed_by}
                        </span>
                      </div>
                      <div className='flex gap-2 mb-0.5'>
                        <span className='text-[var(--text-muted)]'>Role:</span>
                        <span className='text-[var(--text-secondary)]'>
                          {d.reviewer_role}
                        </span>
                      </div>
                      <div className='flex gap-2 mb-0.5'>
                        <span className='text-[var(--text-muted)]'>Time:</span>
                        <span className='text-[var(--text-secondary)]'>
                          {fmtTime(d.reviewed_at)}
                        </span>
                      </div>
                      {d.new_value && (
                        <div className='flex gap-2'>
                          <span className='text-[var(--text-muted)]'>Overridden to:</span>
                          <span className='text-amber-400 font-semibold'>
                            {d.new_value}
                          </span>
                        </div>
                      )}
                    </>
                  ) : (
                    <span className='text-amber-400'>Awaiting review</span>
                  )}
                </div>
              </div>

              {/* AI Reasoning */}
              <div className='rounded-lg bg-black/20 border border-white/5 p-3'>
                <p className='text-[10px] uppercase tracking-wide
                  text-[var(--text-muted)] mb-1'>AI Reasoning</p>
                <p className='text-xs text-[var(--text-secondary)]
                  leading-relaxed'>{d.ai_reasoning}</p>
              </div>

              {/* Override reason */}
              {d.override_reason && (
                <div className='rounded-lg bg-amber-500/5 border
                  border-amber-500/20 p-3'>
                  <p className='text-[10px] uppercase tracking-wide
                    text-amber-400/60 mb-1'>Human Override Reason</p>
                  <p className='text-xs text-amber-200/80 italic leading-relaxed'>
                    "{d.override_reason}"
                  </p>
                </div>
              )}

              {/* GAMP5 reference */}
              {d.gamp5_reference && (
                <div className='rounded-lg bg-blue-500/5 border
                  border-blue-500/20 p-3'>
                  <p className='text-[10px] uppercase tracking-wide
                    text-blue-400/60 mb-1'>GAMP 5 Reference</p>
                  <p className='text-xs text-blue-200/70 italic leading-relaxed'>
                    {d.gamp5_reference}
                  </p>
                </div>
              )}
            </div>
          ))}

          {/* Compliance footer */}
          <div className='rounded-xl border border-white/10 bg-white/2
            p-4 text-center text-xs text-[var(--text-muted)]'>
            <p className='font-medium text-[var(--text-secondary)] mb-1'>
              21 CFR Part 11 Compliance Statement
            </p>
            <p>
              This report constitutes a complete electronic record of all
              AI decisions and human reviews for {selectedUrs}.
              All records are time-stamped, user-attributed, and maintained
              in an append-only audit trail per 21 CFR Part 11 § 11.10(e).
            </p>
            <p className='mt-2 font-mono text-[var(--text-muted)]/60'>
              EVOLV | The Validation Factory · Powered by WingstarTech Inc.
            </p>
          </div>
        </motion.div>
      )}

      {selectedUrs && chain.length === 0 && (
        <p className='text-sm text-[var(--text-muted)] text-center py-8'>
          No decisions found for {selectedUrs}.
        </p>
      )}
    </div>
  )
}

// ── Stats bar ─────────────────────────────────────────────────────
function StatsBar({ stats }) {
  if (!stats) return null
  const items = [
    { label: 'Pending Review',  value: stats.pending,    color: 'text-amber-400' },
    { label: 'Approved',        value: stats.approved,   color: 'text-lime-400' },
    { label: 'Overridden',      value: stats.overridden, color: 'text-blue-400' },
    { label: 'Rejected',        value: stats.rejected,   color: 'text-red-400' },
    { label: 'Review Rate',     value: `${stats.review_rate}%`,
      color: stats.review_rate >= 80 ? 'text-lime-400' : 'text-amber-400' },
  ]
  return (
    <div className='grid grid-cols-5 gap-3'>
      {items.map(({ label, value, color }) => (
        <div key={label}
          className='rounded-xl bg-white/3 border border-white/8
            p-3 text-center'>
          <div className={`text-2xl font-bold ${color}`}>{value}</div>
          <div className='text-xs text-[var(--text-muted)] mt-0.5'>{label}</div>
        </div>
      ))}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────
export default function Governance() {
  const [activeTab, setActiveTab] = useState('queue')
  const [decisions, setDecisions]   = useState([])
  const [overrides, setOverrides]   = useState([])
  const [timeline,  setTimeline]    = useState([])
  const [stats,     setStats]       = useState(null)
  const [loading,   setLoading]     = useState(true)
  const [error,     setError]       = useState(null)

  const fetchAll = useCallback(async () => {
    try {
      const [dRes, oRes, tRes, sRes] = await Promise.all([
        fetch(`${API}/governance/decisions`),
        fetch(`${API}/governance/overrides`),
        fetch(`${API}/governance/timeline`),
        fetch(`${API}/governance/stats`),
      ])
      if (!dRes.ok || !oRes.ok || !tRes.ok || !sRes.ok) {
        throw new Error('API error')
      }
      const [d, o, t, s] = await Promise.all([
        dRes.json(), oRes.json(), tRes.json(), sRes.json(),
      ])
      setDecisions(d.decisions ?? [])
      setOverrides(o.overrides ?? [])
      setTimeline(t.events ?? [])
      setStats(s)
      setError(null)
    } catch (e) {
      setError('Could not reach the EVOLV API. Start the server on port 8000.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 15000)
    return () => clearInterval(interval)
  }, [fetchAll])

  const handleReview = async (decisionId, body) => {
    const res = await fetch(
      `${API}/governance/review/${decisionId}`,
      {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(body),
      }
    )
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail ?? 'Review failed')
    }
    await fetchAll()   // refresh all data
  }

  const TABS = [
    { id: 'queue',    label: 'Decision Queue',
      badge: stats?.pending ? String(stats.pending) : null },
    { id: 'ledger',   label: 'Override Ledger',
      badge: overrides.length ? String(overrides.length) : null },
    { id: 'timeline', label: 'Audit Timeline' },
    { id: 'report',   label: 'Transparency Report' },
  ]

  return (
    <div className='h-full flex flex-col bg-[var(--bg-base)]
      text-[var(--text-primary)] overflow-hidden'>

      {/* Header */}
      <div className='px-6 pt-6 pb-4 border-b border-white/8 flex-shrink-0'>
        <div className='flex items-start justify-between mb-4'>
          <div>
            <h1 className='text-xl font-bold'>AI Governance Hub</h1>
            <p className='text-sm text-[var(--text-muted)] mt-0.5'>
              Human-in-the-Loop oversight for all AI decisions ·
              21 CFR Part 11 compliant
            </p>
          </div>
          <div className='flex items-center gap-2'>
            {stats?.pending > 0 && (
              <span className='flex items-center gap-1.5 px-3 py-1.5
                rounded-full bg-amber-500/15 text-amber-400 text-xs
                font-medium border border-amber-500/30 animate-pulse'>
                <span className='w-2 h-2 rounded-full bg-amber-400' />
                {stats.pending} pending
              </span>
            )}
            <button
              onClick={fetchAll}
              className='p-2 rounded-lg hover:bg-white/5 transition-colors
                text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              title='Refresh'
            >
              ↺
            </button>
          </div>
        </div>

        {/* Stats */}
        {stats && <StatsBar stats={stats} />}
      </div>

      {/* Tab bar */}
      <div className='px-6 pt-3 border-b border-white/8 flex-shrink-0'>
        <div className='flex gap-1'>
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`relative px-4 py-2 text-sm font-medium
                rounded-t-lg transition-all flex items-center gap-2
                ${activeTab === tab.id
                  ? 'text-[var(--text-primary)] bg-white/5 border-b-2'
                    + ' border-[var(--accent)]'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
                }`}
            >
              {tab.label}
              {tab.badge && (
                <span className='px-1.5 py-0.5 rounded-full text-xs
                  font-bold bg-amber-500 text-black leading-none'>
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className='flex-1 overflow-y-auto px-6 py-5'>
        {loading && (
          <div className='text-center py-16 text-[var(--text-muted)]'>
            Loading governance data…
          </div>
        )}
        {error && !loading && (
          <div className='rounded-xl border border-red-500/30 bg-red-500/10
            p-4 text-sm text-red-400 text-center'>
            {error}
          </div>
        )}
        {!loading && !error && (
          <AnimatePresence mode='wait'>
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.15 }}
            >
              {activeTab === 'queue' && (
                <QueueTab decisions={decisions} onReview={handleReview} />
              )}
              {activeTab === 'ledger' && (
                <LedgerTab overrides={overrides} />
              )}
              {activeTab === 'timeline' && (
                <TimelineTab events={timeline} />
              )}
              {activeTab === 'report' && (
                <ReportTab decisions={decisions} />
              )}
            </motion.div>
          </AnimatePresence>
        )}
      </div>
    </div>
  )
}
