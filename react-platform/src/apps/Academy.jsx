/** Academy — Learning hub placeholder. */
const COURSES = [
  {
    title: 'GAMP 5 Foundations',
    icon: '📖',
    level: 'Beginner',
    modules: 8,
    color: '#007FFF',
    desc: 'Risk-based approach to computer system validation. Category 3–5 classification, IQ/OQ/PQ lifecycle.',
  },
  {
    title: '21 CFR Part 11 Compliance',
    icon: '⚖️',
    level: 'Intermediate',
    modules: 6,
    color: '#32CD32',
    desc: 'Electronic records, audit trails, e-signatures, and access controls for FDA-regulated systems.',
  },
  {
    title: 'CSA — Computer Software Assurance',
    icon: '🧪',
    level: 'Intermediate',
    modules: 5,
    color: '#a855f7',
    desc: 'FDA\'s modern approach: risk-based, outcome-focused validation replacing scripted testing where appropriate.',
  },
  {
    title: 'EVOLV AI Engine — Advanced',
    icon: '🤖',
    level: 'Advanced',
    modules: 10,
    color: '#32CD32',
    desc: 'Mastering EVOLV\'s AI agents: RequirementArchitect, SentinelImpactAgent, VerificationAgent, and DeltaAgent.',
  },
  {
    title: 'FDA AI Guidance 2026',
    icon: '🛡️',
    level: 'Advanced',
    modules: 4,
    color: '#f59e0b',
    desc: 'Human-in-the-Loop requirements, HITL documentation, and audit trail requirements for AI/ML-assisted validation.',
  },
]

export default function Academy() {
  return (
    <div className="h-full overflow-y-auto bg-bg-base">
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-white font-bold text-xl">Academy</h1>
            <span className="text-[10px] px-2 py-1 rounded-full border
                             border-border-base text-text-muted">
              Coming Soon
            </span>
          </div>
          <p className="text-text-secondary text-sm">
            GAMP 5 training, 21 CFR Part 11 certification, and EVOLV guided walkthroughs.
          </p>
          <div className="neon-sep mt-3" />
        </div>

        {/* Course grid */}
        <div className="grid grid-cols-2 gap-4">
          {COURSES.map(c => (
            <div key={c.title}
              className="glass rounded-xl p-5 cursor-not-allowed opacity-70
                         hover:opacity-90 transition-opacity">
              <div className="flex items-start gap-3 mb-3">
                <span className="text-3xl">{c.icon}</span>
                <div>
                  <h3 className="text-white font-semibold text-sm">{c.title}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[9px] px-1.5 py-0.5 rounded border
                                     border-border-base text-text-muted">
                      {c.level}
                    </span>
                    <span className="text-text-muted text-[10px]">
                      {c.modules} modules
                    </span>
                  </div>
                </div>
              </div>
              <p className="text-text-secondary text-xs leading-relaxed">{c.desc}</p>
              <div className="mt-3 h-1 rounded-full bg-bg-hover overflow-hidden">
                <div className="h-full w-0 rounded-full"
                     style={{ background: c.color }} />
              </div>
              <p className="text-text-muted text-[10px] mt-1">Not started</p>
            </div>
          ))}
        </div>

        <p className="text-center text-text-muted text-xs mt-8">
          Full Academy launching with EVOLV Enterprise v2.1 — Q3 2026.
        </p>
      </div>
    </div>
  )
}
