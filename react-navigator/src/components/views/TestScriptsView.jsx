/**
 * TestScriptsView — CSA test script browser.
 *
 * Data source: live tree → Test Scripts folder children.
 * Enriched with traceabilityMap metadata where available.
 */
import { useState } from 'react'
import { getItemsByFolder } from '../../utils/treeHelpers.js'
import {
  testScripts as mockScripts,
  getTestScript,
} from '../../data/traceabilityMap.js'

const STATUS_STYLES = {
  approved:   { dot: 'bg-success', label: 'Approved',   text: 'text-success' },
  in_review:  { dot: 'bg-warning', label: 'In Review',  text: 'text-warning' },
  draft:      { dot: 'bg-muted',   label: 'Draft',      text: 'text-muted'   },
  failed:     { dot: 'bg-danger',  label: 'Failed',     text: 'text-danger'  },
  open_issue: { dot: 'bg-danger',  label: 'Open Issue', text: 'text-danger'  },
}

function enrich(treeNode) {
  const base = getTestScript(treeNode.id) || {}
  return {
    id:           treeNode.id,
    title:        treeNode.name,
    status:       treeNode.status        ?? base.status        ?? 'draft',
    aiGenerated:  treeNode.aiGenerated   ?? base.aiGenerated   ?? false,
    humanApproved:treeNode.humanApproved ?? base.humanApproved ?? false,
    heatScore:    treeNode.heatScore     ?? base.heatScore      ?? 0,
    verifies:     base.verifies || [],
    openIssue:    base.openIssue  || treeNode.openIssue,
    failedTest:   base.failedTest || treeNode.failedTest,
  }
}

const typeLabel = title =>
  title.startsWith('UAT') ? 'UAT'
  : title.startsWith('OQ') ? 'OQ'
  : 'Informal'

const typeStyle = title =>
  title.startsWith('UAT')
    ? 'bg-purple-900/30 text-purple-300 border-purple-700/40'
    : title.startsWith('OQ')
      ? 'bg-accent/15 text-accent border-accent/30'
      : 'bg-white/5 text-muted border-white/10'

function MockSteps({ script }) {
  const ref = script.verifies?.[0] || 'FR-1'
  const steps = [
    { type: 'Setup',     n: 1, title: 'Log in as System Owner',       result: '' },
    { type: 'Setup',     n: 2, title: 'Navigate to target module',     result: '' },
    { type: 'Execution', n: 1, title: `Verify ${ref} — Positive Case`, result: 'System responds within SLA; data persisted correctly.' },
    { type: 'Execution', n: 2, title: `Verify ${ref} — Negative Case`, result: 'System rejects invalid input with appropriate error.' },
    { type: 'Execution', n: 3, title: `Verify ${ref} — Edge Case`,     result: 'Boundary values handled without data corruption.' },
  ]
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="border-b border-white/5">
            {['Type','#','Step Title','Expected Result'].map(h => (
              <th key={h} className="px-3 py-2 text-left text-[10px] uppercase
                                     tracking-widest text-muted font-semibold whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {steps.map((s, i) => (
            <tr key={i} className="border-b border-white/3 hover:bg-white/3">
              <td className="px-3 py-2">
                <span className={`text-[10px] px-1.5 py-0.5 rounded border
                  ${s.type === 'Setup'
                    ? 'bg-white/5 text-muted border-white/10'
                    : 'bg-accent/10 text-accent border-accent/20'}`}>
                  {s.type}
                </span>
              </td>
              <td className="px-3 py-2 text-muted font-mono">{s.n}</td>
              <td className="px-3 py-2 text-white/75">{s.title}</td>
              <td className="px-3 py-2 text-white/50">{s.result || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ScriptCard({ script }) {
  const [expanded, setExpanded] = useState(false)
  const s = STATUS_STYLES[script.status] || STATUS_STYLES.draft

  return (
    <div className={`bg-glass-light border rounded-2xl overflow-hidden
                     hover:bg-glass-mid transition-colors
                     ${script.status === 'failed' || script.status === 'open_issue'
                       ? 'border-danger/25' : 'border-white/5'}`}>

      <div className="flex items-start gap-3 px-5 py-4 cursor-pointer select-none"
        onClick={() => setExpanded(v => !v)}>
        <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${s.dot}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-[10px] font-mono font-semibold text-purple-300">
              {script.id}
            </span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full border
                              ${typeStyle(script.title)}`}>
              {typeLabel(script.title)}
            </span>
            {script.aiGenerated && !script.humanApproved && (
              <span className="text-[10px] bg-yellow-900/30 text-yellow-400
                               border border-yellow-700/40 rounded-full px-2 py-0.5">
                🤖 HITL
              </span>
            )}
          </div>
          <p className="text-sm text-white/85 leading-relaxed">{script.title}</p>
          <div className="flex items-center gap-3 mt-1">
            <span className={`text-[10px] ${s.text}`}>{s.label}</span>
            {script.verifies?.length > 0 && (
              <span className="text-muted text-[10px]">
                Verifies: {script.verifies.join(', ')}
              </span>
            )}
          </div>
        </div>
        <span className={`text-white/30 text-xs transition-transform shrink-0 mt-1
                          ${expanded ? 'rotate-180' : ''}`}>▾</span>
      </div>

      {expanded && (
        <div className="border-t border-white/5">
          {(script.openIssue || script.failedTest) && (
            <div className="mx-5 mt-3 flex items-start gap-2 p-3 rounded-xl
                            bg-danger/8 border border-danger/25">
              <span className="text-danger text-sm shrink-0">⚠</span>
              <p className="text-xs text-danger/90">{script.openIssue || script.failedTest}</p>
            </div>
          )}
          <div className="px-5 py-3">
            <MockSteps script={script} />
          </div>
        </div>
      )}
    </div>
  )
}

export default function TestScriptsView({ node, tree }) {
  const [filter, setFilter] = useState('all')

  const rawItems = node?.children?.length
    ? node.children
    : tree
      ? getItemsByFolder(tree, 'Test Scripts')
      : mockScripts

  const items = rawItems.length
    ? rawItems.map(enrich)
    : mockScripts.map(s => enrich({ ...s, name: s.title }))

  const filtered = filter === 'all'
    ? items
    : items.filter(t => t.status === filter)

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-6">
        <p className="text-[10px] uppercase tracking-widest text-accent mb-1">
          Test Scripts
        </p>
        <h2 className="text-xl font-bold text-white tracking-tight">
          CSA Test Scripts — {tree?.name || 'LabCore LIMS v4.2'}
        </h2>
        <p className="text-sm text-muted mt-1">
          {items.length} script{items.length !== 1 ? 's' : ''} · OQ / UAT · GAMP 5 Appendix M3
        </p>
      </div>

      <div className="flex items-center gap-2 mb-6 flex-wrap">
        {['all', 'approved', 'in_review', 'draft', 'failed', 'open_issue'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`text-[11px] px-3 py-1 rounded-full border transition-colors
              ${filter === f
                ? 'bg-accent text-white border-accent'
                : 'text-muted border-white/10 hover:border-white/25'}`}>
            {f === 'all' ? `All (${items.length})` : STATUS_STYLES[f]?.label}
            {f !== 'all' && (
              <span className="ml-1.5 opacity-60">
                {items.filter(t => t.status === f).length}
              </span>
            )}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {filtered.map(ts => <ScriptCard key={ts.id} script={ts} />)}
        {filtered.length === 0 && (
          <div className="text-center py-16 text-muted text-sm">
            No test scripts match this filter.
          </div>
        )}
      </div>
    </div>
  )
}
