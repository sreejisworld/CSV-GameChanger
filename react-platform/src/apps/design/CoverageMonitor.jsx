/**
 * CoverageMonitor — Sprint 15.3 Coverage Gap Detector.
 *
 * Scans `requirements` × `testBundles` and surfaces:
 *   • Banner: "K of N URs have no test bundle" with "Generate now" CTA
 *   • Hard block on Design phase completion when any GxP Direct UR
 *     has zero coverage (computeCoverage().canCompleteDesign === false)
 *   • Same gate fires on Release readiness checklist
 *
 * The pure helper `computeCoverage()` is exported so other phases
 * (Release, Verify) can reuse the same gate logic.
 */

// ── Pure helper ───────────────────────────────────────────────────
// Mirrors Risk.jsx matrix — kept here to avoid a cross-import.
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

/**
 * @returns {{
 *   totalUrs: number,
 *   urs: Array<{ id, hasBundle, isGxpDirect, riskLevel }>,
 *   uncoveredAll: string[],          // UR IDs without a bundle
 *   uncoveredGxpDirect: string[],    // GxP Direct UR IDs uncovered
 *   coveragePct: number,             // 0–100
 *   canCompleteDesign: boolean,      // false if any GxP Direct uncovered
 *   firstUncovered: string | null,   // GxP Direct first, else any
 * }}
 */
export function computeCoverage(requirements, riskData, testBundles) {
  const urs = (requirements ?? []).filter(r => r.type === 'UR')
  const totalUrs = urs.length

  const augmented = urs.map(ur => {
    const row         = riskData?.[ur.id] ?? {}
    const hasBundle   = Boolean(testBundles?.[ur.id])
    const isGxpDirect = row.impact === 'GxP Direct'
    const riskLevel   = _calcRisk(row.impact, row.implMethod)
    return { id: ur.id, hasBundle, isGxpDirect, riskLevel }
  })

  const uncoveredAll = augmented
    .filter(u => !u.hasBundle).map(u => u.id)
  const uncoveredGxpDirect = augmented
    .filter(u => !u.hasBundle && u.isGxpDirect).map(u => u.id)

  const covered = totalUrs - uncoveredAll.length
  const coveragePct = totalUrs === 0 ? 0
    : Math.round((covered / totalUrs) * 100)

  const canCompleteDesign = totalUrs > 0
    && uncoveredGxpDirect.length === 0

  // Prefer pointing the user at GxP Direct gaps first.
  const firstUncovered =
    uncoveredGxpDirect[0] ?? uncoveredAll[0] ?? null

  return {
    totalUrs, urs: augmented,
    uncoveredAll, uncoveredGxpDirect,
    coveragePct, canCompleteDesign, firstUncovered,
  }
}

// ── Banner component ──────────────────────────────────────────────
export default function CoverageMonitor({
  requirements, riskData, testBundles,
  onJumpToAuthoring,           // (reqId) => void
  compact = false,             // tighter version for Release page
}) {
  const cov = computeCoverage(requirements, riskData, testBundles)
  const {
    totalUrs, uncoveredAll, uncoveredGxpDirect,
    coveragePct, canCompleteDesign, firstUncovered,
  } = cov

  if (totalUrs === 0) return null

  // Determine status colour
  let tone = 'green'
  if (uncoveredGxpDirect.length > 0)        tone = 'red'
  else if (uncoveredAll.length > 0)         tone = 'amber'

  const TONE = {
    green: {
      bg: 'rgba(50,205,50,0.06)',  border: 'rgba(50,205,50,0.30)',
      text: '#32CD32', dot: '#32CD32',
    },
    amber: {
      bg: 'rgba(245,158,11,0.06)', border: 'rgba(245,158,11,0.30)',
      text: '#f59e0b', dot: '#f59e0b',
    },
    red: {
      bg: 'rgba(239,68,68,0.06)',  border: 'rgba(239,68,68,0.40)',
      text: '#ef4444', dot: '#ef4444',
    },
  }[tone]

  const headline = (() => {
    if (tone === 'green') {
      return `✓ All ${totalUrs} UR${totalUrs === 1 ? '' : 's'}`
        + ` covered by test bundles · Design phase ready`
    }
    if (tone === 'red') {
      return `🛑 ${uncoveredGxpDirect.length} GxP Direct `
        + `UR${uncoveredGxpDirect.length === 1 ? '' : 's'}`
        + ` uncovered · Design phase blocked`
    }
    return `⚠ ${uncoveredAll.length} of ${totalUrs}`
      + ` UR${uncoveredAll.length === 1 ? '' : 's'} lack test bundles`
  })()

  const detail = (() => {
    if (tone === 'green') return null
    const missing = uncoveredAll.slice(0, 6).join(', ')
    const more = uncoveredAll.length > 6
      ? ` +${uncoveredAll.length - 6} more` : ''
    return `${coveragePct}% coverage · Missing: ${missing}${more}`
  })()

  return (
    <div
      className={`flex items-center gap-3 px-4 ${
        compact ? 'py-1.5' : 'py-2'} border-b shrink-0`}
      style={{ background: TONE.bg, borderColor: TONE.border }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full shrink-0"
        style={{ background: TONE.dot }}
      />
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className={`${compact ? 'text-[10px]' : 'text-[11px]'}
                          font-semibold`}
              style={{ color: TONE.text }}>
          {headline}
        </span>
        {detail && !compact && (
          <span className="text-[10px] text-text-muted truncate">
            {detail}
          </span>
        )}
      </div>

      {/* Coverage % chip */}
      <span className="ml-auto text-[10px] px-2 py-0.5 rounded
                       border border-border-base text-text-muted
                       font-mono shrink-0">
        {coveragePct}%
      </span>

      {/* CTA — only when there's a gap and a jump handler is provided */}
      {firstUncovered && onJumpToAuthoring && !compact && (
        <button
          onClick={() => onJumpToAuthoring(firstUncovered)}
          className="text-[10px] px-2.5 py-1 rounded font-semibold
                     transition-opacity hover:opacity-90 shrink-0"
          style={{
            background: 'rgba(168,85,247,0.85)',
            color: 'white',
          }}
        >
          ⚡ Generate for {firstUncovered}
        </button>
      )}

      {!canCompleteDesign && !compact && (
        <span className="text-[9px] uppercase tracking-wide
                         font-semibold shrink-0"
              style={{ color: TONE.text }}
              title="GxP Direct URs must have at least one test bundle
                before the Design phase can be marked complete.">
          Hard block
        </span>
      )}
    </div>
  )
}
