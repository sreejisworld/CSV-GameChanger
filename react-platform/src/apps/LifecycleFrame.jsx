/**
 * LifecycleFrame — shared iframe wrapper for all active lifecycle phases.
 *
 * Props:
 *   phaseId   — app ID (e.g. 'requirements') — used to mark phase complete
 *   label     — human label shown in the top notice strip
 *   sublabel  — short description shown alongside label
 *   color     — 'blue' | 'lime' | 'amber'
 *   phase     — query-param value sent to Streamlit (?page=<phase>)
 */
import { useAppStore } from '../store/useAppStore.js'

const COLOR_MAP = {
  blue:  {
    strip: 'bg-blue-dim border-blue-DEFAULT/20',
    badge: 'text-blue-DEFAULT',
    link:  'text-blue-DEFAULT/70 hover:text-blue-DEFAULT',
  },
  lime:  {
    strip: 'bg-lime-dim border-lime-DEFAULT/20',
    badge: 'text-lime-DEFAULT',
    link:  'text-lime-DEFAULT/70 hover:text-lime-DEFAULT',
  },
  amber: {
    strip: 'bg-amber-dim border-amber-DEFAULT/20',
    badge: 'text-amber-DEFAULT',
    link:  'text-amber-DEFAULT/70 hover:text-amber-DEFAULT',
  },
}

export default function LifecycleFrame({
  label,
  sublabel,
  color = 'blue',
  phase,
}) {
  const c   = COLOR_MAP[color] ?? COLOR_MAP.blue
  const url = `http://localhost:8501/?page=${phase}&embedded=true`

  return (
    <div className="flex flex-col h-full">
      {/* Notice strip */}
      <div className={`
        flex items-center gap-3 px-4 py-2 border-b shrink-0 ${c.strip}
      `}>
        <span className={`text-xs font-semibold ${c.badge}`}>
          {label}
        </span>
        {sublabel && (
          <span className="text-text-muted text-xs">{sublabel}</span>
        )}
        <a
          href={`http://localhost:8501/?page=${phase}`}
          target="_blank"
          rel="noreferrer"
          className={`
            ml-auto text-[10px] underline underline-offset-2
            transition-colors ${c.link}
          `}
        >
          ↗ Open full screen
        </a>
      </div>

      {/* Streamlit iframe */}
      <iframe
        src={url}
        className="app-iframe flex-1"
        title={label}
        allow="clipboard-write"
      />
    </div>
  )
}
