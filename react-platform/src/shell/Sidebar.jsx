/**
 * Sidebar — collapsible left-hand navigation.
 *
 * Expanded (240px): logo + group labels + icon + label
 * Collapsed (64px):  logo mark + icons only (tooltips on hover)
 */
import { useState } from 'react'
import { NAV_GROUPS, APP_MAP } from '../data/apps.js'

export default function Sidebar({ activeTabId, openTab }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={`
        flex flex-col h-screen bg-bg-surface border-r border-border-base
        sidebar-transition select-none shrink-0 relative z-20
        ${collapsed ? 'sidebar-collapsed' : 'sidebar-expanded'}
      `}
    >
      {/* ── Logo ─────────────────────────────────────────── */}
      <div className="flex items-center gap-3 px-4 py-4 border-b border-border-base">
        <div className="w-9 h-9 rounded-xl shrink-0 flex items-center justify-center
                        bg-gradient-to-br from-blue-DEFAULT to-lime-DEFAULT
                        shadow-[0_0_16px_rgba(0,127,255,0.4)]">
          <span className="text-white font-black text-base leading-none">E</span>
        </div>
        {!collapsed && (
          <div className="min-w-0 animate-slide-in">
            <p className="text-white font-bold text-sm leading-none">EVOLV</p>
            <p className="text-text-muted text-[9px] uppercase tracking-widest mt-0.5">
              The Validation Factory
            </p>
          </div>
        )}
      </div>

      {/* ── Nav groups ───────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto py-3 space-y-4">
        {NAV_GROUPS.map(group => (
          <div key={group.label}>
            {!collapsed && (
              <p className="px-4 text-[9px] text-text-muted uppercase tracking-widest mb-1.5">
                {group.label}
              </p>
            )}
            <div className="space-y-0.5 px-2">
              {group.items.map(appId => {
                const app      = APP_MAP[appId]
                const isActive = activeTabId === appId
                return (
                  <button
                    key={appId}
                    onClick={() => openTab(appId)}
                    title={collapsed ? app.label : undefined}
                    className={`
                      group w-full flex items-center gap-3 rounded-lg px-2.5 py-2
                      text-left transition-all duration-150 focus-blue
                      ${isActive
                        ? 'bg-blue-dim border border-border-blue text-white'
                        : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'}
                    `}
                  >
                    <span className={`
                      text-lg leading-none shrink-0
                      ${isActive ? 'drop-shadow-[0_0_8px_rgba(0,127,255,0.8)]' : ''}
                    `}>
                      {app.emoji}
                    </span>
                    {!collapsed && (
                      <span className="flex-1 text-xs font-medium truncate">
                        {app.label}
                      </span>
                    )}
                    {!collapsed && app.badge && (
                      <span className={`
                        text-[9px] px-1.5 py-0.5 rounded border shrink-0
                        ${app.accentClass === 'lime'
                          ? 'bg-lime-dim border-lime-DEFAULT/30 text-lime-DEFAULT'
                          : 'bg-blue-dim border-blue-DEFAULT/30 text-blue-DEFAULT'}
                      `}>
                        {app.badge}
                      </span>
                    )}
                    {!collapsed && isActive && (
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-DEFAULT shrink-0
                                       shadow-[0_0_6px_#007FFF]" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* ── Footer ───────────────────────────────────────── */}
      <div className="border-t border-border-base px-4 py-3">
        {!collapsed && (
          <p className="text-[9px] text-text-muted text-center">
            Powered by EVOLV | WingstarTech Inc.
          </p>
        )}
      </div>

      {/* ── Collapse toggle ───────────────────────────────── */}
      <button
        onClick={() => setCollapsed(v => !v)}
        className="absolute -right-3 top-[72px] w-6 h-6 rounded-full
                   bg-bg-card border border-border-bright text-text-muted
                   flex items-center justify-center text-[10px]
                   hover:border-border-blue hover:text-blue-DEFAULT
                   transition-colors z-30 focus-blue"
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? '▶' : '◀'}
      </button>
    </aside>
  )
}
