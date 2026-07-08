/**
 * Plan — Lifecycle Phase 1: Validation Planning
 *
 * React-native form (no iframe). Fields:
 *  - Project Name
 *  - GAMP 5 Category (1 / 3 / 4 / 5) with descriptions
 *  - System Description
 *  - Project Scope
 *  - Regulatory Frameworks (checkboxes)
 *  - Validation Master Plan: Upload Template | Create New (inline form)
 */
import { useState, useEffect, useCallback } from 'react'
import { useAppStore }   from '../store/useAppStore.js'
import { useDataBridge } from '../hooks/useDataBridge.js'
import { API_BASE }      from '../config.js'
import { downloadPDF, slugify } from '../utils/downloadPDF.js'

const GAMP_CATEGORIES = [
  {
    value: '1',
    label: 'Category 1 — Infrastructure Software',
    desc:  'OS, DBMS, network software. Verify installation and versioning only.',
  },
  {
    value: '3',
    label: 'Category 3 — Non-Configurable Software',
    desc:  'COTS with fixed functionality. Focus on URS, IQ, and intended-use verification.',
  },
  {
    value: '4',
    label: 'Category 4 — Configurable Software',
    desc:  'eQMS, LIMS, ERP. Full requirements, risk assessment, configuration, OQ/PQ.',
  },
  {
    value: '5',
    label: 'Category 5 — Custom / Bespoke Software',
    desc:  'Full SDLC: design specifications, unit testing, code review, and full V-model.',
  },
]

const FRAMEWORKS = [
  '21 CFR Part 11',
  'EU GMP Annex 11',
  'ISO 13485',
  'ICH Q9',
  'FDA CSA Guidance',
  'GAMP 5 (2nd Ed.)',
]

