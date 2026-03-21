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
import { useState } from 'react'
import { useAppStore }   from '../store/useAppStore.js'
import { useDataBridge } from '../hooks/useDataBridge.js'

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

  const handleSave = () => {
    setPhaseComplete('plan')
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

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
