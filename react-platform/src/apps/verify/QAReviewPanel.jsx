/**
 * QAReviewPanel — Sprint 15.4 Pre-Lock QA Review.
 *
 * Filters a test run to the items that warrant a QA lead's attention
 * BEFORE the executor signs the run off:
 *   • Failed steps (with actual result + evidence + linked defects)
 *   • Blocked steps (need a reason)
 *   • Adhoc inserts (tester-authored mid-run — need justification)
 *
 * Provides a 4-point checklist + comments box so the reviewer can
 * record an independent attestation. The panel does NOT lock — that
 * stays with the executor's electronic signature on the Execute tab.
 *
 * Available pre- AND post-lock so reviewers can revisit later.
 */
import { useEffect, useMemo } from 'react'
import { useAppStore } from '../../store/useAppStore.js'

const CHECKLIST = [
  {
    key:   'actualResultsComplete',
    label: 'All failed steps have a recorded actual result',
    why:   'ALCOA Attributable + Original — failure must be described.',
  },
  {
    key:   'defectsLogged',
    label: 'Every failed step has a linked defect entry',
    why:   '21 CFR §820.100 CAPA traceability.',
  },
  {
    key:   'evidenceAttached',
    label: 'Evidence attached for failures and material findings',
    why:   'EU Annex 11 §9 — data must be supported by evidence.',
  },
  {
    key:   'adhocStepsJustified',
    label: 'All adhoc steps have a documented reason for insertion',
    why:   'Audit-distinguishable (FDA CSA tester-in-the-loop).',
  },
]

// ── Reviewable items derivation ──────────────────────────────────
function deriveReviewItems(steps, stepResults, defects) {
  const items = []
  for (const step of steps) {
    const key   = `${step.step_number}_${step.step_type}`
    const r     = stepResults[key] ?? {}
    const isFail    = r.verdict === 'fail'
    const isBlocked = r.verdict === 'blocked'
    const isAdhoc   = step.source === 'tester-adhoc'
    if (!isFail && !isBlocked && !isAdhoc) continue

    const linkedDefects = defects.filter(d => d.stepKey === key)
    const tags = []
    if (isFail)    tags.push('FAIL')
    if (isBlocked) tags.push('BLOCKED')
    if (isAdhoc)   tags.push('ADHOC')

    items.push({
      key, step, result: r, linkedDefects, tags,
      isFail, isBlocked, isAdhoc,
    })
  }
  return items
}

// ── Auto-suggest checklist values ────────────────────────────────
// Pre-fills suggestions so the reviewer doesn't tick blindly.
function autoSuggest(items) {
  const failItems  = items.filter(i => i.isFail)
  const adhocItems = items.filter(i => i.isAdhoc)
  return {
    actualResultsComplete:
      failItems.length === 0
      || failItems.every(i => Boolean(i.result.actualResult?.trim())),
    defectsLogged:
      failItems.length === 0
      || failItems.every(i => i.linkedDefects.length > 0),
    evidenceAttached:
      failItems.length === 0
      || failItems.every(i => Boolean(i.result.evidence)),
    adhocStepsJustified:
      adhocItems.length === 0
      || adhocItems.every(i => Boolean(i.step.adhoc_reason?.trim())),
  }
}

// ── Tag chip ─────────────────────────────────────────────────────
const TAG_STYLE = {
  FAIL:    { bg: 'rgba(239,68,68,0.15)',  text: '#ef4444' },
  BLOCKED: { bg: 'rgba(245,158,11,0.15)', text: '#f59e0b' },
  ADHOC:   { bg: 'rgba(168,85,247,0.15)', text: '#a855f7' },
}

function Tag({ label }) {
  const s = TAG_STYLE[label] ?? TAG_STYLE.FAIL
  return (
    <span className="text-[8px] px-1.5 py-0.5 rounded font-bold
                     uppercase tracking-wide"
          style={{ background: s.bg, color: s.text }}>
      {label}
    </span>
  )
}