// ── Project templates (Sprint 35) ───────────────────────────────────
// Deterministic one-click pre-fill for the four most common GxP system
// shapes pharma QA pros validate. Each template seeds projectName as a
// placeholder (user must rename), GAMP category, system description,
// project scope, and the regulatory frameworks that are universally
// expected for that system class. **Zero backend code** — same lesson
// as Sprint 34 (BriefIntake): when the value is in the *form-fill*,
// not the LLM, ship a deterministic UI shell over what's already
// there.
//
// Why these four: they cover ~90% of pharma CSV portfolios. LIMS for
// QC labs, eQMS for document/CAPA, ERP/MES for manufacturing, CTMS
// for clinical operations. A fifth "Custom / Bespoke" entry covers
// the GAMP-5-category-5 case (in-house apps) so the templates strip
// isn't conspicuously missing the Cat-5 path.
const PROJECT_TEMPLATES = [
  {
    id: 'lims',
    icon: '🧪',
    name: 'LIMS Validation',
    blurb: 'Lab Information Management System — sample registration, '
         + 'instrument data capture, batch release.',
    plan: {
      projectName:      'LIMS Validation',
      gampCategory:     '4',
      systemDescription:
        'Cloud-hosted Laboratory Information Management System '
      + 'supporting QC sample receipt, chain-of-custody, instrument '
      + 'data capture (HL7 / ASTM), out-of-spec investigations, and '
      + 'final batch release decisions. The system is GxP-direct and '
      + 'subject to 21 CFR Part 11 electronic signatures on all '
      + 'release-relevant transactions.',
      projectScope:
        'In scope: sample registration, chain-of-custody, instrument '
      + 'integration, OOS investigations, electronic signatures, '
      + 'audit trail, role-based access, batch release approval. '
      + 'Out of scope: ERP / MES interfaces, supplier qualification, '
      + 'shipping/logistics modules.',
      regulatoryFrameworks: [
        '21 CFR Part 11', 'EU GMP Annex 11',
        'GAMP 5 (2nd Ed.)', 'FDA CSA Guidance',
      ],
    },
  },
  {
    id: 'eqms',
    icon: '📋',
    name: 'eQMS Validation',
    blurb: 'electronic Quality Management System — document control, '
         + 'CAPA, deviations, change control.',
    plan: {
      projectName:      'eQMS Validation',
      gampCategory:     '4',
      systemDescription:
        'Configurable electronic Quality Management System covering '
      + 'controlled document lifecycle (SOPs, work instructions), '
      + 'deviation management, CAPA, change control, training '
      + 'records, and supplier quality. Used enterprise-wide by '
      + 'Quality, Manufacturing, and R&D for GxP-regulated activities.',
      projectScope:
        'In scope: document control, deviation/CAPA workflows, '
      + 'change control, training records, supplier scorecards, '
      + 'electronic signatures, audit trail, reporting dashboards. '
      + 'Out of scope: complaint handling (separate QMS module), '
      + 'regulatory submissions, payroll integration.',
      regulatoryFrameworks: [
        '21 CFR Part 11', 'EU GMP Annex 11',
        'ISO 13485', 'GAMP 5 (2nd Ed.)',
      ],
    },
  },
  {
    id: 'erp',
    icon: '🏭',
    name: 'ERP / MES Validation',
    blurb: 'Manufacturing module of an ERP — batch records, materials, '
         + 'work-order genealogy.',
    plan: {
      projectName:      'ERP Manufacturing Module Validation',
      gampCategory:     '4',
      systemDescription:
        'Configurable manufacturing module of an ERP / MES platform '
      + 'covering electronic batch records (EBR), materials management, '
      + 'work-order execution, genealogy, weigh-and-dispense, in-process '
      + 'controls, and finished-goods labelling. GxP-direct — every '
      + 'released lot is reviewed against this system\'s data.',
      projectScope:
        'In scope: master batch record templates, work order execution, '
      + 'electronic batch records, materials management, in-process '
      + 'controls, label generation, e-signatures on lot disposition. '
      + 'Out of scope: financial modules, HR, supply-chain forecasting, '
      + 'CRM, plant-floor SCADA interfaces (validated separately).',
      regulatoryFrameworks: [
        '21 CFR Part 11', 'EU GMP Annex 11',
        'GAMP 5 (2nd Ed.)', 'FDA CSA Guidance',
      ],
    },
  },
  {
    id: 'ctms',
    icon: '🩺',
    name: 'CTMS Validation',
    blurb: 'Clinical Trial Management System — subject enrollment, '
         + 'protocol management, EDC integration.',
    plan: {
      projectName:      'CTMS Validation',
      gampCategory:     '4',
      systemDescription:
        'Cloud-hosted Clinical Trial Management System supporting '
      + 'study planning, site activation, subject enrollment, visit '
      + 'tracking, monitoring reports, deviation management, and EDC '
      + 'integration. Subject to ICH GCP, 21 CFR Part 11, and '
      + 'EMA clinical trial regulations.',
      projectScope:
        'In scope: study build, site management, subject enrollment, '
      + 'visit scheduling, monitoring reports, deviation log, EDC '
      + 'data reconciliation, e-signatures on monitoring visit '
      + 'reports. Out of scope: EDC system itself, IRB/EC submissions, '
      + 'safety database (PV system), payroll for site staff.',
      regulatoryFrameworks: [
        '21 CFR Part 11', 'EU GMP Annex 11',
        'ICH Q9', 'GAMP 5 (2nd Ed.)',
      ],
    },
  },
  {
    id: 'custom',
    icon: '⚙',
    name: 'Custom / Bespoke',
    blurb: 'In-house or custom-developed application — full SDLC, '
         + 'GAMP 5 Category 5 rigour.',
    plan: {
      projectName:      'Custom Application Validation',
      gampCategory:     '5',
      systemDescription:
        'In-house or custom-developed software application built '
      + 'against bespoke specifications. Subject to full GAMP 5 '
      + 'Category 5 lifecycle: detailed design specifications, code '
      + 'review, unit/integration testing, full IQ/OQ/PQ, and '
      + 'enhanced change control across releases.',
      projectScope:
        'In scope: full software development lifecycle, design '
      + 'specifications, code review, unit and integration testing, '
      + 'IQ/OQ/PQ, electronic signatures, audit trail, change '
      + 'control. Out of scope: COTS dependencies (validated under '
      + 'their own GAMP categories), infrastructure (Cat 1).',
      regulatoryFrameworks: [
        '21 CFR Part 11', 'EU GMP Annex 11', 'ISO 13485',
        'ICH Q9', 'FDA CSA Guidance', 'GAMP 5 (2nd Ed.)',
      ],
    },
  },
]


