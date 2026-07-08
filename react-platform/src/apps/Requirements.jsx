/**
 * Requirements — Lifecycle Phase 2: Requirements Hub
 *
 * Sprint 17 progress
 * ------------------
 *   ✓ 17.1 Wide-table React-native shell (matches Risk.jsx)
 *   ✓ 17.2 3 Cs editor (Capability / Condition / Constraint)
 *   ✓ 17.3 Functional / Non-Functional + 7-stakeholder dropdowns
 *   ✓ 17.4 Workshop intake → POST /requirements/generate
 *          → backend wraps RequirementArchitect.transform_urs_to_ur_fr()
 *   ✓ 17.5 AI Sidekick — 6 deterministic bad-pattern detectors
 *          (vague / untestable / reg-copy / too-long / and-or /
 *          missing-constraint) with per-row chips + aggregate rail
 *   ✓ 17.6 Mode toggle wired to layout reconfiguration —
 *          Workshop-Driven shows AI intake form; Manual Authoring
 *          hides intake, surfaces Add UR/FR toolbar + per-row delete
 *          + empty-state CTA, AI Sidekick stays live in both modes.
 *   ✓ 17.7 Per-row "✨ Refine with SMART" — flagged rows get a button
 *          that calls POST /requirements/refine-smart and renders the
 *          rewritten text + FDA/EMA flags + negative test scenario in
 *          an inline panel with Apply / Dismiss controls.
 */
import {
  Fragment, useState, useEffect, useCallback, useRef, useMemo,
} from 'react'
import { useAppStore } from '../store/useAppStore.js'
import { API_BASE } from '../config.js'
import {
  analyzeRequirement,
  summarizePatterns,
  SEVERITY_COLORS,
  CATEGORY_ORDER,
} from '../utils/requirementPatterns.js'
import BriefIntake from './requirements/BriefIntake.jsx'

// Sprint 34: `brief` is the new default — single textarea front door
// modeled on the Claude/ChatGPT chat-input pattern (and on Home.jsx
// HeroPrompt from Sprint 31). Workshop-Driven retains the 9-field
// form for power users who want to control role / risk / IM and
// upload diagrams. Manual Authoring stays the escape hatch for
// hand-written rows.
// Sprint 35.6 UX diet: dropped the emoji prefixes from MODES labels —
// emojis read as decoration when the modes are presented as a single
// segmented control (the visual context tells the user "you are
// picking a mode" without the icon doing redundant work).
const MODES = [
  {
    id:       'brief',
    label:    'Brief',
    sublabel: 'Paste a one-paragraph brief, get UR/FR drafts back. '
            + 'Same backend as Workshop, simpler way in.',
  },
  {
    id:       'workshop',
    label:    'Workshop',
    sublabel: 'AI generates first-draft URs/FRs from system description, '
            + 'workshop notes, Lucid diagram, workflow process.',
  },
  {
    id:       'manual',
    label:    'Manual',
    sublabel: 'Write requirements by hand. AI Sidekick flags vague '
            + 'language, missing constraints, reg-copy patterns.',
  },
]

// ── Seed data (visible until live data flows from Validation Factory) ──
const SEED_REQUIREMENTS = [
  {
    id: 'UR-1', type: 'UR',
    statement: 'The system shall register, track, and dispose of laboratory '
             + 'samples with full chain-of-custody.',
  },
  {
    id: 'FR-1', type: 'FR', parentId: 'UR-1',
    statement: 'The system shall capture sample receipt with timestamp and '
             + 'authenticated user attribution.',
  },
  {
    id: 'FR-2', type: 'FR', parentId: 'UR-1',
    statement: 'The system shall generate a unique chain-of-custody record '
             + 'per sample, immutable for the retention period.',
  },
  {
    id: 'UR-2', type: 'UR',
    statement: 'The system shall integrate with laboratory instruments for '
             + 'automated data capture.',
  },
  {
    id: 'FR-3', type: 'FR', parentId: 'UR-2',
    statement: 'The system shall receive instrument data via HL7 or ASTM '
             + 'interface within 30 seconds of acquisition.',
  },
  {
    id: 'UR-3', type: 'UR',
    statement: 'The system shall enforce electronic signatures per '
             + '21 CFR Part 11.',
  },
  {
    id: 'FR-4', type: 'FR', parentId: 'UR-3',
    statement: 'The system shall require authenticated e-signature for '
             + 'result approval.',
  },
  {
    id: 'FR-5', type: 'FR', parentId: 'UR-3',
    statement: 'The system shall maintain an immutable audit trail of all '
             + 'e-signature events.',
  },
]

// ── Type badge colors ──────────────────────────────────────────────────
function typeBadge(type) {
  if (type === 'UR') {
    return { bg: 'rgba(0,127,255,0.10)', fg: '#007FFF',
             border: 'rgba(0,127,255,0.30)' }
  }
  if (type === 'FR') {
    return { bg: 'rgba(168,85,247,0.10)', fg: '#a855f7',
             border: 'rgba(168,85,247,0.30)' }
  }
  return { bg: 'rgba(148,163,184,0.10)', fg: '#94a3b8',
           border: 'rgba(148,163,184,0.30)' }
}

// ── Functional / Non-Functional + Stakeholder enums (Sprint 17.3) ─────
const REQUIREMENT_TYPES = [
  { value: 'Functional',     label: 'Functional',     short: 'F'   },
  { value: 'Non-Functional', label: 'Non-Functional', short: 'NF'  },
]

const STAKEHOLDERS = [
  { value: 'Senior Mgmt', label: 'Senior Mgmt' },
  { value: 'Lab',         label: 'Lab'         },
  { value: 'IT',          label: 'IT'          },
  { value: 'QA/ITQA',     label: 'QA/ITQA'     },
  { value: 'Procurement', label: 'Procurement' },
  { value: 'Supplier',    label: 'Supplier'    },
  { value: 'Data Owner',  label: 'Data Owner'  },
]

// Stakeholder chip color (theme-agnostic — brand-locked accents)
const STAKEHOLDER_COLOR = {
  'Senior Mgmt': '#a855f7',  // purple
  'Lab':         '#007FFF',  // brand blue
  'IT':          '#0ea5e9',  // sky
  'QA/ITQA':     '#32CD32',  // brand lime
  'Procurement': '#f59e0b',  // amber
  'Supplier':    '#94a3b8',  // slate
  'Data Owner':  '#ef4444',  // red
}

// ── SMART refinement fetch helper (Sprint 17.7) ───────────────────────
// Hits POST /requirements/refine-smart. Resolves with the response JSON,
// rejects with a string suitable for inline display.
async function fetchSmartRefinement({
  reqId, statement, category, systemDescription, hasAiComponents,
}) {
  const res = await fetch(`${API_BASE}/requirements/refine-smart`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({
      requirement:        statement,
      requirement_id:     reqId ?? null,
      category:           category ?? 'general',
      system_description: systemDescription ?? '',
      has_ai_components:  Boolean(hasAiComponents),
    }),
  })
  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    try {
      const body = await res.json()
      msg = body?.detail ?? body?.message ?? msg
    } catch { /* ignore JSON parse errors */ }
    throw new Error(msg)
  }
  return res.json()
}


// ── AI Sidekick chip (Sprint 17.5) ─────────────────────────────────────
// Renders a small per-finding pill with the brand-locked severity color
// and a hover tooltip carrying the rewrite hint. Click handler is
// optional — used by the aggregate rail to filter rows.
function PatternChip({ finding, compact, onClick }) {
  const color = SEVERITY_COLORS[finding.severity] ?? SEVERITY_COLORS.info
  return (
    <button
      type="button"
      onClick={onClick}
      title={finding.hint}
      className={`
        inline-flex items-center gap-1 rounded-full font-medium
        whitespace-nowrap border transition-colors
        hover:brightness-110
        ${compact
          ? 'px-1.5 py-0.5 text-[9px]'
          : 'px-2 py-0.5 text-[10px]'}
      `}
      style={{
        background: color + '14',  /* ~8% alpha */
        color,
        borderColor: color + '4d',  /* 30% alpha */
      }}
    >
      <span>{finding.label}</span>
    </button>
  )
}

function PatternChipRow({ findings, dense, refineSlot }) {
  if (!findings || findings.length === 0) {
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full
                   text-[10px] font-medium border"
        style={{
          background: 'rgba(50,205,50,0.08)',
          color:      '#32CD32',
          borderColor: 'rgba(50,205,50,0.30)',
        }}
        title="No bad-pattern findings — looks audit-ready"
      >
        ✓ clean
      </span>
    )
  }
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {findings.map(f => (
        <PatternChip key={f.id} finding={f} compact={dense} />
      ))}
      {refineSlot}
    </div>
  )
}


