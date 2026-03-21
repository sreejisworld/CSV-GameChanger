/**
 * Requirements — Lifecycle Phase 2: Requirements Hub
 *
 * Two tabs:
 *   1. Generate Reqs  — Streamlit page 2 (URS / UR-FR generation)
 *   2. SMART Engine   — Streamlit page 12 (SMART requirement refinement)
 */
import { useState } from 'react'
import { useAppStore } from '../store/useAppStore.js'

const TABS = [
  {
    id:       'generate',
    label:    '🧠 Generate Reqs',
    sublabel: 'AI-powered GAMP 5 URS and UR/FR generation',
    url:      'http://localhost:8501/?page=requirements&embedded=true',
  },
  {
    id:       'smart',
    label:    '✨ SMART Engine',
    sublabel: 'Refine vague requirements to SMART format with FDA/EMA 2026 guidance',
    url:      'http://localhost:8501/?page=smart&embedded=true',
  },
]

export default function Requirements() {
  const [activeTab, setActiveTab] = useState('generate')
  const { setPhaseComplete } = useAppStore()

  const tab = TABS.find(t => t.id === activeTab)

  const handleTabChange = id => {
    setActiveTab(id)
    setPhaseComplete('requirements')
  }

  return (
    <div className="flex flex-col h-full">
      {/* ── Notice strip with inline tabs ─────────────────── */}
      <div className="flex items-center gap-0 px-4 py-0
                      bg-blue-dim border-b border-blue-DEFAULT/20 shrink-0">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => handleTabChange(t.id)}
            className={`
              flex items-center gap-2 px-4 py-2.5 text-xs font-medium
              border-b-2 transition-all whitespace-nowrap
              ${activeTab === t.id
                ? 'border-blue-DEFAULT text-blue-DEFAULT bg-blue-DEFAULT/10'
                : 'border-transparent text-text-muted hover:text-text-secondary'}
            `}
          >
            {t.label}
          </button>
        ))}

        <span className="ml-4 text-text-muted text-xs hidden sm:block">
          {tab.sublabel}
        </span>

        <a
          href={tab.url.replace('&embedded=true', '')}
          target="_blank"
          rel="noreferrer"
          className="ml-auto text-[10px] text-blue-DEFAULT/70
                     hover:text-blue-DEFAULT underline underline-offset-2
                     transition-colors shrink-0 pr-1"
        >
          ↗ Open full screen
        </a>
      </div>

      {/* ── Iframes — both mounted, toggled by visibility ─── */}
      {TABS.map(t => (
        <div
          key={t.id}
          className="flex-1 relative"
          style={{ display: activeTab === t.id ? 'block' : 'none' }}
        >
          <iframe
            src={t.url}
            className="app-iframe"
            title={t.label}
            allow="clipboard-write"
          />
        </div>
      ))}
    </div>
  )
}
