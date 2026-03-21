/**
 * Navigator — embeds the React Project Navigator served by FastAPI at /navigator.
 *
 * Sends live Zustand context (phaseCompletion + planData) into the iframe
 * via postMessage so the navigator can reflect the active project state.
 */
import { useEffect, useRef, useCallback } from 'react'
import { useAppStore } from '../store/useAppStore.js'

export default function Navigator() {
  const { phaseCompletion, planData } = useAppStore()
  const iframeRef = useRef(null)

  const sendContext = useCallback(() => {
    try {
      iframeRef.current?.contentWindow?.postMessage({
        type:    'EVOLV_CONTEXT',
        payload: {
          projectName:     planData.projectName,
          gampCategory:    planData.gampCategory,
          phaseCompletion: phaseCompletion,
        },
      }, '*')
    } catch (_) { /* silently ignore cross-origin errors */ }
  }, [phaseCompletion, planData])

  // Re-send whenever store data changes
  useEffect(() => { sendContext() }, [sendContext])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-4 py-2 bg-blue-dim
                      border-b border-blue-DEFAULT/20 shrink-0">
        <span className="text-blue-DEFAULT text-xs font-medium">
          Project Navigator — GAMP 5 Hierarchical Tree
        </span>
        {planData.projectName && (
          <span className="text-[10px] text-text-muted border border-border-base
                           rounded px-2 py-0.5 truncate max-w-[160px]">
            {planData.projectName}
          </span>
        )}
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
        ref={iframeRef}
        src="http://localhost:8000/navigator"
        className="app-iframe flex-1"
        title="EVOLV Project Navigator"
        onLoad={sendContext}
      />
    </div>
  )
}