// ── Refine with SMART button (Sprint 17.7) ────────────────────────────
// Tucks into the row chip cluster on flagged rows. Shows loading spinner
// while POST /requirements/refine-smart is in flight, then expands into
// the RefinementPanel below the row.
function RefineButton({ status, onClick, disabled }) {
  const isLoading = status === 'loading'
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || isLoading}
      title={
        disabled
          ? 'Add some text to the row first'
          : 'Run SMART engine on this row — adds reg-flag detection, '
          + 'rewrite suggestion, and a negative test scenario'
      }
      className="inline-flex items-center gap-1 rounded-full font-semibold
                 whitespace-nowrap border transition-colors
                 hover:brightness-110 disabled:opacity-40
                 disabled:cursor-not-allowed
                 px-2 py-0.5 text-[10px]"
      style={{
        background:  'rgba(168,85,247,0.10)',
        color:       '#a855f7',
        borderColor: 'rgba(168,85,247,0.40)',
      }}
    >
      {isLoading ? '⏳ Refining…' : '✨ Refine with SMART'}
    </button>
  )
}


// ── Refinement panel (Sprint 17.7) ────────────────────────────────────
// Renders below the Sidekick chip row when the engine returns a
// suggestion. Side-by-side original/refined view, FDA/EMA flags,
// negative test scenario, Apply / Dismiss controls.
function RefinementPanel({ suggestion, error, onApply, onDismiss }) {
  if (error) {
    return (
      <div
        className="px-3 py-2 rounded border text-[10.5px]
                   flex items-center justify-between gap-3"
        style={{
          background:  'rgba(239,68,68,0.06)',
          borderColor: 'rgba(239,68,68,0.30)',
          color:       '#ef4444',
        }}
      >
        <span>
          <span className="font-semibold">SMART refinement failed:</span>{' '}
          <span className="text-text-secondary">{error}</span>
        </span>
        <button
          type="button"
          onClick={onDismiss}
          className="text-[10px] underline hover:no-underline"
        >
          Dismiss
        </button>
      </div>
    )
  }
  if (!suggestion) return null

  const {
    original, smart_text, risk_level, fda_ema_flags,
    acceptance_criteria, negative_test_scenario, engine_mode,
  } = suggestion

  const riskColor = risk_level === 'High'
    ? '#ef4444' : risk_level === 'Medium'
    ? '#f59e0b' : '#32CD32'

  // Acceptance criteria comes back as a {SMART:[…]} dict — flatten
  // to a single bullet list for inline display.
  const acItems = Object.values(acceptance_criteria ?? {})
    .flat()
    .filter(Boolean)

  return (
    <div
      className="rounded border text-[10.5px] overflow-hidden"
      style={{
        background:  'rgba(168,85,247,0.04)',
        borderColor: 'rgba(168,85,247,0.30)',
      }}
    >
      <div
        className="px-3 py-1.5 flex items-center justify-between
                   text-[10px] uppercase tracking-wide font-semibold"
        style={{
          background: 'rgba(168,85,247,0.10)',
          color:      '#a855f7',
        }}
      >
        <span className="flex items-center gap-2">
          ✨ SMART Refinement
          <span
            className="px-1.5 py-0.5 rounded text-[9px] normal-case"
            style={{
              background:  riskColor + '20',
              color:       riskColor,
              borderColor: riskColor + '4d',
            }}
          >
            {risk_level} risk
          </span>
          <span className="text-text-muted normal-case font-normal">
            engine: {engine_mode}
          </span>
        </span>
        <button
          type="button"
          onClick={onDismiss}
          className="text-text-muted hover:text-text-primary normal-case
                     font-normal text-[10px]"
          title="Close panel without applying"
        >
          Dismiss
        </button>
      </div>

      <div className="px-3 py-2 grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <div className="text-[9px] uppercase tracking-wide
                          text-text-muted font-semibold mb-1">
            Original
          </div>
          <div className="text-text-secondary leading-snug">
            {original}
          </div>
        </div>
        <div>
          <div className="text-[9px] uppercase tracking-wide
                          font-semibold mb-1"
               style={{ color: '#a855f7' }}>
            Refined
          </div>
          <div className="text-text-primary leading-snug font-medium">
            {smart_text}
          </div>
        </div>
      </div>

      {(fda_ema_flags?.length > 0 || negative_test_scenario || acItems.length > 0) && (
        <div className="px-3 pb-2 space-y-1.5">
          {fda_ema_flags?.length > 0 && (
            <div className="flex flex-wrap items-center gap-1">
              <span className="text-[9px] uppercase tracking-wide
                              text-text-muted font-semibold mr-1">
                FDA/EMA flags
              </span>
              {fda_ema_flags.map(flag => (
                <span
                  key={flag}
                  className="px-1.5 py-0.5 rounded text-[9px] border"
                  style={{
                    background:  'rgba(239,68,68,0.10)',
                    color:       '#ef4444',
                    borderColor: 'rgba(239,68,68,0.40)',
                  }}
                >
                  {flag}
                </span>
              ))}
            </div>
          )}
          {acItems.length > 0 && (
            <div>
              <div className="text-[9px] uppercase tracking-wide
                              text-text-muted font-semibold mb-0.5">
                Acceptance criteria (template)
              </div>
              <ul className="text-text-secondary leading-snug list-disc
                             pl-4 space-y-0.5">
                {acItems.slice(0, 4).map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          {negative_test_scenario && (
            <div>
              <div className="text-[9px] uppercase tracking-wide
                              text-text-muted font-semibold mb-0.5">
                Negative test scenario
              </div>
              <div className="text-text-secondary leading-snug italic">
                {negative_test_scenario}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="px-3 py-1.5 border-t flex items-center justify-end
                      gap-2 bg-bg-card/30"
           style={{ borderColor: 'rgba(168,85,247,0.20)' }}>
        <button
          type="button"
          onClick={onDismiss}
          className="text-[10px] px-2 py-0.5 rounded text-text-muted
                     hover:text-text-primary hover:bg-bg-card/60
                     transition-colors"
        >
          Dismiss
        </button>
        <button
          type="button"
          onClick={onApply}
          className="text-[10px] px-2.5 py-0.5 rounded font-semibold
                     border transition-colors hover:brightness-110"
          style={{
            background:  'rgba(168,85,247,0.15)',
            color:       '#a855f7',
            borderColor: 'rgba(168,85,247,0.50)',
          }}
          title="Replace this row's Capability cell with the refined text"
        >
          Apply refined →
        </button>
      </div>
    </div>
  )
}


// ── Manual-authoring toolbar (Sprint 17.6) ─────────────────────────────
// Surfaces row-creation actions when the user opts out of the workshop
// intake flow. Add FR is a select-then-confirm flow because every FR
// must be parented to a UR (otherwise the dependency tree breaks the
// PDF/Word exporters).
function ManualAuthoringToolbar({
  urs, requirementCount, onAddUR, onAddFR, onClearAll,
}) {
  const [parentChoice, setParentChoice] = useState('')

  const handleAddFRClick = () => {
    if (!parentChoice) return
    onAddFR(parentChoice)
  }

  return (
    <div
      className="mb-3 px-3 py-2 rounded border flex flex-wrap items-center
                 gap-x-3 gap-y-2 text-[11px]"
      style={{
        background:  'rgba(168,85,247,0.05)',  /* purple = manual flow */
        borderColor: 'rgba(168,85,247,0.25)',
      }}
    >
      <span className="font-semibold uppercase tracking-wide
                       text-[10px] flex items-center gap-1"
            style={{ color: '#a855f7' }}>
        ✏ Manual Authoring
      </span>

      <button
        type="button"
        onClick={onAddUR}
        className="inline-flex items-center gap-1
                   px-2.5 py-1 rounded font-semibold text-[10px]
                   border transition-colors hover:brightness-110"
        style={{
          background:  'rgba(0,127,255,0.10)',
          color:       '#007FFF',
          borderColor: 'rgba(0,127,255,0.40)',
        }}
        title="Append a new User Requirement (UR)"
      >
        + Add UR
      </button>

      <div className="flex items-center gap-1.5">
        <select
          value={parentChoice}
          onChange={e => setParentChoice(e.target.value)}
          className="evolv-input evolv-select text-[10px] py-1 pl-2 pr-1 h-7"
          disabled={urs.length === 0}
          title={urs.length === 0
            ? 'Add a UR first — every FR must be parented to a UR'
            : 'Pick the parent UR for the new FR'}
        >
          <option value="">
            {urs.length === 0 ? 'Add a UR first' : 'Parent UR…'}
          </option>
          {urs.map(u => (
            <option key={u.id} value={u.id}>{u.id}</option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleAddFRClick}
          disabled={!parentChoice}
          className="inline-flex items-center gap-1
                     px-2.5 py-1 rounded font-semibold text-[10px]
                     border transition-colors
                     hover:brightness-110 disabled:opacity-40
                     disabled:cursor-not-allowed"
          style={{
            background:  'rgba(168,85,247,0.10)',
            color:       '#a855f7',
            borderColor: 'rgba(168,85,247,0.40)',
          }}
          title="Append a Functional Requirement (FR) under the chosen UR"
        >
          + Add FR
        </button>
      </div>

      <span className="text-text-muted text-[10px] ml-1">
        Hand-typed rows are flagged live by the AI Sidekick rail below
      </span>

      {requirementCount > 0 && (
        <button
          type="button"
          onClick={onClearAll}
          className="ml-auto text-[10px] text-text-muted
                     hover:text-red-DEFAULT underline underline-offset-2"
          title="Remove every requirement from the table"
        >
          Clear all
        </button>
      )}
    </div>
  )
}

// ── Manual-mode empty state (Sprint 17.6) ──────────────────────────────
// Replaces the seed-data fallback so a brand-new manual session has a
// clear next-step CTA instead of dropping into pre-populated rows the
// user didn't type.
function ManualEmptyState({ onAddUR }) {
  return (
    <div
      className="mb-4 px-6 py-8 rounded border-2 border-dashed
                 flex flex-col items-center justify-center text-center gap-2"
      style={{
        background:  'rgba(168,85,247,0.04)',
        borderColor: 'rgba(168,85,247,0.30)',
      }}
    >
      <span className="text-3xl" role="img" aria-label="pencil">✏</span>
      <h3 className="text-sm font-semibold text-text-primary">
        Start typing your first requirement
      </h3>
      <p className="text-[11px] text-text-muted max-w-md leading-relaxed">
        Manual mode skips AI generation. Add a UR, then layer FRs under
        it. The AI Sidekick rail will flag vague language, missing
        constraints, and reg-copy patterns as you type — advisory only,
        never a hard gate.
      </p>
      <button
        type="button"
        onClick={onAddUR}
        className="mt-2 inline-flex items-center gap-1
                   px-3 py-1.5 rounded font-semibold text-[11px]
                   border transition-colors hover:brightness-110"
        style={{
          background:  'rgba(0,127,255,0.10)',
          color:       '#007FFF',
          borderColor: 'rgba(0,127,255,0.40)',
        }}
      >
        + Add my first UR
      </button>
    </div>
  )
}

// ── Inline select (matches Risk.jsx pattern) ───────────────────────────
function InlineSelect({ value, options, placeholder, onChange }) {
  return (
    <select
      value={value ?? ''}
      onChange={e => onChange(e.target.value)}
      className="evolv-input evolv-select text-[11px] py-1 pl-1.5 pr-0 h-7 w-full"
    >
      <option value="">{placeholder}</option>
      {options.map(o => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  )
}

// ── 3 Cs derivation (Sprint 17.2) ──────────────────────────────────────
// Concatenates Capability + Condition + Constraint into a single
// "The system shall …" statement for downstream consumers (PDF, Word,
// agent calls). Returns the legacy fallback if no 3 Cs are filled.
function deriveStatement(meta, fallback) {
  const cap  = (meta?.capability ?? '').trim()
  const cond = (meta?.condition  ?? '').trim()
  const con  = (meta?.constraint ?? '').trim()
  if (!cap && !cond && !con) return fallback ?? ''
  let s = cap
  if (s && !/^the system\b/i.test(s)) {
    s = 'The system shall ' + s.replace(/^./, c => c.toLowerCase())
  }
  if (cond) s = (s ? s + ' ' : '') + cond
  if (con)  s = (s ? s + ' ' : '') + con
  return s.replace(/\s+/g, ' ').replace(/\s+([.,;:])/g, '$1').trim()
}

// ── 3 Cs editor cell ───────────────────────────────────────────────────
function CsCell({ value, placeholder, onChange, optional }) {
  return (
    <textarea
      value={value ?? ''}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      rows={2}
      className={`
        w-full text-[11px] leading-relaxed p-1.5 rounded
        border bg-bg-card text-text-primary
        placeholder-text-muted
        border-border-base hover:border-border-bright
        focus:outline-none focus:border-blue-DEFAULT/60
        focus:ring-1 focus:ring-blue-DEFAULT/30
        transition-colors resize-y min-h-[44px]
        ${optional ? 'opacity-90' : ''}
      `}
    />
  )
}

// ── Workshop intake form (Sprint 17.4) ─────────────────────────────────
// Top-of-page form (Flow A) that posts the four "additional_context"
// inputs to POST /requirements/generate. The backend runs each parsed
// workflow line through RequirementArchitect.generate_urs() then
// transform_urs_to_ur_fr(additional_context=…) and returns flat UR/FR
// rows + per-UR 3 Cs split, which we drop straight into the store so
// the editor below pre-fills.
function WorkshopIntake({
  onGenerated,
  onError,
  busy,
  setBusy,
  status,
  setStatus,
}) {
  // Sprint 35.5 (F2 fix): read the active project's name + system
  // description from the Plan phase so the Workshop form opens
  // pre-filled. Lazy initialisers prevent stomping on user edits when
  // the parent re-renders. If the user wants the latest Plan values
  // after editing Plan, they can clear the field and tab away — or we
  // ship a "Pull from Plan ↻" button in a future polish sprint.
  const planData = useAppStore(s => s.planData)
  const initialProjectName = planData?.projectName       ?? ''
  const initialSysDesc     = planData?.systemDescription ?? ''

  const [projectName,       setProjectName]       = useState(() => initialProjectName)
  const [systemDescription, setSystemDescription] = useState(() => initialSysDesc)
  const [workshopNotes,     setWorkshopNotes]     = useState('')
  const [diagramUrl,        setDiagramUrl]        = useState('')
  const [diagramContent,    setDiagramContent]    = useState('')
  const [diagramFilename,   setDiagramFilename]   = useState('')
  const [workflowProcess,   setWorkflowProcess]   = useState('')
  const [role,              setRole]              = useState('Lab Technician')
  const [riskAssessment,    setRiskAssessment]    = useState('GxP Indirect')
  const [implementation,    setImplementation]    = useState('Configured')

  const canSubmit = (
    !busy
    && (workflowProcess.trim().length > 9
        || systemDescription.trim().length > 9)
  )

  const handleFile = async e => {
    const f = e.target.files?.[0]
    if (!f) return
    setDiagramFilename(f.name)
    try {
      const text = await f.text()
      setDiagramContent(text)
    } catch {
      // Binary diagram (e.g. .vsdx) — keep filename only.
      setDiagramContent('')
    }
  }

  const handleSubmit = async () => {
    if (!canSubmit) return
    setBusy(true)
    setStatus({ kind: 'info', text: 'Generating UR/FR drafts…' })
    try {
      const res = await fetch(`${API_BASE}/requirements/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name:        projectName       || null,
          system_description:  systemDescription || null,
          workshop_notes:      workshopNotes     || null,
          lucidchart_url:      diagramUrl        || null,
          lucidchart_content:  diagramContent    || null,
          workflow_process:    workflowProcess   || null,
          role,
          risk_assessment:     riskAssessment,
          implementation_method: implementation,
        }),
      })
      if (!res.ok) {
        let detail = `HTTP ${res.status}`
        try {
          const err = await res.json()
          detail = typeof err.detail === 'string'
            ? err.detail
            : (err.detail?.message ?? detail)
        } catch { /* keep status */ }
        throw new Error(detail)
      }
      const data = await res.json()
      onGenerated(data)
      const skipNote = data.skipped?.length
        ? ` · ${data.skipped.length} line${
            data.skipped.length === 1 ? '' : 's'
          } skipped (no GAMP 5 context)`
        : ''
      setStatus({
        kind: 'ok',
        text: `Generated ${data.count} requirement row${
          data.count === 1 ? '' : 's'
        } from workshop inputs${skipNote}`,
      })
    } catch (e) {
      onError?.(e)
      setStatus({
        kind: 'err',
        text: (
          `Generation failed: ${e.message ?? e}. `
          + 'The form is still saved locally — switch to Manual '
          + 'Authoring or retry.'
        ),
      })
    } finally {
      setBusy(false)
    }
  }

  const handleClear = () => {
    setProjectName(''); setSystemDescription(''); setWorkshopNotes('')
    setDiagramUrl(''); setDiagramContent(''); setDiagramFilename('')
    setWorkflowProcess('')
    setStatus(null)
  }

  return (
    <div
      className="mb-4 rounded border bg-bg-card"
      style={{
        borderColor: 'rgba(0,127,255,0.25)',
        boxShadow: '0 0 0 1px rgba(0,127,255,0.04) inset',
      }}
    >
      <div
        className="flex items-center justify-between gap-3 px-4 py-2 border-b"
        style={{ borderColor: 'rgba(0,127,255,0.18)' }}
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-blue-DEFAULT">
            🛠 Workshop Intake
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-DEFAULT/10
                           text-blue-DEFAULT font-medium">
            Flow A · 17.4
          </span>
          <span className="text-[11px] text-text-muted hidden md:inline">
            AI generates first-draft URs/FRs from workshop inputs
            and pre-fills the 3 Cs editor below
          </span>
        </div>
        <div className="flex items-center gap-2">
          {status && (
            <span
              className="text-[10px] px-2 py-0.5 rounded font-medium"
              style={{
                background:
                  status.kind === 'ok'   ? 'rgba(50,205,50,0.10)' :
                  status.kind === 'err'  ? 'rgba(239,68,68,0.10)' :
                                           'rgba(0,127,255,0.10)',
                color:
                  status.kind === 'ok'   ? '#32CD32' :
                  status.kind === 'err'  ? '#ef4444' :
                                           '#007FFF',
              }}
            >
              {status.text}
            </span>
          )}
          <button
            onClick={handleClear}
            disabled={busy}
            className="text-[10px] text-text-muted hover:text-text-secondary
                       transition-colors disabled:opacity-40"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Project name */}
        <label className="flex flex-col gap-1 md:col-span-2">
          <span className="text-[10px] font-semibold uppercase tracking-wide
                           text-text-muted">
            Project Name <span className="text-text-muted/60">(optional)</span>
          </span>
          <input
            type="text"
            value={projectName}
            onChange={e => setProjectName(e.target.value)}
            placeholder="e.g. Sample Tracking System"
            className="evolv-input text-xs py-1.5 px-2 h-8"
            disabled={busy}
          />
        </label>

        {/* System description */}
        <label className="flex flex-col gap-1">
          <span className="text-[10px] font-semibold uppercase tracking-wide
                           text-text-muted">
            System Description
          </span>
          <textarea
            value={systemDescription}
            onChange={e => setSystemDescription(e.target.value)}
            placeholder="LIMS v4.2, cloud-hosted, integrates with HL7 instruments…"
            rows={3}
            className="evolv-input text-xs p-2 leading-relaxed resize-y"
            disabled={busy}
          />
        </label>

        {/* Workshop notes */}
        <label className="flex flex-col gap-1">
          <span className="text-[10px] font-semibold uppercase tracking-wide
                           text-text-muted">
            Workshop Notes
          </span>
          <textarea
            value={workshopNotes}
            onChange={e => setWorkshopNotes(e.target.value)}
            placeholder="Stakeholder asks: chain-of-custody safety-critical, witnessed disposal…"
            rows={3}
            className="evolv-input text-xs p-2 leading-relaxed resize-y"
            disabled={busy}
          />
        </label>

        {/* Diagram URL + file */}
        <label className="flex flex-col gap-1">
          <span className="text-[10px] font-semibold uppercase tracking-wide
                           text-text-muted">
            Diagram URL
            <span className="text-text-muted/60 ml-1 normal-case font-normal">
              (Lucid · draw.io · Visio link)
            </span>
          </span>
          <input
            type="url"
            value={diagramUrl}
            onChange={e => setDiagramUrl(e.target.value)}
            placeholder="https://lucid.app/lucidchart/…"
            className="evolv-input text-xs py-1.5 px-2 h-8"
            disabled={busy}
          />
          <div className="flex items-center gap-2 mt-1">
            <input
              type="file"
              onChange={handleFile}
              disabled={busy}
              className="text-[10px] text-text-muted file:mr-2 file:py-1
                         file:px-2 file:rounded file:border-0
                         file:bg-blue-DEFAULT/10 file:text-blue-DEFAULT
                         file:font-medium hover:file:bg-blue-DEFAULT/15"
            />
            {diagramFilename && (
              <span className="text-[10px] text-text-muted truncate">
                {diagramFilename}
              </span>
            )}
          </div>
        </label>

        {/* Workflow process */}
        <label className="flex flex-col gap-1">
          <span className="text-[10px] font-semibold uppercase tracking-wide
                           text-text-muted">
            Workflow Process
            <span className="text-text-muted/60 ml-1 normal-case font-normal">
              (one step per line; bullets / numbers OK)
            </span>
          </span>
          <textarea
            value={workflowProcess}
            onChange={e => setWorkflowProcess(e.target.value)}
            placeholder={'- Register sample on receipt\n'
                       + '- Track sample through laboratory workflow\n'
                       + '- Record disposal with witness signature'}
            rows={5}
            className="evolv-input text-xs p-2 leading-relaxed resize-y
                       font-mono"
            disabled={busy}
          />
        </label>

        {/* Persona / risk / implementation row */}
        <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <label className="flex flex-col gap-1">
            <span className="text-[10px] font-semibold uppercase tracking-wide
                             text-text-muted">
              Persona
            </span>
            <input
              type="text"
              value={role}
              onChange={e => setRole(e.target.value)}
              placeholder="Lab Technician"
              className="evolv-input text-xs py-1.5 px-2 h-8"
              disabled={busy}
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[10px] font-semibold uppercase tracking-wide
                             text-text-muted">
              Risk Assessment
            </span>
            <select
              value={riskAssessment}
              onChange={e => setRiskAssessment(e.target.value)}
              className="evolv-input evolv-select text-xs py-1.5 px-2 h-8"
              disabled={busy}
            >
              <option>GxP Direct</option>
              <option>GxP Indirect</option>
              <option>GxP None</option>
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[10px] font-semibold uppercase tracking-wide
                             text-text-muted">
              Implementation Method
            </span>
            <select
              value={implementation}
              onChange={e => setImplementation(e.target.value)}
              className="evolv-input evolv-select text-xs py-1.5 px-2 h-8"
              disabled={busy}
            >
              <option>Out of the Box</option>
              <option>Configured</option>
              <option>Custom</option>
            </select>
          </label>
        </div>

        {/* Submit row */}
        <div className="md:col-span-2 flex items-center justify-end gap-2 pt-1">
          <span className="text-[10px] text-text-muted mr-auto">
            POST{' '}
            <code className="px-1 rounded bg-bg-elev text-blue-DEFAULT">
              {API_BASE}/requirements/generate
            </code>
          </span>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className={`
              flex items-center gap-1.5 text-xs font-semibold
              px-3 py-1.5 rounded transition-all
              ${canSubmit
                ? 'bg-blue-DEFAULT text-white hover:bg-blue-DEFAULT/90'
                : 'bg-bg-elev text-text-muted cursor-not-allowed'}
            `}
          >
            {busy
              ? (<>
                  <svg width="12" height="12" viewBox="0 0 12 12"
                       className="animate-spin">
                    <path d="M10 6a4 4 0 01-4 4 4 4 0 01-4-4 4 4 0 014-4"
                          stroke="currentColor" strokeWidth="1.5"
                          fill="none" strokeLinecap="round"/>
                  </svg>
                  Generating…
                </>)
              : '🤖 Generate UR/FR drafts'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────────────────────────────
// Sprint 35.6 Step A wrap-up: accept `openTab` so the new "Rank →"
// CTA in unranked Risk-Level cells can deep-link the user to the
// Risk phase. Also pull `riskData` so the Risk Level + Test Strategy
// columns show LIVE values (set on the Risk page) instead of the
// stale `req.risk_level` / `req.test_strategy` properties that never
// actually existed on the requirement objects.
export default function Requirements({ openTab }) {
  const {
    setPhaseComplete,
    requirements,
    setRequirements,
    requirementMeta,
    setRequirementMeta,
    bulkSetRequirementMeta,
    addRequirement,
    removeRequirement,
    clearRequirements,
    requirementRefinements,
    setRefinementLoading,
    setRefinementSuggestion,
    setRefinementError,
    clearRefinement,
    applyRefinementSuggestion,
    riskData,
  } = useAppStore()

  // Sprint 35.6 Step A wrap-up: pure helpers that mirror Risk.jsx's
  // matrix so the Requirements page derives the same values without
  // a cross-import. If Risk.jsx logic ever changes, update here too
  // (or extract to a shared util — Sprint 38 design-system work).
  const _calcRisk = (impact, impl) => {
    if (!impact || !impl)        return null
    if (impact === 'No GxP')     return 'LOW'
    if (impact === 'GxP Direct') {
      return impl === 'Out of the Box' ? 'MEDIUM' : 'HIGH'
    }
    if (impl === 'Configured')   return 'HIGH'
    if (impl === 'Custom')       return 'MEDIUM'
    return 'LOW'
  }
  const _defaultTestStrategy = level => {
    if (level === 'HIGH')   return 'Scripted'
    if (level === 'MEDIUM') return 'Scripted'
    return 'Unscripted'
  }

  // Sprint 34: default to the single-textarea Brief mode. Power users
  // can still toggle to Workshop-Driven (9-field form) or Manual.
  const [mode, setMode]             = useState('brief')
  const [syncState,   setSyncState] = useState('idle')   // idle|syncing|live|error
  const [syncMsg,     setSyncMsg]   = useState('')
  const [lastSynced, setLastSynced] = useState(null)
  const syncRef = useRef(false)

  // Sprint 35.6 UX diet: `⋯ More` menu collapses the sync controls,
  // seed-data reset, and legacy-Streamlit link off the main header.
  // First-paint surface drops from ~6 actionable controls to ~3.
  const [moreOpen, setMoreOpen] = useState(false)
  const moreRef = useRef(null)
  useEffect(() => {
    if (!moreOpen) return
    const onDocClick = e => {
      if (moreRef.current && !moreRef.current.contains(e.target)) {
        setMoreOpen(false)
      }
    }
    document.addEventListener('mousedown', onDocClick)
    return () => document.removeEventListener('mousedown', onDocClick)
  }, [moreOpen])

  // Sprint 35.6 Step A — view-mode toggles. The 3 Cs columns and
  // AI Sidekick chip rail are powerful but visually heavy. Default
  // to the calm "Statement" view (single column showing the derived
  // requirement text) with advisories off. Manual mode auto-enables
  // 3 Cs editing because that's how users author there. Users can
  // flip either toggle on demand from the ⋯ More menu.
  const [showCs, setShowCs] = useState(false)
  const [showAdvisories, setShowAdvisories] = useState(false)
  useEffect(() => {
    if (mode === 'manual') setShowCs(true)
    // Switching back to Brief/Workshop doesn't force showCs off —
    // respects the user's last preference within the session.
  }, [mode])

  // Workshop intake state (Sprint 17.4)
  const [workshopBusy,   setWorkshopBusy]   = useState(false)
  const [workshopStatus, setWorkshopStatus] = useState(null)

  const handleWorkshopGenerated = useCallback(data => {
    if (Array.isArray(data?.requirements) && data.requirements.length > 0) {
      setRequirements(data.requirements)
      setLastSynced(new Date())
      setSyncState('live')
      setSyncMsg(
        `${data.count} requirement${data.count !== 1 ? 's' : ''} `
        + `generated from workshop intake`
        + (data.project_name ? ` · ${data.project_name}` : '')
      )
    }
    if (data?.meta) {
      Object.entries(data.meta).forEach(([id, m]) => {
        bulkSetRequirementMeta(id, {
          capability:        m.capability       ?? '',
          condition:         m.condition        ?? '',
          constraint:        m.constraint       ?? '',
          requirement_type:  m.requirement_type ?? 'Functional',
          stakeholder:       m.stakeholder      ?? 'Lab',
        })
      })
    }
    setPhaseComplete('requirements')
  }, [setRequirements, bulkSetRequirementMeta, setPhaseComplete])

  // ── Sync from FastAPI ──────────────────────────────────────────────
  const doSync = useCallback(async () => {
    if (syncRef.current) return
    syncRef.current = true
    setSyncState('syncing')
    try {
      const res = await fetch(`${API_BASE}/requirements`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if ((data.requirements ?? []).length > 0) {
        setRequirements(data.requirements)
        setLastSynced(new Date())
        setSyncState('live')
        setSyncMsg(
          `${data.count} requirement${data.count !== 1 ? 's' : ''} `
          + 'synced from EVOLV'
        )
      } else {
        setSyncState('idle')
        setSyncMsg(
          'No requirements synced yet — using seed data'
        )
      }
    } catch {
      setSyncState('error')
      setSyncMsg('FastAPI not reachable — using seed data')
    } finally {
      syncRef.current = false
    }
  }, [setRequirements])

  useEffect(() => { doSync() }, [])  // auto-sync on mount

  // ── Data source by mode (Sprint 17.6) ──────────────────────────────
  // Workshop mode: fall back to seed data so a brand-new project shows
  // a populated editor for orientation. Manual mode: never fall back —
  // seed rows aren't safely editable/removable and the empty state
  // pushes the user to start typing instead.
  // Brief + Workshop modes fall back to seed data so a brand-new
  // project shows a populated editor for orientation. Manual mode
  // never falls back — seed rows aren't safely editable/removable
  // and the empty state pushes the user to start typing instead.
  const activeRequirements = requirements.length > 0
    ? requirements
    : (mode === 'manual' ? [] : SEED_REQUIREMENTS)

  const urCount = activeRequirements.filter(r => r.type === 'UR').length
  const frCount = activeRequirements.filter(r => r.type === 'FR').length

  // ── AI Sidekick — Sprint 17.5 ────────────────────────────────────
  // Run all six pattern detectors against every visible row. Pure
  // computation — no network, no LLM — so cheap to recompute on every
  // 3 Cs / Class edit.
  const flagsByRow = useMemo(() => {
    const map = {}
    for (const req of activeRequirements) {
      const meta = requirementMeta[req.id] ?? {}
      const derived = deriveStatement(meta, req.statement)
      map[req.id] = analyzeRequirement(req, meta, derived)
    }
    return map
  }, [activeRequirements, requirementMeta])

  const sidekickSummary = useMemo(
    () => summarizePatterns(flagsByRow, activeRequirements.length),
    [flagsByRow, activeRequirements.length],
  )

  // Optional: filter the table to one detector category when the user
  // clicks a chip on the aggregate rail.
  const [activeFilter, setActiveFilter] = useState(null)

  const filteredRequirements = activeFilter
    ? activeRequirements.filter(r =>
        (flagsByRow[r.id] ?? []).some(f => f.id === activeFilter))
    : activeRequirements

  const handleModeChange = id => {
    setMode(id)
    // Clear the stale workshop status when mode changes — a red
    // "Generation failed" pill from a prior attempt would otherwise
    // linger above an empty form when the user toggles back.
    setWorkshopStatus(null)
    // Clear any active sidekick filter so a manual user doesn't see
    // an empty table after switching modes if a workshop-only chip
    // was active.
    setActiveFilter(null)
    setPhaseComplete('requirements')
  }

  // ── Manual-authoring handlers (Sprint 17.6) ────────────────────────
  // All paths force live sync state to "live" so the seed-data
  // fallback doesn't quietly re-appear after a hand-typed batch is
  // wiped down to zero rows.
  const handleAddUR = () => {
    addRequirement({ type: 'UR', statement: '' })
    setSyncState('live')
    setSyncMsg('Manual authoring — hand-typed requirements')
    setPhaseComplete('requirements')
  }

  const handleAddFR = parentId => {
    addRequirement({ type: 'FR', statement: '', parentId })
    setSyncState('live')
    setSyncMsg('Manual authoring — hand-typed requirements')
    setPhaseComplete('requirements')
  }

  const handleRemoveRequirement = id => {
    removeRequirement(id)
    setPhaseComplete('requirements')
  }

  const handleClearAll = () => {
    if (typeof window !== 'undefined' && !window.confirm(
      'Remove every requirement from the table? This cannot be undone.'
    )) return
    clearRequirements()
    setSyncState('idle')
    setSyncMsg('Cleared by user')
  }

  // ── SMART refinement handler (Sprint 17.7) ───────────────────────
  // Builds the source text from the row (prefer the derived 3 Cs
  // sentence so the engine refines what the table actually displays),
  // tracks loading/error state in the store, and lets the user choose
  // to Apply or Dismiss the suggestion.
  const handleRefineRow = useCallback(async req => {
    if (!req?.id) return
    const meta = requirementMeta[req.id] ?? {}
    const cap  = (meta.capability ?? '').trim()
    const cond = (meta.condition  ?? '').trim()
    const cons = (meta.constraint ?? '').trim()
    // Reconstruct the visible sentence the same way the row renders
    // it (capability + when … + per/within …).
    const derived = [cap, cond, cons].filter(Boolean).join(' ').trim()
    const sourceText = (
      derived
      || req.statement
      || ''
    ).trim()
    if (!sourceText) {
      setRefinementError(req.id, 'Add some text to the row first')
      return
    }
    setRefinementLoading(req.id)
    try {
      const result = await fetchSmartRefinement({
        reqId:     req.id,
        statement: sourceText,
        category:  meta.requirement_type === 'Non-Functional'
          ? 'non_functional' : 'general',
      })
      setRefinementSuggestion(req.id, result)
    } catch (exc) {
      setRefinementError(req.id, exc?.message ?? String(exc))
    }
  }, [
    requirementMeta,
    setRefinementError, setRefinementLoading, setRefinementSuggestion,
  ])

  const handleApplyRefinement = id => {
    applyRefinementSuggestion(id)
    setSyncState('live')
    setSyncMsg('SMART refinement applied — Capability cell updated')
    setPhaseComplete('requirements')
  }

  const handleDismissRefinement = id => {
    clearRefinement(id)
  }

  // The table iterates over `filteredRequirements`; in workshop mode
  // when nothing has been generated yet we fall back to seed data so
  // testers see the editor populated. In manual mode that fallback
  // is a UX trap (the seed rows aren't editable / removable safely),
  // so we render an empty list and let the empty-state CTA take over.
  const activeURs = activeRequirements.filter(r => r.type === 'UR')

  const activeMode = MODES.find(m => m.id === mode)

  return (
    <div className="flex flex-col h-full bg-bg-base">

      {/* ── Sprint 35.6 UX diet: one clean header replaces the old
            three stacked strips (sync bar + notice strip + roadmap
            banner). First-paint actionable controls: mode picker (1
            segmented control) + ⋯ More menu (1) + counts (label).
            Sync status is a small inline dot, not a bordered bar. ─ */}
      <div className="flex items-center gap-3 px-6 py-2.5
                      border-b border-border-base bg-bg-base shrink-0">

        <h1 className="text-sm font-semibold text-text-primary">
          Requirements
        </h1>

        {/* Inline sync status — dot + state word only. Click to re-sync. */}
        {(() => {
          const isLive    = syncState === 'live'
          const isErr     = syncState === 'error'
          const isSyncing = syncState === 'syncing'
          const dotColor  = isLive ? '#32CD32'
            : isErr   ? '#ef4444'
            : '#94a3b8'
          const label = isSyncing ? 'Syncing…'
            : isLive  ? 'Live'
            : isErr   ? 'Offline'
            : 'Seed'
          const tooltip = [
            syncMsg,
            lastSynced
              ? `Synced ${lastSynced.toLocaleTimeString([], {
                  hour: '2-digit', minute: '2-digit',
                })}`
              : null,
            'Click to re-sync',
          ].filter(Boolean).join(' · ')
          return (
            <button
              onClick={doSync}
              disabled={isSyncing}
              title={tooltip}
              className="flex items-center gap-1.5 text-[10px]
                         text-text-muted hover:text-text-secondary
                         transition-colors disabled:opacity-40"
            >
              <span
                className="w-1.5 h-1.5 rounded-full shrink-0"
                style={{
                  background: dotColor,
                  animation: isSyncing ? 'pulse 1s infinite' : 'none',
                }}
              />
              {label}
            </button>
          )
        })()}

        {/* Segmented mode picker — replaces three separate buttons in
            an overflow-hidden bordered div. Pill shape with a single
            active fill so the picker reads as "one control". */}
        <div
          role="tablist"
          aria-label="Requirements intake mode"
          className="flex items-center bg-bg-elev rounded-full p-0.5
                     border border-border-base"
        >
          {MODES.map(m => {
            const active = mode === m.id
            return (
              <button
                key={m.id}
                role="tab"
                aria-selected={active}
                onClick={() => handleModeChange(m.id)}
                className={`
                  text-[10px] font-medium px-3 py-1 rounded-full
                  transition-all
                  ${active
                    ? 'bg-bg-card text-text-primary shadow-sm'
                    : 'text-text-muted hover:text-text-secondary'}
                `}
              >
                {m.label}
              </button>
            )
          })}
        </div>

        <span className="text-text-muted text-[11px] hidden xl:inline
                         truncate max-w-md">
          {activeMode.sublabel}
        </span>

        <div className="ml-auto flex items-center gap-2">
          <span className="text-[10px] text-text-muted whitespace-nowrap">
            <strong className="text-text-secondary">{urCount}</strong> UR
            {urCount !== 1 ? 's' : ''}
            {' · '}
            <strong className="text-text-secondary">{frCount}</strong> FR
            {frCount !== 1 ? 's' : ''}
          </span>

          {/* ⋯ More menu — sync controls + seed reset + legacy link */}
          <div className="relative" ref={moreRef}>
            <button
              onClick={() => setMoreOpen(o => !o)}
              aria-label="More actions"
              aria-expanded={moreOpen}
              className="w-7 h-7 flex items-center justify-center
                         rounded text-text-muted
                         hover:bg-bg-hover hover:text-text-secondary
                         transition-colors"
            >
              <span className="text-base leading-none">⋯</span>
            </button>
            {moreOpen && (
              <div
                className="absolute right-0 top-full mt-1 z-20
                           min-w-[220px] py-1
                           bg-bg-card border border-border-base
                           rounded-lg shadow-lg text-[11px]"
              >
                {/* Sprint 35.6 Step A — view mode toggles. Default
                    state is calm Statement view + AI Sidekick off so
                    the page is inviting. Power users flip these on. */}
                <div className="px-3 py-1 text-[9px] uppercase
                                tracking-wider text-text-muted/60
                                font-semibold">
                  View
                </div>
                <button
                  onClick={() => setShowCs(v => !v)}
                  className="w-full text-left px-3 py-1.5
                             text-text-secondary hover:bg-bg-hover
                             transition-colors flex items-center
                             justify-between"
                >
                  <span>
                    {showCs ? '✓ ' : ''}Show 3 Cs editor
                  </span>
                  <span className="text-text-muted text-[9px]">
                    {showCs ? 'on' : 'statement only'}
                  </span>
                </button>
                <button
                  onClick={() => setShowAdvisories(v => !v)}
                  className="w-full text-left px-3 py-1.5
                             text-text-secondary hover:bg-bg-hover
                             transition-colors flex items-center
                             justify-between"
                >
                  <span>
                    {showAdvisories ? '✓ ' : ''}Show AI Sidekick
                  </span>
                  <span className="text-text-muted text-[9px]">
                    {showAdvisories ? 'on' : 'off'}
                  </span>
                </button>

                <div className="border-t border-border-base my-1" />
                <div className="px-3 py-1 text-[9px] uppercase
                                tracking-wider text-text-muted/60
                                font-semibold">
                  Data
                </div>
                <button
                  onClick={() => { setMoreOpen(false); doSync() }}
                  disabled={syncState === 'syncing'}
                  className="w-full text-left px-3 py-1.5
                             text-text-secondary hover:bg-bg-hover
                             transition-colors disabled:opacity-40"
                >
                  ↻ Re-sync from EVOLV
                </button>
                {requirements.length > 0 && (
                  <button
                    onClick={() => {
                      setMoreOpen(false)
                      setRequirements([])
                      setSyncState('idle')
                      setSyncMsg('')
                      setLastSynced(null)
                    }}
                    className="w-full text-left px-3 py-1.5
                               text-text-secondary hover:bg-bg-hover
                               transition-colors"
                  >
                    🌱 Reset to seed data
                  </button>
                )}
                <div className="border-t border-border-base my-1" />
                <a
                  href="http://localhost:8501/?page=requirements"
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => setMoreOpen(false)}
                  className="block px-3 py-1.5
                             text-text-muted hover:bg-bg-hover
                             hover:text-text-secondary transition-colors"
                >
                  ↗ Open legacy Streamlit
                </a>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Body ────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-auto px-6 py-4">

        {/* Sprint 35.6 UX diet: removed Sprint 17 roadmap banner —
            it was internal dev signaling that doesn't belong on a
            customer-facing surface. The Sprint 17 work is complete
            and recorded in CLAUDE.md + MEMORY.md for traceability. */}

        {/* Brief intake (Sprint 34) — single textarea front door,
            same backend as Workshop. Reuses the workshop busy/status
            slots so the status pill renders in the same place. */}
        {mode === 'brief' && (
          <BriefIntake
            onGenerated={handleWorkshopGenerated}
            busy={workshopBusy}
            setBusy={setWorkshopBusy}
            status={workshopStatus}
            setStatus={setWorkshopStatus}
          />
        )}

        {/* Workshop intake (Sprint 17.4) — only in workshop mode */}
        {mode === 'workshop' && (
          <WorkshopIntake
            onGenerated={handleWorkshopGenerated}
            busy={workshopBusy}
            setBusy={setWorkshopBusy}
            status={workshopStatus}
            setStatus={setWorkshopStatus}
          />
        )}

        {/* Manual-authoring toolbar (Sprint 17.6) — only in manual mode */}
        {mode === 'manual' && (
          <ManualAuthoringToolbar
            urs={activeURs}
            requirementCount={requirements.length}
            onAddUR={handleAddUR}
            onAddFR={handleAddFR}
            onClearAll={handleClearAll}
          />
        )}

        {/* Empty-state CTA — manual mode with no rows yet */}
        {mode === 'manual' && requirements.length === 0 && (
          <ManualEmptyState onAddUR={handleAddUR} />
        )}

        {/* Section-grouping preview (Sprint 17.3) — counts drive export */}
        {(() => {
          const classCount = REQUIREMENT_TYPES.reduce((acc, t) => {
            acc[t.value] = activeRequirements.filter(
              r => (requirementMeta[r.id]?.requirement_type) === t.value
            ).length
            return acc
          }, {})
          const ownerCount = STAKEHOLDERS.reduce((acc, s) => {
            acc[s.value] = activeRequirements.filter(
              r => (requirementMeta[r.id]?.stakeholder) === s.value
            ).length
            return acc
          }, {})
          const unassigned = activeRequirements.filter(
            r => !requirementMeta[r.id]?.requirement_type
          ).length
          return (
            <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1.5
                            text-[10px]">
              <span className="font-semibold uppercase tracking-wide
                               text-text-muted">
                Sections (drives export grouping):
              </span>

              {/* Class chips */}
              {REQUIREMENT_TYPES.map(t => (
                <span key={t.value}
                      className="flex items-center gap-1 text-text-secondary">
                  <span className="font-mono text-text-muted">{t.short}</span>
                  <strong>{classCount[t.value]}</strong>
                  <span className="text-text-muted">{t.label}</span>
                </span>
              ))}
              {unassigned > 0 && (
                <span className="text-amber-DEFAULT font-medium">
                  ⚠ {unassigned} unassigned
                </span>
              )}

              <span className="text-text-muted/40">·</span>

              {/* Owner chips */}
              {STAKEHOLDERS.filter(s => ownerCount[s.value] > 0).map(s => (
                <span
                  key={s.value}
                  className="px-1.5 py-0.5 rounded font-medium border"
                  style={{
                    background: STAKEHOLDER_COLOR[s.value] + '14',
                    color:      STAKEHOLDER_COLOR[s.value],
                    borderColor: STAKEHOLDER_COLOR[s.value] + '40',
                  }}
                >
                  {s.label} <strong>{ownerCount[s.value]}</strong>
                </span>
              ))}
            </div>
          )
        })()}

        {/* Sprint 35.6 Step A: AI Sidekick aggregate rail gated on
            showAdvisories. Off by default — the rail is information-
            dense and competed with the table for attention. Power
            users toggle it on from the ⋯ More menu. */}
        {showAdvisories && (
        <div
          className="mb-3 px-3 py-2 rounded border flex flex-wrap items-center
                     gap-x-3 gap-y-1.5 text-[10px]"
          style={{
            background: sidekickSummary.totalFlags === 0
              ? 'rgba(50,205,50,0.05)'
              : 'rgba(0,127,255,0.04)',
            borderColor: sidekickSummary.totalFlags === 0
              ? 'rgba(50,205,50,0.25)'
              : 'rgba(0,127,255,0.20)',
          }}
        >
          <span className="font-semibold uppercase tracking-wide
                           text-blue-DEFAULT flex items-center gap-1">
            🪄 AI Sidekick
          </span>
          <span className="text-text-muted">
            <strong className="text-text-secondary">
              {sidekickSummary.cleanRows}
            </strong>{' '}
            clean ·{' '}
            <strong className="text-text-secondary">
              {sidekickSummary.rowsWithFlags}
            </strong>{' '}
            flagged ·{' '}
            <strong className="text-text-secondary">
              {sidekickSummary.totalFlags}
            </strong>{' '}
            finding{sidekickSummary.totalFlags === 1 ? '' : 's'}
          </span>

          {sidekickSummary.totalFlags === 0 ? (
            <span
              className="px-2 py-0.5 rounded-full font-semibold border
                         flex items-center gap-1"
              style={{
                background: 'rgba(50,205,50,0.10)',
                color:      '#32CD32',
                borderColor: 'rgba(50,205,50,0.35)',
              }}
            >
              ✓ all rows audit-ready
            </span>
          ) : (
            <>
              {CATEGORY_ORDER
                .filter(c => sidekickSummary.byCategory[c.id] > 0)
                .map(c => {
                  const color = SEVERITY_COLORS[c.severity]
                  const isActive = activeFilter === c.id
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => setActiveFilter(
                        activeFilter === c.id ? null : c.id,
                      )}
                      className="inline-flex items-center gap-1
                                 px-2 py-0.5 rounded-full font-medium
                                 border transition-all hover:brightness-110"
                      style={{
                        background: isActive ? color + '2a' : color + '14',
                        color,
                        borderColor: isActive ? color : color + '4d',
                        boxShadow: isActive
                          ? `0 0 0 1px ${color}66 inset`
                          : 'none',
                      }}
                      title={
                        `${sidekickSummary.byCategory[c.id]} `
                        + `row${sidekickSummary.byCategory[c.id] === 1
                                  ? '' : 's'} `
                        + `flagged · click to filter`
                      }
                    >
                      <span>{c.label}</span>
                      <strong>{sidekickSummary.byCategory[c.id]}</strong>
                    </button>
                  )
                })}
              {activeFilter && (
                <button
                  onClick={() => setActiveFilter(null)}
                  className="text-text-muted hover:text-text-secondary
                             underline underline-offset-2"
                >
                  Clear filter
                </button>
              )}
            </>
          )}
          <span className="ml-auto text-text-muted/70 text-[10px]">
            Advisory chips · never gates save
          </span>
        </div>
        )}

        {/* Wide table — 3 Cs editor + class/owner (Sprint 17.2 / 17.3)
            + per-row delete column in manual mode (Sprint 17.6) */}
        <table className="w-full text-xs border-collapse table-fixed">
          <colgroup>
            <col style={{ width: '56px'  }} />{/* ID */}
            <col style={{ width: '52px'  }} />{/* Type */}
            <col style={{ width: '60px'  }} />{/* Parent */}
            <col style={{ width: '148px' }} />{/* Class (F/NF) */}
            <col style={{ width: '136px' }} />{/* Owner */}
            {/* Sprint 35.6 Step A: 3 Cs columns hidden by default —
                a single Statement column takes their place. Power
                users flip showCs in ⋯ More to see the editor. */}
            {showCs ? (
              <>
                <col style={{ width: 'auto' }} />{/* Capability */}
                <col style={{ width: 'auto' }} />{/* Condition */}
                <col style={{ width: 'auto' }} />{/* Constraint */}
              </>
            ) : (
              <col style={{ width: 'auto' }} />/* Statement */
            )}
            <col style={{ width: '76px'  }} />{/* Risk Level */}
            <col style={{ width: '108px' }} />{/* Test Strategy */}
            {mode === 'manual' && (
              <col style={{ width: '36px' }} />  /* Delete (manual) */
            )}
          </colgroup>
          <thead>
            <tr className="border-b border-border-base">
              {[
                'ID', 'Type', 'Parent',
                ['Class', 'Functional vs Non-Functional'],
                ['Owner', 'Stakeholder responsible'],
                // Sprint 35.6 Step A: conditional column set —
                // 3 Cs editor vs single Statement column.
                ...(showCs
                  ? [
                      ['Capability',
                       'WHAT the system does — solution-independent'],
                      ['Condition',
                       'WHEN / under what trigger or context'],
                      ['Constraint',
                       'Regulatory or measurable limit (optional)'],
                    ]
                  : [
                      ['Statement',
                       'The full "shall" sentence (audit-ready)'],
                    ]),
                'Risk Level',
                'Test Strategy',
                ...(mode === 'manual' ? [['', 'Delete row']] : []),
              ].map((h, i) => {
                const [label, hint] = Array.isArray(h) ? h : [h, null]
                return (
                  <th
                    key={i}
                    className="text-left text-[10px] font-semibold text-text-muted
                               uppercase tracking-wide py-2 pr-3 align-bottom"
                  >
                    {label}
                    {hint && (
                      <div className="font-normal normal-case tracking-normal
                                      text-[9px] text-text-muted/70 mt-0.5
                                      leading-snug">
                        {hint}
                      </div>
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {filteredRequirements.map(req => {
              const badge    = typeBadge(req.type)
              const meta     = requirementMeta[req.id] ?? {}
              const derived  = deriveStatement(meta, null)
              const hasCs    = !!(meta.capability || meta.condition
                              || meta.constraint)
              const findings = flagsByRow[req.id] ?? []

              return (
                <Fragment key={req.id}>
                  <tr
                    className="border-t border-border-base/50
                               hover:bg-bg-elev/20 transition-colors"
                  >
                    {/* ID */}
                    <td className="py-2 pr-3 align-top whitespace-nowrap
                                   text-text-secondary font-mono text-[11px]">
                      {req.id}
                    </td>
                    {/* Type */}
                    <td className="py-2 pr-3 align-top">
                      <span
                        className="inline-block px-1.5 py-0.5 rounded text-[10px]
                                   font-semibold uppercase tracking-wide border"
                        style={{
                          background: badge.bg,
                          color: badge.fg,
                          borderColor: badge.border,
                        }}
                      >
                        {req.type}
                      </span>
                    </td>
                    {/* Parent */}
                    <td className="py-2 pr-3 align-top whitespace-nowrap
                                   text-text-muted font-mono text-[11px]">
                      {req.parentId ?? '—'}
                    </td>
                    {/* Class — Functional / Non-Functional (17.3) */}
                    <td className="py-2 pr-3 align-top">
                      <InlineSelect
                        value={meta.requirement_type}
                        options={REQUIREMENT_TYPES}
                        placeholder="Select…"
                        onChange={v => {
                          setRequirementMeta(req.id, 'requirement_type', v)
                          setPhaseComplete('requirements')
                        }}
                      />
                    </td>
                    {/* Owner — Stakeholder (17.3) */}
                    <td className="py-2 pr-3 align-top">
                      <InlineSelect
                        value={meta.stakeholder}
                        options={STAKEHOLDERS}
                        placeholder="Select…"
                        onChange={v => {
                          setRequirementMeta(req.id, 'stakeholder', v)
                          setPhaseComplete('requirements')
                        }}
                      />
                      {meta.stakeholder && (
                        <span
                          className="inline-flex mt-1 px-1.5 py-0.5 rounded
                                     text-[9px] font-semibold border"
                          style={{
                            background: STAKEHOLDER_COLOR[meta.stakeholder]
                                          + '1a',  /* 10% alpha */
                            color:      STAKEHOLDER_COLOR[meta.stakeholder],
                            borderColor: STAKEHOLDER_COLOR[meta.stakeholder]
                                          + '4d',  /* 30% alpha */
                          }}
                        >
                          {meta.stakeholder}
                        </span>
                      )}
                    </td>
                    {/* Sprint 35.6 Step A: 3 Cs cells gated on showCs.
                        When off, a single Statement cell takes their
                        place (read-only display of the derived or
                        legacy statement — the audit-ready sentence). */}
                    {showCs ? (
                      <>
                        {/* Capability */}
                        <td className="py-2 pr-3 align-top">
                          <CsCell
                            value={meta.capability}
                            placeholder="register, track, and dispose of samples"
                            onChange={v => {
                              setRequirementMeta(req.id, 'capability', v)
                              setPhaseComplete('requirements')
                            }}
                          />
                        </td>
                        {/* Condition */}
                        <td className="py-2 pr-3 align-top">
                          <CsCell
                            value={meta.condition}
                            placeholder="upon physical sample receipt in the lab"
                            onChange={v => {
                              setRequirementMeta(req.id, 'condition', v)
                              setPhaseComplete('requirements')
                            }}
                          />
                        </td>
                        {/* Constraint */}
                        <td className="py-2 pr-3 align-top">
                          <CsCell
                            value={meta.constraint}
                            placeholder="within 30 s, with 21 CFR Part 11 e-sig (optional)"
                            optional
                            onChange={v => {
                              setRequirementMeta(req.id, 'constraint', v)
                              setPhaseComplete('requirements')
                            }}
                          />
                        </td>
                      </>
                    ) : (
                      /* Statement (read-only, calm default view) */
                      <td className="py-2 pr-3 align-top">
                        <p className="text-[11px] text-text-primary
                                      leading-relaxed">
                          {hasCs
                            ? (derived || <span className="text-text-muted">—</span>)
                            : (req.statement
                                ?? <span className="text-text-muted">—</span>)}
                        </p>
                        {findings.length > 0 && showAdvisories && (
                          <span className="inline-block mt-1 text-[9px]
                                           px-1.5 py-0.5 rounded
                                           bg-blue-DEFAULT/10
                                           text-blue-DEFAULT
                                           border border-blue-DEFAULT/30">
                            🪄 {findings.length} sidekick finding
                            {findings.length === 1 ? '' : 's'}
                          </span>
                        )}
                      </td>
                    )}
                    {/* Risk Level + Test Strategy — Sprint 35.6 Step A
                        wrap-up: read LIVE from riskData[req.id] (set on
                        the Risk page) instead of the non-existent
                        req.risk_level. When a row hasn't been ranked
                        yet, show a "Rank →" deep-link to the Risk
                        phase so the demo flow stays one click away. */}
                    {(() => {
                      const rd = riskData?.[req.id] ?? {}
                      const live = _calcRisk(rd.impact, rd.implMethod)
                      const strategy = rd.testAssurance
                        ?? (live ? _defaultTestStrategy(live) : null)
                      const tone = live === 'HIGH'   ? '#ef4444'
                                 : live === 'MEDIUM' ? '#f59e0b'
                                 : live === 'LOW'    ? '#32CD32'
                                 : null
                      return (
                        <>
                          {/* Risk Level */}
                          <td className="py-2 pr-3 align-top text-[11px]">
                            {live ? (
                              <span
                                className="font-semibold"
                                style={{ color: tone }}
                              >
                                {live.charAt(0)
                                  + live.slice(1).toLowerCase()}
                              </span>
                            ) : (
                              <button
                                type="button"
                                onClick={() => openTab?.('risk')}
                                className="text-[10px] text-blue-DEFAULT
                                           hover:underline transition-colors"
                                title="Open Risk phase to rank this requirement"
                              >
                                Rank →
                              </button>
                            )}
                          </td>
                          {/* Test Strategy */}
                          <td className="py-2 pr-3 align-top text-text-muted
                                         text-[11px] leading-snug">
                            {strategy ?? (
                              <span className="text-text-muted/60">—</span>
                            )}
                          </td>
                        </>
                      )
                    })()}
                    {/* Delete row (manual mode only — Sprint 17.6) */}
                    {mode === 'manual' && (
                      <td className="py-2 align-top text-center">
                        <button
                          type="button"
                          onClick={() => handleRemoveRequirement(req.id)}
                          className="w-6 h-6 inline-flex items-center
                                     justify-center rounded
                                     text-text-muted hover:text-red-DEFAULT
                                     hover:bg-red-DEFAULT/10
                                     transition-colors text-[14px]
                                     leading-none"
                          title={req.type === 'UR'
                            ? `Remove ${req.id} and all its child FRs`
                            : `Remove ${req.id}`}
                          aria-label={`Remove ${req.id}`}
                        >
                          ×
                        </button>
                      </td>
                    )}
                  </tr>

                  {/* Sprint 35.6 Step A: derived/legacy preview row
                      only rendered in 3 Cs editor mode (showCs=true).
                      When the Statement column is visible in the main
                      row, this preview is redundant and just adds
                      noise. Keeps the table calm in default view. */}
                  {showCs && (
                    <tr className="bg-bg-card/40">
                      <td colSpan={3}
                          className="py-1 pr-3 align-top
                                     text-[9px] uppercase tracking-wide
                                     text-text-muted/70 font-semibold text-right">
                        {hasCs ? '→ Derived' : 'Legacy'}
                      </td>
                      <td colSpan={5}
                          className="py-1 pr-3 align-top
                                     text-[11px] text-text-muted italic
                                     leading-relaxed">
                        {hasCs
                          ? (derived || <span>—</span>)
                          : (req.statement ?? '—')}
                      </td>
                    </tr>
                  )}

                  {/* AI Sidekick chips — Sprint 35.6 Step A: gated on
                      showAdvisories. Off by default to keep the table
                      calm. When on, flagged rows surface category
                      chips + a Refine button; clean rows show a green
                      "audit-ready" pill as positive feedback. */}
                  {showAdvisories && (
                    <tr className="bg-bg-card/20 border-b border-border-base/30">
                      <td colSpan={3}
                          className="py-1 pr-3 align-top
                                     text-[9px] uppercase tracking-wide
                                     font-semibold text-right"
                          style={{ color: findings.length ? '#007FFF' : '#32CD32' }}
                      >
                        🪄 Sidekick
                      </td>
                      <td colSpan={mode === 'manual'
                                    ? (showCs ? 8 : 6)
                                    : (showCs ? 7 : 5)}
                          className="py-1 pr-3 align-top">
                        <PatternChipRow
                          findings={findings}
                          refineSlot={
                            findings.length > 0
                              ? (
                                <RefineButton
                                  status={
                                    requirementRefinements[req.id]?.status
                                      ?? 'idle'
                                  }
                                  disabled={
                                    !((meta.capability ?? req.statement ?? '')
                                        .trim())
                                  }
                                  onClick={() => handleRefineRow(req)}
                                />
                              )
                              : null
                          }
                        />
                      </td>
                    </tr>
                  )}

                  {/* Refinement panel (Sprint 17.7) — only when the
                      engine has returned a suggestion or errored for
                      this row. Spans the full width below the chips. */}
                  {(() => {
                    const refState = requirementRefinements[req.id]
                    if (!refState
                        || (refState.status !== 'ready'
                            && refState.status !== 'error')) {
                      return null
                    }
                    return (
                      <tr className="border-b border-border-base/30">
                        <td className="py-0"></td>
                        <td colSpan={mode === 'manual' ? 10 : 9}
                            className="px-3 py-2 align-top">
                          <RefinementPanel
                            suggestion={refState.suggestion}
                            error={
                              refState.status === 'error'
                                ? refState.error
                                : null
                            }
                            onApply={() => handleApplyRefinement(req.id)}
                            onDismiss={() => handleDismissRefinement(req.id)}
                          />
                        </td>
                      </tr>
                    )
                  })()}
                </Fragment>
              )
            })}
          </tbody>
        </table>

        {/* Sprint 35.6 UX diet: removed Sprint-17-era explainer block
            below the table. It contained (1) a 3 Cs schema legend, (2)
            two large "Flow A / Flow B" preview cards with Sprint refs +
            function names (`transform_urs_to_ur_fr()`) + ✓ Live ↑
            badges, and (3) a Schema-contract paragraph. All three were
            internal documentation that shipped to the customer surface.
            Removed; column headers + hover tooltips carry the meaning
            without the noise. ~128 lines deleted. */}

      </div>
    </div>
  )
}
