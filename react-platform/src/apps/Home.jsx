/**
 * Home — LaunchPad command centre.
 *
 * Sprint 8: Live stats from Zustand, lifecycle progress ring,
 * contextual "next action" banner, and project health panel.
 *
 * Bento grid (4-column):
 *   [Verify — 2×2]  [Requirements — 1×1]  [Navigator — 1×1]
 *   [Academy — 1×2] [Risk — 1×1]           [Monitor — 1×2]
 *                   [Impact Analytics — 1×1]
 */
import { useState, useMemo, useRef, useEffect } from 'react'
import { APPS }         from '../data/apps.js'
import { useAppStore,
         LIFECYCLE_PHASES } from '../store/useAppStore.js'
import { DEMO_PROJECT_META } from '../data/demoProject.js'
import { V_NODES, V_PATH }   from '../shell/vmodelGeometry.js'

// ── Sprint 31 — Copilot-style intent routing ────────────────────
// Pharma QA pros land on Home and ask "where do I start?". The
// chat-input hero gives them one front door — they describe what
// they want, and we deterministically route to the matching app.
//
// Order matters: the FIRST entry whose keyword matches wins, so
// list more-specific intents (audit, traceability) before broader
// ones (verify, plan).
const ROUTE_KEYWORDS = [
  ['audit-trail',         ['audit trail', 'audit log', 'inspector', 'inspect',
                           '21 cfr part 11 trail', 'reasoning hash']],
  ['traceability-matrix', ['traceability', 'rtm', 'trace matrix']],
  ['regulatory-watch',    ['regulatory change', 'regulatory update',
                           'new regulation', 'fda guidance', 'ema',
                           'reg watch']],
  ['governance',          ['governance', 'hitl', 'human in the loop',
                           'override', 'ai decision queue']],
  ['portfolio',           ['portfolio', 'inventory', 'estate', 'rag status',
                           'all systems']],
  ['system-journey',      ['journey', 'lifecycle flow', 'timeline view']],
  ['impact-analytics',    ['impact', 'roi', 'savings', 'comparison']],
  ['docs',                ['docs', 'documentation', 'glossary', 'help me',
                           'how do i']],
  ['academy',             ['academy', 'training', 'tutorial', 'walkthrough',
                           'learn']],
  ['dev-portal',          ['api', 'webhook', 'sandbox', 'dev portal']],
  ['config',              ['config', 'tenant', 'site', 'abac', 'policy']],
  // Lifecycle phases (more specific keywords first)
  ['plan',                ['plan', 'start a new', 'new project', 'kick off',
                           'kick-off', 'new validation', 'gamp category',
                           'vmp', 'validation master plan']],
  ['requirements',        ['requirement', 'urs', 'business story',
                           'user story', 'gxp control', 'smart req']],
  ['risk',                ['risk', 'fmea', 'gap analysis', 'rpn',
                           'patient safety', 'severity']],
  ['design',              ['design', 'sds', 'hld', 'lld', 'test author',
                           'configuration spec', 'test bundle']],
  ['verify',              ['verify', 'execute', 'test execution',
                           'run script', 'continue testing', 'pass/fail',
                           'evidence', 'sign off run']],
  ['release',             ['release', 'go live', 'go-live', 'approver',
                           'multi-approver', 'approval', 'release gate']],
  ['monitor',             ['monitor', 'operations', 'change request',
                           'deviation', 'system health']],
  ['retire',              ['retire', 'decommission', 'archive',
                           'sunset']],
]

function routeIntent(text) {
  const t = text.toLowerCase().trim()
  if (!t) return null
  for (const [appId, keywords] of ROUTE_KEYWORDS) {
    if (keywords.some(k => t.includes(k))) return appId
  }
  // Fallback — open Requirements (most natural-language asks
  // route to "I want the system to do X")
  return 'requirements'
}

// Bento grid slot config — [appId, colSpan, rowSpan, extraClass]
const BENTO = [
  ['verify',           2, 2, 'bento-hero-bg lime'],
  ['requirements',     1, 1, ''],
  ['navigator',        1, 1, ''],
  ['monitor',          1, 2, ''],
  ['risk',             1, 1, ''],
  ['impact-analytics', 1, 1, ''],
  ['docs',             1, 1, ''],
]

// Phase config for progress ring label
const PHASE_META = [
  { id: 'plan',         label: 'Plan',         emoji: '📋' },
  { id: 'requirements', label: 'Requirements',  emoji: '📝' },
  { id: 'risk',         label: 'Risk',          emoji: '⚖️' },
  { id: 'design',       label: 'Design',        emoji: '🎨' },
  { id: 'verify',       label: 'Verify',        emoji: '🏭' },
  { id: 'release',      label: 'Release',       emoji: '📄' },
  { id: 'monitor',      label: 'Monitor',       emoji: '📡' },
  { id: 'retire',       label: 'Retire',        emoji: '🔒' },
]

