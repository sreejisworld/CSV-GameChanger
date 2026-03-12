/**
 * TopHeader — global top bar.
 *
 * Contains: EVOLV wordmark (when sidebar collapsed), Impact Search,
 * compliance badges, and a user avatar placeholder.
 */
import { useEffect, useRef, useState } from 'react'
import Fuse from 'fuse.js'
import { APPS } from '../data/apps.js'

const fuse = new Fuse(APPS, {
  threshold: 0.35,
  keys: [
    { name: 'label',       weight: 0.6 },
    { name: 'description', weight: 0.4 },
  ],
})

export default function TopHeader({ openTab }) {
  const [open,  setOpen]  = useState(false)
  const [query, setQuery] = useState('')
  const inputRef          = useRef(null)

  // Cmd+K / Ctrl+K to open
  useEffect(() => {
    const handler = e => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen(v => !v)
      }
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  useEffect(() => {
    if (open) {
      setQuery('')
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  const results = query.trim()
    ? fuse.search(query).map(r => r.item)
    : APPS

  return (
    <>
      {/* ── Header bar ─────────────────────────────────── */}
      <header className="h-12 shrink-0 flex items-center gap-4 px-4
                         bg-bg-surface/80 backdrop-blur border-b border-border-base
                         z-10">

        {/* Search trigger */}
        <button
          onClick={() => setOpen(true)}
          className="flex items-center gap-2 flex-1 max-w-md h-8
                     bg-bg-card border border-border-base rounded-lg
                     px-3 text-text-muted text-xs
                     hover:border-border-blue hover:text-text-secondary
                     transition-colors focus-blue"
        >
          <span className="text-sm">🔍</span>
          <span className="flex-1 text-left">Search apps, docs, requirements…</span>
          <kbd className="hidden sm:flex items-center gap-0.5 text-[9px]
                          bg-bg-hover border border-border-base rounded px-1.5 py-0.5">
            ⌘K
          </kbd>
        </button>

        {/* Compliance badges */}
        <div className="hidden md:flex items-center gap-2">
          {['21 CFR Part 11', 'GAMP 5', 'FDA AI 2026'].map(b => (
            <span key={b}
              className="text-[9px] bg-bg-card border border-border-base
                         text-text-muted rounded px-2 py-1">
              {b} ✓
            </span>
          ))}
        </div>

        {/* EVOLV AI badge */}
        <span className="ai-badge hidden sm:inline animate-pulse-lime">
          EVOLV AI
        </span>

        {/* User avatar */}
        <div className="w-7 h-7 rounded-full bg-gradient-to-br
                        from-blue-DEFAULT to-lime-DEFAULT
                        flex items-center justify-center shrink-0
                        text-white text-[11px] font-bold cursor-pointer
                        shadow-[0_0_10px_rgba(0,127,255,0.3)]">
          U
        </div>
      </header>

      {/* ── Search overlay ──────────────────────────────── */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center pt-20
                     search-backdrop"
          onClick={() => setOpen(false)}
        >
          <div
            className="w-full max-w-xl glass rounded-2xl overflow-hidden
                       shadow-[0_24px_64px_rgba(0,0,0,0.8),0_0_40px_rgba(0,127,255,0.15)]
                       animate-fade-in"
            onClick={e => e.stopPropagation()}
          >
            {/* Input */}
            <div className="flex items-center gap-3 px-4 py-3
                            border-b border-border-base">
              <span className="text-blue-DEFAULT text-lg">🔍</span>
              <input
                ref={inputRef}
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Open an app or search…"
                className="flex-1 bg-transparent text-text-primary text-sm
                           placeholder:text-text-muted outline-none"
              />
              <kbd className="text-[9px] text-text-muted border border-border-base
                              rounded px-1.5 py-0.5">ESC</kbd>
            </div>

            {/* Results */}
            <div className="max-h-80 overflow-y-auto p-2">
              {results.length === 0 ? (
                <p className="text-text-muted text-xs text-center py-6">
                  No results for "{query}"
                </p>
              ) : results.map(app => (
                <button
                  key={app.id}
                  onClick={() => { openTab(app.id); setOpen(false) }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                             hover:bg-bg-hover transition-colors text-left group"
                >
                  <span className="text-2xl leading-none">{app.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-text-primary text-sm font-medium">{app.label}</p>
                    <p className="text-text-muted text-xs truncate">{app.description}</p>
                  </div>
                  {app.badge && (
                    <span className="ai-badge shrink-0">{app.badge}</span>
                  )}
                  <span className="text-text-muted text-xs opacity-0 group-hover:opacity-100
                                   transition-opacity shrink-0">
                    Open →
                  </span>
                </button>
              ))}
            </div>

            {/* Footer hint */}
            <div className="neon-sep" />
            <div className="px-4 py-2 flex items-center gap-4 text-[10px] text-text-muted">
              <span><kbd className="bg-bg-hover border border-border-base rounded px-1">↑↓</kbd> Navigate</span>
              <span><kbd className="bg-bg-hover border border-border-base rounded px-1">↵</kbd> Open</span>
              <span><kbd className="bg-bg-hover border border-border-base rounded px-1">ESC</kbd> Close</span>
              <span className="ml-auto ai-badge">Powered by EVOLV</span>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
