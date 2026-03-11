/**
 * App — root layout.
 *
 * Left:  ProjectNavigator sidebar (fixed 288px)
 * Right: Main content panel (scrollable)
 */
import ProjectNavigator from './components/ProjectNavigator.jsx'

const STATUS_META = {
  approved:   { label: 'Approved',   bg: 'bg-green-900/40',  text: 'text-green-400',  border: 'border-green-700' },
  in_review:  { label: 'In Review',  bg: 'bg-yellow-900/40', text: 'text-yellow-400', border: 'border-yellow-700' },
  draft:      { label: 'Draft',      bg: 'bg-slate-800',     text: 'text-slate-400',  border: 'border-slate-600' },
  failed:     { label: 'Failed',     bg: 'bg-red-900/40',    text: 'text-red-400',    border: 'border-red-700' },
  open_issue: { label: 'Open Issue', bg: 'bg-orange-900/40', text: 'text-orange-400', border: 'border-orange-700' },
}

export default function App() {
  return (
    <div className="flex h-screen bg-navy-900 text-white overflow-hidden">

      {/* ── Sidebar ── */}
      <ProjectNavigator />

      {/* ── Main content ── */}
      <main className="flex-1 overflow-y-auto">
        {/* Top bar */}
        <div className="sticky top-0 z-10 bg-navy-800/90 backdrop-blur
                        border-b border-navy-600 px-6 py-3
                        flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-white font-semibold text-sm">
              Project Navigator
            </h1>
            <span className="text-xs text-muted">
              LabCore LIMS v4.2 — GMP Validation Programme
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted">
            <span className="bg-navy-700 border border-navy-500 rounded px-2 py-1">
              21 CFR Part 11 ✓
            </span>
            <span className="bg-navy-700 border border-navy-500 rounded px-2 py-1">
              GAMP 5 ✓
            </span>
            <span className="bg-navy-700 border border-navy-500 rounded px-2 py-1">
              FDA AI Guidance 2026 ✓
            </span>
          </div>
        </div>

        {/* Welcome / dashboard */}
        <div className="p-6 space-y-6">

          {/* Programme summary */}
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: 'Active Releases',  value: '3', sub: 'v1.0 • v1.1 • v2.0', color: 'text-blue-400' },
              { label: 'Requirements',     value: '11', sub: '8 approved, 3 pending', color: 'text-white' },
              { label: 'Test Scripts',     value: '16', sub: '2 failed, 1 open issue', color: 'text-white' },
              { label: 'Open Issues',      value: '3', sub: 'Requires attention', color: 'text-red-400' },
            ].map(card => (
              <div key={card.label}
                className="bg-navy-700 border border-navy-600 rounded-xl p-4">
                <p className="text-xs text-muted mb-1">{card.label}</p>
                <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
                <p className="text-xs text-navy-400 mt-1">{card.sub}</p>
              </div>
            ))}
          </div>

          {/* Feature guide */}
          <div className="grid grid-cols-2 gap-4">
            <FeatureCard
              icon="🔍"
              title="Impact Search — Cmd+K"
              desc="Fuzzy search across all requirements, test scripts, and risks. Hover any result to see its full blast radius — upstream risks, downstream tests, and cross-release presence."
            />
            <FeatureCard
              icon="🔥"
              title="Impact Heatmap"
              desc="Toggle the heatmap in the sidebar to see which folders are 'hot'. Red = high-risk changes needing audit attention. Green = stable and validated."
            />
            <FeatureCard
              icon="🤖"
              title="Human-in-the-Loop (FDA AI §3.2)"
              desc="Every AI-generated item shows a pulsing 🤖 badge until a human approves it. Hover any item in the tree and click Approve to clear the badge and update the audit trail."
            />
            <FeatureCard
              icon="🔗"
              title="Dynamic Shadow Links"
              desc="When a requirement is added to the URS folder, EVOLV automatically creates a shadow link in the Traceability folder — keeping the bi-directional trace matrix live at all times."
            />
            <FeatureCard
              icon="📁"
              title="New Release — GAMP 5 Template"
              desc="Click + New Release in the sidebar. Choose which of the 7 GAMP 5 standard folders to include. The release is created instantly with the full folder structure."
            />
            <FeatureCard
              icon="⚠️"
              title="Impact Tagging"
              desc="Items with open issues glow red. Validated, human-approved items glow green. The heat score (0–100) on each popover shows relative impact severity."
            />
          </div>

          {/* Open issues alert */}
          <div className="bg-red-900/20 border border-red-700 rounded-xl p-4">
            <h3 className="text-red-400 font-semibold text-sm mb-3 flex items-center gap-2">
              <span>⚠️</span> Open Issues Requiring Attention
            </h3>
            <div className="space-y-2">
              {[
                {
                  id: 'URS-008 / TS-012',
                  issue: 'Temperature alert latency 78s — SLA breach (60s required)',
                  release: 'v1.0, v1.1',
                  ref: 'INC-2034',
                },
                {
                  id: 'URS-011 / TS-017',
                  issue: 'Chain-of-custody bypass found in negative test',
                  release: 'v1.1',
                  ref: 'DEF-441',
                },
                {
                  id: 'vp-003',
                  issue: 'Supplier Qualification Master awaiting QA review',
                  release: 'Governance',
                  ref: 'Rev 2',
                },
              ].map(iss => (
                <div key={iss.id}
                  className="flex items-start gap-3 bg-red-900/20 rounded-lg p-3
                             border border-red-800/50">
                  <div className="flex-1">
                    <span className="font-mono text-xs text-red-300">{iss.id}</span>
                    <p className="text-sm text-white mt-0.5">{iss.issue}</p>
                    <span className="text-xs text-red-400">
                      {iss.release} — {iss.ref}
                    </span>
                  </div>
                  <span className="shrink-0 text-xs bg-red-800/60 text-red-300
                                   border border-red-700 rounded px-2 py-1">
                    Blocked
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* FDA AI Guidance note */}
          <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-xl p-4">
            <h3 className="text-yellow-400 font-semibold text-sm mb-2 flex items-center gap-2">
              <span>🤖</span> FDA AI Guidance 2026 — Human Oversight Status
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              All AI-generated artefacts in this programme carry a{' '}
              <span className="text-yellow-400 font-semibold">🤖 Awaiting Review</span>{' '}
              badge until a qualified person approves them. This satisfies the{' '}
              <span className="text-white font-semibold">
                FDA Guidance on AI/ML-Based Software as Medical Device (January 2026)
              </span>{' '}
              requirement for human oversight of AI-assisted decisions.
              Hover any tree node and click <strong className="text-white">Approve</strong>{' '}
              to record sign-off in the audit trail.
            </p>
          </div>

        </div>
      </main>
    </div>
  )
}

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="bg-navy-700 border border-navy-600 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{icon}</span>
        <h3 className="text-white font-semibold text-sm">{title}</h3>
      </div>
      <p className="text-xs text-muted leading-relaxed">{desc}</p>
    </div>
  )
}
