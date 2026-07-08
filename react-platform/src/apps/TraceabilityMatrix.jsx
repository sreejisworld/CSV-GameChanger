/**
 * TraceabilityMatrix — Sprint 28 Living Traceability Matrix.
 *
 * Single live view that an FDA / EMA inspector can look at and walk
 * any requirement from cradle to grave:
 *
 *   URS / UR  →  Risk  →  UR / FR children  →  Test Bundle  →
 *   Test Runs  →  Pass / Fail  →  Defects  →  Release Approval
 *
 * Pure read-model over the existing Zustand store — no new
 * persistence. The pure helper `computeTraceability()` is exported
 * so other phases (Release readiness, inspector dashboards) can
 * reuse the exact same chain logic.
 *
 * Filters:
 *   • All
 *   • GxP Direct only
 *   • Has gaps only           (no bundle OR bundle authored, no run)
 *   • Failed tests only
 *
 * Drill-down: clicking a row opens a side drawer with the full
 * chain (FRs, every test step result, every defect, every approval).
 *
 * Export: signed PDF via POST /traceability/export-pdf using the
 * same downloadPDF helper as the VP / DS / VSR / Audit pack.
 */
import { useCallback, useMemo, useState } from 'react'
import { useAppStore }       from '../store/useAppStore.js'
import { API_BASE }          from '../config.js'
import { downloadPDF, slugify } from '../utils/downloadPDF.js'

// ─── Pure helpers ────────────────────────────────────────────────

// Mirrors Risk.jsx + CoverageMonitor — kept inline to avoid
// cross-imports between Intelligence and Design phase code.
function _calcRisk(impact, impl) {
  if (!impact || !impl)        return null
  if (impact === 'No GxP')     return 'Low'
  if (impact === 'GxP Direct') {
    return impl === 'Out of the Box' ? 'Medium' : 'High'
  }
  if (impl === 'Configured')   return 'High'
  if (impl === 'Custom')       return 'Medium'
  return 'Low'
}

// Aggregate per-step verdicts on the latest run for a script.
function _summariseRun(run, script) {
  if (!run || !script) {
    return { totalSteps: 0, passed: 0, failed: 0, blocked: 0 }
  }
  const total = (script.steps ?? []).filter(
    s => s.step_type === 'Execution',
  ).length
  let passed = 0, failed = 0, blocked = 0
  for (const sr of Object.values(run.stepResults ?? {})) {
    if (sr.verdict === 'Pass')    passed  += 1
    if (sr.verdict === 'Fail')    failed  += 1
    if (sr.verdict === 'Blocked') blocked += 1
  }
  return { totalSteps: total, passed, failed, blocked }
}

/**
 * Build the trace-rows array from raw store state.
 *
 * One row per UR (FRs are surfaced via `childCount` and the
 * drill-down drawer). The shape is JSON-serialisable so the
 * same array can be POSTed to /traceability/export-pdf.
 *
 * @returns {Array<{
 *   ursId, ursType, statement, parentId,
 *   impact, implMethod, riskLevel, isGxpDirect,
 *   childCount, children,
 *   bundle, scriptId,
 *   runs, latestRunId,
 *   passedCount, failedCount, blockedCount, totalSteps,
 *   defectCount, openDefects, defects,
 *   released, approvalCount, approvals,
 *   status, hasGap,
 * }>}
 */
export function computeTraceability(
  requirements, riskData, testBundles,
  testScripts, testRuns, defects, releaseData,
) {
  const reqs   = Array.isArray(requirements) ? requirements : []
  const urs    = reqs.filter(r => r.type === 'UR')
  const frs    = reqs.filter(r => r.type === 'FR')
  const frsByParent = new Map()
  for (const fr of frs) {
    const arr = frsByParent.get(fr.parentId) ?? []
    arr.push({ id: fr.id, statement: fr.statement ?? '' })
    frsByParent.set(fr.parentId, arr)
  }

  const released       = Boolean(releaseData?.released)
  const approvals      = releaseData?.approvals ?? []
  const approvalCount  = approvals.length

  return urs.map(ur => {
    // ── Risk ──
    const row         = riskData?.[ur.id] ?? {}
    const impact      = row.impact      ?? null
    const implMethod  = row.implMethod  ?? null
    const riskLevel   = _calcRisk(impact, implMethod)
    const isGxpDirect = impact === 'GxP Direct'

    // ── FRs ──
    const children    = frsByParent.get(ur.id) ?? []

    // ── Test bundle ──
    const bundleObj   = testBundles?.[ur.id] ?? null
    const bundle      = bundleObj
      ? {
          id:        bundleObj.bundle_id,
          stepCount: (bundleObj.steps ?? []).length,
          depth:     bundleObj.depth,
          testType:  bundleObj.test_type,
          mode:      bundleObj.mode,
        }
      : null

    // ── Test runs (filter by scriptId) ──
    const scriptId = bundleObj?.bundle_id ?? null
    const script   = scriptId ? testScripts?.[scriptId] : null
    const runsAll  = Object.values(testRuns ?? {})
      .filter(r => r.scriptId === scriptId)
      .sort((a, b) => (b.startedAt ?? '').localeCompare(
        a.startedAt ?? '',
      ))
    const latestRun  = runsAll[0] ?? null
    const summary    = _summariseRun(latestRun, script)

    // Lightweight serialisable run summaries
    const runs = runsAll.map(r => {
      const s = _summariseRun(r, script)
      return {
        runId:     r.runId,
        status:    r.status,
        startedAt: r.startedAt,
        lockedAt:  r.lockedAt,
        signerName: r.signerName ?? '',
        passed:    s.passed,
        failed:    s.failed,
        blocked:   s.blocked,
        totalSteps: s.totalSteps,
      }
    })

    // ── Defects (across all runs for this script) ──
    const allDefects = runsAll.flatMap(
      r => (defects?.[r.runId] ?? []).map(d => ({
        ...d,
        runId: r.runId,
      })),
    )
    const openDefects = allDefects.filter(
      d => (d.status ?? 'Open') !== 'Closed',
    ).length

    // ── Status (single canonical state for filtering) ──
    let status = 'no-bundle'
    if (released)                                status = 'released'
    else if (summary.failed > 0)                 status = 'failed'
    else if (latestRun && latestRun.status === 'locked'
             && summary.failed === 0
             && summary.passed > 0)              status = 'passed'
    else if (latestRun)                          status = 'in-progress'
    else if (bundle)                             status = 'authored'

    const hasGap = status === 'no-bundle' || status === 'authored'

    return {
      ursId:        ur.id,
      ursType:      ur.type,
      statement:    ur.statement ?? '',
      parentId:     ur.parentId ?? null,

      impact, implMethod, riskLevel, isGxpDirect,

      childCount:   children.length,
      children,

      bundle, scriptId,

      runs,
      latestRunId:  latestRun?.runId ?? null,

      passedCount:  summary.passed,
      failedCount:  summary.failed,
      blockedCount: summary.blocked,
      totalSteps:   summary.totalSteps,

      defectCount:  allDefects.length,
      openDefects,
      defects:      allDefects,

      released, approvalCount, approvals,

      status, hasGap,
    }
  })
}

