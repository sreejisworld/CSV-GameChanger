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

const TABS = [
  { id: 'changecontrol', label: '🔄 Change Control' },
  { id: 'aimodels',      label: '🤖 AI Models'      },
  { id: 'health',        label: '📊 System Health'  },
  { id: 'audit',         label: '🔍 Audit Trail'    },
  { id: 'deviations',    label: '⚠️ Deviations'     },
]

export default function Monitor({ openTab }) {
  const { setPhaseComplete } = useAppStore()
  const [activeTab, setActiveTab] = useState('changecontrol')

  useEffect(() => { setPhaseComplete('monitor') }, [setPhaseComplete])

  return (
    <div className="flex flex-col h-full bg-bg-base overflow-hidden">

      {/* Header strip */}
      <div className="flex items-center gap-3 px-6 py-2.5
                      bg-blue-dim border-b border-blue-DEFAULT/20 shrink-0">
        <span className="text-xs font-semibold text-blue-DEFAULT">Monitor</span>
        <span className="text-text-muted text-xs">Operations &amp; Monitoring</span>
        <div className="ml-auto flex gap-1">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                px-3 py-1 text-[11px] rounded transition-colors
                ${activeTab === tab.id
                  ? 'bg-blue-DEFAULT/20 text-blue-DEFAULT'
                  : 'text-text-muted hover:text-text-secondary'}
              `}
            >
              {tab.label}
            </button>
          ))}
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
