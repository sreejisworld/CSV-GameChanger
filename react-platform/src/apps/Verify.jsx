/**
 * Verify — Lifecycle Phase 5: Test Execution
 *
 * React-native page (no iframe) — requires tight UI feedback for
 * real-time step execution, progress tracking, and sign-off.
 *
 * Tabs:
 *   Execute Test  — step-by-step execution with Pass/Fail/Blocked/N/A
 *   Script Review — read-only view of the generated test script
 */
import { useState, useRef, useCallback, useEffect } from 'react'
import { useAppStore }       from '../store/useAppStore.js'

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

// ── Demo test script (Sprint 1 seed — real data via API in Sprint 2) ──
const DEMO_SCRIPT = {
  script_id:    'TS-URS-7.1',
  urs_id:       'URS-7.1',
  ur_id:        'UR-1',
  test_type:    'Informal',
  risk_level:   'High',
  test_strategy:'OQ and/or UAT',
  generated_at: new Date().toISOString(),
  steps: [
    {
      step_type: 'Setup', step_number: 1,
      step_title: 'Login as System Owner',
      step_instruction:
        'Navigate to the application URL and login with System Owner ' +
        'credentials. Confirm role is displayed in the top-right header.',
      expected_result: '',
      test_case_type: '',
      requirement_reference: '',
    },
    {
      step_type: 'Setup', step_number: 2,
      step_title: 'Navigate to Sample Registration',
      step_instruction:
        'From the home screen, navigate to Laboratory > Sample Registration ' +
        'and confirm the module loads without errors.',
      expected_result: '',
      test_case_type: '',
      requirement_reference: '',
    },
    {
      step_type: 'Execution', step_number: 1,
      step_title: 'Register Sample — Positive',
      step_instruction:
        'Enter a valid sample ID, collection date, and submitting user. ' +
        'Click "Register". Verify the sample appears in the chain-of-custody ' +
        'list with a unique COC number.',
      expected_result:
        'Sample is registered. Unique COC number is generated. ' +
        'Timestamp and user are captured in the audit trail.',
      test_case_type: 'Positive',
      requirement_reference: 'UR-1 / FR-1',
    },
    {
      step_type: 'Execution', step_number: 2,
      step_title: 'Register Sample — Negative (duplicate ID)',
      step_instruction:
        'Attempt to register a sample using an ID that already exists in ' +
        'the system. Click "Register".',
      expected_result:
        'System rejects the duplicate. An error message is displayed: ' +
        '"Sample ID already registered." No COC record is created.',
      test_case_type: 'Negative',
      requirement_reference: 'UR-1 / FR-2',
    },
    {
      step_type: 'Execution', step_number: 3,
      step_title: 'Register Sample — Edge Case (max length ID)',
      step_instruction:
        'Enter a sample ID at the maximum allowed character length (255 chars). ' +
        'Complete registration.',
      expected_result:
        'System accepts the max-length ID without truncation. ' +
        'COC record stores full ID.',
      test_case_type: 'Edge Case',
      requirement_reference: 'UR-1 / FR-1',
    },
    {
      step_type: 'Execution', step_number: 4,
      step_title: 'Electronic Signature — Positive',
      step_instruction:
        'Navigate to a sample result awaiting approval. Enter valid ' +
        'credentials and meaning "Approval". Click "Sign".',
      expected_result:
        'Signature is accepted. Result status changes to "Approved". ' +
        'Audit trail records signer name, timestamp, and meaning.',
      test_case_type: 'Positive',
      requirement_reference: 'UR-3 / FR-4',
    },
    {
      step_type: 'Execution', step_number: 5,
      step_title: 'Audit Trail — Immutability Check',
      step_instruction:
        'Attempt to edit a previously signed audit trail entry directly ' +
        'via the UI or by navigating to the audit trail record.',
      expected_result:
        'No edit control is available. All fields are read-only. ' +
        'Audit trail is append-only per 21 CFR Part 11.',
      test_case_type: 'Negative',
      requirement_reference: 'UR-3 / FR-5',
    },
  ],
}

// ── Colours ───────────────────────────────────────────────────────
const VERDICT_CONFIG = {
  pass:    { label: 'Pass',    bg: 'rgba(50,205,50,0.15)',   border: 'rgba(50,205,50,0.4)',   text: '#32CD32' },
  fail:    { label: 'Fail',    bg: 'rgba(239,68,68,0.15)',   border: 'rgba(239,68,68,0.4)',   text: '#ef4444' },
  blocked: { label: 'Blocked', bg: 'rgba(245,158,11,0.15)',  border: 'rgba(245,158,11,0.4)',  text: '#f59e0b' },
  na:      { label: 'N/A',     bg: 'rgba(100,116,139,0.15)', border: 'rgba(100,116,139,0.4)', text: '#64748b' },
}

