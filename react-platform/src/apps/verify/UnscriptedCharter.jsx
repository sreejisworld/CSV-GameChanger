/**
 * UnscriptedCharter — FDA CSA-aligned exploratory testing session
 * for MEDIUM and LOW risk scripts.
 *
 * Stores all session state in Zustand (survives tab switches).
 * Call onComplete(verdict) to lock the run and trigger sign-off.
 */
import { useState, useEffect, useRef } from 'react'
import { useAppStore } from '../../store/useAppStore.js'

const SEVERITY_OPTS = ['Critical', 'Major', 'Minor', 'Observation']

const ERROR_GUESSING = {
  boundary: [
    'Enter values at the exact boundary (min/max allowed).',
    'Enter values just outside the boundary (min-1, max+1).',
    'Leave required fields empty and attempt to save.',
  ],
  auth: [
    'Attempt the action with a lower-privilege role.',
    'Try accessing the feature after session timeout.',
    'Submit the form twice rapidly (double-submit check).',
  ],
  input: [
    'Enter special characters: < > " \' ; & %',
    'Paste a very long string (500+ chars) into text fields.',
    'Enter numeric data into text-only fields and vice versa.',
  ],
  workflow: [
    'Try navigating backwards mid-workflow.',
    'Refresh the browser mid-session — does state persist?',
    'Complete the workflow in a different order than expected.',
  ],
}

function useTimer(startedAt) {
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    if (!startedAt) return
    const tick = () =>
      setElapsed(Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000))
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [startedAt])

  const h = Math.floor(elapsed / 3600).toString().padStart(2, '0')
  const m = Math.floor((elapsed % 3600) / 60).toString().padStart(2, '0')
  const s = (elapsed % 60).toString().padStart(2, '0')
  return `${h}:${m}:${s}`
}

