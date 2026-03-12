/**
 * ValidationFactory — embeds the Streamlit EVOLV platform
 * (port 8501) as a full-height iframe.
 */
export default function ValidationFactory() {
  return (
    <div className="flex flex-col h-full">
      {/* Top notice strip */}
      <div className="flex items-center gap-3 px-4 py-2 bg-lime-dim
                      border-b border-lime-DEFAULT/20 shrink-0">
        <span className="ai-badge">EVOLV AI</span>
        <span className="text-lime-DEFAULT text-xs font-medium">
          Validation Factory — AI-powered GAMP 5 platform
        </span>
        <a
          href="http://localhost:8501"
          target="_blank"
          rel="noreferrer"
          className="ml-auto text-[10px] text-lime-DEFAULT/70 hover:text-lime-DEFAULT
                     underline underline-offset-2 transition-colors"
        >
          ↗ Open full screen
        </a>
      </div>
      <iframe
        src="http://localhost:8501"
        className="app-iframe flex-1"
        title="EVOLV Validation Factory"
        allow="clipboard-write"
      />
    </div>
  )
}