// ─── Tiny presentational helpers ────────────────────────────────

const STATUS_TONE = {
  'released':    { bg: 'rgba(50,205,50,0.15)',  fg: '#32CD32',
                   label: 'Released' },
  'passed':      { bg: 'rgba(50,205,50,0.15)',  fg: '#32CD32',
                   label: 'Passed' },
  'in-progress': { bg: 'rgba(0,127,255,0.15)',  fg: '#007FFF',
                   label: 'In Progress' },
  'authored':    { bg: 'rgba(245,158,11,0.15)', fg: '#f59e0b',
                   label: 'Authored' },
  'failed':      { bg: 'rgba(239,68,68,0.18)',  fg: '#ef4444',
                   label: 'Failed' },
  'no-bundle':   { bg: 'rgba(100,116,139,0.18)', fg: '#94a3b8',
                   label: 'No Bundle' },
}

const RISK_TONE = {
  High:   { bg: 'rgba(239,68,68,0.16)',  fg: '#ef4444' },
  Medium: { bg: 'rgba(245,158,11,0.16)', fg: '#f59e0b' },
  Low:    { bg: 'rgba(50,205,50,0.16)',  fg: '#32CD32' },
}

function StatusPill({ status }) {
  const tone = STATUS_TONE[status] ?? STATUS_TONE['no-bundle']
  return (
    <span
      className="inline-flex items-center text-[10px] font-semibold
                 px-2 py-0.5 rounded"
      style={{ background: tone.bg, color: tone.fg }}
    >
      {tone.label}
    </span>
  )
}

// Sprint 37 — Validated State Confidence pill. Color-coded by tier;
// numeric score for at-a-glance scanning. Click expands the drawer.
const STATE_TONE = {
  green:  { bg: 'rgba(50,205,50,0.15)',  fg: '#32CD32' },
  yellow: { bg: 'rgba(245,158,11,0.15)', fg: '#f59e0b' },
  red:    { bg: 'rgba(239,68,68,0.18)',  fg: '#ef4444' },
}

function StatePill({ assessment }) {
  if (!assessment) {
    return (
      <span className="text-[10px] text-text-muted/60">—</span>
    )
  }
  const tone = STATE_TONE[assessment.tier] ?? STATE_TONE.green
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[10px]
                 font-semibold px-2 py-0.5 rounded-full"
      style={{ background: tone.bg, color: tone.fg }}
      title={assessment.suggested_action || 'Validated State score'}
    >
      <span
        className="w-1.5 h-1.5 rounded-full shrink-0"
        style={{ background: tone.fg }}
      />
      {assessment.score}
    </span>
  )
}

function RiskPill({ riskLevel, isGxpDirect }) {
  if (!riskLevel) {
    return (
      <span className="text-[10px] text-text-muted">—</span>
    )
  }
  const tone = RISK_TONE[riskLevel] ?? RISK_TONE.Low
  return (
    <span
      className="inline-flex items-center gap-1 text-[10px]
                 font-semibold px-2 py-0.5 rounded"
      style={{ background: tone.bg, color: tone.fg }}
    >
      {riskLevel}
      {isGxpDirect && (
        <span title="GxP Direct">★</span>
      )}
    </span>
  )
}

function FilterChip({ label, count, active, onClick, tone }) {
  const palette = {
    blue:  { bg: 'rgba(0,127,255,0.15)',  fg: '#007FFF' },
    amber: { bg: 'rgba(245,158,11,0.15)', fg: '#f59e0b' },
    red:   { bg: 'rgba(239,68,68,0.18)',  fg: '#ef4444' },
    slate: { bg: 'rgba(100,116,139,0.18)', fg: '#94a3b8' },
  }[tone ?? 'slate']
  return (
    <button
      onClick={onClick}
      className={`text-[11px] px-3 py-1.5 rounded-full
                  border transition-all flex items-center gap-1.5
                  ${active
                    ? 'border-transparent font-semibold'
                    : 'border-border-base text-text-muted '
                      + 'hover:border-border-bright'}`}
      style={active
        ? { background: palette.bg, color: palette.fg }
        : undefined}
    >
      {label}
      {Number.isFinite(count) && (
        <span className="text-[10px] opacity-80">({count})</span>
      )}
    </button>
  )
}

