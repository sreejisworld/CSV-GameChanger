/**
 * ImpactAnalytics — Impact Analytics module.
 *
 * Contains the "Legacy vs. EVOLV" Comparison Report:
 *  - Two-column table: Legacy Pains vs The EVOLV Solution
 *  - Green glow for EVOLV column, muted gray for Legacy column
 *  - CSS user-select: none + faint "EVOLV Proprietary" watermark
 */
import { useState } from 'react'

// ── Comparison data ────────────────────────────────────────────

const CATEGORIES = [
  {
    category: 'Requirement Generation',
    legacy: {
      tool:  'Veeva / Kneat / SAP',
      pain:  'Manual Word docs. No regulatory traceability. '
             + 'Requirements written from memory — no GAMP 5 context. '
             + '2–4 weeks per URS. High re-work at audit.',
    },
    evolv: {
      headline: 'AI-Generated in Seconds',
      solution: 'RequirementArchitect pulls live GAMP 5 / CSA guidance from '
                + 'Pinecone. Every URS is Pinecone-verified, criticality-classified, '
                + 'and audit-ready on first generation.',
    },
  },
  {
    category: 'Regulatory Verification',
    legacy: {
      tool:  'Manual SME Review',
      pain:  'Subject-matter experts manually cross-check requirements against '
             + 'printed GAMP 5 binders. Error-prone, inconsistent across sites. '
             + 'Compliance exceptions discovered at inspection.',
    },
    evolv: {
      headline: 'Automated 3-Point Verification',
      solution: 'VerificationAgent runs Criticality Alignment, Rationale Relevance, '
                + 'and Contradiction Scan against GAMP 5 text before any URS leaves '
                + 'the system. Zero manual review required for Tier 1 checks.',
    },
  },
  {
    category: 'Test Script Generation',
    legacy: {
      tool:  'Kneat / Excel Templates',
      pain:  'Protocol writers copy-paste from previous projects. '
             + 'Positive-only test coverage. No formal CSA risk stratification. '
             + 'UAT scripts written after OQ — misaligned acceptance criteria.',
    },
    evolv: {
      headline: 'CSA-Aligned Test Scripts',
      solution: 'DeltaAgent generates Informal, Formal OQ, and Formal UAT scripts '
                + 'per CSA risk level — positive, negative, and edge-case steps. '
                + 'Acceptance criteria auto-derived from FR statements.',
    },
  },
  {
    category: 'Audit Trail & 21 CFR Part 11',
    legacy: {
      tool:  'SAP GRC / Manual Logs',
      pain:  'Fragmented audit trail across SharePoint, paper binders, and SAP. '
             + 'No AI reasoning transparency. Cannot demonstrate "who decided what '
             + 'and why" to FDA inspector in real-time.',
    },
    evolv: {
      headline: 'Immutable + AI-Transparent',
      solution: 'IntegrityManager writes SHA-256 hashed CSV rows + Logic Archive '
                + 'JSON for every AI decision. Full ALCOA+ compliance. FDA inspector '
                + 'can query any decision chain within 30 seconds.',
    },
  },
  {
    category: 'Change Impact Assessment',
    legacy: {
      tool:  'Veeva Vault Change Control',
      pain:  'Change impact assessed by a single SME with no cross-system '
             + 'visibility. Blast radius unknown until post-implementation audit. '
             + 'Average change cycle: 6–12 weeks.',
    },
    evolv: {
      headline: 'Blast Radius in Real-Time',
      solution: 'SentinelImpactAgent maps every linked requirement, test script, '
                + 'and validation document in <5 seconds. Shadow Links propagate '
                + 'impact across the full GAMP 5 lifecycle tree automatically.',
    },
  },
  {
    category: 'Reporting & Compliance Export',
    legacy: {
      tool:  'SAP Crystal Reports / Excel',
      pain:  'Validation reports assembled manually. Signature pages printed, '
             + 'wet-signed, scanned. No tamper-evidence. Inspection-readiness '
             + 'preparation: 2–3 days minimum.',
    },
    evolv: {
      headline: '1-Click Validation Report PDF',
      solution: 'generate_validation_report_pdf() produces a 5-page IQ/OQ/PQ-ready '
                + 'PDF with Manifestation of Signature (21 CFR Part 11 § 11.50) in '
                + 'under 3 seconds. Fully audit-trailed.',
    },
  },
  {
    category: 'System Integration',
    legacy: {
      tool:  'Custom ETL / Manual Imports',
      pain:  'Data silos between ServiceNow, SAP, Veeva, and validation tools. '
             + 'Bi-weekly sync cycles. Change requests arrive in validation systems '
             + '3–5 days after creation.',
    },
    evolv: {
      headline: 'EVOLV Connect — Native Webhooks',
      solution: 'ServiceNow CRs assessed in <2 seconds via native webhook. '
                + 'EVOLV Connect pre-built for SAP S/4HANA, Salesforce Health Cloud, '
                + 'and Veeva Vault. Real-time, bidirectional, HMAC-signed.',
    },
  },
  {
    category: 'Total Cost of Validation',
    legacy: {
      tool:  'Traditional CSV Approach',
      pain:  'Industry average: $500K–$2M per validation project. '
             + '60–80% of cost in documentation labour. '
             + 'Typical system: 18–24 months to validated state.',
    },
    evolv: {
      headline: '80% Reduction in Validation Labour',
      solution: 'EVOLV automates URS, UR/FR, test scripts, verification, and '
                + 'reporting. Average time-to-validated-state: 6–8 weeks. '
                + 'Documentation labour cost: reduced by 70–85% per project.',
    },
  },
]

