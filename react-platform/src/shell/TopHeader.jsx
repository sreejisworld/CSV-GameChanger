/**
 * TopHeader — unified 44px header bar combining tabs + global controls.
 *
 * Layout (Sprint 30 — Navigation Diet):
 *   ┌─[tabs scroll]─[+]──│──[search][proj pill][audit][avatar]─┐
 *
 * Sprint 30 removed: EVOLV AI vanity badge, the 3 compliance pills
 * (21 CFR 11 / GAMP 5 / FDA AI), and the standalone font-size button.
 * Font size moved into the avatar dropdown as a segmented control.
 *
 * Sprint 31.2 — Cmd+K command palette upgrade:
 *   • Empty-query state shows sectioned picker (Recent / Commands /
 *     Lifecycle / Intelligence / Tools) instead of one long flat list
 *   • Typed-query state runs Fuse over apps + commands together so
 *     "demo" jumps to the demo loader, "audit" jumps to the trail
 *   • Recent apps tracked in store via `recentApps` (FIFO max 5,
 *     persisted across reloads)
 *   • Project-switcher commands generated from `projects` map
 */
import { useEffect, useMemo, useRef, useState } from 'react'
import Fuse           from 'fuse.js'
import { APPS, APP_MAP, NAV_GROUPS } from '../data/apps.js'
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

// Module-level Fuse over apps only — used as a fallback when commands
// haven't been built yet. The component-level Fuse (combinedFuse) below
// searches apps + commands together once the commands array is materialised.
const fuse = new Fuse(APPS, {
  threshold: 0.35,
  keys: [
    { name: 'label',       weight: 0.6 },
    { name: 'description', weight: 0.4 },
  ],
})