// ─── Drill-down drawer ──────────────────────────────────────────

function TraceDrawer({ row, assessment, onClose, onJumpTo }) {
  if (!row) return null
  return (
    <div
      className="absolute inset-0 z-30 flex justify-end"
      onClick={onClose}
    >
      <div
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
      />
      <div
        className="relative w-[640px] max-w-full h-full
                   bg-bg-card border-l border-border-base
                   shadow-[-8px_0_40px_rgba(0,0,0,0.4)]
                   flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-5 py-4 border-b border-border-base
                        flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <code className="text-sm font-mono font-bold
                               text-text-primary">
                {row.ursId}
              </code>
              <StatusPill status={row.status} />
              <RiskPill
                riskLevel={row.riskLevel}
                isGxpDirect={row.isGxpDirect}
              />
            </div>
            <p className="text-[11px] text-text-secondary mt-1
                          line-clamp-3">
              {row.statement || '(no statement)'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary
                       text-lg leading-none"
            title="Close"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4
                        text-[11px]">

          {/* Sprint 37 — Validated State Confidence section. Shows
              the per-UR score, suggested action, and the full
              signal breakdown that drove the score. The audit-
              defensible reasoning trail an inspector reads. */}
          {assessment && (
            <DrawerSection title="Validated State">
              <div
                className="rounded-lg p-3 border space-y-2"
                style={{
                  background:  STATE_TONE[assessment.tier].bg,
                  borderColor: STATE_TONE[assessment.tier].fg + '55',
                }}
              >
                <div className="flex items-baseline gap-2">
                  <span
                    className="text-2xl font-bold"
                    style={{ color: STATE_TONE[assessment.tier].fg }}
                  >
                    {assessment.score}
                  </span>
                  <span
                    className="text-[10px] uppercase tracking-wider
                               font-semibold"
                    style={{ color: STATE_TONE[assessment.tier].fg }}
                  >
                    /100 · {assessment.tier}
                  </span>
                </div>
                <p className="text-[11px] text-text-secondary
                              leading-relaxed">
                  {assessment.suggested_action}
                </p>
              </div>

              {assessment.signals?.length > 0 && (
                <div className="mt-2 space-y-1">
                  <p className="text-[9px] uppercase tracking-wider
                                text-text-muted font-semibold">
                    Signals
                  </p>
                  {assessment.signals.map((s, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 px-2 py-1.5
                                 rounded border border-border-base
                                 bg-bg-base text-[10px]"
                    >
                      <span
                        className="font-mono font-semibold shrink-0
                                   min-w-[36px] text-right"
                        style={{
                          color: s.weight > 0 ? '#ef4444' : '#32CD32',
                        }}
                      >
                        {s.weight > 0 ? '−' : '+'}{Math.abs(Math.round(s.weight))}
                      </span>
                      <div className="min-w-0">
                        <div className="font-semibold text-text-primary">
                          {s.name}
                        </div>
                        <div className="text-text-muted leading-snug">
                          {s.detail}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </DrawerSection>
          )}

          {/* Risk */}
          <DrawerSection title="Risk Profile">
            <DrawerKV label="Impact"            v={row.impact}    />
            <DrawerKV label="Implementation"    v={row.implMethod} />
            <DrawerKV label="Risk Level"        v={row.riskLevel} />
            <DrawerKV label="GxP Direct"
                       v={row.isGxpDirect ? 'Yes' : 'No'} />
          </DrawerSection>

          {/* Functional Requirements */}
          <DrawerSection
            title={`Functional Requirements (${row.childCount})`}
          >
            {row.children.length === 0 ? (
              <p className="text-text-muted italic">
                No FRs decomposed yet.
              </p>
            ) : (
              <ul className="space-y-1.5">
                {row.children.map(c => (
                  <li
                    key={c.id}
                    className="flex gap-2 px-2 py-1.5 rounded
                               border border-border-base
                               bg-bg-base"
                  >
                    <code className="font-mono font-semibold
                                     text-text-primary shrink-0">
                      {c.id}
                    </code>
                    <span className="text-text-secondary">
                      {c.statement || '(empty)'}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </DrawerSection>

          {/* Bundle */}
          <DrawerSection
            title="Test Bundle"
            cta={!row.bundle ? {
              label: '⚡ Author Bundle',
              onClick: () => onJumpTo?.('design'),
            } : null}
          >
            {!row.bundle ? (
              <p className="text-text-muted italic">
                No test bundle authored. GxP Direct URs are
                blocked from completing the Design phase
                without one.
              </p>
            ) : (
              <>
                <DrawerKV label="Bundle ID"  v={row.bundle.id} />
                <DrawerKV label="Steps"
                           v={String(row.bundle.stepCount)} />
                <DrawerKV label="Depth"      v={row.bundle.depth} />
                <DrawerKV label="Test Type"  v={row.bundle.testType} />
                <DrawerKV label="Mode"       v={row.bundle.mode} />
              </>
            )}
          </DrawerSection>

          {/* Runs */}
          <DrawerSection
            title={`Test Runs (${row.runs.length})`}
            cta={row.bundle && row.runs.length === 0 ? {
              label: '▶ Execute',
              onClick: () => onJumpTo?.('verify'),
            } : null}
          >
            {row.runs.length === 0 ? (
              <p className="text-text-muted italic">
                Bundle authored but no test run yet.
              </p>
            ) : (
              <ul className="space-y-1.5">
                {row.runs.map(r => (
                  <li
                    key={r.runId}
                    className="px-2 py-1.5 rounded border
                               border-border-base bg-bg-base"
                  >
                    <div className="flex items-center
                                    justify-between gap-2">
                      <code className="font-mono text-[10px]
                                       text-text-primary truncate">
                        {r.runId}
                      </code>
                      <span className={`text-[10px] font-semibold
                                        ${r.status === 'locked'
                                          ? 'text-blue-DEFAULT'
                                          : 'text-amber-500'}`}>
                        {r.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-3
                                    text-[10px] text-text-muted
                                    mt-0.5">
                      <span>
                        ✅ {r.passed} / ❌ {r.failed}
                        {' / '}
                        ⏸ {r.blocked} of {r.totalSteps}
                      </span>
                      {r.signerName && (
                        <span title="Signed by">
                          Sgn: {r.signerName}
                        </span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </DrawerSection>

          {/* Defects */}
          <DrawerSection
            title={`Defects (${row.defectCount}, `
                   + `${row.openDefects} open)`}
          >
            {row.defectCount === 0 ? (
              <p className="text-text-muted italic">
                No defects raised against this requirement.
              </p>
            ) : (
              <ul className="space-y-1.5">
                {row.defects.map(d => (
                  <li
                    key={d.id}
                    className="px-2 py-1.5 rounded border
                               border-border-base bg-bg-base"
                  >
                    <div className="flex items-center gap-2">
                      <code className="font-mono font-semibold
                                       text-text-primary">
                        {d.id}
                      </code>
                      <span className={`text-[10px] font-semibold
                                        ${
                                          d.severity === 'High'
                                            ? 'text-red-500'
                                            : d.severity === 'Medium'
                                              ? 'text-amber-500'
                                              : 'text-blue-DEFAULT'
                                        }`}>
                        {d.severity ?? 'Medium'}
                      </span>
                      <span className="text-[10px]
                                       text-text-muted ml-auto">
                        {d.status ?? 'Open'}
                      </span>
                    </div>
                    <p className="text-[11px] text-text-secondary
                                  mt-0.5 line-clamp-2">
                      {d.description || '(no description)'}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </DrawerSection>

          {/* Approvals */}
          <DrawerSection
            title={`Release Approvals (${row.approvalCount})`}
          >
            {!row.released ? (
              <p className="text-text-muted italic">
                System not yet released.
              </p>
            ) : (
              <ul className="space-y-1.5">
                {row.approvals.map((a, i) => (
                  <li
                    key={i}
                    className="px-2 py-1.5 rounded border
                               border-border-base bg-bg-base"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-semibold
                                       text-text-primary">
                        {a.signerName ?? a.name ?? 'Approver'}
                      </span>
                      <span className="text-[10px]
                                       text-text-muted ml-auto">
                        {a.signedAt ?? a.timestamp ?? ''}
                      </span>
                    </div>
                    {(a.role || a.meaning) && (
                      <p className="text-[10px] text-text-muted
                                    mt-0.5">
                        {[a.role, a.meaning]
                          .filter(Boolean).join(' · ')}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </DrawerSection>
        </div>
      </div>
    </div>
  )
}

function DrawerSection({ title, children, cta }) {
  return (
    <section>
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <h3 className="text-[10px] uppercase tracking-wider
                       font-semibold text-text-muted">
          {title}
        </h3>
        {cta && (
          <button
            onClick={cta.onClick}
            className="text-[10px] px-2 py-0.5 rounded font-semibold
                       text-white bg-blue-DEFAULT
                       hover:bg-blue-bright transition-colors"
          >
            {cta.label}
          </button>
        )}
      </div>
      <div className="space-y-1">{children}</div>
    </section>
  )
}

function DrawerKV({ label, v }) {
  return (
    <div className="flex gap-2">
      <span className="text-text-muted w-32 shrink-0">{label}</span>
      <span className="text-text-primary truncate">{v ?? '—'}</span>
    </div>
  )
}

// ─── Export modal ───────────────────────────────────────────────

function ExportModal({
  state, count, filterSummary, projectName,
  onChange, onCancel, onSubmit,
}) {
  return (
    <div
      className="absolute inset-0 z-30 flex items-center justify-center
                 bg-black/40 backdrop-blur-sm"
      onClick={onCancel}
    >
      <div
        className="w-[480px] max-w-full bg-bg-card border
                   border-border-base rounded-xl
                   shadow-[0_8px_40px_rgba(0,0,0,0.4)] p-5 space-y-4"
        onClick={e => e.stopPropagation()}
      >
        <div>
          <h3 className="text-base font-semibold text-text-primary">
            Export Traceability Matrix
          </h3>
          <p className="text-[11px] text-text-muted mt-0.5">
            Generates a signed PDF with cover, full chain table,
            and Manifestation of Signature
            (21 CFR Part 11 §11.50).
          </p>
        </div>

        <div className="text-[11px] text-text-secondary
                        bg-bg-base px-3 py-2 rounded
                        border border-border-base space-y-1">
          <div>
            <span className="text-text-muted">Project:</span>{' '}
            <span className="font-semibold">
              {projectName || 'Untitled Project'}
            </span>
          </div>
          <div>
            <span className="text-text-muted">
              Requirements to include:
            </span>{' '}
            <span className="font-semibold">{count}</span>
          </div>
          <div>
            <span className="text-text-muted">Filters:</span>{' '}
            <span className="font-mono text-[10px]">
              {filterSummary}
            </span>
          </div>
        </div>

        <label className="block text-[11px] text-text-secondary">
          Inspector / Signer Name
          <input
            value={state.signer}
            onChange={e => onChange({ signer: e.target.value })}
            placeholder="e.g. Jane Smith, QA Director"
            className="evolv-input mt-1 w-full text-xs px-2 py-1.5"
          />
        </label>

        {state.error && (
          <div className="px-3 py-2 rounded border
                          border-red-500/30 bg-red-500/10
                          text-[11px] text-red-400">
            {state.error}
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-1">
          <button
            onClick={onCancel}
            className="px-3 py-1.5 text-xs rounded
                       border border-border-base text-text-muted
                       hover:text-text-secondary transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onSubmit}
            disabled={state.loading}
            className="px-3 py-1.5 text-xs rounded font-semibold
                       text-white bg-blue-DEFAULT
                       hover:bg-blue-bright
                       disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors"
          >
            {state.loading ? 'Generating…' : '📑 Download PDF'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Main component ─────────────────────────────────────────────

export default function TraceabilityMatrix({ openTab }) {
  const requirements = useAppStore(s => s.requirements)
  const riskData     = useAppStore(s => s.riskData)
  const testBundles  = useAppStore(s => s.testBundles)
  const testScripts  = useAppStore(s => s.testScripts)
  const testRuns     = useAppStore(s => s.testRuns)
  const defects      = useAppStore(s => s.defects)
  const releaseData  = useAppStore(s => s.releaseData)
  const projectName  = useAppStore(s => s.planData.projectName)

  // Sprint 37 — Validated State Engine slice + assessment trigger.
  // The "EVOLV helps you STAY validated" surface lives here on the
  // Living Traceability Matrix as a new column + an "Assess" CTA.
  const changeRecords         = useAppStore(s => s.changeRecords)
  const validatedState        = useAppStore(s => s.validatedState)
  const setValidatedStateLoading = useAppStore(s => s.setValidatedStateLoading)
  const setValidatedStateReport  = useAppStore(s => s.setValidatedStateReport)
  const setValidatedStateError   = useAppStore(s => s.setValidatedStateError)

  // Sprint 38 — Regulatory Drift slice. If a drift scan exists in
  // the store (set by RegulatoryWatch), forward it to the VSE
  // assess call as `drift_report` so the citation_drift signal
  // slot fires (-15 per affected citation, capped at -30).
  // Default-guard: pre-Sprint-38 persisted state has no
  // regulatoryDrift key — keep the page alive on stale localStorage.
  const regulatoryDrift = useAppStore(s => s.regulatoryDrift) ?? {
    report: null, byUrId: {}, loading: false,
    error: null, lastFetched: null,
  }

  const handleAssessVse = useCallback(async () => {
    setValidatedStateLoading(true)
    try {
      const res = await fetch(`${API_BASE}/validated-state/assess`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name:    projectName || 'Untitled Project',
          requirements:    requirements ?? [],
          risk_data:       riskData      ?? {},
          test_bundles:    testBundles   ?? {},
          test_runs:       testRuns      ?? {},
          defects:         defects       ?? {},
          change_records:  changeRecords ?? {},
          // Sprint 38 — drift wire-through. Engine accepts null
          // gracefully (skips the citation_drift signal entirely).
          drift_report:    regulatoryDrift.report ?? null,
          user_id:         'demo',
        }),
        signal: AbortSignal.timeout(20000),
      })
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(errBody.detail ?? `HTTP ${res.status}`)
      }
      const report = await res.json()
      setValidatedStateReport(report)
    } catch (e) {
      setValidatedStateError(
        e.message ?? 'State assessment failed. '
        + 'Ensure FastAPI is running on port 8000.',
      )
    }
  }, [
    projectName, requirements, riskData, testBundles, testRuns,
    defects, changeRecords, regulatoryDrift.report,
    setValidatedStateLoading, setValidatedStateReport,
    setValidatedStateError,
  ])

  // Compute the trace matrix — pure derivation, re-runs on any
  // state change so the table stays live.
  const allRows = useMemo(() => computeTraceability(
    requirements, riskData, testBundles,
    testScripts, testRuns, defects, releaseData,
  ), [
    requirements, riskData, testBundles,
    testScripts, testRuns, defects, releaseData,
  ])

  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [sort,   setSort]   = useState({ key: 'ursId', dir: 'asc' })
  const [drillRow, setDrillRow] = useState(null)
  const [exporter, setExporter] = useState({
    open: false, signer: '', loading: false, error: '',
  })

  // ── Filter ──
  const filtered = useMemo(() => {
    let rows = allRows
    if (filter === 'gxp')      rows = rows.filter(r => r.isGxpDirect)
    if (filter === 'gaps')     rows = rows.filter(r => r.hasGap)
    if (filter === 'failed')   rows = rows.filter(
      r => r.failedCount > 0,
    )
    if (filter === 'released') rows = rows.filter(r => r.released)
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      rows = rows.filter(r =>
        r.ursId.toLowerCase().includes(q)
        || (r.statement ?? '').toLowerCase().includes(q),
      )
    }
    return rows
  }, [allRows, filter, search])

  const sorted = useMemo(() => {
    const dir = sort.dir === 'asc' ? 1 : -1
    return [...filtered].sort((a, b) => {
      const av = a[sort.key], bv = b[sort.key]
      if (av == null && bv == null) return 0
      if (av == null) return  1
      if (bv == null) return -1
      if (typeof av === 'number') return (av - bv) * dir
      return String(av).localeCompare(String(bv)) * dir
    })
  }, [filtered, sort])

  // ── Counts (for chip labels) ──
  const counts = useMemo(() => ({
    all:      allRows.length,
    gxp:      allRows.filter(r => r.isGxpDirect).length,
    gaps:     allRows.filter(r => r.hasGap).length,
    failed:   allRows.filter(r => r.failedCount > 0).length,
    released: allRows.filter(r => r.released).length,
  }), [allRows])

  // ── Filter summary (for PDF cover) ──
  const filterSummary = useMemo(() => {
    const parts = []
    if (filter !== 'all')   parts.push(`Filter: ${filter}`)
    if (search.trim())      parts.push(`Search: "${search.trim()}"`)
    if (parts.length === 0) parts.push('All requirements')
    parts.push(`${sorted.length} of ${allRows.length} rows`)
    return parts.join(' · ')
  }, [filter, search, sorted.length, allRows.length])

  // ── Sort toggle ──
  const onSort = useCallback(key => {
    setSort(prev =>
      prev.key === key
        ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: 'asc' },
    )
  }, [])

  // ── Export ──
  const handleExportPdf = useCallback(async () => {
    if (!exporter.signer.trim()) {
      setExporter(x => ({
        ...x,
        error: 'Please enter a signer name before exporting.',
      }))
      return
    }
    setExporter(x => ({ ...x, loading: true, error: '' }))
    try {
      const proj = projectName || 'Untitled Project'
      await downloadPDF(
        `${API_BASE}/traceability/export-pdf`,
        {
          rows:           sorted,
          project_name:   proj,
          signer_name:    exporter.signer.trim(),
          meaning:
            'Traceability Matrix Inspection Export',
          filter_summary: filterSummary,
        },
        `traceability-matrix-${slugify(proj)}.pdf`,
      )
      setExporter(x => ({ ...x, loading: false, open: false }))
    } catch (err) {
      setExporter(x => ({
        ...x,
        loading: false,
        error: err.message || 'PDF export failed.',
      }))
    }
  }, [exporter.signer, sorted, filterSummary, projectName])

  // ── CSV export (client-side) ──
  const handleExportCsv = useCallback(() => {
    const cols = [
      'URS ID', 'Statement', 'Risk', 'GxP Direct',
      'FR Children', 'Bundle', 'Bundle Steps',
      'Latest Run', 'Passed', 'Failed', 'Total Steps',
      'Defects (open)', 'Released', 'Status',
    ]
    const cell = v => `"${String(v ?? '')
      .replace(/"/g, '""').replace(/\n/g, ' ')}"`
    const lines = [
      cols.map(cell).join(','),
      ...sorted.map(r => [
        r.ursId, r.statement, r.riskLevel ?? '',
        r.isGxpDirect ? 'Yes' : 'No',
        r.childCount,
        r.bundle?.id ?? '',
        r.bundle?.stepCount ?? 0,
        r.latestRunId ?? '',
        r.passedCount, r.failedCount, r.totalSteps,
        `${r.defectCount} (${r.openDefects})`,
        r.released ? 'Yes' : 'No',
        STATUS_TONE[r.status]?.label ?? r.status,
      ].map(cell).join(',')),
    ]
    const blob = new Blob([lines.join('\n')], {
      type: 'text/csv;charset=utf-8',
    })
    const url = URL.createObjectURL(blob)
    const a   = document.createElement('a')
    a.href = url
    a.download = `traceability-matrix-`
      + `${slugify(projectName || 'project')}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }, [sorted, projectName])

  // ── Render ──
  return (
    <div className="relative flex flex-col h-full
                    bg-bg-base text-text-primary">
      {/* Header */}
      <div className="px-6 pt-5 pb-3 border-b border-border-base
                      shrink-0">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-text-primary">
              Requirements Traceability Matrix
            </h1>
            <p className="text-[11px] text-text-muted mt-0.5">
              Live read-model — Requirements → Risk → UR/FR →
              Test Bundle → Runs → Defects → Release.{' '}
              {allRows.length} requirement(s)
              {filtered.length !== allRows.length && (
                <> · {filtered.length} after filters</>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Sprint 37 — Assess Validated State button. Calls
                POST /validated-state/assess and persists the
                per-UR scores to the store; the State Confidence
                column reads them. */}
            <button
              onClick={handleAssessVse}
              disabled={validatedState.loading || allRows.length === 0}
              className="px-3 py-1.5 text-xs rounded font-semibold
                         text-white shadow-sm
                         disabled:opacity-40
                         disabled:cursor-not-allowed
                         transition-opacity hover:opacity-90"
              style={{
                background:
                  'linear-gradient(90deg, #007FFF, #32CD32)',
              }}
              title="Compute the per-UR Validated State Confidence score"
            >
              {validatedState.loading
                ? '🧠 Assessing…'
                : '🧠 Assess Validated State'}
            </button>
            <button
              onClick={handleExportCsv}
              disabled={sorted.length === 0}
              className="px-3 py-1.5 text-xs rounded
                         border border-border-base
                         text-text-muted hover:text-text-secondary
                         hover:border-border-bright
                         disabled:opacity-40
                         transition-colors"
              title="Download current filtered view as CSV"
            >
              ⬇ CSV
            </button>
            <button
              onClick={() => setExporter(x => ({
                ...x, open: true, error: '',
              }))}
              disabled={sorted.length === 0}
              className="px-3 py-1.5 text-xs rounded font-semibold
                         text-white bg-blue-DEFAULT
                         hover:bg-blue-bright
                         disabled:opacity-40
                         disabled:cursor-not-allowed
                         transition-colors"
              title={sorted.length === 0
                ? 'No rows in current filter to export'
                : 'Export the current filtered view as a '
                  + 'signed PDF'}
            >
              📑 Export Signed PDF
            </button>
          </div>
        </div>

        {/* Sprint 37 — Validated State headline banner. Shows the
            aggregate score + headline + tier counts when an
            assessment has been run. The "EVOLV helps you STAY
            validated" surface — what every CSV lead sees first
            on Monday morning. */}
        {validatedState.report && !validatedState.loading && (() => {
          const r    = validatedState.report
          const tone = STATE_TONE[r.aggregate_tier] ?? STATE_TONE.green
          return (
            <div
              className="mt-3 px-4 py-2.5 rounded-lg border
                         flex items-center gap-3 text-[11px]"
              style={{
                background:  tone.bg,
                borderColor: tone.fg + '44',
              }}
            >
              <div
                className="flex items-center gap-2 font-semibold
                           shrink-0"
                style={{ color: tone.fg }}
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ background: tone.fg }}
                />
                Validated State: {r.aggregate_score}/100
              </div>
              <span className="text-text-secondary flex-1
                               leading-relaxed">
                {r.headline}
              </span>
              <span className="text-[10px] text-text-muted shrink-0">
                · {r.tier_counts.green} green
                · {r.tier_counts.yellow} yellow
                · {r.tier_counts.red} red
                · assessed {new Date(r.assessed_at)
                    .toLocaleTimeString([], {
                      hour: '2-digit', minute: '2-digit',
                    })}
              </span>
            </div>
          )
        })()}
        {validatedState.error && (
          <div className="mt-3 px-4 py-2 rounded-lg text-[11px]
                          border border-red-500/30
                          bg-red-500/10 text-red-400">
            {validatedState.error}
          </div>
        )}

        {/* Sprint 38 — Regulatory drift banner. Surfaces the drift
            scan result alongside the Validated State banner so a
            QA lead sees both continuity signals at once. The amber
            tone is intentional: drift never blocks, only flags
            (AI proposes, human signs the revalidation). */}
        {regulatoryDrift.report && !regulatoryDrift.loading && (() => {
          const r       = regulatoryDrift.report
          const hits    = r.affected_ur_count ?? 0
          const isClean = hits === 0
          const tone    = isClean
            ? { fg: '#32CD32', bg: 'rgba(50,205,50,0.08)' }
            : { fg: '#f59e0b', bg: 'rgba(245,158,11,0.08)' }
          return (
            <div
              className="mt-3 px-4 py-2.5 rounded-lg border
                         flex items-center gap-3 text-[11px]"
              style={{
                background:  tone.bg,
                borderColor: tone.fg + '44',
              }}
            >
              <div
                className="flex items-center gap-2 font-semibold
                           shrink-0"
                style={{ color: tone.fg }}
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ background: tone.fg }}
                />
                {isClean
                  ? 'Regulatory Drift: clean'
                  : `Regulatory Drift: ${hits}` +
                    ` of ${r.ur_count} UR(s) affected`}
              </div>
              <span className="text-text-secondary flex-1
                               leading-relaxed">
                {r.headline}
              </span>
              <span className="text-[10px] text-text-muted shrink-0">
                · scanned {new Date(r.scanned_at)
                    .toLocaleTimeString([], {
                      hour: '2-digit', minute: '2-digit',
                    })}
              </span>
            </div>
          )
        })()}
        {regulatoryDrift.error && (
          <div className="mt-3 px-4 py-2 rounded-lg text-[11px]
                          border border-red-500/30
                          bg-red-500/10 text-red-400">
            Drift scan: {regulatoryDrift.error}
          </div>
        )}

        {/* Filter chips */}
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          <FilterChip label="All" tone="slate"
            count={counts.all}
            active={filter === 'all'}
            onClick={() => setFilter('all')} />
          <FilterChip label="GxP Direct" tone="red"
            count={counts.gxp}
            active={filter === 'gxp'}
            onClick={() => setFilter('gxp')} />
          <FilterChip label="Has Gaps" tone="amber"
            count={counts.gaps}
            active={filter === 'gaps'}
            onClick={() => setFilter('gaps')} />
          <FilterChip label="Failed Tests" tone="red"
            count={counts.failed}
            active={filter === 'failed'}
            onClick={() => setFilter('failed')} />
          <FilterChip label="Released" tone="blue"
            count={counts.released}
            active={filter === 'released'}
            onClick={() => setFilter('released')} />

          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search ID or statement…"
            className="ml-auto evolv-input text-xs px-2 py-1
                       w-56 max-w-full"
          />
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {sorted.length === 0 ? (
          <EmptyState filter={filter} totalAll={allRows.length}
                      openTab={openTab} />
        ) : (
          <table className="w-full text-[11px]">
            <thead className="sticky top-0 z-10 bg-bg-base
                              border-b border-border-base">
              <tr className="text-text-muted text-[10px] uppercase
                             tracking-wider">
                <Th k="ursId"        label="URS ID"
                    sort={sort} onSort={onSort} />
                <Th k="statement"    label="Requirement"
                    sort={sort} onSort={onSort} />
                <Th k="riskLevel"    label="Risk"
                    sort={sort} onSort={onSort} />
                <Th k="childCount"   label="UR/FR"
                    sort={sort} onSort={onSort} />
                <th className="text-left px-3 py-2 font-semibold">
                  Bundle
                </th>
                <Th k="passedCount"  label="Pass / Fail"
                    sort={sort} onSort={onSort} />
                <Th k="defectCount"  label="Defects"
                    sort={sort} onSort={onSort} />
                <Th k="released"     label="Released"
                    sort={sort} onSort={onSort} />
                <Th k="status"       label="Status"
                    sort={sort} onSort={onSort} />
                {/* Sprint 37 — State Confidence column. Reads from
                    validatedState.byUrId. Shows the per-UR score
                    pill with tier color; click row to see full
                    drill-down with signals + suggested action. */}
                <th className="text-left px-3 py-2 font-semibold">
                  State
                </th>
                <th className="w-8" />
              </tr>
            </thead>
            <tbody>
              {sorted.map(r => (
                <tr
                  key={r.ursId}
                  className="border-b border-border-base
                             hover:bg-bg-card transition-colors
                             cursor-pointer"
                  onClick={() => setDrillRow(r)}
                >
                  <td className="px-3 py-2 align-top">
                    <code className="font-mono font-semibold
                                     text-text-primary">
                      {r.ursId}
                    </code>
                  </td>
                  <td className="px-3 py-2 align-top
                                 text-text-secondary
                                 max-w-[480px]">
                    <span className="line-clamp-2">
                      {r.statement || '(no statement)'}
                    </span>
                  </td>
                  <td className="px-3 py-2 align-top">
                    <RiskPill
                      riskLevel={r.riskLevel}
                      isGxpDirect={r.isGxpDirect}
                    />
                  </td>
                  <td className="px-3 py-2 align-top
                                 text-text-secondary text-[10px]">
                    {r.childCount > 0
                      ? `UR + ${r.childCount} FR`
                      : 'UR only'}
                  </td>
                  <td className="px-3 py-2 align-top
                                 text-text-secondary text-[10px]">
                    {r.bundle ? (
                      <>
                        <code className="font-mono">
                          {r.bundle.id}
                        </code>
                        <span className="text-text-muted"> · </span>
                        <span>
                          {r.bundle.stepCount} steps
                        </span>
                      </>
                    ) : (
                      <span className="text-text-muted italic">
                        none
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 align-top text-[10px]">
                    {(r.passedCount + r.failedCount) === 0 ? (
                      <span className="text-text-muted">—</span>
                    ) : (
                      <span>
                        <span className="text-green-500
                                         font-semibold">
                          {r.passedCount}P
                        </span>
                        <span className="text-text-muted"> / </span>
                        <span className={r.failedCount > 0
                          ? 'text-red-500 font-semibold'
                          : 'text-text-muted'}>
                          {r.failedCount}F
                        </span>
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 align-top text-[10px]">
                    {r.defectCount === 0 ? (
                      <span className="text-text-muted">—</span>
                    ) : (
                      <span className={r.openDefects > 0
                        ? 'text-amber-500 font-semibold'
                        : 'text-text-muted'}>
                        {r.defectCount}{' '}
                        ({r.openDefects} open)
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 align-top text-[10px]">
                    {r.released
                      ? <span className="text-green-500
                                          font-semibold">
                          ✓ {r.approvalCount}
                        </span>
                      : <span className="text-text-muted">—</span>}
                  </td>
                  <td className="px-3 py-2 align-top">
                    <StatusPill status={r.status} />
                  </td>
                  <td className="px-3 py-2 align-top">
                    <StatePill
                      assessment={validatedState.byUrId[r.ursId]}
                    />
                  </td>
                  <td className="px-3 py-2 align-top
                                 text-text-muted text-center">
                    ›
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Drill-down drawer */}
      {drillRow && (
        <TraceDrawer
          row={drillRow}
          assessment={validatedState.byUrId[drillRow.ursId]}
          onClose={() => setDrillRow(null)}
          onJumpTo={appId => {
            setDrillRow(null)
            openTab?.(appId)
          }}
        />
      )}

      {/* Export modal */}
      {exporter.open && (
        <ExportModal
          state={exporter}
          count={sorted.length}
          filterSummary={filterSummary}
          projectName={projectName}
          onChange={patch => setExporter(x => ({ ...x, ...patch }))}
          onCancel={() => setExporter(x => ({
            ...x, open: false, error: '',
          }))}
          onSubmit={handleExportPdf}
        />
      )}
    </div>
  )
}

function Th({ k, label, sort, onSort }) {
  const active = sort.key === k
  const arrow = !active ? ''
    : sort.dir === 'asc' ? ' ▲' : ' ▼'
  return (
    <th
      className={`text-left px-3 py-2 font-semibold cursor-pointer
                  select-none ${active
                    ? 'text-text-primary'
                    : 'hover:text-text-secondary'}`}
      onClick={() => onSort(k)}
    >
      {label}{arrow}
    </th>
  )
}

function EmptyState({ filter, totalAll, openTab }) {
  if (totalAll === 0) {
    return (
      <div className="flex flex-col items-center justify-center
                      h-full text-text-muted gap-3 px-6 py-12
                      text-center">
        <div className="text-4xl">🧭</div>
        <div className="text-sm font-semibold text-text-primary">
          No requirements yet
        </div>
        <p className="text-[11px] max-w-md">
          Open the Requirements tab to author or import URs and FRs.
          The traceability matrix will populate live as you advance
          through Risk → Design → Verify → Release.
        </p>
        <button
          onClick={() => openTab?.('requirements')}
          className="mt-2 px-3 py-1.5 text-xs rounded font-semibold
                     text-white bg-blue-DEFAULT
                     hover:bg-blue-bright transition-colors"
        >
          → Open Requirements
        </button>
      </div>
    )
  }
  const filterLabels = {
    gxp:      'No GxP Direct requirements match this filter.',
    gaps:     'Every requirement has a test bundle authored — no gaps.',
    failed:   'No requirements have failed test runs.',
    released: 'No requirements are released yet.',
  }
  return (
    <div className="flex flex-col items-center justify-center
                    h-full text-text-muted gap-3 px-6 py-12
                    text-center">
      <div className="text-3xl">🔍</div>
      <p className="text-[11px] max-w-md">
        {filterLabels[filter] ?? 'No rows match the active filter.'}
      </p>
    </div>
  )
}
