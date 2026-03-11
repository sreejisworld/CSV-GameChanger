/**
 * GlobalSearchBar — Cmd+K command-palette style search.
 *
 * Features:
 *  - Cmd+K / Ctrl+K keyboard shortcut to open
 *  - Fuzzy search via Fuse.js (useSearch hook)
 *  - Results grouped by: Requirements | Test Scripts | Risks
 *  - Hover → BlastRadiusPopover shows impact data
 *  - Status indicator: red glow for issues, green check for valid
 */
import { useRef, useState } from 'react'
import { useSearch } from '../hooks/useSearch.js'
import BlastRadiusPopover from './BlastRadiusPopover.jsx'

const STATUS_META = {
  approved:   { label: '✓ Approved',   cls: 'text-green-400' },
  in_review:  { label: '⏳ In Review', cls: 'text-yellow-400' },
  draft:      { label: '✏ Draft',      cls: 'text-slate-500'  },
  failed:     { label: '✗ Failed',     cls: 'text-red-400'    },
  open_issue: { label: '⚠ Issue',      cls: 'text-orange-400' },
}

const TYPE_ICONS = {
  Requirement:  '📋',
  'Test Script': '🧪',
  Risk:         '⚠️',
}

export default function GlobalSearchBar() {
  const {
    query, setQuery,
    isOpen, open, close,
    results, totalCount,
  } = useSearch()

  const [hovered,  setHovered]  = useState(null)
  const [popoverPos, setPopoverPos] = useState({ x: 0, y: 0 })
  const inputRef = useRef(null)

  const handleMouseEnter = (item, e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setHovered(item)
    setPopoverPos({ x: rect.right, y: rect.top })
  }
  const handleMouseLeave = () => setHovered(null)

  const hasResults = totalCount > 0

  return (
    <>
      {/* ── Trigger pill in sidebar ── */}
      <button
        onClick={open}
        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg
                   bg-navy-700 border border-navy-500 hover:border-navy-400
                   text-muted hover:text-white text-xs transition-all group"
      >
        <span className="text-sm">🔍</span>
        <span className="flex-1 text-left">Impact Search…</span>
        <kbd className="hidden group-hover:flex items-center gap-0.5
                        bg-navy-600 border border-navy-500 rounded px-1.5 py-0.5
                        text-[10px] text-muted font-mono">
          ⌘K
        </kbd>
      </button>

      {/* ── Command palette overlay ── */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 flex flex-col items-center
                     pt-[10vh] px-4 search-overlay"
          onClick={e => { if (e.target === e.currentTarget) close() }}
        >
          <div className="w-full max-w-2xl bg-navy-700 border border-navy-500
                          rounded-2xl shadow-2xl overflow-hidden animate-fade-in">

            {/* Search input */}
            <div className="flex items-center gap-3 px-4 py-3.5
                            border-b border-navy-600">
              <span className="text-lg text-muted">🔍</span>
              <input
                ref={inputRef}
                autoFocus
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search requirements, test scripts, risks… (fuzzy)"
                className="flex-1 bg-transparent text-white placeholder-navy-400
                           text-sm focus:outline-none"
              />
              {query && (
                <button
                  onClick={() => setQuery('')}
                  className="text-muted hover:text-white text-xs"
                >
                  clear
                </button>
              )}
              <kbd className="bg-navy-600 border border-navy-500 rounded px-1.5 py-0.5
                             text-[10px] text-muted font-mono">
                ESC
              </kbd>
            </div>

            {/* Results */}
            <div className="max-h-[60vh] overflow-y-auto">
              {!query && (
                <div className="px-4 py-8 text-center text-muted text-sm">
                  <p className="text-2xl mb-2">🔎</p>
                  <p>Start typing to search across all releases</p>
                  <p className="text-xs mt-1 text-navy-400">
                    Fuzzy match — "login" finds "authentication"
                  </p>
                </div>
              )}

              {query && !hasResults && (
                <div className="px-4 py-8 text-center text-muted text-sm">
                  No results for <strong className="text-white">"{query}"</strong>
                </div>
              )}

              {hasResults && Object.entries(results).map(([category, items]) => {
                if (!items.length) return null
                return (
                  <div key={category}>
                    {/* Category header */}
                    <div className="px-4 py-2 sticky top-0 bg-navy-700/95 backdrop-blur
                                    border-b border-navy-600 flex items-center gap-2">
                      <span className="text-sm">{TYPE_ICONS[category]}</span>
                      <span className="text-xs font-semibold text-muted uppercase tracking-wider">
                        {category}
                      </span>
                      <span className="ml-auto text-xs text-navy-400">{items.length}</span>
                    </div>

                    {/* Result rows */}
                    {items.map(item => {
                      const meta   = STATUS_META[item.status] || {}
                      const hasIss = item.status === 'open_issue' || item.status === 'failed'
                      const isVal  = item.status === 'approved' && item.humanApproved

                      return (
                        <div
                          key={item.id}
                          onMouseEnter={e => handleMouseEnter(item, e)}
                          onMouseLeave={handleMouseLeave}
                          className={`
                            flex items-center gap-3 px-4 py-2.5 cursor-pointer
                            border-b border-navy-600/50 last:border-0
                            hover:bg-navy-600/50 transition-colors
                            ${hasIss ? 'glow-red rounded' : ''}
                            ${isVal  ? 'glow-green rounded' : ''}
                          `}
                        >
                          {/* ID + title */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs text-accent shrink-0">
                                {item.id}
                              </span>
                              {item.releases?.length > 1 && (
                                <span className="text-[10px] bg-navy-600 text-slate-400
                                                 rounded px-1.5 py-0.5 shrink-0">
                                  ×{item.releases.length} releases
                                </span>
                              )}
                              {item.aiGenerated && !item.humanApproved && (
                                <span className="text-[10px] bg-yellow-900/50 text-yellow-400
                                                 border border-yellow-700 rounded px-1.5 py-0.5
                                                 shrink-0 hitl-pulse">
                                  🤖 Awaiting Review
                                </span>
                              )}
                            </div>
                            <p className="text-white text-xs mt-0.5 truncate">
                              {item.title}
                            </p>
                          </div>

                          {/* Status */}
                          <span className={`text-xs shrink-0 ${meta.cls || 'text-muted'}`}>
                            {meta.label || item.status}
                          </span>

                          {/* Heat score pill */}
                          {item.heatScore != null && (
                            <span className={`
                              text-[10px] rounded-full px-1.5 py-0.5 shrink-0
                              ${item.heatScore > 75 ? 'bg-red-900/50 text-red-400'
                                : item.heatScore > 40 ? 'bg-orange-900/50 text-orange-400'
                                : 'bg-green-900/50 text-green-400'}
                            `}>
                              {item.heatScore}°
                            </span>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )
              })}
            </div>

            {/* Footer */}
            <div className="px-4 py-2.5 border-t border-navy-600 flex items-center
                            justify-between text-[11px] text-navy-400">
              <span>{totalCount} result{totalCount !== 1 ? 's' : ''} — hover for blast radius</span>
              <div className="flex items-center gap-2">
                <span>↑↓ navigate</span>
                <span>↵ select</span>
                <span>ESC close</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Blast radius popover */}
      <BlastRadiusPopover item={hovered} position={popoverPos} />
    </>
  )
}