// ── Project Templates strip (Sprint 35) ─────────────────────────────
// Renders as the first section in the form body. Clicking a card
// applies the template's `plan` object via the parent's setPlanData
// setter (one call per field). The strip self-collapses to a single
// "Use a template" link once the user has typed anything into
// projectName so it doesn't squat on the canvas after first use.
function PlanTemplates({ planData, setPlanData, applied, setApplied }) {
  // Strip starts open on a brand-new project (planData seeded blank
  // by FRESH_PROJECT) so cold-start users see the templates first.
  // It collapses itself in two situations: the user types into
  // projectName (their own name beats our templates), or they
  // explicitly apply / skip it.
  const [collapsed, setCollapsed] = useState(
    planData.projectName.trim().length > 0
  )

  // Watcher: if the user types into projectName *after* opening the
  // page (without picking a template), collapse the strip on the
  // next change. Run-once (`!applied`) so re-opening via "Switch
  // template" doesn't immediately re-collapse.
  useEffect(() => {
    if (planData.projectName.trim().length > 0 && !applied) {
      setCollapsed(true)
    }
  }, [planData.projectName, applied])

  const handleApply = tpl => {
    setPlanData('projectName',          tpl.plan.projectName)
    setPlanData('gampCategory',         tpl.plan.gampCategory)
    setPlanData('systemDescription',    tpl.plan.systemDescription)
    setPlanData('projectScope',         tpl.plan.projectScope)
    setPlanData('regulatoryFrameworks', tpl.plan.regulatoryFrameworks)
    setApplied(tpl.id)
    setCollapsed(true)
  }

  if (collapsed) {
    return (
      <div className="rounded-xl border border-border-base bg-bg-card
                      px-4 py-2.5 flex items-center gap-3">
        <span className="text-[11px] text-text-muted">
          {applied
            ? `✓ ${PROJECT_TEMPLATES.find(t => t.id === applied)?.name} `
              + 'template applied — fields below are pre-filled.'
            : 'Want a head start?'}
        </span>
        <button
          onClick={() => setCollapsed(false)}
          className="ml-auto text-[11px] text-blue-DEFAULT hover:underline"
        >
          {applied ? 'Switch template' : 'Use a template'}
        </button>
      </div>
    )
  }

  return (
    <div
      className="rounded-xl border bg-bg-card p-5"
      style={{
        borderColor: 'rgba(0,127,255,0.25)',
        boxShadow: '0 0 0 1px rgba(0,127,255,0.04) inset',
      }}
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="text-blue-DEFAULT text-sm">✨</span>
        <h3 className="text-sm font-semibold text-text-primary">
          Quick start — pick a template
        </h3>
        <span className="text-[11px] text-text-muted hidden md:inline">
          One click pre-fills GAMP category, system description, scope,
          and regulatory frameworks. Edit anything below.
        </span>
        <button
          onClick={() => setCollapsed(true)}
          className="ml-auto text-[11px] text-text-muted hover:text-text-secondary"
          title="Hide templates and start from blank"
        >
          Skip ✕
        </button>
      </div>

      <div
        className="grid gap-2.5"
        style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}
      >
        {PROJECT_TEMPLATES.map(tpl => {
          const isActive = applied === tpl.id
          return (
            <button
              key={tpl.id}
              onClick={() => handleApply(tpl)}
              className={`
                text-left rounded-lg border p-3 transition-all
                ${isActive
                  ? 'border-blue-DEFAULT bg-blue-dim'
                  : 'border-border-base bg-bg-base hover:border-blue-DEFAULT/40 hover:bg-blue-DEFAULT/5'}
              `}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-base">{tpl.icon}</span>
                <span className={`text-xs font-semibold ${
                  isActive ? 'text-blue-DEFAULT' : 'text-text-primary'
                }`}>
                  {tpl.name}
                </span>
                {isActive && (
                  <span className="ml-auto text-[10px] text-blue-DEFAULT">
                    ✓ Applied
                  </span>
                )}
              </div>
              <p className="text-[10px] text-text-muted leading-relaxed">
                {tpl.blurb}
              </p>
              <p className="mt-2 text-[10px] text-text-muted/80">
                <span className="font-semibold text-text-secondary">
                  GAMP {tpl.plan.gampCategory}
                </span>
                {' · '}
                {tpl.plan.regulatoryFrameworks.length} frameworks
              </p>
            </button>
          )
        })}
      </div>
    </div>
  )
}


