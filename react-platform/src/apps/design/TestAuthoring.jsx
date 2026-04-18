/**
 * TestAuthoring — Sprint 14 phase-page (Design tab #2).
 *
 * 3-pane layout:
 *   ┌────────────┬──────────────────┬──────────────────────┐
 *   │ Req list   │ Generator        │ Bundle preview       │
 *   │ (URs +     │ (mode, type,     │ (steps, citations,   │
 *   │  status)   │  generate / del) │  quality, promote)   │
 *   └────────────┴──────────────────┴──────────────────────┘
 *
 * Reads:    requirements + riskData + testBundles (Zustand)
 * Writes:   testBundles[reqId] via setTestBundle
 *           promoteBundleToScript on user click → testScripts
 * Network:  POST /test-authoring/generate
 */
import { useEffect, useMemo, useState } from 'react'
import { useAppStore } from '../../store/useAppStore.js'
import { API_BASE }    from '../../config.js'

// ── Risk colour map ───────────────────────────────────────────────
const RISK_COLORS = {
  High:   { bg: 'rgba(239,68,68,0.12)',  text: '#ef4444',
            border: 'rgba(239,68,68,0.40)' },
  Medium: { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b',
            border: 'rgba(245,158,11,0.40)' },
  Low:    { bg: 'rgba(50,205,50,0.12)',  text: '#32CD32',
            border: 'rgba(50,205,50,0.40)' },
}

const ARCHETYPE_BADGE = {
  setup:    { label: 'Setup',     bg: '#1e293b', text: '#94a3b8' },
  positive: { label: 'Positive',  bg: '#0f3d2e', text: '#32CD32' },
  negative: { label: 'Negative',  bg: '#3d0f1e', text: '#ef4444' },
  boundary: { label: 'Boundary',  bg: '#3d2e0f', text: '#f59e0b' },
  edge_case:{ label: 'Edge Case', bg: '#3d2e0f', text: '#f59e0b' },
  recovery: { label: 'Recovery',  bg: '#1e2a3d', text: '#60a5fa' },
  security: { label: 'Security',  bg: '#3d1e2a', text: '#f87171' },
  uat:      { label: 'UAT',       bg: '#2a1e3d', text: '#a855f7' },
  charter:  { label: 'Charter',   bg: '#1e3d3a', text: '#34d399' },
}

// Mirror Risk.jsx matrix in JS
function calcRisk(impact, impl) {
  if (!impact || !impl) return null
  if (impact === 'No GxP') return 'Low'
  if (impact === 'GxP Direct') {
    return impl === 'Out of the Box' ? 'Medium' : 'High'
  }
  if (impl === 'Configured') return 'High'
  if (impl === 'Custom')     return 'Medium'
  return 'Low'
}

