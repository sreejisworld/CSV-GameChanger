/**
 * Retire — Lifecycle Phase 8: Controlled Decommissioning
 *
 * Sprint 18.1: rebuilt from a stub to a full Decommissioning
 * Checklist grounded in 21 CFR Part 11 §11.10(c) (record retention),
 * EU GMP Annex 11 §17 (data archiving), and GAMP 5 Appendix M11
 * (system retirement). The checklist tracks the actions a regulated
 * customer must complete BEFORE turning a validated system off.
 *
 * UX rules:
 *   - Phase is locked until the system has been formally released
 *     (releaseData.released === true).
 *   - When unlocked, each checklist item is a regulated action with
 *     a citation chip and a hover tooltip explaining "why".
 *   - The "Mark as Decommissioned" sign-off only enables when every
 *     mandatory item is complete.
 *   - "Generate Decommissioning Report" is wired but PDF export
 *     is deferred to Sprint 19 (Validation Deliverables Pack).
 *
 * :requirement: URS-24.2 - Decommissioning checklist grounded in
 *               21 CFR Part 11 §11.10(c) retention requirements.
 * :requirement: URS-24.3 - Phase locked until system is in active
 *               validated/released state.
 */
import { useState, useMemo } from 'react'
import { useAppStore } from '../store/useAppStore.js'

// ── Checklist taxonomy ────────────────────────────────────────────
// Each entry has:
//   id        — stable key for retireData.checklist[id]
//   label     — checkbox label
//   detail    — long-form description
//   citation  — { reg, section } shown as a hover chip
//   why       — regulator-friendly rationale (tooltip)
//   mandatory — block sign-off when false
const DECOM_CHECKLIST = [
  {
    id: 'data-migration',
    label: 'Data migration plan defined',
    detail: 'A signed plan describes which records move to the '
      + 'successor system, which are archived in read-only form, '
      + 'and the validation evidence that data integrity was '
      + 'preserved during transfer.',
    citation: { reg: 'GAMP 5 (2nd Ed.)', section: 'Appendix M11' },
    why: 'Per GAMP 5 Appendix M11, a system retirement plan must '
      + 'identify all GxP data, its destination, and the means of '
      + 'demonstrating integrity post-migration.',
    mandatory: true,
  },
  {
    id: 'archival-period',
    label: 'Archival period defined per 21 CFR Part 11 §11.10(c)',
    detail: 'Records will be retained for the duration required by '
      + 'predicate rules (typically 7–10 years for pharmaceutical '
      + 'manufacturing; longer for medical device DHRs).',
    citation: { reg: '21 CFR Part 11', section: '§11.10(c)' },
    why: 'Persons who use closed systems shall employ procedures '
      + '"to protect records to enable their accurate and ready '
      + 'retrieval throughout the records retention period."',
    mandatory: true,
  },
  {
    id: 'integrity-assessment',
    label: 'Final data-integrity assessment scheduled',
    detail: 'A formal final read of the audit trail, e-signature '
      + 'log, and migrated data set will be performed and the '
      + 'results signed by QA before access is revoked.',
    citation: { reg: 'EU GMP Annex 11', section: '§17 (Archiving)' },
    why: 'Annex 11 requires that archived data shall be checked '
      + 'for accessibility, readability, and integrity throughout '
      + 'the retention period.',
    mandatory: true,
  },
  {
    id: 'stakeholder-notification',
    label: 'Stakeholder notifications sent',
    detail: 'Process owners, end users, IT operations, and external '
      + 'auditors have been notified of the decommissioning '
      + 'schedule and the location of archived records.',
    citation: { reg: 'GAMP 5 (2nd Ed.)', section: 'Appendix M11' },
    why: 'Coordination with end users prevents loss of access at '
      + 'cut-over and ensures the audit trail can still be '
      + 'produced if requested by inspectors.',
    mandatory: true,
  },
  {
    id: 'access-revocation',
    label: 'System access revocation plan signed',
    detail: 'A documented plan removes user accounts, service '
      + 'accounts, and integration credentials in a controlled '
      + 'order. Audit-trail-write access is revoked LAST so the '
      + 'final log is captured.',
    citation: { reg: '21 CFR Part 11', section: '§11.10(d)' },
    why: 'Limiting system access to authorised individuals is a '
      + 'closed-system requirement that applies through the very '
      + 'last write to the audit trail.',
    mandatory: true,
  },
  {
    id: 'audit-trail-preserved',
    label: 'Audit trail preservation confirmed',
    detail: 'The complete, time-stamped, computer-generated audit '
      + 'trail is exported to the validated archive in a format '
      + 'that can be regenerated as a human-readable record on '
      + 'demand.',
    citation: { reg: '21 CFR Part 11', section: '§11.10(e)' },
    why: 'The audit trail must remain reviewable for as long as '
      + 'the underlying records are retained.',
    mandatory: true,
  },
  {
    id: 'decom-report',
    label: 'Decommissioning Report generated and signed',
    detail: 'The summary report records the date of decommissioning, '
      + 'the responsible signers, the disposition of all GxP '
      + 'records, and the location of the archive.',
    citation: { reg: 'GAMP 5 (2nd Ed.)', section: 'Appendix M11' },
    why: 'A signed Retirement / Decommissioning Report is the '
      + 'final validation deliverable for a regulated system.',
    mandatory: true,
  },
]

