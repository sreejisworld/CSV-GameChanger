/**
 * BriefingPanel — pre-execution briefing with risk-graduated acknowledgement.
 *
 * HIGH  : tick each item + enter tester name → "Begin Execution" unlocks
 * MEDIUM: single checkbox → "Begin Exploratory Session" unlocks
 * LOW   : auto-dismissing banner (3 s) or manual dismiss
 */
import { useState, useEffect } from 'react'

const RISK_META = {
  High:   { color: '#ef4444', bg: 'rgba(239,68,68,0.08)',
            border: 'rgba(239,68,68,0.25)', label: 'HIGH RISK' },
  Medium: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)',
            border: 'rgba(245,158,11,0.25)', label: 'MEDIUM RISK' },
  Low:    { color: '#32CD32', bg: 'rgba(50,205,50,0.08)',
            border: 'rgba(50,205,50,0.25)', label: 'LOW RISK' },
}

// ── LOW risk — auto-dismissing banner ────────────────────────────
function LowRiskBanner({ onAcknowledge }) {
  const [countdown, setCountdown] = useState(3)

  useEffect(() => {
    if (countdown <= 0) { onAcknowledge({ autoAcknowledged: true }) ; return }
    const t = setTimeout(() => setCountdown(c => c - 1), 1000)
    return () => clearTimeout(t)
  }, [countdown, onAcknowledge])

  return (
    <div className="flex-1 flex items-center justify-center px-8">
      <div className="max-w-lg w-full p-6 rounded-xl border"
        style={{
          background:   RISK_META.Low.bg,
          borderColor:  RISK_META.Low.border,
        }}
      >
        <div className="flex items-center gap-3 mb-3">
          <span className="text-xl">🟢</span>
          <span className="font-semibold text-sm" style={{ color: RISK_META.Low.color }}>
            LOW RISK — Unscripted Exploratory Session
          </span>
        </div>
        <p className="text-text-muted text-xs leading-relaxed mb-4">
          Per FDA CSA guidance, low-risk systems are appropriate for
          unscripted, exploratory testing. Record your observations and
          findings as you go — no step-by-step script is required.
        </p>
        <div className="flex items-center justify-between">
          <span className="text-text-muted text-[10px]">
            Auto-starting in {countdown}s…
          </span>
          <button
            onClick={() => onAcknowledge({ autoAcknowledged: false })}
            className="px-4 py-1.5 rounded text-xs font-semibold
                       bg-lime-DEFAULT text-bg-base hover:opacity-90
                       transition-opacity"
          >
            Begin Now
          </button>
        </div>
      </div>
    </div>
  )
}

// ── MEDIUM risk — single checkbox ────────────────────────────────
function MediumRiskBriefing({ script, items, onAcknowledge }) {
  const [checked,    setChecked]    = useState(false)
  const [testerName, setTesterName] = useState('')
  const meta = RISK_META.Medium

  return (
    <div className="flex-1 flex items-center justify-center px-8">
      <div className="max-w-lg w-full p-6 rounded-xl border"
        style={{ background: meta.bg, borderColor: meta.border }}
      >
        <div className="flex items-center gap-3 mb-1">
          <span className="text-xl">🟡</span>
          <span className="font-semibold text-sm" style={{ color: meta.color }}>
            Pre-Session Briefing — {meta.label}
          </span>
        </div>
        <p className="text-text-muted text-[10px] mb-4">
          {script.script_id} · {script.urs_id} · {script.test_type}
        </p>

        <label className="flex items-start gap-3 cursor-pointer mb-4
                           p-3 rounded-lg bg-bg-card border border-border-base">
          <input
            type="checkbox"
            checked={checked}
            onChange={e => setChecked(e.target.checked)}
            className="mt-0.5 accent-amber-400 w-4 h-4 shrink-0"
          />
          <span className="text-text-secondary text-xs leading-relaxed">
            {items?.[0] ?? 'I confirm the test environment is ready and I am prepared to execute this exploratory charter session.'}
          </span>
        </label>

        <div className="mb-4">
          <label className="text-[10px] text-text-muted block mb-1">
            Tester Name (required)
          </label>
          <input
            value={testerName}
            onChange={e => setTesterName(e.target.value)}
            placeholder="Full name…"
            className="evolv-input text-xs px-3 py-1.5 w-full"
          />
        </div>

        <button
          disabled={!checked || testerName.trim().length < 2}
          onClick={() => onAcknowledge({
            testerName:      testerName.trim(),
            acknowledgedAt:  new Date().toISOString(),
            itemsConfirmed:  [checked],
          })}
          className={`
            w-full py-2 rounded text-xs font-semibold transition-opacity
            ${checked && testerName.trim().length >= 2
              ? 'bg-amber-500 text-white hover:opacity-90'
              : 'bg-bg-card text-text-muted cursor-not-allowed opacity-50'}
          `}
        >
          Begin Exploratory Session
        </button>
      </div>
    </div>
  )
}

