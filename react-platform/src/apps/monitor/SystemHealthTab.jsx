import { useAppStore } from '../../store/useAppStore.js'

export default function SystemHealthTab() {
  const {
    phaseCompletion, planData, releaseData,
    testRuns, activeRunId, riskData,
  } = useAppStore()

  const run      = activeRunId ? testRuns[activeRunId] : null
  const riskRows = Object.values(riskData)

  const phases = [
    { id: 'plan',         label: 'Plan',        emoji: '📋' },
    { id: 'requirements', label: 'Requirements', emoji: '📝' },
    { id: 'risk',         label: 'Risk',         emoji: '⚖️' },
    { id: 'design',       label: 'Design',       emoji: '🔒', locked: true },
    { id: 'verify',       label: 'Verify',       emoji: '🏭' },
    { id: 'release',      label: 'Release',      emoji: '📄' },
    { id: 'monitor',      label: 'Monitor',      emoji: '📡' },
    { id: 'retire',       label: 'Retire',       emoji: '🔒', locked: true },
  ]

  const metrics = [
    {
      label: 'Project',
      value: planData.projectName || 'Not set',
      sub:   planData.gampCategory
        ? `GAMP 5 Cat ${planData.gampCategory}`
        : 'Category not set',
      color: planData.projectName ? '#32CD32' : '#64748b',
    },
    {
      label: 'Phases Complete',
      value: `${Object.values(phaseCompletion).filter(Boolean).length} / 8`,
      sub:   'Lifecycle progress',
      color: '#007FFF',
    },
    {
      label: 'Test Status',
      value: run?.status === 'locked'
        ? 'Signed Off'
        : run ? 'In Progress' : 'Not Started',
      sub:   run?.signerName ? `Signed by ${run.signerName}` : '',
      color: run?.status === 'locked' ? '#32CD32'
           : run ? '#f59e0b' : '#64748b',
    },
    {
      label: 'Approvals',
      value: `${releaseData.approvals.length} signed`,
      sub:   releaseData.released ? 'System Released ✓' : 'Pending release',
      color: releaseData.released ? '#32CD32'
           : releaseData.approvals.length > 0 ? '#f59e0b' : '#64748b',
    },
    {
      label: 'Requirements',
      value: `${riskRows.length} assessed`,
      sub:   `${riskRows.filter(r => r.impact && r.implMethod).length} fully profiled`,
      color: '#007FFF',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-3">
        {metrics.map(m => (
          <div key={m.label}
            className="p-4 rounded-lg border border-border-base bg-bg-card">
            <p className="text-[10px] text-text-muted uppercase tracking-wide mb-1">
              {m.label}
            </p>
            <p className="text-lg font-bold" style={{ color: m.color }}>
              {m.value}
            </p>
            {m.sub && (
              <p className="text-[10px] text-text-muted mt-0.5">{m.sub}</p>
            )}
          </div>
        ))}
      </div>

      <div>
        <h3 className="text-[10px] font-semibold text-text-muted uppercase
                       tracking-widest mb-3">
          Lifecycle Status
        </h3>
        <div className="grid grid-cols-4 gap-2">
          {phases.map(p => {
            const done   = !p.locked && phaseCompletion[p.id]
            const locked = p.locked
            return (
              <div key={p.id}
                className={`
                  p-3 rounded-lg border text-center transition-colors
                  ${locked
                    ? 'border-border-base bg-bg-base opacity-40'
                    : done
                      ? 'border-lime-DEFAULT/30 bg-lime-DEFAULT/5'
                      : 'border-border-base bg-bg-card'}
                `}>
                <div className="text-xl mb-1">{p.emoji}</div>
                <p className={`text-[10px] font-medium ${
                  locked ? 'text-text-muted'
                         : done ? 'text-lime-DEFAULT' : 'text-text-secondary'
                }`}>
                  {p.label}
                </p>
                <p className="text-[9px] mt-0.5" style={{
                  color: locked ? '#334155' : done ? '#32CD32' : '#475569',
                }}>
                  {locked ? 'Locked' : done ? '✓ Complete' : '○ Pending'}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