// ── Sprint 32 — V-model node geometry ────────────────────────────
// V_NODES + V_PATH are now imported from `shell/vmodelGeometry.js`
// (Sprint 33) so the Home hero and the persistent LifecycleStrip
// spine share a single source of truth. Both components show the
// same 8 phases in the same V-shape — the V-model is the platform's
// visual spine, not just a Home decoration.

// Sprint 32.3 — natural-language "what's next" router. Matches
// patterns like "what's next", "where am I", "next phase",
// "continue", "resume". When the user types one of these in the
// HeroPrompt, we look up the active project's first incomplete
// phase from the store rather than going through ROUTE_KEYWORDS.
const NEXT_PATTERNS = /\b(what'?s?\s+next|where\s+am\s+i|next\s+(phase|step)|continue|pick\s+up|resume|what\s+should\s+i\s+do)\b/i

// Next-action suggestions keyed by the FIRST incomplete phase
const NEXT_ACTION = {
  plan:         { msg: 'Start with Plan — define your project and GAMP 5 category.',  appId: 'plan' },
  requirements: { msg: 'Plan complete — generate your URS in Requirements.',           appId: 'requirements' },
  risk:         { msg: 'Requirements done — run risk profiling in Risk.',              appId: 'risk' },
  design:       { msg: 'Risk complete — capture your design specs.',                   appId: 'design' },
  verify:       { msg: 'Design approved — execute CSA test scripts in Verify.',        appId: 'verify' },
  release:      { msg: 'Verify signed off — complete multi-approver sign-off.',        appId: 'release' },
  monitor:      { msg: 'System released! Review your audit trail in Monitor.',         appId: 'monitor' },
  retire:       { msg: 'All lifecycle phases complete. System is in validated state.', appId: null },
}

// ── Minimal stroke SVG icons (currentColor, no fill) ─────────────
const ICONS = {
  verify: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      <path d="M9 12l2 2 4-4"/>
    </svg>
  ),
  requirements: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/>
      <rect x="9" y="3" width="6" height="4" rx="1"/>
      <path d="M9 12h6M9 16h4"/>
    </svg>
  ),
  navigator: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <circle cx="12" cy="12" r="10"/>
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
    </svg>
  ),
  monitor: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>
  ),
  risk: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  ),
  'impact-analytics': (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <line x1="18" y1="20" x2="18" y2="10"/>
      <line x1="12" y1="20" x2="12" y2="4"/>
      <line x1="6"  y1="20" x2="6"  y2="14"/>
      <line x1="2"  y1="20" x2="22" y2="20"/>
    </svg>
  ),
  docs: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
    </svg>
  ),
  plan: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <rect x="8" y="2" width="8" height="4" rx="1"/>
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
      <path d="M9 12h6M9 16h4"/>
    </svg>
  ),
  // Stat card icons
  stat_reqs: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <line x1="8" y1="6" x2="21" y2="6"/>
      <line x1="8" y1="12" x2="21" y2="12"/>
      <line x1="8" y1="18" x2="21" y2="18"/>
      <line x1="3" y1="6" x2="3.01" y2="6"/>
      <line x1="3" y1="12" x2="3.01" y2="12"/>
      <line x1="3" y1="18" x2="3.01" y2="18"/>
    </svg>
  ),
  stat_scripts: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <polyline points="9 11 12 14 22 4"/>
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
    </svg>
  ),
  stat_approvals: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="9" y1="15" x2="15" y2="15"/>
      <line x1="12" y1="12" x2="12" y2="18"/>
    </svg>
  ),
  stat_project: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <polygon points="12 2 2 7 12 12 22 7 12 2"/>
      <polyline points="2 17 12 22 22 17"/>
      <polyline points="2 12 12 17 22 12"/>
    </svg>
  ),
  shield: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      <path d="M9 12l2 2 4-4"/>
    </svg>
  ),
  cpu: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
         strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
      <rect x="4" y="4" width="16" height="16" rx="2"/>
      <rect x="9" y="9" width="6" height="6"/>
      <line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/>
      <line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/>
      <line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/>
      <line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>
    </svg>
  ),
}

function AppIcon({ id, size = 'md', color }) {
  const sz = size === 'lg' ? 'w-12 h-12' : size === 'sm' ? 'w-4 h-4' : 'w-8 h-8'
  return (
    <div className={`${sz} shrink-0`} style={{ color }}>
      {ICONS[id] ?? ICONS.docs}
    </div>
  )
}

