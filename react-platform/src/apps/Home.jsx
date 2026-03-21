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
import { useState, useMemo } from 'react'
import { APPS }         from '../data/apps.js'
import { useAppStore,
         LIFECYCLE_PHASES } from '../store/useAppStore.js'

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
  onSwitch, onCreate, onDelete,
}) {
  const [creating, setCreating] = useState(false)
  const [newName,  setNewName]  = useState('')

  const projectList   = Object.values(projects)
  const activeProj    = projects[activeProjectId]
  const otherProjects = projectList.filter(p => p.id !== activeProjectId)
  const activeDone    = Object.values(phaseCompletion).filter(Boolean).length

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

// ── Main component ────────────────────────────────────────────────
export default function Home() {
  const {
    tabs, activeTabId, openTab, switchTab,
    phaseCompletion, requirements, testScripts,
    testRuns, activeRunId, releaseData, planData,
    riskData,
    projects, activeProjectId,
    createProject, switchProject, deleteProject,
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

        {/* ── Hero header ────────────────────────────────── */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold text-white">
              EVOLV Platform
            </h1>
            <span className="ai-badge animate-pulse-lime text-sm px-2 py-1">
              EVOLV AI Active
            </span>
          </div>
          <p className="text-text-secondary text-sm">
            The Validation Factory — GAMP 5 · CSA · 21 CFR Part 11
            · FDA AI Guidance 2026
          </p>
          <div className="neon-sep mt-4" />
        </div>

        {/* ── Project switcher ────────────────────────────── */}
        <ProjectsSwitcher
          projects={projects}
          activeProjectId={activeProjectId}
          phaseCompletion={phaseCompletion}
          onSwitch={switchProject}
          onCreate={createProject}
          onDelete={deleteProject}
        />

        {/* ── Project health banner ───────────────────────── */}
        <div className="glass rounded-2xl p-5 mb-6 flex items-center gap-6">

          {/* Progress ring */}
          <ProgressRing done={doneCount} total={totalPhases} />

          {/* Phase pills */}
          <div className="flex-1 min-w-0">
            <p className="text-[10px] text-text-muted uppercase tracking-widest
                          mb-2 font-semibold">
              Lifecycle Progress
            </p>
            <div className="flex flex-wrap gap-1.5">
              {PHASE_META.map(p => {
                const done   = phaseCompletion[p.id]
                const locked = p.id === 'retire'
                return (
                  <button
                    key={p.id}
                    onClick={() =>
                      !locked && handleCardClick(p.id)}
                    disabled={locked}
                    className={`
                      flex items-center gap-1 px-2 py-1 rounded-lg
                      text-[10px] font-medium transition-colors
                      ${locked
                        ? 'border border-border-base text-text-muted opacity-40 cursor-not-allowed'
                        : done
                          ? 'border border-lime-DEFAULT/30 bg-lime-DEFAULT/10 text-lime-DEFAULT'
                          : 'border border-border-base text-text-muted hover:border-border-bright hover:text-text-secondary'}
                    `}
                  >
                    <span>{p.emoji}</span>
                    <span>{p.label}</span>
                    {done && <span className="text-lime-DEFAULT">✓</span>}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Next action CTA */}
          <div className="shrink-0 max-w-[220px]">
            <p className="text-[10px] text-text-muted uppercase tracking-widest
                          mb-2 font-semibold">
              Next Action
            </p>
            <p className="text-xs text-text-secondary leading-relaxed mb-3">
              {nextAction.msg}
            </p>
            {nextAction.appId && (
              <button
                onClick={() => handleCardClick(nextAction.appId)}
                className="w-full py-1.5 text-xs rounded-lg font-semibold
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

          {/* Compliance card (decorative) */}
          <div
            className="glass rounded-2xl p-5 flex flex-col justify-between"
            style={{ gridColumn: 'span 2', gridRow: 'span 1' }}
          >
            <div className="flex items-center gap-2 mb-3">
              <div className="w-4 h-4 text-text-secondary shrink-0">
                {ICONS.shield}
              </div>
              <p className="text-text-secondary text-xs font-semibold
                            uppercase tracking-wider">
                Compliance Status
              </p>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: '21 CFR Part 11', ok: true },
                { label: 'GAMP 5 Rev 2',  ok: true },
                { label: 'FDA AI 2026',    ok: true },
                { label: 'ISO 13485',      ok: true },
                { label: 'GMP Mode',       ok: true },
                { label: 'Audit Trail',    ok: true },
              ].map(c => (
                <div key={c.label}
                  className="flex items-center gap-1.5 text-[10px]">
                  <span className={c.ok
                    ? 'text-lime-DEFAULT' : 'text-red-400'}>
                    {c.ok ? '✓' : '✗'}
                  </span>
                  <span className="text-text-secondary">{c.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* EVOLV AI status card (decorative) */}
          <div
            className="glass-lime rounded-2xl p-5 flex flex-col justify-between"
            style={{ gridColumn: 'span 2', gridRow: 'span 1' }}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 text-lime-DEFAULT shrink-0">
                  {ICONS.cpu}
                </div>
                <p className="text-lime-DEFAULT text-xs font-semibold
                              uppercase tracking-wider">
                  EVOLV AI Engine
                </p>
              </div>
              <span className="text-[9px] text-lime-DEFAULT border
                               border-lime-DEFAULT/30 bg-lime-dim rounded-full
                               px-2 py-0.5 animate-pulse-lime">
                Online
              </span>
            </div>
            <div className="space-y-1.5 text-[11px] text-text-secondary">
              {[
                'RequirementArchitect — GAMP 5 URS generation',
                'VerificationAgent — Regulatory compliance check',
                'DeltaAgent — CSA test script generation',
                'SentinelImpactAgent — Blast radius analysis',
              ].map(agent => (
                <div key={agent} className="flex items-center gap-2">
                  <span className="text-lime-DEFAULT text-[9px]">●</span>
                  <span>{agent}</span>
                </div>
              ))}
            </div>
          </div>
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