// ── Subcomponent: requirement-list pane (left) ────────────────────
function ReqListPane({
  reqs, riskData, testBundles, selectedReqId, onSelect,
}) {
  const urs = reqs.filter(r => r.type === 'UR')

  if (urs.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center
                      gap-2 text-center px-4">
        <span className="text-2xl opacity-30">📝</span>
        <p className="text-xs text-text-muted">
          No requirements available.
        </p>
        <p className="text-[10px] text-text-muted">
          Complete the Requirements and Risk phases first.
        </p>
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto">
      <div className="px-3 py-2 sticky top-0 bg-bg-base z-10
                      border-b border-border-base">
        <p className="text-[10px] uppercase tracking-wide
                      text-text-muted font-semibold">
          User Requirements ({urs.length})
        </p>
      </div>
      <ul className="p-2 space-y-1">
        {urs.map(ur => {
          const row    = riskData[ur.id] ?? {}
          const risk   = calcRisk(row.impact, row.implMethod)
          const bundle = testBundles[ur.id]
          const isSelected = ur.id === selectedReqId
          const cfg = risk ? RISK_COLORS[risk] : null

          return (
            <li key={ur.id}>
              <button
                onClick={() => onSelect(ur.id)}
                className={`
                  w-full text-left p-2.5 rounded-lg border
                  transition-all
                  ${isSelected
                    ? 'border-purple-DEFAULT/60 bg-purple-dim'
                    : 'border-border-base bg-bg-card '
                      + 'hover:border-border-bright'}
                `}
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono font-semibold
                                   text-[11px] text-text-secondary">
                    {ur.id}
                  </span>
                  {cfg && (
                    <span
                      className="text-[9px] font-bold px-1.5 py-0.5
                                 rounded-full"
                      style={{ background: cfg.bg, color: cfg.text }}
                    >
                      {risk.toUpperCase()}
                    </span>
                  )}
                  <span className="ml-auto">
                    {bundle ? (
                      <span
                        className="text-[9px] px-1.5 py-0.5 rounded
                                   font-semibold"
                        style={{
                          background: 'rgba(50,205,50,0.12)',
                          color:      '#32CD32',
                        }}
                      >
                        ✓ {bundle.steps?.length ?? 0} steps
                      </span>
                    ) : (
                      <span className="text-[9px] text-text-muted
                                       opacity-60">
                        no bundle
                      </span>
                    )}
                  </span>
                </div>
                <p className="text-[10px] text-text-muted mt-1
                              line-clamp-2 leading-relaxed">
                  {ur.statement}
                </p>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

// ── Subcomponent: generator pane (middle) ─────────────────────────
function GeneratorPane({
  selectedReq, riskRow, frs, bundle, onGenerate, busy, lastError,
}) {
  const [mode, setMode] = useState('hybrid')
  const [testType, setTestType] = useState('Informal')

  if (!selectedReq) {
    return (
      <div className="h-full flex flex-col items-center justify-center
                      gap-2 text-center px-6">
        <span className="text-3xl opacity-30">⚡</span>
        <p className="text-xs text-text-muted">
          Select a requirement to begin authoring.
        </p>
      </div>
    )
  }

  const risk = calcRisk(riskRow.impact, riskRow.implMethod)
  const cfg  = risk ? RISK_COLORS[risk] : null

  // Predict step count for the selected mode/depth
  const predictedSteps = (() => {
    if (!risk) return null
    if (risk === 'Low') return (frs.length || 1) + 1  // 1 setup + N
    const setupSteps = 3
    if (testType === 'Formal UAT') return setupSteps + (frs.length || 1) + 1
    if (testType === 'Formal OQ')  return setupSteps + (frs.length || 1)
    // Informal: depth-driven multiplier
    const m = risk === 'High'
      ? (riskRow.implMethod === 'Custom' ? 5 : 3)
      : 2
    return setupSteps + (frs.length || 1) * m
  })()

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <span className="font-mono font-semibold text-[11px]
                           text-text-secondary">
            {selectedReq.id}
          </span>
          {cfg && (
            <span
              className="text-[9px] font-bold px-2 py-0.5 rounded-full
                         border"
              style={{
                background: cfg.bg, color: cfg.text,
                borderColor: cfg.border,
              }}
            >
              {risk.toUpperCase()} RISK
            </span>
          )}
        </div>
        <p className="text-[11px] text-text-secondary leading-relaxed">
          {selectedReq.statement}
        </p>
      </div>

      {/* Risk context (read-only) */}
      <div className="grid grid-cols-2 gap-2 text-[10px]">
        <div className="px-2 py-1.5 rounded bg-bg-card border
                        border-border-base">
          <p className="text-text-muted uppercase tracking-wide
                        text-[9px]">Impact</p>
          <p className="text-text-secondary mt-0.5 font-medium">
            {riskRow.impact || '—'}
          </p>
        </div>
        <div className="px-2 py-1.5 rounded bg-bg-card border
                        border-border-base">
          <p className="text-text-muted uppercase tracking-wide
                        text-[9px]">Method</p>
          <p className="text-text-secondary mt-0.5 font-medium">
            {riskRow.implMethod || '—'}
          </p>
        </div>
      </div>

      {/* Linked FRs */}
      <div>
        <p className="text-[9px] uppercase tracking-wide text-text-muted
                      font-semibold mb-1.5">
          Linked Functional Requirements ({frs.length})
        </p>
        {frs.length === 0 ? (
          <p className="text-[10px] text-text-muted italic">
            No FRs linked — engine will treat the UR statement as
            a single test target.
          </p>
        ) : (
          <ul className="space-y-1">
            {frs.map(fr => (
              <li key={fr.id}
                  className="flex items-start gap-2 text-[10px]
                             text-text-secondary">
                <span className="font-mono font-semibold text-text-muted
                                 shrink-0">{fr.id}</span>
                <span className="line-clamp-2">{fr.statement}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Mode selector */}
      <div>
        <p className="text-[9px] uppercase tracking-wide text-text-muted
                      font-semibold mb-1.5">
          Generation Mode
        </p>
        <div className="grid grid-cols-2 gap-1.5">
          {[
            ['hybrid',
             'Hybrid', 'Deterministic skeleton + LLM enrichment'],
            ['deterministic',
             'Deterministic', 'Templates only (offline-safe)'],
          ].map(([val, label, hint]) => (
            <button
              key={val}
              onClick={() => setMode(val)}
              className={`
                px-2 py-2 rounded border text-left transition-colors
                ${mode === val
                  ? 'border-purple-DEFAULT/60 bg-purple-dim'
                  : 'border-border-base hover:border-border-bright'}
              `}
            >
              <p className="text-[11px] font-semibold text-text-secondary">
                {label}
              </p>
              <p className="text-[9px] text-text-muted mt-0.5
                            leading-tight">{hint}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Test type */}
      <div>
        <p className="text-[9px] uppercase tracking-wide text-text-muted
                      font-semibold mb-1.5">
          Test Type
        </p>
        <select
          value={testType}
          onChange={e => setTestType(e.target.value)}
          className="evolv-input evolv-select w-full text-[11px]
                     px-2 py-1.5"
        >
          <option value="Informal">Informal (CSA — flexible)</option>
          <option value="Formal OQ">Formal OQ (Operational Qualification)</option>
          <option value="Formal UAT">Formal UAT (User Acceptance)</option>
        </select>
      </div>

      {/* Predicted output */}
      {predictedSteps && !bundle && (
        <div className="px-3 py-2 rounded bg-bg-card border
                        border-border-base text-[10px] text-text-muted">
          <span className="font-semibold text-text-secondary">
            Predicted output:
          </span>{' '}
          ~{predictedSteps} steps
          {risk === 'High' && mode === 'hybrid' && (
            <> · LLM will enrich negative / boundary / recovery / security</>
          )}
        </div>
      )}

      {/* Generate button */}
      <button
        disabled={busy || !risk}
        onClick={() => onGenerate({ mode, testType })}
        className={`
          mt-auto px-4 py-2.5 rounded-lg text-[12px] font-semibold
          transition-all
          ${busy || !risk
            ? 'bg-bg-card text-text-muted cursor-not-allowed opacity-50'
            : 'bg-purple-DEFAULT/80 text-white hover:opacity-90'}
        `}
        style={!busy && risk
          ? { background: 'rgba(168,85,247,0.85)' }
          : {}}
      >
        {busy
          ? '⏳ Generating…'
          : bundle
            ? `↻ Regenerate Bundle (${mode})`
            : `⚡ Generate Test Bundle (${mode})`}
      </button>

      {!risk && (
        <p className="text-[10px] text-amber-DEFAULT">
          ⚠ Complete impact + implementation method on the Risk
          page before generating a bundle.
        </p>
      )}

      {lastError && (
        <p className="text-[10px] text-red-400 leading-relaxed">
          {lastError}
        </p>
      )}
    </div>
  )
}

// ── Subcomponent: bundle preview (right) ──────────────────────────
function PreviewPane({ bundle, onPromote, onRemove, promoted }) {
  if (!bundle) {
    return (
      <div className="h-full flex flex-col items-center justify-center
                      gap-2 text-center px-6">
        <span className="text-3xl opacity-30">📋</span>
        <p className="text-xs text-text-muted">
          No bundle yet. Generate one to see the preview.
        </p>
      </div>
    )
  }

  const risk    = bundle.risk_level
  const cfg     = RISK_COLORS[risk] ?? null
  const setup   = (bundle.steps ?? []).filter(s => s.step_type === 'Setup')
  const exec    = (bundle.steps ?? []).filter(s => s.step_type === 'Execution')
  const quality = bundle.quality_checklist ?? {}
  const qPass   = Object.values(quality).every(v => v === true)

  return (
    <div className="h-full overflow-auto">
      {/* Bundle header */}
      <div className="sticky top-0 z-10 bg-bg-base border-b
                      border-border-base px-4 py-3">
        <div className="flex items-center gap-2 flex-wrap mb-1.5">
          <span className="font-mono text-[11px] font-semibold
                           text-text-secondary">
            {bundle.bundle_id}
          </span>
          {cfg && (
            <span
              className="text-[9px] font-bold px-2 py-0.5 rounded-full
                         border"
              style={{
                background: cfg.bg, color: cfg.text,
                borderColor: cfg.border,
              }}
            >
              {risk.toUpperCase()}
            </span>
          )}
          <span className="text-[9px] uppercase tracking-wide
                           text-text-muted px-1.5 py-0.5 rounded
                           bg-bg-card border border-border-base">
            depth: {bundle.depth}
          </span>
          <span className="text-[9px] uppercase tracking-wide
                           text-text-muted px-1.5 py-0.5 rounded
                           bg-bg-card border border-border-base">
            mode: {bundle.mode}
            {bundle.enrichment_applied && ' + LLM'}
          </span>
          <span className="text-[9px] uppercase tracking-wide
                           text-text-muted px-1.5 py-0.5 rounded
                           bg-bg-card border border-border-base">
            type: {bundle.test_type}
          </span>
          <span className="ml-auto text-[10px]">
            <span className={qPass
              ? 'text-lime-DEFAULT' : 'text-amber-DEFAULT'}>
              {qPass ? '✓' : '⚠'} quality
            </span>
          </span>
        </div>
        <p className="text-[10px] text-text-muted">
          {setup.length} setup · {exec.length} execution ·{' '}
          {(bundle.bundle_citations ?? []).length} bundle citations ·{' '}
          generated {new Date(bundle.generated_at)
            .toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
        </p>

        {/* Action row */}
        <div className="flex items-center gap-2 mt-2">
          <button
            onClick={onPromote}
            disabled={promoted}
            className={`
              text-[10px] px-2.5 py-1 rounded border font-medium
              transition-colors
              ${promoted
                ? 'border-lime-DEFAULT/40 text-lime-DEFAULT '
                  + 'bg-lime-DEFAULT/10 cursor-default'
                : 'border-blue-DEFAULT/40 text-blue-DEFAULT '
                  + 'bg-blue-dim hover:opacity-90'}
            `}
          >
            {promoted ? '✓ Sent to Verify' : '→ Send to Verify'}
          </button>
          <button
            onClick={onRemove}
            className="text-[10px] px-2.5 py-1 rounded border
                       border-border-base text-text-muted
                       hover:text-red-400 hover:border-red-400/40
                       transition-colors"
          >
            Delete bundle
          </button>
        </div>
      </div>

      {/* Bundle citations */}
      {(bundle.bundle_citations ?? []).length > 0 && (
        <div className="px-4 py-3 border-b border-border-base">
          <p className="text-[9px] uppercase tracking-wide text-text-muted
                        font-semibold mb-1.5">
            Bundle-level Regulatory Rationale
          </p>
          <ul className="space-y-1.5">
            {bundle.bundle_citations.map((c, i) => (
              <li key={i} className="text-[10px] text-text-secondary
                                     leading-relaxed">
                <span className="font-semibold text-blue-DEFAULT">
                  {c.regulation} {c.section}:
                </span>{' '}
                {c.rationale}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Steps */}
      <div className="px-2 py-3">
        {(bundle.steps ?? []).map((step, idx) => {
          const arch = ARCHETYPE_BADGE[step.archetype]
            ?? { label: step.archetype, bg: '#1e293b', text: '#94a3b8' }
          return (
            <div
              key={`${step.step_type}-${step.step_number}-${idx}`}
              className="px-3 py-2.5 mb-1.5 rounded border
                         border-border-base bg-bg-card"
            >
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="text-[10px] font-mono text-text-muted">
                  {step.step_type === 'Setup' ? 'S' : 'E'}
                  {step.step_number}
                </span>
                <span
                  className="text-[9px] font-semibold px-1.5 py-0.5
                             rounded uppercase"
                  style={{ background: arch.bg, color: arch.text }}
                >
                  {arch.label}
                </span>
                {step.requirement_reference && (
                  <span className="text-[9px] font-mono px-1.5 py-0.5
                                   rounded bg-blue-dim text-blue-DEFAULT">
                    {step.requirement_reference}
                  </span>
                )}
                <span className="ml-auto text-[11px] font-semibold
                                 text-text-primary">
                  {step.step_title}
                </span>
              </div>
              <p className="text-[10px] text-text-secondary
                            leading-relaxed mt-1">
                <span className="text-text-muted font-semibold">
                  Instruction:
                </span>{' '}
                {step.step_instruction}
              </p>
              {step.expected_result && (
                <p className="text-[10px] text-text-secondary
                              leading-relaxed mt-1">
                  <span className="text-text-muted font-semibold">
                    Expected:
                  </span>{' '}
                  {step.expected_result}
                </p>
              )}
              {(step.citations ?? []).length > 0 && (
                <details className="mt-1.5">
                  <summary className="text-[9px] text-blue-DEFAULT
                                      cursor-pointer hover:opacity-80">
                    {step.citations.length} regulatory citation
                    {step.citations.length !== 1 ? 's' : ''}
                  </summary>
                  <ul className="mt-1 ml-3 space-y-0.5">
                    {step.citations.map((c, i) => (
                      <li key={i} className="text-[9px]
                                             text-text-muted
                                             leading-snug">
                        <span className="font-semibold text-blue-DEFAULT">
                          {c.regulation} {c.section}
                        </span>
                        {' — '}{c.rationale}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          )
        })}
      </div>

      {/* Quality checklist */}
      <div className="px-4 py-3 border-t border-border-base">
        <p className="text-[9px] uppercase tracking-wide text-text-muted
                      font-semibold mb-2">
          Quality Self-Check
        </p>
        <ul className="space-y-1">
          {Object.entries(quality).map(([key, ok]) => (
            <li key={key} className="flex items-center gap-2 text-[10px]">
              <span style={{ color: ok ? '#32CD32' : '#ef4444' }}>
                {ok ? '✓' : '✗'}
              </span>
              <span className="text-text-secondary">
                {key.replace(/_/g, ' ')}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

// ── Main TestAuthoring tab ────────────────────────────────────────
export default function TestAuthoring({ planData }) {
  const {
    requirements, riskData,
    testBundles, testScripts,
    setTestBundle, removeTestBundle, promoteBundleToScript,
    setPhaseComplete,
  } = useAppStore()

  const [selectedReqId, setSelectedReqId] = useState(null)
  const [busyReqId,     setBusyReqId]     = useState(null)
  const [lastError,     setLastError]     = useState('')

  // Auto-select first UR with risk data on mount
  useEffect(() => {
    if (selectedReqId) return
    const firstUr = requirements.find(r => {
      if (r.type !== 'UR') return false
      const row = riskData[r.id] ?? {}
      return row.impact && row.implMethod
    })
    if (firstUr) setSelectedReqId(firstUr.id)
  }, [requirements, riskData, selectedReqId])

  const selectedReq = useMemo(
    () => requirements.find(r => r.id === selectedReqId) ?? null,
    [requirements, selectedReqId],
  )
  const riskRow = riskData[selectedReqId] ?? {}
  const frs = useMemo(
    () => requirements.filter(
      r => r.type === 'FR' && r.parentId === selectedReqId,
    ),
    [requirements, selectedReqId],
  )
  const bundle = selectedReqId ? testBundles[selectedReqId] : null
  const promoted = bundle
    ? Boolean(testScripts[bundle.bundle_id])
    : false

  const handleGenerate = async ({ mode, testType }) => {
    if (!selectedReq) return
    setBusyReqId(selectedReqId)
    setLastError('')
    try {
      const body = {
        project_name:           planData?.projectName
                                  || 'Untitled Project',
        requirement_id:         selectedReq.id,
        statement:              selectedReq.statement,
        functional_requirements: frs.map(fr => ({
          fr_id:     fr.id,
          statement: fr.statement,
        })),
        risk_assessment: {
          impact:     riskRow.impact     || 'GxP Indirect',
          implMethod: riskRow.implMethod || 'Configured',
        },
        mode,
        test_type: testType,
        persist:   true,
      }
      const res = await fetch(
        `${API_BASE}/test-authoring/generate`,
        {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify(body),
        },
      )
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? `HTTP ${res.status}`)
      }
      const newBundle = await res.json()
      setTestBundle(selectedReq.id, newBundle)
      setPhaseComplete('design')
    } catch (err) {
      setLastError(
        `${err.message} — tried ${API_BASE}/test-authoring/generate. `
        + `Ensure FastAPI is running and reachable at that URL.`,
      )
    } finally {
      setBusyReqId(null)
    }
  }

  const handlePromote = () => {
    if (!selectedReq || !bundle) return
    promoteBundleToScript(selectedReq.id)
  }

  const handleRemove = () => {
    if (!selectedReq) return
    removeTestBundle(selectedReq.id)
  }

  return (
    <div className="grid grid-cols-[260px_320px_1fr]
                    h-[calc(100vh-200px)] gap-0
                    border border-border-base rounded-lg overflow-hidden
                    bg-bg-base">
      {/* Left: requirement list */}
      <div className="border-r border-border-base">
        <ReqListPane
          reqs={requirements}
          riskData={riskData}
          testBundles={testBundles}
          selectedReqId={selectedReqId}
          onSelect={setSelectedReqId}
        />
      </div>

      {/* Middle: generator */}
      <div className="border-r border-border-base">
        <GeneratorPane
          selectedReq={selectedReq}
          riskRow={riskRow}
          frs={frs}
          bundle={bundle}
          onGenerate={handleGenerate}
          busy={busyReqId === selectedReqId}
          lastError={lastError}
        />
      </div>

      {/* Right: preview */}
      <PreviewPane
        bundle={bundle}
        onPromote={handlePromote}
        onRemove={handleRemove}
        promoted={promoted}
      />
    </div>
  )
}