const CASE_COLORS = {
  Positive:   { bg: 'rgba(50,205,50,0.12)',  text: '#32CD32' },
  Negative:   { bg: 'rgba(239,68,68,0.12)',  text: '#ef4444' },
  'Edge Case':{ bg: 'rgba(245,158,11,0.12)', text: '#f59e0b' },
}

// ── Sub-components ────────────────────────────────────────────────

function VerdictButton({ verdict, active, locked, onClick }) {
  const cfg = VERDICT_CONFIG[verdict]
  return (
    <button
      onClick={locked ? undefined : onClick}
      disabled={locked}
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

function RunSummaryBar({ steps, stepResults }) {
  const total    = steps.length
  const pass     = Object.values(stepResults).filter(r => r.verdict === 'pass').length
  const fail     = Object.values(stepResults).filter(r => r.verdict === 'fail').length
  const blocked  = Object.values(stepResults).filter(r => r.verdict === 'blocked').length
  const na       = Object.values(stepResults).filter(r => r.verdict === 'na').length
  const executed = pass + fail + blocked + na
  const pct      = total ? Math.round((executed / total) * 100) : 0

  let verdict = 'IN PROGRESS'
  let vColor  = '#64748b'
  if (executed === total && total > 0) {
    if (fail > 0)    { verdict = 'FAIL';    vColor = '#ef4444' }
    else if (blocked > 0) { verdict = 'BLOCKED'; vColor = '#f59e0b' }
    else             { verdict = 'PASS';    vColor = '#32CD32' }
  }

  return (
    <div className="px-6 py-3 bg-bg-surface border-b border-border-base shrink-0">
      {/* Progress bar */}
      <div className="flex items-center gap-3 mb-2">
        <span className="text-[10px] text-text-muted w-20 shrink-0">
          Progress
        </span>
        <div className="flex-1 h-1.5 bg-bg-card rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{
              width: `${pct}%`,
              background: fail > 0
                ? '#ef4444'
                : blocked > 0
                  ? '#f59e0b'
                  : '#32CD32',
            }}
          />
        </div>
        <span className="text-[10px] text-text-muted w-10 text-right shrink-0">
          {pct}%
        </span>
      </div>

      {/* Counts + verdict */}
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
        <span className="text-text-muted text-[10px]">
          / {total} steps
        </span>
        <span
          className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded"
          style={{
            color: vColor,
            background: vColor + '20',
            border: `1px solid ${vColor}40`,
          }}
        >
          {verdict}
        </span>
      </div>
    </div>
  )
}

