/**
 * Verify — Lifecycle Phase 5: Test Execution
 *
 * State machine: briefing → executing → (end-of-run) ALCOA report tab
 *
 * Tabs:
 *   Execute Test  — briefing panel OR step table (High) OR charter (Med/Low)
 *   Script Review — read-only script view
 *   ALCOA Report  — appears after sign-off / charter complete
 *
 * Keyboard shortcuts (scripted mode only, when not focused in input):
 *   P = Pass  F = Fail  B = Blocked  N = N/A  → auto-advance to next step
 */
import { useState, useRef, useCallback, useEffect } from 'react'
import { useAppStore }       from '../store/useAppStore.js'
import { API_BASE }          from '../config.js'
import BriefingPanel         from './verify/BriefingPanel.jsx'
import UnscriptedCharter     from './verify/UnscriptedCharter.jsx'
import ALCOAReport           from './verify/ALCOAReport.jsx'

// ── Client-side helpers ───────────────────────────────────────────
function downloadCSV(filename, headers, rows) {
  const escape = v =>
    `"${String(v ?? '').replace(/"/g, '""')}"`
  const lines = [
    headers.join(','),
    ...rows.map(r => headers.map(h => escape(r[h])).join(',')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

async function downloadPDF(url, body, filename) {
  const res = await fetch(url, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  const blob = await res.blob()
  const burl = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = burl; a.download = filename; a.click()
  URL.revokeObjectURL(burl)
}

// ── Constants ─────────────────────────────────────────────────────
const VERDICT_CONFIG = {
  pass:    { label: 'Pass',    bg: 'rgba(50,205,50,0.15)',   border: 'rgba(50,205,50,0.4)',   text: '#32CD32', key: 'p' },
  fail:    { label: 'Fail',    bg: 'rgba(239,68,68,0.15)',   border: 'rgba(239,68,68,0.4)',   text: '#ef4444', key: 'f' },
  blocked: { label: 'Blocked', bg: 'rgba(245,158,11,0.15)',  border: 'rgba(245,158,11,0.4)',  text: '#f59e0b', key: 'b' },
  na:      { label: 'N/A',     bg: 'rgba(100,116,139,0.15)', border: 'rgba(100,116,139,0.4)', text: '#64748b', key: 'n' },
}

const CASE_COLORS = {
  Positive:   { bg: 'rgba(50,205,50,0.12)',  text: '#32CD32' },
  Negative:   { bg: 'rgba(239,68,68,0.12)',  text: '#ef4444' },
  'Edge Case':{ bg: 'rgba(245,158,11,0.12)', text: '#f59e0b' },
}

const SEV_OPTS = ['Critical', 'Major', 'Minor', 'Observation']

// ── VerdictButton ─────────────────────────────────────────────────
function VerdictButton({ verdict, active, locked, onClick }) {
  const cfg = VERDICT_CONFIG[verdict]
  return (
    <button
      onClick={locked ? undefined : onClick}
      disabled={locked}
      title={`${cfg.label} [${cfg.key.toUpperCase()}]`}
      className={`
        px-2 py-0.5 rounded text-[10px] font-semibold border
        transition-all duration-100 shrink-0
        ${locked ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
      `}
      style={active ? {
        background: cfg.bg, border: `1px solid ${cfg.border}`,
        color: cfg.text,
      } : {
        background: 'transparent',
        border: '1px solid var(--border-base)',
        color: 'var(--text-muted)',
      }}
    >
      {cfg.label}
    </button>
  )
}

// ── RunSummaryBar ─────────────────────────────────────────────────
function RunSummaryBar({ steps, stepResults }) {
  const total    = steps.length
  const pass     = Object.values(stepResults).filter(r => r.verdict === 'pass').length
  const fail     = Object.values(stepResults).filter(r => r.verdict === 'fail').length
  const blocked  = Object.values(stepResults).filter(r => r.verdict === 'blocked').length
  const na       = Object.values(stepResults).filter(r => r.verdict === 'na').length
  const executed = pass + fail + blocked + na
  const pct      = total ? Math.round((executed / total) * 100) : 0

  let verdict = 'IN PROGRESS' ; let vColor = '#64748b'
  if (executed === total && total > 0) {
    if (fail > 0)         { verdict = 'FAIL'    ; vColor = '#ef4444' }
    else if (blocked > 0) { verdict = 'BLOCKED' ; vColor = '#f59e0b' }
    else                  { verdict = 'PASS'    ; vColor = '#32CD32' }
  }

  return (
    <div className="px-6 py-3 bg-bg-surface border-b border-border-base shrink-0">
      <div className="flex items-center gap-3 mb-2">
        <span className="text-[10px] text-text-muted w-20 shrink-0">Progress</span>
        <div className="flex-1 h-1.5 bg-bg-card rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{
              width: `${pct}%`,
              background: fail > 0 ? '#ef4444' : blocked > 0 ? '#f59e0b' : '#32CD32',
            }}
          />
        </div>
        <span className="text-[10px] text-text-muted w-10 text-right shrink-0">
          {pct}%
        </span>
      </div>
      <div className="flex items-center gap-4">
        {[
          { label: 'Pass',    count: pass,    color: '#32CD32' },
          { label: 'Fail',    count: fail,    color: '#ef4444' },
          { label: 'Blocked', count: blocked, color: '#f59e0b' },
          { label: 'N/A',     count: na,      color: '#64748b' },
        ].map(({ label, count, color }) => (
          <span key={label} className="flex items-center gap-1 text-[10px]">
            <span className="font-semibold" style={{ color }}>{count}</span>
            <span className="text-text-muted">{label}</span>
          </span>
        ))}
        <span className="text-text-muted text-[10px]">/ {total} steps</span>
        <span
          className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded"
          style={{ color: vColor, background: vColor + '20', border: `1px solid ${vColor}40` }}
        >
          {verdict}
        </span>
      </div>
    </div>
  )
}

// ── DefectForm — inline under failed step ─────────────────────────
function DefectForm({ stepKey, stepTitle, runId, onDismiss }) {
  const { addDefect, defects } = useAppStore()
  const runDefects = defects[runId] ?? []
  const nextId = `DEF-${String(runDefects.length + 1).padStart(3, '0')}`

  const [sev,      setSev]      = useState('Major')
  const [desc,     setDesc]     = useState('')
  const [assignee, setAssignee] = useState('')
  const [fixDate,  setFixDate]  = useState('')
  const [frRef,    setFrRef]    = useState('')
  const fileRef = useRef(null)
  const [screenName, setScreenName] = useState('')

  const handleFile = e => {
    const file = e.target.files?.[0]
    if (!file) return
    setScreenName(file.name)
  }

  const submit = () => {
    if (!desc.trim()) return
    addDefect(runId, {
      id:          nextId,
      stepKey,
      severity:    sev,
      description: desc.trim(),
      assignee:    assignee.trim(),
      fixDate,
      frRef:       frRef.trim(),
      screenshotName: screenName,
      createdAt:   new Date().toISOString(),
    })
    onDismiss()
  }

  return (
    <tr>
      <td colSpan={11}
        className="px-4 py-3 bg-red-500/5 border-b border-red-500/20">
        <div className="flex items-start gap-2 mb-2">
          <span className="text-[10px] font-semibold text-red-400 uppercase tracking-wide">
            🐛 Log Defect — {nextId}
          </span>
          <span className="text-[10px] text-text-muted">
            for step: {stepTitle}
          </span>
          <button
            onClick={onDismiss}
            className="ml-auto text-[10px] text-text-muted hover:text-text-secondary"
          >
            ✕ Dismiss
          </button>
        </div>
        <div className="flex gap-2 flex-wrap items-end">
          <div className="flex flex-col gap-1">
            <label className="text-[9px] text-text-muted">Severity</label>
            <select value={sev} onChange={e => setSev(e.target.value)}
              className="evolv-input evolv-select text-[11px] px-1.5 py-1">
              {SEV_OPTS.map(o => <option key={o}>{o}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1 flex-1 min-w-[140px]">
            <label className="text-[9px] text-text-muted">Description *</label>
            <input value={desc} onChange={e => setDesc(e.target.value)}
              placeholder="Describe the defect…"
              className="evolv-input text-[11px] px-2 py-1" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[9px] text-text-muted">Assignee</label>
            <input value={assignee} onChange={e => setAssignee(e.target.value)}
              placeholder="Name…"
              className="evolv-input text-[11px] px-2 py-1 w-28" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[9px] text-text-muted">Fix By</label>
            <input type="date" value={fixDate} onChange={e => setFixDate(e.target.value)}
              className="evolv-input text-[11px] px-2 py-1 w-32" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[9px] text-text-muted">FR Ref</label>
            <input value={frRef} onChange={e => setFrRef(e.target.value)}
              placeholder="FR-1…"
              className="evolv-input text-[11px] px-2 py-1 w-20" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[9px] text-text-muted">Screenshot</label>
            <input type="file" ref={fileRef} className="hidden" accept="image/*"
              onChange={handleFile} />
            <button onClick={() => fileRef.current?.click()}
              className="text-[10px] border border-border-base rounded px-2 py-1
                         text-text-muted hover:text-text-secondary transition-colors">
              {screenName ? `📎 ${screenName.slice(0, 12)}…` : 'Attach…'}
            </button>
          </div>
          <button
            onClick={submit}
            disabled={!desc.trim()}
            className="px-3 py-1.5 rounded text-[11px] font-semibold
                       bg-red-500 text-white hover:opacity-90 transition-opacity
                       disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Log Defect
          </button>
        </div>
      </td>
    </tr>
  )
}

// ── StepRow ───────────────────────────────────────────────────────
function StepRow({
  step, result, locked, isFocused,
  onVerdictChange, onActualChange, onEvidenceChange, onTesterChange,
}) {
  const stepKey   = `${step.step_number}_${step.step_type}`
  const isSetup   = step.step_type === 'Setup'
  const caseColor = CASE_COLORS[step.test_case_type]
  const fileRef   = useRef(null)

  const handleFile = e => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 5 * 1024 * 1024) { alert('Evidence file must be under 5 MB.') ; return }
    const reader = new FileReader()
    reader.onload = ev => onEvidenceChange({
      name: file.name, size: file.size, dataUrl: ev.target.result,
    })
    reader.readAsDataURL(file)
  }

  return (
    <tr className={`
      border-b border-border-base transition-colors
      ${isFocused            ? 'bg-blue-DEFAULT/8 outline outline-1 outline-blue-DEFAULT/30' : ''}
      ${result?.verdict === 'fail'
        ? 'bg-red-500/5'
        : result?.verdict === 'pass'
          ? 'bg-lime-500/5'
          : isFocused ? '' : 'hover:bg-bg-hover/30'}
    `}>
      {/* Type */}
      <td className="py-2.5 pr-3 whitespace-nowrap">
        <span className={`
          text-[9px] px-1.5 py-0.5 rounded font-semibold uppercase
          ${isSetup
            ? 'bg-bg-card text-text-muted border border-border-base'
            : 'bg-blue-dim text-blue-DEFAULT border border-blue-DEFAULT/30'}
        `}>
          {step.step_type}
        </span>
      </td>
      {/* # */}
      <td className="py-2.5 pr-3 font-mono text-text-muted text-[11px]">
        {isFocused
          ? <span className="text-blue-DEFAULT font-bold">{step.step_number}</span>
          : step.step_number
        }
      </td>
      {/* Title */}
      <td className="py-2.5 pr-4 text-text-secondary text-[11px] font-medium max-w-[140px]">
        <span className="line-clamp-2">{step.step_title}</span>
      </td>
      {/* Instruction */}
      <td className="py-2.5 pr-4 text-text-muted text-[11px] max-w-[200px]">
        <span className="line-clamp-3 leading-relaxed">{step.step_instruction}</span>
      </td>
      {/* Expected */}
      <td className="py-2.5 pr-4 text-text-muted text-[11px] max-w-[160px]">
        {step.expected_result
          ? <span className="line-clamp-3">{step.expected_result}</span>
          : <span className="text-text-muted opacity-40 italic">Setup step</span>
        }
      </td>
      {/* Case */}
      <td className="py-2.5 pr-4 whitespace-nowrap">
        {caseColor
          ? (
            <span className="text-[9px] px-1.5 py-0.5 rounded font-semibold"
              style={{ background: caseColor.bg, color: caseColor.text }}>
              {step.test_case_type}
            </span>
          )
          : <span className="text-text-muted opacity-40">—</span>
        }
      </td>
      {/* Ref */}
      <td className="py-2.5 pr-4 font-mono text-[10px] text-text-muted whitespace-nowrap">
        {step.requirement_reference || '—'}
      </td>
      {/* Verdict buttons */}
      <td className="py-2.5 pr-3">
        <div className="flex gap-1">
          {Object.keys(VERDICT_CONFIG).map(v => (
            <VerdictButton
              key={v}
              verdict={v}
              active={result?.verdict === v}
              locked={locked}
              onClick={() => {
                onVerdictChange(stepKey, v)
                onTesterChange(stepKey, 'executedAt', new Date().toISOString())
              }}
            />
          ))}
        </div>
      </td>
      {/* Actual result */}
      <td className="py-2.5 pr-3 min-w-[160px]">
        {!isSetup && (
          <textarea
            value={result?.actualResult ?? ''}
            onChange={e => onActualChange(stepKey, e.target.value)}
            disabled={locked}
            rows={2}
            placeholder={
              result?.verdict === 'fail'
                ? 'Required for failures…'
                : 'Actual result…'
            }
            className={`
              w-full text-[10px] bg-bg-card border rounded px-2 py-1
              text-text-secondary placeholder:text-text-muted resize-none
              focus:outline-none focus:border-blue-DEFAULT
              ${result?.verdict === 'fail' && !result?.actualResult?.trim()
                ? 'border-red-500'
                : 'border-border-base'}
              ${locked ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          />
        )}
      </td>
      {/* Evidence */}
      <td className="py-2.5 pr-3">
        <input type="file" ref={fileRef} className="hidden" onChange={handleFile} />
        {result?.evidence
          ? (
            <span className="text-[10px] text-lime-DEFAULT truncate max-w-[80px] block"
              title={result.evidence.name}>
              📎 {result.evidence.name}
            </span>
          )
          : !locked && (
            <button
              onClick={() => fileRef.current?.click()}
              className="text-[10px] text-text-muted hover:text-text-secondary
                         border border-border-base rounded px-1.5 py-0.5
                         hover:border-border-bright transition-colors"
            >
              Attach
            </button>
          )
        }
      </td>
      {/* Tester + time */}
      <td className="py-2.5 min-w-[100px]">
        {result?.executedAt && (
          <div className="text-[9px] text-text-muted leading-relaxed">
            <div className="text-text-secondary font-medium">
              {result.testerName || 'Tester'}
            </div>
            <div>{new Date(result.executedAt).toLocaleTimeString()}</div>
          </div>
        )}
      </td>
    </tr>
  )
}

// ── SignOffPanel ──────────────────────────────────────────────────
function SignOffPanel({ run, locked, onSign, apiLoading }) {
  const { setRunMeta, activeRunId, userProfile } = useAppStore()
  const runId = activeRunId
  const [error, setError] = useState('')

  useEffect(() => {
    if (!locked && !run.signerName && userProfile?.name) {
      setRunMeta(runId, 'signerName', userProfile.name)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId])

  const handleSign = () => {
    if (!run.signerName.trim()) { setError('Signer name is required.') ; return }
    setError('') ; onSign()
  }

  if (locked) {
    return (
      <div className="mx-6 mb-4 p-4 rounded-lg border border-lime-DEFAULT/30
                      bg-lime-DEFAULT/5">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lime-DEFAULT font-bold text-sm">✓ Test Run Locked</span>
          <span className="text-text-muted text-[10px]">
            {run.lockedAt ? new Date(run.lockedAt).toLocaleString() : ''}
          </span>
        </div>
        <p className="text-text-muted text-[11px] mb-2">
          Signed by:{' '}
          <span className="text-text-secondary font-medium">{run.signerName}</span>
          {' — '}{run.signingMeaning}
        </p>
        {run.reasoningHash && (
          <div className="font-mono text-[9px] text-text-muted bg-bg-card
                          px-3 py-2 rounded border border-border-base break-all">
            Chain-of-custody hash: {run.reasoningHash}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="mx-6 mb-4 p-4 rounded-lg border border-blue-DEFAULT/20
                    bg-blue-dim/40">
      <p className="text-xs font-semibold text-white mb-3">
        Sign &amp; Lock Test Run
        <span className="ml-2 text-[10px] text-text-muted font-normal">
          21 CFR Part 11 §11.50 — Electronic Signature
        </span>
      </p>
      <div className="flex items-end gap-3 flex-wrap">
        <div className="flex flex-col gap-1">
          <label className="text-[10px] text-text-muted">Signer Name</label>
          <input
            value={run.signerName}
            onChange={e => setRunMeta(runId, 'signerName', e.target.value)}
            placeholder="Full name…"
            className="evolv-input text-xs px-2 py-1.5 w-48"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[10px] text-text-muted">Meaning</label>
          <select
            value={run.signingMeaning}
            onChange={e => setRunMeta(runId, 'signingMeaning', e.target.value)}
            className="evolv-input evolv-select text-xs px-2 py-1.5"
          >
            <option>Approval of Test Execution</option>
            <option>Review of Test Results</option>
            <option>Witnessed Test Execution</option>
          </select>
        </div>
        <button
          onClick={handleSign}
          disabled={apiLoading}
          className={`
            px-4 py-1.5 rounded text-xs font-semibold bg-lime-DEFAULT text-bg-base
            hover:opacity-90 transition-opacity
            ${apiLoading ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          {apiLoading ? 'Signing…' : 'Sign & Lock'}
        </button>
      </div>
      {error && <p className="mt-2 text-[10px] text-red-400">{error}</p>}
    </div>
  )
}

// ── Empty state ───────────────────────────────────────────────────
function NoScriptsState() {
  return (
    <div className="flex flex-col h-full bg-bg-base items-center
                    justify-center gap-4 px-8">
      <span className="text-5xl opacity-20">🏭</span>
      <div className="text-center max-w-sm">
        <p className="text-text-secondary text-sm font-semibold mb-2">
          No test scripts loaded
        </p>
        <p className="text-text-muted text-xs leading-relaxed">
          Generate a test script from the{' '}
          <span className="text-blue-DEFAULT font-medium">Validation Factory</span>.
          Complete the UR/FR transformation and CSA test generation
          steps — your script will appear here automatically.
        </p>
        <p className="text-text-muted text-[10px] mt-3 opacity-60">
          Path: Validation Factory → Generate Reqs → UR/FR → Generate Test Script
        </p>
      </div>
    </div>
  )
}

// ── Keyboard shortcut hint strip ──────────────────────────────────
function KeyHintStrip() {
  return (
    <div className="flex items-center gap-3 px-6 py-1.5 bg-bg-surface shrink-0
                    border-b border-border-base">
      <span className="text-[9px] text-text-muted uppercase tracking-wider mr-1">
        Keyboard
      </span>
      {Object.entries(VERDICT_CONFIG).map(([, cfg]) => (
        <span key={cfg.key}
          className="flex items-center gap-1 text-[9px] text-text-muted">
          <kbd className="px-1 py-0.5 rounded border border-border-base
                          bg-bg-card font-mono text-[9px]">
            {cfg.key.toUpperCase()}
          </kbd>
          <span>{cfg.label}</span>
        </span>
      ))}
      <span className="text-[9px] text-text-muted">· auto-advances to next step</span>
    </div>
  )
}

// ── Main Verify page ──────────────────────────────────────────────
export default function Verify() {
  const {
    testScripts, testRuns, activeRunId, initTestRun,
    setStepResult, setRunMeta, lockTestRun,
    setPhaseComplete, setStatusBadge,
    briefingConfig, setBriefingAcknowledged, setBriefingOverride,
    briefingAcknowledged,
    defects, initUnscriptedSession, setSessionVerdict,
  } = useAppStore()

  const [activeTab,        setActiveTab]        = useState('execute')
  const [apiLoading,       setApiLoading]       = useState(false)
  const [apiError,         setApiError]         = useState('')
  const [pdfLoading,       setPdfLoading]       = useState(false)
  const [pdfError,         setPdfError]         = useState('')
  const [selectedScriptId, setSelectedScriptId] = useState(null)
  const [focusedStepIdx,   setFocusedStepIdx]   = useState(0)
  // Set of stepKeys with open defect forms
  const [openDefects,      setOpenDefects]      = useState(new Set())

  // ── Script selection ───────────────────────────────────────────
  const scriptIds      = Object.keys(testScripts)
  const activeScriptId = selectedScriptId ?? scriptIds[0] ?? null
  const activeScript   = activeScriptId ? testScripts[activeScriptId] : null

  // ── Derived state ──────────────────────────────────────────────
  const run         = activeRunId ? testRuns[activeRunId] : null
  const stepResults = run?.stepResults ?? {}
  const locked      = run?.status === 'locked'
  const steps       = activeScript?.steps ?? []
  const isHighRisk  = activeScript?.risk_level === 'High'

  const pass     = Object.values(stepResults).filter(r => r.verdict === 'pass').length
  const fail     = Object.values(stepResults).filter(r => r.verdict === 'fail').length
  const blocked  = Object.values(stepResults).filter(r => r.verdict === 'blocked').length
  const na       = Object.values(stepResults).filter(r => r.verdict === 'na').length
  const executed = pass + fail + blocked + na
  const allDone  = executed === steps.length && steps.length > 0
  const overallVerdict =
    fail > 0 ? 'FAIL' : blocked > 0 ? 'BLOCKED' : allDone ? 'PASS' : 'IN_PROGRESS'

  // Briefing state
  const isAcknowledged = !!briefingAcknowledged[activeRunId]
  const showBriefing   = !!activeRunId && !isAcknowledged && !locked

  // Briefing items: override > default
  const briefingItems = (() => {
    const override = briefingConfig?.overrides?.[activeScriptId]
    if (override) return override.items
    const riskLevel = activeScript?.risk_level ?? 'High'
    return briefingConfig?.defaults?.[riskLevel] ?? []
  })()

  // Defects for current run
  const runDefects = run ? (defects[run.runId] ?? []) : []

  // Init a run when active script changes and no run exists
  useEffect(() => {
    if (activeScript && !activeRunId) initTestRun(activeScript)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeScriptId])

  // Auto-switch to ALCOA tab after locking
  useEffect(() => {
    if (locked) setActiveTab(t => t === 'execute' ? 'alcoa' : t)
  }, [locked])

  // Reset focused step when script changes
  useEffect(() => { setFocusedStepIdx(0) }, [activeScriptId])

  // ── Keyboard shortcuts (scripted HIGH risk only) ──────────────
  useEffect(() => {
    if (!isHighRisk || showBriefing || locked || activeTab !== 'execute') return

    const execSteps = steps.filter(s => s.step_type !== 'Setup')

    const handler = e => {
      const tag = e.target.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

      const keyMap = { p: 'pass', f: 'fail', b: 'blocked', n: 'na' }
      const verdict = keyMap[e.key.toLowerCase()]
      if (!verdict || !activeRunId) return

      const step = execSteps[focusedStepIdx]
      if (!step) return

      const stepKey = `${step.step_number}_${step.step_type}`
      setStepResult(activeRunId, stepKey, 'verdict', verdict)
      setStepResult(activeRunId, stepKey, 'executedAt', new Date().toISOString())

      if (verdict === 'fail') {
        setOpenDefects(s => new Set([...s, stepKey]))
      }

      // Auto-advance to next incomplete execution step
      const next = execSteps.findIndex(
        (s, i) =>
          i > focusedStepIdx &&
          !stepResults[`${s.step_number}_${s.step_type}`]?.verdict
      )
      if (next !== -1) setFocusedStepIdx(next)

      e.preventDefault()
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isHighRisk, showBriefing, locked, activeTab,
      focusedStepIdx, steps, stepResults, activeRunId, setStepResult])

  // ── Handlers ──────────────────────────────────────────────────
  const handleVerdictChange = (stepKey, verdict) => {
    if (!activeRunId) return
    setStepResult(activeRunId, stepKey, 'verdict', verdict)
    setStepResult(activeRunId, stepKey, 'executedAt', new Date().toISOString())
    if (verdict === 'fail') {
      setOpenDefects(s => new Set([...s, stepKey]))
    } else {
      setOpenDefects(s => { const n = new Set(s) ; n.delete(stepKey) ; return n })
    }
  }

  const handleActualChange = (stepKey, value) => {
    if (!activeRunId) return
    setStepResult(activeRunId, stepKey, 'actualResult', value)
  }

  const handleEvidenceChange = (stepKey, evidence) => {
    if (!activeRunId) return
    setStepResult(activeRunId, stepKey, 'evidence', evidence)
  }

  const handleTesterChange = (stepKey, field, value) => {
    if (!activeRunId) return
    setStepResult(activeRunId, stepKey, field, value)
  }

  const handleAcknowledge = data => {
    setBriefingAcknowledged(activeRunId, data)
    if (!isHighRisk) initUnscriptedSession(activeRunId)
  }

  const handleCharterComplete = overallVerdict => {
    if (!run) return
    const verdictLabel =
      overallVerdict === 'PASS' ? 'Satisfactory'
      : overallVerdict === 'FAIL' ? 'Unsatisfactory'
      : 'Incomplete'
    setSessionVerdict(activeRunId, verdictLabel)
    lockTestRun(activeRunId, null)
    setPhaseComplete('verify')
    setStatusBadge('verify', {
      type:  overallVerdict === 'PASS' ? 'success' : 'warning',
      label: overallVerdict === 'PASS' ? 'Passed' : 'Review',
    })
    setActiveTab('alcoa')
  }

  const handleSignOff = async () => {
    if (!run) return
    const failMissingActual = steps.some(step => {
      const key    = `${step.step_number}_${step.step_type}`
      const result = stepResults[key]
      return result?.verdict === 'fail' && !result?.actualResult?.trim()
    })
    if (failMissingActual) {
      setApiError('All failed steps must have an actual result before signing.')
      return
    }
    setApiLoading(true) ; setApiError('')
    try {
      const res = await fetch(`${API_BASE}/verify/sign-off`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_id:       activeScript.script_id,
          run_id:          run.runId,
          urs_id:          activeScript.urs_id,
          signer_name:     run.signerName,
          meaning:         run.signingMeaning,
          pass_count:      pass, fail_count: fail,
          blocked_count:   blocked, na_count: na,
          total_steps:     steps.length,
          overall_verdict: overallVerdict,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail ?? 'Sign-off failed')
      }
      const data = await res.json()
      lockTestRun(run.runId, data.reasoning_hash)
      setPhaseComplete('verify')
      setStatusBadge('verify', {
        type:  'success',
        label: overallVerdict === 'PASS' ? 'Passed' : 'Review',
      })
      setActiveTab('alcoa')
    } catch (err) {
      // Offline fallback — lock locally without API hash
      lockTestRun(run.runId, null)
      setPhaseComplete('verify')
      setStatusBadge('verify', {
        type:  'success',
        label: overallVerdict === 'PASS' ? 'Passed' : 'Review',
      })
      setActiveTab('alcoa')
      setApiError(
        `Sign-off recorded locally (API offline): ${err.message}`
      )
    } finally {
      setApiLoading(false)
    }
  }

  const handleExportCSV = useCallback(() => {
    const headers = [
      'step_number', 'step_type', 'step_title', 'test_case_type',
      'requirement_reference', 'verdict', 'actual_result', 'executed_at',
    ]
    const rows = steps.map(step => {
      const key = `${step.step_number}_${step.step_type}`
      const res = stepResults[key] ?? {}
      return {
        step_number:           step.step_number,
        step_type:             step.step_type,
        step_title:            step.step_title,
        test_case_type:        step.test_case_type,
        requirement_reference: step.requirement_reference,
        verdict:               res.verdict ?? '',
        actual_result:         res.actualResult ?? '',
        executed_at:           res.executedAt ?? '',
      }
    })
    downloadCSV(`${activeScript.script_id}-results.csv`, headers, rows)
  }, [steps, stepResults, activeScript])

  const handleExportPDF = useCallback(async () => {
    if (!run) return
    setPdfLoading(true) ; setPdfError('')
    try {
      const stepsPayload = steps.map(step => {
        const key = `${step.step_number}_${step.step_type}`
        const res = stepResults[key] ?? {}
        return {
          step_number: step.step_number, step_type: step.step_type,
          step_title: step.step_title, step_instruction: step.step_instruction,
          expected_result: step.expected_result, test_case_type: step.test_case_type,
          requirement_reference: step.requirement_reference,
          verdict: res.verdict ?? null, actual_result: res.actualResult ?? '',
          executed_at: res.executedAt ?? null, tester_name: res.testerName ?? '',
        }
      })
      await downloadPDF(
        `${API_BASE}/exports/verify-report`,
        {
          script_id: activeScript.script_id, urs_id: activeScript.urs_id,
          ur_id: activeScript.ur_id, test_type: activeScript.test_type,
          risk_level: activeScript.risk_level, test_strategy: activeScript.test_strategy,
          run_id: run.runId, started_at: run.startedAt, locked_at: run.lockedAt,
          signer_name: run.signerName || 'Unsigned', signing_meaning: run.signingMeaning,
          reasoning_hash: run.reasoningHash, pass_count: pass, fail_count: fail,
          blocked_count: blocked, na_count: na, total_steps: steps.length,
          overall_verdict: overallVerdict, steps: stepsPayload,
        },
        `${activeScript.script_id}-report.pdf`,
      )
    } catch (err) {
      setPdfError(`PDF export failed: ${err.message}. Ensure FastAPI is running.`)
    } finally {
      setPdfLoading(false)
    }
  }, [steps, stepResults, activeScript, run, pass, fail, blocked, na, overallVerdict])

  // ── Risk badge config ─────────────────────────────────────────
  const RISK_COLORS = {
    High:   { bg: 'rgba(239,68,68,0.12)',  text: '#ef4444' },
    Medium: { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b' },
    Low:    { bg: 'rgba(50,205,50,0.12)',  text: '#32CD32' },
  }
  const riskCfg = RISK_COLORS[activeScript?.risk_level] ?? RISK_COLORS.Low

  // ── Tab definitions ───────────────────────────────────────────
  const TABS = [
    { id: 'execute', label: showBriefing ? '📋 Briefing' : '▶ Execute Test' },
    { id: 'review',  label: '📋 Script Review' },
    ...(locked ? [{ id: 'alcoa', label: '🔍 ALCOA Report' }] : []),
  ]

  if (!activeScript) return <NoScriptsState />

  // Execution steps for keyboard nav
  const execSteps = steps.filter(s => s.step_type !== 'Setup')

  return (
    <div className="flex flex-col h-full bg-bg-base overflow-hidden">

      {/* ── Header strip ──────────────────────────────────── */}
      <div className="flex items-center gap-3 px-6 py-2.5
                      bg-lime-dim border-b border-lime-DEFAULT/20 shrink-0">
        <span className="text-xs font-semibold text-lime-DEFAULT">Verify</span>

        {scriptIds.length > 1 ? (
          <select
            value={activeScriptId ?? ''}
            onChange={e => setSelectedScriptId(e.target.value)}
            className="bg-bg-base border border-border-base rounded px-2 py-1
                       text-xs text-text-secondary outline-none
                       focus:border-blue-DEFAULT transition-colors"
          >
            {scriptIds.map(id => (
              <option key={id} value={id}>{id}</option>
            ))}
          </select>
        ) : (
          <span className="text-text-muted text-xs">
            {activeScript.script_id} · {activeScript.urs_id}
          </span>
        )}

        <span
          className="text-[9px] font-semibold px-2 py-0.5 rounded-full"
          style={{ background: riskCfg.bg, color: riskCfg.text }}
        >
          {activeScript.risk_level} Risk
        </span>
        <span className="text-[10px] text-text-muted px-2 py-0.5 rounded
                         border border-border-base">
          {activeScript.test_type}
        </span>

        {/* Export buttons (only when not in briefing) */}
        {!showBriefing && (
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={handleExportCSV}
              className="text-[10px] px-2 py-1 rounded border border-border-base
                         text-text-muted hover:text-text-secondary
                         hover:border-border-bright transition-colors"
            >
              📥 Export CSV
            </button>
            <button
              onClick={handleExportPDF}
              disabled={pdfLoading}
              className={`
                text-[10px] px-2 py-1 rounded border font-medium transition-colors
                ${pdfLoading
                  ? 'border-border-base text-text-muted opacity-50'
                  : 'border-blue-DEFAULT/40 text-blue-DEFAULT bg-blue-dim'}
              `}
            >
              {pdfLoading ? 'Generating…' : '📄 PDF Report'}
            </button>
          </div>
        )}

        {/* Tabs */}
        <div className={`flex gap-1 ${showBriefing ? 'ml-auto' : ''}`}>
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                px-3 py-1 text-[11px] rounded transition-colors
                ${activeTab === tab.id
                  ? tab.id === 'alcoa'
                    ? 'bg-blue-DEFAULT/20 text-blue-DEFAULT'
                    : 'bg-lime-DEFAULT/20 text-lime-DEFAULT'
                  : 'text-text-muted hover:text-text-secondary'}
              `}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Execute tab ───────────────────────────────────── */}
      {activeTab === 'execute' && (
        <>
          {/* Briefing panel — shown until acknowledged */}
          {showBriefing ? (
            <BriefingPanel
              script={activeScript}
              riskLevel={activeScript.risk_level}
              items={briefingItems}
              onAcknowledge={handleAcknowledge}
              onEdit={items => setBriefingOverride(activeScriptId, items)}
            />
          ) : isHighRisk ? (
            /* Scripted execution — HIGH risk */
            <>
              <KeyHintStrip />
              <RunSummaryBar steps={steps} stepResults={stepResults} />

              {(apiError || pdfError) && (
                <div className="mx-6 mt-3 px-4 py-2 rounded border
                                border-red-500/30 bg-red-500/10 text-[11px]
                                text-red-400 shrink-0 space-y-1">
                  {apiError && <div>{apiError}</div>}
                  {pdfError && <div>{pdfError}</div>}
                </div>
              )}

              <div className="flex-1 overflow-auto px-6 py-4">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-border-base">
                      {[
                        'Type', '#', 'Title', 'Instruction',
                        'Expected Result', 'Case', 'Ref',
                        'Verdict', 'Actual Result', 'Evidence', 'Tester',
                      ].map(h => (
                        <th key={h}
                          className="text-left text-[10px] font-semibold
                                     text-text-muted uppercase tracking-wide
                                     py-2 pr-3 whitespace-nowrap">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {steps.map((step, globalIdx) => {
                      const key     = `${step.step_number}_${step.step_type}`
                      const isExec  = step.step_type !== 'Setup'
                      const execIdx = isExec
                        ? execSteps.findIndex(s =>
                            s.step_number === step.step_number &&
                            s.step_type   === step.step_type)
                        : -1
                      const focused = isExec && execIdx === focusedStepIdx
                      return (
                        <>
                          <StepRow
                            key={key}
                            step={step}
                            result={stepResults[key] ?? {}}
                            locked={locked}
                            isFocused={focused}
                            onVerdictChange={handleVerdictChange}
                            onActualChange={handleActualChange}
                            onEvidenceChange={ev => handleEvidenceChange(key, ev)}
                            onTesterChange={handleTesterChange}
                          />
                          {/* Inline defect form for failed steps */}
                          {stepResults[key]?.verdict === 'fail' &&
                           openDefects.has(key) && (
                            <DefectForm
                              key={`def-${key}`}
                              stepKey={key}
                              stepTitle={step.step_title}
                              runId={activeRunId}
                              onDismiss={() =>
                                setOpenDefects(s => {
                                  const n = new Set(s) ; n.delete(key) ; return n
                                })
                              }
                            />
                          )}
                          {/* Log defect button for closed defect form */}
                          {stepResults[key]?.verdict === 'fail' &&
                           !openDefects.has(key) &&
                           !locked && (
                            <tr key={`def-btn-${key}`}>
                              <td colSpan={11}
                                className="pb-1 px-4 border-b border-border-base">
                                <button
                                  onClick={() =>
                                    setOpenDefects(s => new Set([...s, key]))}
                                  className="text-[9px] text-red-400 hover:text-red-300
                                             underline underline-offset-2"
                                >
                                  + Log Defect for this step
                                </button>
                              </td>
                            </tr>
                          )}
                        </>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {allDone && run && (
                <SignOffPanel
                  run={run}
                  locked={locked}
                  onSign={handleSignOff}
                  apiLoading={apiLoading}
                />
              )}
              {!allDone && !locked && (
                <div className="px-6 pb-4 shrink-0">
                  <p className="text-[10px] text-text-muted">
                    Execute all {steps.length} steps to unlock sign-off.
                    {isHighRisk && (
                      <span className="ml-2 text-text-muted opacity-60">
                        Tip: use P/F/B/N keys to record verdicts quickly.
                      </span>
                    )}
                  </p>
                </div>
              )}
            </>
          ) : (
            /* Unscripted charter — MEDIUM / LOW risk */
            <UnscriptedCharter
              script={activeScript}
              runId={activeRunId}
              locked={locked}
              onComplete={handleCharterComplete}
            />
          )}
        </>
      )}

      {/* ── Script Review tab ─────────────────────────────── */}
      {activeTab === 'review' && (
        <div className="flex-1 overflow-auto px-6 py-4">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border-base">
                {['Type', '#', 'Title', 'Instruction',
                  'Expected Result', 'Case', 'Ref'].map(h => (
                  <th key={h}
                    className="text-left text-[10px] font-semibold text-text-muted
                               uppercase tracking-wide py-2 pr-4 whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {steps.map(step => {
                const isSetup   = step.step_type === 'Setup'
                const caseColor = CASE_COLORS[step.test_case_type]
                return (
                  <tr key={`${step.step_number}_${step.step_type}`}
                    className="border-b border-border-base hover:bg-bg-hover/30
                               transition-colors">
                    <td className="py-2.5 pr-3">
                      <span className={`
                        text-[9px] px-1.5 py-0.5 rounded font-semibold uppercase
                        ${isSetup
                          ? 'bg-bg-card text-text-muted border border-border-base'
                          : 'bg-blue-dim text-blue-DEFAULT border border-blue-DEFAULT/30'}
                      `}>
                        {step.step_type}
                      </span>
                    </td>
                    <td className="py-2.5 pr-3 font-mono text-text-muted text-[11px]">
                      {step.step_number}
                    </td>
                    <td className="py-2.5 pr-4 text-text-secondary text-[11px]
                                   font-medium max-w-[160px]">
                      {step.step_title}
                    </td>
                    <td className="py-2.5 pr-4 text-text-muted text-[11px]
                                   max-w-[240px] leading-relaxed">
                      {step.step_instruction}
                    </td>
                    <td className="py-2.5 pr-4 text-text-muted text-[11px] max-w-[200px]">
                      {step.expected_result || (
                        <span className="opacity-40 italic">Setup step</span>
                      )}
                    </td>
                    <td className="py-2.5 pr-4">
                      {caseColor
                        ? (
                          <span className="text-[9px] px-1.5 py-0.5 rounded font-semibold"
                            style={{ background: caseColor.bg, color: caseColor.text }}>
                            {step.test_case_type}
                          </span>
                        )
                        : <span className="text-text-muted opacity-40">—</span>
                      }
                    </td>
                    <td className="py-2.5 font-mono text-[10px] text-text-muted">
                      {step.requirement_reference || '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          <div className="mt-6 flex items-center gap-6 text-[10px] text-text-muted">
            <span>Script: <span className="text-text-secondary font-mono">
              {activeScript.script_id}
            </span></span>
            <span>Strategy: <span className="text-text-secondary">
              {activeScript.test_strategy}
            </span></span>
            <span>Generated: <span className="text-text-secondary">
              {new Date(activeScript.generated_at).toLocaleDateString()}
            </span></span>
          </div>
        </div>
      )}

      {/* ── ALCOA Report tab ──────────────────────────────── */}
      {activeTab === 'alcoa' && (
        <ALCOAReport
          script={activeScript}
          run={run}
          steps={steps}
          stepResults={stepResults}
          defects={runDefects}
        />
      )}
    </div>
  )
}
