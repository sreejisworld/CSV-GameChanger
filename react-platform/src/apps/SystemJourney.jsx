/**
 * SystemJourney — Full lifecycle flow for a single validated system.
 *
 * Shows the complete journey from GAMP 5 classification through
 * every validation phase to retirement, with artifacts produced
 * at each stage and a regulatory compliance trail.
 *
 * Three pre-loaded demo systems at different lifecycle stages
 * answer Karunakar's request: "show entire flow — project →
 * system → validation plan → start to retire."
 */
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// ── GAMP 5 category descriptions ─────────────────────────────────
const GAMP_CATEGORIES = {
  3: { label: 'Category 3', sub: 'Non-Configured COTS',
       color: '#64748b',
       desc: 'Standard off-the-shelf software used as supplied with '
           + 'no site-specific configuration. Validation relies on '
           + 'vendor testing evidence and supplier qualification.' },
  4: { label: 'Category 4', sub: 'Configured COTS',
       color: '#007FFF',
       desc: 'Vendor-supplied platform configured for site-specific '
           + 'use. Validation scope covers the configuration layer. '
           + 'IQ, OQ, and risk-based UAT are typically required.' },
  5: { label: 'Category 5', sub: 'Custom Software',
       color: '#ef4444',
       desc: 'Bespoke or heavily customised application. Highest '
           + 'validation burden. Full lifecycle: URS → design → '
           + 'code review → IQ/OQ/PQ → 21 CFR Part 11 controls.' },
}

// ── Artifact type styling ─────────────────────────────────────────
const ARTIFACT_TYPE = {
  plan:         { color: '#007FFF', bg: 'bg-blue-DEFAULT/10',   border: 'border-blue-DEFAULT/30',   icon: '📋' },
  urs:          { color: '#a855f7', bg: 'bg-purple-500/10',     border: 'border-purple-500/30',     icon: '📄' },
  requirements: { color: '#a855f7', bg: 'bg-purple-500/10',     border: 'border-purple-500/30',     icon: '📋' },
  risk:         { color: '#f59e0b', bg: 'bg-amber-DEFAULT/10',  border: 'border-amber-DEFAULT/30',  icon: '⚖️' },
  design:       { color: '#a855f7', bg: 'bg-purple-500/10',     border: 'border-purple-500/30',     icon: '🎨' },
  test:         { color: '#32CD32', bg: 'bg-lime-DEFAULT/10',   border: 'border-lime-DEFAULT/30',   icon: '🧪' },
  approval:     { color: '#32CD32', bg: 'bg-lime-DEFAULT/10',   border: 'border-lime-DEFAULT/30',   icon: '✅' },
  report:       { color: '#007FFF', bg: 'bg-blue-DEFAULT/10',   border: 'border-blue-DEFAULT/30',   icon: '📊' },
}

// ── Phase status styling ──────────────────────────────────────────
const PHASE_STATUS = {
  complete:    { node: '#32CD32', ring: 'ring-lime-DEFAULT/50',  label: 'Complete',    icon: '✓' },
  in_progress: { node: '#007FFF', ring: 'ring-blue-DEFAULT/50',  label: 'In Progress', icon: '⟳' },
  pending:     { node: '#f59e0b', ring: 'ring-amber-DEFAULT/50', label: 'Pending',     icon: '◷' },
  locked:      { node: '#334155', ring: 'ring-border-base',      label: 'Not Started', icon: '○' },
}

// ── Phase config ──────────────────────────────────────────────────
const PHASES = [
  { id: 'plan',         label: 'Plan',         emoji: '📋' },
  { id: 'requirements', label: 'Requirements', emoji: '📝' },
  { id: 'risk',         label: 'Risk',         emoji: '⚖️' },
  { id: 'design',       label: 'Design',       emoji: '🎨' },
  { id: 'verify',       label: 'Verify',       emoji: '🏭' },
  { id: 'release',      label: 'Release',      emoji: '📄' },
  { id: 'monitor',      label: 'Monitor',      emoji: '📡' },
  { id: 'retire',       label: 'Retire',       emoji: '🔒' },
]

