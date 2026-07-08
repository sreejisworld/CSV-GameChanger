/**
 * BriefIntake — Sprint 34 single-textarea front door.
 *
 * The Workshop intake (Sprint 17.4) asks for nine fields. Pharma QA
 * pros at the April demos liked the *output* but balked at the *form*:
 * "I just want to paste a paragraph and see what the AI gives me."
 * BriefIntake is that single-textarea front door — same backend
 * (`POST /requirements/generate`), same data contract back, but the
 * form is one box and one button.
 *
 * Pattern source: Claude/ChatGPT chat-input hero (already used on
 * Home.jsx via HeroPrompt in Sprint 31). Pharma QA pros recognise
 * this surface from the AI tools they already trust.
 *
 * Wiring:
 *   • Reuses the parent's existing `handleWorkshopGenerated` callback
 *     (data shape returned by /requirements/generate is identical
 *     between brief and workshop modes — 9-field workshop just adds
 *     more `additional_context` to the LLM prompt).
 *   • Reuses parent's busy/status setters so the status pill renders
 *     in the same place as the workshop form.
 *
 * Stepwise progress messages cycle while we wait so the user sees the
 * AI "thinking out loud" rather than a frozen spinner — same UX trick
 * Claude/Cursor use during long requests.
 */
import { useState, useEffect } from 'react'
import { useAppStore } from '../../store/useAppStore.js'
import { API_BASE } from '../../config.js'

// Stepwise narration cycles every ~900ms while the request is
// in-flight. Three steps lets the cycle feel deliberate without
// feeling slow on a fast (~2s) backend response.
const PROGRESS_STEPS = [
  'Querying GAMP 5 corpus…',
  'Extracting candidate requirements…',
  'Classifying criticality + risk…',
]

// Pre-filled sample so demo presenters can show the round-trip
// without typing. Mirrors the kind of one-paragraph brief a CSV
// lead would paste from a project kickoff doc.
const SAMPLE_BRIEF = (
  'We are validating a cloud-hosted LIMS (LabCore v4.2) used by '
  + 'QC labs to track sample receipt, chain-of-custody, instrument '
  + 'data capture (HL7), out-of-spec investigations, and final batch '
  + 'release. Users include lab technicians, supervisors, and QA '
  + 'reviewers. The system is GxP-direct and must enforce '
  + '21 CFR Part 11 electronic signatures on all release decisions.'
)


