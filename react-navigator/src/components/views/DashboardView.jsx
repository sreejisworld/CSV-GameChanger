/**
 * DashboardView — live project overview.
 *
 * Counts are derived from the live tree (API or demo).
 * Falls back gracefully when tree is empty.
 */
import { getItemsByFolder, getReleases, countByStatus } from '../../utils/treeHelpers.js'

function ProgressRing({ pct, size = 56, stroke = 5, color = '#3b82f6' }) {
  const r    = (size - stroke) / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (pct / 100) * circ
  return (
    <svg width={size} height={size} className="rotate-[-90deg]">
      <circle cx={size/2} cy={size/2} r={r}
        fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={stroke} />
      <circle cx={size/2} cy={size/2} r={r}
        fill="none" stroke={color} strokeWidth={stroke}
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.8s cubic-bezier(0.22,1,0.36,1)' }}
      />
    </svg>
  )
}

function KpiCard({ label, stats, icon, ringColor }) {
  const pct = stats.total ? Math.round((stats.approved / stats.total) * 100) : 0
  return (
    <div className="bg-glass-light border border-white/5 rounded-2xl p-5
                    hover:bg-glass-mid transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-[10px] uppercase tracking-widest text-muted">{label}</p>
          <p className="text-2xl font-bold text-white mt-1">{stats.total}</p>
        </div>
        <span className="text-xl">{icon}</span>
      </div>
      <div className="flex items-center gap-3">
        <ProgressRing pct={pct} color={ringColor} />
        <div>
          <p className="text-sm font-semibold text-white">{pct}%</p>
          <p className="text-[11px] text-muted">{stats.approved} approved</p>
          {(stats.failed + stats.open_issue) > 0 && (
            <p className="text-[10px] text-danger">
              {stats.failed + stats.open_issue} issue{(stats.failed + stats.open_issue) > 1 ? 's' : ''}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

function PhaseBar({ label, pct, status }) {
  const color = status === 'done'   ? '#32CD32'
    : status === 'active' ? '#3b82f6'
    : 'rgba(255,255,255,0.1)'
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-white/70">{label}</span>
        <span className="text-[10px] text-muted">{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  )
}

export default function DashboardView({ tree }) {
  const reqs   = getItemsByFolder(tree, 'URS')
  const tests  = getItemsByFolder(tree, 'Test Scripts')
  const risks  = getItemsByFolder(tree, 'Risk Matrix')
  const releases = getReleases(tree)

  const reqStats  = countByStatus(reqs)
  const testStats = countByStatus(tests)
  const riskStats = countByStatus(risks)

  const highRisks = risks.filter(r => r.riskLevel === 'high').length

  // Open issues across reqs + tests
  const openIssues = [
    ...reqs.filter(r  => r.status === 'open_issue' || r.status === 'failed'),
    ...tests.filter(t => t.status === 'open_issue' || t.status === 'failed'),
  ]

  // Phase progress derived from stats
  const phases = [
    { label: 'URS',          pct: reqStats.total  ? Math.round(reqStats.approved  / reqStats.total  * 100) : 0, status: reqStats.approved  === reqStats.total  && reqStats.total  > 0 ? 'done' : 'active' },
    { label: 'Risk Matrix',  pct: riskStats.total ? Math.round(riskStats.approved / riskStats.total * 100) : 0, status: riskStats.approved === riskStats.total && riskStats.total > 0 ? 'done' : 'active' },
    { label: 'Test Scripts', pct: testStats.total ? Math.round(testStats.approved / testStats.total * 100) : 0, status: testStats.approved === testStats.total && testStats.total > 0 ? 'done' : 'active' },
    { label: 'Traceability', pct: reqStats.total  ? Math.round(reqStats.approved  / reqStats.total  * 100 * 0.6) : 0, status: 'active' },
    { label: 'VSR',          pct: 0, status: 'todo' },
  ]

  const projectName = tree?.name || 'LabCore LIMS v4.2'

  return (
    <div className="p-8 max-w-4xl mx-auto">

      {/* Hero */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full bg-lime animate-pulse-dot inline-block" />
          <span className="text-[10px] uppercase tracking-widest text-lime font-semibold">
            Live Validation Status
          </span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">{projectName}</h1>
        <div className="flex items-center gap-3 mt-1">
          <p className="text-muted text-sm">GMP Validated System · 21 CFR Part 11 · GAMP 5 Category 4</p>
          {releases.length > 0 && (
            <span className="text-[10px] text-white/30">
              {releases.length} release{releases.length > 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <KpiCard label="Requirements" stats={reqStats}  icon="📋" ringColor="#3b82f6" />
        <KpiCard label="Test Scripts" stats={testStats} icon="🧪" ringColor="#32CD32" />
        <KpiCard
          label="Risk Items"
          stats={{ ...riskStats, approved: riskStats.total - highRisks }}
          icon="⚠️" ringColor="#f87171"
        />
      </div>

      {/* Phase + open issues */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="bg-glass-light border border-white/5 rounded-2xl p-5">
          <p className="text-[10px] uppercase tracking-widest text-muted mb-4">
            Validation Phase Progress
          </p>
          <div className="space-y-3">
            {phases.map(p => <PhaseBar key={p.label} {...p} />)}
          </div>
        </div>

        <div className="bg-glass-light border border-white/5 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <p className="text-[10px] uppercase tracking-widest text-muted">Open Issues</p>
            <span className="text-[10px] bg-danger/15 text-danger border border-danger/30
                             rounded-full px-2 py-0.5 font-semibold">
              {openIssues.length} items
            </span>
          </div>
          {openIssues.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-24 text-muted text-sm">
              <span className="text-success text-2xl mb-2">✓</span>
              No open issues
            </div>
          ) : (
            <div className="space-y-2.5">
              {openIssues.slice(0, 5).map(item => (
                <div key={item.id}
                  className="flex items-start gap-2 p-2.5 rounded-lg
                             bg-danger/5 border border-danger/15">
                  <span className="text-danger text-sm shrink-0 mt-0.5">
                    {item.status === 'failed' ? '✕' : '!'}
                  </span>
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold text-white/90 font-mono">
                      {item.id}
                    </p>
                    <p className="text-[10px] text-white/50 leading-snug mt-0.5 line-clamp-2">
                      {item.name}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Releases row */}
      {releases.length > 0 && (
        <div className="mb-8">
          <p className="text-[10px] uppercase tracking-widest text-muted mb-3">Releases</p>
          <div className="flex gap-3 flex-wrap">
            {releases.map(rel => {
              const statusColor = rel.status === 'Released'    ? 'text-success border-success/30 bg-success/5'
                : rel.status === 'In Progress' ? 'text-warning border-warning/30 bg-warning/5'
                : 'text-muted border-white/10 bg-white/3'
              return (
                <div key={rel.id}
                  className={`px-4 py-2.5 rounded-xl border text-xs font-medium ${statusColor}`}>
                  <p className="font-semibold">{rel.name}</p>
                  <p className="text-[10px] opacity-60 mt-0.5">{rel.status}</p>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Compliance badges */}
      <div className="flex items-center gap-3 flex-wrap">
        {[
          { label: '21 CFR Part 11', ok: true },
          { label: 'GAMP 5 Category 4', ok: true },
          { label: 'FDA AI Guidance 2026', ok: true },
          { label: 'HITL Review', warn: openIssues.length > 0 },
        ].map(b => (
          <span key={b.label}
            className={`text-[10px] rounded-full px-3 py-1 border font-medium
              ${b.ok
                ? 'bg-success/10 text-success border-success/30'
                : b.warn
                  ? 'bg-warning/10 text-warning border-warning/30'
                  : 'bg-white/5 text-muted border-white/10'}`}>
            {b.ok ? '✓ ' : b.warn ? '⏳ ' : ''}{b.label}
          </span>
        ))}
      </div>
    </div>
  )
}