// ── ReviewItemCard ───────────────────────────────────────────────
function ReviewItemCard({ item }) {
  const { step, result, linkedDefects, tags, isFail, isAdhoc } = item
  return (
    <div className="rounded-lg border border-border-base bg-bg-surface
                    p-3 flex flex-col gap-2">
      <div className="flex items-center gap-2 flex-wrap">
        {tags.map(t => <Tag key={t} label={t} />)}
        <span className="font-mono text-[10px] text-text-muted">
          Step {step.step_number}
        </span>
        <span className="text-[11px] text-text-secondary font-medium">
          {step.step_title}
        </span>
        {step.requirement_reference && (
          <span className="ml-auto text-[9px] font-mono
                           px-1.5 py-0.5 rounded
                           bg-bg-card text-text-muted
                           border border-border-base">
            {step.requirement_reference}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 text-[10px]">
        <div>
          <span className="text-text-muted uppercase tracking-wide
                           text-[9px] font-semibold">
            Expected
          </span>
          <div className="text-text-secondary leading-relaxed mt-0.5">
            {step.expected_result || (
              <span className="opacity-40 italic">—</span>
            )}
          </div>
        </div>
        <div>
          <span className="text-text-muted uppercase tracking-wide
                           text-[9px] font-semibold">
            Actual
          </span>
          <div className={`leading-relaxed mt-0.5 ${
            isFail && !result.actualResult?.trim()
              ? 'text-red-400 italic'
              : 'text-text-secondary'}`}>
            {result.actualResult?.trim()
              || <span className="italic">— not recorded —</span>}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3 text-[10px]
                      text-text-muted flex-wrap">
        {result.evidence ? (
          <span className="text-lime-DEFAULT">
            📎 {result.evidence.name}
          </span>
        ) : isFail ? (
          <span className="text-red-400">⚠ No evidence</span>
        ) : null}

        {result.testerName && (
          <span>by {result.testerName}</span>
        )}
        {result.executedAt && (
          <span>at {new Date(result.executedAt).toLocaleString()}</span>
        )}
      </div>

      {isAdhoc && (
        <div className="rounded border border-purple-DEFAULT/30
                        bg-purple-DEFAULT/5 px-2 py-1.5 text-[10px]">
          <span className="text-purple-300 font-semibold uppercase
                           tracking-wide text-[9px]">
            Adhoc reason
          </span>
          <div className="text-text-secondary mt-0.5">
            {step.adhoc_reason
              || <span className="text-red-400 italic">
                  — missing, must be provided —
                 </span>}
          </div>
          {step.inserted_by && (
            <div className="text-text-muted mt-0.5">
              Inserted by {step.inserted_by}
              {step.inserted_at && (
                ` · ${new Date(step.inserted_at).toLocaleString()}`
              )}
            </div>
          )}
        </div>
      )}

      {linkedDefects.length > 0 && (
        <div className="rounded border border-red-500/20
                        bg-red-500/5 px-2 py-1.5">
          <div className="text-[9px] uppercase tracking-wide
                          font-semibold text-red-400 mb-1">
            🐛 {linkedDefects.length} linked defect
            {linkedDefects.length === 1 ? '' : 's'}
          </div>
          <ul className="text-[10px] text-text-secondary space-y-0.5">
            {linkedDefects.map(d => (
              <li key={d.id} className="flex items-start gap-2">
                <span className="font-mono text-text-muted">{d.id}</span>
                <span className="font-semibold opacity-90">
                  [{d.severity}]
                </span>
                <span className="flex-1">{d.description}</span>
                {d.assignee && (
                  <span className="text-text-muted">→ {d.assignee}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {isFail && linkedDefects.length === 0 && (
        <div className="text-[10px] text-red-400">
          ⚠ No defect logged for this failure.
        </div>
      )}
    </div>
  )
}

// ── Main panel ───────────────────────────────────────────────────
export default function QAReviewPanel({
  run, steps, stepResults, defects, locked,
}) {
  const {
    qaReviews, setQaReview, setQaReviewCheck, markQaReviewSigned,
    userProfile,
  } = useAppStore()

  const runId  = run?.runId
  const review = qaReviews[runId] ?? {
    reviewerName: '',
    comments:     '',
    checks: {
      actualResultsComplete: false,
      defectsLogged:         false,
      evidenceAttached:      false,
      adhocStepsJustified:   false,
    },
    reviewedAt:   null,
  }

  const items = useMemo(
    () => deriveReviewItems(steps, stepResults, defects),
    [steps, stepResults, defects],
  )
  const suggestions = useMemo(() => autoSuggest(items), [items])

  if (!run) {
    return (
      <div className="flex-1 flex items-center justify-center
                      text-text-muted text-xs">
        Start a test run to enable the QA review.
      </div>
    )
  }

  const failCount    = items.filter(i => i.isFail).length
  const blockedCount = items.filter(i => i.isBlocked).length
  const adhocCount   = items.filter(i => i.isAdhoc).length

  const allChecked = CHECKLIST.every(c => review.checks[c.key])
  const canSign    = allChecked && review.reviewerName.trim().length > 0

  const handleSign = () => {
    if (!canSign) return
    markQaReviewSigned(runId)
  }

  // Pre-fill reviewer name from user profile (one-shot per run).
  useEffect(() => {
    if (!runId) return
    if (review.reviewedAt) return
    if (review.reviewerName) return
    if (!userProfile?.name) return
    setQaReview(runId, 'reviewerName', userProfile.name)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId])

  return (
    <div className="flex-1 overflow-auto">
      {/* ── Top summary strip ─────────────────────────────────── */}
      <div className="px-6 py-3 border-b border-border-base
                      bg-bg-surface flex items-center gap-4 flex-wrap">
        <span className="text-xs font-semibold text-text-secondary">
          Pre-lock QA Review
        </span>
        <span className="text-[10px] text-text-muted">
          21 CFR Part 11 §11.10(b) — independent record review
        </span>
        <div className="ml-auto flex items-center gap-3 text-[10px]">
          <span className="text-red-400 font-semibold">
            {failCount} Fail
          </span>
          <span className="text-amber-DEFAULT font-semibold">
            {blockedCount} Blocked
          </span>
          <span style={{ color: '#a855f7' }} className="font-semibold">
            {adhocCount} Adhoc
          </span>
          <span className="text-text-muted">
            of {steps.length} step{steps.length === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      {/* ── Body grid: items left, attestation right ──────────── */}
      <div className="grid grid-cols-3 gap-4 px-6 py-4">

        {/* Items column */}
        <div className="col-span-2 flex flex-col gap-2">
          {items.length === 0 ? (
            <div className="rounded-lg border border-lime-DEFAULT/30
                            bg-lime-DEFAULT/5 p-4 text-center">
              <span className="text-lime-DEFAULT text-sm font-semibold">
                ✓ Nothing requires QA attention
              </span>
              <p className="text-[11px] text-text-muted mt-1">
                No failed, blocked, or adhoc steps in this run. Review
                is still recommended before sign-off.
              </p>
            </div>
          ) : (
            <>
              <div className="text-[10px] uppercase tracking-wide
                              text-text-muted font-semibold mb-1">
                Items requiring review ({items.length})
              </div>
              {items.map(item => (
                <ReviewItemCard key={item.key} item={item} />
              ))}
            </>
          )}
        </div>

        {/* Attestation column */}
        <div className="col-span-1 flex flex-col gap-3">
          <div className="rounded-lg border border-border-base
                          bg-bg-surface p-4 flex flex-col gap-3
                          sticky top-4">
            <div className="text-[11px] font-semibold text-text-secondary
                            uppercase tracking-wide">
              Reviewer Attestation
            </div>

            {/* Checklist */}
            <div className="flex flex-col gap-2">
              {CHECKLIST.map(c => {
                const checked   = !!review.checks[c.key]
                const suggested = !!suggestions[c.key]
                return (
                  <label key={c.key}
                    className="flex items-start gap-2 cursor-pointer
                               group">
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={!!review.reviewedAt}
                      onChange={e => setQaReviewCheck(
                        runId, c.key, e.target.checked,
                      )}
                      className="mt-0.5 cursor-pointer
                                 disabled:cursor-not-allowed"
                    />
                    <span className="flex-1 text-[10px]
                                     text-text-secondary leading-snug">
                      {c.label}
                      {!checked && suggested && (
                        <span className="ml-1 text-[9px] text-lime-DEFAULT">
                          (auto-OK)
                        </span>
                      )}
                      {!checked && !suggested && (
                        <span className="ml-1 text-[9px] text-amber-DEFAULT">
                          (gap detected)
                        </span>
                      )}
                      <span className="block text-text-muted text-[9px]
                                       opacity-70 italic">
                        {c.why}
                      </span>
                    </span>
                  </label>
                )
              })}
            </div>

            {/* Comments */}
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-text-muted">
                Reviewer comments
              </label>
              <textarea
                value={review.comments}
                onChange={e => setQaReview(
                  runId, 'comments', e.target.value,
                )}
                disabled={!!review.reviewedAt}
                rows={4}
                placeholder="Notes for the executor / batch record…"
                className="evolv-input text-[11px] px-2 py-1.5
                           resize-none"
              />
            </div>

            {/* Reviewer name */}
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-text-muted">
                Reviewer name
              </label>
              <input
                value={review.reviewerName}
                onChange={e => setQaReview(
                  runId, 'reviewerName', e.target.value,
                )}
                disabled={!!review.reviewedAt}
                placeholder="Full name…"
                className="evolv-input text-[11px] px-2 py-1.5"
              />
            </div>

            {/* Sign / status */}
            {review.reviewedAt ? (
              <div className="rounded border border-lime-DEFAULT/30
                              bg-lime-DEFAULT/5 p-2.5">
                <div className="text-[11px] font-semibold
                                text-lime-DEFAULT">
                  ✓ Reviewed by {review.reviewerName}
                </div>
                <div className="text-[10px] text-text-muted">
                  {new Date(review.reviewedAt).toLocaleString()}
                </div>
                {locked && (
                  <div className="text-[9px] text-text-muted mt-1
                                  italic">
                    Run is locked — review is read-only.
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={handleSign}
                disabled={!canSign}
                title={canSign ? 'Record QA review attestation'
                  : 'Tick all checks and enter your name to sign.'}
                className="px-3 py-2 rounded text-[11px] font-semibold
                           bg-lime-DEFAULT text-bg-base
                           hover:opacity-90 transition-opacity
                           disabled:opacity-40
                           disabled:cursor-not-allowed"
              >
                {allChecked
                  ? 'Sign Review'
                  : `Tick all ${CHECKLIST.length} checks to enable`}
              </button>
            )}

            <p className="text-[9px] text-text-muted leading-relaxed">
              This QA review is independent of the executor's electronic
              signature on the Execute tab. Both are recorded in the
              ALCOA audit trail.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
