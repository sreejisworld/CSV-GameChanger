/**
 * RegulatoryWatch — Regulatory Change Impact Analyzer
 *
 * Select a regulation (built-in or user-added) → EVOLV cross-references
 * the full system portfolio and flags every system that requires action.
 *
 * Built-in regulations are hard-coded with precise impact logic.
 * Custom regulations use user-defined scope rules (impact level +
 * recommended actions per GxP tier).
 */
import { useState, useMemo, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { SYSTEMS, AI_MODELS } from '../data/systems.js'
import { useAppStore } from '../store/useAppStore.js'
import { API_BASE } from '../config.js'

// ── Built-in regulation definitions ───────────────────────────────
const REGULATIONS = [
  {
    id:    'qmsr',
    icon:  '⚖️',
    color: '#f59e0b',
    name:  '21 CFR Part 820 QMSR',
    date:  'Effective Feb 2, 2026',
    tag:   'Mandatory Now',
    summary:
      'Quality Management System Regulation replaces the old QSR. '
      + 'ISO 13485:2016 is incorporated by reference at §820.7. '
      + 'Old §820.30 (Design Controls), §820.40 (Document Controls), '
      + 'and §820.180 (Records) are now Reserved.',
    sections: [
      '§820.7 — ISO 13485:2016 incorporated by reference',
      '§820.30 — RESERVED (was Design Controls)',
      '§820.40 — RESERVED (was Document Controls)',
      '§820.180 / §820.181 — RESERVED (was Records)',
    ],
  },
  {
    id:    'pccp',
    icon:  '🤖',
    color: '#a855f7',
    name:  'FDA PCCP Guidance',
    date:  'Final — Aug 18, 2025',
    tag:   'Final Guidance',
    summary:
      'Marketing Submission Recommendations for a Predetermined '
      + 'Change Control Plan for AI-Enabled Device Software Functions. '
      + 'Issued under 21 U.S.C. 360e-4 (added by FDORA Dec 2022).',
    sections: [
      '§V — Authorized PCCP (pre-approved change scope)',
      '§VI.C — Locked Changes require new submission',
      '§VII.B — Modification Protocol & acceptance criteria',
      '§VII.B(4) — Post-market performance monitoring',
    ],
  },
  {
    id:    'euaiact',
    icon:  '🇪🇺',
    color: '#007FFF',
    name:  'EU AI Act',
    date:  'In force Aug 2024',
    tag:   'EU Mandatory',
    summary:
      'Risk-based framework for AI systems placed on the EU market. '
      + 'AI used in medical devices is classified as high-risk '
      + '(Annex III). Requires conformity assessment, risk management, '
      + 'transparency, and human oversight.',
    sections: [
      'Art. 6 / Annex III — High-risk classification',
      'Art. 9 — Risk management system',
      'Art. 13 — Transparency obligations',
      'Art. 14 — Human oversight',
      'Art. 43 — Conformity assessment',
    ],
  },
  {
    id:    'ichq9r1',
    icon:  '📊',
    color: '#32CD32',
    name:  'ICH Q9(R1)',
    date:  'Adopted 2023',
    tag:   'Revised Guidance',
    summary:
      'Revised Quality Risk Management guideline. Key additions: '
      + 'explicit acknowledgement of subjectivity in risk assessments '
      + '(§2.5), updated risk communication requirements, and clearer '
      + 'triggers for QRM review and escalation.',
    sections: [
      '§2.5 — Subjectivity in risk assessment (new)',
      '§3 — Risk communication obligations',
      '§4 — QRM integration into lifecycle',
      'Annex I — Risk assessment methods updated',
    ],
  },
]

// ── Built-in impact analysis engine ───────────────────────────────
const IMPACT_LEVEL_ORDER = { High: 0, Medium: 1, Low: 2 }

function analyzeBuiltInImpact(regulationId, allSystems) {
  return allSystems.map(sys => {
    let level = null; let reason = ''; let actions = []

    if (regulationId === 'qmsr') {
      if (sys.gxpStatus === 'GxP Direct') {
        level  = 'High'
        reason = 'GxP Direct systems are fully subject to QMSR. Old '
          + '§820.30/§820.40/§820.180 are Reserved — all citations must '
          + 'now reference ISO 13485:2016 via §820.7.'
        actions = [
          'Update SOPs citing §820.30 → ISO 13485 Clause 7.3',
          'Update document control refs: §820.40 → ISO 13485 §4.2',
          'Update record retention refs: §820.180 → ISO 13485 §4.2.5',
          'Confirm VMP and URS cite §820.7 not deprecated sections',
          'Schedule QMSR gap assessment with QA lead',
        ]
      } else if (sys.gxpStatus === 'GxP Indirect') {
        level  = 'Medium'
        reason = 'GxP Indirect systems may reference deprecated QSR '
          + 'sections in validation docs. Review and update citations.'
        actions = [
          'Scan validation docs for §820.30 / §820.40 references',
          'Update any references to ISO 13485 equivalent clauses',
          'Document review finding in change control record',
        ]
      }
    }

    if (regulationId === 'pccp') {
      if (sys.isAIModel && sys.gxpStatus === 'GxP Direct') {
        level  = 'High'
        reason = 'GxP Direct AI model — PCCP compliance mandatory for '
          + 'any planned changes to architecture, training data, or '
          + 'performance thresholds. Locked changes need new submission.'
        actions = [
          'Verify PCCP has been submitted or prepare PCCP document',
          'Classify all planned changes: Locked vs Adaptive',
          'Establish Modification Protocol with acceptance criteria',
          'Implement post-market performance monitoring (§VII.B(4))',
          sys.modelMeta?.pccpApproved
            ? '✓ PCCP already approved — verify coverage of current scope'
            : '⚠ PCCP not yet approved — submit before next model update',
        ]
      } else if (sys.isAIModel && sys.gxpStatus === 'GxP Indirect') {
        level  = 'Medium'
        reason = 'GxP Indirect AI model — assess whether PCCP '
          + 'submission is required. Document planned changes.'
        actions = [
          'Assess whether intended use triggers PCCP requirement',
          'Document planned model changes and risk classification',
          'Consult regulatory affairs on submission strategy',
        ]
      } else if (sys.regulations?.includes('FDA PCCP Guidance Aug 2025')) {
        level  = 'High'
        reason = 'System flagged as subject to PCCP guidance. '
          + 'Verify compliance with final Aug 2025 version.'
        actions = [
          'Review PCCP compliance status against final guidance',
          'Ensure Modification Protocol is current and approved',
        ]
      }
    }

    if (regulationId === 'euaiact') {
      if (sys.isAIModel && sys.gxpStatus === 'GxP Direct') {
        level  = 'High'
        reason = 'AI system in medical device context — classified as '
          + 'high-risk under EU AI Act Annex III. Conformity assessment '
          + 'and human oversight are mandatory.'
        actions = [
          'Conduct conformity assessment (Art. 43)',
          'Implement and document risk management system (Art. 9)',
          'Establish human oversight mechanism (Art. 14)',
          'Prepare technical documentation (Annex IV)',
          'Register in EU database before EU market placement',
        ]
      } else if (sys.isAIModel && sys.gxpStatus === 'GxP Indirect') {
        level  = 'Medium'
        reason = 'AI system — assess risk classification under EU AI '
          + 'Act. GxP Indirect use may still trigger high-risk category.'
        actions = [
          'Classify system risk level under Art. 6 / Annex III',
          'Document intended purpose and foreseeable misuse scenarios',
          'Assess transparency obligations (Art. 13)',
        ]
      } else if (sys.isAIModel) {
        level  = 'Low'
        reason = 'Non-GxP AI system — likely limited-risk under EU AI '
          + 'Act. Transparency obligations may still apply.'
        actions = [
          'Confirm risk classification (Art. 6)',
          'Review transparency requirements for your use case',
        ]
      }
    }

    if (regulationId === 'ichq9r1') {
      if (sys.gxpStatus === 'GxP Direct') {
        level  = 'Medium'
        reason = 'GxP Direct system — QRM processes should reflect '
          + 'ICH Q9(R1) additions on subjectivity (§2.5) and updated '
          + 'risk communication requirements.'
        actions = [
          'Review risk assessments for subjectivity acknowledgement (§2.5)',
          'Update risk communication procedures (§3)',
          'Schedule QRM process review with QA',
          'Align FMEA templates with Annex I updates',
        ]
      } else if (sys.gxpStatus === 'GxP Indirect') {
        level  = 'Low'
        reason = 'GxP Indirect — review QRM documentation for R1 alignment.'
        actions = [
          'Scan QRM documents for Q9(R1) compliance gaps',
          'Update where needed and document in change control',
        ]
      }
    }

    if (!level) return null
    return { ...sys, impactLevel: level, impactReason: reason,
             impactActions: actions }
  })
  .filter(Boolean)
  .sort((a, b) =>
    IMPACT_LEVEL_ORDER[a.impactLevel] - IMPACT_LEVEL_ORDER[b.impactLevel])
}

// ── Custom regulation impact engine ───────────────────────────────
function analyzeCustomImpact(reg, allSystems) {
  const { rules } = reg
  return allSystems.map(sys => {
    let rule = null
    if (sys.isAIModel && sys.gxpStatus === 'GxP Direct')
      rule = rules.aiModelDirect
    else if (sys.isAIModel && sys.gxpStatus === 'GxP Indirect')
      rule = rules.aiModelIndirect
    else if (sys.gxpStatus === 'GxP Direct')
      rule = rules.gxpDirect
    else if (sys.gxpStatus === 'GxP Indirect')
      rule = rules.gxpIndirect
    else
      rule = rules.nonGxP

    if (!rule?.level) return null
    return {
      ...sys,
      impactLevel:   rule.level,
      impactReason:  `Per ${reg.name} (${reg.date}): This system's `
        + `${sys.gxpStatus} classification requires compliance review.`,
      impactActions: rule.actions.filter(Boolean),
    }
  })
  .filter(Boolean)
  .sort((a, b) =>
    IMPACT_LEVEL_ORDER[a.impactLevel] - IMPACT_LEVEL_ORDER[b.impactLevel])
}

// ── Shared helpers ─────────────────────────────────────────────────
const LEVEL_COLOR = {
  High: '#ef4444', Medium: '#f59e0b', Low: '#32CD32',
}
const LEVEL_BG = {
  High: 'rgba(239,68,68,0.1)', Medium: 'rgba(245,158,11,0.1)',
  Low:  'rgba(50,205,50,0.1)',
}
const GXP_COLOR = {
  'GxP Direct':   '#ef4444',
  'GxP Indirect': '#f59e0b',
  'Non-GxP':      '#64748b',
}
const PHASE_EMOJI = {
  Plan:'📋', Requirements:'📝', Risk:'⚖️', Design:'🎨',
  Verify:'🏭', Released:'✅', Monitor:'📡', Retire:'🔒',
}
const PRESET_COLORS = [
  '#007FFF', '#f59e0b', '#ef4444', '#32CD32',
  '#a855f7', '#ec4899', '#14b8a6', '#64748b',
]
const LEVEL_OPTIONS = ['High', 'Medium', 'Low', 'None']

function downloadCSV(reg, results) {
  const rows = results.map(s => [
    s.id, s.name, s.gxpStatus,
    `GAMP ${s.gampCategory}`, s.phase, s.impactLevel,
    `"${s.impactReason.replace(/"/g, "'")}"`,
    `"${s.impactActions.join(' | ').replace(/"/g, "'")}"`,
  ])
  const header = [
    'System ID','System Name','GxP Status','GAMP Category',
    'Phase','Impact Level','Rationale','Recommended Actions',
  ]
  const csv  = [header, ...rows].map(r => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url
  a.download = `EVOLV-ImpactAlert-${reg.id}-${
    new Date().toISOString().slice(0,10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// ─── Sprint 38 — Drift Detection Panel ────────────────────────────
// Sister surface to the change-impact analyzer below. The analyzer
// is forward-looking ("a NEW reg landed — which systems are hit?");
// the drift panel is backward-looking ("which of my URs cite a
// SUPERSEDED version of a reg I'm already grounded against?").
//
// Drift detection has two information surfaces:
//   1. Corpus version registry — what EVOLV is currently grounded
//      against. Read-only. Auditor question: "What corpus did the
//      AI use?"
//   2. Project scan — runs the agent over the live requirements
//      slice and surfaces affected URs with citation deltas
//      (cited_version → current_version) + a suggested action.
//
// :requirement: URS-38.9 - Surface drift detection in the platform UI.

function CorpusVersionsCard({ registry, loading, error, onReload }) {
  const frameworks = registry?.frameworks ?? {}
  const entries    = Object.entries(frameworks)

  return (
    <div className="glass rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-text-primary text-[12px] font-semibold">
            📚 Corpus Version Registry
          </p>
          <p className="text-text-muted text-[10px] mt-0.5">
            The regulatory frameworks EVOLV is currently grounded
            against. Read-only — corpus versions are bumped only
            by the Ingestor agent.
          </p>
        </div>
        <button
          onClick={onReload}
          disabled={loading}
          className="px-2.5 py-1 text-[10px] rounded border
                     border-border-base text-text-muted
                     hover:text-text-secondary disabled:opacity-40
                     transition-colors"
        >
          {loading ? '…' : '↻ Reload'}
        </button>
      </div>

      {error && (
        <p className="text-[10px] text-red-400">{error}</p>
      )}

      {entries.length > 0 && (
        <div className="grid grid-cols-2 gap-2">
          {entries.map(([name, meta]) => (
            <div key={name}
              className="rounded-lg border border-border-base
                         px-3 py-2 bg-bg-base/40">
              <div className="flex items-center justify-between gap-2">
                <span className="text-text-primary text-[11px]
                                 font-semibold truncate">
                  {name}
                </span>
                <span className="text-[9px] font-mono px-1.5 py-0.5
                                 rounded"
                  style={{ color:'#32CD32',
                           background:'rgba(50,205,50,0.1)' }}>
                  {meta?.current_version ?? '—'}
                </span>
              </div>
              {Array.isArray(meta?.previous_versions)
                && meta.previous_versions.length > 0 && (
                <p className="text-[9px] text-text-muted mt-1">
                  Previous:{' '}
                  <span className="font-mono">
                    {meta.previous_versions.join(', ')}
                  </span>
                </p>
              )}
              {meta?.last_ingested_at && (
                <p className="text-[9px] text-text-muted mt-0.5">
                  Last ingested:{' '}
                  {new Date(meta.last_ingested_at)
                    .toLocaleDateString()}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function AffectedURRow({ ur }) {
  return (
    <div className="rounded-lg border border-amber-500/30
                    bg-amber-500/5 px-3 py-2.5 space-y-2">
      <div className="flex items-start gap-2">
        <span className="text-[9px] font-mono text-text-muted shrink-0
                         mt-0.5">
          {ur.ur_id}
        </span>
        <p className="text-text-secondary text-[11px] leading-snug
                      flex-1">
          {ur.statement || '(no statement)'}
        </p>
      </div>
      <div className="space-y-1.5">
        {(ur.affected_citations ?? []).map((c, i) => (
          <div key={i}
            className="flex items-center gap-2 text-[10px]
                       text-text-secondary">
            <span className="font-semibold">{c.framework}</span>
            <span className="font-mono px-1.5 py-0.5 rounded"
              style={{ color:'#ef4444',
                       background:'rgba(239,68,68,0.1)' }}>
              {c.cited_version}
            </span>
            <span className="text-text-muted">→</span>
            <span className="font-mono px-1.5 py-0.5 rounded"
              style={{ color:'#32CD32',
                       background:'rgba(50,205,50,0.1)' }}>
              {c.current_version}
            </span>
            <span className="text-text-muted text-[9px] ml-auto">
              via {c.detection_source}
            </span>
          </div>
        ))}
      </div>
      {ur.suggested_action && (
        <p className="text-[10px] text-amber-400 italic">
          → {ur.suggested_action}
        </p>
      )}
    </div>
  )
}

function DriftDetectionPanel() {
  const requirements    = useAppStore(s => s.requirements)
  const projectName     = useAppStore(s => s.planData?.projectName)
  // Default-guard: pre-Sprint-38 persisted state has no
  // regulatoryDrift key — keep the panel alive on stale localStorage.
  const regulatoryDrift = useAppStore(s => s.regulatoryDrift) ?? {
    report: null, byUrId: {}, loading: false,
    error: null, lastFetched: null,
  }
  const setLoading      = useAppStore(s => s.setRegulatoryDriftLoading)
  const setReport       = useAppStore(s => s.setRegulatoryDriftReport)
  const setError        = useAppStore(s => s.setRegulatoryDriftError)
  const clear           = useAppStore(s => s.clearRegulatoryDrift)

  const [registry,     setRegistry]     = useState(null)
  const [regLoading,   setRegLoading]   = useState(false)
  const [regError,     setRegError]     = useState('')

  const loadRegistry = useCallback(async () => {
    setRegLoading(true); setRegError('')
    try {
      const res = await fetch(
        `${API_BASE}/regulatory-drift/corpus-versions`,
        { signal: AbortSignal.timeout(10000) },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setRegistry(await res.json())
    } catch (e) {
      setRegError(
        e.message ?? 'Failed to load corpus registry. '
        + 'Ensure FastAPI is running on port 8000.',
      )
    } finally {
      setRegLoading(false)
    }
  }, [])

  useEffect(() => { loadRegistry() }, [loadRegistry])

  const reqCount = requirements?.length ?? 0
  const canScan  = reqCount > 0 && !regulatoryDrift.loading

  const handleScan = useCallback(async () => {
    setLoading(true)
    try {
      const body = {
        project_name: projectName || 'Untitled Project',
        requirements: (requirements ?? []).map(r => ({
          id:        r.urId ?? r.id,
          type:      r.type ?? 'UR',
          statement: r.statement ?? r.text ?? '',
          parentId:  r.parentId ?? null,
          reg_versions_cited: r.regVersionsCited ?? null,
        })),
        user_id: 'demo',
      }
      const res = await fetch(
        `${API_BASE}/regulatory-drift/scan`,
        {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify(body),
          signal:  AbortSignal.timeout(20000),
        },
      )
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(errBody.detail ?? `HTTP ${res.status}`)
      }
      setReport(await res.json())
    } catch (e) {
      setError(
        e.message ?? 'Drift scan failed. '
        + 'Ensure FastAPI is running on port 8000.',
      )
    }
  }, [projectName, requirements, setLoading, setReport, setError])

  const report = regulatoryDrift.report

  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-text-primary font-semibold text-sm mb-1">
          Are any of my requirements citing superseded regulations?
        </h2>
        <p className="text-text-secondary text-xs">
          The drift detector scans every UR against the corpus
          version registry. If a UR cites a previous version of any
          framework EVOLV has re-ingested, it's flagged here and
          the citation_drift signal fires on the Validated State
          Engine's per-UR score.
        </p>
      </div>

      <CorpusVersionsCard
        registry={registry}
        loading={regLoading}
        error={regError}
        onReload={loadRegistry}
      />

      <div className="glass rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between gap-3
                        flex-wrap">
          <div>
            <p className="text-text-primary text-[12px] font-semibold">
              🔎 Project Drift Scan
            </p>
            <p className="text-text-muted text-[10px] mt-0.5">
              Scans {reqCount} requirement(s) from{' '}
              <span className="text-text-secondary">
                {projectName || '(no project selected)'}
              </span>
              .
            </p>
          </div>
          <div className="flex items-center gap-2">
            {report && (
              <button onClick={clear}
                className="px-2.5 py-1 text-[10px] rounded border
                           border-border-base text-text-muted
                           hover:text-text-secondary transition-colors">
                Clear
              </button>
            )}
            <button
              onClick={handleScan}
              disabled={!canScan}
              className="px-3 py-1.5 text-xs rounded font-semibold
                         text-white shadow-sm disabled:opacity-40
                         disabled:cursor-not-allowed
                         transition-opacity hover:opacity-90"
              style={{
                background:
                  'linear-gradient(90deg, #007FFF, #32CD32)',
              }}
              title={reqCount === 0
                ? 'No requirements in the current project to scan'
                : 'Run the Regulatory Drift Agent against this '
                  + 'project'}
            >
              {regulatoryDrift.loading
                ? '🔎 Scanning…'
                : '🔎 Scan project for drift'}
            </button>
          </div>
        </div>

        {regulatoryDrift.error && (
          <div className="px-3 py-2 rounded-lg text-[11px]
                          border border-red-500/30
                          bg-red-500/10 text-red-400">
            {regulatoryDrift.error}
          </div>
        )}

        {report && (
          <div className="space-y-3">
            {(() => {
              const hits    = report.affected_ur_count ?? 0
              const isClean = hits === 0
              const tone    = isClean
                ? { fg: '#32CD32', bg: 'rgba(50,205,50,0.08)' }
                : { fg: '#f59e0b', bg: 'rgba(245,158,11,0.08)' }
              return (
                <div className="px-3 py-2 rounded-lg border
                                flex items-center gap-3 text-[11px]"
                  style={{
                    background:  tone.bg,
                    borderColor: tone.fg + '44',
                  }}
                >
                  <span className="w-2 h-2 rounded-full shrink-0"
                    style={{ background: tone.fg }} />
                  <span className="font-semibold"
                    style={{ color: tone.fg }}>
                    {isClean
                      ? 'Clean'
                      : `${hits} of ${report.ur_count}` +
                        ` UR(s) affected`}
                  </span>
                  <span className="text-text-secondary flex-1
                                   leading-relaxed">
                    {report.headline}
                  </span>
                  <span className="text-[10px] text-text-muted
                                   shrink-0">
                    {new Date(report.scanned_at)
                      .toLocaleString()}
                  </span>
                </div>
              )
            })()}

            {(report.affected_urs ?? []).length > 0 && (
              <div className="space-y-2">
                {report.affected_urs.map(ur => (
                  <AffectedURRow key={ur.ur_id} ur={ur} />
                ))}
              </div>
            )}

            {Array.isArray(report.reasoning_chain)
              && report.reasoning_chain.length > 0 && (
              <details className="text-[10px] text-text-muted">
                <summary className="cursor-pointer
                                    hover:text-text-secondary">
                  Show agent reasoning chain
                  ({report.reasoning_chain.length} steps)
                </summary>
                <ol className="mt-2 space-y-1 pl-5 list-decimal">
                  {report.reasoning_chain.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ol>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ── System impact card ─────────────────────────────────────────────
function ImpactCard({ sys, index }) {
  const [expanded, setExpanded] = useState(false)
  const lvlColor = LEVEL_COLOR[sys.impactLevel]
  const lvlBg    = LEVEL_BG[sys.impactLevel]

  return (
    <motion.div
      initial={{ opacity:0, y:10 }}
      animate={{ opacity:1, y:0 }}
      transition={{ delay: index * 0.04 }}
      className="glass rounded-xl overflow-hidden"
    >
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center gap-3 px-4 py-3
                   hover:bg-bg-hover/40 transition-colors text-left"
      >
        <span
          className="text-[9px] font-bold px-2 py-1 rounded shrink-0
                     min-w-[52px] text-center"
          style={{ color:lvlColor, background:lvlBg,
                   border:`1px solid ${lvlColor}30` }}
        >
          {sys.impactLevel}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-white text-[11px] font-semibold truncate">
              {sys.isAIModel ? '🤖 ' : ''}{sys.name}
            </span>
            <span className="text-[9px] font-mono text-text-muted shrink-0">
              {sys.id}
            </span>
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-[9px]"
              style={{ color: GXP_COLOR[sys.gxpStatus] }}>
              {sys.gxpStatus}
            </span>
            <span className="text-text-muted text-[9px]">·</span>
            <span className="text-text-muted text-[9px]">
              GAMP {sys.gampCategory}
            </span>
            <span className="text-text-muted text-[9px]">·</span>
            <span className="text-text-muted text-[9px]">
              {PHASE_EMOJI[sys.phase] ?? '📌'} {sys.phase}
            </span>
            <span className="text-text-muted text-[9px]">·</span>
            <span className="text-text-muted text-[9px]">{sys.site}</span>
          </div>
        </div>
        <span className={`text-text-muted text-xs transition-transform
          ${expanded ? 'rotate-180' : ''}`}>▾</span>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height:0, opacity:0 }}
            animate={{ height:'auto', opacity:1 }}
            exit={{ height:0, opacity:0 }}
            transition={{ duration:0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3 border-t border-border-base pt-3">
              <div>
                <p className="text-[9px] text-text-muted uppercase
                               tracking-wider mb-1">Why impacted</p>
                <p className="text-[11px] text-text-secondary leading-relaxed">
                  {sys.impactReason}
                </p>
              </div>
              <div>
                <p className="text-[9px] text-text-muted uppercase
                               tracking-wider mb-1.5">
                  Recommended actions
                </p>
                <ul className="space-y-1">
                  {sys.impactActions.map((a, i) => (
                    <li key={i}
                      className="flex items-start gap-2 text-[11px]
                                 text-text-secondary">
                      <span className="mt-0.5 w-1.5 h-1.5 rounded-full shrink-0"
                        style={{ backgroundColor: lvlColor }} />
                      {a}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="flex items-center gap-4 text-[9px]
                              text-text-muted pt-1">
                <span>Owner: {sys.owner ?? '—'}</span>
                {sys.dueDate && (
                  <span className="px-1.5 py-0.5 rounded"
                    style={{ color:'#f59e0b',
                             background:'rgba(245,158,11,0.1)' }}>
                    Due {sys.dueDate}
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ── Add Regulation Panel ───────────────────────────────────────────
const BLANK_RULES = {
  gxpDirect:      { level:'High',   actions:[''] },
  gxpIndirect:    { level:'Medium', actions:[''] },
  aiModelDirect:  { level:'High',   actions:[''] },
  aiModelIndirect:{ level:'Low',    actions:[''] },
  nonGxP:         { level:'None',   actions:[]   },
}

const SCOPE_LABELS = {
  gxpDirect:      'GxP Direct systems',
  gxpIndirect:    'GxP Indirect systems',
  aiModelDirect:  'AI Models — GxP Direct',
  aiModelIndirect:'AI Models — GxP Indirect',
  nonGxP:         'Non-GxP systems',
}

function AddRegulationPanel({ onClose, onSave }) {
  const [form, setForm] = useState({
    icon: '📋', name: '', date: '', tag: '',
    color: '#007FFF', summary: '', sections: [''],
    rules: structuredClone(BLANK_RULES),
  })
  const [error, setError] = useState('')

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const setSection = (i, val) =>
    setForm(f => {
      const s = [...f.sections]; s[i] = val
      return { ...f, sections: s }
    })

  const addSection = () =>
    setForm(f => ({ ...f, sections: [...f.sections, ''] }))

  const removeSection = i =>
    setForm(f => ({
      ...f, sections: f.sections.filter((_, idx) => idx !== i),
    }))

  const setRuleLevel = (scope, level) =>
    setForm(f => ({
      ...f,
      rules: { ...f.rules,
        [scope]: { ...f.rules[scope], level },
      },
    }))

  const setRuleAction = (scope, i, val) =>
    setForm(f => {
      const actions = [...f.rules[scope].actions]
      actions[i] = val
      return { ...f,
        rules: { ...f.rules, [scope]: { ...f.rules[scope], actions } },
      }
    })

  const addRuleAction = scope =>
    setForm(f => ({
      ...f,
      rules: { ...f.rules,
        [scope]: { ...f.rules[scope],
          actions: [...f.rules[scope].actions, ''],
        },
      },
    }))

  const removeRuleAction = (scope, i) =>
    setForm(f => ({
      ...f,
      rules: { ...f.rules,
        [scope]: { ...f.rules[scope],
          actions: f.rules[scope].actions.filter((_, idx) => idx !== i),
        },
      },
    }))

  const handleSave = () => {
    if (!form.name.trim()) { setError('Name is required.'); return }
    if (!form.date.trim()) { setError('Date is required.'); return }
    setError('')
    onSave({
      ...form,
      id:       'custom-' + Date.now(),
      custom:   true,
      sections: form.sections.filter(s => s.trim()),
      rules:    Object.fromEntries(
        Object.entries(form.rules).map(([k, v]) => [
          k,
          { level: v.level === 'None' ? null : v.level,
            actions: v.actions.filter(a => a.trim()) },
        ])
      ),
    })
  }

  return (
    <motion.div
      initial={{ opacity:0 }}
      animate={{ opacity:1 }}
      exit={{ opacity:0 }}
      className="fixed inset-0 z-50 flex items-start justify-center
                 pt-12 px-4 pb-4"
      style={{ background:'rgba(0,0,0,0.7)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <motion.div
        initial={{ scale:0.96, y:16 }}
        animate={{ scale:1, y:0 }}
        exit={{ scale:0.96, y:16 }}
        className="bg-bg-base border border-border-base rounded-2xl
                   w-full max-w-2xl max-h-[85vh] overflow-y-auto
                   shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Modal header */}
        <div className="flex items-center justify-between px-6 py-4
                        border-b border-border-base sticky top-0
                        bg-bg-base z-10">
          <div>
            <p className="text-white text-sm font-semibold">
              Add Regulation
            </p>
            <p className="text-text-muted text-[10px] mt-0.5">
              Define the regulation and impact rules per GxP scope
            </p>
          </div>
          <button onClick={onClose}
            className="text-text-muted hover:text-text-primary
                       transition-colors text-lg leading-none">
            ✕
          </button>
        </div>

        <div className="px-6 py-5 space-y-5">

          {/* ── Basic info ─────────────────────────────────────── */}
          <div className="grid grid-cols-12 gap-3">
            {/* Icon */}
            <div className="col-span-2">
              <label className="text-[10px] text-text-muted block mb-1">
                Icon
              </label>
              <input value={form.icon}
                onChange={e => set('icon', e.target.value)}
                className="evolv-input w-full text-center text-xl px-2 py-2"
                maxLength={4}
              />
            </div>
            {/* Name */}
            <div className="col-span-6">
              <label className="text-[10px] text-text-muted block mb-1">
                Regulation Name *
              </label>
              <input value={form.name}
                onChange={e => set('name', e.target.value)}
                placeholder="e.g. EU GMP Annex 11"
                className="evolv-input w-full text-xs px-3 py-2"
              />
            </div>
            {/* Date */}
            <div className="col-span-4">
              <label className="text-[10px] text-text-muted block mb-1">
                Date / Version *
              </label>
              <input value={form.date}
                onChange={e => set('date', e.target.value)}
                placeholder="e.g. Revised 2011"
                className="evolv-input w-full text-xs px-3 py-2"
              />
            </div>
          </div>

          <div className="grid grid-cols-12 gap-3">
            {/* Tag */}
            <div className="col-span-4">
              <label className="text-[10px] text-text-muted block mb-1">
                Tag
              </label>
              <input value={form.tag}
                onChange={e => set('tag', e.target.value)}
                placeholder="e.g. Mandatory, Guidance"
                className="evolv-input w-full text-xs px-3 py-2"
              />
            </div>
            {/* Color */}
            <div className="col-span-8">
              <label className="text-[10px] text-text-muted block mb-1">
                Accent Color
              </label>
              <div className="flex gap-2 items-center">
                {PRESET_COLORS.map(c => (
                  <button key={c} onClick={() => set('color', c)}
                    className="w-6 h-6 rounded-full border-2 transition-all"
                    style={{
                      backgroundColor: c,
                      borderColor: form.color === c ? '#fff' : 'transparent',
                      transform: form.color === c ? 'scale(1.25)' : 'scale(1)',
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Summary */}
          <div>
            <label className="text-[10px] text-text-muted block mb-1">
              Summary
            </label>
            <textarea value={form.summary}
              onChange={e => set('summary', e.target.value)}
              rows={3}
              placeholder="Brief description of what changed and why it matters…"
              className="evolv-input w-full text-xs px-3 py-2 resize-none"
            />
          </div>

          {/* Key sections */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-[10px] text-text-muted">
                Key Sections
              </label>
              <button onClick={addSection}
                className="text-[10px] text-blue-DEFAULT hover:underline">
                + Add section
              </button>
            </div>
            <div className="space-y-1.5">
              {form.sections.map((s, i) => (
                <div key={i} className="flex gap-2">
                  <input value={s}
                    onChange={e => setSection(i, e.target.value)}
                    placeholder={`e.g. §${i + 1} — Section title`}
                    className="evolv-input flex-1 text-xs px-3 py-1.5"
                  />
                  {form.sections.length > 1 && (
                    <button onClick={() => removeSection(i)}
                      className="text-text-muted hover:text-red-400
                                 transition-colors text-xs px-1">
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Impact rules per scope */}
          <div>
            <p className="text-[10px] text-text-muted uppercase
                          tracking-wider mb-3">
              Impact Rules — per GxP scope
            </p>
            <div className="space-y-4">
              {Object.entries(SCOPE_LABELS).map(([scope, label]) => {
                const rule = form.rules[scope]
                return (
                  <div key={scope}
                    className="glass rounded-xl p-3 space-y-2">
                    <div className="flex items-center gap-3">
                      <p className="text-[11px] text-text-secondary
                                   font-medium flex-1">
                        {label}
                      </p>
                      {/* Level selector */}
                      <div className="flex gap-1">
                        {LEVEL_OPTIONS.map(lvl => (
                          <button key={lvl}
                            onClick={() => setRuleLevel(scope, lvl)}
                            className="px-2 py-0.5 rounded text-[9px]
                                       font-semibold border transition-all"
                            style={rule.level === lvl ? {
                              backgroundColor:
                                lvl === 'High'   ? '#ef4444'
                                : lvl === 'Medium' ? '#f59e0b'
                                : lvl === 'Low'  ? '#32CD32' : '#374151',
                              borderColor:'transparent', color:'#fff',
                            } : {
                              borderColor:'rgba(255,255,255,0.1)',
                              color:'#64748b',
                            }}
                          >
                            {lvl}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Actions — only show if level isn't None */}
                    {rule.level && rule.level !== 'None' && (
                      <div className="space-y-1 pl-1">
                        {rule.actions.map((a, i) => (
                          <div key={i} className="flex gap-2">
                            <input value={a}
                              onChange={e =>
                                setRuleAction(scope, i, e.target.value)}
                              placeholder="Recommended action…"
                              className="evolv-input flex-1 text-[10px]
                                         px-2 py-1"
                            />
                            <button
                              onClick={() => removeRuleAction(scope, i)}
                              className="text-text-muted hover:text-red-400
                                         transition-colors text-[10px] px-1">
                              ✕
                            </button>
                          </div>
                        ))}
                        <button onClick={() => addRuleAction(scope)}
                          className="text-[9px] text-blue-DEFAULT
                                     hover:underline mt-0.5">
                          + Add action
                        </button>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Error */}
          {error && (
            <p className="text-red-400 text-[10px]">{error}</p>
          )}

          {/* Save / Cancel */}
          <div className="flex gap-3 pt-1">
            <button onClick={handleSave}
              className="flex-1 py-2.5 rounded-xl text-xs font-bold
                         bg-blue-DEFAULT text-white hover:opacity-90
                         transition-opacity">
              Save Regulation
            </button>
            <button onClick={onClose}
              className="px-5 py-2.5 rounded-xl text-xs border
                         border-border-base text-text-muted
                         hover:text-text-secondary transition-colors">
              Cancel
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

// ── Main component ─────────────────────────────────────────────────
export default function RegulatoryWatch() {
  const {
    customSystems,
    customRegulations,
    addCustomRegulation,
    deleteCustomRegulation,
  } = useAppStore()

  const allSystems = useMemo(
    () => [...SYSTEMS, ...AI_MODELS, ...customSystems],
    [customSystems],
  )

  const allRegulations = useMemo(
    () => [...REGULATIONS, ...customRegulations],
    [customRegulations],
  )

  const [selectedId,  setSelectedId]  = useState(null)
  const [filterLevel, setFilterLevel] = useState('All')
  const [showAdd,     setShowAdd]     = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(null)

  const selectedReg = allRegulations.find(r => r.id === selectedId)

  const results = useMemo(() => {
    if (!selectedReg) return []
    return selectedReg.custom
      ? analyzeCustomImpact(selectedReg, allSystems)
      : analyzeBuiltInImpact(selectedReg.id, allSystems)
  }, [selectedReg, allSystems])

  const filtered = useMemo(() => {
    if (filterLevel === 'All') return results
    return results.filter(s => s.impactLevel === filterLevel)
  }, [results, filterLevel])

  const counts = useMemo(() => ({
    High:   results.filter(s => s.impactLevel === 'High').length,
    Medium: results.filter(s => s.impactLevel === 'Medium').length,
    Low:    results.filter(s => s.impactLevel === 'Low').length,
  }), [results])

  const handleSave = reg => {
    addCustomRegulation(reg)
    setSelectedId(reg.id)
    setFilterLevel('All')
    setShowAdd(false)
  }

  const handleDelete = id => {
    deleteCustomRegulation(id)
    if (selectedId === id) setSelectedId(null)
    setDeleteConfirm(null)
  }

  return (
    <>
      <div className="flex flex-col h-full bg-bg-base overflow-hidden">

        {/* ── Header ──────────────────────────────────────────── */}
        <div className="flex items-center gap-3 px-6 py-2.5
                        bg-blue-dim border-b border-blue-DEFAULT/20
                        shrink-0">
          <span className="text-xs font-semibold text-blue-DEFAULT">
            Regulatory Watch
          </span>
          <span className="text-text-muted text-xs">
            Change Impact Analyzer
          </span>
          <div className="ml-auto flex items-center gap-2">
            <span className="text-[9px] px-2 py-0.5 rounded border
                             text-text-muted border-border-base">
              {allSystems.length} systems monitored
            </span>
            <button
              onClick={() => setShowAdd(true)}
              className="px-3 py-1 text-[10px] rounded-lg font-semibold
                         bg-blue-DEFAULT/10 text-blue-DEFAULT border
                         border-blue-DEFAULT/30 hover:bg-blue-DEFAULT/20
                         transition-colors"
            >
              ＋ Add Regulation
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">

          {/* ── Sprint 38 — Drift Detection (top) ─────────────── */}
          <DriftDetectionPanel />

          <div className="border-t border-border-base my-2" />

          {/* ── Intro ─────────────────────────────────────────── */}
          <div>
            <h2 className="text-text-primary font-semibold text-sm mb-1">
              Which of your systems are impacted by this regulation?
            </h2>
            <p className="text-text-secondary text-xs">
              Select a regulation below. EVOLV cross-references your
              entire validated system portfolio and flags every system
              that requires action — with rationale and next steps.
            </p>
          </div>

          {/* ── Regulation picker ─────────────────────────────── */}
          <div className="grid grid-cols-4 gap-3">
            {allRegulations.map(reg => (
              <div key={reg.id} className="relative group">
                <button
                  onClick={() => {
                    setSelectedId(reg.id); setFilterLevel('All')
                  }}
                  className={`w-full p-4 rounded-xl border text-left
                    transition-all space-y-2
                    ${selectedId === reg.id
                      ? 'bg-bg-hover'
                      : 'border-border-base hover:bg-bg-hover/50'}`}
                  style={selectedId === reg.id ? {
                    borderColor: reg.color + '60',
                    boxShadow: `0 0 20px ${reg.color}18`,
                  } : {}}
                >
                  <div className="flex items-start justify-between">
                    <span className="text-xl">{reg.icon}</span>
                    <div className="flex items-center gap-1">
                      {reg.custom && (
                        <span className="text-[8px] px-1 py-0.5 rounded
                                         bg-bg-base text-text-muted border
                                         border-border-base">
                          Custom
                        </span>
                      )}
                      {reg.tag && (
                        <span className="text-[8px] font-semibold px-1.5
                                         py-0.5 rounded"
                          style={{ color:reg.color,
                                   background:reg.color+'18' }}>
                          {reg.tag}
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-white text-[11px] font-semibold
                                leading-tight">
                    {reg.name}
                  </p>
                  <p className="text-text-muted text-[9px]">{reg.date}</p>
                </button>

                {/* Delete button for custom regulations */}
                {reg.custom && (
                  <button
                    onClick={e => {
                      e.stopPropagation()
                      setDeleteConfirm(reg.id)
                    }}
                    className="absolute top-2 right-2 w-5 h-5 rounded
                               bg-red-500/10 text-red-400 text-[9px]
                               opacity-0 group-hover:opacity-100
                               transition-opacity flex items-center
                               justify-center hover:bg-red-500/20"
                    title="Delete regulation"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Delete confirm */}
          <AnimatePresence>
            {deleteConfirm && (
              <motion.div
                initial={{ opacity:0, y:-4 }}
                animate={{ opacity:1, y:0 }}
                exit={{ opacity:0, y:-4 }}
                className="glass rounded-xl p-3 flex items-center gap-4
                           border border-red-500/30"
              >
                <span className="text-red-400 text-xs flex-1">
                  Delete this custom regulation? This cannot be undone.
                </span>
                <button onClick={() => handleDelete(deleteConfirm)}
                  className="px-3 py-1 text-[10px] rounded bg-red-500/20
                             text-red-400 hover:bg-red-500/30
                             transition-colors font-semibold">
                  Delete
                </button>
                <button onClick={() => setDeleteConfirm(null)}
                  className="px-3 py-1 text-[10px] rounded border
                             border-border-base text-text-muted
                             hover:text-text-secondary transition-colors">
                  Cancel
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Regulation detail ─────────────────────────────── */}
          <AnimatePresence mode="wait">
            {selectedReg && (
              <motion.div
                key={selectedReg.id}
                initial={{ opacity:0, y:6 }}
                animate={{ opacity:1, y:0 }}
                exit={{ opacity:0, y:-6 }}
                transition={{ duration:0.2 }}
                className="glass rounded-xl p-4 space-y-3"
              >
                <div className="flex items-start gap-4">
                  <div className="flex-1">
                    <p className="text-white text-[11px] font-semibold mb-1">
                      {selectedReg.icon} {selectedReg.name}
                      <span className="ml-2 text-[9px] font-medium
                                       px-1.5 py-0.5 rounded"
                        style={{ color:selectedReg.color,
                                 background:selectedReg.color+'18' }}>
                        {selectedReg.date}
                      </span>
                    </p>
                    <p className="text-text-secondary text-[11px]
                                  leading-relaxed">
                      {selectedReg.summary || 'No summary provided.'}
                    </p>
                  </div>
                  {selectedReg.sections?.length > 0 && (
                    <div className="shrink-0 space-y-1 min-w-[220px]">
                      {selectedReg.sections.map(s => (
                        <p key={s}
                          className="text-[9px] text-text-muted font-mono
                                     bg-bg-base/60 rounded px-2 py-1">
                          {s}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Impact results ────────────────────────────────── */}
          <AnimatePresence mode="wait">
            {results.length > 0 && (
              <motion.div
                key={selectedId + '-results'}
                initial={{ opacity:0 }}
                animate={{ opacity:1 }}
                className="space-y-4"
              >
                {/* Summary + filter bar */}
                <div className="flex items-center gap-3 flex-wrap">
                  <p className="text-text-secondary text-xs">
                    <span className="text-white font-semibold">
                      {results.length}
                    </span>{' '}
                    of {allSystems.length} systems require action
                  </p>
                  {['All','High','Medium','Low'].map(lvl => (
                    <button key={lvl}
                      onClick={() => setFilterLevel(lvl)}
                      className={`px-2.5 py-1 rounded-lg text-[10px]
                        font-semibold border transition-all
                        ${filterLevel === lvl
                          ? 'text-white border-transparent'
                          : 'text-text-muted border-border-base'}`}
                      style={filterLevel === lvl ? {
                        backgroundColor:
                          lvl === 'All'    ? '#007FFF'
                          : lvl === 'High' ? '#ef4444'
                          : lvl === 'Medium' ? '#f59e0b' : '#32CD32',
                      } : {}}
                    >
                      {lvl === 'All'
                        ? `All (${results.length})`
                        : `${lvl} (${counts[lvl]})`}
                    </button>
                  ))}
                  <div className="flex gap-2 ml-auto">
                    {['High','Medium','Low']
                      .filter(l => counts[l] > 0)
                      .map(l => (
                        <span key={l}
                          className="text-[9px] font-bold px-2 py-1
                                     rounded-full"
                          style={{ color:LEVEL_COLOR[l],
                                   background:LEVEL_BG[l] }}>
                          {counts[l]} {l}
                        </span>
                      ))}
                  </div>
                  <button
                    onClick={() => downloadCSV(selectedReg, results)}
                    className="px-3 py-1 text-[10px] rounded border
                               border-border-base text-text-muted
                               hover:text-text-secondary
                               hover:border-border-bright transition-colors"
                  >
                    ↓ Export CSV
                  </button>
                </div>

                {/* System cards */}
                <div className="space-y-2">
                  {filtered.map((sys, i) => (
                    <ImpactCard key={sys.id} sys={sys} index={i} />
                  ))}
                </div>
              </motion.div>
            )}

            {!selectedId && (
              <motion.div
                key="empty"
                initial={{ opacity:0 }}
                animate={{ opacity:1 }}
                className="flex flex-col items-center justify-center
                           py-16 gap-3 text-center"
              >
                <span className="text-4xl opacity-20">📋</span>
                <p className="text-text-muted text-xs max-w-xs">
                  Select a regulation above to see which systems in
                  your portfolio require review or revalidation.
                </p>
                <button onClick={() => setShowAdd(true)}
                  className="mt-2 text-[10px] text-blue-DEFAULT
                             hover:underline">
                  ＋ Add a custom regulation
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* ── Add Regulation modal ─────────────────────────────── */}
      <AnimatePresence>
        {showAdd && (
          <AddRegulationPanel
            onClose={() => setShowAdd(false)}
            onSave={handleSave}
          />
        )}
      </AnimatePresence>
    </>
  )
}
