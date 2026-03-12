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
 */
import { lazy, Suspense } from 'react'
import { useTabManager }  from './hooks/useTabManager.js'
import Sidebar            from './shell/Sidebar.jsx'
import TopHeader          from './shell/TopHeader.jsx'
import TabBar             from './shell/TabBar.jsx'

// Lazy-load each app to keep initial bundle small
const RENDERERS = {
  'home':               lazy(() => import('./apps/Home.jsx')),
  'validation-factory': lazy(() => import('./apps/ValidationFactory.jsx')),
  'navigator':          lazy(() => import('./apps/Navigator.jsx')),
  'dev-portal':         lazy(() => import('./apps/DevPortal.jsx')),
  'config':             lazy(() => import('./apps/Config.jsx')),
  'academy':            lazy(() => import('./apps/Academy.jsx')),
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

export default function App() {
  const { tabs, activeTabId, openTab, closeTab, switchTab } = useTabManager()

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-primary">

      {/* ── Sidebar ──────────────────────────────────── */}
      <Sidebar activeTabId={activeTabId} openTab={openTab} />

      {/* ── Main column ──────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">

        {/* Top header */}
        <TopHeader openTab={openTab} />

        {/* Tab bar */}
        <TabBar
          tabs={tabs}
          activeTabId={activeTabId}
          switchTab={switchTab}
          closeTab={closeTab}
        />

        {/* App pane — render all tabs, hide inactive ones */}
        <div className="flex-1 relative overflow-hidden">
          {tabs.map(tab => {
            const Component = RENDERERS[tab.appId]
            const isActive  = tab.appId === activeTabId
            return (
              <div
                key={tab.appId}
                className="absolute inset-0 overflow-hidden transition-opacity duration-150"
                style={{
                  opacity:        isActive ? 1 : 0,
                  pointerEvents:  isActive ? 'auto' : 'none',
                  zIndex:         isActive ? 1 : 0,
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
        </div>
      </div>
    </div>
  )
}
