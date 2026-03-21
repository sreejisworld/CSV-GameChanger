/**
 * RiskView — 2026-style Risk Assessment table.
 *
 * Data source: live tree → Risk Matrix folder children.
 * Enriched with traceabilityMap metadata where available.
 */
import { getItemsByFolder } from '../../utils/treeHelpers.js'
import {
  risks as mockRisks,
  getRisk,
  requirements,
} from '../../data/traceabilityMap.js'

const rpn = heatScore => Math.max(1, Math.round((heatScore / 100) * 27))

const RPN_STYLE = v =>
  v >= 20 ? 'text-danger bg-danger/10 border-danger/30'
  : v >= 10 ? 'text-warning bg-warning/10 border-warning/30'
  : 'text-success bg-success/10 border-success/30'

const LEVEL_STYLE = {
  high:   'bg-danger/15 text-danger border-danger/30',
  medium: 'bg-warning/15 text-warning border-warning/30',
  low:    'bg-success/15 text-success border-success/30',
}

const PROB_LABEL = heatScore =>
  heatScore >= 70 ? 'Frequent' : heatScore >= 40 ? 'Occasional' : 'Rare'

const PROB_LEVEL = heatScore =>
  heatScore >= 70 ? 'high' : heatScore >= 40 ? 'medium' : 'low'

function enrich(treeNode) {
  const base = getRisk(treeNode.id) || {}
  return {
    id:         treeNode.id,
    title:      treeNode.name,
    riskLevel:  treeNode.riskLevel  ?? base.riskLevel  ?? 'medium',
    heatScore:  treeNode.heatScore  ?? base.heatScore   ?? 30,
    regulation: base.regulation || '',
    mitigatedBy:base.mitigatedBy || [],
  }
}

export default function RiskView({ node, tree }) {
  const rawItems = node?.children?.length
    ? node.children
    : tree
      ? getItemsByFolder(tree, 'Risk Matrix')
      : mockRisks

  const items = rawItems.length
    ? rawItems.map(enrich)
    : mockRisks.map(r => enrich({ ...r, name: r.title }))

  const totalHigh = items.filter(r => r.riskLevel === 'high').length

  return (
    <div className="p-8">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <p className="text-[10px] uppercase tracking-widest text-accent mb-1">
            Risk Assessment
          </p>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Risk Matrix — {tree?.name || 'LabCore LIMS v4.2'}
          </h2>
          <p className="text-sm text-muted mt-1">
            {items.length} risk item{items.length !== 1 ? 's' : ''} · GAMP 5 §5 · ICH Q9
          </p>
        </div>
        <span className="text-[10px] bg-danger/10 text-danger border border-danger/30
                         rounded-full px-3 py-1 font-semibold shrink-0">
          {totalHigh} HIGH
        </span>
      </div>

      <div className="flex items-center gap-4 mb-6 text-[11px]">
        <span className="text-muted">RPN = Severity × Occurrence × Detectability</span>
        {[
          { color: 'bg-danger/60',  label: '≥ 20 High'    },
          { color: 'bg-warning/60', label: '10–19 Medium'  },
          { color: 'bg-success/60', label: '< 10 Low'      },
        ].map(l => (
          <span key={l.label} className="flex items-center gap-1">
            <span className={`w-2.5 h-2.5 rounded-sm inline-block ${l.color}`}/>
            <span className="text-white/60">{l.label}</span>
          </span>
        ))}
      </div>

      <div className="rounded-2xl border border-white/5 overflow-hidden">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-navy-900/80 border-b border-white/5">
              {['Hazard', 'Regulation', 'Probability', 'Severity', 'RPN',
                'Mitigated By', 'Level'].map(h => (
                <th key={h}
                  className="px-4 py-3 text-left text-[10px] font-semibold
                             uppercase tracking-widest text-muted whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((risk, i) => {
              const score = rpn(risk.heatScore)
              const mitigations = risk.mitigatedBy
                .map(id => requirements.find(r => r.id === id))
                .filter(Boolean)

              return (
                <tr key={risk.id}
                  className={`border-b border-white/3 transition-colors hover:bg-white/3
                              ${i % 2 === 0 ? '' : 'bg-white/[0.015]'}`}>
                  <td className="px-4 py-3 max-w-xs">
                    <p className="text-white/85 leading-snug">{risk.title}</p>
                    <p className="text-[10px] font-mono text-muted mt-0.5">{risk.id}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-[10px] text-muted">{risk.regulation || '—'}</span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`text-[10px] px-2 py-0.5 rounded border
                                     ${LEVEL_STYLE[PROB_LEVEL(risk.heatScore)]}`}>
                      {PROB_LABEL(risk.heatScore)}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`text-[10px] px-2 py-0.5 rounded border
                                     ${LEVEL_STYLE[risk.riskLevel]}`}>
                      {risk.riskLevel === 'high' ? 'High' : risk.riskLevel === 'medium' ? 'Medium' : 'Low'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-sm font-bold px-2 py-0.5 rounded border
                                     ${RPN_STYLE(score)}`}>
                      {score}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-1">
                      {mitigations.length > 0
                        ? mitigations.map(m => (
                            <span key={m.id} className="text-[10px] font-mono text-accent/80">
                              {m.id}
                            </span>
                          ))
                        : <span className="text-[10px] text-white/25">—</span>
                      }
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border
                                     font-semibold ${LEVEL_STYLE[risk.riskLevel]}`}>
                      {risk.riskLevel?.toUpperCase()}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4">
        {[
          { level: 'HIGH',   strategy: 'Rigorous Scripted Testing (OQ + UAT)',   color: 'danger'  },
          { level: 'MEDIUM', strategy: 'Hybrid Testing (Scripted + Unscripted)', color: 'warning' },
          { level: 'LOW',    strategy: 'Unscripted / Exploratory Testing',       color: 'success' },
        ].map(s => (
          <div key={s.level}
            className={`rounded-xl p-4 border bg-${s.color}/5 border-${s.color}/20`}>
            <p className={`text-[10px] font-bold uppercase tracking-widest text-${s.color} mb-1`}>
              {s.level} Risk
            </p>
            <p className="text-xs text-white/60">{s.strategy}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