function StepRow({ step, result, locked, onVerdictChange, onActualChange,
                   onEvidenceChange, onTesterChange }) {
  const stepKey   = `${step.step_number}_${step.step_type}`
  const isSetup   = step.step_type === 'Setup'
  const caseColor = CASE_COLORS[step.test_case_type]
  const fileRef   = useRef(null)

  const handleFile = e => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 5 * 1024 * 1024) {
      alert('Evidence file must be under 5 MB.')
      return
    }
    const reader = new FileReader()
    reader.onload = ev => onEvidenceChange({
      name: file.name, size: file.size, dataUrl: ev.target.result,
    })
    reader.readAsDataURL(file)
  }

  return (
    <tr className={`
      border-b border-border-base transition-colors
      ${result?.verdict === 'fail'
        ? 'bg-red-500/5'
        : result?.verdict === 'pass'
          ? 'bg-lime-500/5'
          : 'hover:bg-bg-hover/30'}
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
        {step.step_number}
      </td>

      {/* Title */}
      <td className="py-2.5 pr-4 text-text-secondary text-[11px] font-medium
                     max-w-[140px]">
        <span className="line-clamp-2">{step.step_title}</span>
      </td>

      {/* Instruction */}
      <td className="py-2.5 pr-4 text-text-muted text-[11px] max-w-[200px]">
        <span className="line-clamp-3 leading-relaxed">
          {step.step_instruction}
        </span>
      </td>

      {/* Expected result */}
      <td className="py-2.5 pr-4 text-text-muted text-[11px] max-w-[160px]">
        {step.expected_result
          ? <span className="line-clamp-3">{step.expected_result}</span>
          : <span className="text-text-muted opacity-40 italic">Setup step</span>
        }
      </td>

      {/* Case type */}
      <td className="py-2.5 pr-4 whitespace-nowrap">
        {caseColor
          ? (
            <span
              className="text-[9px] px-1.5 py-0.5 rounded font-semibold"
              style={{ background: caseColor.bg, color: caseColor.text }}
            >
              {step.test_case_type}
            </span>
          )
          : <span className="text-text-muted opacity-40">—</span>
        }
      </td>

      {/* Ref */}
      <td className="py-2.5 pr-4 font-mono text-[10px] text-text-muted
                     whitespace-nowrap">
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
                onTesterChange(stepKey, 'executedAt',
                  new Date().toISOString())
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
        <input
          type="file"
          ref={fileRef}
          className="hidden"
          onChange={handleFile}
        />
        {result?.evidence
          ? (
            <span className="text-[10px] text-lime-DEFAULT truncate max-w-[80px]
                             block" title={result.evidence.name}>
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
            <div>
              {new Date(result.executedAt).toLocaleTimeString()}
            </div>
          </div>
        )}
      </td>
    </tr>
  )
}

function SignOffPanel({ run, locked, onSign, apiLoading }) {
  const {
    setRunMeta, activeRunId, userProfile,
  } = useAppStore()
  const runId = activeRunId

  const [error, setError] = useState('')

  // Auto-fill signer name from user profile when field is blank
  useEffect(() => {
    if (!locked && !run.signerName && userProfile?.name) {
      setRunMeta(runId, 'signerName', userProfile.name)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId])

  const handleSign = () => {
    if (!run.signerName.trim()) {
      setError('Signer name is required.')
      return
    }
    setError('')
    onSign()
  }

  if (locked) {
    return (
      <div className="mx-6 mb-4 p-4 rounded-lg border border-lime-DEFAULT/30
                      bg-lime-DEFAULT/5">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lime-DEFAULT font-bold text-sm">
            ✓ Test Run Locked
          </span>
          <span className="text-text-muted text-[10px]">
            {run.lockedAt
              ? new Date(run.lockedAt).toLocaleString()
              : ''}
          </span>
        </div>
        <p className="text-text-muted text-[11px] mb-2">
          Signed by: <span className="text-text-secondary font-medium">
            {run.signerName}
          </span>
          {' — '}{run.signingMeaning}
        </p>
        {run.reasoningHash && (
          <div className="font-mono text-[9px] text-text-muted
                          bg-bg-card px-3 py-2 rounded border border-border-base
                          break-all">
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
            onChange={e =>
              setRunMeta(runId, 'signingMeaning', e.target.value)}
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
            px-4 py-1.5 rounded text-xs font-semibold
            bg-lime-DEFAULT text-bg-base
            hover:opacity-90 transition-opacity
            ${apiLoading ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          {apiLoading ? 'Signing…' : 'Sign & Lock'}
        </button>
      </div>
      {error && (
        <p className="mt-2 text-[10px] text-red-400">{error}</p>
      )}
    </div>
  )
}

// ── Main Verify page ──────────────────────────────────────────────
export default function Verify() {
  const {
    testScripts, setTestScript,
    testRuns, activeRunId, initTestRun,
    setStepResult, setRunMeta, lockTestRun,
    setPhaseComplete, setStatusBadge,
  } = useAppStore()

  const [activeTab,  setActiveTab]  = useState('execute')
  const [apiLoading, setApiLoading] = useState(false)
  const [apiError,   setApiError]   = useState('')
  const [pdfLoading, setPdfLoading] = useState(false)
  const [pdfError,   setPdfError]   = useState('')

  // ── Derived state (must be declared before useCallback hooks) ──
  const activeScript = testScripts['TS-URS-7.1'] ?? DEMO_SCRIPT
  const run          = activeRunId ? testRuns[activeRunId] : null
  const stepResults  = run?.stepResults ?? {}
  const locked       = run?.status === 'locked'
  const steps        = activeScript.steps ?? []
  const pass     = Object.values(stepResults).filter(r => r.verdict === 'pass').length
  const fail     = Object.values(stepResults).filter(r => r.verdict === 'fail').length
  const blocked  = Object.values(stepResults).filter(r => r.verdict === 'blocked').length
  const na       = Object.values(stepResults).filter(r => r.verdict === 'na').length
  const executed = pass + fail + blocked + na
  const allDone  = executed === steps.length && steps.length > 0
  const overallVerdict = fail > 0 ? 'FAIL'
    : blocked > 0 ? 'BLOCKED'
    : allDone     ? 'PASS'
    : 'IN_PROGRESS'

  // Seed demo script once on mount
  useEffect(() => {
    const existing = testScripts['TS-URS-7.1'] ?? null
    if (!existing) {
      setTestScript('TS-URS-7.1', DEMO_SCRIPT)
      initTestRun(DEMO_SCRIPT)
    } else if (!activeRunId) {
      initTestRun(existing)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleExportCSV = useCallback(() => {
    const headers = [
      'step_number', 'step_type', 'step_title',
      'test_case_type', 'requirement_reference',
      'verdict', 'actual_result', 'executed_at',
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
    downloadCSV(
      `${activeScript.script_id}-results.csv`, headers, rows
    )
  }, [steps, stepResults, activeScript])

  const handleExportPDF = useCallback(async () => {
    if (!run) return
    setPdfLoading(true)
    setPdfError('')
    try {
      const stepsPayload = steps.map(step => {
        const key = `${step.step_number}_${step.step_type}`
        const res = stepResults[key] ?? {}
        return {
          step_number:           step.step_number,
          step_type:             step.step_type,
          step_title:            step.step_title,
          step_instruction:      step.step_instruction,
          expected_result:       step.expected_result,
          test_case_type:        step.test_case_type,
          requirement_reference: step.requirement_reference,
          verdict:               res.verdict ?? null,
          actual_result:         res.actualResult ?? '',
          executed_at:           res.executedAt ?? null,
          tester_name:           res.testerName ?? '',
        }
      })
      await downloadPDF(
        'http://localhost:8000/exports/verify-report',
        {
          script_id:       activeScript.script_id,
          urs_id:          activeScript.urs_id,
          ur_id:           activeScript.ur_id,
          test_type:       activeScript.test_type,
          risk_level:      activeScript.risk_level,
          test_strategy:   activeScript.test_strategy,
          run_id:          run.runId,
          started_at:      run.startedAt,
          locked_at:       run.lockedAt,
          signer_name:     run.signerName || 'Unsigned',
          signing_meaning: run.signingMeaning,
          reasoning_hash:  run.reasoningHash,
          pass_count:      pass,
          fail_count:      fail,
          blocked_count:   blocked,
          na_count:        na,
          total_steps:     steps.length,
          overall_verdict: overallVerdict,
          steps:           stepsPayload,
        },
        `${activeScript.script_id}-report.pdf`,
      )
    } catch (err) {
      setPdfError(
        `PDF export failed: ${err.message}. ` +
        'Ensure FastAPI is running on port 8000.'
      )
    } finally {
      setPdfLoading(false)
    }
  }, [steps, stepResults, activeScript, run,
      pass, fail, blocked, na, overallVerdict])

  // Check all fail-verdict steps have actual results
  const failStepsMissingActual = steps.some(step => {
    const key    = `${step.step_number}_${step.step_type}`
    const result = stepResults[key]
    return result?.verdict === 'fail' && !result?.actualResult?.trim()
  })

  const handleVerdictChange = (stepKey, verdict) => {
    if (!activeRunId) return
    setStepResult(activeRunId, stepKey, 'verdict', verdict)
    setStepResult(activeRunId, stepKey, 'executedAt',
      new Date().toISOString())
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

  const handleSignOff = async () => {
    if (!run) return
    if (failStepsMissingActual) {
      setApiError(
        'All failed steps must have an actual result before signing.'
      )
      return
    }
    setApiLoading(true)
    setApiError('')
    try {
      const res = await fetch('http://localhost:8000/verify/sign-off', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_id:       activeScript.script_id,
          run_id:          run.runId,
          urs_id:          activeScript.urs_id,
          signer_name:     run.signerName,
          meaning:         run.signingMeaning,
          pass_count:      pass,
          fail_count:      fail,
          blocked_count:   blocked,
          na_count:        na,
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
        type: 'success',
        label: overallVerdict === 'PASS' ? 'Passed' : 'Review',
      })
    } catch (err) {
      setApiError(
        `Sign-off failed: ${err.message}. ` +
        'Ensure FastAPI is running on port 8000.'
      )
    } finally {
      setApiLoading(false)
    }
  }

  const RISK_COLORS = {
    High:   { bg: 'rgba(239,68,68,0.12)',  text: '#ef4444' },
    Medium: { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b' },
    Low:    { bg: 'rgba(50,205,50,0.12)',  text: '#32CD32' },
  }
  const riskCfg = RISK_COLORS[activeScript.risk_level] ?? RISK_COLORS.Low

  return (
    <div className="flex flex-col h-full bg-bg-base overflow-hidden">

      {/* ── Header strip ──────────────────────────────────── */}
      <div className="flex items-center gap-4 px-6 py-2.5
                      bg-lime-dim border-b border-lime-DEFAULT/20 shrink-0">
        <span className="text-xs font-semibold text-lime-DEFAULT">
          Verify
        </span>
        <span className="text-text-muted text-xs">
          {activeScript.script_id} · {activeScript.urs_id}
        </span>
        {/* Risk badge */}
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
        {/* Export buttons */}
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="text-[10px] px-2 py-1 rounded border
                       border-border-base text-text-muted
                       hover:text-text-secondary hover:border-border-bright
                       transition-colors"
          >
            📥 Export CSV
          </button>
          <button
            onClick={handleExportPDF}
            disabled={pdfLoading}
            className={`
              text-[10px] px-2 py-1 rounded border font-medium
              transition-colors
              ${pdfLoading
                ? 'border-border-base text-text-muted opacity-50'
                : 'border-blue-DEFAULT/40 text-blue-DEFAULT bg-blue-dim'
              }
            `}
          >
            {pdfLoading ? 'Generating…' : '📄 PDF Report'}
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1">
          {[
            { id: 'execute', label: '▶ Execute Test' },
            { id: 'review',  label: '📋 Script Review' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                px-3 py-1 text-[11px] rounded transition-colors
                ${activeTab === tab.id
                  ? 'bg-lime-DEFAULT/20 text-lime-DEFAULT'
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
          {/* Progress bar */}
          <RunSummaryBar steps={steps} stepResults={stepResults} />

          {/* API / export errors */}
          {(apiError || pdfError) && (
            <div className="mx-6 mt-3 px-4 py-2 rounded border
                            border-red-500/30 bg-red-500/10 text-[11px]
                            text-red-400 shrink-0 space-y-1">
              {apiError && <div>{apiError}</div>}
              {pdfError && <div>{pdfError}</div>}
            </div>
          )}

          {/* Step table */}
          <div className="flex-1 overflow-auto px-6 py-4">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-border-base">
                  {[
                    'Type', '#', 'Title', 'Instruction',
                    'Expected Result', 'Case', 'Ref',
                    'Verdict', 'Actual Result', 'Evidence', 'Tester',
                  ].map(h => (
                    <th
                      key={h}
                      className="text-left text-[10px] font-semibold
                                 text-text-muted uppercase tracking-wide
                                 py-2 pr-3 whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {steps.map(step => {
                  const key = `${step.step_number}_${step.step_type}`
                  return (
                    <StepRow
                      key={key}
                      step={step}
                      result={stepResults[key] ?? {}}
                      locked={locked}
                      onVerdictChange={handleVerdictChange}
                      onActualChange={handleActualChange}
                      onEvidenceChange={(ev) =>
                        handleEvidenceChange(key, ev)}
                      onTesterChange={handleTesterChange}
                    />
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Sign-off panel — shown when all steps are done */}
          {allDone && run && (
            <SignOffPanel
              run={run}
              locked={locked}
              onSign={handleSignOff}
              apiLoading={apiLoading}
            />
          )}

          {/* Pending hint */}
          {!allDone && (
            <div className="px-6 pb-4 shrink-0">
              <p className="text-[10px] text-text-muted">
                Execute all {steps.length} steps to unlock sign-off.
              </p>
            </div>
          )}
        </>
      )}

      {/* ── Script Review tab ─────────────────────────────── */}
      {activeTab === 'review' && (
        <div className="flex-1 overflow-auto px-6 py-4">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border-base">
                {[
                  'Type', '#', 'Title', 'Instruction',
                  'Expected Result', 'Case', 'Ref',
                ].map(h => (
                  <th
                    key={h}
                    className="text-left text-[10px] font-semibold
                               text-text-muted uppercase tracking-wide
                               py-2 pr-4 whitespace-nowrap"
                  >
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
                  <tr
                    key={`${step.step_number}_${step.step_type}`}
                    className="border-b border-border-base hover:bg-bg-hover/30
                               transition-colors"
                  >
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
                    <td className="py-2.5 pr-4 text-text-muted text-[11px]
                                   max-w-[200px]">
                      {step.expected_result || (
                        <span className="opacity-40 italic">Setup step</span>
                      )}
                    </td>
                    <td className="py-2.5 pr-4">
                      {caseColor
                        ? (
                          <span
                            className="text-[9px] px-1.5 py-0.5 rounded font-semibold"
                            style={{
                              background: caseColor.bg,
                              color: caseColor.text,
                            }}
                          >
                            {step.test_case_type}
                          </span>
                        )
                        : <span className="text-text-muted opacity-40">—</span>
                      }
                    </td>
                    <td className="py-2.5 font-mono text-[10px]
                                   text-text-muted">
                      {step.requirement_reference || '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          {/* Script metadata footer */}
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
    </div>
  )
}
