/**
 * TopHeader — unified 44px header bar combining tabs + global controls.
 *
 * Layout:
 *   ┌─[tabs scroll]──────────[+]──│──[search][proj][badges][AI][theme][avatar]─┐
 *
 * Replaces the old TopHeader (48px) + TabBar (36px) = 84px stack with a
 * single 44px bar, recovering 40px of content height on every page.
 *
 * macOS Spotlight-style Cmd+K search overlay is unchanged.
 */
import { useEffect, useRef, useState } from 'react'
import Fuse           from 'fuse.js'
import { APPS, APP_MAP } from '../data/apps.js'
import { useAppStore }   from '../store/useAppStore.js'
import AuditDrawer    from './AuditDrawer.jsx'

const PROFILE_ROLES = [
  'System Owner', 'QA Lead', 'Validation Lead',
  'IT Manager', 'Business Owner',
]

function initials(name) {
  const parts = (name ?? '').trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return 'U'
  if (parts.length === 1) return parts[0][0].toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

const fuse = new Fuse(APPS, {
  threshold: 0.35,
  keys: [
    { name: 'label',       weight: 0.6 },
    { name: 'description', weight: 0.4 },
  ],
})

export default function TopHeader() {
  const {
    openTab, theme, toggleTheme, fontSize, cycleFontSize,
    userProfile, setUserProfile,
    projects, activeProjectId,
    tabs, activeTabId, switchTab, closeTab,
  } = useAppStore()

  const activeProjectName = projects?.[activeProjectId]?.name ?? ''

  const [searchOpen,   setSearchOpen]   = useState(false)
  const [query,        setQuery]        = useState('')
  const [cursor,       setCursor]       = useState(0)
  const [profileOpen,  setProfileOpen]  = useState(false)
  const [auditOpen,    setAuditOpen]    = useState(false)

  const inputRef   = useRef(null)
  const listRef    = useRef(null)
  const profileRef = useRef(null)

  // Cmd+K / Ctrl+K to open search; Escape to close overlays
  useEffect(() => {
    const handler = e => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setSearchOpen(v => !v)
      }
      if (e.key === 'Escape') {
        setSearchOpen(false)
        setProfileOpen(false)
        setAuditOpen(false)
      }
      // `A` key opens audit drawer (outside inputs)
      if (e.key === 'a' || e.key === 'A') {
        if (!e.metaKey && !e.ctrlKey && !e.altKey) {
          const tag = document.activeElement?.tagName
          if (tag !== 'INPUT' && tag !== 'TEXTAREA' && tag !== 'SELECT') {
            e.preventDefault()
            setAuditOpen(v => !v)
          }
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Close profile on outside click
  useEffect(() => {
    if (!profileOpen) return
    const handler = e => {
      if (profileRef.current && !profileRef.current.contains(e.target))
        setProfileOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [profileOpen])

  // Focus search input when overlay opens
  useEffect(() => {
    if (searchOpen) {
      setQuery('')
      setCursor(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [searchOpen])

  const results = query.trim() ? fuse.search(query).map(r => r.item) : APPS

  const handleKeyDown = e => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setCursor(c => Math.min(c + 1, results.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setCursor(c => Math.max(c - 1, 0)) }
    else if (e.key === 'Enter' && results[cursor]) { openTab(results[cursor].id); setSearchOpen(false) }
  }

  useEffect(() => {
    listRef.current?.children[cursor]?.scrollIntoView({ block: 'nearest' })
  }, [cursor])

  useEffect(() => { setCursor(0) }, [query])

  const pick = appId => { openTab(appId); setSearchOpen(false) }

  return (
    <>
      {/* ── Unified header bar (44px) ─────────────────────── */}
      <header className="h-11 shrink-0 flex items-stretch
                         bg-bg-surface border-b border-border-base z-10">

        {/* ── Tab strip (left, scrollable) ──────────────── */}
        <div className="flex items-stretch overflow-x-auto shrink-0
                        max-w-[55%] select-none">
          {tabs.map(tab => {
            const app      = APP_MAP[tab.appId]
            if (!app) return null
            const isActive = activeTabId === tab.appId
            const pinned   = !app.closeable

            return (
              <div
                key={tab.appId}
                onClick={() => switchTab(tab.appId)}
                className={`
                  tab-item flex items-center gap-1.5 px-3 h-full
                  border-r border-border-base cursor-pointer
                  text-xs transition-colors shrink-0 group
                  min-w-[72px] max-w-[140px]
                  ${isActive
                    ? 'active bg-bg-base text-text-primary'
                    : 'text-text-muted hover:bg-bg-hover hover:text-text-secondary'}
                `}
              >
                <span className="flex-1 truncate font-medium">{app.label}</span>
                {pinned ? (
                  <span className="text-[10px] text-text-muted shrink-0
                                   opacity-30 font-mono">·</span>
                ) : (
                  <button
                    onClick={e => { e.stopPropagation(); closeTab(tab.appId) }}
                    className="w-3.5 h-3.5 rounded flex items-center justify-center
                               shrink-0 text-text-muted opacity-0 group-hover:opacity-70
                               hover:opacity-100 hover:text-text-primary
                               transition-opacity text-sm leading-none"
                  >
                    ×
                  </button>
                )}
              </div>
            )
          })}

          {/* New-tab button → triggers Cmd+K */}
          <button
            className="px-3 h-full text-text-muted hover:text-text-secondary
                       hover:bg-bg-hover transition-colors text-base shrink-0
                       focus-blue border-r border-border-base"
            title="Open app (Cmd+K)"
            onClick={() => setSearchOpen(true)}
          >
            +
          </button>
        </div>

        {/* ── Divider ───────────────────────────────────── */}
        <div className="w-px bg-border-base shrink-0 my-2" />

        {/* ── Right controls ────────────────────────────── */}
        <div className="flex items-center gap-3 px-4 flex-1 min-w-0">

          {/* Search trigger */}
          <button
            onClick={() => setSearchOpen(true)}
            className="flex items-center gap-2 flex-1 max-w-xs h-7
                       bg-bg-card border border-border-base rounded-lg
                       px-3 text-text-muted text-xs
                       hover:border-blue-DEFAULT/40 hover:text-text-secondary
                       transition-colors focus-blue"
          >
            <svg width="12" height="12" viewBox="0 0 14 14" className="shrink-0 opacity-50">
              <circle cx="5.5" cy="5.5" r="4" stroke="currentColor"
                      strokeWidth="1.5" fill="none"/>
              <line x1="9" y1="9" x2="13" y2="13" stroke="currentColor"
                    strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <span className="flex-1 text-left truncate">Search…</span>
            <kbd className="hidden sm:flex items-center text-[9px]
                            bg-bg-hover border border-border-base rounded px-1">
              ⌘K
            </kbd>
          </button>

          {/* Active project pill */}
          {activeProjectName && (
            <span className="hidden lg:flex items-center gap-1.5 text-[10px]
                             text-text-muted border border-border-base
                             bg-bg-card rounded px-2 py-1 shrink-0 max-w-[120px]">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-DEFAULT shrink-0" />
              <span className="truncate">{activeProjectName}</span>
            </span>
          )}

          {/* Compliance badges */}
          <div className="hidden xl:flex items-center gap-1.5">
            {['21 CFR 11', 'GAMP 5', 'FDA AI'].map(b => (
              <span key={b}
                className="text-[9px] bg-bg-card border border-border-base
                           text-text-muted rounded px-1.5 py-0.5 whitespace-nowrap">
                {b} ✓
              </span>
            ))}
          </div>

          {/* Audit trail toggle */}
          <button
            onClick={() => setAuditOpen(v => !v)}
            title="Audit trail (A)"
            className={`w-7 h-7 rounded-full border flex items-center
                        justify-center shrink-0 transition-colors focus-blue
                        ${auditOpen
                          ? 'border-blue-DEFAULT bg-blue-dim text-blue-DEFAULT'
                          : 'border-border-base bg-bg-card text-text-muted hover:border-blue-DEFAULT/40'}`}
          >
            <svg width="12" height="12" viewBox="0 0 14 14">
              <circle cx="7" cy="7" r="6" stroke="currentColor"
                      strokeWidth="1.5" fill="none"/>
              <polyline points="7,4 7,7 9.5,9.5" stroke="currentColor"
                        strokeWidth="1.5" strokeLinecap="round" fill="none"/>
            </svg>
          </button>

          {/* EVOLV AI badge */}
          <span className="ai-badge hidden md:inline animate-pulse-lime shrink-0">
            EVOLV AI
          </span>

          {/* Font size toggle */}
          <button
            onClick={cycleFontSize}
            title={`Font size: ${fontSize} — click to cycle (Normal → Large → XL)`}
            className={`
              h-7 px-2 rounded-full border flex items-center justify-center
              shrink-0 transition-colors focus-blue font-semibold
              ${fontSize !== 'normal'
                ? 'border-blue-DEFAULT/50 bg-blue-dim text-blue-DEFAULT'
                : 'border-border-base bg-bg-card text-text-muted hover:border-blue-DEFAULT/40'}
            `}
          >
            <span className={`leading-none ${
              fontSize === 'xl' ? 'text-sm' : 'text-xs'
            }`}>
              {fontSize === 'normal' ? 'A' : fontSize === 'large' ? 'A+' : 'A++'}
            </span>
          </button>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="w-7 h-7 rounded-full border border-border-base
                       flex items-center justify-center text-sm shrink-0
                       bg-bg-card hover:border-blue-DEFAULT/40
                       transition-colors focus-blue"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>

          {/* User avatar + profile panel */}
          <div className="relative shrink-0" ref={profileRef}>
            <button
              onClick={() => setProfileOpen(v => !v)}
              title="User profile"
              className={`
                w-7 h-7 rounded-full bg-gradient-to-br
                from-blue-DEFAULT to-lime-DEFAULT
                flex items-center justify-center
                text-white text-[11px] font-bold cursor-pointer
                shadow-[0_0_10px_rgba(0,127,255,0.3)]
                transition-opacity hover:opacity-80
                ${profileOpen ? 'ring-2 ring-blue-DEFAULT/50' : ''}
              `}
            >
              {initials(userProfile?.name)}
            </button>

            {profileOpen && (
              <div
                className="absolute right-0 top-9 w-64 rounded-xl z-50
                           border border-border-base bg-bg-surface
                           shadow-xl animate-fade-in p-4"
              >
                <p className="text-[10px] text-text-muted uppercase
                              tracking-widest mb-3 font-semibold">
                  User Profile
                </p>
                <div className="flex flex-col gap-1 mb-3">
                  <label className="text-[10px] text-text-muted">Full Name</label>
                  <input
                    value={userProfile?.name ?? ''}
                    onChange={e => setUserProfile('name', e.target.value)}
                    placeholder="Your full name…"
                    className="evolv-input text-xs px-2 py-1.5 w-full"
                  />
                </div>
                <div className="flex flex-col gap-1 mb-3">
                  <label className="text-[10px] text-text-muted">Role</label>
                  <select
                    value={userProfile?.role ?? ''}
                    onChange={e => setUserProfile('role', e.target.value)}
                    className="evolv-input evolv-select text-xs px-2 py-1.5 w-full"
                  >
                    <option value="">Select role…</option>
                    {PROFILE_ROLES.map(r => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>
                <div className="flex flex-col gap-1 mb-3">
                  <label className="text-[10px] text-text-muted">Organisation</label>
                  <input
                    value={userProfile?.org ?? ''}
                    onChange={e => setUserProfile('org', e.target.value)}
                    placeholder="Your organisation…"
                    className="evolv-input text-xs px-2 py-1.5 w-full"
                  />
                </div>
                {userProfile?.role && (
                  <div className="mt-2 text-[10px] text-blue-DEFAULT
                                  bg-blue-dim px-2 py-1 rounded text-center
                                  border border-blue-DEFAULT/20">
                    {userProfile.role}
                    {userProfile.org ? ` — ${userProfile.org}` : ''}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* ── Cmd+K Search overlay ──────────────────────────── */}
      {/* ── Audit trail drawer ────────────────────────────── */}
      <AuditDrawer open={auditOpen} onClose={() => setAuditOpen(false)} />

      {searchOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center
                     pt-[18vh] search-backdrop"
          onClick={() => setSearchOpen(false)}
        >
          <div
            className="w-full max-w-[620px] rounded-2xl overflow-hidden
                       animate-fade-in"
            style={{
              background:          'rgba(12,12,22,0.82)',
              backdropFilter:      'blur(48px) saturate(180%)',
              WebkitBackdropFilter:'blur(48px) saturate(180%)',
              border:              '1px solid rgba(255,255,255,0.08)',
              boxShadow:           '0 32px 80px rgba(0,0,0,0.9), 0 0 0 1px rgba(0,127,255,0.12)',
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Input row */}
            <div className="flex items-center gap-3 px-5 py-4">
              <svg width="18" height="18" viewBox="0 0 18 18" className="shrink-0 opacity-50">
                <circle cx="7.5" cy="7.5" r="5.5" stroke="#007FFF"
                        strokeWidth="1.8" fill="none"/>
                <line x1="12" y1="12" x2="16" y2="16" stroke="#007FFF"
                      strokeWidth="1.8" strokeLinecap="round"/>
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

            <div className="h-px bg-white/6 mx-5" />

            <p className="px-5 pt-3 pb-1 text-[10px] text-text-muted
                          uppercase tracking-widest">
              {query.trim() ? `Results for "${query}"` : 'All Apps'}
            </p>

            <div ref={listRef} className="max-h-[340px] overflow-y-auto p-2 pb-3">
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
                      ${highlighted
                        ? 'bg-blue-DEFAULT/15 border border-blue-DEFAULT/25'
                        : 'hover:bg-white/5'}
                    `}
                  >
                    <span
                      className="w-8 h-8 rounded-lg flex items-center justify-center
                                 text-[11px] font-bold shrink-0"
                      style={{
                        background: (app.accentColor ?? '#007FFF') + '20',
                        border:     `1px solid ${app.accentColor ?? '#007FFF'}35`,
                        color:       app.accentColor ?? '#007FFF',
                      }}
                    >
                      {app.label.replace(/[^a-zA-Z ]/g, '').split(' ')
                        .filter(Boolean).slice(0, 2)
                        .map(w => w[0]).join('').toUpperCase() ||
                        app.label.slice(0, 2).toUpperCase()}
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
                      <span className="ai-badge shrink-0 text-[9px]">
                        {app.badge}
                      </span>
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
