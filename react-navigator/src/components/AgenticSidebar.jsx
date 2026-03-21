/**
 * AgenticSidebar — Evolv Reasoning panel.
 *
 * Slides in from the right when an agentic continuity hint exists.
 * Shows:
 *  - Agent badge + icon
 *  - Message
 *  - Animated thought log
 *  - Action button
 *  - Dismiss
 */
import { useState, useEffect } from 'react'

export default function AgenticSidebar({ hint, onDismiss }) {
  const [visibleThoughts, setVisibleThoughts] = useState([])
  const [done, setDone] = useState(false)

  // Staggered thought reveal
  useEffect(() => {
    if (!hint) { setVisibleThoughts([]); setDone(false); return }

    setVisibleThoughts([])
    setDone(false)

    const thoughts = hint.thoughts || []
    thoughts.forEach((_, i) => {
      setTimeout(() => {
        setVisibleThoughts(prev => [...prev, thoughts[i]])
        if (i === thoughts.length - 1) {
          setTimeout(() => setDone(true), 400)
        }
      }, i * 480)
    })
  }, [hint])

  if (!hint) return null

  return (
    <div className="flex flex-col h-full bg-navy-800 w-[280px]">

      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 flex items-start gap-2">
        <div className="w-7 h-7 rounded-lg bg-lime/10 border border-lime/30
                        flex items-center justify-center text-sm shrink-0 mt-0.5">
          {hint.icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-widest
                        text-lime mb-0.5">
            Evolv Reasoning
          </p>
          <p className="text-xs text-white/80 leading-snug">{hint.message}</p>
        </div>
        <button
          onClick={onDismiss}
          className="text-white/30 hover:text-white/70 transition-colors
                     text-base leading-none shrink-0 mt-0.5"
          aria-label="Dismiss"
        >
          ×
        </button>
      </div>

      {/* Thought log */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1.5">
        <p className="text-[10px] uppercase tracking-widest text-white/30 mb-2">
          Reasoning Steps
        </p>
        {visibleThoughts.map((thought, i) => (
          <div
            key={i}
            className="flex items-start gap-2 animate-thought"
          >
            <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-lime shrink-0" />
            <span className="text-xs text-white/70 leading-relaxed">{thought}</span>
          </div>
        ))}

        {/* Streaming spinner on last step */}
        {!done && visibleThoughts.length < (hint.thoughts || []).length && (
          <div className="flex items-center gap-2 pl-0">
            <span className="w-3 h-3 rounded-full border-2 border-lime/40
                             border-t-lime animate-spin shrink-0" />
            <span className="text-[11px] text-white/40 italic">Analysing…</span>
          </div>
        )}
      </div>

      {/* Action footer */}
      {done && (
        <div className="px-4 py-3 border-t border-white/5">
          <button
            className="w-full py-2 rounded-lg text-xs font-semibold
                       bg-lime text-navy-950 hover:bg-lime-dark
                       transition-colors shadow-lime"
          >
            {hint.action}
          </button>
          <button
            onClick={onDismiss}
            className="w-full mt-1.5 py-1.5 rounded-lg text-xs
                       text-white/40 hover:text-white/70 transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  )
}
