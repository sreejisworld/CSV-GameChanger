/**
 * BlastRadiusPopover — shows on hover over any search result.
 * Displays: upstream risks, downstream test scripts, and
 * which releases this item spans.
 */
import { getBlastRadius } from '../data/traceabilityMap.js'

const STATUS_COLORS = {
  approved:   'text-green-400',
  in_review:  'text-yellow-400',
  draft:      'text-slate-400',
  failed:     'text-red-400',
  open_issue: 'text-orange-400',
}

const RISK_COLORS = {
  high:   'bg-red-900/60 text-red-300 border-red-700',
  medium: 'bg-yellow-900/60 text-yellow-300 border-yellow-700',
  low:    'bg-green-900/60 text-green-300 border-green-700',
}

export default function BlastRadiusPopover({ item, position }) {
  if (!item) return null

  const { upstream, downstream, crossRelease } = getBlastRadius(item.id)

  const hasIssue  = item.status === 'open_issue' || item.status === 'failed'
  const validated = item.status === 'approved' && item.humanApproved

  return (
    <div
      className="popover-arrow fixed z-50 w-72 bg-navy-700 border border-navy-500
                 rounded-xl shadow-2xl p-4 animate-fade-in pointer-events-none"
      style={{
        top:  Math.min(position.y - 20, window.innerHeight - 320),
        left: position.x + 14,
      }}
    >
      {/* Item header */}
      <div className="mb-3">
        <div className="flex items-start justify-between gap-2">
          <span className="text-white text-xs font-semibold leading-snug">
            {item.title?.slice(0, 60) || item.id}
            {(item.title?.length ?? 0) > 60 ? '…' : ''}
          </span>
          {hasIssue && (
            <span className="shrink-0 text-xs bg-red-900/50 text-red-400
                             border border-red-700 rounded px-1.5 py-0.5">
              ⚠ Issue
            </span>
          )}
          {validated && (
            <span className="shrink-0 text-xs bg-green-900/50 text-green-400
                             border border-green-700 rounded px-1.5 py-0.5">
              ✓ Valid
            </span>
          )}
        </div>
        <span className="font-mono text-xs text-muted">{item.id}</span>
        {item.openIssue && (
          <p className="mt-1 text-xs text-orange-400 leading-snug">{item.openIssue}</p>
        )}
        {item.failedTest && (
          <p className="mt-1 text-xs text-red-400 leading-snug">{item.failedTest}</p>
        )}
      </div>

      <div className="space-y-2.5 text-xs">
        {/* Upstream risks */}
        <Section label="⬆ Upstream — Business Risk Mitigated">
          {upstream.length ? upstream.map(r => (
            <div key={r.id} className="flex items-center gap-1.5">
              <span className={`shrink-0 text-[10px] border rounded px-1 ${RISK_COLORS[r.riskLevel] || ''}`}>
                {r.riskLevel?.toUpperCase()}
              </span>
              <span className="text-slate-300 truncate">{r.id} — {r.title?.slice(0, 35)}…</span>
            </div>
          )) : <Empty label="No upstream risks linked" />}
        </Section>

        {/* Downstream tests */}
        <Section label="⬇ Downstream — Test Scripts">
          {downstream.length ? downstream.map(t => (
            <div key={t.id} className="flex items-center gap-1.5">
              <span className={`font-mono ${STATUS_COLORS[t.status] || 'text-slate-400'}`}>{t.id}</span>
              <span className="text-slate-300 truncate">{t.title?.slice(0, 32)}…</span>
            </div>
          )) : <Empty label="No test scripts linked" />}
        </Section>

        {/* Cross-release */}
        <Section label="↔ Cross-Release Presence">
          {crossRelease?.length ? (
            <div className="flex flex-wrap gap-1">
              {crossRelease.map(r => (
                <span key={r} className="bg-navy-600 text-slate-300 rounded px-2 py-0.5 text-[11px]">
                  {r}
                </span>
              ))}
            </div>
          ) : <Empty label="Single release only" />}
        </Section>
      </div>

      {/* Heat score bar */}
      {item.heatScore != null && (
        <div className="mt-3 pt-2.5 border-t border-navy-600">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-muted">Impact Heat Score</span>
            <span className={`text-[11px] font-semibold ${
              item.heatScore > 75 ? 'text-red-400'
              : item.heatScore > 40 ? 'text-orange-400'
              : 'text-green-400'
            }`}>{item.heatScore}/100</span>
          </div>
          <div className="h-1.5 bg-navy-600 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${item.heatScore}%`,
                background: item.heatScore > 75
                  ? '#f87171'
                  : item.heatScore > 40
                  ? '#f97316'
                  : '#22c55e',
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function Section({ label, children }) {
  return (
    <div>
      <p className="text-[10px] font-semibold text-muted uppercase tracking-wide mb-1">
        {label}
      </p>
      <div className="space-y-1">{children}</div>
    </div>
  )
}

function Empty({ label }) {
  return <p className="text-[11px] text-navy-400 italic">{label}</p>
}
