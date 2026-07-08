/**
 * Monitor — Lifecycle Phase 7: Operations & Monitoring
 *
 * Tabs:
 *  - Change Control : ServiceNow CR → GAMP 5 risk + portfolio cross-reference
 *  - AI Models      : PCCP-based AI model change control
 *  - System Health  : lifecycle status dashboard
 *  - Audit Trail    : live viewer for output/audit_trail.csv
 *  - Deviations     : log and track deviations / CAPAs
 */
import { useState, useEffect } from 'react'
import { useAppStore }         from '../store/useAppStore.js'

import ChangeControlTab from './monitor/ChangeControlTab.jsx'
import AIModelsTab      from './monitor/AIModelsTab.jsx'
import SystemHealthTab  from './monitor/SystemHealthTab.jsx'
import AuditTrailTab    from './monitor/AuditTrailTab.jsx'
import DeviationsTab    from './monitor/DeviationsTab.jsx'

// Sprint 35.6 UX diet: dropped emoji prefixes from tab labels.
// Decoration that competed with the active-state indicator. The
// tab strip now reads as a clean nav, not a toolbar of icons.
const TABS = [
  { id: 'changecontrol', label: 'Change Control' },
  { id: 'aimodels',      label: 'AI Models'      },
  { id: 'health',        label: 'System Health'  },
  { id: 'audit',         label: 'Audit Trail'    },
  { id: 'deviations',    label: 'Deviations'     },
]

export default function Monitor({ openTab }) {
  const { setPhaseComplete } = useAppStore()
  const [activeTab, setActiveTab] = useState('changecontrol')

  useEffect(() => { setPhaseComplete('monitor') }, [setPhaseComplete])

  return (
    <div className="flex flex-col h-full bg-bg-base overflow-hidden">

      {/* Header strip — Sprint 35.6 UX diet: underline-only active
          indicator (no fill) for a cleaner, more 2026-premium look.
          The blue-dim background is dropped; the strip reads as a
          true nav bar, not a notice. */}
      <div className="flex items-center gap-4 px-6
                      border-b border-border-base bg-bg-base shrink-0">
        <span className="text-xs font-semibold text-text-primary
                         py-2.5">
          Monitor
        </span>
        <span className="text-text-muted text-xs hidden md:inline
                         py-2.5">
          Operations &amp; Monitoring
        </span>
        <div className="ml-auto flex gap-0">
          {TABS.map(tab => {
            const active = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  relative px-3 py-2.5 text-[11px] font-medium
                  transition-colors whitespace-nowrap
                  ${active
                    ? 'text-blue-DEFAULT'
                    : 'text-text-muted hover:text-text-secondary'}
                `}
              >
                {tab.label}
                {active && (
                  <span
                    className="absolute left-3 right-3 bottom-0 h-0.5
                               bg-blue-DEFAULT rounded-full"
                  />
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden px-6 py-4 flex flex-col">
        {activeTab === 'changecontrol' && <ChangeControlTab />}
        {activeTab === 'aimodels'      && <AIModelsTab openTab={openTab} />}
        {activeTab === 'health'        && <SystemHealthTab />}
        {activeTab === 'audit'         && <AuditTrailTab />}
        {activeTab === 'deviations'    && <DeviationsTab />}
      </div>
    </div>
  )
}
