/**
 * SupplierView — Supplier / Vendor Assessment (GAMP 5 §3.2).
 *
 * Scorecard per supplier with GxP classification and qualification status.
 */

const SUPPLIERS = [
  {
    id: 'SUP-001',
    name: 'LabCore Technologies Inc.',
    product: 'LabCore LIMS v4.2',
    category: 'Category 4 — Configurable Software',
    gxpClass: 'Direct Impact',
    score: 92,
    status: 'Qualified',
    audited: '2025-11-14',
    nextAudit: '2026-11-14',
    criteria: [
      { label: 'ISO 9001:2015',           pass: true  },
      { label: '21 CFR Part 11 Controls', pass: true  },
      { label: 'SDLC Documentation',      pass: true  },
      { label: 'Change Control Process',  pass: true  },
      { label: 'Defect Management',       pass: true  },
      { label: 'Disaster Recovery',       pass: false },
    ],
  },
  {
    id: 'SUP-002',
    name: 'CloudSecure Ltd.',
    product: 'Hosting Infrastructure (AWS GovCloud)',
    category: 'Category 1 — Infrastructure',
    gxpClass: 'Indirect Impact',
    score: 78,
    status: 'Conditional',
    audited: '2025-08-03',
    nextAudit: '2026-08-03',
    criteria: [
      { label: 'SOC 2 Type II',            pass: true  },
      { label: 'FedRAMP Moderate',          pass: true  },
      { label: '21 CFR Part 11 Controls',  pass: false },
      { label: 'Backup & Recovery SLA',    pass: true  },
      { label: 'Penetration Test Report',  pass: false },
    ],
  },
  {
    id: 'SUP-003',
    name: 'IntegraMed Connectors',
    product: 'ERP Integration Middleware',
    category: 'Category 3 — Bespoke Software',
    gxpClass: 'Direct Impact',
    score: 55,
    status: 'Under Review',
    audited: '2025-06-20',
    nextAudit: '2026-06-20',
    criteria: [
      { label: 'ISO 9001:2015',           pass: false },
      { label: 'SDLC Documentation',      pass: false },
      { label: 'Change Control Process',  pass: true  },
      { label: '21 CFR Part 11 Controls', pass: false },
    ],
  },
]

const STATUS_STYLE = {
  Qualified:     'bg-success/15 text-success border-success/30',
  Conditional:   'bg-warning/15 text-warning border-warning/30',
  'Under Review':'bg-danger/15 text-danger border-danger/30',
}

function ScoreBar({ score }) {
  const color = score >= 85 ? '#22c55e' : score >= 65 ? '#f0a500' : '#f87171'
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700"
          style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="text-sm font-bold text-white w-10 text-right">{score}</span>
    </div>
  )
}

function SupplierCard({ sup }) {
  const passCount = sup.criteria.filter(c => c.pass).length
  return (
    <div className="bg-glass-light border border-white/5 rounded-2xl p-6">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono text-muted">{sup.id}</span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold
                              ${STATUS_STYLE[sup.status]}`}>
              {sup.status}
            </span>
          </div>
          <h3 className="text-sm font-semibold text-white">{sup.name}</h3>
          <p className="text-xs text-muted mt-0.5">{sup.product}</p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-[9px] uppercase tracking-widest text-muted">GxP Class</p>
          <p className="text-xs text-white/70">{sup.gxpClass}</p>
        </div>
      </div>

      {/* Score */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <p className="text-[10px] uppercase tracking-widest text-muted">Qualification Score</p>
          <p className="text-[10px] text-muted">{passCount}/{sup.criteria.length} criteria passed</p>
        </div>
        <ScoreBar score={sup.score} />
      </div>

      {/* Criteria checklist */}
      <div className="grid grid-cols-2 gap-1.5">
        {sup.criteria.map(c => (
          <div key={c.label}
            className="flex items-center gap-2 bg-navy-900/40 rounded-lg px-3 py-1.5">
            <span className={c.pass ? 'text-success text-xs' : 'text-danger text-xs'}>
              {c.pass ? '✓' : '✕'}
            </span>
            <span className="text-[11px] text-white/70">{c.label}</span>
          </div>
        ))}
      </div>

      {/* Audit dates */}
      <div className="flex items-center gap-6 mt-4 pt-4 border-t border-white/5">
        <div>
          <p className="text-[9px] uppercase tracking-widest text-muted">Last Audit</p>
          <p className="text-xs text-white/70">{sup.audited}</p>
        </div>
        <div>
          <p className="text-[9px] uppercase tracking-widest text-muted">Next Audit Due</p>
          <p className="text-xs text-white/70">{sup.nextAudit}</p>
        </div>
        <span className="ml-auto text-[10px] text-muted">{sup.category}</span>
      </div>
    </div>
  )
}

export default function SupplierView() {
  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-6">
        <p className="text-[10px] uppercase tracking-widest text-accent mb-1">
          Supplier Assessment
        </p>
        <h2 className="text-xl font-bold text-white tracking-tight">
          Vendor Qualification Register
        </h2>
        <p className="text-sm text-muted mt-1">
          GAMP 5 §3.2 · {SUPPLIERS.length} suppliers assessed
        </p>
      </div>
      <div className="space-y-4">
        {SUPPLIERS.map(s => <SupplierCard key={s.id} sup={s} />)}
      </div>
    </div>
  )
}
