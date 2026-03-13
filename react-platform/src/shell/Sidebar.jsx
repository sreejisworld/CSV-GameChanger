/**
 * Sidebar — collapsible left-hand navigation.
 *
 * Expanded (240px): SVG logo + group labels + icon + label + status badge
 * Collapsed (64px):  logo mark + icons only (tooltips on hover)
 *
 * Status badge colours:
 *   error   → red dot    (🔴 risk / blocker)
 *   warning → amber dot  (🟡 review needed)
 *   success → green dot  (🟢 all clear)
 *   info    → blue dot   (🔵 FYI)
 */
import { useState } from 'react'
import { NAV_GROUPS, APP_MAP } from '../data/apps.js'
import { useAppStore }         from '../store/useAppStore.js'

// ── EVOLV SVG Logo ─────────────────────────────────────────────
function EvolvLogo({ collapsed }) {
  return (
    <div className="flex items-center gap-3 px-4 py-4 border-b border-border-base
                    shrink-0">
      {/* Icon mark — lightning bolt in gradient square */}
      <svg
        width="36" height="36" viewBox="0 0 36 36"
        className="shrink-0"
        aria-label="EVOLV"
      >
        <defs>
          <linearGradient id="evolv-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%"   stopColor="#007FFF" />
            <stop offset="100%" stopColor="#32CD32" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="1.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {/* Rounded square background */}
        <rect x="0" y="0" width="36" height="36" rx="10" ry="10"
              fill="url(#evolv-grad)" opacity="0.15" />
        <rect x="0" y="0" width="36" height="36" rx="10" ry="10"
              fill="none" stroke="url(#evolv-grad)" strokeWidth="1.2" />
        {/* Lightning bolt */}
        <path
          d="M21 4 L12 19 H18 L15 32 L26 17 H20 Z"
          fill="url(#evolv-grad)"
          filter="url(#glow)"
        />
      </svg>

      {!collapsed && (
        <div className="min-w-0 animate-slide-in">
          <p className="text-white font-black text-sm leading-none tracking-wide">
            EVOLV
          </p>
          <p className="text-text-muted text-[9px] uppercase tracking-widest mt-0.5">
            The Validation Factory
          </p>
        </div>
      )}
    </div>
  )
}

// ── Status dot component ───────────────────────────────────────
const DOT_COLORS = {
  error:   '#ef4444',
  warning: '#f59e0b',
  success: '#32CD32',
  info:    '#007FFF',
}

function StatusDot({ badge, collapsed }) {
  if (!badge) return null
  const color = DOT_COLORS[badge.type] ?? DOT_COLORS.info

  return collapsed ? (
    // Collapsed: tiny dot overlaid on icon (handled in parent)
    null
  ) : (
    <span
      className="shrink-0 flex items-center gap-1 text-[9px] font-medium
                 px-1.5 py-0.5 rounded-full"
      style={{
        color,
        background:  color + '18',
        border:      `1px solid ${color}40`,
      }}
      title={badge.label}
    >
      <span
        className="w-1.5 h-1.5 rounded-full shrink-0 animate-pulse"
        style={{ background: color }}
      />
      {badge.label}
    </span>
  )
}

// ── Main Sidebar ───────────────────────────────────────────────
export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const { activeTabId, openTab, statusBadges } = useAppStore()

  return (
    <aside
      className={`
        flex flex-col h-screen bg-bg-surface border-r border-border-base
        sidebar-transition select-none shrink-0 relative z-20
        ${collapsed ? 'sidebar-collapsed' : 'sidebar-expanded'}
      `}
    >
      {/* ── Logo ─────────────────────────────────────────── */}
      <EvolvLogo collapsed={collapsed} />

      {/* ── Nav groups ───────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto py-3 space-y-4">
        {NAV_GROUPS.map(group => (
          <div key={group.label}>
            {!collapsed && (
              <p className="px-4 text-[9px] text-text-muted uppercase
                            tracking-widest mb-1.5">
                {group.label}
              </p>
            )}
            <div className="space-y-0.5 px-2">
              {group.items.map(appId => {
                const app      = APP_MAP[appId]
                const isActive = activeTabId === appId
                const badge    = statusBadges[appId] ?? null
                const dotColor = badge ? DOT_COLORS[badge.type] : null

                return (
                  <button
                    key={appId}
                    onClick={() => openTab(appId)}
                    title={collapsed ? app.label : undefined}
                    className={`
                      group w-full flex items-center gap-3 rounded-lg px-2.5 py-2
                      text-left transition-all duration-150 focus-blue relative
                      ${isActive
                        ? 'bg-blue-dim border border-border-blue text-white'
                        : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'}
                    `}
                  >
                    {/* App icon */}
                    <span className={`
                      text-lg leading-none shrink-0 relative
                      ${isActive ? 'drop-shadow-[0_0_8px_rgba(0,127,255,0.8)]' : ''}
                    `}>
                      {app.emoji}
                      {/* Collapsed status dot — tiny overlay */}
                      {collapsed && badge && (
                        <span
                          className="absolute -top-0.5 -right-0.5 w-2 h-2
                                     rounded-full border border-bg-surface"
                          style={{ background: dotColor }}
                        />
                      )}
                    </span>

                    {/* Label */}
                    {!collapsed && (
                      <span className="flex-1 text-xs font-medium truncate">
                        {app.label}
                      </span>
                    )}

                    {/* Status badge (expanded only) */}
                    {!collapsed && badge && (
                      <StatusDot badge={badge} collapsed={false} />
                    )}

                    {/* App meta-badge (only when no status badge) */}
                    {!collapsed && !badge && app.badge && (
                      <span className={`
                        text-[9px] px-1.5 py-0.5 rounded border shrink-0
                        ${app.accentClass === 'lime'
                          ? 'bg-lime-dim border-lime-DEFAULT/30 text-lime-DEFAULT'
                          : 'bg-blue-dim border-blue-DEFAULT/30 text-blue-DEFAULT'}
                      `}>
                        {app.badge}
                      </span>
                    )}

                    {/* Active indicator dot */}
                    {!collapsed && isActive && !badge && (
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
      <div className="border-t border-border-base px-4 py-3 shrink-0">
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
