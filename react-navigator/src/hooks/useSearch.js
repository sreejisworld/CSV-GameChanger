/**
 * useSearch — Fuzzy search hook backed by Fuse.js.
 *
 * Searches across requirements, test scripts, and risks.
 * Returns results grouped by category with blast-radius
 * data attached.
 */
import { useState, useMemo, useCallback, useEffect } from 'react'
import Fuse from 'fuse.js'
import { searchIndex } from '../data/traceabilityMap.js'

const FUSE_OPTIONS = {
  keys: [
    { name: 'id',       weight: 0.4 },
    { name: 'title',    weight: 0.5 },
    { name: 'regulation', weight: 0.1 },
  ],
  threshold: 0.35,       // 0=exact, 1=match anything
  minMatchCharLength: 2,
  includeScore: true,
  includeMatches: true,
}

export function useSearch() {
  const [query, setQuery]       = useState('')
  const [isOpen, setIsOpen]     = useState(false)
  const [selected, setSelected] = useState(null)

  // Build Fuse instance once
  const fuse = useMemo(() => new Fuse(searchIndex, FUSE_OPTIONS), [])

  // Cmd+K / Ctrl+K to open
  useEffect(() => {
    const handler = e => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen(o => !o)
      }
      if (e.key === 'Escape') {
        setIsOpen(false)
        setQuery('')
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const results = useMemo(() => {
    if (!query.trim()) return { Requirement: [], 'Test Script': [], Risk: [] }

    const raw = fuse.search(query).slice(0, 20)

    const grouped = { Requirement: [], 'Test Script': [], Risk: [] }
    raw.forEach(({ item }) => {
      const bucket = item._type
      if (grouped[bucket]) grouped[bucket].push(item)
    })
    return grouped
  }, [query, fuse])

  const totalCount = useMemo(
    () => Object.values(results).reduce((s, arr) => s + arr.length, 0),
    [results]
  )

  const open  = useCallback(() => setIsOpen(true),  [])
  const close = useCallback(() => { setIsOpen(false); setQuery('') }, [])

  return {
    query, setQuery,
    isOpen, open, close,
    results, totalCount,
    selected, setSelected,
  }
}