function FindingForm({ onAdd, frIds }) {
  const [sev, setSev]   = useState('Major')
  const [desc, setDesc] = useState('')
  const [frRef, setFr]  = useState(frIds[0] ?? '')

  const submit = () => {
    if (!desc.trim()) return
    onAdd({
      id:          `FND-${Date.now()}`,
      severity:    sev,
      description: desc.trim(),
      frRef,
      loggedAt:    new Date().toISOString(),
    })
    setDesc('')
  }

  return (
    <div className="flex gap-2 items-end flex-wrap">
      <div className="flex flex-col gap-1">
        <label className="text-[10px] text-text-muted">Severity</label>
        <select
          value={sev}
          onChange={e => setSev(e.target.value)}
          className="evolv-input evolv-select text-xs px-2 py-1"
        >
          {SEVERITY_OPTS.map(o => <option key={o}>{o}</option>)}
        </select>
      </div>
      <div className="flex flex-col gap-1 flex-1 min-w-[160px]">
        <label className="text-[10px] text-text-muted">Description</label>
        <input
          value={desc}
          onChange={e => setDesc(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && submit()}
          placeholder="Describe the finding…"
          className="evolv-input text-xs px-2 py-1"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-[10px] text-text-muted">FR Ref</label>
        <select
          value={frRef}
          onChange={e => setFr(e.target.value)}
          className="evolv-input evolv-select text-xs px-2 py-1"
        >
          {frIds.map(id => <option key={id}>{id}</option>)}
          <option value="">General</option>
        </select>
      </div>
      <button
        onClick={submit}
        disabled={!desc.trim()}
        className="px-3 py-1.5 rounded text-xs font-semibold
                   bg-amber-500 text-white hover:opacity-90 transition-opacity
                   disabled:opacity-40 disabled:cursor-not-allowed"
      >
        + Log Finding
      </button>
    </div>
  )
}

const SEV_COLORS = {
  Critical:    { bg: 'rgba(239,68,68,0.15)',  text: '#ef4444' },
  Major:       { bg: 'rgba(245,158,11,0.15)', text: '#f59e0b' },
  Minor:       { bg: 'rgba(0,127,255,0.15)',  text: '#007FFF' },
  Observation: { bg: 'rgba(100,116,139,0.15)',text: '#64748b' },
}

export default function UnscriptedCharter({
  script, runId, locked, onComplete,
}) {
  const {
    unscriptedSessions, initUnscriptedSession,
    addSessionNote, addSessionFinding, setSessionVerdict,
    lockTestRun, setRunMeta, testRuns,
  } = useAppStore()

  const [noteText,    setNoteText]    = useState('')
  const [verdict,     setVerdict]     = useState(null)
  const [showSignOff, setShowSignOff] = useState(false)
  const [signerName,  setSignerName]  = useState('')
  const [signerError, setSignerError] = useState('')
  const notesEndRef = useRef(null)

  // Init session on mount
  useEffect(() => { initUnscriptedSession(runId) }, [runId])

  const session  = unscriptedSessions[runId]
  const timer    = useTimer(session?.startedAt)
  const run      = testRuns[runId]

  // Build exploration targets from script steps
  const executionSteps = (script.steps ?? []).filter(
    s => s.step_type !== 'Setup'
  )
  const frIds = [...new Set(
    executionSteps
      .map(s => s.requirement_reference)
      .filter(Boolean)
  )]
  const errorGuessCategories = ['boundary', 'auth', 'input', 'workflow']

  const handleAddNote = () => {
    const text = noteText.trim()
    if (!text) return
    addSessionNote(runId, text)
    setNoteText('')
    setTimeout(() => notesEndRef.current?.scrollIntoView(), 50)
  }

  const handleComplete = () => {
    if (!verdict) return
    if (!signerName.trim()) { setSignerError('Required'); return }
    setSignerError('')
    setSessionVerdict(runId, verdict)
    setRunMeta(runId, 'signerName', signerName.trim())
    const overallVerdict =
      verdict === 'Satisfactory' ? 'PASS'
      : verdict === 'Unsatisfactory' ? 'FAIL'
      : 'BLOCKED'
    onComplete(overallVerdict)
  }

  if (!session) return null

  const isLocked = locked

  return (
    <div className="flex-1 overflow-auto px-6 py-4 space-y-5">

      {/* Charter header */}
      <div className="flex items-center gap-4 p-3 rounded-lg
                      bg-bg-card border border-border-base">
        <div>
          <p className="text-xs font-semibold text-text-secondary">
            {script.script_id}
          </p>
          <p className="text-[10px] text-text-muted">
            {script.urs_id} · {script.test_type} · {script.risk_level} Risk
          </p>
        </div>
        <div className="ml-auto text-right">
          <p className="font-mono text-sm text-amber-400">{timer}</p>
          <p className="text-[10px] text-text-muted">Session Duration</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-text-secondary font-medium">
            {session.notes.length} notes · {session.findings.length} findings
          </p>
          <p className="text-[10px] text-text-muted">Recorded so far</p>
        </div>
      </div>

      {/* Session mission */}
      <div>
        <h3 className="text-[10px] font-semibold text-text-muted uppercase
                       tracking-widest mb-2">
          Charter Mission
        </h3>
        <div className="p-3 rounded-lg bg-bg-surface border border-border-base">
          <p className="text-xs text-text-secondary leading-relaxed">
            Explore and verify that{' '}
            <span className="text-white font-medium">
              {script.requirement_summary ?? executionSteps[0]?.step_title ?? 'the system under test'}
            </span>{' '}
            behaves correctly across typical use cases, error conditions, and
            boundary values per FDA CSA guidance for{' '}
            {script.risk_level?.toLowerCase()} risk systems.
          </p>
        </div>
      </div>

      {/* Exploration areas */}
      <div>
        <h3 className="text-[10px] font-semibold text-text-muted uppercase
                       tracking-widest mb-2">
          Areas to Explore
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {executionSteps.slice(0, 6).map((step, i) => (
            <div key={i}
              className="p-3 rounded-lg border border-border-base bg-bg-card">
              <p className="text-[10px] text-blue-DEFAULT font-medium mb-1">
                {step.requirement_reference || `Area ${i + 1}`}
              </p>
              <p className="text-xs text-text-secondary leading-snug">
                {step.step_title}
              </p>
              <p className="text-[10px] text-text-muted mt-1 leading-relaxed">
                {step.step_instruction}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Error guessing prompts */}
      <div>
        <h3 className="text-[10px] font-semibold text-text-muted uppercase
                       tracking-widest mb-2">
          Error Guessing Prompts
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {errorGuessCategories.map(cat => (
            <div key={cat}
              className="p-3 rounded-lg border border-border-base bg-bg-surface">
              <p className="text-[10px] font-semibold text-text-secondary uppercase
                             tracking-wide mb-1.5">
                {cat}
              </p>
              <ul className="space-y-1">
                {ERROR_GUESSING[cat].map((tip, i) => (
                  <li key={i}
                    className="text-[10px] text-text-muted leading-snug flex gap-1">
                    <span className="text-amber-400 shrink-0">·</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Live notes */}
      <div>
        <h3 className="text-[10px] font-semibold text-text-muted uppercase
                       tracking-widest mb-2">
          Session Notes
          <span className="ml-2 text-[9px] font-normal normal-case">
            Timestamped automatically — record observations as you go
          </span>
        </h3>

        {!isLocked && (
          <div className="flex gap-2 mb-3">
            <textarea
              value={noteText}
              onChange={e => setNoteText(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleAddNote()
              }}
              placeholder="Observation or note… (Ctrl+Enter to save)"
              rows={2}
              className="flex-1 text-xs bg-bg-card border border-border-base rounded
                         px-3 py-2 text-text-secondary placeholder:text-text-muted
                         focus:outline-none focus:border-blue-DEFAULT resize-none"
            />
            <button
              onClick={handleAddNote}
              disabled={!noteText.trim()}
              className="px-3 py-1 rounded text-xs font-medium
                         bg-blue-DEFAULT text-white hover:opacity-90
                         transition-opacity disabled:opacity-40"
            >
              + Note
            </button>
          </div>
        )}

        {session.notes.length === 0 ? (
          <p className="text-[10px] text-text-muted opacity-60 italic">
            No notes yet — add observations above.
          </p>
        ) : (
          <div className="space-y-1.5 max-h-40 overflow-auto pr-1">
            {session.notes.map((n, i) => (
              <div key={i}
                className="flex gap-3 px-3 py-2 rounded bg-bg-card
                           border border-border-base">
                <span className="font-mono text-[9px] text-text-muted shrink-0 pt-0.5">
                  {new Date(n.timestamp).toLocaleTimeString()}
                </span>
                <span className="text-[11px] text-text-secondary leading-snug">
                  {n.text}
                </span>
              </div>
            ))}
            <div ref={notesEndRef} />
          </div>
        )}
      </div>

      {/* Findings log */}
      <div>
        <h3 className="text-[10px] font-semibold text-text-muted uppercase
                       tracking-widest mb-2">
          Structured Findings
        </h3>

        {!isLocked && (
          <div className="mb-3 p-3 rounded-lg bg-bg-card border border-border-base">
            <FindingForm onAdd={f => addSessionFinding(runId, f)} frIds={frIds} />
          </div>
        )}

        {session.findings.length === 0 ? (
          <p className="text-[10px] text-text-muted opacity-60 italic">
            No findings logged yet.
          </p>
        ) : (
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border-base">
                {['ID', 'Severity', 'Description', 'FR Ref', 'Time'].map(h => (
                  <th key={h}
                    className="text-left text-[10px] font-semibold text-text-muted
                               uppercase tracking-wide py-1.5 pr-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {session.findings.map(f => {
                const sc = SEV_COLORS[f.severity] ?? SEV_COLORS.Observation
                return (
                  <tr key={f.id}
                    className="border-b border-border-base hover:bg-bg-hover/20">
                    <td className="py-2 pr-3 font-mono text-[10px] text-text-muted">
                      {f.id}
                    </td>
                    <td className="py-2 pr-3">
                      <span className="text-[9px] px-1.5 py-0.5 rounded font-semibold"
                        style={{ background: sc.bg, color: sc.text }}>
                        {f.severity}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-[11px] text-text-secondary">
                      {f.description}
                    </td>
                    <td className="py-2 pr-3 font-mono text-[10px] text-text-muted">
                      {f.frRef || '—'}
                    </td>
                    <td className="py-2 text-[10px] text-text-muted">
                      {new Date(f.loggedAt).toLocaleTimeString()}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Session verdict + sign-off */}
      {!isLocked && (
        <div className="p-4 rounded-lg border border-amber-500/20
                        bg-amber-500/5">
          <p className="text-xs font-semibold text-white mb-3">
            Session Verdict &amp; Sign-Off
          </p>
          <div className="flex gap-2 mb-4">
            {['Satisfactory', 'Unsatisfactory', 'Incomplete'].map(v => (
              <button
                key={v}
                onClick={() => { setVerdict(v) ; setShowSignOff(true) }}
                className={`
                  px-3 py-1.5 rounded text-xs font-semibold border transition-all
                  ${verdict === v
                    ? v === 'Satisfactory'
                      ? 'bg-lime-DEFAULT/20 border-lime-DEFAULT/40 text-lime-DEFAULT'
                      : v === 'Unsatisfactory'
                        ? 'bg-red-500/20 border-red-500/40 text-red-400'
                        : 'bg-amber-500/20 border-amber-500/40 text-amber-400'
                    : 'bg-bg-card border-border-base text-text-muted hover:border-border-bright'}
                `}
              >
                {v}
              </button>
            ))}
          </div>

          {showSignOff && verdict && (
            <div className="flex items-end gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-[10px] text-text-muted">
                  Tester Name (21 CFR Part 11)
                </label>
                <input
                  value={signerName}
                  onChange={e => setSignerName(e.target.value)}
                  placeholder="Full name…"
                  className="evolv-input text-xs px-2 py-1.5 w-44"
                />
                {signerError && (
                  <span className="text-[10px] text-red-400">{signerError}</span>
                )}
              </div>
              <button
                onClick={handleComplete}
                className="px-4 py-1.5 rounded text-xs font-semibold
                           bg-lime-DEFAULT text-bg-base hover:opacity-90
                           transition-opacity"
              >
                Complete Charter Session
              </button>
            </div>
          )}
        </div>
      )}

      {isLocked && (
        <div className="p-4 rounded-lg border border-lime-DEFAULT/30
                        bg-lime-DEFAULT/5 text-center">
          <p className="text-lime-DEFAULT font-semibold text-sm mb-1">
            ✓ Charter Session Complete
          </p>
          <p className="text-text-muted text-[11px]">
            Verdict: {session.verdict} · Signed by {run?.signerName}
          </p>
        </div>
      )}
    </div>
  )
}