// ── HIGH risk — full checklist ────────────────────────────────────
function HighRiskBriefing({ script, items, onAcknowledge, onEdit }) {
  const [checked, setChecked] = useState(() => items.map(() => false))
  const [testerName, setTesterName] = useState('')
  const [editMode, setEditMode] = useState(false)
  const [draftItems, setDraftItems] = useState(items.join('\n'))
  const meta = RISK_META.High

  const allChecked  = checked.every(Boolean)
  const nameValid   = testerName.trim().length >= 2
  const canProceed  = allChecked && nameValid

  const handleSaveEdit = () => {
    const newItems = draftItems
      .split('\n')
      .map(s => s.trim())
      .filter(Boolean)
    onEdit(newItems)
    setChecked(newItems.map(() => false))
    setEditMode(false)
  }

  return (
    <div className="flex-1 flex items-center justify-center px-8 py-6 overflow-auto">
      <div className="max-w-xl w-full p-6 rounded-xl border"
        style={{ background: meta.bg, borderColor: meta.border }}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-1">
          <div className="flex items-center gap-3">
            <span className="text-xl">🔴</span>
            <span className="font-semibold text-sm" style={{ color: meta.color }}>
              Pre-Execution Briefing — {meta.label}
            </span>
          </div>
          <button
            onClick={() => setEditMode(v => !v)}
            className="text-[10px] text-text-muted hover:text-text-secondary
                       border border-border-base rounded px-2 py-0.5
                       transition-colors"
          >
            {editMode ? 'Cancel Edit' : '✏️ Edit Checklist'}
          </button>
        </div>
        <p className="text-text-muted text-[10px] mb-4">
          {script.script_id} · {script.urs_id} · {script.test_type}
          <span className="ml-2 text-red-400 font-medium">
            All items must be confirmed before execution may begin.
          </span>
        </p>

        {/* Edit mode */}
        {editMode ? (
          <div className="mb-4">
            <p className="text-[10px] text-text-muted mb-1">
              One item per line — saved as script override
            </p>
            <textarea
              value={draftItems}
              onChange={e => setDraftItems(e.target.value)}
              rows={items.length + 1}
              className="w-full text-xs bg-bg-card border border-border-base
                         rounded px-3 py-2 text-text-secondary
                         focus:outline-none focus:border-blue-DEFAULT resize-none"
            />
            <button
              onClick={handleSaveEdit}
              className="mt-2 px-3 py-1 rounded text-xs font-medium
                         bg-blue-DEFAULT text-white hover:opacity-90
                         transition-opacity"
            >
              Save Override
            </button>
          </div>
        ) : (
          /* Checklist */
          <div className="space-y-2 mb-4">
            {items.map((item, i) => (
              <label
                key={i}
                className={`
                  flex items-start gap-3 cursor-pointer p-3 rounded-lg border
                  transition-colors
                  ${checked[i]
                    ? 'bg-red-500/10 border-red-500/30'
                    : 'bg-bg-card border-border-base hover:border-border-bright'}
                `}
              >
                <input
                  type="checkbox"
                  checked={checked[i]}
                  onChange={e => {
                    const next = [...checked]
                    next[i] = e.target.checked
                    setChecked(next)
                  }}
                  className="mt-0.5 accent-red-500 w-4 h-4 shrink-0"
                />
                <span className={`text-xs leading-relaxed ${
                  checked[i] ? 'text-text-secondary' : 'text-text-muted'
                }`}>
                  {item}
                </span>
              </label>
            ))}
          </div>
        )}

        {/* Tester name */}
        {!editMode && (
          <>
            <div className="mb-4">
              <label className="text-[10px] text-text-muted block mb-1">
                Tester Name — I confirm the above (21 CFR Part 11 §11.10)
              </label>
              <input
                value={testerName}
                onChange={e => setTesterName(e.target.value)}
                placeholder="Enter your full name to confirm…"
                className="evolv-input text-xs px-3 py-1.5 w-full"
              />
            </div>

            {/* Progress indicator */}
            <div className="flex items-center gap-2 mb-4">
              <div className="flex-1 h-1 bg-bg-card rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{
                    width: `${(checked.filter(Boolean).length / items.length) * 100}%`,
                    background: '#ef4444',
                  }}
                />
              </div>
              <span className="text-[10px] text-text-muted">
                {checked.filter(Boolean).length}/{items.length} confirmed
              </span>
            </div>

            <button
              disabled={!canProceed}
              onClick={() => onAcknowledge({
                testerName:     testerName.trim(),
                acknowledgedAt: new Date().toISOString(),
                itemsConfirmed: checked,
              })}
              className={`
                w-full py-2 rounded text-xs font-semibold transition-opacity
                ${canProceed
                  ? 'bg-red-500 text-white hover:opacity-90'
                  : 'bg-bg-card text-text-muted cursor-not-allowed opacity-40'}
              `}
            >
              {canProceed
                ? '▶ Begin Execution'
                : `Confirm all ${items.length} items and enter your name to proceed`
              }
            </button>
          </>
        )}
      </div>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────
export default function BriefingPanel({
  script, riskLevel, items, onAcknowledge, onEdit,
}) {
  if (riskLevel === 'Low') {
    return <LowRiskBanner onAcknowledge={onAcknowledge} />
  }
  if (riskLevel === 'Medium') {
    return (
      <MediumRiskBriefing
        script={script}
        items={items}
        onAcknowledge={onAcknowledge}
      />
    )
  }
  return (
    <HighRiskBriefing
      script={script}
      items={items}
      onAcknowledge={onAcknowledge}
      onEdit={onEdit}
    />
  )
}
