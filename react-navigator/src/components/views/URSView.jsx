/**
 * URSView — SMART requirement editor.
 *
 * Data source (priority order):
 *  1. node.children  — items from the clicked URS folder (live tree)
 *  2. tree walk      — all URS items across all releases
 *  3. traceabilityMap fallback — demo data enrichment
 */
import { useState } from 'react'
import { getItemsByFolder } from '../../utils/treeHelpers.js'
import {
  requirements as mockReqs,
  getRequirement,
} from '../../data/traceabilityMap.js'

const STATUS_STYLES = {
  approved:   { dot: 'bg-success', label: 'Approved',   text: 'text-success' },
  in_review:  { dot: 'bg-warning', label: 'In Review',  text: 'text-warning' },
  draft:      { dot: 'bg-muted',   label: 'Draft',      text: 'text-muted'   },
  failed:     { dot: 'bg-danger',  label: 'Failed',     text: 'text-danger'  },
  open_issue: { dot: 'bg-danger',  label: 'Open Issue', text: 'text-danger'  },
}

const CRIT_STYLES = {
  high:   'bg-danger/15 text-danger border-danger/30',
  medium: 'bg-warning/15 text-warning border-warning/30',
  low:    'bg-success/15 text-success border-success/30',
}

/** Merge tree node with any matching mock enrichment data */
function enrich(treeNode) {
  const base = getRequirement(treeNode.id) || {}
  return {
    id:           treeNode.id,
    title:        treeNode.name,
    status:       treeNode.status       ?? base.status       ?? 'draft',
    aiGenerated:  treeNode.aiGenerated  ?? base.aiGenerated  ?? false,
    humanApproved:treeNode.humanApproved?? base.humanApproved?? false,
    heatScore:    treeNode.heatScore    ?? base.heatScore     ?? 0,
    criticality:  base.criticality || 'medium',
    regulation:   base.regulation  || treeNode.regulation || '',
    upstream:     base.upstream    || [],
    downstream:   base.downstream  || [],
    openIssue:    base.openIssue   || treeNode.openIssue,
    failedTest:   base.failedTest  || treeNode.failedTest,
  }
}

function RequirementCard({ req }) {
  const [expanded, setExpanded] = useState(false)
  const s = STATUS_STYLES[req.status] || STATUS_STYLES.draft

  return (
    <div className={`bg-glass-light border rounded-2xl overflow-hidden transition-colors
                     hover:bg-glass-mid
                     ${req.status === 'failed' || req.status === 'open_issue'
                       ? 'border-danger/25' : 'border-white/5'}`}>

      <div className="flex items-start gap-3 px-5 py-4 cursor-pointer select-none"
        onClick={() => setExpanded(v => !v)}>
        <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${s.dot}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-[10px] font-mono font-semibold text-accent">{req.id}</span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium
                              ${CRIT_STYLES[req.criticality]}`}>
              {req.criticality?.toUpperCase()}
            </span>
            {req.aiGenerated && !req.humanApproved && (
              <span className="text-[10px] bg-yellow-900/30 text-yellow-400
                               border border-yellow-700/40 rounded-full px-2 py-0.5">
                🤖 HITL
              </span>
            )}
          </div>
          <p className="text-sm text-white/85 leading-relaxed">{req.title}</p>
          {req.regulation && (
            <p className="text-[10px] text-muted mt-1">{req.regulation}</p>
          )}
        </div>
        <span className={`text-white/30 text-xs transition-transform shrink-0 mt-1
                          ${expanded ? 'rotate-180' : ''}`}>▾</span>
      </div>

      {expanded && (
        <div className="px-5 pb-4 border-t border-white/5">
          <div className="grid grid-cols-2 gap-3 mt-3">
            {[
              { label: 'Specific',   value: req.title },
              { label: 'Measurable', value: 'Quantifiable acceptance criteria defined' },
              { label: 'Achievable', value: 'Implementation method: Configured' },
              { label: 'Relevant',   value: req.regulation || 'Per GAMP 5 guidance' },
              { label: 'Time-bound', value: 'Target: current release' },
            ].map(f => (
              <div key={f.label}
                className="bg-navy-900/50 rounded-xl p-3 border border-white/5">
                <p className="text-[9px] uppercase tracking-widest text-muted mb-1">{f.label}</p>
                <p className="text-xs text-white/75 leading-snug">{f.value}</p>
              </div>
            ))}
            {req.downstream?.length > 0 && (
              <div className="bg-navy-900/50 rounded-xl p-3 border border-white/5">
                <p className="text-[9px] uppercase tracking-widest text-muted mb-1">
                  Linked Tests
                </p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {req.downstream.map(ts => (
                    <span key={ts}
                      className="text-[10px] font-mono bg-accent/10 text-accent
                                 border border-accent/20 rounded px-1.5 py-0.5">
                      {ts}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
          {(req.openIssue || req.failedTest) && (
            <div className="mt-3 flex items-start gap-2 p-3 rounded-xl
                            bg-danger/8 border border-danger/25">
              <span className="text-danger text-sm shrink-0">⚠</span>
              <p className="text-xs text-danger/90">{req.openIssue || req.failedTest}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function URSView({ node, tree }) {
  const [filter, setFilter] = useState('all')

  // Priority: clicked folder's children → walk tree → mock fallback
  const rawItems = node?.children?.length
    ? node.children
    : tree
      ? getItemsByFolder(tree, 'URS')
      : mockReqs

  const items = rawItems.length
    ? rawItems.map(enrich)
    : mockReqs.map(r => enrich({ ...r, name: r.title }))

  const filtered = filter === 'all'
    ? items
    : items.filter(r => r.status === filter)

  const releaseName = node?.name
    ? null
    : tree?.name || 'LabCore LIMS v4.2'

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-6">
        <p className="text-[10px] uppercase tracking-widest text-accent mb-1">
          User Requirements
        </p>
        <h2 className="text-xl font-bold text-white tracking-tight">
          URS — {releaseName || tree?.name || 'LabCore LIMS v4.2'}
        </h2>
        <p className="text-sm text-muted mt-1">
          {items.length} requirement{items.length !== 1 ? 's' : ''} · GAMP 5 §4.3
        </p>
      </div>

      <div className="flex items-center gap-2 mb-6 flex-wrap">
        {['all', 'approved', 'in_review', 'draft', 'failed', 'open_issue'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`text-[11px] px-3 py-1 rounded-full border transition-colors
              ${filter === f
                ? 'bg-accent text-white border-accent'
                : 'text-muted border-white/10 hover:border-white/25 hover:text-white/70'}`}>
            {f === 'all' ? `All (${items.length})` : STATUS_STYLES[f]?.label}
            {f !== 'all' && (
              <span className="ml-1.5 opacity-60">
                {items.filter(r => r.status === f).length}
              </span>
            )}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {filtered.map(req => <RequirementCard key={req.id} req={req} />)}
        {filtered.length === 0 && (
          <div className="text-center py-16 text-muted text-sm">
            No requirements match this filter.
          </div>
        )}
      </div>
    </div>
  )
}
