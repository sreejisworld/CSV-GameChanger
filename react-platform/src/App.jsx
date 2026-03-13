/**
 * App — EVOLV Platform Shell root.
 *
 * Layout:
 *  ┌──────────┬────────────────────────────┐
 *  │          │  TopHeader                 │
 *  │ Sidebar  ├────────────────────────────┤
 *  │          │  TabBar                    │
 *  │          ├────────────────────────────┤
 *  │          │  Active App (full height)  │
 *  └──────────┴────────────────────────────┘
 *
 * State management: Zustand (useAppStore)
 * Animations:       Framer Motion
 * Persistence:      All tabs stay mounted; drafts live in store.
 */
import { lazy, Suspense } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore }  from './store/useAppStore.js'
import Sidebar          from './shell/Sidebar.jsx'
import TopHeader        from './shell/TopHeader.jsx'
import TabBar           from './shell/TabBar.jsx'

// Lazy-load each app to keep initial bundle small
const RENDERERS = {
  'home':               lazy(() => import('./apps/Home.jsx')),
  'validation-factory': lazy(() => import('./apps/ValidationFactory.jsx')),
  'navigator':          lazy(() => import('./apps/Navigator.jsx')),
  'dev-portal':         lazy(() => import('./apps/DevPortal.jsx')),
  'config':             lazy(() => import('./apps/Config.jsx')),
  'academy':            lazy(() => import('./apps/Academy.jsx')),
  'impact-analytics':   lazy(() => import('./apps/ImpactAnalytics.jsx')),
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

export default function App() {
  const { tabs, activeTabId, openTab, closeTab, switchTab } = useAppStore()

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-primary">

      {/* ── Sidebar ──────────────────────────────────── */}
      <Sidebar />

      {/* ── Main column ──────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">

        {/* Top header */}
        <TopHeader />

        {/* Tab bar */}
        <TabBar />

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

          {/* Framer Motion overlay — plays a slide-up animation on tab switch */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTabId}
              variants={tabVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="absolute inset-0 pointer-events-none"
              style={{
                background: 'linear-gradient(to bottom, rgba(7,7,15,0.18) 0%, transparent 40%)',
                zIndex: 2,
              }}
            />
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
