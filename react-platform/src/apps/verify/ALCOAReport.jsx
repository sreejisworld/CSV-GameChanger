/**
 * ALCOAReport — end-of-run ALCOA+ data integrity audit report.
 *
 * Runs six ALCOA+ principle checks over the completed test run,
 * produces a per-step flag table, QA reviewer badge, and defect summary.
 * The QA reviewer can export the report to CSV.
 */

// ── ALCOA+ principle definitions ─────────────────────────────────
const PRINCIPLES = {
  Attributable:    'Every recorded result is traceable to a named tester.',
  Legible:         'Actual results are readable and meaningful (≥ 5 chars on Fail).',
  Contemporaneous: 'Results were recorded at the time of execution (executedAt populated).',
  Original:        'Run is cryptographically locked with a chain-of-custody hash.',
  Accurate:        'Failed steps have documented actual results — no blank fails.',
  Complete:        'All execution steps have a verdict — no steps left unrecorded.',
}

const P_COLORS = {
  PASS: { bg: 'rgba(50,205,50,0.1)',  border: 'rgba(50,205,50,0.3)',  text: '#32CD32' },
  FAIL: { bg: 'rgba(239,68,68,0.1)',  border: 'rgba(239,68,68,0.3)',  text: '#ef4444' },
  WARN: { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.3)', text: '#f59e0b' },
}

const SEV_COLORS = {
  Critical:    { bg: 'rgba(239,68,68,0.15)',  text: '#ef4444' },
  Major:       { bg: 'rgba(245,158,11,0.15)', text: '#f59e0b' },
  Minor:       { bg: 'rgba(0,127,255,0.15)',  text: '#007FFF' },
  Observation: { bg: 'rgba(100,116,139,0.15)',text: '#64748b' },
}

