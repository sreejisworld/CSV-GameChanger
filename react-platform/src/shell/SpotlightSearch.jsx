/**
 * SpotlightSearch — Global Cmd/Ctrl+K quick-open modal.
 *
 * Filters all apps in APP_MAP by label, description, and badge.
 * Results grouped by nav group. Click or Enter to open the app.
 * Esc to close.
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { NAV_GROUPS, APP_MAP } from '../data/apps.js'
import { useAppStore }         from '../store/useAppStore.js'

// Flat list of all searchable apps in display order
const ALL_APPS = NAV_GROUPS.flatMap(group =>
  group.items
    .map(id => ({ ...APP_MAP[id], id, group: group.label }))
    .filter(Boolean)
)

function highlight(text, query) {
  if (!query || !text) return text
  const idx = text.toLowerCase().indexOf(query.toLowerCase())
  if (idx === -1) return text
  return (
    <>
      {text.slice(0, idx)}
      <mark className="bg-blue-DEFAULT/30 text-blue-DEFAULT rounded-sm px-0.5">
        {text.slice(idx, idx + query.length)}
      </mark>
      {text.slice(idx + query.length)}
    </>
  )
}

export default function SpotlightSearch() {
  const [open,    setOpen]    = useState(false)
  const [query,   setQuery]   = useState('')
  const [focused, setFocused] = useState(0)
  const inputRef  = useRef(null)
  const listRef   = useRef(null)
  const { openTab } = useAppStore()

  // Keyboard shortcut to open
  useEffect(() => {
    const handler = e => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen(v => !v)
        setQuery('')
        setFocused(0)
      }
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Focus input when modal opens
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50)
  }, [open])

  const results = query.trim()
    ? ALL_APPS.filter(app => {
        if (app.locked) return false
        const q = query.toLowerCase()
        return (
          app.label?.toLowerCase().includes(q) ||
          app.description?.toLowerCase().includes(q) ||
          app.badge?.toLowerCase().includes(q) ||
          app.group?.toLowerCase().includes(q)
        )
      })
    : ALL_APPS.filter(a => !a.locked)

  // Group results
  const grouped = NAV_GROUPS.map(g => ({
    label: g.label,
    items: results.filter(r => r.group === g.label),
  })).filter(g => g.items.length > 0)

  // Flat index for keyboard nav
  const flat = grouped.flatMap(g => g.items)

  const handleKeyDown = e => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setFocused(v => Math.min(v + 1, flat.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setFocused(v => Math.max(v - 1, 0))
    } else if (e.key === 'Enter') {
      const app = flat[focused]
      if (app) { openTab(app.id); setOpen(false) }
    }
  }

  // Scroll focused item into view
  useEffect(() => {
    const el = listRef.current?.querySelector('[data-focused="true"]')
    el?.scrollIntoView({ block: 'nearest' })
  }, [focused])

  const handleSelect = id => {
    openTab(id)
    setOpen(false)
  }

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
        onClick={() => setOpen(false)}
      />

      {/* Modal */}
      <div
        className="fixed left-1/2 top-[20%] -translate-x-1/2 z-50
                   w-full max-w-lg"
        onKeyDown={handleKeyDown}
      >
        <div className="bg-bg-card border border-border-bright rounded-xl
                        shadow-[0_24px_64px_rgba(0,0,0,0.6)] overflow-hidden">

          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3
                          border-b border-border-base">
            <span className="text-text-muted text-base shrink-0">🔍</span>
            <input
              ref={inputRef}
              value={query}
              onChange={e => { setQuery(e.target.value); setFocused(0) }}
              placeholder="Search apps…"
              className="flex-1 bg-transparent text-sm text-text-primary
                         placeholder:text-text-muted outline-none"
            />
            <kbd className="text-[10px] text-text-muted border border-border-base
                            rounded px-1.5 py-0.5 shrink-0">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <div
            ref={listRef}
            className="overflow-y-auto max-h-80 py-2"
          >
            {grouped.length === 0 ? (
              <p className="px-4 py-6 text-center text-text-muted text-xs">
                No apps found for "{query}"
              </p>
            ) : (
              grouped.map(group => {
                return (
                  <div key={group.label}>
                    <p className="px-4 pt-3 pb-1 text-[9px] font-semibold
                                  text-text-muted uppercase tracking-widest">
                      {group.label}
                    </p>
                    {group.items.map(app => {
                      const idx     = flat.indexOf(app)
                      const isFocus = idx === focused
                      return (
                        <button
                          key={app.id}
                          data-focused={isFocus}
                          onClick={() => handleSelect(app.id)}
                          className={`
                            w-full flex items-center gap-3 px-4 py-2.5
                            text-left transition-colors
                            ${isFocus
                              ? 'bg-blue-dim border-l-2 border-blue-DEFAULT'
                              : 'hover:bg-bg-hover border-l-2 border-transparent'}
                          `}
                        >
                          <span className="text-lg shrink-0">{app.emoji}</span>
                          <div className="min-w-0 flex-1">
                            <p className="text-xs font-medium text-text-primary truncate">
                              {highlight(app.label, query)}
                            </p>
                            {app.description && (
                              <p className="text-[10px] text-text-muted truncate mt-0.5">
                                {highlight(app.description, query)}
                              </p>
                            )}
                          </div>
                          {app.badge && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded border
                                             border-blue-DEFAULT/30 text-blue-DEFAULT
                                             bg-blue-dim shrink-0">
                              {app.badge}
                            </span>
                          )}
                          {isFocus && (
                            <kbd className="text-[10px] text-text-muted border
                                            border-border-base rounded px-1 py-0.5
                                            shrink-0">
                              ↵
                            </kbd>
                          )}
                        </button>
                      )
                    })}
                  </div>
                )
              })
            )}
          </div>

          {/* Footer hint */}
          <div className="flex items-center gap-4 px-4 py-2
                          border-t border-border-base">
            {[
              ['↑↓', 'navigate'],
              ['↵',  'open'],
              ['ESC','close'],
            ].map(([key, label]) => (
              <span key={key} className="flex items-center gap-1
                                         text-[10px] text-text-muted">
                <kbd className="border border-border-base rounded px-1 py-0.5">
                  {key}
                </kbd>
                {label}
              </span>
            ))}
            <span className="ml-auto text-[10px] text-text-muted">
              {flat.length} app{flat.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      </div>
    </>
  )
}
