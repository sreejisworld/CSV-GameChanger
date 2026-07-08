import { useState, useCallback, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '../../store/useAppStore.js'
import { SYSTEMS } from '../../data/systems.js'
import { API_BASE } from '../../config.js'

const CC_API = API_BASE

// ── Sprint 35.5 (F3 fix) ────────────────────────────────────────────
// Synthesize an "active project" system entry from the live store so
// a CR submitted via this tab can target the project the user is
// actually validating — not just the static `SYSTEMS` demo registry.
//
// Returns null if there's no usable active project (no projectName,
// or projectName matches the empty default). The full Change Impact
// Assessment (compute which URs/bundles are affected, generate CIA
// document, trigger targeted revalidation) is Sprint 36 work — this
// fix is the prerequisite wire-up so the CR knows about the project
// at all.
function buildActiveProjectSystem(
  planData, riskData, requirements, phaseCompletion, releaseData,
) {
  const name = (planData?.projectName ?? '').trim()
  if (!name) return null

  // Roll up GxP status from per-UR risk impacts (worst wins).
  const rows = Object.values(riskData ?? {})
  let gxpStatus = 'Non-GxP'
  if (rows.some(r => r?.impact === 'GxP Direct'))   gxpStatus = 'GxP Direct'
  else if (rows.some(r => r?.impact === 'GxP Indirect')) gxpStatus = 'GxP Indirect'

  // Roll up risk level — worst wins.
  let risk = 'Low'
  if (rows.some(r => r?.riskLevel === 'HIGH'))   risk = 'High'
  else if (rows.some(r => r?.riskLevel === 'MEDIUM')) risk = 'Medium'

  // Current lifecycle phase — `Monitor` once released, otherwise the
  // most-recently-completed phase. Mirrors the SYSTEMS.phase strings.
  const PHASE_ORDER = [
    ['plan',         'Plan'],
    ['requirements', 'Requirements'],
    ['risk',         'Risk'],
    ['design',       'Design'],
    ['verify',       'Verify'],
    ['release',      'Released'],
  ]
  let phase = 'Plan'
  if (releaseData?.released) phase = 'Monitor'
  else {
    for (const [k, label] of PHASE_ORDER) {
      if (phaseCompletion?.[k]) phase = label
    }
  }

  const urCount = (requirements ?? []).filter(r => r?.type === 'UR').length

  return {
    id:           'PROJ-ACTIVE',
    name,
    gampCategory: Number(planData?.gampCategory) || 4,
    gxpStatus,
    site:         'Active validation project',
    phase,
    risk,
    owner:        planData?.vmpContent?.resourcesResponsibilities
                    ? 'See VMP'
                    : 'Unassigned',
    lastAction:   new Date().toISOString().slice(0, 10),
    dueDate:      null,
    regulations:  planData?.regulatoryFrameworks ?? [],
    notes:
      `Active EVOLV project · ${urCount} UR${urCount === 1 ? '' : 's'} · `
      + 'changes will (Sprint 36) trigger Change Impact Assessment.',
    isActiveProject: true,
  }
}

const SN_SCENARIOS = [
  { label: 'Emergency Patch',     icon: '🚨', color: '#ef4444',
    cr_id: 'CR-2024-0891', description: 'Critical security patch — production LIMS',
    system_criticality: 'critical', change_type: 'emergency',
    system_name: 'LabVantage LIMS' },
  { label: 'Normal Upgrade',      icon: '🔼', color: '#f59e0b',
    cr_id: 'CR-2024-0892', description: 'ServiceNow v8.2 platform upgrade',
    system_criticality: 'high',     change_type: 'normal',
    system_name: 'ServiceNow ITSM' },
  { label: 'Config Change',       icon: '⚙️', color: '#007FFF',
    cr_id: 'CR-2024-0893', description: 'Update change approval workflow',
    system_criticality: 'medium',   change_type: 'standard',
    system_name: 'SharePoint DMS' },
  { label: 'Routine Maintenance', icon: '🔧', color: '#32CD32',
    cr_id: 'CR-2024-0894', description: 'Quarterly password rotation',
    system_criticality: 'low',      change_type: 'routine',
    system_name: 'Salesforce CRM' },
]

const CC_SEV_MAP = {
  critical: 'HIGH', high: 'HIGH', medium: 'MEDIUM',
  moderate: 'MEDIUM', low: 'LOW', minor: 'LOW',
}
const CC_OCC_MAP = {
  emergency: 'FREQUENT', expedited: 'FREQUENT',
  normal: 'OCCASIONAL', standard: 'RARE', routine: 'RARE',
}
const CC_SCALE = {
  HIGH: 3, MEDIUM: 2, LOW: 1, FREQUENT: 3, OCCASIONAL: 2, RARE: 1,
}
const CC_GAMP_DETECT = { 5: 'LOW', 4: 'MEDIUM', 3: 'HIGH' }
const CC_ACTIVE_PHASES = new Set([
  'Plan', 'Requirements', 'Risk', 'Design', 'Verify',
])
const GXP_COLORS = {
  'GxP Direct':   { text: '#ef4444', bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.3)'   },
  'GxP Indirect': { text: '#f59e0b', bg: 'rgba(245,158,11,0.12)',  border: 'rgba(245,158,11,0.3)'  },
  'Non-GxP':      { text: '#6b7280', bg: 'rgba(107,114,128,0.12)', border: 'rgba(107,114,128,0.3)' },
}
const CC_FLAG_COLORS = {
  high:    { text: '#ef4444', bg: 'rgba(239,68,68,0.1)',   icon: '⚠' },
  warning: { text: '#f59e0b', bg: 'rgba(245,158,11,0.1)',  icon: '⚡' },
  none:    { text: '#6b7280', bg: 'rgba(107,114,128,0.1)', icon: '✓' },
}
const RISK_COLORS = { High: '#ef4444', Medium: '#f59e0b', Low: '#32CD32' }
const RISK_BG = {
  High:   'rgba(239,68,68,0.12)',
  Medium: 'rgba(245,158,11,0.12)',
  Low:    'rgba(50,205,50,0.12)',
}

const GXP_QUESTIONS = [
  { id: 'q1', group: 'GxP Status',
    text: 'Does this system directly generate, process, or store data used for GxP regulatory decisions?',
    hint: 'e.g. batch release, QC lab results, clinical trial data, product quality records' },
  { id: 'q2', group: 'GxP Status',
    text: 'Does a failure in this system have a direct impact on patient safety or product quality?',
    hint: 'e.g. dosing calculations, sterility testing, adverse event reporting' },
  { id: 'q3', group: 'GxP Status',
    text: 'Does it support GxP processes but not directly produce GxP records?',
    hint: 'e.g. change management, ITSM, training tracking, document storage' },
  { id: 'q4', group: 'GAMP Category',
    text: 'Is this commercially available off-the-shelf (COTS) software, configured but not custom-coded?',
    hint: 'e.g. SAP, ServiceNow, Veeva Vault — vendor-supplied, configured for your processes' },
  { id: 'q5', group: 'GAMP Category',
    text: 'Was this system custom-developed or does it contain significant bespoke code?',
    hint: 'e.g. in-house built applications, heavily customised platforms with custom modules' },
  { id: 'q6', group: 'GAMP Category',
    text: 'Is this infrastructure or platform software?',
    hint: 'e.g. operating systems, middleware, database servers, virtualisation platforms' },
]

function classifyFromAnswers(answers) {
  let gxpStatus = 'Non-GxP'
  if (answers.q1 || answers.q2)  gxpStatus = 'GxP Direct'
  else if (answers.q3)           gxpStatus = 'GxP Indirect'
  let gampCategory = 4
  if (answers.q6)      gampCategory = 3
  else if (answers.q5) gampCategory = 5
  else if (answers.q4) gampCategory = 4
  return { gxpStatus, gampCategory }
}

function ccBuildSystemContext(system) {
  if (!system) return null
  const isNonGxP  = system.gxpStatus === 'Non-GxP'
  const isDirect  = system.gxpStatus === 'GxP Direct'
  const inActive  = CC_ACTIVE_PHASES.has(system.phase)
  const validated = system.phase === 'Released' || system.phase === 'Monitor'
  let revalidationFlag = null
  if (isNonGxP) {
    revalidationFlag = {
      level: 'none',
      message: 'Non-GxP system — validation not required for this change',
    }
  } else if (inActive) {
    revalidationFlag = {
      level: 'warning',
      message: `Change during active ${system.phase} phase — impact assessment required`,
    }
  } else if (validated) {
    revalidationFlag = {
      level: 'high',
      message: `Validated system in ${system.phase} — revalidation scope must be determined`,
    }
  }
  return {
    id: system.id, name: system.name, gxpStatus: system.gxpStatus,
    gampCategory: system.gampCategory, phase: system.phase,
    site: system.site, regulations: system.regulations,
    notes: system.notes, isNonGxP, isDirect, revalidationFlag,
  }
}

function ccLocalRisk(cr_id, system_criticality, change_type, system) {
  const ctx = ccBuildSystemContext(system)
  if (ctx?.isNonGxP) {
    const hash = btoa(`${cr_id}:LOW:1`).slice(0, 16).replace(/[+/=]/g, 'x')
    return {
      status: 'assessed', cr_id, timestamp: new Date().toISOString(),
      risk_assessment: {
        severity: 'LOW',
        occurrence: CC_OCC_MAP[change_type?.toLowerCase()] ?? 'OCCASIONAL',
        detectability: 'HIGH', rpn: 1, risk_level: 'Low',
        testing_strategy: 'No validation required — Non-GxP system',
        patient_safety_override: false,
      },
      _reasoning_hash: hash, _offline: true, _system_context: ctx,
    }
  }
  const severity     = CC_SEV_MAP[system_criticality?.toLowerCase()] ?? 'MEDIUM'
  const occurrence   = CC_OCC_MAP[change_type?.toLowerCase()]        ?? 'OCCASIONAL'
  const detectability = system
    ? (CC_GAMP_DETECT[system.gampCategory] ?? 'MEDIUM')
    : 'MEDIUM'
  const rpn = CC_SCALE[severity] * CC_SCALE[occurrence] * CC_SCALE[detectability]
  const patient_safety_override = severity === 'HIGH' && (ctx?.isDirect ?? true)
  const risk_level =
    patient_safety_override || rpn > 12 ? 'High'
    : rpn >= 5                          ? 'Medium' : 'Low'
  const testing_strategy =
    risk_level === 'High'
      ? (system?.gampCategory === 5
          ? 'Rigorous Scripted Testing — OQ + UAT required (GAMP Cat 5)'
          : 'Rigorous Scripted Testing')
      : risk_level === 'Medium'
        ? 'Hybrid Testing (Scripted + Unscripted)'
        : 'Unscripted Testing'
  const hash = btoa(`${cr_id}:${severity}:${occurrence}:${rpn}`)
    .slice(0, 16).replace(/[+/=]/g, 'x')
  return {
    status: 'assessed', cr_id, timestamp: new Date().toISOString(),
    risk_assessment: {
      severity, occurrence, detectability, rpn,
      risk_level, testing_strategy, patient_safety_override,
    },
    _reasoning_hash: hash, _offline: true, _system_context: ctx,
  }
}

function GxPClassifier({ systemName, onClassified }) {
  const [answers, setAnswers] = useState({})
  const toggle        = (id, val) => setAnswers(a => ({ ...a, [id]: val }))
  const answeredAll   = GXP_QUESTIONS.every(q => answers[q.id] !== undefined)
  const classification = answeredAll ? classifyFromAnswers(answers) : null
  const groups        = [...new Set(GXP_QUESTIONS.map(q => q.group))]

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-xl p-4 space-y-4"
    >
      <div className="flex items-center gap-2">
        <span className="text-base">🔍</span>
        <div>
          <p className="text-white text-[11px] font-semibold">
            GxP Classification Questionnaire
          </p>
          <p className="text-text-muted text-[9px]">
            Answer 6 questions — EVOLV determines GxP status and GAMP category
          </p>
        </div>
      </div>
      {groups.map((group, gi) => (
        <div key={group} className="space-y-2">
          <p className="text-[9px] text-text-muted uppercase tracking-wider
                         border-b border-border-base pb-1">{group}</p>
          {GXP_QUESTIONS.filter(q => q.group === group).map((q, i) => (
            <div key={q.id}
              className={`rounded-lg p-3 border transition-all
                ${answers[q.id] !== undefined
                  ? answers[q.id]
                    ? 'border-blue-DEFAULT/40 bg-blue-dim'
                    : 'border-border-base bg-bg-base'
                  : 'border-border-base'}`}>
              <p className="text-[11px] text-text-primary mb-0.5 leading-snug">
                <span className="text-text-muted mr-1.5 font-mono">
                  {gi === 0 ? i + 1 : i + 4}.
                </span>
                {q.text}
              </p>
              <p className="text-[9px] text-text-muted mb-2">{q.hint}</p>
              <div className="flex gap-2">
                {[
                  { val: true,  label: 'Yes', col: '#007FFF' },
                  { val: false, label: 'No',  col: '#6b7280' },
                ].map(opt => (
                  <button key={String(opt.val)}
                    onClick={() => toggle(q.id, opt.val)}
                    className={`px-3 py-1 rounded-lg text-[10px] font-semibold
                      border transition-all
                      ${answers[q.id] === opt.val
                        ? 'text-white'
                        : 'text-text-muted border-border-base hover:text-text-secondary'}`}
                    style={answers[q.id] === opt.val
                      ? { backgroundColor: opt.col, borderColor: opt.col } : {}}>
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
      <AnimatePresence>
        {classification && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            className="rounded-xl p-4 space-y-3"
            style={{
              backgroundColor: GXP_COLORS[classification.gxpStatus]?.bg,
              border: `1px solid ${GXP_COLORS[classification.gxpStatus]?.border}`,
            }}>
            <p className="text-[10px] text-text-muted uppercase tracking-wider">
              Classification Result
            </p>
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold"
                style={{ color: GXP_COLORS[classification.gxpStatus]?.text }}>
                {classification.gxpStatus}
              </span>
              <span className="text-text-muted">·</span>
              <span className="text-purple-400 text-sm font-bold">
                GAMP Category {classification.gampCategory}
              </span>
              <span className="text-text-muted">·</span>
              <span className="text-[10px] text-text-muted">
                Detectability: {CC_GAMP_DETECT[classification.gampCategory]}
              </span>
            </div>
            <p className="text-[9px] text-text-muted">
              {classification.gxpStatus === 'GxP Direct'
                ? 'Validation required. All changes must follow GAMP 5 change control procedure.'
                : classification.gxpStatus === 'GxP Indirect'
                  ? 'Abbreviated validation may apply. Change control documentation required.'
                  : 'No validation required. Standard IT change management applies.'}
            </p>
            <button
              onClick={() => onClassified(systemName, classification)}
              className="w-full flex items-center justify-center gap-2
                         py-2 rounded-lg text-xs font-semibold
                         bg-blue-DEFAULT text-white hover:brightness-110
                         transition-all shadow-[0_0_12px_rgba(0,127,255,0.3)]">
              ＋ Add "{systemName || 'New System'}" to EVOLV Portfolio
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function buildAuditFeed(cr_id, data, t0, hash, ctx) {
  const ra   = data.risk_assessment
  const feed = [{
    event: 'CHANGE_REQUEST_RECEIVED', time: t0,
    detail: `CR ${cr_id} received — system: ${ctx?.name ?? 'unknown'}`,
    color: '#007FFF',
  }]
  if (ctx) feed.push({
    event: 'PORTFOLIO_LOOKUP_COMPLETED', time: new Date().toISOString(),
    detail:
      `${ctx.name} | ${ctx.gxpStatus} | GAMP Cat ${ctx.gampCategory} | Phase: ${ctx.phase}`,
    color: '#a78bfa',
  })
  feed.push({
    event: 'RISK_ASSESSMENT_COMPLETED', time: new Date().toISOString(),
    detail: `Risk: ${ra?.risk_level} | RPN: ${ra?.rpn} | Hash: ${hash}`,
    color: '#32CD32',
  })
  return feed
}

// ── Sprint 36 — CIA viewer ──────────────────────────────────────────
//
// Renders an AI-drafted Change Impact Assessment inline below the
// CR form. Shows summary + affected URs (with risk before/after) +
// affected FRs + affected bundles + invalidated approvals + the
// full reasoning chain. The Sign CCR button on the bottom is the
// human-signature gate per bounded-autonomy principle.

function CIAViewer({ cia, ccr, onOpenCcrModal }) {
  return (
    <div
      className="rounded-xl border p-5 space-y-4 animate-fade-in"
      style={{
        background:  'rgba(0,127,255,0.04)',
        borderColor: 'rgba(0,127,255,0.25)',
      }}
    >
      <div className="flex items-start gap-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center
                     shrink-0 text-lg"
          style={{
            background: 'rgba(0,127,255,0.12)',
            border:     '1px solid rgba(0,127,255,0.30)',
          }}
        >
          📋
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-sm font-bold text-text-primary">
              {cia.cia_id}
            </span>
            <span className="text-[9px] px-1.5 py-0.5 rounded-full border
                             font-semibold"
              style={{
                background:  'rgba(168,85,247,0.12)',
                color:       '#a855f7',
                borderColor: 'rgba(168,85,247,0.30)',
              }}
            >
              AI-DRAFTED
            </span>
            <span className="text-[10px] text-text-muted">
              for {cia.cr_id}
            </span>
          </div>
          <p className="text-[12px] text-text-secondary leading-relaxed">
            {cia.summary}
          </p>
        </div>
      </div>

      {/* Affected URs */}
      {cia.affected_urs?.length > 0 && (
        <div className="space-y-2">
          <p className="text-[9px] uppercase tracking-wider
                        text-text-muted font-semibold">
            Affected User Requirements ({cia.affected_urs.length})
          </p>
          <div className="space-y-1.5">
            {cia.affected_urs.map(ur => (
              <div
                key={ur.requirement_id}
                className="px-3 py-2 rounded border border-border-base
                           bg-bg-card text-[11px]"
              >
                <div className="flex items-center gap-2 mb-1">
                  <code className="font-mono font-semibold
                                   text-text-primary">
                    {ur.requirement_id}
                  </code>
                  {ur.risk_before && (
                    <span className="text-[10px] text-text-muted">
                      risk: <strong className="text-text-secondary">
                        {ur.risk_before}
                      </strong>
                      {ur.risk_after && ur.risk_after !== ur.risk_before
                        && (
                          <>
                            {' → '}
                            <strong>{ur.risk_after}</strong>
                          </>
                        )}
                    </span>
                  )}
                </div>
                <p className="text-text-secondary line-clamp-2 mb-1">
                  {ur.statement}
                </p>
                <p className="text-[10px] text-text-muted italic">
                  {ur.reason}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Affected FRs */}
      {cia.affected_frs?.length > 0 && (
        <div className="space-y-2">
          <p className="text-[9px] uppercase tracking-wider
                        text-text-muted font-semibold">
            Downstream FRs ({cia.affected_frs.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {cia.affected_frs.map(fr => (
              <span
                key={fr.requirement_id}
                className="text-[10px] font-mono px-2 py-0.5 rounded
                           border border-border-base bg-bg-card
                           text-text-secondary"
                title={fr.reason}
              >
                {fr.requirement_id} · via {fr.parent_id}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Affected Bundles */}
      {cia.affected_bundles?.length > 0 && (
        <div className="space-y-2">
          <p className="text-[9px] uppercase tracking-wider
                        text-text-muted font-semibold">
            Test Bundles Requiring Revalidation
            ({cia.affected_bundles.length})
          </p>
          <div className="space-y-1.5">
            {cia.affected_bundles.map(b => (
              <div
                key={b.bundle_id}
                className="px-3 py-2 rounded border text-[11px]"
                style={{
                  background:  'rgba(245,158,11,0.08)',
                  borderColor: 'rgba(245,158,11,0.30)',
                }}
              >
                <div className="flex items-center gap-2">
                  <code className="font-mono font-semibold text-amber-500">
                    {b.bundle_id}
                  </code>
                  <span className="text-[10px] text-text-muted">
                    covers {b.requirement_id}
                  </span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded-full
                                   ml-auto font-semibold"
                    style={{
                      background:  'rgba(245,158,11,0.15)',
                      color:       '#f59e0b',
                    }}
                  >
                    ↻ NEEDS REVAL
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Invalidated Approvals */}
      {cia.invalidated_approvals?.length > 0 && (
        <div className="space-y-2">
          <p className="text-[9px] uppercase tracking-wider
                        text-text-muted font-semibold">
            Prior Approvals Requiring Re-attestation
            ({cia.invalidated_approvals.length})
          </p>
          <div className="space-y-1">
            {cia.invalidated_approvals.map((a, i) => (
              <div
                key={i}
                className="px-3 py-1.5 rounded border border-border-base
                           bg-bg-card text-[11px] flex items-center gap-2"
              >
                <span className="text-text-primary font-semibold">
                  {a.approver_name}
                </span>
                <span className="text-text-muted">
                  · {a.role}
                </span>
                <span className="text-[10px] text-text-muted ml-auto">
                  signed {a.signed_at?.slice(0, 10)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reasoning chain */}
      <details className="text-[11px]">
        <summary className="text-text-muted cursor-pointer
                            hover:text-text-secondary transition-colors
                            text-[10px] uppercase tracking-wider font-semibold">
          AI Reasoning Chain (Logic Archive preview)
        </summary>
        <ol className="mt-2 ml-4 space-y-1 list-decimal
                       text-text-secondary leading-relaxed">
          {cia.reasoning_chain?.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ol>
      </details>

      {/* CCR action bar */}
      <div className="pt-3 border-t border-border-base
                      flex items-center gap-3">
        <p className="text-[10px] text-text-muted leading-relaxed
                      flex-1">
          <strong>This is a draft proposal.</strong> No records have
          been modified; no revalidation has been triggered. The
          Change Control Record (CCR) below is the human signature
          that authorises (or rejects) action.
        </p>
        {ccr ? (
          <div className="rounded-lg px-3 py-2 border text-[11px]"
            style={{
              background:  'rgba(50,205,50,0.10)',
              borderColor: 'rgba(50,205,50,0.30)',
              color:       '#32CD32',
            }}
          >
            <div className="font-semibold">✓ CCR Signed</div>
            <div className="text-[9px] opacity-80">
              {ccr.signer_name} · {ccr.decision.replace(/_/g, ' ')}
            </div>
          </div>
        ) : (
          <button
            onClick={onOpenCcrModal}
            className="px-4 py-2 rounded-lg text-xs font-semibold
                       text-white shadow-sm transition-opacity
                       hover:opacity-90"
            style={{
              background:
                'linear-gradient(90deg, #007FFF, #32CD32)',
            }}
          >
            ✍ Sign Change Control Record
          </button>
        )}
      </div>
    </div>
  )
}

// ── Sprint 36 — CCR sign modal ──────────────────────────────────────

function CCRSignModal({
  cia, defaultSigner, onCancel, onSubmit, submitting, error,
}) {
  const [signerName, setSignerName] = useState(defaultSigner ?? '')
  const [role,       setRole]       = useState('QA Director')
  const [meaning,    setMeaning]    =
    useState('Approval of Change Impact Assessment')
  // No default decision — user must consciously pick per the
  // Sprint 36 design call we agreed.
  const [decision,   setDecision]   = useState('')

  const canSubmit = (
    signerName.trim().length > 0
    && decision.length > 0
    && !submitting
  )

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center
                    bg-black/40 backdrop-blur-sm"
         onClick={onCancel}>
      <div
        className="w-[560px] max-w-full bg-bg-card border
                   border-border-base rounded-xl shadow-2xl p-6
                   space-y-4"
        onClick={e => e.stopPropagation()}
      >
        <div>
          <h3 className="text-base font-semibold text-text-primary">
            Sign Change Control Record
          </h3>
          <p className="text-[11px] text-text-muted mt-0.5">
            21 CFR Part 11 §11.50 — qualified electronic signature.
            Your signature authorises (or rejects) action against{' '}
            <code className="font-mono text-text-secondary">
              {cia.cia_id}
            </code>.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 text-[11px]">
          <label className="block">
            <span className="text-text-muted text-[10px]
                             uppercase tracking-wider font-semibold">
              Signer Name
            </span>
            <input
              value={signerName}
              onChange={e => setSignerName(e.target.value)}
              placeholder="e.g. Sarah Chen"
              className="evolv-input mt-1 w-full"
            />
          </label>
          <label className="block">
            <span className="text-text-muted text-[10px]
                             uppercase tracking-wider font-semibold">
              Role
            </span>
            <input
              value={role}
              onChange={e => setRole(e.target.value)}
              className="evolv-input mt-1 w-full"
            />
          </label>
          <label className="block col-span-2">
            <span className="text-text-muted text-[10px]
                             uppercase tracking-wider font-semibold">
              Meaning of Signature
            </span>
            <input
              value={meaning}
              onChange={e => setMeaning(e.target.value)}
              className="evolv-input mt-1 w-full"
            />
          </label>
        </div>

        <div>
          <p className="text-[10px] uppercase tracking-wider
                        text-text-muted font-semibold mb-2">
            Decision <span className="text-red-500">*</span>
          </p>
          <div className="space-y-1.5">
            {[
              {
                value: 'approve_revalidation',
                label: 'Approve — trigger revalidation',
                desc:
                  'Authorises revalidation sub-run on affected '
                  + 'bundles. (Sprint 37 spawns the sub-run; '
                  + 'today the signed CCR is the gate.)',
                color: '#32CD32',
              },
              {
                value: 'approve_no_revalidation',
                label: 'Approve — no revalidation needed',
                desc:
                  'Authorises the change without revalidation. '
                  + 'Use when the AI flagged URs but QA judges no '
                  + 'material effect.',
                color: '#007FFF',
              },
              {
                value: 'reject',
                label: 'Reject the change',
                desc:
                  'CR is not authorised. No revalidation; no '
                  + 'records modified.',
                color: '#ef4444',
              },
            ].map(opt => {
              const active = decision === opt.value
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setDecision(opt.value)}
                  className={`w-full text-left px-3 py-2 rounded-lg
                              border transition-all`}
                  style={{
                    borderColor: active
                      ? opt.color
                      : 'var(--border-base)',
                    background: active
                      ? `${opt.color}14`
                      : 'transparent',
                  }}
                >
                  <p className="text-[11px] font-semibold"
                     style={{ color: active ? opt.color
                                            : 'var(--text-primary)' }}>
                    {opt.label}
                  </p>
                  <p className="text-[10px] text-text-muted mt-0.5">
                    {opt.desc}
                  </p>
                </button>
              )
            })}
          </div>
        </div>

        {error && (
          <div className="px-3 py-2 rounded border border-red-500/30
                          bg-red-500/10 text-[11px] text-red-400">
            {error}
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-1">
          <button
            onClick={onCancel}
            disabled={submitting}
            className="px-3 py-1.5 text-xs rounded border
                       border-border-base text-text-muted
                       hover:text-text-secondary transition-colors
                       disabled:opacity-40"
          >
            Cancel
          </button>
          <button
            onClick={() => onSubmit({
              signerName: signerName.trim(),
              role:       role.trim(),
              meaning:    meaning.trim(),
              decision,
            })}
            disabled={!canSubmit}
            className="px-4 py-1.5 text-xs rounded font-semibold
                       text-white shadow-sm transition-opacity
                       hover:opacity-90 disabled:opacity-40
                       disabled:cursor-not-allowed"
            style={{
              background:
                'linear-gradient(90deg, #007FFF, #32CD32)',
            }}
          >
            {submitting ? 'Signing…' : '✍ Apply Electronic Signature'}
          </button>
        </div>
      </div>
    </div>
  )
}


export default function ChangeControlTab() {
  const customSystems   = useAppStore(s => s.customSystems)
  const addCustomSystem = useAppStore(s => s.addCustomSystem)

  // Sprint 35.5 (F3 fix): pull the active project from the store so
  // we can stitch it into the dropdown ahead of the static SYSTEMS
  // demo registry. Without this, a CR posted from Monitor lands on a
  // hardcoded fictional portfolio item and the user's real project
  // is invisible to change control — the bug we want to kill.
  const planData         = useAppStore(s => s.planData)
  const riskData         = useAppStore(s => s.riskData)
  const requirements     = useAppStore(s => s.requirements)
  const phaseCompletion  = useAppStore(s => s.phaseCompletion)
  const releaseData      = useAppStore(s => s.releaseData)

  // Sprint 36 — Change Impact Assessment. AI proposes, human signs,
  // revalidation runs. The store actions live in useAppStore.
  const testBundles      = useAppStore(s => s.testBundles)
  const changeRecords    = useAppStore(s => s.changeRecords)
  const addChangeRecord  = useAppStore(s => s.addChangeRecord)
  const attachCIA        = useAppStore(s => s.attachCIA)
  const signCCRAction    = useAppStore(s => s.signCCR)
  const userProfile      = useAppStore(s => s.userProfile)

  const activeProject = useMemo(
    () => buildActiveProjectSystem(
      planData, riskData, requirements, phaseCompletion, releaseData,
    ),
    [planData, riskData, requirements, phaseCompletion, releaseData],
  )

  const allSystems = useMemo(
    () => activeProject
      ? [activeProject, ...SYSTEMS, ...customSystems]
      : [...SYSTEMS, ...customSystems],
    [activeProject, customSystems],
  )

  const [form, setForm] = useState({
    cr_id: '', description: '',
    system_criticality: 'high', change_type: 'normal',
    // Pre-select the active project so the user lands on "this CR
    // targets my project" instead of "— Unknown —".
    system_name: activeProject?.name ?? '',
  })

  // Keep the dropdown in sync if the user renames the project in Plan
  // while this tab is mounted. Only auto-fill if the user hasn't
  // explicitly picked a different system, so we don't stomp on a
  // demo-portfolio selection.
  useEffect(() => {
    if (!activeProject) return
    setForm(f => {
      const isOnDemoPortfolio = !!SYSTEMS.find(s => s.name === f.system_name)
      const isAlreadyOnProject = f.system_name === activeProject.name
      if (isOnDemoPortfolio || isAlreadyOnProject) return f
      return { ...f, system_name: activeProject.name }
    })
  }, [activeProject])
  const [loading,        setLoading]        = useState(false)
  const [result,         setResult]         = useState(null)
  const [apiOnline,      setApiOnline]      = useState(null)
  const [auditFeed,      setAuditFeed]      = useState([])
  const [activeScen,     setActiveScen]     = useState(null)
  const [showClassifier, setShowClassifier] = useState(false)
  const [newSysName,     setNewSysName]     = useState('')

  // Sprint 36 — CIA generation + CCR signing state
  const [ciaLoading,     setCiaLoading]     = useState(false)
  const [ciaError,       setCiaError]       = useState('')
  const [ccrModalOpen,   setCcrModalOpen]   = useState(false)
  const [ccrSubmitting,  setCcrSubmitting]  = useState(false)
  const [ccrError,       setCcrError]       = useState('')

  const matchedSystem = allSystems.find(s => s.name === form.system_name) ?? null

  const applyScenario = useCallback(scen => {
    setActiveScen(scen.label)
    setResult(null); setAuditFeed([]); setShowClassifier(false)
    setForm({
      cr_id: scen.cr_id, description: scen.description,
      system_criticality: scen.system_criticality,
      change_type: scen.change_type, system_name: scen.system_name ?? '',
    })
  }, [])

  const handleClassified = useCallback((name, classification) => {
    const newSystem = {
      id: `SYS-USR-${Date.now()}`,
      name: name || 'New System',
      gampCategory: classification.gampCategory,
      gxpStatus:    classification.gxpStatus,
      site: 'User-defined', phase: 'Plan',
      risk: classification.gxpStatus === 'GxP Direct' ? 'High' : 'Low',
      owner: 'Unassigned',
      lastAction: new Date().toISOString().slice(0, 10),
      dueDate: null,
      regulations:
        classification.gxpStatus !== 'Non-GxP' ? ['21 CFR Part 11'] : [],
      notes: 'Classified via GxP Questionnaire — validation not yet started.',
    }
    addCustomSystem(newSystem)
    setForm(f => ({ ...f, system_name: newSystem.name }))
    setShowClassifier(false)
  }, [addCustomSystem])

  const submit = useCallback(async () => {
    if (!form.cr_id || !form.description) return
    setLoading(true); setResult(null); setAuditFeed([])
    const t0  = new Date().toISOString()
    const ctx = ccBuildSystemContext(matchedSystem)
    try {
      const res = await fetch(`${CC_API}/webhook/sn-change`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cr_id: form.cr_id, description: form.description,
          system_criticality: form.system_criticality,
          change_type: form.change_type,
        }),
        signal: AbortSignal.timeout(5000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setApiOnline(true)
      setResult({ ...data, _offline: false, _system_context: ctx })
      const hash = data._reasoning_hash ?? btoa(form.cr_id).slice(0, 16)
      setAuditFeed(buildAuditFeed(form.cr_id, data, t0, hash, ctx))
    } catch {
      setApiOnline(false)
      const fb = ccLocalRisk(
        form.cr_id, form.system_criticality, form.change_type, matchedSystem,
      )
      setResult(fb)
      setAuditFeed(buildAuditFeed(form.cr_id, fb, t0, fb._reasoning_hash, ctx))
    } finally {
      setLoading(false)
    }
  }, [form, matchedSystem])

  const ra   = result?.risk_assessment
  const rlvl = ra?.risk_level
  const rCol = RISK_COLORS[rlvl] ?? '#888'
  const rBg  = RISK_BG[rlvl]    ?? 'rgba(128,128,128,0.1)'

  // ── Sprint 36 — Change Impact Assessment handlers ───────────────
  //
  // Active record lookup: if a CR has been submitted, we look it up
  // in the store by cr_id to find its current state (received,
  // cia_generated, ccr_signed). This is what powers the CIA viewer
  // and Sign CCR button below.
  const activeRecord = form.cr_id
    ? changeRecords[form.cr_id]
    : null
  const hasCia       = !!activeRecord?.cia
  const hasCcr       = !!activeRecord?.ccr

  // Only allow CIA generation when the active project is selected.
  // CRs against demo-portfolio entries don't have real project data
  // to assess against; that's a sales-demo signal, not a workflow.
  const ciaEligible = (
    !!activeProject
    && form.system_name === activeProject.name
    && !!form.cr_id
    && !!form.description
  )

  const handleGenerateCIA = useCallback(async () => {
    if (!ciaEligible) return
    setCiaLoading(true)
    setCiaError('')

    // Optimistic store add — the row appears in changeRecords as
    // soon as the user clicks; the CIA attaches when the backend
    // returns.
    addChangeRecord(form.cr_id, {
      cr_text:      form.description,
      project_name: activeProject.name,
    })

    try {
      const res = await fetch(`${CC_API}/change-control/cia`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cr_id:        form.cr_id,
          cr_text:      form.description,
          project_name: activeProject.name,
          requirements: requirements ?? [],
          risk_data:    riskData      ?? {},
          test_bundles: testBundles   ?? {},
          approvals:    releaseData?.approvals ?? [],
          user_id:      userProfile?.name ?? 'demo',
        }),
        signal: AbortSignal.timeout(15000),
      })
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(
          errBody.detail ?? `HTTP ${res.status}`,
        )
      }
      const cia = await res.json()
      attachCIA(form.cr_id, cia)
    } catch (e) {
      setCiaError(
        `CIA generation failed: ${e.message ?? e}. `
        + 'Ensure FastAPI is running on port 8000.',
      )
    } finally {
      setCiaLoading(false)
    }
  }, [
    ciaEligible, form.cr_id, form.description,
    activeProject, requirements, riskData, testBundles,
    releaseData, userProfile, addChangeRecord, attachCIA,
  ])

  const handleSignCCR = useCallback(async ({
    signerName, role, meaning, decision,
  }) => {
    if (!activeRecord?.cia) return
    setCcrSubmitting(true)
    setCcrError('')
    try {
      const res = await fetch(`${CC_API}/change-control/ccr`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cia_id:      activeRecord.cia.cia_id,
          cr_id:       activeRecord.cr_id,
          signer_name: signerName,
          role,
          meaning,
          decision,
          user_id:     userProfile?.name ?? 'demo',
        }),
        signal: AbortSignal.timeout(10000),
      })
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(
          errBody.detail ?? `HTTP ${res.status}`,
        )
      }
      const ccr = await res.json()
      signCCRAction(activeRecord.cr_id, ccr)
      setCcrModalOpen(false)
    } catch (e) {
      setCcrError(
        `CCR sign-off failed: ${e.message ?? e}. `
        + 'Ensure FastAPI is running on port 8000.',
      )
    } finally {
      setCcrSubmitting(false)
    }
  }, [activeRecord, signCCRAction, userProfile])

  return (
    <div className="space-y-5 overflow-y-auto h-full pr-1">

      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-white font-semibold text-sm flex items-center gap-2 mb-1">
            🔄 Change Control
            <span className="text-[9px] px-1.5 py-0.5 rounded border font-medium"
              style={{ color: '#32CD32', borderColor: 'rgba(50,205,50,0.3)',
                       backgroundColor: 'rgba(50,205,50,0.1)' }}>
              ServiceNow Webhook
            </span>
          </h2>
          <p className="text-text-secondary text-xs">
            Submit a Change Request — EVOLV cross-references the GAMP 5 system
            registry, assesses risk, and logs a 21 CFR Part 11 audit record.
          </p>
          {/* Sprint 35.5 (F3 fix): tell the user up-front which project
              this CR will target. Sprint 36 will replace this with a
              "Generate Impact Assessment" call-to-action. */}
          {activeProject && (
            <p className="text-[10px] mt-1.5 px-2 py-1 rounded inline-block"
              style={{
                background: 'rgba(0,127,255,0.08)',
                border:     '1px solid rgba(0,127,255,0.25)',
                color:      '#007FFF',
              }}
            >
              ★ Active project pre-selected:
              {' '}
              <span className="font-semibold">{activeProject.name}</span>
              {' · '}
              {activeProject.phase}
              {' · '}
              {activeProject.gxpStatus}
            </p>
          )}
        </div>
        {apiOnline !== null && (
          <span className={`text-[10px] px-2 py-1 rounded-lg border shrink-0 ml-4
            ${apiOnline
              ? 'text-lime-DEFAULT border-lime-DEFAULT/30 bg-lime-dim'
              : 'text-amber-400 border-amber-400/30 bg-amber-400/10'}`}>
            {apiOnline ? '● API Live' : '⚡ Offline Mode'}
          </span>
        )}
      </div>

      {/* Scenarios */}
      <div>
        <p className="text-text-muted text-[10px] mb-2 uppercase tracking-wider">
          Quick-fire scenarios
        </p>
        <div className="grid grid-cols-4 gap-2">
          {SN_SCENARIOS.map(s => (
            <button key={s.label} onClick={() => applyScenario(s)}
              className={`p-3 rounded-xl border text-left transition-all
                ${activeScen === s.label
                  ? 'bg-bg-hover' : 'hover:bg-bg-hover border-border-base'}`}
              style={activeScen === s.label
                ? { borderColor: s.color + '60',
                    boxShadow: `0 0 16px ${s.color}22` } : {}}>
              <div className="text-xl mb-1.5">{s.icon}</div>
              <p className="text-white text-[11px] font-semibold leading-tight">
                {s.label}
              </p>
              <p className="text-text-muted text-[9px] mt-0.5">
                {s.change_type} · {s.system_criticality}
              </p>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-5">

        {/* Form */}
        <div className="glass rounded-xl p-5 space-y-4">
          <p className="text-text-muted text-[10px] uppercase tracking-wider">
            Change Request
          </p>

          <div>
            <label className="text-[10px] text-text-muted block mb-1">
              System
              <span className="ml-1.5 text-[9px] text-blue-DEFAULT">
                ↗ cross-references EVOLV Portfolio
              </span>
            </label>
            <select value={form.system_name}
              onChange={e => setForm(f => ({ ...f, system_name: e.target.value }))}
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors">
              <option value="">— Unknown / Not in EVOLV registry —</option>
              {/* Sprint 35.5 (F3 fix): pin the active project at the
                  top of the list in its own optgroup so it's
                  unmistakable. The demo portfolio (SYSTEMS) is for
                  story-mode; the active project is what a real CR
                  will target. */}
              {activeProject && (
                <optgroup label="★ Your active project">
                  <option value={activeProject.name}>
                    {activeProject.name} ({activeProject.gxpStatus},
                    {' '}Cat {activeProject.gampCategory},
                    {' '}{activeProject.phase})
                  </option>
                </optgroup>
              )}
              <optgroup label="Demo portfolio + classified systems">
                {allSystems
                  .filter(s => s.id !== 'PROJ-ACTIVE')
                  .map(s => (
                    <option key={s.id} value={s.name}>
                      {s.name} ({s.gxpStatus}, Cat {s.gampCategory})
                    </option>
                  ))
                }
              </optgroup>
            </select>
            {matchedSystem && (
              <div className="mt-2 rounded-lg px-3 py-2 flex items-center gap-3
                              animate-fade-in text-[10px]"
                style={{
                  backgroundColor: GXP_COLORS[matchedSystem.gxpStatus]?.bg,
                  border: `1px solid ${GXP_COLORS[matchedSystem.gxpStatus]?.border}`,
                }}>
                <span className="font-semibold shrink-0"
                  style={{ color: GXP_COLORS[matchedSystem.gxpStatus]?.text }}>
                  {matchedSystem.gxpStatus}
                </span>
                <span className="text-text-muted">·</span>
                <span className="text-text-secondary">
                  GAMP Cat {matchedSystem.gampCategory}
                </span>
                <span className="text-text-muted">·</span>
                <span className="text-text-secondary">{matchedSystem.phase}</span>
                <span className="text-text-muted">·</span>
                <span className="text-text-muted truncate">{matchedSystem.site}</span>
              </div>
            )}
            {!matchedSystem && form.system_name === '' && (
              <div className="mt-2 rounded-lg px-3 py-2 flex items-center
                              justify-between gap-3 animate-fade-in
                              bg-amber-400/10 border border-amber-400/30">
                <div>
                  <p className="text-[10px] text-amber-400 font-semibold">
                    ⚠ System not in EVOLV registry
                  </p>
                  <p className="text-[9px] text-text-muted">
                    GxP classification unknown — risk assessment will be limited
                  </p>
                </div>
                <button
                  onClick={() => { setShowClassifier(p => !p); setNewSysName('') }}
                  className="shrink-0 text-[10px] px-3 py-1.5 rounded-lg
                             border border-amber-400/40 text-amber-400
                             hover:bg-amber-400/10 transition-all font-semibold
                             whitespace-nowrap">
                  {showClassifier ? '✕ Cancel' : '🔍 Classify System'}
                </button>
              </div>
            )}
          </div>

          <AnimatePresence>
            {showClassifier && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                style={{ overflow: 'hidden' }}>
                <div className="mb-3">
                  <label className="text-[10px] text-text-muted block mb-1">
                    System name to register
                  </label>
                  <input value={newSysName}
                    onChange={e => setNewSysName(e.target.value)}
                    placeholder="e.g. Chromatography Data System"
                    className="w-full bg-bg-base border border-border-base rounded-lg
                               px-3 py-2 text-xs text-text-primary outline-none
                               focus:border-border-blue transition-colors" />
                </div>
                <GxPClassifier systemName={newSysName} onClassified={handleClassified} />
              </motion.div>
            )}
          </AnimatePresence>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-text-muted block mb-1">CR ID</label>
              <input value={form.cr_id}
                onChange={e => setForm(f => ({ ...f, cr_id: e.target.value }))}
                placeholder="CR-2024-0001"
                className="w-full bg-bg-base border border-border-base rounded-lg
                           px-3 py-2 text-xs font-mono text-text-primary outline-none
                           focus:border-border-blue transition-colors" />
            </div>
            <div>
              <label className="text-[10px] text-text-muted block mb-1">
                System Criticality
              </label>
              <select value={form.system_criticality}
                onChange={e =>
                  setForm(f => ({ ...f, system_criticality: e.target.value }))
                }
                className="w-full bg-bg-base border border-border-base rounded-lg
                           px-3 py-2 text-xs text-text-primary outline-none
                           focus:border-border-blue transition-colors">
                {['critical', 'high', 'medium', 'low', 'minor'].map(v => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-[10px] text-text-muted block mb-1">Description</label>
            <textarea value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              rows={3} placeholder="Describe the change…"
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors resize-none" />
          </div>

          <div>
            <label className="text-[10px] text-text-muted block mb-1">Change Type</label>
            <div className="grid grid-cols-4 gap-1.5">
              {['emergency', 'normal', 'standard', 'routine'].map(v => (
                <button key={v}
                  onClick={() => setForm(f => ({ ...f, change_type: v }))}
                  className={`py-1.5 rounded-lg text-[10px] font-medium border
                    transition-all capitalize
                    ${form.change_type === v
                      ? 'border-blue-DEFAULT bg-blue-dim text-blue-DEFAULT'
                      : 'border-border-base text-text-muted hover:text-text-secondary'}`}>
                  {v}
                </button>
              ))}
            </div>
          </div>

          <button onClick={submit}
            disabled={loading || !form.cr_id}
            className="w-full flex items-center justify-center gap-2
                       px-4 py-3 rounded-xl text-sm font-bold
                       bg-blue-DEFAULT text-white hover:brightness-110
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all shadow-[0_0_24px_rgba(0,127,255,0.35)]">
            {loading
              ? <><span className="animate-spin">⏳</span> Assessing…</>
              : '⚡ Submit to EVOLV'}
          </button>

          {/* Sprint 36 — Change Impact Assessment button. Visible only
              when the active project is selected and a CR has been
              entered. The button generates a CIA via the agent +
              renders the viewer below. AI proposes; the user signs
              the CCR before any action propagates. */}
          {ciaEligible && !hasCia && (
            <button
              onClick={handleGenerateCIA}
              disabled={ciaLoading}
              className="w-full mt-2 flex items-center justify-center
                         gap-2 px-4 py-2.5 rounded-xl text-xs font-bold
                         text-white shadow-sm transition-opacity
                         hover:opacity-90 disabled:opacity-50
                         disabled:cursor-not-allowed"
              style={{
                background:
                  'linear-gradient(90deg, #007FFF, #32CD32)',
              }}
            >
              {ciaLoading
                ? <><span className="animate-spin">🧠</span>{' '}
                    Generating Change Impact Assessment…</>
                : '🧠 Generate Change Impact Assessment (AI)'}
            </button>
          )}
          {ciaError && (
            <p className="text-red-400 text-[10px] mt-1">
              {ciaError}
            </p>
          )}
          {apiOnline === false && (
            <p className="text-amber-400 text-[10px] text-center">
              ⚠ API server offline — showing deterministic fallback
            </p>
          )}
        </div>

        {/* Response */}
        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div key="result"
                initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.22 }}
                className="glass rounded-xl p-5 space-y-4">
                {result._system_context && (
                  <div className="rounded-xl p-3 space-y-2 animate-fade-in"
                    style={{
                      backgroundColor:
                        GXP_COLORS[result._system_context.gxpStatus]?.bg,
                      border: `1px solid ${GXP_COLORS[result._system_context.gxpStatus]?.border}`,
                    }}>
                    <div className="flex items-center justify-between">
                      <p className="text-white text-[11px] font-semibold">
                        {result._system_context.name}
                      </p>
                      <span className="text-[9px] font-mono text-text-muted">
                        {result._system_context.id}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {[
                        { label: result._system_context.gxpStatus,
                          col: GXP_COLORS[result._system_context.gxpStatus]?.text },
                        { label: `GAMP Cat ${result._system_context.gampCategory}`,
                          col: '#a78bfa' },
                        { label: result._system_context.phase, col: '#007FFF' },
                        { label: result._system_context.site, col: '#6b7280' },
                      ].map(b => (
                        <span key={b.label}
                          className="text-[9px] px-1.5 py-0.5 rounded font-medium"
                          style={{ color: b.col, backgroundColor: b.col + '18',
                                   border: `1px solid ${b.col}30` }}>
                          {b.label}
                        </span>
                      ))}
                    </div>
                    {result._system_context.revalidationFlag && (
                      <div className="rounded-lg px-2 py-1.5 flex items-start gap-1.5"
                        style={{
                          backgroundColor:
                            CC_FLAG_COLORS[result._system_context.revalidationFlag.level]?.bg,
                        }}>
                        <span className="shrink-0 text-[10px]">
                          {CC_FLAG_COLORS[result._system_context.revalidationFlag.level]?.icon}
                        </span>
                        <p className="text-[9px] leading-relaxed"
                          style={{
                            color:
                              CC_FLAG_COLORS[result._system_context.revalidationFlag.level]?.text,
                          }}>
                          {result._system_context.revalidationFlag.message}
                        </p>
                      </div>
                    )}
                    <p className="text-[9px] text-text-muted italic">
                      {result._system_context.notes}
                    </p>
                  </div>
                )}
                <div className="rounded-xl p-4 flex flex-col items-center gap-1"
                  style={{ backgroundColor: rBg, border: `1px solid ${rCol}40` }}>
                  <p className="text-[10px] text-text-muted uppercase tracking-widest">
                    Risk Level
                  </p>
                  <p className="text-4xl font-black tracking-wider"
                    style={{ color: rCol, textShadow: `0 0 24px ${rCol}88` }}>
                    {rlvl?.toUpperCase()}
                  </p>
                  <p className="text-[10px] font-mono" style={{ color: rCol + 'cc' }}>
                    {ra?.testing_strategy}
                  </p>
                  {ra?.patient_safety_override && (
                    <span className="mt-1 text-[9px] px-2 py-0.5 rounded-full
                                     bg-red-500/20 border border-red-500/40
                                     text-red-400 font-semibold">
                      ⚠ PATIENT SAFETY OVERRIDE
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-4 gap-2">
                  {[
                    { label: 'Severity',      val: ra?.severity },
                    { label: 'Occurrence',    val: ra?.occurrence },
                    { label: 'Detectability', val: ra?.detectability },
                    { label: 'RPN', val: ra?.rpn, highlight: true, col: rCol },
                  ].map(item => (
                    <div key={item.label} className="rounded-lg p-2 text-center"
                      style={item.highlight
                        ? { backgroundColor: rBg, border: `1px solid ${rCol}40` }
                        : { backgroundColor: 'rgba(255,255,255,0.04)',
                            border: '1px solid rgba(255,255,255,0.08)' }}>
                      <p className="text-[9px] text-text-muted">{item.label}</p>
                      <p className="text-sm font-bold mt-0.5"
                        style={{ color: item.highlight ? item.col : 'var(--text-primary)' }}>
                        {item.val}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="text-[9px] text-text-muted font-mono text-right">
                  {result.cr_id} · {result.timestamp?.slice(0, 19).replace('T', ' ')}
                </div>
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="glass rounded-xl p-8 flex flex-col items-center
                           justify-center gap-3 min-h-[200px]">
                <p className="text-4xl">🔄</p>
                <p className="text-text-muted text-xs text-center">
                  Select a scenario and click<br />
                  <span className="text-blue-DEFAULT">Submit to EVOLV</span>
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Sprint 36 — CIA viewer renders when the active project's
              CR has had its CIA generated. Lives right below the risk
              result so the visual flow reads as: CR → risk → AI-drafted
              impact assessment → human signs CCR. */}
          {hasCia && (
            <CIAViewer
              cia={activeRecord.cia}
              ccr={activeRecord.ccr}
              onOpenCcrModal={() => {
                setCcrError('')
                setCcrModalOpen(true)
              }}
            />
          )}

          <AnimatePresence>
            {auditFeed.length > 0 && (
              <motion.div key="audit"
                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="glass rounded-xl p-4 space-y-2">
                <p className="text-[10px] text-text-muted uppercase tracking-wider
                              flex items-center gap-1.5 mb-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-lime-DEFAULT
                                   animate-pulse-lime inline-block" />
                  21 CFR Part 11 Audit Trail
                </p>
                {auditFeed.map((ev, i) => (
                  <motion.div key={ev.event}
                    initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.18 }}
                    className="flex gap-3 items-start">
                    <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0"
                      style={{ backgroundColor: ev.color }} />
                    <div className="min-w-0">
                      <p className="text-[10px] font-semibold font-mono"
                        style={{ color: ev.color }}>{ev.event}</p>
                      <p className="text-[9px] text-text-muted truncate">{ev.detail}</p>
                      <p className="text-[9px] text-text-muted/60 font-mono">
                        {ev.time?.slice(0, 19).replace('T', ' ')} UTC
                      </p>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <div className="glass rounded-xl p-4 grid grid-cols-4 gap-4 text-center">
        {[
          { icon: '📥', label: 'Webhook Receiver',
            desc: 'POST /webhook/sn-change accepts ServiceNow CR payload' },
          { icon: '🗂️', label: 'Portfolio Cross-Reference',
            desc: 'EVOLV looks up GxP status + GAMP category — context ServiceNow lacks' },
          { icon: '⚖️', label: 'GAMP 5 Risk Engine',
            desc: 'Severity × Occurrence × Detectability (by GAMP cat) → RPN → Risk Level' },
          { icon: '📋', label: '21 CFR Part 11 Log',
            desc: 'Tamper-evident audit trail with SHA-256 reasoning hash' },
        ].map(item => (
          <div key={item.label} className="space-y-1">
            <p className="text-2xl">{item.icon}</p>
            <p className="text-white text-[11px] font-semibold">{item.label}</p>
            <p className="text-text-muted text-[10px] leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>

      {/* Sprint 36 — CCR Sign modal. Lives at the root of the
          ChangeControlTab so it can overlay the entire surface
          rather than being constrained by the response panel. */}
      {ccrModalOpen && activeRecord?.cia && (
        <CCRSignModal
          cia={activeRecord.cia}
          defaultSigner={userProfile?.name ?? ''}
          submitting={ccrSubmitting}
          error={ccrError}
          onCancel={() => setCcrModalOpen(false)}
          onSubmit={handleSignCCR}
        />
      )}
    </div>
  )
}