// ── Demo system data ──────────────────────────────────────────────
const DEMO_SYSTEMS = [
  // ── 1. ServiceNow — Cat 4, mid-validation ───────────────────────
  {
    id: 'SYS-002',
    name: 'ServiceNow ITSM Platform',
    version: 'v8.2 Upgrade',
    gampCategory: 4,
    gxpStatus: 'GxP Indirect',
    site: 'Basel, CH',
    owner: 'A. Müller',
    projectStart: '2026-01-06',
    targetRelease: '2026-04-30',
    classificationRationale:
      'ServiceNow is a vendor-supplied ITSM platform (COTS) configured '
      + 'with site-specific change management and CMDB workflows. '
      + 'Classification: Category 4. Validation scope is limited to the '
      + 'configuration layer; core platform is supplier-qualified.',
    regulations: ['21 CFR Part 11', 'GMP Annex 11'],
    phases: {
      plan: {
        status: 'complete', date: '2026-01-15',
        summary:
          'Validation scope defined covering Change Management, Incident, '
          + 'and CMDB modules. Validation Master Plan v1.2 approved by QA Head.',
        stats: [
          { label: 'VMP Version',   value: 'v1.2' },
          { label: 'Team Members',  value: '6' },
          { label: 'Frameworks',    value: '2' },
          { label: 'Duration',      value: '16 weeks' },
        ],
        artifacts: [
          { id: 'VMP-001',   label: 'Validation Master Plan v1.2',  type: 'plan' },
          { id: 'SCOPE-001', label: 'Validation Scope Document',     type: 'plan' },
        ],
        findings: [],
      },
      requirements: {
        status: 'complete', date: '2026-01-31',
        summary:
          '12 URS generated from GAMP 5 knowledge base. All SMART-refined '
          + 'and verified. 0 requirements rejected. UR/FR document produced '
          + 'for each URS with acceptance criteria.',
        stats: [
          { label: 'URS Generated',  value: '12' },
          { label: 'SMART Refined',  value: '12' },
          { label: 'Verified',       value: '12' },
          { label: 'Rejected',       value: '0' },
        ],
        artifacts: [
          { id: 'URS-001', label: 'URS — Change Management',   type: 'urs' },
          { id: 'URS-002', label: 'URS — Incident Module',     type: 'urs' },
          { id: 'URS-003', label: 'URS — CMDB Integration',    type: 'urs' },
          { id: 'URS-004', label: 'URS — Audit Trail Controls',type: 'urs' },
          { id: 'URFR-001',label: 'UR/FR Document (12 reqs)',  type: 'requirements' },
        ],
        findings: [],
      },
      risk: {
        status: 'complete', date: '2026-02-10',
        summary:
          'FMEA risk profiling complete across all 12 UR/FR pairs. '
          + '3 requirements elevated to High due to audit trail controls '
          + 'under 21 CFR Part 11. Scripted OQ/UAT required for High items.',
        stats: [
          { label: 'High Risk',              value: '3' },
          { label: 'Medium Risk',            value: '5' },
          { label: 'Low Risk',               value: '4' },
          { label: 'Patient Safety Override', value: '0' },
        ],
        artifacts: [
          { id: 'RISK-001', label: 'Risk Matrix (FMEA)',       type: 'risk' },
          { id: 'GAP-001',  label: 'Regulatory Gap Analysis',  type: 'risk' },
        ],
        findings: [
          'URS-004 (Audit Trail) elevated to High — 21 CFR Part 11 §11.10 requires tamper-evident audit logs.',
        ],
      },
      design: {
        status: 'complete', date: '2026-02-28',
        summary:
          'System Design Specification approved. Traceability matrix '
          + 'links all 12 URS to design elements. 7 configuration items '
          + 'documented. 0 open issues at design review.',
        stats: [
          { label: 'URS Traced',        value: '12/12' },
          { label: 'Config Items',      value: '7' },
          { label: 'Integration Points',value: '3' },
          { label: 'Open Issues',       value: '0' },
        ],
        artifacts: [
          { id: 'SDS-001',   label: 'System Design Specification', type: 'design' },
          { id: 'TM-001',    label: 'Traceability Matrix',         type: 'design' },
          { id: 'CSPEC-001', label: 'Configuration Specification', type: 'design' },
        ],
        findings: [],
      },
      verify: {
        status: 'in_progress', date: null,
        summary:
          'OQ execution underway. 14 of 18 test scripts completed. '
          + '1 defect open (TS-007 audit timestamp format). '
          + '4 scripts pending execution this week.',
        stats: [
          { label: 'Test Scripts', value: '18' },
          { label: 'Executed',     value: '14' },
          { label: 'Passed',       value: '13' },
          { label: 'Failed',       value: '1' },
        ],
        artifacts: [
          { id: 'TS-001', label: 'Test Script — Audit Trail OQ',    type: 'test' },
          { id: 'TS-002', label: 'Test Script — Change Mgmt UAT',   type: 'test' },
          { id: 'TS-003', label: 'Test Script — Access Control OQ', type: 'test' },
          { id: 'TS-004', label: 'Test Script — CMDB Integration',  type: 'test' },
        ],
        findings: [
          'TS-007 FAILED: Audit log timestamp not in UTC — defect DEF-003 raised.',
          'DEF-003 fix deployed to test environment 2026-03-20 — re-test pending.',
        ],
      },
      release: {
        status: 'pending', date: null,
        summary:
          'Multi-approver sign-off pending resolution of DEF-003. '
          + '1 of 3 approvals received. System Owner and QA Head signatures outstanding.',
        stats: [
          { label: 'Approvals Required', value: '3' },
          { label: 'Signed',             value: '1' },
          { label: 'Pending',            value: '2' },
        ],
        artifacts: [],
        findings: [],
      },
      monitor: {
        status: 'locked', date: null,
        summary: 'Periodic review and change monitoring will commence after formal release.',
        stats: [],
        artifacts: [],
        findings: [],
      },
      retire: {
        status: 'locked', date: null,
        summary: 'Retirement not applicable — system not yet in validated state.',
        stats: [],
        artifacts: [],
        findings: [],
      },
    },
  },

  // ── 2. Veeva Vault QMS — Cat 4, fully validated ─────────────────
  {
    id: 'SYS-004',
    name: 'Veeva Vault QMS',
    version: 'v23.3 → v24.1 Migration',
    gampCategory: 4,
    gxpStatus: 'GxP Direct',
    site: 'Basel, CH',
    owner: 'M. Dubois',
    projectStart: '2025-06-01',
    targetRelease: '2026-01-20',
    classificationRationale:
      'Veeva Vault is a cloud-hosted, configured COTS platform for '
      + 'quality document management. Directly supports GxP processes '
      + '(SOP control, CAPA, deviation management). '
      + 'Classification: Category 4. Full IQ/OQ/UAT required.',
    regulations: ['21 CFR Part 11', 'ISO 13485', 'GMP Annex 11'],
    phases: {
      plan: {
        status: 'complete', date: '2025-06-20',
        summary: 'Validation scope covers QMS, CAPA, Deviation, and Document Control vaults. VMP approved.',
        stats: [
          { label: 'VMP Version',  value: 'v2.0' },
          { label: 'Team Members', value: '8' },
          { label: 'Frameworks',   value: '3' },
          { label: 'Duration',     value: '32 weeks' },
        ],
        artifacts: [
          { id: 'VMP-002', label: 'Validation Master Plan v2.0', type: 'plan' },
          { id: 'SQ-001',  label: 'Supplier Qualification Report', type: 'plan' },
        ],
        findings: [],
      },
      requirements: {
        status: 'complete', date: '2025-07-18',
        summary: '18 URS generated and verified. 3 rejected in first pass — rewritten after SMART refinement.',
        stats: [
          { label: 'URS Generated', value: '18' },
          { label: 'SMART Refined', value: '18' },
          { label: 'Verified',      value: '18' },
          { label: 'Rejected',      value: '3 (rewritten)' },
        ],
        artifacts: [
          { id: 'URS-SYS4-001', label: 'URS — Document Control',   type: 'urs' },
          { id: 'URS-SYS4-002', label: 'URS — CAPA Module',        type: 'urs' },
          { id: 'URS-SYS4-003', label: 'URS — Audit Trail (21 CFR)',type: 'urs' },
          { id: 'URFR-SYS4',   label: 'UR/FR Document (18 reqs)',  type: 'requirements' },
        ],
        findings: [
          '3 URS initially rejected (Contradiction Scan) — "no audit trail" phrase detected. Rewritten.',
        ],
      },
      risk: {
        status: 'complete', date: '2025-08-05',
        summary: 'Full FMEA complete. 5 High risk due to GxP Direct + custom config. Patient safety override applied to 1 requirement.',
        stats: [
          { label: 'High Risk',               value: '5' },
          { label: 'Medium Risk',             value: '8' },
          { label: 'Low Risk',                value: '5' },
          { label: 'Patient Safety Override',  value: '1' },
        ],
        artifacts: [
          { id: 'RISK-SYS4', label: 'Risk Matrix (FMEA)',      type: 'risk' },
          { id: 'GAP-SYS4',  label: 'Regulatory Gap Report',   type: 'risk' },
        ],
        findings: [
          'URS-SYS4-003 triggered patient safety override — Severity forced to HIGH.',
        ],
      },
      design: {
        status: 'complete', date: '2025-09-12',
        summary: 'SDS and HLD approved. All 18 URS fully traced. 14 configuration items documented.',
        stats: [
          { label: 'URS Traced',         value: '18/18' },
          { label: 'Config Items',       value: '14' },
          { label: 'Integration Points', value: '5' },
          { label: 'Open Issues',        value: '0' },
        ],
        artifacts: [
          { id: 'SDS-SYS4',   label: 'System Design Specification', type: 'design' },
          { id: 'HLD-SYS4',   label: 'High-Level Design',           type: 'design' },
          { id: 'TM-SYS4',    label: 'Traceability Matrix',         type: 'design' },
        ],
        findings: [],
      },
      verify: {
        status: 'complete', date: '2025-12-10',
        summary: 'All 26 test scripts passed. 0 open defects. OQ and UAT sign-offs received. Validation Report issued.',
        stats: [
          { label: 'Test Scripts', value: '26' },
          { label: 'Executed',     value: '26' },
          { label: 'Passed',       value: '26' },
          { label: 'Failed',       value: '0' },
        ],
        artifacts: [
          { id: 'TS-SYS4-1', label: '18 Scripted Test Scripts (OQ)', type: 'test' },
          { id: 'TS-SYS4-2', label: '8 UAT Test Scripts',            type: 'test' },
          { id: 'VR-SYS4',   label: 'Validation Report',             type: 'report' },
        ],
        findings: [],
      },
      release: {
        status: 'complete', date: '2026-01-20',
        summary: 'System formally released to production. 3/3 approvals received with 21 CFR Part 11 e-signatures.',
        stats: [
          { label: 'Approvals', value: '3/3' },
          { label: 'Release ID',value: 'REL-2026-004' },
        ],
        artifacts: [
          { id: 'REL-SYS4', label: 'Release Approval Package', type: 'approval' },
          { id: 'CERT-SYS4',label: 'System Release Certificate', type: 'approval' },
        ],
        findings: [],
      },
      monitor: {
        status: 'complete', date: '2026-01-20',
        summary: 'System in validated state. Periodic review scheduled for 2027-01. Change control active.',
        stats: [
          { label: 'Next Review',  value: '2027-01-20' },
          { label: 'Open Changes', value: '0' },
          { label: 'Deviations',   value: '0' },
        ],
        artifacts: [
          { id: 'MON-SYS4', label: 'Ongoing Monitoring Plan', type: 'report' },
        ],
        findings: [],
      },
      retire: {
        status: 'locked', date: null,
        summary: 'System is validated and operational. Retirement not currently planned.',
        stats: [],
        artifacts: [],
        findings: [],
      },
    },
  },

  // ── 3. LabVantage LIMS — Cat 5, early-stage ─────────────────────
  {
    id: 'SYS-003',
    name: 'LabVantage LIMS',
    version: 'v5.8 — New Implementation',
    gampCategory: 5,
    gxpStatus: 'GxP Direct',
    site: 'Frankfurt, DE',
    owner: 'S. Fischer',
    projectStart: '2026-02-01',
    targetRelease: '2026-09-30',
    classificationRationale:
      'LabVantage is a laboratory information management system with '
      + 'significant custom scripting for sample management, CoC tracking, '
      + 'and instrument integration. Directly supports GxP laboratory operations. '
      + 'Classification: Category 5. Full lifecycle validation with code review required.',
    regulations: ['21 CFR Part 11', 'GLP', 'ISO 17025'],
    phases: {
      plan: {
        status: 'complete', date: '2026-02-20',
        summary: 'Validation scope defined. VMP approved. Cross-site team assembled across Frankfurt and Basel labs.',
        stats: [
          { label: 'VMP Version',  value: 'v1.0' },
          { label: 'Team Members', value: '10' },
          { label: 'Frameworks',   value: '3' },
          { label: 'Duration',     value: '34 weeks' },
        ],
        artifacts: [
          { id: 'VMP-003',  label: 'Validation Master Plan v1.0', type: 'plan' },
          { id: 'RISK-003', label: 'Initial Risk Assessment',     type: 'plan' },
        ],
        findings: [],
      },
      requirements: {
        status: 'complete', date: '2026-03-10',
        summary: '22 URS generated covering sample management, CoC, instrument integration, and audit trail. All verified.',
        stats: [
          { label: 'URS Generated', value: '22' },
          { label: 'SMART Refined', value: '22' },
          { label: 'Verified',      value: '20' },
          { label: 'Rejected',      value: '2 (rewriting)' },
        ],
        artifacts: [
          { id: 'URS-003-1', label: 'URS — Sample Management',     type: 'urs' },
          { id: 'URS-003-2', label: 'URS — Chain of Custody',       type: 'urs' },
          { id: 'URS-003-3', label: 'URS — Instrument Integration', type: 'urs' },
          { id: 'URFR-003',  label: 'UR/FR Document (20 reqs)',     type: 'requirements' },
        ],
        findings: [
          '2 URS under revision — Criticality Alignment check flagged possible under-classification.',
        ],
      },
      risk: {
        status: 'in_progress', date: null,
        summary: 'FMEA in progress. 10 of 22 requirements profiled. High risk count expected to be significant for Cat 5 GxP Direct system.',
        stats: [
          { label: 'Profiled',   value: '10/22' },
          { label: 'High Risk',  value: '6' },
          { label: 'Medium Risk',value: '3' },
          { label: 'Low Risk',   value: '1' },
        ],
        artifacts: [
          { id: 'RISK-003-WIP', label: 'Risk Matrix (In Progress)', type: 'risk' },
        ],
        findings: [
          'URS-003-2 (Chain of Custody) likely patient safety override — safety review pending.',
        ],
      },
      design: {
        status: 'locked', date: null,
        summary: 'Design phase will begin after risk profiling is complete.',
        stats: [],
        artifacts: [],
        findings: [],
      },
      verify: {
        status: 'locked', date: null,
        summary: 'Verification phase locked until design is approved.',
        stats: [],
        artifacts: [],
        findings: [],
      },
      release: {
        status: 'locked', date: null,
        summary: 'Release gate not yet reached.',
        stats: [],
        artifacts: [],
        findings: [],
      },
      monitor: {
        status: 'locked', date: null,
        summary: 'Not applicable at this stage.',
        stats: [],
        artifacts: [],
        findings: [],
      },
      retire: {
        status: 'locked', date: null,
        summary: 'Not applicable at this stage.',
        stats: [],
        artifacts: [],
        findings: [],
      },
    },
  },
]

