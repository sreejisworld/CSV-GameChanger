import { useState } from 'react'

const DEVIATION_TYPES  = ['Deviation', 'CAPA', 'Change Control', 'Incident']
const SEVERITY_OPTIONS = ['Critical', 'Major', 'Minor']
const STATUS_OPTIONS   = ['Open', 'Under Review', 'Resolved', 'Closed']

const SEVERITY_COLORS = {
  Critical: { bg: 'rgba(239,68,68,0.12)',  text: '#ef4444' },
  Major:    { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b' },
  Minor:    { bg: 'rgba(100,116,139,0.12)',text: '#64748b' },
}
const STATUS_COLORS = {
  Open:          { bg: 'rgba(239,68,68,0.10)',  text: '#ef4444' },
  'Under Review':{ bg: 'rgba(245,158,11,0.10)', text: '#f59e0b' },
  Resolved:      { bg: 'rgba(50,205,50,0.10)',  text: '#32CD32' },
  Closed:        { bg: 'rgba(100,116,139,0.10)',text: '#64748b' },
}

let _devId = 1

export default function DeviationsTab() {
  const [deviations, setDeviations] = useState([])
  const [form, setForm] = useState({
    type: DEVIATION_TYPES[0], title: '', description: '',
    severity: SEVERITY_OPTIONS[1], status: STATUS_OPTIONS[0],
    affectedReq: '',
  })
  const [showForm, setShowForm] = useState(false)

  const addDeviation = () => {
    if (!form.title.trim()) return
    setDeviations(prev => [{
      id:       `DEV-${String(_devId++).padStart(3, '0')}`,
      loggedAt: new Date().toISOString(),
      ...form,
    }, ...prev])
    setForm({
      type: DEVIATION_TYPES[0], title: '', description: '',
      severity: SEVERITY_OPTIONS[1], status: STATUS_OPTIONS[0],
      affectedReq: '',
    })
    setShowForm(false)
  }

  const updateStatus = (id, status) =>
    setDeviations(prev =>
      prev.map(d => d.id === id ? { ...d, status } : d)
    )

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 pb-3 shrink-0">
        <button
          onClick={() => setShowForm(v => !v)}
          className="px-3 py-1.5 text-xs rounded bg-blue-dim border
                     border-blue-DEFAULT/30 text-blue-DEFAULT
                     hover:opacity-90 transition-opacity"
        >
          {showForm ? '✕ Cancel' : '+ Log Deviation'}
        </button>
        <span className="ml-auto text-[10px] text-text-muted">
          {deviations.length} record{deviations.length !== 1 ? 's' : ''}
          {' · '}
          {deviations.filter(d => d.status === 'Open').length} open
        </span>
      </div>

      {showForm && (
        <div className="mb-4 p-4 rounded-lg border border-border-base
                        bg-bg-card space-y-3 shrink-0">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-text-muted">Type</label>
              <select value={form.type}
                onChange={e => setForm(f => ({ ...f, type: e.target.value }))}
                className="evolv-input evolv-select text-xs px-2 py-1.5">
                {DEVIATION_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-text-muted">Severity</label>
              <select value={form.severity}
                onChange={e => setForm(f => ({ ...f, severity: e.target.value }))}
                className="evolv-input evolv-select text-xs px-2 py-1.5">
                {SEVERITY_OPTIONS.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-text-muted">Title</label>
            <input value={form.title}
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
              placeholder="Brief description of the deviation…"
              className="evolv-input text-xs px-2 py-1.5" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-text-muted">
              Details / Root Cause
            </label>
            <textarea value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              rows={2}
              placeholder="Root cause, impact, and proposed CAPA…"
              className="evolv-input text-xs px-2 py-1.5 resize-none" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-text-muted">
              Affected Requirement
            </label>
            <input value={form.affectedReq}
              onChange={e => setForm(f => ({ ...f, affectedReq: e.target.value }))}
              placeholder="e.g. UR-1, FR-3…"
              className="evolv-input text-xs px-2 py-1.5 w-40" />
          </div>
          <button
            onClick={addDeviation}
            className="px-4 py-1.5 text-xs rounded bg-blue-DEFAULT text-white
                       font-semibold hover:opacity-90 transition-opacity"
          >
            Log Deviation
          </button>
        </div>
      )}

      <div className="flex-1 overflow-auto">
        {deviations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full
                          text-text-muted gap-2">
            <span className="text-2xl opacity-30">✅</span>
            <p className="text-xs">No deviations logged.</p>
          </div>
        ) : (
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border-base">
                {['ID', 'Type', 'Title', 'Severity', 'Req',
                  'Status', 'Logged'].map(h => (
                  <th key={h}
                    className="text-left text-[10px] font-semibold
                               text-text-muted uppercase tracking-wide
                               py-2 pr-4 whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {deviations.map(d => {
                const sevCfg = SEVERITY_COLORS[d.severity]
                const stsCfg = STATUS_COLORS[d.status]
                return (
                  <tr key={d.id}
                    className="border-b border-border-base
                               hover:bg-bg-hover/30 transition-colors">
                    <td className="py-2.5 pr-4 font-mono text-text-muted
                                   text-[10px] whitespace-nowrap">
                      {d.id}
                    </td>
                    <td className="py-2.5 pr-4 text-text-muted text-[10px]
                                   whitespace-nowrap">
                      {d.type}
                    </td>
                    <td className="py-2.5 pr-4 text-text-secondary text-[11px]
                                   max-w-[180px]">
                      <span className="line-clamp-2">{d.title}</span>
                    </td>
                    <td className="py-2.5 pr-4">
                      <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded"
                        style={{ background: sevCfg.bg, color: sevCfg.text }}>
                        {d.severity}
                      </span>
                    </td>
                    <td className="py-2.5 pr-4 font-mono text-[10px] text-text-muted">
                      {d.affectedReq || '—'}
                    </td>
                    <td className="py-2.5 pr-4">
                      <select
                        value={d.status}
                        onChange={e => updateStatus(d.id, e.target.value)}
                        className="evolv-input evolv-select text-[10px] py-0.5
                                   px-1.5 h-6"
                        style={{ color: stsCfg.text }}
                      >
                        {STATUS_OPTIONS.map(s =>
                          <option key={s}>{s}</option>)}
                      </select>
                    </td>
                    <td className="py-2.5 font-mono text-[9px] text-text-muted
                                   whitespace-nowrap">
                      {new Date(d.loggedAt).toLocaleDateString()}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
