/**
 * FRSView — Functional Requirements Specification.
 *
 * Derived from URS requirements; shows FR decomposition per requirement.
 */
import { useState } from 'react'
import { requirements } from '../../data/traceabilityMap.js'

// Generate deterministic FRs per requirement
function buildFRs(req) {
  return [
    {
      id: `FR-${req.id}-01`,
      statement: `The system shall ${req.title.toLowerCase().replace(/^the system shall /i, '')}`,
      ac: [
        `Given a valid user session, when the action is performed, then the system shall complete it within the defined SLA.`,
        `Given an invalid input, when the action is attempted, then the system shall reject it and display a compliant error.`,
      ],
    },
    {
      id: `FR-${req.id}-02`,
      statement: `The system shall log all ${req.id} events to the audit trail with a tamper-evident hash.`,
      ac: [
        `Given any state change, when it occurs, then an audit record shall be created within 1 second.`,
      ],
    },
  ]
}

function FRCard({ req }) {
  const [open, setOpen] = useState(false)
  const frs = buildFRs(req)

  return (
    <div className="bg-glass-light border border-white/5 rounded-2xl overflow-hidden
                    hover:bg-glass-mid transition-colors">
      <div className="flex items-start gap-3 px-5 py-4 cursor-pointer select-none"
        onClick={() => setOpen(v => !v)}>
        <span className="text-[10px] font-mono font-semibold text-lime mt-0.5 shrink-0">
          {req.id}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-white/85 leading-relaxed">{req.title}</p>
          <p className="text-[10px] text-muted mt-0.5">{frs.length} functional requirements</p>
        </div>
        <span className={`text-white/30 text-xs transition-transform shrink-0 mt-1
                          ${open ? 'rotate-180' : ''}`}>▾</span>
      </div>

      {open && (
        <div className="border-t border-white/5 px-5 py-4 space-y-4">
          {frs.map(fr => (
            <div key={fr.id} className="bg-navy-900/40 rounded-xl p-4 border border-white/5">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[10px] font-mono text-lime font-semibold">{fr.id}</span>
              </div>
              <p className="text-xs text-white/80 mb-3 leading-relaxed">{fr.statement}</p>
              <p className="text-[9px] uppercase tracking-widest text-muted mb-2">
                Acceptance Criteria
              </p>
              <ul className="space-y-1.5">
                {fr.ac.map((ac, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-lime text-[10px] shrink-0 mt-0.5">›</span>
                    <span className="text-xs text-white/60 leading-snug">{ac}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function FRSView() {
  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-6">
        <p className="text-[10px] uppercase tracking-widest text-accent mb-1">
          Functional Specifications
        </p>
        <h2 className="text-xl font-bold text-white tracking-tight">
          FRS — LabCore LIMS v4.2
        </h2>
        <p className="text-sm text-muted mt-1">
          Derived from {requirements.length} URS requirements · GAMP 5 §6
        </p>
      </div>
      <div className="space-y-3">
        {requirements.map(req => <FRCard key={req.id} req={req} />)}
      </div>
    </div>
  )
}