// ── Progress ring (SVG) ───────────────────────────────────────────
function ProgressRing({ done, total }) {
  const r   = 36
  const circ = 2 * Math.PI * r
  const pct  = total > 0 ? done / total : 0
  const dash = pct * circ
  const color = pct === 1 ? '#32CD32' : pct >= 0.5 ? '#007FFF' : '#f59e0b'

  return (
    <svg width="92" height="92" viewBox="0 0 92 92" className="shrink-0">
      {/* Track */}
      <circle
        cx="46" cy="46" r={r}
        fill="none"
        style={{ stroke: 'var(--ring-track)' }}
        strokeWidth="8"
      />
      {/* Progress arc */}
      <circle
        cx="46" cy="46" r={r}
        fill="none"
        stroke={color}
        strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray={`${dash} ${circ}`}
        strokeDashoffset={circ / 4}   /* start at 12 o'clock */
        style={{ filter: `drop-shadow(0 0 6px ${color}88)`,
                 transition: 'stroke-dasharray 0.5s ease' }}
      />
      {/* Label */}
      <text x="46" y="42" textAnchor="middle" fill={color}
            fontSize="16" fontWeight="700" fontFamily="Inter,sans-serif">
        {done}
      </text>
      <text x="46" y="58" textAnchor="middle" fill="rgba(255,255,255,0.35)"
            fontSize="9" fontFamily="Inter,sans-serif">
        / {total} phases
      </text>
    </svg>
  )
}

// ── Live stat card ────────────────────────────────────────────────
function StatCard({ label, value, sub, color, icon }) {
  return (
    <div className="glass rounded-xl p-4 flex items-start gap-3">
      <div className="w-5 h-5 shrink-0 mt-0.5" style={{ color }}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[10px] text-text-muted uppercase tracking-wide mb-0.5">
          {label}
        </p>
        <p className="text-xl font-bold leading-none" style={{ color }}>
          {value}
        </p>
        {sub && (
          <p className="text-[10px] text-text-muted mt-1 truncate">{sub}</p>
        )}
      </div>
    </div>
  )
}

// ── Project switcher strip ────────────────────────────────────────
function ProjectsSwitcher({
  projects, activeProjectId, phaseCompletion,
  onSwitch, onCreate, onDelete, onLoadDemo,
}) {
  const [creating, setCreating] = useState(false)
  const [newName,  setNewName]  = useState('')

  const projectList   = Object.values(projects)
  const activeProj    = projects[activeProjectId]
  const otherProjects = projectList.filter(p => p.id !== activeProjectId)
  const activeDone    = Object.values(phaseCompletion).filter(Boolean).length
  const demoLoaded    = Boolean(projects[DEMO_PROJECT_META.id])
  const onDemo        = activeProjectId === DEMO_PROJECT_META.id

  const handleDemoClick = () => {
    if (onDemo) {
      // Already on demo — offer reset
      const ok = window.confirm(
        'Reset the LabCore demo to its pristine seeded state?\n\n'
        + 'Any test runs, defects, or sign-offs you added on the '
        + 'demo will be cleared.',
      )
      if (ok) onLoadDemo()
      return
    }
    const verb = demoLoaded ? 'Switch back to' : 'Load'
    const ok = window.confirm(
      `${verb} the LabCore LIMS v4.2 Migration demo?\n\n`
      + 'A pre-populated mid-flight CSV project will be loaded so '
      + 'you can walk Plan → Requirements → Risk → Design → '
      + 'Verify → Release end-to-end.\n\n'
      + 'Your current project will be saved and remains available '
      + 'in the project switcher.',
    )
    if (ok) onLoadDemo()
  }

  const handleCreate = () => {
    if (!newName.trim()) return
    onCreate(newName.trim())
    setNewName('')
    setCreating(false)
  }

  return (
    <div className="flex items-center gap-2 flex-wrap mb-5">

      {/* Active project chip */}
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg
                      border border-blue-DEFAULT/30 bg-blue-dim shrink-0">
        <span className="w-1.5 h-1.5 rounded-full bg-blue-DEFAULT
                         animate-pulse shrink-0" />
        <span className="text-xs font-semibold text-blue-DEFAULT">
          {activeProj?.name ?? 'Default Project'}
        </span>
        <span className="text-[9px] text-text-muted">
          {activeDone}/8 phases
        </span>
      </div>

      {/* Other project chips */}
      {otherProjects.map(proj => {
        const done = Object.values(
          proj.data?.phaseCompletion ?? {}
        ).filter(Boolean).length
        return (
          <button
            key={proj.id}
            onClick={() => onSwitch(proj.id)}
            className="group flex items-center gap-2 px-3 py-1.5 rounded-lg
                       border border-border-base bg-bg-card shrink-0
                       hover:border-border-bright transition-colors"
          >
            <span className="text-xs text-text-secondary
                             group-hover:text-text-primary transition-colors">
              {proj.name}
            </span>
            <span className="text-[9px] text-text-muted">{done}/8</span>
            <span
              onClick={e => { e.stopPropagation(); onDelete(proj.id) }}
              className="text-text-muted hover:text-red-400 text-sm
                         opacity-0 group-hover:opacity-100 transition-opacity
                         leading-none ml-0.5"
              title="Delete project"
            >
              ×
            </span>
          </button>
        )
      })}

      {/* Load / reset demo project */}
      <button
        onClick={handleDemoClick}
        className={`
          flex items-center gap-1.5 px-3 py-1.5 rounded-lg shrink-0
          text-xs font-semibold transition-all
          ${onDemo
            ? 'border border-lime-DEFAULT/40 bg-lime-dim text-lime-DEFAULT'
            : 'border border-blue-DEFAULT/40 bg-blue-dim text-blue-DEFAULT '
              + 'hover:bg-blue-DEFAULT/15 hover:border-blue-DEFAULT/60'}
        `}
        title={onDemo
          ? 'Reset the demo project to its pristine state'
          : (demoLoaded
              ? 'Switch back to the LabCore LIMS demo'
              : 'Load a pre-populated end-to-end CSV project to '
                + 'explore the platform')}
      >
        <span aria-hidden>{onDemo ? '↺' : '★'}</span>
        <span>
          {onDemo
            ? 'Reset Demo'
            : demoLoaded
              ? 'Open Demo'
              : 'Load Demo Project'}
        </span>
      </button>

      {/* New project */}
      {creating ? (
        <div className="flex items-center gap-2">
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter')  handleCreate()
              if (e.key === 'Escape') { setCreating(false); setNewName('') }
            }}
            placeholder="Project name…"
            className="evolv-input text-xs px-2 py-1 w-44"
            autoFocus
          />
          <button
            onClick={handleCreate}
            className="px-3 py-1 text-xs rounded bg-blue-DEFAULT text-white
                       font-semibold hover:opacity-90 transition-opacity"
          >
            Create
          </button>
          <button
            onClick={() => { setCreating(false); setNewName('') }}
            className="text-[11px] text-text-muted hover:text-text-secondary"
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          onClick={() => setCreating(true)}
          className="flex items-center gap-1.5 text-[11px] text-text-muted
                     hover:text-text-secondary transition-colors px-2 py-1.5
                     rounded-lg border border-dashed border-border-base
                     hover:border-border-bright shrink-0"
        >
          + New Project
        </button>
      )}
    </div>
  )
}