// ── Metric cards ───────────────────────────────────────────────

const METRICS = [
  { label: 'Avg. URS Generation Time',   legacy: '2–4 weeks',    evolv: '< 30 sec',   icon: '⏱' },
  { label: 'Test Script Coverage',       legacy: 'Positive only', evolv: 'Full CSA',   icon: '🧪' },
  { label: 'Inspection Readiness',       legacy: '2–3 days prep', evolv: 'Real-time',  icon: '🛡️' },
  { label: 'Regulatory Findings at Audit', legacy: 'High risk',   evolv: 'Near-zero',  icon: '⚖️' },
]

// ── Component ──────────────────────────────────────────────────

export default function ImpactAnalytics() {
  const [activeReport, setActiveReport] = useState('comparison')

  return (
    <div className="h-full overflow-y-auto bg-bg-base">
      <div className="max-w-6xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-white font-bold text-xl">Impact Analytics</h1>
            <span className="ai-badge text-[10px]">EVOLV Intelligence</span>
          </div>
          <p className="text-text-secondary text-sm">
            Quantified impact of EVOLV vs. legacy validation toolchains.
          </p>
          <div className="neon-sep mt-3" />
        </div>

        {/* Report tabs */}
        <div className="flex gap-2 mb-6">
          {[
            { id: 'comparison', label: '⚔️ Legacy vs. EVOLV' },
            { id: 'metrics',    label: '📊 Key Metrics' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveReport(tab.id)}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition-colors
                ${activeReport === tab.id
                  ? 'bg-lime-DEFAULT text-bg-base'
                  : 'glass text-text-muted hover:text-text-secondary'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeReport === 'metrics' && <MetricsView />}
        {activeReport === 'comparison' && <ComparisonReport />}

      </div>
    </div>
  )
}

// ── Metrics view ───────────────────────────────────────────────

function MetricsView() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {METRICS.map(m => (
          <div key={m.label} className="glass rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl">{m.icon}</span>
              <p className="text-text-secondary text-xs font-medium">{m.label}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl p-3 bg-bg-hover text-center">
                <p className="text-[9px] text-text-muted mb-1 uppercase tracking-wider">
                  Legacy
                </p>
                <p className="text-sm font-bold text-text-muted">{m.legacy}</p>
              </div>
              <div className="rounded-xl p-3 text-center"
                   style={{ background: 'rgba(50,205,50,0.08)',
                            boxShadow: '0 0 12px rgba(50,205,50,0.15)' }}>
                <p className="text-[9px] text-lime-DEFAULT/70 mb-1 uppercase tracking-wider">
                  EVOLV
                </p>
                <p className="text-sm font-bold text-lime-DEFAULT">{m.evolv}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      <WatermarkFooter />
    </div>
  )
}

// ── Comparison report ──────────────────────────────────────────

function ComparisonReport() {
  return (
    <div>
      {/* Column header */}
      <div className="grid grid-cols-[1fr_1fr_1fr] gap-0 mb-2 sticky top-0 z-10">
        <div className="px-5 py-2">
          <p className="text-text-muted text-[10px] font-semibold uppercase tracking-wider">
            Category
          </p>
        </div>
        <div className="px-5 py-3 rounded-t-xl"
             style={{ background: 'rgba(255,255,255,0.03)' }}>
          <p className="text-text-muted text-[10px] font-semibold uppercase tracking-wider">
            Legacy Tools (Veeva / Kneat / SAP)
          </p>
        </div>
        <div className="px-5 py-3 rounded-t-xl"
             style={{ background: 'rgba(50,205,50,0.08)',
                      boxShadow: '0 0 20px rgba(50,205,50,0.15)' }}>
          <p className="text-lime-DEFAULT text-[10px] font-semibold uppercase tracking-wider">
            ⚡ The EVOLV Solution
          </p>
        </div>
      </div>

      {/* Rows */}
      <div
        className="rounded-xl overflow-hidden border border-border-base"
        style={{ userSelect: 'none', WebkitUserSelect: 'none' }}
      >
        {CATEGORIES.map((row, i) => (
          <div
            key={row.category}
            className={`grid grid-cols-[1fr_1fr_1fr] gap-0
                        ${i < CATEGORIES.length - 1 ? 'border-b border-border-base' : ''}`}
          >
            {/* Category label */}
            <div className="px-5 py-4 flex items-start"
                 style={{ background: 'rgba(255,255,255,0.02)' }}>
              <p className="text-text-secondary text-xs font-semibold">
                {row.category}
              </p>
            </div>

            {/* Legacy pain */}
            <div className="px-5 py-4 border-l border-border-base">
              <p className="text-[10px] font-mono text-text-muted mb-1.5">
                {row.legacy.tool}
              </p>
              <p className="text-xs text-text-muted leading-relaxed">
                {row.legacy.pain}
              </p>
            </div>

            {/* EVOLV solution */}
            <div className="px-5 py-4 border-l border-lime-DEFAULT/20 relative"
                 style={{ background: 'rgba(50,205,50,0.04)' }}>
              <p className="text-xs font-semibold text-lime-DEFAULT mb-1.5">
                ✓ {row.evolv.headline}
              </p>
              <p className="text-xs text-text-secondary leading-relaxed">
                {row.evolv.solution}
              </p>
            </div>
          </div>
        ))}
      </div>

      <WatermarkFooter />
    </div>
  )
}

function WatermarkFooter() {
  return (
    <div className="mt-6 flex items-center justify-between">
      <p className="text-text-muted text-[10px]"
         style={{ userSelect: 'none', WebkitUserSelect: 'none' }}>
        EVOLV Proprietary &amp; Confidential — WingstarTech Inc. © 2026.
        Unauthorised reproduction prohibited.
      </p>
      <p className="text-text-muted text-[10px]"
         style={{ userSelect: 'none', WebkitUserSelect: 'none' }}>
        Powered by EVOLV | The Validation Factory
      </p>
    </div>
  )
}
