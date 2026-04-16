/**
 * App — EVOLV Platform Shell root.
 *
 * Layout:
 *  ┌──────────┬────────────────────────────────────┐
 *  │          │  TopHeader (tabs + controls, 44px) │
 *  │ Sidebar  ├────────────────────────────────────┤
 *  │          │  LifecycleStrip (V-model progress) │
 *  │          ├────────────────────────────────────┤
 *  │          │  Active App (full height)           │
 *  └──────────┴────────────────────────────────────┘
 *
 * State management: Zustand (useAppStore)
 * Animations:       Framer Motion
 * Persistence:      All tabs stay mounted; drafts live in store.
 */
import { lazy, Suspense, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore }   from './store/useAppStore.js'
import Sidebar           from './shell/Sidebar.jsx'
import TopHeader         from './shell/TopHeader.jsx'
import LifecycleStrip    from './shell/LifecycleStrip.jsx'
import { useDataBridge } from './hooks/useDataBridge.js'
import { useKeyChord }  from './hooks/useKeyChord.js'

// Lazy-load each app to keep initial bundle small
const RENDERERS = {
  'home':               lazy(() => import('./apps/Home.jsx')),
  // Lifecycle phases
  'plan':               lazy(() => import('./apps/Plan.jsx')),
  'requirements':       lazy(() => import('./apps/Requirements.jsx')),
  'risk':               lazy(() => import('./apps/Risk.jsx')),
  'design':             lazy(() => import('./apps/Design.jsx')),
  'verify':             lazy(() => import('./apps/Verify.jsx')),
  'release':            lazy(() => import('./apps/Release.jsx')),
  'monitor':            lazy(() => import('./apps/Monitor.jsx')),
  'retire':             lazy(() => import('./apps/Retire.jsx')),
  // Intelligence
  'system-journey':     lazy(() => import('./apps/SystemJourney.jsx')),
  'portfolio':          lazy(() => import('./apps/Portfolio.jsx')),
  'governance':         lazy(() => import('./apps/Governance.jsx')),
  'navigator':          lazy(() => import('./apps/Navigator.jsx')),
  'regulatory-watch':   lazy(() => import('./apps/RegulatoryWatch.jsx')),
  'impact-analytics':   lazy(() => import('./apps/ImpactAnalytics.jsx')),
  // Tools
  'dev-portal':         lazy(() => import('./apps/DevPortal.jsx')),
  'config':             lazy(() => import('./apps/Config.jsx')),
  'academy':            lazy(() => import('./apps/Academy.jsx')),
  'docs':               lazy(() => import('./apps/Docs.jsx')),
}

function AppLoader() {
  return (
    <div className="flex items-center justify-center h-full text-text-muted text-sm">
      <div className="flex items-center gap-3">
        <div className="w-5 h-5 rounded-full border-2 border-blue-DEFAULT
                        border-t-transparent animate-spin" />
        Loading…
      </div>
    </div>
  )
}

// Slide-up + fade when a tab becomes active
const tabVariants = {
  hidden:  { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.18, ease: 'easeOut' } },
  exit:    { opacity: 0, y: -6, transition: { duration: 0.12, ease: 'easeIn' } },
}

// Lifecycle phase IDs — strip is shown only when one is active
const LIFECYCLE_IDS = new Set([
  'plan', 'requirements', 'risk', 'design',
  'verify', 'release', 'monitor', 'retire',
])

export default function App() {
  const {
    tabs, activeTabId, openTab, closeTab, switchTab, theme,
    phaseCompletion, setStatusBadge, statusBadges,
  } = useAppStore()

  // Global Streamlit ↔ React data sync (requirements + plan polling)
  useDataBridge()

  // G → <letter> chord shortcuts (G+P=Plan, G+R=Reqs, G+K=Risk, …)
  const chordPending = useKeyChord(openTab)

  // Show the lifecycle strip whenever any lifecycle phase is open
  const showStrip = tabs.some(t => LIFECYCLE_IDS.has(t.appId))

  // Phase-advance badge notifications:
  // When a phase completes, set a "Ready" badge on the next phase
  // so the user knows they can advance.
  const prevCompletion = useRef({ ...phaseCompletion })
  useEffect(() => {
    const prev = prevCompletion.current
    const ADVANCES = [
      { from: 'plan',         to: 'requirements', label: 'Ready' },
      { from: 'requirements', to: 'risk',          label: 'Ready' },
      { from: 'risk',         to: 'design',        label: 'Ready' },
      { from: 'design',       to: 'verify',        label: 'Ready' },
      { from: 'verify',       to: 'release',       label: 'Ready' },
      { from: 'release',      to: 'monitor',       label: 'Active' },
    ]
    ADVANCES.forEach(({ from, to, label }) => {
      if (!prev[from] && phaseCompletion[from]) {
        // Phase just completed — badge the next phase if it has no badge
        if (!statusBadges[to]) {
          setStatusBadge(to, { type: 'success', label })
        }
      }
    })
    prevCompletion.current = { ...phaseCompletion }
  }, [phaseCompletion, setStatusBadge, statusBadges])

  return (
    <div
      data-theme={theme}
      className="flex h-screen overflow-hidden bg-bg-base text-text-primary"
    >

      {/* ── Sidebar ──────────────────────────────────────── */}
      <Sidebar />

      {/* ── Main column ──────────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">

        {/* Top header (merged tabs + controls) */}
        <TopHeader />

        {/* V-model lifecycle strip — visible when any lifecycle tab is open */}
        {showStrip && <LifecycleStrip />}

        {/* G-chord pending indicator — bottom-right corner */}
        {chordPending && (
          <div
            className="fixed bottom-5 right-5 z-50
                       flex items-center gap-2 px-3 py-2 rounded-xl
                       border border-blue-DEFAULT/40 bg-bg-card
                       shadow-[0_4px_24px_rgba(0,0,0,0.5)]
                       animate-fade-in text-xs"
          >
            <kbd className="text-blue-DEFAULT font-mono font-bold text-sm">G</kbd>
            <span className="text-text-muted">›</span>
            <span className="text-text-secondary">
              H P R K D V L M T N I
            </span>
          </div>
        )}

        {/* App pane */}
        <div className="flex-1 relative overflow-hidden">

          {/* Always-mounted tabs — hidden when inactive (state preserved) */}
          {tabs.map(tab => {
            const Component = RENDERERS[tab.appId]
            const isActive  = tab.appId === activeTabId
            return (
              <div
                key={tab.appId}
                className="absolute inset-0 overflow-hidden"
                style={{
                  opacity:       isActive ? 1 : 0,
                  pointerEvents: isActive ? 'auto' : 'none',
                  zIndex:        isActive ? 1 : 0,
                }}
              >
                <Suspense fallback={<AppLoader />}>
                  {Component
                    ? <Component openTab={openTab} />
                    : <AppLoader />}
                </Suspense>
              </div>
            )
          })}

          {/* Framer Motion overlay — slide-up animation on tab switch */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTabId}
              variants={tabVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="absolute inset-0 pointer-events-none"
              style={{
                background:
                  'linear-gradient(to bottom, rgba(7,7,15,0.18) 0%, transparent 40%)',
                zIndex: 2,
              }}
            />
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
