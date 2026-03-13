/**
 * TopHeader — global top bar.
 *
 * macOS Spotlight-style Cmd+K search:
 *  - Semi-transparent frosted glass panel centred on screen
 *  - Arrow keys navigate results; Enter opens; Escape closes
 *  - Powered by Fuse.js fuzzy search across all APPS
 */
import { useEffect, useRef, useState } from 'react'
import Fuse from 'fuse.js'
import { APPS } from '../data/apps.js'
import { useAppStore } from '../store/useAppStore.js'

const fuse = new Fuse(APPS, {
  threshold: 0.35,
  keys: [
    { name: 'label',       weight: 0.6 },
    { name: 'description', weight: 0.4 },
  ],
})

export default function TopHeader() {
  const { openTab } = useAppStore()
  const [open,    setOpen]    = useState(false)
  const [query,   setQuery]   = useState('')
  const [cursor,  setCursor]  = useState(0)
  const inputRef              = useRef(null)
  const listRef               = useRef(null)

  // Cmd+K / Ctrl+K
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
      setCursor(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  const results = query.trim()
    ? fuse.search(query).map(r => r.item)
    : APPS

  // Keyboard navigation inside the search overlay
  const handleKeyDown = e => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setCursor(c => Math.min(c + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setCursor(c => Math.max(c - 1, 0))
    } else if (e.key === 'Enter' && results[cursor]) {
      openTab(results[cursor].id)
      setOpen(false)
    }
  }

  // Scroll highlighted item into view
  useEffect(() => {
    const el = listRef.current?.children[cursor]
    el?.scrollIntoView({ block: 'nearest' })
  }, [cursor])

  // Reset cursor when results change
  useEffect(() => { setCursor(0) }, [query])

  const pick = appId => { openTab(appId); setOpen(false) }

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

      {/* ── macOS Spotlight-style search overlay ─────────── */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center pt-[18vh]
                     search-backdrop"
          onClick={() => setOpen(false)}
        >
          <div
            className="w-full max-w-[620px] rounded-2xl overflow-hidden
                       animate-fade-in"
            style={{
              background:   'rgba(12, 12, 22, 0.82)',
              backdropFilter: 'blur(48px) saturate(180%)',
              WebkitBackdropFilter: 'blur(48px) saturate(180%)',
              border:       '1px solid rgba(255,255,255,0.08)',
              boxShadow:    '0 32px 80px rgba(0,0,0,0.9), 0 0 0 1px rgba(0,127,255,0.12), 0 0 60px rgba(0,127,255,0.08)',
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Input row */}
            <div className="flex items-center gap-3 px-5 py-4">
              <svg width="18" height="18" viewBox="0 0 18 18" className="shrink-0 opacity-50">
                <circle cx="7.5" cy="7.5" r="5.5" stroke="#007FFF" strokeWidth="1.8" fill="none"/>
                <line x1="12" y1="12" x2="16" y2="16" stroke="#007FFF" strokeWidth="1.8"
                      strokeLinecap="round"/>
              </svg>
              <input
                ref={inputRef}
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search apps, docs, requirements…"
                className="flex-1 bg-transparent text-text-primary text-sm
                           placeholder:text-text-muted/60 outline-none"
              />
              <kbd className="text-[10px] text-text-muted border border-white/10
                              rounded px-1.5 py-0.5 bg-white/5">
                ESC
              </kbd>
            </div>

            {/* Thin separator line */}
            <div className="h-px bg-white/6 mx-5" />

            {/* Section label */}
            <p className="px-5 pt-3 pb-1 text-[10px] text-text-muted uppercase
                          tracking-widest">
              {query.trim() ? `Results for "${query}"` : 'All Apps'}
            </p>

            {/* Results list */}
            <div
              ref={listRef}
              className="max-h-[340px] overflow-y-auto p-2 pb-3"
            >
              {results.length === 0 ? (
                <p className="text-text-muted text-xs text-center py-8">
                  No results for "{query}"
                </p>
              ) : results.map((app, idx) => {
                const highlighted = idx === cursor
                return (
                  <button
                    key={app.id}
                    onMouseEnter={() => setCursor(idx)}
                    onClick={() => pick(app.id)}
                    className={`
                      w-full flex items-center gap-3.5 px-3 py-2.5 rounded-xl
                      transition-all text-left group
                      ${highlighted ? 'bg-blue-DEFAULT/15 border border-blue-DEFAULT/25'
                                    : 'hover:bg-white/5'}
                    `}
                  >
                    <span className="text-2xl leading-none shrink-0
                                     drop-shadow-[0_0_6px_rgba(0,127,255,0.4)]">
                      {app.emoji}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-text-primary text-sm font-semibold">
                        {app.label}
                      </p>
                      <p className="text-text-muted text-[11px] truncate mt-0.5">
                        {app.description}
                      </p>
                    </div>
                    {app.badge && (
                      <span className="ai-badge shrink-0 text-[9px]">{app.badge}</span>
                    )}
                    <span className={`
                      text-[10px] font-medium shrink-0 transition-opacity
                      ${highlighted ? 'text-blue-DEFAULT opacity-100' : 'opacity-0'}
                    `}>
                      Open ↵
                    </span>
                  </button>
                )
              })}
            </div>

            {/* Footer */}
            <div className="h-px bg-white/6 mx-5" />
            <div className="px-5 py-2.5 flex items-center gap-5 text-[10px]
                            text-text-muted">
              <span className="flex items-center gap-1.5">
                <kbd className="bg-white/8 border border-white/10 rounded px-1">↑↓</kbd>
                Navigate
              </span>
              <span className="flex items-center gap-1.5">
                <kbd className="bg-white/8 border border-white/10 rounded px-1">↵</kbd>
                Open
              </span>
              <span className="flex items-center gap-1.5">
                <kbd className="bg-white/8 border border-white/10 rounded px-1">ESC</kbd>
                Close
              </span>
              <span className="ml-auto ai-badge text-[9px]">Powered by EVOLV</span>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