function downloadCSV(filename, headers, rows) {
  const escape = v => `"${String(v ?? '').replace(/"/g, '""')}"`
  const lines = [
    headers.join(','),
    ...rows.map(r => headers.map(h => escape(r[h])).join(',')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url ; a.download = filename ; a.click()
  URL.revokeObjectURL(url)
}

export default function ALCOAReport({ script, run, steps, stepResults, defects }) {
  if (!run) return null

  const execSteps = steps.filter(s => s.step_type !== 'Setup')

  // ── Run ALCOA+ checks ─────────────────────────────────────────
  const flagged = []

  steps.forEach(step => {
    const key    = `${step.step_number}_${step.step_type}`
    const result = stepResults[key] ?? {}
    const isExec = step.step_type !== 'Setup'
    const issues = []

    // Attributable — verdict set but no tester name
    if (result.verdict && !result.testerName?.trim()) {
      issues.push({ principle: 'Attributable', detail: 'No tester name recorded.' })
    }

    // Legible — Fail with short actual result
    if (result.verdict === 'fail' && (result.actualResult ?? '').trim().length < 5) {
      issues.push({
        principle: 'Legible',
        detail: `Actual result is "${(result.actualResult ?? '').trim() || '(empty)'}".`,
      })
    }

    // Contemporaneous — verdict but no timestamp
    if (result.verdict && !result.executedAt) {
      issues.push({ principle: 'Contemporaneous', detail: 'No execution timestamp.' })
    }

    // Accurate — Fail with no actual result
    if (result.verdict === 'fail' && !result.actualResult?.trim()) {
      issues.push({ principle: 'Accurate', detail: 'Fail recorded with no actual result.' })
    }

    // Complete — execution step with no verdict
    if (isExec && !result.verdict) {
      issues.push({ principle: 'Complete', detail: 'Execution step has no verdict.' })
    }

    if (issues.length > 0) {
      flagged.push({ step, result, issues })
    }
  })

  // Original — locked run must have reasoning hash
  const originalCheck = run.reasoningHash
    ? { status: 'PASS', detail: `Hash: ${run.reasoningHash.slice(0, 16)}…` }
    : { status: 'WARN', detail: 'No chain-of-custody hash (run not API-locked).' }

  // ── Per-principle summary ─────────────────────────────────────
  const principleResults = {}
  ;['Attributable', 'Legible', 'Contemporaneous', 'Accurate', 'Complete'].forEach(p => {
    const hits = flagged.flatMap(f => f.issues).filter(i => i.principle === p).length
    principleResults[p] = hits === 0 ? 'PASS' : 'FAIL'
  })
  principleResults['Original'] = originalCheck.status

  const totalFlags = flagged.reduce((n, f) => n + f.issues.length, 0)

  // ── QA reviewer badge ─────────────────────────────────────────
  const badge =
    totalFlags === 0
      ? { label: 'Clean — Spot Check',      color: '#32CD32', bg: 'rgba(50,205,50,0.1)' }
      : totalFlags <= 3
        ? { label: 'Review Flagged Steps',    color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' }
        : { label: 'Full Manual Review Required', color: '#ef4444', bg: 'rgba(239,68,68,0.1)' }

  // ── Export handler ─────────────────────────────────────────────
  const handleExport = () => {
    const headers = [
      'step_type', 'step_number', 'step_title', 'verdict',
      'actual_result', 'tester_name', 'executed_at',
      'alcoa_issues',
    ]
    const rows = steps.map(step => {
      const key    = `${step.step_number}_${step.step_type}`
      const result = stepResults[key] ?? {}
      const entry  = flagged.find(f => f.step === step)
      return {
        step_type:     step.step_type,
        step_number:   step.step_number,
        step_title:    step.step_title,
        verdict:       result.verdict ?? '',
        actual_result: result.actualResult ?? '',
        tester_name:   result.testerName ?? '',
        executed_at:   result.executedAt ?? '',
        alcoa_issues:  entry
          ? entry.issues.map(i => `${i.principle}: ${i.detail}`).join(' | ')
          : '',
      }
    })
    downloadCSV(`${script.script_id}-alcoa-report.csv`, headers, rows)
  }

  return (
    <div className="flex-1 overflow-auto px-6 py-4 space-y-6">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white mb-0.5">
            ALCOA+ Compliance Report
          </h2>
          <p className="text-[10px] text-text-muted">
            {script.script_id} · Run: {run.runId}
            {run.lockedAt && (
              <> · Locked {new Date(run.lockedAt).toLocaleString()}</>
            )}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* QA badge */}
          <div
            className="px-4 py-2 rounded-lg border text-center"
            style={{ background: badge.bg, borderColor: badge.color + '40' }}
          >
            <p className="text-[10px] text-text-muted mb-0.5">QA Recommendation</p>
            <p className="text-xs font-bold" style={{ color: badge.color }}>
              {badge.label}
            </p>
            <p className="text-[9px] text-text-muted mt-0.5">
              {totalFlags} flag{totalFlags !== 1 ? 's' : ''} detected
            </p>
          </div>

          <button
            onClick={handleExport}
            className="px-3 py-1.5 rounded text-xs border border-border-base
                       text-text-muted hover:text-text-secondary
                       hover:border-border-bright transition-colors"
          >
            📥 Export CSV
          </button>
        </div>
      </div>

      {/* ALCOA+ principle grid */}
      <div>
        <h3 className="text-[10px] font-semibold text-text-muted uppercase
                       tracking-widest mb-3">
          ALCOA+ Principle Checks
        </h3>
        <div className="grid grid-cols-3 gap-2">
          {Object.entries(PRINCIPLES).map(([name, desc]) => {
            const status = principleResults[name]
            const cfg    = P_COLORS[status] ?? P_COLORS.WARN
            const isOriginal = name === 'Original'
            return (
              <div key={name}
                className="p-3 rounded-lg border"
                style={{ background: cfg.bg, borderColor: cfg.border }}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold" style={{ color: cfg.text }}>
                    {name}
                  </span>
                  <span
                    className="text-[9px] font-bold px-1.5 py-0.5 rounded"
                    style={{ background: cfg.border, color: cfg.text }}
                  >
                    {status}
                  </span>
                </div>
                <p className="text-[10px] text-text-muted leading-snug">{desc}</p>
                {isOriginal && status !== 'PASS' && (
                  <p className="text-[9px] text-amber-400 mt-1">
                    {originalCheck.detail}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Flagged steps table */}
      {flagged.length > 0 && (
        <div>
          <h3 className="text-[10px] font-semibold text-text-muted uppercase
                         tracking-widest mb-3">
            Flagged Steps ({flagged.length})
          </h3>
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border-base">
                {['Type', '#', 'Title', 'Verdict', 'Issue', 'Principle'].map(h => (
                  <th key={h}
                    className="text-left text-[10px] font-semibold text-text-muted
                               uppercase tracking-wide py-2 pr-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {flagged.flatMap(({ step, result, issues }) =>
                issues.map((issue, i) => (
                  <tr key={`${step.step_number}_${step.step_type}_${i}`}
                    className="border-b border-border-base bg-red-500/3">
                    <td className="py-2 pr-3">
                      <span className={`
                        text-[9px] px-1.5 py-0.5 rounded font-semibold uppercase
                        ${step.step_type === 'Setup'
                          ? 'bg-bg-card text-text-muted border border-border-base'
                          : 'bg-blue-dim text-blue-DEFAULT border border-blue-DEFAULT/30'}
                      `}>
                        {step.step_type}
                      </span>
                    </td>
                    <td className="py-2 pr-3 font-mono text-text-muted text-[10px]">
                      {step.step_number}
                    </td>
                    <td className="py-2 pr-3 text-text-secondary text-[11px]
                                   max-w-[160px]">
                      <span className="line-clamp-2">{step.step_title}</span>
                    </td>
                    <td className="py-2 pr-3">
                      {result.verdict
                        ? (
                          <span className={`
                            text-[9px] px-1.5 py-0.5 rounded font-semibold uppercase
                            ${result.verdict === 'pass'  ? 'text-lime-DEFAULT'
                            : result.verdict === 'fail'  ? 'text-red-400'
                            : result.verdict === 'blocked' ? 'text-amber-400'
                            : 'text-text-muted'}
                          `}>
                            {result.verdict}
                          </span>
                        )
                        : <span className="text-text-muted opacity-40">—</span>
                      }
                    </td>
                    <td className="py-2 pr-3 text-[10px] text-red-400 max-w-[200px]">
                      {issue.detail}
                    </td>
                    <td className="py-2 text-[10px] font-medium text-text-secondary">
                      {issue.principle}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {flagged.length === 0 && (
        <div className="p-4 rounded-lg border border-lime-DEFAULT/30
                        bg-lime-DEFAULT/5 text-center">
          <p className="text-lime-DEFAULT font-semibold text-sm">
            ✓ All ALCOA+ Checks Passed
          </p>
          <p className="text-text-muted text-xs mt-1">
            No data integrity flags detected. Spot check recommended.
          </p>
        </div>
      )}

      {/* Defect summary */}
      {defects.length > 0 && (
        <div>
          <h3 className="text-[10px] font-semibold text-text-muted uppercase
                         tracking-widest mb-3">
            Defects Logged ({defects.length})
          </h3>
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border-base">
                {['ID', 'Severity', 'Description', 'Assignee', 'Fix By',
                  'FR Ref', 'Step'].map(h => (
                  <th key={h}
                    className="text-left text-[10px] font-semibold text-text-muted
                               uppercase tracking-wide py-2 pr-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {defects.map(d => {
                const sc = SEV_COLORS[d.severity] ?? SEV_COLORS.Observation
                return (
                  <tr key={d.id}
                    className="border-b border-border-base hover:bg-bg-hover/20">
                    <td className="py-2 pr-3 font-mono text-[10px] text-text-muted">
                      {d.id}
                    </td>
                    <td className="py-2 pr-3">
                      <span className="text-[9px] px-1.5 py-0.5 rounded font-semibold"
                        style={{ background: sc.bg, color: sc.text }}>
                        {d.severity}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-[11px] text-text-secondary
                                   max-w-[200px]">
                      <span className="line-clamp-2">{d.description}</span>
                    </td>
                    <td className="py-2 pr-3 text-[10px] text-text-muted">
                      {d.assignee || '—'}
                    </td>
                    <td className="py-2 pr-3 text-[10px] text-text-muted">
                      {d.fixDate || '—'}
                    </td>
                    <td className="py-2 pr-3 font-mono text-[10px] text-text-muted">
                      {d.frRef || '—'}
                    </td>
                    <td className="py-2 font-mono text-[10px] text-text-muted">
                      {d.stepKey || '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Run metadata footer */}
      <div className="flex items-center gap-6 text-[10px] text-text-muted
                      pt-2 border-t border-border-base">
        <span>Script: <span className="font-mono text-text-secondary">
          {script.script_id}
        </span></span>
        <span>Risk: <span className="text-text-secondary">
          {script.risk_level}
        </span></span>
        <span>Strategy: <span className="text-text-secondary">
          {script.test_strategy}
        </span></span>
        <span>Signer: <span className="text-text-secondary">
          {run.signerName || 'Unsigned'}
        </span></span>
        {run.lockedAt && (
          <span>Locked: <span className="text-text-secondary">
            {new Date(run.lockedAt).toLocaleString()}
          </span></span>
        )}
      </div>
    </div>
  )
}
