/**
 * HeatmapToggle — button that switches Impact Heatmap on/off.
 * When ON, folder and release nodes take orange-red tints
 * proportional to their heatScore.
 */
export default function HeatmapToggle({ on, onToggle }) {
  return (
    <button
      onClick={onToggle}
      title="Impact Heatmap — highlights hot areas needing audit attention"
      className={`
        flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold
        border transition-all duration-200
        ${on
          ? 'bg-orange-900/60 border-orange-500 text-orange-300 shadow-[0_0_8px_rgba(249,115,22,0.4)]'
          : 'bg-navy-600 border-navy-500 text-muted hover:border-navy-400 hover:text-white'}
      `}
    >
      <span className="text-sm">{on ? '🔥' : '🌡️'}</span>
      <span>Impact Heatmap</span>
      {on && (
        <span className="ml-0.5 text-orange-400">ON</span>
      )}
    </button>
  )
}

/** Compute inline background style for a node in heatmap mode */
export function heatStyle(score, heatmapOn) {
  if (!heatmapOn || score == null) return {}
  if (score <= 20) return {}
  if (score <= 40) return { backgroundColor: 'rgba(154,52,18,0.08)' }
  if (score <= 60) return { backgroundColor: 'rgba(154,52,18,0.18)' }
  if (score <= 80) return { backgroundColor: 'rgba(194,65,12,0.28)' }
  return { backgroundColor: 'rgba(220,38,38,0.30)' }
}
