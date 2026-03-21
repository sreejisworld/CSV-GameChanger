/**
 * LifecycleStrip — horizontal V-model lifecycle progress bar.
 *
 * Behaviour:
 *   • Collapsed (default): 6px gradient progress line — shows completion at a glance.
 *   • Hover → full 52px strip slides down.
 *   • Press `L` (outside inputs) to pin/unpin the strip permanently.
 *   • A small lock badge appears in the top-right corner when pinned.
 *
 * Node states:
 *   active    — current tab (electric blue)
 *   completed — phase has been visited (lime green ✓)
 *   available — can be opened (grey)
 *   locked    — not applicable yet (dim, disabled)
 *
 * Clicking a node opens that phase as a tab.
 * Connector lines fill lime as phases complete.
 */
import { useState, useEffect } from 'react'
import { useAppStore, LIFECYCLE_PHASES } from '../store/useAppStore.js'
import { APP_MAP }                        from '../data/apps.js'

const PHASE_LABELS = {
  plan:         'Plan',
  requirements: 'Reqs',
  risk:         'Risk',
  design:       'Design',
  verify:       'Verify',
  release:      'Release',
  monitor:      'Monitor',
  retire:       'Retire',
}

// ── Individual phase node ────────────────────────────────────
function PhaseNode({ phaseId, isActive, isCompleted, isLocked, onClick }) {
  const app = APP_MAP[phaseId]

  const nodeClass = isActive    ? 'phase-node-active'
    : isCompleted ? 'phase-node-complete'
    : isLocked    ? 'phase-node-locked'
    : 'phase-node-avail'

  const labelClass = isActive    ? 'phase-label-active'
    : isCompleted ? 'phase-label-complete'
    : isLocked    ? 'phase-label-locked'
    : 'phase-label-avail'

  return (
    <button
      onClick={isLocked ? undefined : onClick}
      disabled={isLocked}
      title={isLocked ? (app?.lockedReason ?? 'Locked') : app?.description}
      className={`
        flex flex-col items-center gap-1 group
        transition-all duration-150 outline-none
        ${isLocked ? 'cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {/* Circle node */}
      <div
        className={`
          w-5 h-5 rounded-full border-2 flex items-center
          justify-center transition-all duration-150 shrink-0
          ${nodeClass}
          ${isActive ? 'shadow-[0_0_0_3px_rgba(0,127,255,0.20)]' : ''}
          ${isCompleted && !isActive ? 'shadow-[0_0_0_2px_rgba(50,205,50,0.15)]' : ''}
        `}
      >
        {isCompleted && !isActive && (
          <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
            <path
              d="M1.5 4L3 5.5L6.5 2"
              stroke="white"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
        {isLocked && (
          <svg width="7" height="7" viewBox="0 0 7 7" fill="none">
            <rect x="1" y="3" width="5" height="3.5" rx="0.8"
                  fill="currentColor" opacity="0.4" />
            <path d="M2 3V2a1.5 1.5 0 013 0v1"
                  stroke="currentColor" strokeWidth="1.2"
                  strokeLinecap="round" fill="none" opacity="0.4" />
          </svg>
        )}
        {isActive && (
          <div className="w-1.5 h-1.5 rounded-full bg-white" />
        )}
      </div>

      {/* Label */}
      <span
        className={`text-[9px] font-medium uppercase tracking-wide
                    leading-none whitespace-nowrap transition-colors
                    ${labelClass}`}
      >
        {PHASE_LABELS[phaseId]}
      </span>
    </button>
  )
}

// ── Connector line ───────────────────────────────────────────
function Connector({ leftCompleted, rightCompleted }) {
  const filled = leftCompleted && rightCompleted
  const connClass = filled
    ? 'connector-lime'
    : leftCompleted
      ? 'connector-half'
      : 'connector-empty'

  return (
    <div className="flex-1 flex items-center pb-4 min-w-[12px]">
      <div
        className={`w-full transition-all duration-300 ${connClass}`}
        style={{ height: '1.5px' }}
      />
    </div>
  )
}

// ── Main LifecycleStrip ──────────────────────────────────────
export default function LifecycleStrip() {
  const { activeTabId, openTab, phaseCompletion, setPhaseComplete } = useAppStore()
  const [pinned,  setPinned]  = useState(false)
  const [hovered, setHovered] = useState(false)

  const expanded = pinned || hovered

  // `L` key outside input fields toggles pin
  useEffect(() => {
    const handler = e => {
      if (
        (e.key === 'l' || e.key === 'L') &&
        !e.metaKey && !e.ctrlKey && !e.altKey
      ) {
        const tag = document.activeElement?.tagName
        if (tag !== 'INPUT' && tag !== 'TEXTAREA' && tag !== 'SELECT') {
          e.preventDefault()
          setPinned(v => !v)
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Compute how far through the lifecycle we are (for the thin bar gradient)
  const completedCount = LIFECYCLE_PHASES.filter(p => phaseCompletion[p]).length
  const pct            = (completedCount / LIFECYCLE_PHASES.length) * 100

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="shrink-0 select-none bg-bg-surface border-b border-border-base
                 relative overflow-hidden"
      style={{
        height:     expanded ? '52px' : '6px',
        transition: 'height 0.22s cubic-bezier(0.4,0,0.2,1)',
      }}
    >

      {/* ── Collapsed view: gradient progress line ──────── */}
      <div
        className="absolute inset-0 flex"
        style={{
          opacity:    expanded ? 0 : 1,
          transition: 'opacity 0.12s',
          pointerEvents: expanded ? 'none' : 'auto',
        }}
      >
        {/* Filled portion */}
        <div
          style={{
            width:      `${pct}%`,
            background: 'linear-gradient(90deg, #007FFF 0%, #32CD32 100%)',
            transition: 'width 0.4s ease',
          }}
        />
        {/* Unfilled portion */}
        <div
          style={{
            flex: 1,
            background: 'var(--connector-empty)',
          }}
        />
      </div>

      {/* ── Expanded view: full node strip ──────────────── */}
      <div
        className="absolute inset-0 flex items-center px-4 py-2 overflow-x-auto"
        style={{
          opacity:       expanded ? 1 : 0,
          transition:    'opacity 0.15s 0.06s',
          pointerEvents: expanded ? 'auto' : 'none',
          minHeight:     '52px',
        }}
      >
        {LIFECYCLE_PHASES.map((phaseId, idx) => {
          const app         = APP_MAP[phaseId]
          const isActive    = activeTabId === phaseId
          const isCompleted = phaseCompletion[phaseId] ?? false
          const isLocked    = app?.locked ?? false
          const isLast      = idx === LIFECYCLE_PHASES.length - 1

          return (
            <div key={phaseId} className="flex items-center flex-1 min-w-0">
              <PhaseNode
                phaseId={phaseId}
                isActive={isActive}
                isCompleted={isCompleted}
                isLocked={isLocked}
                onClick={() => { openTab(phaseId); setPhaseComplete(phaseId) }}
              />
              {!isLast && (
                <Connector
                  leftCompleted={isCompleted}
                  rightCompleted={phaseCompletion[LIFECYCLE_PHASES[idx + 1]] ?? false}
                />
              )}
            </div>
          )
        })}
      </div>

      {/* ── Pin badge (top-right, visible when pinned) ──── */}
      {pinned && (
        <button
          onClick={() => setPinned(false)}
          title="Unpin lifecycle strip (L)"
          className="absolute top-1 right-2 z-10
                     text-[9px] text-blue-DEFAULT border border-blue-DEFAULT/30
                     bg-blue-dim rounded px-1.5 py-0.5
                     hover:bg-blue-DEFAULT/20 transition-colors"
        >
          pinned · L
        </button>
      )}
    </div>
  )
}
