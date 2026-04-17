import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '../../store/useAppStore.js'
import { AI_MODELS } from '../../data/systems.js'

const AI_SCENARIOS = [
  {
    label: 'Architecture Upgrade', icon: '🏗️', color: '#ef4444',
    model: 'Drug Interaction Predictor',
    change_type: 'architecture_change',
    description: 'Upgrade from PyTorch 1.13 → PyTorch 2.1 with new attention layers',
    new_version: 'v2.2-rc1',
  },
  {
    label: 'New Training Data', icon: '📊', color: '#f59e0b',
    model: 'QC Defect Classifier',
    change_type: 'new_training_data',
    description: 'Retrained on 50,000 additional defect images from Frankfurt line',
    new_version: 'v1.4-rc1',
  },
  {
    label: 'Drift Correction', icon: '📉', color: '#007FFF',
    model: 'Drug Interaction Predictor',
    change_type: 'drift_correction',
    description: 'Minor weight recalibration — performance drift detected in monitoring',
    new_version: 'v2.1.1',
  },
  {
    label: 'Non-GxP Update', icon: '🔧', color: '#32CD32',
    model: 'Demand Forecasting Model',
    change_type: 'hyperparameter_tuning',
    description: 'Seasonal adjustment — updated learning rate for Q2 forecasting',
    new_version: 'v4.1',
  },
]

const AI_CHANGE_PROFILES = {
  architecture_change: {
    label: 'Architecture Change',
    risk_level: 'High',
    pccp_category: 'Locked Change — Full Revalidation Required',
    rationale:
      'Architecture changes alter model decision boundaries fundamentally. '
      + 'Per FDA PCCP Guidance (Aug 2025), modifications outside the authorized '
      + 'Description of Modifications require a new marketing submission and '
      + 'full revalidation cycle.',
    required_evidence: [
      'IQ — Environment qualification (new framework version)',
      'OQ — Functional regression testing across all decision paths',
      'UAT — Clinical acceptance testing with domain experts',
      'Performance benchmarking vs. previous version (pre-defined acceptance criteria)',
      'Bias & fairness assessment on holdout dataset',
    ],
    governance_required: true,
    fda_ref: 'FDA PCCP Guidance Aug 18, 2025 — §V, §VI.C (21 U.S.C. 360e-4)',
  },
  new_training_data: {
    label: 'New Training Data',
    risk_level: 'Medium',
    pccp_category: 'Adaptive Change — Abbreviated Testing',
    rationale:
      'New training data may shift model decision boundaries. Per FDA PCCP '
      + 'Guidance (Aug 2025), the Modification Protocol must include pre-defined '
      + 'acceptance criteria for re-training. If criteria are not met, the '
      + 'modification must not be implemented and the failure must be recorded.',
    required_evidence: [
      'Training data validation report (source, completeness, bias check)',
      'Tuning data evaluation report (independent from training set)',
      'Performance benchmarking — accuracy, AUC, precision/recall vs. pre-defined thresholds',
      'Bias & fairness delta report',
      'Data lineage audit record (21 CFR Part 820 QMSR / ISO 13485:2016 §4.2.5)',
    ],
    governance_required: true,
    fda_ref:
      'FDA PCCP Guidance Aug 18, 2025 — §VII.B(2)(3) Re-training & Performance Evaluation',
  },
  drift_correction: {
    label: 'Drift Correction',
    risk_level: 'Low',
    pccp_category: 'Pre-Approved Change — Monitoring Evidence Sufficient',
    rationale:
      'Minor recalibration within PCCP-authorized bounds. Per FDA PCCP Guidance '
      + '(Aug 2025), modifications specified in and implemented per an authorized '
      + 'PCCP do not require a new marketing submission. Post-market monitoring '
      + 'evidence is sufficient if delta is within pre-specified thresholds.',
    required_evidence: [
      'Performance monitoring report (pre/post comparison)',
      'Drift analysis log with threshold confirmation',
      'Post-market surveillance record (21 CFR Part 820 QMSR / ISO 13485:2016 §8.2.1)',
      'Audit record of change (21 CFR Part 820 QMSR / ISO 13485:2016 §4.2.5)',
    ],
    governance_required: false,
    fda_ref:
      'FDA PCCP Guidance Aug 18, 2025 — §V (Authorized PCCP), §VII.B(4) Post-Market Monitoring',
  },
  hyperparameter_tuning: {
    label: 'Hyperparameter Tuning',
    risk_level: 'Low',
    pccp_category: 'Non-GxP — Standard IT Change Management',
    rationale:
      'Non-GxP system. No regulatory validation required. Standard IT change '
      + 'management and performance verification apply.',
    required_evidence: [
      'Unit tests passing',
      'Performance comparison report (MAPE, RMSE)',
    ],
    governance_required: false,
    fda_ref: 'N/A — Non-GxP system',
  },
}

