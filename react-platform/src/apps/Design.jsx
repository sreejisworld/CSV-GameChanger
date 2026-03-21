/**
 * Design — Lifecycle Phase 4: Design Specifications
 *
 * Unlocks when the Risk phase is complete (phaseCompletion.risk).
 * Before that, shows a gate screen with a prompt to complete Risk.
 *
 * Three tabs:
 *  1. Design Spec       — architecture notes, HLD/LLD, integrations,
 *                         diagram link; adapts to GAMP category
 *  2. Traceability      — auto-built URS → UR → FR → Test matrix
 *  3. Config Spec       — configured-item table (all categories)
 */
import { useState, useCallback } from 'react'
import { useAppStore }           from '../store/useAppStore.js'

const GAMP_LABELS = {
  '1': 'Cat 1 — Infrastructure',
  '3': 'Cat 3 — Non-Configured',
  '4': 'Cat 4 — Configured Software',
  '5': 'Cat 5 — Custom / Bespoke',
}

// ── CSV helper ────────────────────────────────────────────────────
function downloadCSV(filename, headers, rows) {
  const escape = v =>
    `"${String(v ?? '').replace(/"/g, '""')}"`
  const lines = [
    headers.join(','),
    ...rows.map(r => headers.map(h => escape(r[h])).join(',')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

// ── Field row ─────────────────────────────────────────────────────
function FieldRow({ label, hint, children }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline gap-2">
        <label className="text-xs font-semibold text-text-secondary">
          {label}
        </label>
        {hint && (
          <span className="text-[10px] text-text-muted">{hint}</span>
        )}
      </div>
      {children}
    </div>
  )
}

// ── Design Spec tab ───────────────────────────────────────────────
function DesignSpecTab({ designData, setDesignField,
                         planData, setPhaseComplete }) {
  const cat  = planData.gampCategory
  const isCat5 = cat === '5'

  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setPhaseComplete('design')
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  return (
    <div className="space-y-6 max-w-3xl">

      {/* GAMP category context */}
      <div className="flex items-center gap-3 px-4 py-2.5 rounded-lg
                      bg-purple-dim border border-purple-DEFAULT/20">
        <span className="text-[10px] font-semibold text-purple-DEFAULT
                         uppercase tracking-wide">
          GAMP 5 Context
        </span>
        <span className="text-xs text-text-secondary">
          {cat
            ? GAMP_LABELS[cat] ?? `Category ${cat}`
            : 'No GAMP category set — configure in Plan'}
        </span>
        {isCat5 && (
          <span className="ml-auto text-[9px] px-2 py-0.5 rounded
                           bg-amber-dim text-amber-DEFAULT
                           border border-amber-DEFAULT/30 font-semibold">
            LLD required for Cat 5
          </span>
        )}
      </div>

      {/* Architecture notes */}
      <FieldRow
        label="System Architecture Notes"
        hint="High-level description of system components and boundaries"
      >
        <textarea
          value={designData.architectureNotes}
          onChange={e => setDesignField('architectureNotes', e.target.value)}
          rows={5}
          placeholder={
            'Describe the system architecture: components, '
            + 'integrations, data flows, and deployment topology…'
          }
          className="evolv-input w-full text-xs px-3 py-2 resize-y
                     leading-relaxed"
        />
      </FieldRow>

      {/* HLD */}
      <FieldRow
        label="High-Level Design (HLD)"
        hint="Functional decomposition, modules, key design decisions"
      >
        <textarea
          value={designData.hldNotes}
          onChange={e => setDesignField('hldNotes', e.target.value)}
          rows={5}
          placeholder={
            'Document the high-level design: major modules, '
            + 'data models, key algorithms, and design patterns…'
          }
          className="evolv-input w-full text-xs px-3 py-2 resize-y
                     leading-relaxed"
        />
      </FieldRow>

      {/* LLD — Cat 5 only */}
      {isCat5 && (
        <FieldRow
          label="Low-Level Design (LLD)"
          hint="Required for GAMP 5 Category 5 — detailed component specs"
        >
          <textarea
            value={designData.lldNotes}
            onChange={e => setDesignField('lldNotes', e.target.value)}
            rows={5}
            placeholder={
              'Detailed design: class diagrams, database schema, '
              + 'API contracts, error handling, and security controls…'
            }
            className="evolv-input w-full text-xs px-3 py-2 resize-y
                       leading-relaxed border-amber-DEFAULT/30"
          />
        </FieldRow>
      )}

      {/* Integration notes */}
      <FieldRow
        label="Interface / Integration Notes"
        hint="External systems, APIs, data formats, and integration points"
      >
        <textarea
          value={designData.integrationNotes}
          onChange={e => setDesignField('integrationNotes', e.target.value)}
          rows={3}
          placeholder={
            'List external interfaces: ERP, LIMS, HL7/ASTM feeds, '
            + 'REST APIs, file exchanges…'
          }
          className="evolv-input w-full text-xs px-3 py-2 resize-y
                     leading-relaxed"
        />
      </FieldRow>

      {/* Diagram URL */}
      <FieldRow
        label="Architecture Diagram Link"
        hint="Lucidchart, draw.io, Miro, or any URL"
      >
        <input
          type="url"
          value={designData.diagramUrl}
          onChange={e => setDesignField('diagramUrl', e.target.value)}
          placeholder="https://lucid.app/…"
          className="evolv-input w-full text-xs px-3 py-2"
        />
        {designData.diagramUrl && (
          <a
            href={designData.diagramUrl}
            target="_blank"
            rel="noreferrer"
            className="text-[10px] text-blue-DEFAULT hover:opacity-80
                       underline underline-offset-2"
          >
            ↗ Open diagram
          </a>
        )}
      </FieldRow>

      {/* Save button */}
      <div className="flex items-center gap-3 pt-2">
        <button
          onClick={handleSave}
          className="px-5 py-2 rounded-lg text-xs font-semibold
                     bg-purple-DEFAULT/80 text-white
                     hover:opacity-90 transition-opacity"
          style={{ background: 'rgba(168,85,247,0.8)' }}
        >
          Save Design Spec
        </button>
        {saved && (
          <span className="text-[10px] text-lime-DEFAULT font-medium">
            ✓ Saved — Design phase marked complete
          </span>
        )}
      </div>
    </div>
  )
}

// ── Traceability Matrix tab ───────────────────────────────────────
function TraceabilityTab({ requirements, riskData, testScripts }) {
  // Build index: ur_id → { urReq, frs[], scriptId, stepRefs[] }
  const urRows = requirements.filter(r => r.type === 'UR')
  const frsByUr = {}
  requirements
    .filter(r => r.type === 'FR')
    .forEach(fr => {
      const key = fr.parentId ?? ''
      if (!frsByUr[key]) frsByUr[key] = []
      frsByUr[key].push(fr)
    })

  // Find test script + steps for each UR
  const scriptForUr = {}
  Object.values(testScripts).forEach(script => {
    const urId = script.ur_id ?? ''
    if (urId) scriptForUr[urId] = script
  })

  const RISK_COLORS = {
    HIGH:   { bg: 'rgba(239,68,68,0.12)',  text: '#ef4444' },
    MEDIUM: { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b' },
    LOW:    { bg: 'rgba(50,205,50,0.12)',  text: '#32CD32' },
  }

  const handleExport = useCallback(() => {
    const headers = [
      'urs_id', 'ur_id', 'ur_statement',
      'fr_ids', 'risk_level', 'test_assurance',
      'script_id', 'step_refs',
    ]
    const rows = urRows.map(ur => {
      const frs    = frsByUr[ur.id] ?? []
      const script = scriptForUr[ur.id]
      const risk   = riskData[ur.id] ?? {}
      return {
        urs_id:        ur.urs_id ?? '',
        ur_id:         ur.id,
        ur_statement:  ur.statement,
        fr_ids:        frs.map(f => f.id).join('; '),
        risk_level:    ur.risk_level ?? (
          riskData[ur.id]?.impact
            ? 'assessed'
            : 'not assessed'
        ),
        test_assurance: risk.testAssurance ?? '',
        script_id:     script?.script_id ?? '',
        step_refs:     (script?.steps ?? [])
          .filter(s => s.requirement_reference)
          .map(s => s.requirement_reference)
          .join('; '),
      }
    })
    downloadCSV('traceability-matrix.csv', headers, rows)
  }, [urRows, frsByUr, scriptForUr, riskData])

  if (urRows.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center
                      h-48 gap-3 text-center">
        <span className="text-2xl opacity-30">🔗</span>
        <p className="text-xs text-text-muted">
          No requirements loaded yet.
        </p>
        <p className="text-[10px] text-text-muted">
          Generate requirements in the Streamlit Validation Factory
          and click "Save to Risk Matrix", then complete the Risk phase.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Controls */}
      <div className="flex items-center gap-3">
        <p className="text-[10px] text-text-muted">
          {urRows.length} user requirement{urRows.length !== 1 ? 's' : ''}
          {' · '}
          {requirements.filter(r => r.type === 'FR').length} functional requirements
          {' · '}
          {Object.keys(scriptForUr).length} test script{
            Object.keys(scriptForUr).length !== 1 ? 's' : ''} linked
        </p>
        <button
          onClick={handleExport}
          className="ml-auto text-[10px] px-2.5 py-1 rounded border
                     border-border-base text-text-muted
                     hover:text-text-secondary hover:border-border-bright
                     transition-colors"
        >
          📥 Export CSV
        </button>
      </div>

      {/* Matrix table */}
      <div className="overflow-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="border-b border-border-base">
              {[
                'URS ID', 'UR ID', 'User Requirement',
                'Functional Reqs (FRs)', 'Risk Level',
                'Test Assurance', 'Script', 'Step Refs',
              ].map(h => (
                <th
                  key={h}
                  className="text-left text-[10px] font-semibold
                             text-text-muted uppercase tracking-wide
                             py-2 pr-4 whitespace-nowrap"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {urRows.map(ur => {
              const frs      = frsByUr[ur.id] ?? []
              const script   = scriptForUr[ur.id]
              const risk     = riskData[ur.id] ?? {}
              const riskLevel = ur.risk_level?.toUpperCase()
                ?? (risk.impact ? 'assessed' : null)
              const riskCfg  = RISK_COLORS[riskLevel] ?? null
              const stepRefs = (script?.steps ?? [])
                .filter(s => s.requirement_reference)
                .map(s => s.requirement_reference)
                .filter((v, i, a) => a.indexOf(v) === i)

              return (
                <tr
                  key={ur.id}
                  className="border-b border-border-base
                             hover:bg-bg-hover/30 transition-colors
                             bg-bg-surface/20"
                >
                  {/* URS ID */}
                  <td className="py-3 pr-4 font-mono text-[10px]
                                 text-text-muted whitespace-nowrap">
                    {ur.urs_id ?? '—'}
                  </td>

                  {/* UR ID */}
                  <td className="py-3 pr-4 font-mono font-semibold
                                 text-text-secondary text-[11px]
                                 whitespace-nowrap">
                    {ur.id}
                  </td>

                  {/* Statement */}
                  <td className="py-3 pr-4 text-text-secondary
                                 text-[11px] max-w-xs">
                    <span className="line-clamp-2 leading-relaxed">
                      {ur.statement}
                    </span>
                  </td>

                  {/* FRs */}
                  <td className="py-3 pr-4 max-w-[160px]">
                    {frs.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {frs.map(fr => (
                          <span
                            key={fr.id}
                            className="text-[9px] px-1.5 py-0.5 rounded
                                       bg-bg-card border border-border-base
                                       font-mono text-text-muted"
                          >
                            {fr.id}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-text-muted opacity-40 text-[10px]">
                        —
                      </span>
                    )}
                  </td>

                  {/* Risk level */}
                  <td className="py-3 pr-4 whitespace-nowrap">
                    {riskCfg ? (
                      <span
                        className="text-[9px] font-semibold px-2 py-0.5
                                   rounded-full"
                        style={{
                          background: riskCfg.bg,
                          color:      riskCfg.text,
                        }}
                      >
                        {riskLevel}
                      </span>
                    ) : (
                      <span className="text-[10px] text-text-muted
                                       opacity-40">—</span>
                    )}
                  </td>

                  {/* Test assurance */}
                  <td className="py-3 pr-4 text-[10px] text-text-muted
                                 whitespace-nowrap">
                    {risk.testAssurance ?? '—'}
                  </td>

                  {/* Script */}
                  <td className="py-3 pr-4 font-mono text-[10px]
                                 whitespace-nowrap">
                    {script ? (
                      <span className="text-lime-DEFAULT font-semibold">
                        {script.script_id}
                      </span>
                    ) : (
                      <span className="text-text-muted opacity-40">—</span>
                    )}
                  </td>

                  {/* Step refs */}
                  <td className="py-3 max-w-[120px]">
                    {stepRefs.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {stepRefs.map(ref => (
                          <span
                            key={ref}
                            className="text-[9px] px-1 py-0.5 rounded
                                       bg-blue-dim text-blue-DEFAULT
                                       font-mono"
                          >
                            {ref}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-text-muted opacity-40
                                       text-[10px]">—</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-[10px] text-text-muted
                      mt-4">
        <span className="font-semibold uppercase tracking-wide">
          Traceability:
        </span>
        <span>URS → UR → FR → Test Script → Step References</span>
        <span className="ml-auto">
          Complete end-to-end traceability per GAMP 5 Appendix M5
        </span>
      </div>
    </div>
  )
}

// ── Config Spec tab ───────────────────────────────────────────────
function ConfigSpecTab({ designData, addConfigItem, removeConfigItem }) {
  const [form, setForm] = useState({
    item: '', system: '', parameter: '', value: '',
    rationale: '', verifiedBy: '',
  })
  const [showForm, setShowForm] = useState(false)

  const handleAdd = () => {
    if (!form.item.trim()) return
    addConfigItem({ ...form, addedAt: new Date().toISOString() })
    setForm({
      item: '', system: '', parameter: '', value: '',
      rationale: '', verifiedBy: '',
    })
    setShowForm(false)
  }

  const handleExport = () => {
    const headers = [
      'item', 'system', 'parameter', 'value',
      'rationale', 'verifiedBy', 'addedAt',
    ]
    downloadCSV('config-spec.csv', headers, designData.configItems)
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setShowForm(v => !v)}
          className="px-3 py-1.5 text-xs rounded bg-purple-dim border
                     border-purple-DEFAULT/30 font-medium
                     hover:opacity-90 transition-opacity"
          style={{ color: '#a855f7' }}
        >
          {showForm ? '✕ Cancel' : '+ Add Config Item'}
        </button>
        {designData.configItems.length > 0 && (
          <button
            onClick={handleExport}
            className="text-[10px] px-2.5 py-1 rounded border
                       border-border-base text-text-muted
                       hover:text-text-secondary hover:border-border-bright
                       transition-colors"
          >
            📥 Export CSV
          </button>
        )}
        <span className="ml-auto text-[10px] text-text-muted">
          {designData.configItems.length} item{
            designData.configItems.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="p-4 rounded-lg border border-border-base
                        bg-bg-card space-y-3">
          <div className="grid grid-cols-2 gap-3">
            {[
              ['item',      'Config Item / Feature',    ''],
              ['system',    'System / Module',          ''],
              ['parameter', 'Configuration Parameter',  ''],
              ['value',     'Configured Value',         ''],
            ].map(([key, label, ph]) => (
              <div key={key} className="flex flex-col gap-1">
                <label className="text-[10px] text-text-muted">
                  {label}
                </label>
                <input
                  value={form[key]}
                  onChange={e =>
                    setForm(f => ({ ...f, [key]: e.target.value }))}
                  placeholder={ph || label}
                  className="evolv-input text-xs px-2 py-1.5"
                />
              </div>
            ))}
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-text-muted">
              Rationale / Business Justification
            </label>
            <textarea
              value={form.rationale}
              onChange={e =>
                setForm(f => ({ ...f, rationale: e.target.value }))}
              rows={2}
              placeholder="Why is this configured this way?…"
              className="evolv-input text-xs px-2 py-1.5 resize-none"
            />
          </div>
          <div className="flex items-end gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-text-muted">
                Verified By
              </label>
              <input
                value={form.verifiedBy}
                onChange={e =>
                  setForm(f => ({ ...f, verifiedBy: e.target.value }))}
                placeholder="Name / role…"
                className="evolv-input text-xs px-2 py-1.5 w-40"
              />
            </div>
            <button
              onClick={handleAdd}
              className="px-4 py-1.5 text-xs rounded font-semibold
                         text-white hover:opacity-90 transition-opacity"
              style={{ background: '#a855f7' }}
            >
              Add Item
            </button>
          </div>
        </div>
      )}

      {/* Table */}
      {designData.configItems.length === 0 ? (
        <div className="flex flex-col items-center justify-center
                        h-40 gap-2 text-center">
          <span className="text-2xl opacity-30">⚙️</span>
          <p className="text-xs text-text-muted">
            No configuration items logged.
          </p>
          <p className="text-[10px] text-text-muted">
            Document configured parameters, their values, and
            business rationale per GAMP 5 §7.4.
          </p>
        </div>
      ) : (
        <div className="overflow-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border-base">
                {['Item', 'System', 'Parameter', 'Value',
                  'Rationale', 'Verified By', ''].map(h => (
                  <th
                    key={h}
                    className="text-left text-[10px] font-semibold
                               text-text-muted uppercase tracking-wide
                               py-2 pr-4 whitespace-nowrap"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {designData.configItems.map((ci, idx) => (
                <tr
                  key={idx}
                  className="border-b border-border-base
                             hover:bg-bg-hover/30 transition-colors"
                >
                  <td className="py-2.5 pr-4 text-text-secondary
                                 font-medium text-[11px]">
                    {ci.item}
                  </td>
                  <td className="py-2.5 pr-4 text-text-muted text-[11px]">
                    {ci.system || '—'}
                  </td>
                  <td className="py-2.5 pr-4 font-mono text-[10px]
                                 text-text-muted">
                    {ci.parameter || '—'}
                  </td>
                  <td className="py-2.5 pr-4 font-mono text-[10px]
                                 text-blue-DEFAULT">
                    {ci.value || '—'}
                  </td>
                  <td className="py-2.5 pr-4 text-text-muted text-[10px]
                                 max-w-[180px]">
                    <span className="line-clamp-2">
                      {ci.rationale || '—'}
                    </span>
                  </td>
                  <td className="py-2.5 pr-4 text-text-muted text-[10px]
                                 whitespace-nowrap">
                    {ci.verifiedBy || '—'}
                  </td>
                  <td className="py-2.5">
                    <button
                      onClick={() => removeConfigItem(idx)}
                      className="text-[10px] text-text-muted
                                 hover:text-red-400 transition-colors"
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── Gate screen ───────────────────────────────────────────────────
function GateScreen({ openTab }) {
  return (
    <div className="flex flex-col h-full items-center justify-center
                    gap-5 text-center px-8">
      <div className="w-14 h-14 rounded-2xl bg-bg-card border
                      border-border-base flex items-center
                      justify-center text-3xl">
        🎨
      </div>
      <div className="max-w-sm space-y-2">
        <h2 className="text-text-primary font-semibold text-base">
          Design Specifications
        </h2>
        <p className="text-text-muted text-sm">
          Complete the{' '}
          <span className="text-amber-DEFAULT font-medium">
            Risk Assessment
          </span>{' '}
          phase before creating design artefacts. Risk profiling
          determines which design documents are required per your
          GAMP 5 category.
        </p>
      </div>
      <button
        onClick={() => openTab('risk')}
        className="px-5 py-2 rounded-lg text-xs font-semibold
                   bg-amber-dim border border-amber-DEFAULT/40
                   text-amber-DEFAULT hover:opacity-90
                   transition-opacity"
      >
        → Go to Risk Assessment
      </button>
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full
                      bg-bg-card border border-border-base mt-1">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-DEFAULT/60" />
        <span className="text-[10px] text-text-muted uppercase
                         tracking-widest">
          Awaiting Risk completion
        </span>
      </div>
    </div>
  )
}

// ── Main Design page ──────────────────────────────────────────────
export default function Design({ openTab }) {
  const {
    phaseCompletion, planData,
    designData, setDesignField, addConfigItem, removeConfigItem,
    setPhaseComplete,
    requirements, riskData, testScripts,
  } = useAppStore()

  const [activeTab, setActiveTab] = useState('spec')

  // Gate: Risk must be complete
  if (!phaseCompletion.risk) {
    return <GateScreen openTab={openTab} />
  }

  const tabs = [
    { id: 'spec',    label: '🎨 Design Spec'       },
    { id: 'trace',   label: '🔗 Traceability Matrix' },
    { id: 'config',  label: '⚙️ Config Spec'        },
  ]

  return (
    <div className="flex flex-col h-full bg-bg-base overflow-hidden">

      {/* ── Header strip ─────────────────────────────────── */}
      <div className="flex items-center gap-3 px-6 py-2.5 shrink-0
                      border-b"
        style={{
          background: 'rgba(168,85,247,0.06)',
          borderColor: 'rgba(168,85,247,0.20)',
        }}
      >
        <span className="text-xs font-semibold"
          style={{ color: '#a855f7' }}>
          Design
        </span>
        <span className="text-text-muted text-xs">
          {planData.projectName || 'No project name'}
        </span>
        {planData.gampCategory && (
          <span className="text-[10px] text-text-muted px-2 py-0.5
                           rounded border border-border-base">
            {GAMP_LABELS[planData.gampCategory] ?? ''}
          </span>
        )}
        {phaseCompletion.design && (
          <span className="text-[10px] font-medium text-lime-DEFAULT">
            ✓ Phase complete
          </span>
        )}
        {/* Tab switcher */}
        <div className="ml-auto flex gap-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                px-3 py-1 text-[11px] rounded transition-colors
                ${activeTab === tab.id
                  ? 'text-white'
                  : 'text-text-muted hover:text-text-secondary'}
              `}
              style={activeTab === tab.id
                ? { background: 'rgba(168,85,247,0.20)',
                    color: '#a855f7' }
                : {}}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Tab content ──────────────────────────────────── */}
      <div className="flex-1 overflow-auto px-6 py-5">
        {activeTab === 'spec' && (
          <DesignSpecTab
            designData={designData}
            setDesignField={setDesignField}
            planData={planData}
            setPhaseComplete={setPhaseComplete}
          />
        )}
        {activeTab === 'trace' && (
          <TraceabilityTab
            requirements={requirements}
            riskData={riskData}
            testScripts={testScripts}
          />
        )}
        {activeTab === 'config' && (
          <ConfigSpecTab
            designData={designData}
            addConfigItem={addConfigItem}
            removeConfigItem={removeConfigItem}
          />
        )}
      </div>
    </div>
  )
}