// ── Helper: overall lifecycle progress ───────────────────────────
function getProgress(phases) {
  const all     = PHASES.map(p => phases[p.id]?.status ?? 'locked')
  const done    = all.filter(s => s === 'complete').length
  const active  = all.find(s => s === 'in_progress')
  return { done, total: PHASES.length, hasActive: !!active }
}

// ── Sub-components ────────────────────────────────────────────────
function ArtifactBadge({ artifact }) {
  const t = ARTIFACT_TYPE[artifact.type] ?? ARTIFACT_TYPE.plan
  return (
    <div className={`
      flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs
      border ${t.border} ${t.bg}
    `}>
      <span>{t.icon}</span>
      <span style={{ color: t.color }} className="font-medium">
        {artifact.id}
      </span>
      <span className="text-text-muted truncate max-w-[180px]">
        {artifact.label}
      </span>
    </div>
  )
}

// ── Timeline node ─────────────────────────────────────────────────
function PhaseNode({ phase, phaseData, isSelected, isLast, onClick }) {
  const status  = phaseData?.status ?? 'locked'
  const style   = PHASE_STATUS[status]
  const isPulse = status === 'in_progress'

  return (
    <div className="flex flex-col items-center flex-1 min-w-0">
      {/* Node + connector */}
      <div className="flex items-center w-full">
        {/* Left line */}
        <div className={`flex-1 h-px ${
          isSelected || status === 'complete'
            ? 'bg-lime-DEFAULT/40' : 'bg-border-base'
        }`} />

        {/* Node circle */}
        <button
          onClick={onClick}
          className={`
            relative w-9 h-9 rounded-full border-2 flex items-center
            justify-center shrink-0 z-10 transition-all duration-200
            ${isSelected ? `ring-2 ring-offset-2 ring-offset-bg-base ${style.ring}` : ''}
          `}
          style={{
            borderColor: style.node,
            backgroundColor: status === 'complete'
              ? `${style.node}20`
              : status === 'in_progress'
                ? `${style.node}15`
                : '#0d1b2a',
          }}
        >
          {isPulse && (
            <span
              className="absolute inset-0 rounded-full animate-ping opacity-40"
              style={{ backgroundColor: style.node }}
            />
          )}
          <span className="text-sm relative z-10" style={{ color: style.node }}>
            {status === 'complete' ? '✓' : phase.emoji}
          </span>
        </button>

        {/* Right line — omit after last node */}
        {!isLast && (
          <div className={`flex-1 h-px ${
            status === 'complete' ? 'bg-lime-DEFAULT/40' : 'bg-border-base'
          }`} />
        )}
        {isLast && <div className="flex-1" />}
      </div>

      {/* Label below node */}
      <div className="mt-2 text-center px-0.5">
        <p className={`text-[10px] font-semibold leading-tight ${
          isSelected ? 'text-text-primary' : 'text-text-secondary'
        }`}>
          {phase.label}
        </p>
        {phaseData?.date ? (
          <p className="text-[9px] text-text-muted mt-0.5">
            {phaseData.date}
          </p>
        ) : (
          <p className="text-[9px] mt-0.5" style={{ color: style.node }}>
            {style.label}
          </p>
        )}
      </div>
    </div>
  )
}

