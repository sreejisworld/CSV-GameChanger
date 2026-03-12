/**
 * TabBar — browser-style horizontal tab strip.
 *
 * Active tab has an Electric Blue underline.
 * Home tab is pinned (shows 📌 instead of ×).
 * All other tabs show × on hover.
 */
import { APP_MAP } from '../data/apps.js'

export default function TabBar({ tabs, activeTabId, switchTab, closeTab }) {
  return (
    <div className="flex items-end h-9 bg-bg-surface border-b border-border-base
                    overflow-x-auto shrink-0 select-none">
      {tabs.map(tab => {
        const app      = APP_MAP[tab.appId]
        if (!app) return null
        const isActive = activeTabId === tab.appId
        const pinned   = !app.closeable

        return (
          <div
            key={tab.appId}
            className={`
              tab-item flex items-center gap-1.5 px-3 h-full
              border-r border-border-base cursor-pointer
              text-xs transition-colors shrink-0 group
              min-w-[80px] max-w-[160px]
              ${isActive
                ? 'active bg-bg-card text-text-primary'
                : 'text-text-muted hover:bg-bg-hover hover:text-text-secondary'}
            `}
            onClick={() => switchTab(tab.appId)}
          >
            {/* Icon */}
            <span className="text-sm leading-none shrink-0">{app.emoji}</span>

            {/* Label */}
            <span className="flex-1 truncate font-medium">{app.label}</span>

            {/* Close / Pin button */}
            {pinned ? (
              <span className="text-[10px] text-text-muted shrink-0 opacity-50">📌</span>
            ) : (
              <button
                onClick={e => { e.stopPropagation(); closeTab(tab.appId) }}
                className="w-4 h-4 rounded flex items-center justify-center shrink-0
                           text-text-muted opacity-0 group-hover:opacity-100
                           hover:bg-border-base hover:text-text-primary
                           transition-opacity"
              >
                ×
              </button>
            )}
          </div>
        )
      })}

      {/* New tab button */}
      <button
        className="h-full px-3 text-text-muted hover:text-text-secondary
                   hover:bg-bg-hover transition-colors text-lg shrink-0
                   focus-blue"
        title="Open app (Cmd+K)"
        onClick={() => {
          // Trigger global search — dispatch a synthetic keydown
          window.dispatchEvent(
            new KeyboardEvent('keydown', { key: 'k', metaKey: true, bubbles: true })
          )
        }}
      >
        +
      </button>
    </div>
  )
}