export default function TopHeader() {
  // Sprint 29: dark mode deleted — `theme` and `toggleTheme` removed
  // from destructure since we no longer surface a theme toggle.
  // Sprint 31.2: pull `recentApps`, `loadDemoProject`, `switchProject`
  // for the upgraded Cmd+K command palette.
  const {
    openTab, fontSize, cycleFontSize,
    userProfile, setUserProfile,
    projects, activeProjectId,
    tabs, activeTabId, switchTab, closeTab,
    recentApps, loadDemoProject, switchProject,
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

  // ── Sprint 31.2 — command palette actions ────────────────────
  // Each action is a "fake app row" that runs a function instead of
  // opening a tab. Built fresh each render so closures see the
  // latest store actions / project list.
  // Convention:
  //   id          unique within the overlay (`cmd:*` prefix avoids
  //               collision with app ids)
  //   kind        'command' (apps are kind: 'app')
  //   label       what the user types / sees
  //   description one-line context shown under the label
  //   accentColor swatch for the rounded-square monogram on the left
  //   run()       invoked when the row is picked (Enter / click)
  const commands = useMemo(() => {
    const list = [
      {
        id:          'cmd:demo',
        kind:        'command',
        label:       'Open Demo project',
        description: 'Load the LabCore LIMS sample project — pre-populated through Verify',
        accentColor: '#a855f7',
        run: () => loadDemoProject(),
      },
      {
        id:          'cmd:audit',
        kind:        'command',
        label:       'Toggle audit drawer',
        description: 'Open the live 21 CFR Part 11 audit trail side panel (hotkey: A)',
        accentColor: '#007FFF',
        run: () => setAuditOpen(v => !v),
      },
      {
        id:          'cmd:font-reset',
        kind:        'command',
        label:       'Reset reading size',
        description: 'Restore default body text size (A / A+ / A++)',
        accentColor: '#64748b',
        run: () => {
          // cycleFontSize advances by one — call until we land on 'normal'
          for (let i = 0; i < 3; i++) {
            if (useAppStore.getState().fontSize === 'normal') break
            cycleFontSize()
          }
        },
      },
      {
        id:          'cmd:home',
        kind:        'command',
        label:       'Go to Home',
        description: 'Jump back to the EVOLV LaunchPad command centre',
        accentColor: '#007FFF',
        run: () => openTab('home'),
      },
    ]
    // One project-switch command per registered project, except the
    // currently active one (no-op).
    Object.values(projects ?? {}).forEach(p => {
      if (!p?.id || p.id === activeProjectId) return
      list.push({
        id:          `cmd:project:${p.id}`,
        kind:        'command',
        label:       `Switch project: ${p.name}`,
        description: p.isDemo
          ? 'Demo dataset (LabCore LIMS) — safe to explore'
          : 'User project — last edited state preserved',
        accentColor: '#32CD32',
        run: () => switchProject(p.id),
      })
    })
    return list
  }, [projects, activeProjectId, loadDemoProject, switchProject, cycleFontSize, openTab])

  // Combined Fuse over apps + commands — used when the user types.
  // Memoised so we don't rebuild the index on every keystroke; only on
  // command-list changes (project added/switched).
  const combinedEntries = useMemo(
    () => [
      ...APPS.map(a => ({ ...a, kind: 'app' })),
      ...commands,
    ],
    [commands]
  )
  const combinedFuse = useMemo(
    () => new Fuse(combinedEntries, {
      threshold: 0.35,
      keys: [
        { name: 'label',       weight: 0.6 },
        { name: 'description', weight: 0.4 },
      ],
    }),
    [combinedEntries]
  )

  // ── Sectioned palette layout ────────────────────────────────
  // When the query is empty, we partition results into named sections
  // (Recent / Commands / Lifecycle / Intelligence / Tools) so the
  // overlay reads as a curated picker, not a dump. When the user types,
  // we collapse to a single flat "Results" section over apps + commands
  // ranked by Fuse — that's the moment they want fewest clicks, most
  // relevance.
  const sections = useMemo(() => {
    if (query.trim()) {
      const flat = combinedFuse.search(query).map(r => r.item)
      return [{ label: `Results for "${query}"`, items: flat }]
    }
    const recentItems = (recentApps ?? [])
      .map(id => APP_MAP[id])
      .filter(Boolean)
      .map(a => ({ ...a, kind: 'app' }))
    const groupItems = label => {
      const grp = NAV_GROUPS.find(g => g.label === label)
      if (!grp) return []
      return grp.items
        .map(id => APP_MAP[id])
        .filter(Boolean)
        .map(a => ({ ...a, kind: 'app' }))
    }
    return [
      { label: 'Recent',       items: recentItems },
      { label: 'Commands',     items: commands },
      { label: 'Lifecycle',    items: groupItems('Lifecycle') },
      { label: 'Intelligence', items: groupItems('Intelligence') },
      { label: 'Tools',        items: groupItems('Tools') },
    ].filter(s => s.items.length > 0)
  }, [query, combinedFuse, recentApps, commands])

  // Flat list of pickable items in render order — drives keyboard nav.
  const flatItems = useMemo(
    () => sections.flatMap(s => s.items),
    [sections]
  )

  const pick = item => {
    if (item.kind === 'command') item.run()
    else openTab(item.id)
    setSearchOpen(false)
  }

  const handleKeyDown = e => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setCursor(c => Math.min(c + 1, flatItems.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setCursor(c => Math.max(c - 1, 0))
    } else if (e.key === 'Enter' && flatItems[cursor]) {
      pick(flatItems[cursor])
    }
  }

  useEffect(() => {
    listRef.current
      ?.querySelectorAll('[data-row="1"]')
      ?.[cursor]
      ?.scrollIntoView({ block: 'nearest' })
  }, [cursor])

  useEffect(() => { setCursor(0) }, [query])

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

          {/* Audit trail toggle */}
          {/* Sprint 30 — kept (it's a frequently-used inspector, with
              an `A` hotkey). EVOLV AI badge + 3 compliance pills + the
              standalone font-size button were removed in this sprint
              to declutter the header per April demo feedback ("too
              busy, doesn't feel like Claude / ChatGPT"). Font size
              moved into the avatar dropdown — it's a preference, not
              a frequent action. Compliance certs are surfaced on the
              Home dashboard and Release page where they belong. */}
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

          {/* User avatar + profile panel */}
          {/* Sprint 29: dark/light theme toggle removed — single warm
              light theme is the product surface going forward.
              Sprint 30: font-size cycler moved into this dropdown
              (it's a preference, fits with role/org). */}
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
                {/* Sprint 30 — font-size lives here now (preference
                    bucket alongside name / role / org). Three-segment
                    pill control mirrors the old standalone button's
                    A / A+ / A++ semantics. */}
                <div className="flex flex-col gap-1 mb-3">
                  <label className="text-[10px] text-text-muted">
                    Reading size
                  </label>
                  <div className="flex items-stretch border border-border-base
                                  rounded-lg overflow-hidden">
                    {['normal', 'large', 'xl'].map(size => {
                      const isActive = fontSize === size
                      const labelMap = { normal: 'A', large: 'A+', xl: 'A++' }
                      return (
                        <button
                          key={size}
                          onClick={() => {
                            // cycleFontSize advances by one — call until
                            // we land on the requested size (max 3 hops).
                            for (let i = 0; i < 3; i++) {
                              if (useAppStore.getState().fontSize === size) break
                              cycleFontSize()
                            }
                          }}
                          className={`
                            flex-1 py-1 text-[11px] font-semibold transition-colors
                            ${isActive
                              ? 'bg-blue-dim text-blue-DEFAULT'
                              : 'bg-bg-card text-text-muted hover:bg-bg-hover'}
                            ${size !== 'normal' ? 'border-l border-border-base' : ''}
                          `}
                        >
                          {labelMap[size]}
                        </button>
                      )
                    })}
                  </div>
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
          {/* Sprint 29: warm-light overlay (was hardcoded dark glass).
              Uses pure-white card on the warm cream backdrop so it
              reads as the focal element without going clinical. */}
          <div
            className="w-full max-w-[620px] rounded-2xl overflow-hidden
                       animate-fade-in"
            style={{
              background:          'rgba(255,255,255,0.96)',
              backdropFilter:      'blur(48px) saturate(180%)',
              WebkitBackdropFilter:'blur(48px) saturate(180%)',
              border:              '1px solid rgba(42,40,37,0.08)',
              boxShadow:           '0 32px 80px rgba(42,40,37,0.18), 0 0 0 1px rgba(0,127,255,0.10)',
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
              <kbd className="text-[10px] text-text-muted border border-border-base
                              rounded px-1.5 py-0.5 bg-bg-hover">
                ESC
              </kbd>
            </div>

            <div className="h-px bg-border-base mx-5" />

            {/* Sprint 31.2 — sectioned palette. We track an absolute
                index across sections so the keyboard cursor (↑/↓)
                threads through all rows in render order. */}
            <div ref={listRef} className="max-h-[420px] overflow-y-auto p-2 pb-3">
              {flatItems.length === 0 ? (
                <p className="text-text-muted text-xs text-center py-8">
                  No results for "{query}"
                </p>
              ) : (() => {
                let absoluteIdx = 0
                return sections.map(section => (
                  <div key={section.label} className="mb-2 last:mb-0">
                    <p className="px-3 pt-2 pb-1 text-[10px] text-text-muted
                                  uppercase tracking-widest">
                      {section.label}
                    </p>
                    {section.items.map(item => {
                      const idx = absoluteIdx++
                      const highlighted = idx === cursor
                      const isCommand   = item.kind === 'command'
                      return (
                        <button
                          key={item.id}
                          data-row="1"
                          onMouseEnter={() => setCursor(idx)}
                          onClick={() => pick(item)}
                          className={`
                            w-full flex items-center gap-3.5 px-3 py-2.5 rounded-xl
                            transition-all text-left group
                            ${highlighted
                              ? 'bg-blue-DEFAULT/10 border border-blue-DEFAULT/25'
                              : 'hover:bg-bg-hover'}
                          `}
                        >
                          <span
                            className="w-8 h-8 rounded-lg flex items-center justify-center
                                       text-[11px] font-bold shrink-0"
                            style={{
                              background: (item.accentColor ?? '#007FFF') + '20',
                              border:     `1px solid ${item.accentColor ?? '#007FFF'}35`,
                              color:       item.accentColor ?? '#007FFF',
                            }}
                          >
                            {isCommand
                              ? '⌘'
                              : (item.label.replace(/[^a-zA-Z ]/g, '').split(' ')
                                  .filter(Boolean).slice(0, 2)
                                  .map(w => w[0]).join('').toUpperCase() ||
                                  item.label.slice(0, 2).toUpperCase())}
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="text-text-primary text-sm font-semibold">
                              {item.label}
                            </p>
                            <p className="text-text-muted text-[11px] truncate mt-0.5">
                              {item.description}
                            </p>
                          </div>
                          {item.badge && (
                            <span className="ai-badge shrink-0 text-[9px]">
                              {item.badge}
                            </span>
                          )}
                          {isCommand && !item.badge && (
                            <span className="shrink-0 text-[9px] font-medium
                                             text-text-muted border border-border-base
                                             rounded px-1.5 py-0.5 bg-bg-hover">
                              run
                            </span>
                          )}
                          <span className={`
                            text-[10px] font-medium shrink-0 transition-opacity
                            ${highlighted ? 'text-blue-DEFAULT opacity-100' : 'opacity-0'}
                          `}>
                            {isCommand ? 'Run ↵' : 'Open ↵'}
                          </span>
                        </button>
                      )
                    })}
                  </div>
                ))
              })()}
            </div>

            <div className="h-px bg-border-base mx-5" />
            <div className="px-5 py-2.5 flex items-center gap-5 text-[10px]
                            text-text-muted">
              <span className="flex items-center gap-1.5">
                <kbd className="bg-bg-hover border border-border-base rounded px-1">↑↓</kbd>
                Navigate
              </span>
              <span className="flex items-center gap-1.5">
                <kbd className="bg-bg-hover border border-border-base rounded px-1">↵</kbd>
                Open
              </span>
              <span className="flex items-center gap-1.5">
                <kbd className="bg-bg-hover border border-border-base rounded px-1">ESC</kbd>
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