// ── Phase detail panel ────────────────────────────────────────────
function PhaseDetail({ phase, phaseData }) {
  const status = phaseData?.status ?? 'locked'
  const style  = PHASE_STATUS[status]

  return (
    <motion.div
      key={phase.id}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: 0.18 }}
      className="glass rounded-xl p-5"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">{phase.emoji}</span>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-text-primary">
              {phase.label} Phase
            </h3>
            <span
              className="text-[10px] px-2 py-0.5 rounded-full border font-semibold"
              style={{
                color:            style.node,
                borderColor:      `${style.node}50`,
                backgroundColor:  `${style.node}10`,
              }}
            >
              {style.label}
            </span>
            {phaseData?.date && (
              <span className="text-[10px] text-text-muted">
                {status === 'complete' ? 'Completed' : 'Started'} {phaseData.date}
              </span>
            )}
          </div>
          <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">
            {phaseData?.summary ?? 'Phase not yet started.'}
          </p>
        </div>
      </div>

      {/* Stats + artifacts row */}
      {(phaseData?.stats?.length > 0 || phaseData?.artifacts?.length > 0) && (
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Stats */}
          {phaseData.stats?.length > 0 && (
            <div>
              <p className="text-[10px] text-text-muted uppercase tracking-widest
                            mb-2 font-semibold">
                Phase Metrics
              </p>
              <div className="grid grid-cols-2 gap-2">
                {phaseData.stats.map(s => (
                  <div key={s.label}
                    className="bg-bg-hover rounded-lg p-2.5 text-center">
                    <p className="text-base font-bold text-text-primary leading-none">
                      {s.value}
                    </p>
                    <p className="text-[10px] text-text-muted mt-0.5">
                      {s.label}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Artifacts */}
          {phaseData.artifacts?.length > 0 && (
            <div>
              <p className="text-[10px] text-text-muted uppercase tracking-widest
                            mb-2 font-semibold">
                Artifacts Produced
              </p>
              <div className="space-y-1.5">
                {phaseData.artifacts.map(a => (
                  <ArtifactBadge key={a.id} artifact={a} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Findings */}
      {phaseData?.findings?.length > 0 && (
        <div>
          <p className="text-[10px] text-text-muted uppercase tracking-widest
                        mb-2 font-semibold">
            Findings / Issues
          </p>
          <div className="space-y-1.5">
            {phaseData.findings.map((f, i) => (
              <div key={i}
                className="flex items-start gap-2 text-xs text-amber-DEFAULT
                           bg-amber-DEFAULT/5 border border-amber-DEFAULT/20
                           rounded-lg px-3 py-2">
                <span className="shrink-0 mt-0.5">⚠</span>
                <span className="leading-relaxed">{f}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {status === 'locked' && (
        <div className="flex items-center gap-2 text-xs text-text-muted
                        bg-bg-hover rounded-lg px-3 py-2 mt-2">
          <span>🔒</span>
          <span>This phase will unlock when the previous phase is complete.</span>
        </div>
      )}
    </motion.div>
  )
}

// ── Main component ────────────────────────────────────────────────
export default function SystemJourney() {
  const [systemIdx,  setSystemIdx]  = useState(0)
  const [activePhase, setActivePhase] = useState('verify')

  const sys       = DEMO_SYSTEMS[systemIdx]
  const gamp      = GAMP_CATEGORIES[sys.gampCategory]
  const progress  = getProgress(sys.phases)
  const phaseData = sys.phases[activePhase]
  const activeP   = PHASES.find(p => p.id === activePhase)

  return (
    <div className="h-full overflow-y-auto bg-bg-base">
      <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col gap-5">

        {/* ── Header ──────────────────────────────────────── */}
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-white">
              System Journey
            </h1>
            <span className="text-[10px] px-2 py-0.5 rounded border
                             border-blue-DEFAULT/30 bg-blue-dim
                             text-blue-DEFAULT font-semibold uppercase tracking-wider">
              Full Lifecycle View
            </span>
          </div>
          <p className="text-text-muted text-xs">
            GAMP 5 classification → validation plan → requirements →
            risk → design → verify → release → monitor → retire
          </p>
          <div className="neon-sep mt-3" />
        </div>

        {/* ── System selector ─────────────────────────────── */}
        <div className="flex gap-2 flex-wrap">
          {DEMO_SYSTEMS.map((s, i) => {
            const p = getProgress(s.phases)
            return (
              <button
                key={s.id}
                onClick={() => {
                  setSystemIdx(i)
                  // Select the first non-locked phase
                  const first = PHASES.find(ph =>
                    s.phases[ph.id]?.status !== 'locked'
                    && s.phases[ph.id]?.status === 'in_progress'
                  ) ?? PHASES.find(ph =>
                    s.phases[ph.id]?.status === 'complete'
                  )
                  if (first) setActivePhase(first.id)
                }}
                className={`
                  flex items-center gap-2 px-3 py-2 rounded-xl
                  border transition-all text-left
                  ${i === systemIdx
                    ? 'border-blue-DEFAULT/50 bg-blue-dim'
                    : 'border-border-base bg-bg-card hover:border-border-bright'}
                `}
              >
                <div className="min-w-0">
                  <p className={`text-xs font-semibold truncate ${
                    i === systemIdx
                      ? 'text-blue-DEFAULT' : 'text-text-secondary'
                  }`}>
                    {s.name}
                  </p>
                  <p className="text-[10px] text-text-muted">
                    {s.version} · Cat {s.gampCategory} · {p.done}/{p.total} phases
                  </p>
                </div>
              </button>
            )
          })}
        </div>

        {/* ── System header card ──────────────────────────── */}
        <div className="glass rounded-xl p-5 flex gap-5">
          {/* GAMP category badge */}
          <div
            className="shrink-0 w-20 h-20 rounded-xl flex flex-col
                       items-center justify-center border text-center"
            style={{
              borderColor:     `${gamp.color}40`,
              backgroundColor: `${gamp.color}10`,
            }}
          >
            <p className="text-2xl font-black" style={{ color: gamp.color }}>
              {sys.gampCategory}
            </p>
            <p className="text-[9px] font-semibold uppercase tracking-wider
                          text-text-muted mt-0.5 leading-tight px-1">
              {gamp.sub}
            </p>
          </div>

          {/* System info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-1">
              <div>
                <h2 className="text-lg font-bold text-white">
                  {sys.name}
                </h2>
                <p className="text-xs text-text-muted">{sys.version}</p>
              </div>
              {/* Progress ring */}
              <div className="shrink-0 text-right">
                <p className="text-2xl font-black text-lime-DEFAULT leading-none">
                  {progress.done}
                  <span className="text-sm text-text-muted font-normal">
                    /{progress.total}
                  </span>
                </p>
                <p className="text-[10px] text-text-muted">phases</p>
              </div>
            </div>

            {/* Classification rationale */}
            <p className="text-[11px] text-text-secondary leading-relaxed mb-3
                          border-l-2 pl-3"
              style={{ borderColor: gamp.color }}>
              {sys.classificationRationale}
            </p>

            {/* Meta row */}
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
              {[
                { label: 'GxP',          value: sys.gxpStatus },
                { label: 'Site',         value: sys.site },
                { label: 'Owner',        value: sys.owner },
                { label: 'Started',      value: sys.projectStart },
                { label: 'Target',       value: sys.targetRelease },
              ].map(({ label, value }) => (
                <span key={label} className="text-text-muted">
                  {label}:{' '}
                  <span className="text-text-secondary font-medium">{value}</span>
                </span>
              ))}
              {sys.regulations.map(r => (
                <span key={r}
                  className="px-1.5 py-0.5 rounded border border-border-base
                             text-[9px] text-text-muted">
                  {r}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Phase timeline ──────────────────────────────── */}
        <div className="glass rounded-xl p-5">
          <p className="text-[10px] text-text-muted uppercase tracking-widest
                        mb-4 font-semibold">
            Validation Lifecycle
          </p>
          <div className="flex items-start">
            {PHASES.map((phase, i) => (
              <PhaseNode
                key={phase.id}
                phase={phase}
                phaseData={sys.phases[phase.id]}
                isSelected={activePhase === phase.id}
                isLast={i === PHASES.length - 1}
                onClick={() => setActivePhase(phase.id)}
              />
            ))}
          </div>
        </div>

        {/* ── Phase detail ─────────────────────────────────── */}
        <AnimatePresence mode="wait">
          {activeP && (
            <PhaseDetail
              key={`${sys.id}-${activePhase}`}
              phase={activeP}
              phaseData={phaseData}
            />
          )}
        </AnimatePresence>

        <p className="text-center text-text-muted text-xs pb-2">
          Powered by EVOLV | WingstarTech Inc. — AI-assisted, human-approved.
        </p>
      </div>
    </div>
  )
}