// ── Reusable field wrapper ──────────────────────────────
function Field({ label, hint, children }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-text-secondary">
        {label}
        {hint && (
          <span className="ml-2 font-normal text-text-muted">{hint}</span>
        )}
      </label>
      {children}
    </div>
  )
}

// ── Section card ────────────────────────────────────────
function Section({ title, children }) {
  return (
    <div className="rounded-xl border border-border-base bg-bg-card p-5 space-y-4">
      <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
      {children}
    </div>
  )
}

export default function Plan() {
  const { planData, setPlanData, setPlanVmp, setPhaseComplete } = useAppStore()
  const { syncNow } = useDataBridge()
  const [showVmpForm, setShowVmpForm] = useState(planData.vmpCreated)
  const [saved,       setSaved]       = useState(false)
  const [syncing,     setSyncing]     = useState(false)
  const [syncMsg,     setSyncMsg]     = useState(null)
  const [vpLoading,   setVpLoading]   = useState(false)
  const [vpError,     setVpError]     = useState('')
  const [vpSigner,    setVpSigner]    = useState('')
  // Sprint 35: which Project Template (if any) was applied. Tracked
  // so the strip can show a "✓ LIMS template applied" pill when
  // collapsed, and so re-applying lights up the active card.
  const [appliedTemplate, setAppliedTemplate] = useState(null)

  const handleSave = () => {
    setPhaseComplete('plan')
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  // ── Validation Plan (VP) export ──────────────────────────
  // Sends the planData slice to /exports/validation-plan,
  // which returns a signed 3-page PDF (Cover + VMP + MoS).
  const handleExportVP = useCallback(async () => {
    setVpLoading(true)
    setVpError('')
    try {
      if (!vpSigner.trim()) {
        throw new Error(
          'Enter a signer name before exporting the VP.'
        )
      }
      const projName = planData.projectName || 'Untitled Project'
      await downloadPDF(
        `${API_BASE}/exports/validation-plan`,
        {
          plan_data:   planData,
          signer_name: vpSigner.trim(),
          meaning:     'Approval of Validation Plan',
        },
        `validation-plan-${slugify(projName)}.pdf`,
      )
    } catch (err) {
      setVpError(
        `${err.message}. Ensure FastAPI is running on port 8000.`
      )
    } finally {
      setVpLoading(false)
    }
  }, [planData, vpSigner])

  const handleSync = async () => {
    setSyncing(true)
    setSyncMsg(null)
    const plan = await syncNow()
    setSyncing(false)
    if (!plan || !plan.projectName) {
      setSyncMsg({ ok: false, text: 'No plan data found in Streamlit.' })
    } else {
      const fields = ['projectName', 'gampCategory', 'systemDescription',
                      'projectScope', 'regulatoryFrameworks']
      let updated = 0
      fields.forEach(k => {
        if (plan[k] !== undefined && plan[k] !== planData[k]) {
          setPlanData(k, plan[k])
          updated++
        }
      })
      setSyncMsg({
        ok:   true,
        text: updated > 0
          ? `Synced ${updated} field${updated > 1 ? 's' : ''} from Streamlit.`
          : 'Already up to date.',
      })
    }
    setTimeout(() => setSyncMsg(null), 4000)
  }

  const toggleFramework = fw => {
    const current = planData.regulatoryFrameworks ?? []
    const next = current.includes(fw)
      ? current.filter(f => f !== fw)
      : [...current, fw]
    setPlanData('regulatoryFrameworks', next)
  }

  return (
    <div className="h-full overflow-y-auto bg-bg-base">
      {/* ── Notice strip ──────────────────────────────────── */}
      <div className="flex items-center gap-3 px-6 py-2.5
                      bg-blue-dim border-b border-blue-DEFAULT/20 shrink-0">
        <span className="text-xs font-semibold text-blue-DEFAULT">
          Validation Planning
        </span>
        <span className="text-text-muted text-xs">
          Define project scope, system description, and Validation Master Plan
        </span>
        <div className="ml-auto flex items-center gap-2">
          {syncMsg && (
            <span className={`text-[11px] ${syncMsg.ok ? 'text-lime-DEFAULT' : 'text-amber-400'}`}>
              {syncMsg.text}
            </span>
          )}
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg border
                       border-blue-DEFAULT/30 bg-blue-DEFAULT/10 text-blue-DEFAULT
                       text-[11px] font-medium hover:bg-blue-DEFAULT/20
                       transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {syncing
              ? <span className="w-3 h-3 rounded-full border border-blue-DEFAULT
                                  border-t-transparent animate-spin" />
              : '↓'}
            {syncing ? 'Syncing…' : 'Sync from Streamlit'}
          </button>
        </div>
      </div>

      {/* ── Form body ─────────────────────────────────────── */}
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">

        {/* Project Templates strip (Sprint 35) — first thing the user
            sees on a brand-new project. Self-collapses once they
            either apply a template or start typing a project name. */}
        <PlanTemplates
          planData={planData}
          setPlanData={setPlanData}
          applied={appliedTemplate}
          setApplied={setAppliedTemplate}
        />

        {/* Project basics */}
        <Section title="Project Details">
          <Field label="Project Name">
            <input
              className="evolv-input"
              placeholder="e.g. LabCore LIMS v4.2 Validation"
              value={planData.projectName}
              onChange={e => setPlanData('projectName', e.target.value)}
            />
          </Field>

          <Field
            label="GAMP 5 Software Category"
            hint="— determines validation depth required"
          >
            <select
              className="evolv-input evolv-select"
              value={planData.gampCategory}
              onChange={e => setPlanData('gampCategory', e.target.value)}
            >
              <option value="">Select category…</option>
              {GAMP_CATEGORIES.map(c => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
            {planData.gampCategory && (
              <p className="text-[11px] text-text-muted mt-1 pl-1">
                {GAMP_CATEGORIES.find(c => c.value === planData.gampCategory)?.desc}
              </p>
            )}
          </Field>

          <Field label="System Description" hint="— per EU GMP Annex 11">
            <textarea
              className="evolv-input"
              rows={3}
              placeholder="Describe the system's purpose, architecture, and intended use…"
              value={planData.systemDescription}
              onChange={e => setPlanData('systemDescription', e.target.value)}
            />
          </Field>

          <Field label="Project Scope">
            <textarea
              className="evolv-input"
              rows={3}
              placeholder="Define what is in and out of scope for this validation project…"
              value={planData.projectScope}
              onChange={e => setPlanData('projectScope', e.target.value)}
            />
          </Field>
        </Section>

        {/* Regulatory frameworks */}
        <Section title="Applicable Regulatory Frameworks">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {FRAMEWORKS.map(fw => {
              const checked = (planData.regulatoryFrameworks ?? []).includes(fw)
              return (
                <label
                  key={fw}
                  onClick={() => toggleFramework(fw)}
                  className={`
                    flex items-center gap-2.5 px-3 py-2 rounded-lg border
                    cursor-pointer text-xs transition-all
                    ${checked
                      ? 'border-blue-DEFAULT/50 bg-blue-dim text-text-primary'
                      : 'border-border-base bg-bg-base text-text-muted hover:border-border-bright'}
                  `}
                >
                  <span
                    className={`
                      w-3.5 h-3.5 rounded border-2 shrink-0 flex items-center
                      justify-center transition-colors
                      ${checked
                        ? 'border-blue-DEFAULT bg-blue-DEFAULT'
                        : 'border-border-bright'}
                    `}
                  >
                    {checked && (
                      <svg width="8" height="6" viewBox="0 0 8 6" fill="none">
                        <path d="M1 3l2 2 4-4" stroke="white"
                              strokeWidth="1.5" strokeLinecap="round"
                              strokeLinejoin="round"/>
                      </svg>
                    )}
                  </span>
                  {fw}
                </label>
              )
            })}
          </div>
        </Section>

        {/* VMP section */}
        <Section title="Validation Master Plan (VMP)">
          <div className="flex items-center gap-3">
            <label
              className="flex items-center gap-2 px-4 py-2 rounded-lg border
                         border-border-base bg-bg-base text-text-secondary text-xs
                         hover:border-border-bright cursor-pointer transition-colors"
            >
              <span>📎</span>
              Upload Template
              <input type="file" accept=".docx,.pdf,.doc" className="hidden"
                onChange={() => setPlanData('vmpCreated', true)} />
            </label>

            <button
              onClick={() => { setShowVmpForm(v => !v); setPlanData('vmpCreated', true) }}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg border text-xs
                transition-colors
                ${showVmpForm
                  ? 'border-blue-DEFAULT bg-blue-dim text-blue-DEFAULT'
                  : 'border-border-base bg-bg-base text-text-secondary hover:border-border-bright'}
              `}
            >
              <span>{showVmpForm ? '▾' : '▸'}</span>
              Create New VMP
            </button>
          </div>

          {showVmpForm && (
            <div className="mt-2 space-y-4 pt-4 border-t border-border-base
                            animate-fade-in">
              <Field label="Validation Strategy">
                <textarea
                  className="evolv-input"
                  rows={3}
                  placeholder="Describe the overall validation approach (risk-based, CSA, lifecycle)…"
                  value={planData.vmpContent.validationStrategy}
                  onChange={e => setPlanVmp('validationStrategy', e.target.value)}
                />
              </Field>
              <Field label="Resources & Responsibilities">
                <textarea
                  className="evolv-input"
                  rows={3}
                  placeholder="List validation team members, their roles, and responsibilities…"
                  value={planData.vmpContent.resourcesResponsibilities}
                  onChange={e => setPlanVmp('resourcesResponsibilities', e.target.value)}
                />
              </Field>
              <Field label="Timeline & Milestones">
                <textarea
                  className="evolv-input"
                  rows={3}
                  placeholder="Key milestones: URS sign-off, IQ, OQ, PQ completion, VSR approval…"
                  value={planData.vmpContent.timeline}
                  onChange={e => setPlanVmp('timeline', e.target.value)}
                />
              </Field>
            </div>
          )}
        </Section>

        {/* Validation Plan PDF export (Sprint 18.2) */}
        <Section title="Export Validation Plan (Signed PDF)">
          <p className="text-[11px] text-text-muted mb-3">
            Generate a 21 CFR Part 11-compliant Validation Plan PDF
            with a Manifestation of Signature page. The PDF includes
            Project Identification, System Description, Scope, VMP
            strategy, and the regulatory frameworks selected above.
          </p>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-1 grow min-w-[220px]">
              <label className="text-[10px] text-text-muted">
                Signer Name (QA / Validation Lead)
              </label>
              <input
                value={vpSigner}
                onChange={e => setVpSigner(e.target.value)}
                placeholder="e.g. Jane Smith"
                className="evolv-input text-xs"
              />
            </div>
            <button
              onClick={handleExportVP}
              disabled={vpLoading || !vpSigner.trim()}
              className={`
                px-4 py-2 rounded-lg text-xs font-medium
                transition-colors
                ${vpLoading || !vpSigner.trim()
                  ? 'bg-bg-card border border-border-base text-text-muted opacity-60 cursor-not-allowed'
                  : 'bg-blue-DEFAULT/10 border border-blue-DEFAULT/40 text-blue-DEFAULT hover:bg-blue-DEFAULT/20'}
              `}
            >
              {vpLoading ? 'Generating…' : '📄 Download VP PDF'}
            </button>
          </div>
          {vpError && (
            <p className="mt-2 text-[11px] text-red-400">
              {vpError}
            </p>
          )}
        </Section>

        {/* Save button */}
        <div className="flex items-center justify-between pt-2">
          <p className="text-[11px] text-text-muted">
            Data is stored locally in the platform session.
          </p>
          <button
            onClick={handleSave}
            className={`
              flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-medium
              transition-all
              ${saved
                ? 'bg-lime-dim border border-lime-DEFAULT/40 text-lime-DEFAULT'
                : 'bg-blue-DEFAULT text-white hover:bg-blue-DEFAULT/90'}
            `}
          >
            {saved ? '✓ Saved' : 'Save & Mark Complete'}
          </button>
        </div>
      </div>
    </div>
  )
}
