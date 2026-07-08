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

// Accent colors for lifecycle group label
const LIFECYCLE_ACCENT = '#007FFF'

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
          <p className="text-text-primary font-black text-sm leading-none tracking-wide">
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

// ── Monogram for collapsed mode — 32px with colored ring ────────
function Monogram({ label, accentColor, isActive }) {
  const initials = label
    .replace(/[^a-zA-Z ]/g, '')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0].toUpperCase())
    .join('') || label.slice(0, 2).toUpperCase()

  const color = isActive ? '#007FFF' : accentColor ?? '#64748b'
  return (
    <span
      className="w-8 h-8 rounded-full flex items-center justify-center
                 text-[11px] font-bold shrink-0 leading-none transition-all"
      style={{
        background:  color + '18',
        border:      `2px solid ${color}${isActive ? 'cc' : '40'}`,
        color,
        boxShadow:   isActive ? `0 0 0 2px ${color}30` : 'none',
      }}
    >
      {initials}
    </span>
  )
}

// ── Main Sidebar ───────────────────────────────────────────────
export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const {
    activeTabId, openTab, statusBadges, phaseCompletion, setPhaseComplete,
    navGroupsCollapsed, toggleNavGroup,
  } = useAppStore()

  // Sprint 30 — `navGroupsCollapsed` lives in the store and persists
  // (defaults: Intelligence + Tools collapsed, Lifecycle expanded).
  // The local toggle just delegates to the store action.
  const toggleGroup = label => toggleNavGroup(label)

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
        {NAV_GROUPS.map(group => {
          const isGroupCollapsed = Boolean(navGroupsCollapsed?.[group.label])

          // Sprint 30 — when a group is collapsed, surface a tiny dot
          // on its header if any item inside is active or carries a
          // badge, so the user can tell there's hidden activity in
          // there. Keeps the calm "lifecycle-first" first paint
          // honest: nothing is disappeared without a breadcrumb.
          const hiddenActivity = isGroupCollapsed && group.items.some(
            id => id === activeTabId
                  || (statusBadges?.[id]?.type
                      && statusBadges[id].type !== 'info')
          )
          return (
          <div key={group.label}>
            {!collapsed && (
              <button
                onClick={() => toggleGroup(group.label)}
                className="w-full flex items-center justify-between
                           px-4 mb-1.5 group focus-blue outline-none"
              >
                <span className="flex items-center gap-1.5">
                  <p className="text-[9px] text-text-muted uppercase
                                tracking-widest group-hover:text-text-secondary
                                transition-colors">
                    {group.label}
                  </p>
                  {hiddenActivity && (
                    <span
                      className="w-1.5 h-1.5 rounded-full shrink-0
                                 animate-pulse"
                      style={{ background: '#f59e0b' }}
                      title="Activity in this group"
                    />
                  )}
                </span>
                <span
                  className="text-[9px] text-text-muted transition-transform
                             duration-200 group-hover:text-text-secondary"
                  style={{
                    display: 'inline-block',
                    transform: isGroupCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)',
                  }}
                >
                  ▾
                </span>
              </button>
            )}
            {!isGroupCollapsed && (
            <div className="space-y-0.5 px-2">
              {group.items.map(appId => {
                const app        = APP_MAP[appId]
                const isActive   = activeTabId === appId
                const badge      = statusBadges[appId] ?? null
                const dotColor   = badge ? DOT_COLORS[badge.type] : null
                const isLocked   = app?.locked ?? false
                const isComplete = !isLocked && (phaseCompletion?.[appId] ?? false)

                // Single indicator — highest priority wins
                const indicator = badge
                  ? <StatusDot badge={badge} collapsed={false} />
                  : isActive
                    ? <span className="w-1.5 h-1.5 rounded-full bg-blue-DEFAULT
                                       shrink-0 shadow-[0_0_6px_#007FFF]" />
                    : isComplete
                      ? <span className="shrink-0 text-[10px] font-semibold
                                         text-lime-DEFAULT" title="Phase complete">✓</span>
                      : isLocked
                        ? <span className="text-[9px] text-text-muted shrink-0
                                           border border-border-base rounded px-1">
                            locked
                          </span>
                        : app.badge
                          ? <span className={`
                              text-[9px] px-1.5 py-0.5 rounded border shrink-0
                              ${app.accentClass === 'lime'
                                ? 'bg-lime-dim border-lime-DEFAULT/30 text-lime-DEFAULT'
                                : app.accentClass === 'amber'
                                  ? 'bg-amber-dim border-amber-DEFAULT/30 text-amber-DEFAULT'
                                  : 'bg-blue-dim border-blue-DEFAULT/30 text-blue-DEFAULT'}
                            `}>
                              {app.badge}
                            </span>
                          : null

                // Collapsed: single dot above monogram (badge > complete > nothing)
                const collapsedDot = badge
                  ? <span className="absolute -top-0.5 -right-0.5 w-2 h-2
                                     rounded-full border border-bg-surface"
                           style={{ background: dotColor }} />
                  : isComplete
                    ? <span className="absolute -top-0.5 -right-0.5 w-2 h-2
                                       rounded-full border border-bg-surface
                                       bg-lime-DEFAULT" />
                    : null

                return (
                  <button
                    key={appId}
                    onClick={isLocked ? undefined : () => {
                      openTab(appId)
                      if (APP_MAP[appId]?.category === 'lifecycle') {
                        setPhaseComplete(appId)
                      }
                    }}
                    disabled={isLocked}
                    title={
                      isLocked
                        ? (app?.lockedReason ?? 'Locked')
                        : collapsed
                          ? app.label
                          : undefined
                    }
                    className={`
                      group w-full flex items-center gap-2.5 rounded-lg
                      px-2 py-1.5 text-left transition-all duration-150
                      focus-blue relative
                      ${isLocked
                        ? 'cursor-not-allowed opacity-35'
                        : isActive
                          ? 'bg-blue-dim border border-border-blue text-text-primary'
                          : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'}
                    `}
                  >
                    {/* Collapsed: monogram + single dot overlay */}
                    {collapsed ? (
                      <div className="relative">
                        <Monogram
                          label={app.label}
                          accentColor={app.accentColor}
                          isActive={isActive}
                        />
                        {collapsedDot}
                      </div>
                    ) : (
                      /* Expanded: thin left accent line */
                      <span
                        className="w-0.5 h-3.5 rounded-full shrink-0 transition-all"
                        style={{
                          background: isActive
                            ? '#007FFF'
                            : isComplete
                              ? '#32CD32'
                              : 'transparent',
                          boxShadow: isActive
                            ? '0 0 6px rgba(0,127,255,0.6)'
                            : 'none',
                        }}
                      />
                    )}

                    {/* Label (expanded only) */}
                    {!collapsed && (
                      <span className="flex-1 text-xs font-medium truncate">
                        {app.label}
                      </span>
                    )}

                    {/* Single right-side indicator (expanded only) */}
                    {!collapsed && indicator}
                  </button>
                )
              })}
            </div>
            )}
          </div>
          )
        })}
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
