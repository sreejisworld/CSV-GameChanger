/**
 * useKeyChord — two-key chord navigation (GitHub-style).
 *
 * Press G followed by a letter within 600 ms to jump to any app.
 *
 * Map:
 *   G + H → Home            G + D → Design
 *   G + P → Plan            G + V → Verify
 *   G + R → Requirements    G + L → Release
 *   G + K → Risk (risK)     G + M → Monitor
 *   G + T → Retire          G + N → Navigator
 *   G + I → Impact Analytics
 *
 * Ignored when focus is inside an input / textarea / select.
 *
 * Returns `pending` (boolean) — true while waiting for the second key.
 * Callers can render a small "G ›" badge while pending.
 */
import { useEffect, useRef, useState } from 'react'

const GOTO_MAP = {
  h: 'home',
  p: 'plan',
  r: 'requirements',
  k: 'risk',
  d: 'design',
  v: 'verify',
  l: 'release',
  m: 'monitor',
  t: 'retire',
  n: 'navigator',
  i: 'impact-analytics',
}

const CHORD_TIMEOUT_MS = 600

export function useKeyChord(openTab) {
  const [pending, setPending] = useState(false)
  const timerRef = useRef(null)

  useEffect(() => {
    const handler = e => {
      // Never fire inside form elements
      const tag = document.activeElement?.tagName
      if (
        tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' ||
        e.metaKey || e.ctrlKey || e.altKey
      ) return

      if (!pending && e.key === 'g') {
        e.preventDefault()
        setPending(true)
        clearTimeout(timerRef.current)
        timerRef.current = setTimeout(() => setPending(false), CHORD_TIMEOUT_MS)
        return
      }

      if (pending) {
        clearTimeout(timerRef.current)
        setPending(false)
        const dest = GOTO_MAP[e.key.toLowerCase()]
        if (dest) {
          e.preventDefault()
          openTab(dest)
        }
      }
    }

    window.addEventListener('keydown', handler)
    return () => {
      window.removeEventListener('keydown', handler)
      clearTimeout(timerRef.current)
    }
  }, [pending, openTab])

  return pending
}