// ── VModelHero — Sprint 32 animated phase-progress strip ────────
// A live status board that doubles as the brand visual. The SVG V
// curve sketches itself in once on first paint (~1.2s), then sits
// still as a clickable phase map. Each node is colour-coded by
// `phaseCompletion[id]`:
//   • lime    → done
//   • blue    → next incomplete phase (pulses)
//   • muted   → not started
//   • locked  → retire (when project hasn't been released yet)
//
// Click a node → opens that phase. Hover → tooltip with full label.
// The overlay below the curve names the active project + first
// incomplete phase in plain English.
function VModelHero({
  phaseCompletion, nextPhase, projectName, doneCount, totalPhases,
  onPhaseClick,
}) {
  const pathRef = useRef(null)
  const [pathLength, setPathLength] = useState(640)
  const [drawn,      setDrawn]      = useState(false)

  // Measure the actual path length once mounted, then trigger the
  // draw animation on the next frame. Two rAFs are necessary
  // because we need React to commit the dasharray=length /
  // dashoffset=length state before transitioning to dashoffset=0.
  useEffect(() => {
    if (pathRef.current) {
      setPathLength(pathRef.current.getTotalLength())
    }
    const r1 = requestAnimationFrame(() => {
      requestAnimationFrame(() => setDrawn(true))
    })
    return () => cancelAnimationFrame(r1)
  }, [])

  return (
    <div
      className="rounded-2xl bg-bg-card border border-border-base
                 px-6 py-5 mb-6"
      style={{ boxShadow: '0 1px 2px rgba(42,40,37,0.04)' }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3 min-w-0">
          <p className="text-[10px] uppercase tracking-[0.18em]
                        text-text-muted font-semibold">
            Lifecycle
          </p>
          {projectName && (
            <span className="text-xs text-text-secondary truncate">
              · {projectName}
            </span>
          )}
        </div>
        <span className="text-[11px] text-text-muted font-mono">
          {doneCount}/{totalPhases} complete
        </span>
      </div>

      <svg
        viewBox="0 0 720 170"
        preserveAspectRatio="xMidYMid meet"
        className="w-full h-auto"
        style={{ maxHeight: '180px' }}
      >
        <defs>
          <linearGradient id="v-grad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%"   stopColor="#007FFF" />
            <stop offset="50%"  stopColor="#32CD32" />
            <stop offset="100%" stopColor="#007FFF" />
          </linearGradient>
        </defs>

        {/* Track path — drawn first as a faint guide so the animated
            stroke has something to fill in over. */}
        <path
          d={V_PATH}
          fill="none"
          stroke="var(--border-base)"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Animated brand-gradient stroke — the headline visual. */}
        <path
          ref={pathRef}
          d={V_PATH}
          fill="none"
          stroke="url(#v-grad)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={pathLength}
          strokeDashoffset={drawn ? 0 : pathLength}
          style={{ transition: 'stroke-dashoffset 1.2s ease-out' }}
        />

        {/* Nodes — fade in sequentially after the path completes. */}
        {V_NODES.map((n, i) => {
          const done    = !!phaseCompletion?.[n.id]
          const active  = n.id === nextPhase
          const locked  = n.id === 'retire' && !phaseCompletion?.monitor
          const fill    = done   ? '#32CD32'
                        : active ? '#007FFF'
                        : locked ? 'var(--bg-card)'
                        :          'var(--bg-card)'
          const stroke  = done   ? '#32CD32'
                        : active ? '#007FFF'
                        : locked ? 'var(--border-base)'
                        :          'var(--border-base)'
          const labelClr = done || active
                        ? 'var(--text-primary)'
                        : 'var(--text-muted)'

          return (
            <g
              key={n.id}
              style={{
                opacity: drawn ? 1 : 0,
                transition: `opacity 0.45s ease-out ${i * 0.12 + 0.4}s`,
                cursor: locked ? 'not-allowed' : 'pointer',
              }}
              onClick={() => !locked && onPhaseClick?.(n.id)}
            >
              {/* Pulse halo for the active phase only. */}
              {active && (
                <circle
                  cx={n.x} cy={n.y} r="14"
                  fill="#007FFF" opacity="0.18"
                  className="animate-pulse"
                />
              )}
              {/* Main node */}
              <circle
                cx={n.x} cy={n.y} r="9"
                fill={fill}
                stroke={stroke}
                strokeWidth="2.5"
                style={{
                  filter: done || active
                    ? `drop-shadow(0 0 6px ${active ? '#007FFF' : '#32CD32'}80)`
                    : 'none',
                }}
              />
              {/* Tick mark on done nodes */}
              {done && (
                <path
                  d={`M ${n.x - 3.5},${n.y} L ${n.x - 1},${n.y + 2.5} L ${n.x + 4},${n.y - 2.5}`}
                  fill="none"
                  stroke="#fff"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}
              {/* Label — above for top-row nodes, below for apex. */}
              <text
                x={n.x}
                y={n.y > 130 ? n.y + 24 : n.y - 16}
                textAnchor="middle"
                fill={labelClr}
                fontSize="11"
                fontWeight={done || active ? '600' : '500'}
                fontFamily="Inter, sans-serif"
              >
                {n.short}
              </text>
              <title>
                {n.label}
                {' — '}
                {done ? 'Complete' : active ? 'In progress (next up)' : 'Not started'}
              </title>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

// ── HeroPrompt — Sprint 31 Copilot-style chat input ─────────────
// The headline interaction surface on Home. Three goals:
//   1. Answer the new-user question "where do I start?" with one
//      input box instead of 20 sidebar items.
//   2. Feel native to anyone arriving from Claude / ChatGPT.
//   3. Stay deterministic — every keystroke routes via a fixed
//      keyword map (see ROUTE_KEYWORDS), no LLM call, no surprises
//      in a demo. Falls back to Requirements when nothing matches.
//
// The 4 chips below the input are calibrated to the most common
// pharma QA tasks identified in April demos: start a project,
// continue testing, review portfolio, search the audit trail.
const SUGGESTIONS = [
  { label: 'Start a new validation',  hint: 'Plan',         appId: 'plan'         },
  { label: 'Continue test execution', hint: 'Verify',       appId: 'verify'       },
  { label: 'Review portfolio status', hint: 'Portfolio',    appId: 'portfolio'    },
  { label: 'Search the audit trail',  hint: 'Audit Trail',  appId: 'audit-trail'  },
]

function HeroPrompt({ userName, onRoute, nextPhase }) {
  const [text,     setText]     = useState('')
  const [focused,  setFocused]  = useState(false)
  const inputRef = useRef(null)

  // First-name greeting — falls back to the generic prompt copy.
  const firstName = (userName ?? '').trim().split(/\s+/)[0]
  const greeting = firstName
    ? `Hi ${firstName} — what do you want to validate today?`
    : 'What do you want to validate today?'

  // Auto-grow the textarea (max 5 rows) as the user types.
  useEffect(() => {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }, [text])

  const handleSubmit = e => {
    e?.preventDefault?.()
    const t = text.trim()
    if (!t) return
    // Sprint 32.3 — "what's next" / "where am I" / "continue" /
    // "resume" route to the active project's first incomplete
    // phase rather than going through ROUTE_KEYWORDS. Falls back
    // to the keyword router when no project state is available.
    if (NEXT_PATTERNS.test(t) && nextPhase) {
      onRoute(nextPhase, t)
      setText('')
      return
    }
    const target = routeIntent(t)
    if (!target) return
    onRoute(target, t)
    setText('')
  }

  const handleKeyDown = e => {
    // Enter submits; Shift+Enter inserts a newline (Claude/ChatGPT
    // convention — pharma QA pros recognise it from those tools).
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="mb-6">
      {/* Sprint 35.6 UX diet: removed the "GAMP 5 · CSA · 21 CFR Part 11
          · FDA AI Guidance 2026" credibility strip. EVOLV is FOR the
          regulated-pharma audience — users inside the platform already
          trust it's built for these frameworks. Showing the labels on
          Home was outsider-facing marketing copy that didn't earn its
          space on the surface a user sees every day. The chat input
          is the only thing that needs the eye on first paint. */}

      <h1 className="text-2xl md:text-3xl font-semibold text-text-primary
                     mb-5 tracking-tight">
        {greeting}
      </h1>

      {/* Chat-input card — gradient ring on focus is the brand
          accent (lime → blue, same as the EVOLV logo) so the focal
          point on first paint is unmistakably "EVOLV is AI". */}
      <form
        onSubmit={handleSubmit}
        className="relative rounded-2xl bg-bg-card border transition-all
                   duration-200"
        style={{
          borderColor: focused
            ? 'transparent'
            : 'var(--border-base)',
          boxShadow:   focused
            ? '0 0 0 1.5px #007FFF, 0 8px 32px rgba(0,127,255,0.10)'
            : '0 1px 2px rgba(42,40,37,0.04)',
          backgroundImage: focused
            ? 'linear-gradient(white,white), linear-gradient(135deg,#007FFF,#32CD32)'
            : 'none',
          backgroundOrigin: 'border-box',
          backgroundClip:   'padding-box, border-box',
        }}
      >
        <textarea
          ref={inputRef}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          rows={1}
          placeholder="Describe a system to validate, ask about a regulation, or jump to a phase…"
          className="w-full resize-none bg-transparent outline-none
                     text-text-primary text-sm leading-relaxed
                     placeholder:text-text-muted/70
                     px-5 pt-4 pb-2"
          style={{ minHeight: '52px' }}
        />

        {/* Footer row — keyboard hint + submit button */}
        <div className="flex items-center justify-between px-5 pb-3 pt-1">
          <span className="flex items-center gap-1.5 text-[10px]
                           text-text-muted">
            <kbd className="bg-bg-hover border border-border-base
                            rounded px-1.5 py-0.5 text-[9px] font-mono">
              ↵
            </kbd>
            to submit
            <span className="opacity-50">·</span>
            <kbd className="bg-bg-hover border border-border-base
                            rounded px-1.5 py-0.5 text-[9px] font-mono">
              ⇧↵
            </kbd>
            new line
          </span>

          <button
            type="submit"
            disabled={!text.trim()}
            title="Submit (Enter)"
            className="w-8 h-8 rounded-full flex items-center justify-center
                       transition-all disabled:opacity-30
                       disabled:cursor-not-allowed shrink-0"
            style={{
              background: text.trim()
                ? 'linear-gradient(135deg,#007FFF 0%,#32CD32 100%)'
                : 'var(--bg-hover)',
              color: text.trim() ? '#ffffff' : 'var(--text-muted)',
              boxShadow: text.trim()
                ? '0 4px 12px rgba(0,127,255,0.25)'
                : 'none',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor"
                    strokeWidth="1.8" strokeLinecap="round"
                    strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </form>

      {/* Suggestion chips — calibrated to top pharma QA tasks. */}
      <div className="flex flex-wrap gap-2 mt-3">
        {SUGGESTIONS.map(s => (
          <button
            key={s.appId}
            onClick={() => onRoute(s.appId, s.label)}
            className="group flex items-center gap-2 px-3 py-1.5 rounded-full
                       bg-bg-card border border-border-base
                       text-xs text-text-secondary
                       hover:border-blue-DEFAULT/40 hover:text-text-primary
                       hover:bg-bg-hover transition-all"
          >
            <span>{s.label}</span>
            <span className="text-[9px] text-text-muted
                             group-hover:text-blue-DEFAULT
                             border border-border-base rounded px-1.5
                             py-0.5 transition-colors">
              {s.hint}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────
export default function Home() {
  const {
    tabs, activeTabId, openTab, switchTab,
    phaseCompletion, requirements, testScripts,
    testRuns, activeRunId, releaseData, planData,
    riskData,
    projects, activeProjectId,
    createProject, switchProject, deleteProject,
    loadDemoProject,
    userProfile,
  } = useAppStore()

  const openTabIds = new Set(tabs.map(t => t.appId))

  const handleCardClick = appId => {
    if (openTabIds.has(appId)) switchTab?.(appId)
    else openTab(appId)
  }

  // ── Derived live stats ─────────────────────────────────────────
  const doneCount  = useMemo(
    () => LIFECYCLE_PHASES.filter(p => phaseCompletion[p]).length,
    [phaseCompletion],
  )
  const totalPhases = LIFECYCLE_PHASES.length

  const reqCount    = requirements.length
  const scriptCount = Object.keys(testScripts).length
  const runCount    = Object.keys(testRuns).length
  const approvals   = releaseData.approvals.length
  const released    = releaseData.released

  // Risk summary
  const riskRows    = Object.values(riskData)
  const highRisk    = riskRows.filter(r => r.riskLevel === 'High').length
  const medRisk     = riskRows.filter(r => r.riskLevel === 'Medium').length

  // Active test run
  const activeRun   = activeRunId ? testRuns[activeRunId] : null
  const testStatus  = activeRun?.status === 'locked' ? 'Signed Off'
                    : activeRun             ? 'In Progress'
                    : 'Not Started'

  // First incomplete phase → next action
  const nextPhase = useMemo(
    () => LIFECYCLE_PHASES.find(p => !phaseCompletion[p]),
    [phaseCompletion],
  )
  const nextAction = nextPhase ? NEXT_ACTION[nextPhase] : NEXT_ACTION['retire']

  const liveStats = [
    {
      label: 'Requirements',
      value: reqCount > 0 ? String(reqCount) : '—',
      sub:   reqCount > 0
        ? `${highRisk} high risk · ${medRisk} medium`
        : 'Run Requirements phase',
      color: reqCount > 0 ? '#32CD32' : '#64748b',
      icon:  ICONS.stat_reqs,
    },
    {
      label: 'Test Scripts',
      value: scriptCount > 0 ? String(scriptCount) : '—',
      sub:   runCount > 0
        ? `${runCount} run${runCount !== 1 ? 's' : ''} · ${testStatus}`
        : 'Run Verify phase',
      color: scriptCount > 0 ? '#007FFF' : '#64748b',
      icon:  ICONS.stat_scripts,
    },
    {
      label: 'Approvals',
      value: approvals > 0 ? String(approvals) : '—',
      sub:   released ? '✓ System Released'
           : approvals > 0 ? 'Pending go-live'
           : 'Run Release phase',
      color: released ? '#32CD32' : approvals > 0 ? '#f59e0b' : '#64748b',
      icon:  ICONS.stat_approvals,
    },
    {
      label: 'Project',
      value: planData.projectName || '—',
      sub:   planData.gampCategory
        ? `GAMP 5 Cat ${planData.gampCategory}`
        : 'Set in Plan phase',
      color: planData.projectName ? '#a855f7' : '#64748b',
      icon:  ICONS.stat_project,
    },
  ]

  return (
    <div className="h-full overflow-y-auto bg-bg-base">
      <div className="max-w-6xl mx-auto px-6 py-8">

        {/* ── Hero — Sprint 31 Copilot-style prompt ─────── */}
        {/* Sprint 31 replaces the old "EVOLV Platform" title +
            "EVOLV AI Active" badge with a chat-input front door.
            The AI is now implied by the interaction surface — no
            decorative badge needed. The standards strip moves
            inside HeroPrompt as a small uppercase line above the
            greeting (only compliance signal on Home after Sprint
            30 deleted the header pills). */}
        <HeroPrompt
          userName={userProfile?.name}
          onRoute={appId => handleCardClick(appId)}
          nextPhase={nextPhase}
        />
        <div className="neon-sep mb-6" />

        {/* ── Sprint 32 — V-model hero ──────────────────────
            Animated SVG curve (plays once on first paint) that
            doubles as a clickable phase-progress strip. Replaces
            the old "Lifecycle Progress" pills row in the health
            banner — the V-model itself shows phase status, so
            pills are redundant. */}
        <VModelHero
          phaseCompletion={phaseCompletion}
          nextPhase={nextPhase}
          projectName={projects?.[activeProjectId]?.name}
          doneCount={doneCount}
          totalPhases={totalPhases}
          onPhaseClick={handleCardClick}
        />

        {/* ── Project switcher ────────────────────────────── */}
        <ProjectsSwitcher
          projects={projects}
          activeProjectId={activeProjectId}
          phaseCompletion={phaseCompletion}
          onSwitch={switchProject}
          onCreate={createProject}
          onDelete={deleteProject}
          onLoadDemo={loadDemoProject}
        />

        {/* ── Project health banner — now ring + next action only.
            Phase pills moved up into VModelHero (Sprint 32). */}
        <div className="glass rounded-2xl p-5 mb-6 flex items-center gap-6">

          {/* Progress ring */}
          <ProgressRing done={doneCount} total={totalPhases} />

          {/* Next action CTA — wider now that phase pills are gone. */}
          <div className="flex-1 min-w-0">
            <p className="text-[10px] text-text-muted uppercase tracking-widest
                          mb-2 font-semibold">
              Next Action
            </p>
            <p className="text-sm text-text-secondary leading-relaxed mb-3">
              {nextAction.msg}
            </p>
            {nextAction.appId && (
              <button
                onClick={() => handleCardClick(nextAction.appId)}
                className="px-4 py-1.5 text-xs rounded-lg font-semibold
                           bg-blue-DEFAULT text-white hover:opacity-90
                           transition-opacity"
              >
                Go to {NEXT_ACTION[nextPhase]
                  ? PHASE_META.find(p => p.id === nextPhase)?.label
                  : 'Monitor'} →
              </button>
            )}
          </div>
        </div>

        {/* ── Live stats row ──────────────────────────────── */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          {liveStats.map(stat => (
            <StatCard key={stat.label} {...stat} />
          ))}
        </div>

        {/* ── Bento Grid ──────────────────────────────────── */}
        <div
          className="grid gap-3"
          style={{
            gridTemplateColumns: 'repeat(4, 1fr)',
            gridAutoRows: '160px',
          }}
        >
          {BENTO.map(([appId, colSpan, rowSpan, extra]) => {
            const app = APPS.find(a => a.id === appId)
            if (!app) return null
            const isOpen   = openTabIds.has(appId)
            const isActive = activeTabId === appId
            return (
              <BentoCard
                key={appId}
                app={app}
                colSpan={colSpan}
                rowSpan={rowSpan}
                extra={extra}
                isOpen={isOpen}
                isActive={isActive}
                phaseComplete={!!phaseCompletion[appId]}
                onClick={() => handleCardClick(appId)}
              />
            )
          })}

          {/* Sprint 35.6 UX diet: removed two decorative span-2 cards.
              (1) "Compliance Status" card claimed ✓ on 6 frameworks
              including FDA AI 2026 and ISO 13485 — overclaims you'd
              have to defend in a vendor review, contradicts Newsletter
              #3 Q6 honesty stance. (2) "EVOLV AI Engine" card listed
              internal *Agent class names with a hardcoded pulsing
              "Online" badge — theatre + the exact "agentic" language
              Nuno publicly cautioned against. Both deleted. The bento
              grid breathes more; honesty story tightens. */}
        </div>

        {/* ── Bottom tagline ───────────────────────────────── */}
        <p className="text-center text-text-muted text-xs mt-8">
          Powered by EVOLV | WingstarTech Inc. — AI-assisted, human-approved.
        </p>
      </div>
    </div>
  )
}

function BentoCard({
  app, colSpan, rowSpan, extra, isOpen, isActive,
  phaseComplete, onClick,
}) {
  return (
    <div
      className={`
        glass rounded-2xl p-5 bento-card ${extra} flex flex-col
        justify-between cursor-pointer
        ${isActive ? 'ring-1 ring-blue-DEFAULT/60' : ''}
        ${phaseComplete ? 'ring-1 ring-lime-DEFAULT/30' : ''}
      `}
      style={{
        gridColumn: `span ${colSpan}`,
        gridRow:    `span ${rowSpan}`,
      }}
      onClick={onClick}
    >
      {/* Top section */}
      <div className="flex items-start justify-between">
        <div
          className={`app-icon-3d shrink-0 ${colSpan > 1 ? 'w-10 h-10' : 'w-7 h-7'}`}
          style={{ color: app.accentColor }}
        >
          {ICONS[app.id] ?? ICONS.docs}
        </div>

        {/* Badges: priority active > open > phase-complete > app.badge */}
        {isActive ? (
          <span className="text-[9px] px-1.5 py-0.5 rounded border
                           bg-blue-dim border-blue-DEFAULT/50 text-blue-DEFAULT
                           animate-pulse">
            ● Active
          </span>
        ) : isOpen ? (
          <span className="text-[9px] px-1.5 py-0.5 rounded border
                           bg-bg-hover border-border-base text-text-secondary">
            Open ↗
          </span>
        ) : phaseComplete ? (
          <span className="text-[9px] px-1.5 py-0.5 rounded border
                           bg-lime-dim border-lime-DEFAULT/30 text-lime-DEFAULT">
            ✓ Done
          </span>
        ) : app.badge ? (
          <span className={`
            text-[9px] px-1.5 py-0.5 rounded border
            ${app.accentClass === 'lime'
              ? 'bg-lime-dim border-lime-DEFAULT/30 text-lime-DEFAULT'
              : 'bg-blue-dim border-blue-DEFAULT/30 text-blue-DEFAULT'}
          `}>
            {app.badge}
          </span>
        ) : null}
      </div>

      {/* Bottom section */}
      <div>
        <h3 className={`font-semibold text-white mb-1
                        ${colSpan > 1 ? 'text-lg' : 'text-sm'}`}>
          {app.label}
        </h3>
        {(colSpan > 1 || rowSpan > 1) && (
          <p className="text-text-secondary text-xs leading-relaxed">
            {app.description}
          </p>
        )}
        <div className="flex items-center gap-1.5 mt-2">
          <span
            className="text-xs font-medium"
            style={{ color: app.accentColor }}
          >
            {isOpen ? 'Switch →' : 'Open →'}
          </span>
        </div>
      </div>
    </div>
  )
}