const AI_RISK_COLORS = { High: '#ef4444', Medium: '#f59e0b', Low: '#32CD32' }
const AI_RISK_BG = {
  High: 'rgba(239,68,68,0.12)', Medium: 'rgba(245,158,11,0.12)',
  Low: 'rgba(50,205,50,0.12)',
}

function ModelCard({ model }) {
  const m      = model.modelMeta
  const gxpCol = model.gxpStatus === 'GxP Direct'   ? '#ef4444'
               : model.gxpStatus === 'GxP Indirect' ? '#f59e0b' : '#6b7280'
  return (
    <div className="glass rounded-xl p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-white text-[11px] font-semibold">{model.name}</p>
          <p className="text-text-muted text-[9px] font-mono mt-0.5">
            {m.version} · {m.framework}
          </p>
        </div>
        <span className="text-[9px] px-1.5 py-0.5 rounded font-medium"
          style={{ color: gxpCol, backgroundColor: gxpCol + '18',
                   border: `1px solid ${gxpCol}30` }}>
          {model.gxpStatus}
        </span>
      </div>
      <div className="space-y-1">
        {Object.entries(m.performance).map(([k, v]) => (
          <div key={k} className="flex justify-between text-[9px]">
            <span className="text-text-muted capitalize">{k}</span>
            <span className="font-mono text-text-secondary">
              {typeof v === 'number' && v < 1 ? (v * 100).toFixed(1) + '%' : v}
            </span>
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium ${
          m.pccpApproved
            ? 'text-lime-DEFAULT bg-lime-DEFAULT/10 border border-lime-DEFAULT/30'
            : 'text-amber-400 bg-amber-400/10 border border-amber-400/30'
        }`}>
          {m.pccpApproved ? '✓ PCCP Approved' : '⚠ PCCP Pending'}
        </span>
        <span className="text-[9px] text-text-muted truncate">{model.site}</span>
      </div>
      {m.validationRef && (
        <p className="text-[9px] font-mono text-text-muted/60">{m.validationRef}</p>
      )}
    </div>
  )
}

export default function AIModelsTab({ openTab }) {
  const addAIGovernanceItem = useAppStore(s => s.addAIGovernanceItem)
  const setStatusBadge      = useAppStore(s => s.setStatusBadge)

  const [form, setForm] = useState({
    model: '', change_type: 'architecture_change',
    description: '', new_version: '',
  })
  const [loading,   setLoading]   = useState(false)
  const [result,    setResult]    = useState(null)
  const [auditFeed, setAuditFeed] = useState([])
  const [activeScen,setActiveScen] = useState(null)
  const [sentToGov, setSentToGov] = useState(false)

  const selectedModel = AI_MODELS.find(m => m.name === form.model) ?? null

  const applyScenario = useCallback(scen => {
    setActiveScen(scen.label)
    setResult(null)
    setAuditFeed([])
    setSentToGov(false)
    setForm({
      model: scen.model, change_type: scen.change_type,
      description: scen.description, new_version: scen.new_version,
    })
  }, [])

  const assess = useCallback(() => {
    if (!form.model || !form.description) return
    setLoading(true); setResult(null); setAuditFeed([]); setSentToGov(false)
    setTimeout(() => {
      const profile = AI_CHANGE_PROFILES[form.change_type]
        ?? AI_CHANGE_PROFILES.drift_correction
      const t0   = new Date().toISOString()
      const hash = btoa(`${form.model}:${form.change_type}:${form.new_version}`)
        .slice(0, 16).replace(/[+/=]/g, 'x')
      setResult({ profile, model: selectedModel, form: { ...form }, hash, t0 })
      setAuditFeed([
        {
          event: 'MODEL_CHANGE_RECEIVED', time: t0,
          detail: `${form.model} — ${profile.label} (${form.new_version})`,
          color: '#007FFF',
        },
        {
          event: 'PCCP_ASSESSMENT_COMPLETED', time: new Date().toISOString(),
          detail:
            `Risk: ${profile.risk_level} | Category: ${profile.pccp_category}`,
          color: profile.risk_level === 'High' ? '#ef4444'
               : profile.risk_level === 'Medium' ? '#f59e0b' : '#32CD32',
        },
      ])
      setLoading(false)
    }, 800)
  }, [form, selectedModel])

  const sendToGovernance = useCallback(() => {
    if (!result) return
    addAIGovernanceItem({
      id: `AI-GOV-${Date.now()}`,
      type: 'AI_MODEL_CHANGE',
      status: 'pending',
      created_at: new Date().toISOString(),
      model_name: result.form.model,
      change_type: result.profile.label,
      new_version: result.form.new_version,
      risk_level: result.profile.risk_level,
      pccp_category: result.profile.pccp_category,
      description: result.form.description,
      required_evidence: result.profile.required_evidence,
      fda_ref: result.profile.fda_ref,
      reasoning_hash: result.hash,
    })
    setStatusBadge('governance', { type: 'warning', label: 'Review needed' })
    setSentToGov(true)
    setAuditFeed(prev => [...prev, {
      event: 'SENT_TO_GOVERNANCE_HUB', time: new Date().toISOString(),
      detail: `Awaiting HITL review — ${result.profile.risk_level} risk change`,
      color: '#a78bfa',
    }])
  }, [result, addAIGovernanceItem, setStatusBadge])

  const rl   = result?.profile?.risk_level
  const rCol = AI_RISK_COLORS[rl] ?? '#888'
  const rBg  = AI_RISK_BG[rl]    ?? 'rgba(128,128,128,0.1)'

  return (
    <div className="space-y-5 overflow-y-auto h-full pr-1">

      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-white font-semibold text-sm flex items-center gap-2 mb-1">
            🤖 AI Model Change Control
            <span className="text-[9px] px-1.5 py-0.5 rounded border font-medium"
              style={{ color: '#a78bfa', borderColor: 'rgba(167,139,250,0.3)',
                       backgroundColor: 'rgba(167,139,250,0.1)' }}>
              FDA PCCP Guidance Aug 2025
            </span>
          </h2>
          <p className="text-text-secondary text-xs">
            Validated AI models are GAMP Cat 5 assets. Every change is assessed
            against the Predetermined Change Control Plan (PCCP) and routed for
            HITL approval when required.
          </p>
        </div>
      </div>

      {/* Model registry */}
      <div>
        <p className="text-text-muted text-[10px] mb-2 uppercase tracking-wider">
          Validated model registry
        </p>
        <div className="grid grid-cols-3 gap-3">
          {AI_MODELS.map(m => <ModelCard key={m.id} model={m} />)}
        </div>
      </div>

      {/* Scenario presets */}
      <div>
        <p className="text-text-muted text-[10px] mb-2 uppercase tracking-wider">
          Quick-fire scenarios
        </p>
        <div className="grid grid-cols-4 gap-2">
          {AI_SCENARIOS.map(s => (
            <button key={s.label} onClick={() => applyScenario(s)}
              className={`p-3 rounded-xl border text-left transition-all
                ${activeScen === s.label
                  ? 'bg-bg-hover' : 'hover:bg-bg-hover border-border-base'}`}
              style={activeScen === s.label
                ? { borderColor: s.color + '60',
                    boxShadow: `0 0 16px ${s.color}22` } : {}}
            >
              <div className="text-xl mb-1.5">{s.icon}</div>
              <p className="text-white text-[11px] font-semibold leading-tight">
                {s.label}
              </p>
              <p className="text-text-muted text-[9px] mt-0.5">{s.model}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Form + result */}
      <div className="grid grid-cols-2 gap-5">

        <div className="glass rounded-xl p-5 space-y-4">
          <p className="text-text-muted text-[10px] uppercase tracking-wider">
            Model Change Request
          </p>
          <div>
            <label className="text-[10px] text-text-muted block mb-1">Model</label>
            <select value={form.model}
              onChange={e => setForm(f => ({ ...f, model: e.target.value }))}
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors">
              <option value="">— Select a model —</option>
              {AI_MODELS.map(m => (
                <option key={m.id} value={m.name}>
                  {m.name} ({m.modelMeta.version} · {m.gxpStatus})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-text-muted block mb-1">
              Change Type
            </label>
            <div className="grid grid-cols-2 gap-1.5">
              {Object.entries(AI_CHANGE_PROFILES).map(([k, v]) => (
                <button key={k}
                  onClick={() => setForm(f => ({ ...f, change_type: k }))}
                  className={`py-2 px-2 rounded-lg text-[9px] font-medium border
                    transition-all text-left
                    ${form.change_type === k
                      ? 'border-blue-DEFAULT bg-blue-dim text-blue-DEFAULT'
                      : 'border-border-base text-text-muted hover:text-text-secondary'}`}>
                  {v.label}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-text-muted block mb-1">
                New Version
              </label>
              <input value={form.new_version}
                onChange={e => setForm(f => ({ ...f, new_version: e.target.value }))}
                placeholder="e.g. v2.2-rc1"
                className="w-full bg-bg-base border border-border-base rounded-lg
                           px-3 py-2 text-xs font-mono text-text-primary outline-none
                           focus:border-border-blue transition-colors" />
            </div>
            <div className="flex flex-col justify-end">
              {selectedModel && (
                <p className="text-[9px] text-text-muted">
                  Current:{' '}
                  <span className="font-mono text-text-secondary">
                    {selectedModel.modelMeta.version}
                  </span>
                </p>
              )}
            </div>
          </div>
          <div>
            <label className="text-[10px] text-text-muted block mb-1">
              Description
            </label>
            <textarea value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              rows={3} placeholder="Describe the model change…"
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors resize-none" />
          </div>
          <button onClick={assess}
            disabled={loading || !form.model || !form.description}
            className="w-full flex items-center justify-center gap-2
                       px-4 py-3 rounded-xl text-sm font-bold
                       bg-blue-DEFAULT text-white hover:brightness-110
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all shadow-[0_0_24px_rgba(0,127,255,0.35)]">
            {loading
              ? <><span className="animate-spin">⏳</span> Assessing PCCP…</>
              : '⚡ Assess Change'}
          </button>
        </div>

        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div key="result"
                initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.22 }}
                className="glass rounded-xl p-5 space-y-4">
                <div className="rounded-xl p-4 flex flex-col items-center gap-1"
                  style={{ backgroundColor: rBg, border: `1px solid ${rCol}40` }}>
                  <p className="text-[10px] text-text-muted uppercase tracking-widest">
                    PCCP Risk Level
                  </p>
                  <p className="text-4xl font-black tracking-wider"
                    style={{ color: rCol, textShadow: `0 0 24px ${rCol}88` }}>
                    {rl?.toUpperCase()}
                  </p>
                  <p className="text-[10px] text-center font-mono mt-1"
                    style={{ color: rCol + 'cc' }}>
                    {result.profile.pccp_category}
                  </p>
                </div>
                <div className="rounded-lg bg-bg-hover p-3">
                  <p className="text-[9px] text-text-muted uppercase tracking-wider mb-1">
                    FDA Regulatory Basis
                  </p>
                  <p className="text-[10px] text-text-secondary leading-relaxed">
                    {result.profile.rationale}
                  </p>
                  <p className="text-[9px] text-blue-DEFAULT/70 mt-2 italic">
                    {result.profile.fda_ref}
                  </p>
                </div>
                <div>
                  <p className="text-[9px] text-text-muted uppercase tracking-wider mb-2">
                    Required Evidence
                  </p>
                  <div className="space-y-1">
                    {result.profile.required_evidence.map((ev, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className="text-[10px] mt-0.5" style={{ color: rCol }}>
                          ☐
                        </span>
                        <p className="text-[10px] text-text-secondary">{ev}</p>
                      </div>
                    ))}
                  </div>
                </div>
                {result.profile.governance_required ? (
                  sentToGov ? (
                    <div className="rounded-xl p-3 flex items-center gap-3
                                    bg-purple-500/10 border border-purple-500/30">
                      <span className="text-base">✓</span>
                      <div>
                        <p className="text-[11px] text-purple-300 font-semibold">
                          Sent to AI Governance Hub
                        </p>
                        <button
                          onClick={() => openTab?.('governance')}
                          className="text-[10px] text-purple-400 hover:underline">
                          View in Decision Queue →
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button onClick={sendToGovernance}
                      className="w-full flex items-center justify-center gap-2
                                 py-2.5 rounded-xl text-xs font-bold
                                 border border-purple-500/40 text-purple-300
                                 bg-purple-500/10 hover:bg-purple-500/20 transition-all">
                      🏛️ Send to AI Governance Hub for HITL Approval
                    </button>
                  )
                ) : (
                  <div className="rounded-xl p-3 bg-lime-DEFAULT/5
                                  border border-lime-DEFAULT/20">
                    <p className="text-[10px] text-lime-DEFAULT font-semibold">
                      ✓ Pre-Approved Change
                    </p>
                    <p className="text-[9px] text-text-muted mt-0.5">
                      Within PCCP bounds — log monitoring evidence and proceed.
                      No governance approval required.
                    </p>
                  </div>
                )}
                <div className="text-[9px] text-text-muted font-mono text-right">
                  Hash: {result.hash}
                </div>
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="glass rounded-xl p-8 flex flex-col items-center
                           justify-center gap-3 min-h-[200px]">
                <p className="text-4xl">🤖</p>
                <p className="text-text-muted text-xs text-center">
                  Select a scenario and click<br />
                  <span className="text-blue-DEFAULT">Assess Change</span>
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {auditFeed.length > 0 && (
              <motion.div key="audit"
                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="glass rounded-xl p-4 space-y-2">
                <p className="text-[10px] text-text-muted uppercase tracking-wider
                              flex items-center gap-1.5 mb-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-lime-DEFAULT
                                   animate-pulse-lime inline-block" />
                  21 CFR Part 11 Audit Trail
                </p>
                {auditFeed.map((ev, i) => (
                  <motion.div key={ev.event + i}
                    initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.15 }}
                    className="flex gap-3 items-start">
                    <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0"
                      style={{ backgroundColor: ev.color }} />
                    <div className="min-w-0">
                      <p className="text-[10px] font-semibold font-mono"
                        style={{ color: ev.color }}>{ev.event}</p>
                      <p className="text-[9px] text-text-muted">{ev.detail}</p>
                      <p className="text-[9px] text-text-muted/60 font-mono">
                        {ev.time?.slice(0, 19).replace('T', ' ')} UTC
                      </p>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <div className="glass rounded-xl p-4 grid grid-cols-4 gap-4 text-center">
        {[
          { icon: '🤖', label: 'GAMP Cat 5 Asset',
            desc: 'Every validated AI model is registered as a software asset with version history' },
          { icon: '📋', label: 'PCCP Framework',
            desc: 'Predetermined Change Control Plan pre-specifies locked vs adaptive changes' },
          { icon: '⚖️', label: 'FDA PCCP Guidance',
            desc: 'Risk logic aligned to FDA final guidance (Aug 18, 2025) on AI-enabled device software functions' },
          { icon: '🏛️', label: 'HITL Governance',
            desc: 'High and medium risk changes route to the AI Governance Hub for human approval' },
        ].map(item => (
          <div key={item.label} className="space-y-1">
            <p className="text-2xl">{item.icon}</p>
            <p className="text-white text-[11px] font-semibold">{item.label}</p>
            <p className="text-text-muted text-[10px] leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