export default function BriefIntake({
  onGenerated,
  onError,
  busy,
  setBusy,
  status,
  setStatus,
}) {
  // Sprint 35.5 (F2 fix): read the active project's name + system
  // description from the Plan phase so the generated rows are tagged
  // to the right project, and the user doesn't lose context if they
  // bounced from Plan → Requirements without re-typing.
  const planData = useAppStore(s => s.planData)
  const projectName       = planData?.projectName       ?? ''
  const planSystemDescPin = planData?.systemDescription ?? ''

  const [brief,    setBrief]    = useState('')
  const [stepIdx,  setStepIdx]  = useState(0)

  const canSubmit = !busy && brief.trim().length > 9

  // Cycle the progress narration while the request is in flight.
  // Resets to step 0 when busy flips back off so the next submit
  // starts narrating from "Querying GAMP 5 corpus…" again.
  useEffect(() => {
    if (!busy) { setStepIdx(0); return }
    const t = setInterval(() => {
      setStepIdx(i => (i + 1) % PROGRESS_STEPS.length)
    }, 900)
    return () => clearInterval(t)
  }, [busy])

  const handleSubmit = async () => {
    if (!canSubmit) return
    setBusy(true)
    setStatus({ kind: 'info', text: PROGRESS_STEPS[0] })
    try {
      const res = await fetch(`${API_BASE}/requirements/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          // Sprint 35.5: include the active project name so generated
          // rows are tagged to the right project end-to-end, and so
          // the Plan → Requirements handoff isn't anonymous.
          project_name:          projectName || null,
          // The brief drops into `system_description` — the backend's
          // RequirementArchitect parses sentences, runs each through
          // generate_urs(), and aggregates UR/FR rows. If the user's
          // brief is sparse but Plan has a richer system description,
          // we concatenate so the LLM gets the best context available.
          system_description:    planSystemDescPin
            ? `${brief}\n\nProject context (from Plan phase):\n${planSystemDescPin}`
            : brief,
          role:                  'User',
          risk_assessment:       'GxP Indirect',
          implementation_method: 'Configured',
        }),
      })
      if (!res.ok) {
        let detail = `HTTP ${res.status}`
        try {
          const err = await res.json()
          detail = typeof err.detail === 'string'
            ? err.detail
            : (err.detail?.message ?? detail)
        } catch { /* keep status code */ }
        throw new Error(detail)
      }
      const data = await res.json()
      onGenerated(data)
      const skipNote = data.skipped?.length
        ? ` · ${data.skipped.length} line${
            data.skipped.length === 1 ? '' : 's'
          } skipped (no GAMP 5 context)`
        : ''
      setStatus({
        kind: 'ok',
        text: `Drafted ${data.count} requirement row${
          data.count === 1 ? '' : 's'
        } from your brief${skipNote}`,
      })
    } catch (e) {
      onError?.(e)
      setStatus({
        kind: 'err',
        text: (
          `Draft failed: ${e.message ?? e}. `
          + 'Try Workshop-Driven for finer control, or Manual '
          + 'Authoring to write rows by hand.'
        ),
      })
    } finally {
      setBusy(false)
    }
  }

  // Submit on Enter (no shift). Matches Home.jsx HeroPrompt and
  // Claude/ChatGPT chat-input convention; Shift+Enter adds a newline.
  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div
      className="mb-4 rounded-lg border bg-bg-card"
      style={{
        borderColor: 'rgba(0,127,255,0.25)',
        boxShadow: '0 0 0 1px rgba(0,127,255,0.04) inset',
      }}
    >
      {/* Header strip — mirrors WorkshopIntake's visual weight so
          the two modes feel like siblings, not parent/child. */}
      <div
        className="px-4 py-2.5 flex items-center gap-2 border-b
                   border-border-base"
      >
        <span className="text-blue-DEFAULT text-sm">✨</span>
        <span className="text-[11px] font-semibold uppercase
                         tracking-wide text-text-secondary">
          Brief → Requirements
        </span>
        {/* Sprint 35.5 (F2 fix): project context pill — proves the
            Plan → Requirements wire is live so users don't wonder
            "is this getting tagged to my project?" */}
        {projectName ? (
          <span
            className="text-[10px] font-medium px-2 py-0.5 rounded-full
                       border"
            style={{
              borderColor: 'rgba(0,127,255,0.3)',
              background:  'rgba(0,127,255,0.08)',
              color:       '#007FFF',
            }}
            title="From Plan phase — generated rows tag to this project"
          >
            for: {projectName}
          </span>
        ) : (
          <span className="text-[10px] text-amber-500"
            title="Plan phase has no project name yet — generated rows
                   will be untagged. Set the project name in Plan first."
          >
            (no project — set name in Plan)
          </span>
        )}
        <span className="text-text-muted text-[11px] hidden lg:inline">
          One paragraph in, draft UR/FRs out.
        </span>
        <button
          onClick={() => setBrief(SAMPLE_BRIEF)}
          disabled={busy}
          className="ml-auto text-[10px] text-blue-DEFAULT hover:underline
                     disabled:opacity-40"
          title="Insert a sample LIMS brief"
        >
          Use sample brief
        </button>
      </div>

      {/* Textarea + submit row */}
      <div className="p-4">
        <label className="block text-[11px] font-medium text-text-secondary
                          mb-2">
          Paste a one-paragraph brief about the system you're validating
        </label>
        <textarea
          value={brief}
          onChange={e => setBrief(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={busy}
          rows={5}
          placeholder={
            'e.g. We are validating a cloud LIMS used by QC for '
            + 'sample receipt, chain-of-custody, HL7 instrument data '
            + 'capture, and final batch release. GxP-direct; '
            + '21 CFR Part 11 e-signatures on release decisions.'
          }
          className="w-full px-3 py-2.5 rounded border border-border-base
                     bg-bg-base text-sm text-text-primary placeholder:text-text-muted
                     focus:outline-none focus:border-blue-DEFAULT
                     focus:ring-2 focus:ring-blue-DEFAULT/20
                     disabled:opacity-60 resize-y"
          style={{ minHeight: '110px', fontFamily: 'inherit' }}
        />

        <div className="mt-3 flex items-center gap-3">
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className={`
              text-xs font-semibold px-4 py-2 rounded transition-all
              ${canSubmit
                ? 'text-white shadow-sm hover:opacity-90'
                : 'bg-bg-elev text-text-muted cursor-not-allowed'}
            `}
            style={canSubmit ? {
              background: 'linear-gradient(90deg, #007FFF, #32CD32)',
            } : undefined}
          >
            {busy ? 'Drafting…' : 'Draft my requirements'}
          </button>

          <span className="text-[10px] text-text-muted">
            <kbd className="px-1.5 py-0.5 rounded bg-bg-elev
                            border border-border-base">Enter</kbd>
            {' to submit · '}
            <kbd className="px-1.5 py-0.5 rounded bg-bg-elev
                            border border-border-base">Shift</kbd>
            {' + '}
            <kbd className="px-1.5 py-0.5 rounded bg-bg-elev
                            border border-border-base">Enter</kbd>
            {' for newline'}
          </span>

          {/* Live narration while in-flight — replaces the static
              status pill so the user sees the AI "thinking". */}
          {busy && (
            <span className="ml-auto text-[11px] text-blue-DEFAULT
                             flex items-center gap-2">
              <span
                className="inline-block w-1.5 h-1.5 rounded-full
                           bg-blue-DEFAULT animate-pulse"
              />
              {PROGRESS_STEPS[stepIdx]}
            </span>
          )}
        </div>

        {/* Final status pill (after submit completes) — colour-coded
            by kind. Hidden while busy so we don't double-up with the
            live narration above. */}
        {status && !busy && (
          <div
            className={`
              mt-3 px-3 py-2 rounded text-[11px] border
              ${status.kind === 'ok'
                ? 'border-green-500/30 bg-green-500/8 text-green-700'
                : status.kind === 'err'
                  ? 'border-red-500/30 bg-red-500/8 text-red-700'
                  : 'border-blue-DEFAULT/30 bg-blue-DEFAULT/8 text-blue-DEFAULT'}
            `}
          >
            {status.text}
          </div>
        )}
      </div>
    </div>
  )
}