// ── Citation chip ────────────────────────────────────────────────
function CitationChip({ reg, section }) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full
                 text-[10px] font-medium border whitespace-nowrap"
      style={{
        background: 'rgba(0,127,255,0.08)',
        borderColor: 'rgba(0,127,255,0.30)',
        color: '#007FFF',
      }}
    >
      {reg} <span className="opacity-70">{section}</span>
    </span>
  )
}

// ── Single checklist row ─────────────────────────────────────────
function ChecklistRow({ item, checked, onToggle, locked }) {
  return (
    <div className={`
      group rounded-xl border p-4 transition-colors
      ${checked
        ? 'border-lime-DEFAULT/30 bg-lime-DEFAULT/5'
        : 'border-border-base bg-bg-card hover:border-border-bright'}
      ${locked ? 'opacity-50' : ''}
    `}>
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        <button
          onClick={() => !locked && onToggle(!checked)}
          disabled={locked}
          aria-checked={checked}
          role="checkbox"
          className={`
            shrink-0 w-5 h-5 rounded border-2 mt-0.5
            flex items-center justify-center transition-colors
            ${checked
              ? 'bg-lime-DEFAULT border-lime-DEFAULT text-bg-base'
              : 'bg-transparent border-border-bright '
                + 'hover:border-text-secondary'}
            ${locked ? 'cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          {checked && (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="3" strokeLinecap="round"
              strokeLinejoin="round" className="w-3 h-3">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          )}
        </button>

        {/* Body */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-3
                          flex-wrap mb-1">
            <span className={`text-sm font-semibold
              ${checked ? 'text-lime-DEFAULT' : 'text-text-primary'}`}>
              {item.label}
            </span>
            <CitationChip {...item.citation} />
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            {item.detail}
          </p>
          <p className="text-[11px] text-text-muted leading-relaxed
                        mt-2 italic border-l-2 border-border-base pl-2">
            {item.why}
          </p>
        </div>
      </div>
    </div>
  )
}

// ── Locked-state hero (unreleased system) ─────────────────────────
function LockedHero({ projectName }) {
  return (
    <div className="rounded-2xl border border-border-base bg-bg-card
                    p-8 text-center max-w-2xl mx-auto">
      <div className="w-14 h-14 mx-auto rounded-2xl bg-bg-base
                      border border-border-bright flex items-center
                      justify-center text-3xl mb-4">
        🔒
      </div>
      <h2 className="text-text-primary font-semibold text-lg mb-2">
        Decommissioning is locked
      </h2>
      <p className="text-text-secondary text-sm leading-relaxed mb-4">
        Retirement can only begin once <span className="font-semibold
        text-text-primary">{projectName || 'this project'}</span> has
        been formally released. Complete the Release phase first —
        the multi-approver sign-off establishes the system is in
        active validated state, which is the trigger for the
        regulated decommissioning workflow.
      </p>
      <div className="inline-flex items-center gap-2 px-3 py-1.5
                      rounded-full bg-bg-base border border-border-base">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
        <span className="text-[10px] text-text-muted uppercase
                         tracking-widest">
          Locked — requires released state
        </span>
      </div>
    </div>
  )
}

// ── Already-decommissioned hero ───────────────────────────────────
function DecommissionedHero({ retireData, projectName }) {
  const ts = retireData.decommissionedAt
    ? new Date(retireData.decommissionedAt).toLocaleString()
    : ''
  return (
    <div className="rounded-2xl border border-lime-DEFAULT/30
                    bg-lime-DEFAULT/5 p-6 max-w-2xl mx-auto
                    text-center">
      <div className="w-12 h-12 mx-auto rounded-2xl bg-bg-base
                      border border-lime-DEFAULT/40 flex items-center
                      justify-center text-2xl mb-3">
        ✓
      </div>
      <h2 className="text-lime-DEFAULT font-semibold text-base mb-2">
        System decommissioned
      </h2>
      <p className="text-text-secondary text-xs leading-relaxed mb-3">
        <span className="text-text-primary font-medium">
          {projectName}
        </span>{' '}was formally retired by{' '}
        <span className="text-text-primary font-medium">
          {retireData.decommissionedBy || 'a system administrator'}
        </span>{' '}on{' '}
        <span className="text-text-primary font-medium">
          {ts}
        </span>.
      </p>
      <p className="text-[11px] text-text-muted">
        Archived records remain retrievable per
        21 CFR Part 11 §11.10(c).
      </p>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────
export default function Retire() {
  const { planData, releaseData, retireData,
          setRetireCheck, setRetireNotes,
          markDecommissioned, setPhaseComplete } = useAppStore()

  const released  = releaseData.released
  const retired   = Boolean(retireData.decommissionedAt)
  const checklist = retireData.checklist ?? {}

  const [signerName, setSignerName] = useState('')
  const [showConfirm, setShowConfirm] = useState(false)

  const allMandatoryDone = useMemo(
    () => DECOM_CHECKLIST
      .filter(i => i.mandatory)
      .every(i => Boolean(checklist[i.id])),
    [checklist],
  )

  const completedCount = DECOM_CHECKLIST
    .filter(i => Boolean(checklist[i.id])).length
  const totalCount = DECOM_CHECKLIST.length

  const handleSignOff = () => {
    if (!allMandatoryDone) return
    if (!signerName.trim()) {
      alert('Please enter a signer name to attest the '
            + 'decommissioning.')
      return
    }
    setShowConfirm(true)
  }

  const confirmSignOff = () => {
    markDecommissioned(signerName.trim())
    setPhaseComplete('retire')
    setShowConfirm(false)
  }

  const handleGenerateReport = () => {
    // Sprint 19 will wire this to a PDF generator.
    alert(
      'Decommissioning Report generation will be available in '
      + 'Sprint 19 (Validation Deliverables Pack). For now, the '
      + 'checklist + signed attestation is captured in the audit '
      + 'trail.',
    )
  }

  // Locked → released yet?
  if (!released && !retired) {
    return (
      <div className="h-full overflow-y-auto bg-bg-base">
        <div className="max-w-5xl mx-auto px-6 py-10">
          <Header />
          <div className="mt-8">
            <LockedHero projectName={planData.projectName} />
          </div>
          <ReadOnlyChecklistPreview />
        </div>
      </div>
    )
  }

  // Already decommissioned?
  if (retired) {
    return (
      <div className="h-full overflow-y-auto bg-bg-base">
        <div className="max-w-5xl mx-auto px-6 py-10">
          <Header />
          <div className="mt-8 space-y-6">
            <DecommissionedHero
              retireData={retireData}
              projectName={planData.projectName}
            />
            <div className="rounded-xl border border-border-base
                            bg-bg-card p-5">
              <h3 className="text-sm font-semibold text-text-primary
                             mb-3">
                Final checklist record
              </h3>
              <div className="space-y-2">
                {DECOM_CHECKLIST.map(i => (
                  <ChecklistRow
                    key={i.id}
                    item={i}
                    checked={Boolean(checklist[i.id])}
                    onToggle={() => {}}
                    locked={true}
                  />
                ))}
              </div>
              {retireData.notes && (
                <div className="mt-4 p-3 rounded-lg bg-bg-base
                                border border-border-base">
                  <p className="text-[10px] uppercase tracking-widest
                                text-text-muted font-semibold mb-1">
                    Notes
                  </p>
                  <p className="text-xs text-text-secondary
                                whitespace-pre-wrap">
                    {retireData.notes}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Active workflow
  return (
    <div className="h-full overflow-y-auto bg-bg-base">
      <div className="max-w-5xl mx-auto px-6 py-10">
        <Header />

        {/* Progress strip */}
        <div className="mt-6 mb-6 flex items-center gap-4 rounded-xl
                        border border-border-base bg-bg-card p-4">
          <div className="shrink-0">
            <div className="text-[10px] uppercase tracking-widest
                            text-text-muted font-semibold mb-1">
              Checklist progress
            </div>
            <div className="text-2xl font-bold text-text-primary
                            leading-none">
              {completedCount}<span className="text-text-muted text-base">
                {' '}/ {totalCount}
              </span>
            </div>
          </div>
          <div className="flex-1 h-2 rounded-full bg-bg-base
                          border border-border-base overflow-hidden">
            <div
              className="h-full bg-lime-DEFAULT transition-all"
              style={{
                width: `${(completedCount / totalCount) * 100}%`,
              }}
            />
          </div>
          {allMandatoryDone && (
            <span className="text-[11px] font-semibold text-lime-DEFAULT
                             border border-lime-DEFAULT/30 bg-lime-dim
                             rounded-full px-3 py-1 shrink-0">
              ✓ Ready to sign
            </span>
          )}
        </div>

        {/* Checklist */}
        <div className="space-y-3 mb-6">
          {DECOM_CHECKLIST.map(item => (
            <ChecklistRow
              key={item.id}
              item={item}
              checked={Boolean(checklist[item.id])}
              onToggle={v => setRetireCheck(item.id, v)}
              locked={false}
            />
          ))}
        </div>

        {/* Notes */}
        <div className="rounded-xl border border-border-base
                        bg-bg-card p-4 mb-6">
          <label className="text-[10px] uppercase tracking-widest
                            text-text-muted font-semibold block mb-2">
            Decommissioning notes
          </label>
          <textarea
            value={retireData.notes ?? ''}
            onChange={e => setRetireNotes(e.target.value)}
            placeholder="Add archival location, retention period,
              successor system, special considerations…"
            rows={3}
            className="evolv-input w-full text-xs"
          />
        </div>

        {/* Sign-off + report */}
        <div className="rounded-2xl border border-border-base
                        bg-bg-card p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-1">
            Final attestation
          </h3>
          <p className="text-xs text-text-muted mb-4">
            By signing, you attest that all mandatory decommissioning
            steps are complete and that records are retained per
            21 CFR Part 11 §11.10(c).
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              value={signerName}
              onChange={e => setSignerName(e.target.value)}
              placeholder="Signer name (e.g. Jane Smith, QA Lead)"
              className="evolv-input text-xs"
              disabled={!allMandatoryDone}
            />
            <button
              onClick={handleSignOff}
              disabled={!allMandatoryDone || !signerName.trim()}
              className={`
                px-4 py-2 rounded-lg font-semibold text-xs
                transition-colors
                ${allMandatoryDone && signerName.trim()
                  ? 'bg-blue-DEFAULT text-white hover:opacity-90'
                  : 'bg-bg-base text-text-muted border '
                    + 'border-border-base cursor-not-allowed'}
              `}
            >
              Mark as Decommissioned →
            </button>
          </div>

          <div className="mt-4 pt-4 border-t border-border-base">
            <button
              onClick={handleGenerateReport}
              className="text-[11px] text-blue-DEFAULT font-medium
                         hover:underline"
            >
              📄 Generate Decommissioning Report (PDF — Sprint 19)
            </button>
          </div>
        </div>

        {/* Confirm modal */}
        {showConfirm && (
          <div className="fixed inset-0 bg-black/60 flex items-center
                          justify-center z-50 p-4"
               onClick={() => setShowConfirm(false)}>
            <div className="bg-bg-card rounded-xl border
                            border-border-bright p-6 max-w-md w-full"
                 onClick={e => e.stopPropagation()}>
              <h3 className="text-base font-semibold text-text-primary
                             mb-2">
                Confirm decommissioning
              </h3>
              <p className="text-sm text-text-secondary leading-relaxed
                            mb-4">
                You are about to formally retire{' '}
                <span className="font-medium text-text-primary">
                  {planData.projectName || 'this system'}
                </span>. This action will be recorded in the audit
                trail with{' '}
                <span className="font-medium text-text-primary">
                  {signerName.trim()}
                </span>{' '}as the responsible signer.
              </p>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowConfirm(false)}
                  className="px-3 py-1.5 text-xs rounded
                             bg-bg-base text-text-secondary
                             border border-border-base
                             hover:border-border-bright"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmSignOff}
                  className="px-3 py-1.5 text-xs rounded
                             bg-blue-DEFAULT text-white
                             font-semibold hover:opacity-90"
                >
                  Sign and Decommission
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Header (shared across locked / active / done) ────────────────
function Header() {
  return (
    <div>
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 rounded-xl bg-bg-card
                        border border-border-base flex items-center
                        justify-center text-xl shrink-0">
          🔒
        </div>
        <div>
          <h1 className="text-2xl font-bold text-text-primary">
            Decommissioning
          </h1>
          <p className="text-text-muted text-xs">
            Phase 8 of 8 — Controlled retirement per
            21 CFR Part 11 §11.10(c) + GAMP 5 Appendix M11
          </p>
        </div>
      </div>
      <div className="neon-sep mt-3" />
    </div>
  )
}

// ── Read-only checklist preview (locked state) ───────────────────
function ReadOnlyChecklistPreview() {
  return (
    <div className="mt-10 rounded-xl border border-border-base
                    bg-bg-card p-5">
      <h3 className="text-xs font-semibold text-text-primary
                     uppercase tracking-widest mb-1">
        What this phase will require
      </h3>
      <p className="text-[11px] text-text-muted mb-4">
        When the system reaches released state, you will work
        through these regulated steps. The list is grounded in
        21 CFR Part 11 §11.10(c) and GAMP 5 Appendix M11.
      </p>
      <ul className="space-y-2">
        {DECOM_CHECKLIST.map(item => (
          <li key={item.id} className="flex items-start gap-2 text-xs
                                       text-text-secondary">
            <span className="text-text-muted mt-0.5 shrink-0">○</span>
            <span className="flex-1">
              {item.label}
              <span className="text-text-muted ml-2">
                — {item.citation.reg} {item.citation.section}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
