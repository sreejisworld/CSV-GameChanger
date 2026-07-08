/**
 * LifecycleStrip — persistent V-shape lifecycle spine above phase pages.
 *
 * Sprint 33 upgrade: replaced the flat horizontal node row with a
 * compact V-shape SVG that mirrors VModelHero's geometry. Same nodes,
 * same gradient stroke, same colour conventions — the V-model is now
 * the platform's *spine*, not just a Home decoration. Pharma QA pros
 * see the same brand visual on landing AND above every working phase.
 *
 * Behaviour:
 *   • Collapsed (default): 6px gradient progress line — completion at
 *     a glance.
 *   • Hover → full ~96px V-shape strip slides down.
 *   • Press `L` (outside inputs) to pin/unpin permanently.
 *   • Lock badge appears in the top-right corner when pinned.
 *
 * Node states (matches VModelHero on Home):
 *   active    — current open tab (electric blue + halo)
 *   completed — visited / signed-off (lime green ✓)
 *   available — clickable, not yet visited (muted)
 *   locked    — not applicable yet (Retire before release)
 *
 * Click any node → opens that phase as a tab.
 */
import { useState, useEffect } from 'react'
import { useAppStore, LIFECYCLE_PHASES } from '../store/useAppStore.js'
import { APP_MAP }                        from '../data/apps.js'
import { V_NODES_SPINE, V_PATH_SPINE,
         PHASE_SHORT }                    from './vmodelGeometry.js'

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
        height:     expanded ? '96px' : '6px',
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

      {/* ── Expanded view: compact V-shape SVG ──────────── */}
      <div
        className="absolute inset-0 flex items-center justify-center px-6"
        style={{
          opacity:       expanded ? 1 : 0,
          transition:    'opacity 0.15s 0.06s',
          pointerEvents: expanded ? 'auto' : 'none',
        }}
      >
        <svg
          viewBox="0 0 720 80"
          preserveAspectRatio="xMidYMid meet"
          className="w-full h-full"
          style={{ maxHeight: '88px', maxWidth: '1180px' }}
          aria-label="Lifecycle V-model spine"
        >
          <defs>
            <linearGradient id="v-spine-grad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%"   stopColor="#007FFF" />
              <stop offset="50%"  stopColor="#32CD32" />
              <stop offset="100%" stopColor="#007FFF" />
            </linearGradient>
          </defs>

          {/* Track path — faint guide so the gradient stroke has
              something to layer over on light backgrounds. */}
          <path
            d={V_PATH_SPINE}
            fill="none"
            stroke="var(--border-base)"
            strokeWidth="1.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Brand gradient stroke. No draw-in animation here — the
              hero earns that on first paint; on the spine it'd be
              jarring every time the user opens a phase. */}
          <path
            d={V_PATH_SPINE}
            fill="none"
            stroke="url(#v-spine-grad)"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity="0.55"
          />

          {/* Nodes — coloured by state. Active phase (current tab) takes
              precedence over completion: even on a phase you've already
              signed, when you re-open it the spine shows you're THERE. */}
          {V_NODES_SPINE.map(n => {
            const app       = APP_MAP[n.id]
            const isActive  = activeTabId === n.id
            const done      = !!phaseCompletion?.[n.id]
            const locked    = (app?.locked ?? false)
                              || (n.id === 'retire' && !phaseCompletion?.monitor)

            const fill   = isActive ? '#007FFF'
                          : done    ? '#32CD32'
                          : locked  ? 'var(--bg-card)'
                          :           'var(--bg-card)'
            const stroke = isActive ? '#007FFF'
                          : done    ? '#32CD32'
                          : locked  ? 'var(--border-base)'
                          :           'var(--border-base)'
            const labelClr = isActive
                          ? '#007FFF'
                          : done
                            ? 'var(--text-primary)'
                            : 'var(--text-muted)'

            // Label position: above for the four "top" nodes (Plan,
            // Reqs / Monitor, Retire — y < 24), below for apex nodes
            // (Design, Verify, Risk, Release — y > 24). Keeps labels
            // outside the V curve so they never collide with the
            // gradient stroke.
            const labelY = n.y > 28 ? n.y + 14 : n.y - 9

            return (
              <g
                key={n.id}
                style={{ cursor: locked ? 'not-allowed' : 'pointer' }}
                onClick={() => {
                  if (locked) return
                  openTab(n.id)
                  setPhaseComplete(n.id)
                }}
              >
                {/* Pulse halo on active node — same as Home hero. */}
                {isActive && (
                  <circle
                    cx={n.x} cy={n.y} r="9"
                    fill="#007FFF" opacity="0.22"
                    className="animate-pulse"
                  />
                )}
                {/* Main node */}
                <circle
                  cx={n.x} cy={n.y} r="5.5"
                  fill={fill}
                  stroke={stroke}
                  strokeWidth="1.8"
                  style={{
                    filter: isActive
                      ? 'drop-shadow(0 0 4px rgba(0,127,255,0.55))'
                      : done
                        ? 'drop-shadow(0 0 3px rgba(50,205,50,0.45))'
                        : 'none',
                  }}
                />
                {/* Tick on completed (only when not the active node —
                    on active node we want the solid blue dot). */}
                {done && !isActive && (
                  <path
                    d={`M ${n.x - 2.5},${n.y} L ${n.x - 0.5},${n.y + 1.8} L ${n.x + 3},${n.y - 1.8}`}
                    fill="none"
                    stroke="#fff"
                    strokeWidth="1.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}
                {/* Label */}
                <text
                  x={n.x}
                  y={labelY}
                  textAnchor="middle"
                  fill={labelClr}
                  fontSize="9"
                  fontWeight={isActive ? '700' : done ? '600' : '500'}
                  fontFamily="Inter, sans-serif"
                  style={{ textTransform: 'uppercase', letterSpacing: '0.04em' }}
                >
                  {PHASE_SHORT[n.id] ?? n.short}
                </text>
                <title>
                  {app?.label ?? n.label}
                  {' — '}
                  {isActive
                    ? 'Active phase'
                    : done
                      ? 'Complete'
                      : locked
                        ? (app?.lockedReason ?? 'Locked')
                        : 'Available'}
                </title>
              </g>
            )
          })}
        </svg>
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
