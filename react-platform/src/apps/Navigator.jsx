/**
 * Navigator — embeds the React Project Navigator
 * served by FastAPI at /navigator.
 */
export default function Navigator() {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-4 py-2 bg-blue-dim
                      border-b border-blue-DEFAULT/20 shrink-0">
        <span className="text-blue-DEFAULT text-xs font-medium">
          🗺️ Project Navigator — GAMP 5 Hierarchical Tree
        </span>
        <a
          href="http://localhost:8000/navigator"
          target="_blank"
          rel="noreferrer"
          className="ml-auto text-[10px] text-blue-DEFAULT/70 hover:text-blue-DEFAULT
                     underline underline-offset-2 transition-colors"
        >
          ↗ Open full screen
        </a>
      </div>
      <iframe
        src="http://localhost:8000/navigator"
        className="app-iframe flex-1"
        title="EVOLV Project Navigator"
      />
    </div>
  )
}
