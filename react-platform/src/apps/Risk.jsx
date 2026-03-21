/**
 * Risk — Lifecycle Phase 3: Per UR/FR Risk Assessment
 *
 * Columns per requirement row:
 *   ID | Type | Requirement Statement
 *   | Impact to Product Quality/Patient Safety
 *   | Implementation Method
 *   | Risk Level (auto-calculated)
 *   | Test Assurance
 *
 * Risk Level matrix (from CLAUDE.md):
 *   GxP Direct  × Custom      → HIGH
 *   GxP Direct  × Configured  → HIGH
 *   GxP Direct  × OOB         → MEDIUM
 *   GxP Indirect× Custom      → MEDIUM
 *   GxP Indirect× Configured  → HIGH
 *   GxP Indirect× OOB         → LOW
 *   No GxP      × any         → LOW
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { useAppStore } from '../store/useAppStore.js'

function downloadCSV(filename, headers, rows) {
  const escape = v =>
    `"${String(v ?? '').replace(/"/g, '""')}"`
  const lines = [
    headers.join(','),
    ...rows.map(r => headers.map(h => escape(r[h])).join(',')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

// ── Sample requirements (seeded until real data flows in) ─
const SEED_REQUIREMENTS = [
  {
    id: 'UR-1', type: 'UR',
    statement: 'The system shall register, track, and dispose of laboratory samples with full chain-of-custody.',
  },
  {
    id: 'FR-1', type: 'FR', parentId: 'UR-1',
    statement: 'The system shall capture sample receipt with timestamp and user attribution.',
  },
  {
    id: 'FR-2', type: 'FR', parentId: 'UR-1',
    statement: 'The system shall generate a unique chain-of-custody record per sample.',
  },
  {
    id: 'UR-2', type: 'UR',
    statement: 'The system shall integrate with laboratory instruments for automated data capture.',
  },
  {
    id: 'FR-3', type: 'FR', parentId: 'UR-2',
    statement: 'The system shall receive instrument data via HL7 or ASTM interface.',
  },
  {
    id: 'UR-3', type: 'UR',
    statement: 'The system shall enforce electronic signatures per 21 CFR Part 11.',
  },
  {
    id: 'FR-4', type: 'FR', parentId: 'UR-3',
    statement: 'The system shall require authenticated e-signature for result approval.',
  },
  {
    id: 'FR-5', type: 'FR', parentId: 'UR-3',
    statement: 'The system shall maintain an immutable audit trail of all e-signature events.',
  },
]

const IMPACT_OPTIONS = [
  { value: 'GxP Direct',   label: 'GxP Direct',   color: '#ef4444' },
  { value: 'GxP Indirect', label: 'GxP Indirect', color: '#f59e0b' },
  { value: 'No GxP',       label: 'No GxP',       color: '#32CD32' },
]

const IMPL_OPTIONS = [
  { value: 'Custom',        label: 'Custom' },
  { value: 'Configured',    label: 'Configured' },
  { value: 'Out of the Box',label: 'OOB' },
]

const TEST_OPTIONS = [
  { value: 'Scripted',   label: 'Scripted' },
  { value: 'Unscripted', label: 'Unscripted' },
]

// ── Risk matrix ──────────────────────────────────────────
function calcRisk(impact, impl) {
  if (!impact || !impl) return null
  if (impact === 'No GxP') return 'LOW'
  if (impact === 'GxP Direct') {
    return impl === 'Out of the Box' ? 'MEDIUM' : 'HIGH'
  }
  // GxP Indirect
  if (impl === 'Configured') return 'HIGH'
  if (impl === 'Custom')     return 'MEDIUM'
  return 'LOW'
}

function defaultTestAssurance(riskLevel) {
  if (riskLevel === 'HIGH')   return 'Scripted'
  if (riskLevel === 'MEDIUM') return 'Scripted'
  return 'Unscripted'
}

const RISK_COLORS = {
  HIGH:   { bg: 'rgba(239,68,68,0.12)',  border: 'rgba(239,68,68,0.35)',  text: '#ef4444' },
  MEDIUM: { bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.35)', text: '#f59e0b' },
  LOW:    { bg: 'rgba(50,205,50,0.12)',  border: 'rgba(50,205,50,0.35)',  text: '#32CD32' },
}

// ── Inline select ────────────────────────────────────────
function InlineSelect({ value, options, placeholder, onChange }) {
  return (
    <select
      value={value ?? ''}
      onChange={e => onChange(e.target.value)}
      className="evolv-input evolv-select text-[11px] py-1 px-2 h-7 min-w-[100px]"
    >
      <option value="">{placeholder}</option>
      {options.map(o => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  )
}

// ── Risk badge ───────────────────────────────────────────
function RiskBadge({ level }) {
  if (!level) return <span className="text-text-muted text-[10px]">—</span>
  const c = RISK_COLORS[level]
  return (
    <span
      className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
      style={{ background: c.bg, border: `1px solid ${c.border}`, color: c.text }}
    >
      {level}
    </span>
  )
}

export default function Risk() {
  const {
    riskData, setRiskRow, setPhaseComplete,
    planData, setTestScript, initTestRun, openTab,
    requirements, setRequirements,
  } = useAppStore()

  const [genLoading,  setGenLoading]  = useState(false)
  const [genError,    setGenError]    = useState('')
  const [genDone,     setGenDone]     = useState(false)
  const [syncState,   setSyncState]   = useState('idle')  // idle | syncing | live | error
  const [syncMsg,     setSyncMsg]     = useState('')
  const [lastSynced,  setLastSynced]  = useState(null)    // Date
  const syncRef = useRef(false)

  const doSync = useCallback(async () => {
    if (syncRef.current) return
    syncRef.current = true
    setSyncState('syncing')
    try {
      const res = await fetch('http://localhost:8000/requirements')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if ((data.requirements ?? []).length > 0) {
        setRequirements(data.requirements)
        setLastSynced(new Date())
        setSyncState('live')
        setSyncMsg(
          `${data.count} requirement${data.count !== 1 ? 's' : ''} from Validation Factory`
        )
      } else {
        setSyncState('idle')
        setSyncMsg('No requirements in Validation Factory yet — using seed data')
      }
    } catch {
      setSyncState('error')
      setSyncMsg('FastAPI not reachable — using seed data')
    } finally {
      syncRef.current = false
    }
  }, [setRequirements])

  // Auto-sync on mount
  useEffect(() => { doSync() }, [])

  // Use live requirements if available, otherwise fall back to seed
  const activeRequirements = requirements.length > 0
    ? requirements
    : SEED_REQUIREMENTS

  const getRow = id => riskData[id] ?? {}

  const handleExportCSV = useCallback(() => {
    const headers = [
      'id', 'type', 'statement',
      'impact', 'implMethod', 'riskLevel', 'testAssurance',
    ]
    const rows = activeRequirements.map(req => {
      const row = getRow(req.id)
      return {
        id:            req.id,
        type:          req.type,
        statement:     req.statement,
        impact:        row.impact        ?? '',
        implMethod:    row.implMethod    ?? '',
        riskLevel:     calcRisk(row.impact, row.implMethod) ?? '',
        testAssurance: row.testAssurance ?? '',
      }
    })
    downloadCSV('risk-matrix.csv', headers, rows)
  }, [activeRequirements, riskData])

  const handleChange = (id, field, value) => {
    setRiskRow(id, field, value)
    setPhaseComplete('risk')

    // Auto-derive test assurance from risk level when impact or impl changes
    if (field === 'impact' || field === 'implMethod') {
      const row     = { ...getRow(id), [field]: value }
      const risk    = calcRisk(
        field === 'impact'     ? value : row.impact,
        field === 'implMethod' ? value : row.implMethod,
      )
      if (risk && !riskData[id]?.testAssuranceOverride) {
        setRiskRow(id, 'testAssurance', defaultTestAssurance(risk))
      }
    }
    if (field === 'testAssurance') {
      // Manual override — mark as overridden so auto-derive stops
      setRiskRow(id, 'testAssuranceOverride', true)
    }
  }

  const allComplete = activeRequirements.every(r => {
    const row = getRow(r.id)
    return row.impact && row.implMethod
  })

  const handleGenerateScript = async () => {
    setGenLoading(true)
    setGenError('')
    setGenDone(false)
    try {
      const rows = activeRequirements.map(r => {
        const row = getRow(r.id)
        return {
          id:            r.id,
          type:          r.type,
          statement:     r.statement,
          impact:        row.impact     || 'GxP Indirect',
          implMethod:    row.implMethod || 'Configured',
          testAssurance: row.testAssurance || 'Scripted',
          riskLevel:     calcRisk(row.impact, row.implMethod) ?? null,
        }
      })
      const res = await fetch('http://localhost:8000/verify/generate-script', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name:  planData.projectName || 'Untitled Project',
          gamp_category: planData.gampCategory || '',
          rows,
          test_type: 'Informal',
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail ?? 'Script generation failed')
      }
      const script = await res.json()
      setTestScript(script.script_id, script)
      initTestRun(script)
      setGenDone(true)
    } catch (err) {
      setGenError(
        `${err.message}. Ensure FastAPI is running on port 8000.`
      )
    } finally {
      setGenLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-bg-base">

      {/* ── Sync status bar ─────────────────────────────── */}
      {(() => {
        const isLive  = syncState === 'live'
        const isErr   = syncState === 'error'
        const isSyncing = syncState === 'syncing'
        const dotColor = isLive ? '#32CD32' : isErr ? '#ef4444' : '#007FFF'
        const bg       = isLive
          ? 'rgba(50,205,50,0.06)'
          : isErr
            ? 'rgba(239,68,68,0.06)'
            : 'rgba(0,127,255,0.06)'
        const border   = isLive
          ? 'rgba(50,205,50,0.18)'
          : isErr
            ? 'rgba(239,68,68,0.18)'
            : 'rgba(0,127,255,0.18)'

        return (
          <div
            className="flex items-center gap-3 px-6 py-1.5 shrink-0 text-[10px]"
            style={{ background: bg, borderBottom: `1px solid ${border}` }}
          >
            {/* Source indicator */}
            <span className="flex items-center gap-1.5 font-medium"
                  style={{ color: dotColor }}>
              <span
                className="w-1.5 h-1.5 rounded-full shrink-0"
                style={{
                  background: dotColor,
                  animation: isSyncing ? 'pulse 1s infinite' : 'none',
                }}
              />
              {isSyncing ? 'Syncing…'
                : isLive  ? 'Live data'
                : isErr   ? 'Offline'
                : 'Seed data'}
            </span>

            {syncMsg && (
              <span className="text-text-muted">{syncMsg}</span>
            )}

            {lastSynced && (
              <span className="text-text-muted">
                · synced {lastSynced.toLocaleTimeString([], {
                  hour: '2-digit', minute: '2-digit', second: '2-digit'
                })}
              </span>
            )}

            {/* Manual sync */}
            <button
              onClick={doSync}
              disabled={isSyncing}
              className="flex items-center gap-1 text-text-muted
                         hover:text-text-secondary transition-colors
                         disabled:opacity-40 ml-1"
              title="Re-sync from Validation Factory"
            >
              <svg width="10" height="10" viewBox="0 0 12 12"
                   className={isSyncing ? 'animate-spin' : ''}>
                <path d="M10 6a4 4 0 01-4 4 4 4 0 01-4-4 4 4 0 014-4"
                      stroke="currentColor" strokeWidth="1.5"
                      fill="none" strokeLinecap="round"/>
                <polyline points="8,2 10,2 10,4" stroke="currentColor"
                          strokeWidth="1.5" strokeLinecap="round" fill="none"/>
              </svg>
              Sync
            </button>

            {/* Revert to seed */}
            {requirements.length > 0 && (
              <button
                onClick={() => {
                  setRequirements([])
                  setSyncState('idle')
                  setSyncMsg('')
                  setLastSynced(null)
                }}
                className="text-text-muted hover:text-red-400
                           transition-colors underline underline-offset-2 ml-1"
              >
                use seed
              </button>
            )}
          </div>
        )
      })()}

      {/* ── Notice strip ────────────────────────────────── */}
      <div className="flex items-center gap-3 px-6 py-2.5
                      bg-amber-dim border-b border-amber-DEFAULT/20 shrink-0">
        <span className="text-xs font-semibold text-amber-DEFAULT">
          Risk Assessment
        </span>
        <span className="text-text-muted text-xs">
          Assign impact, implementation method, and test assurance to each UR and FR
        </span>
        <div className="ml-auto flex items-center gap-3">
          {allComplete && (
            <span className="text-[10px] text-lime-DEFAULT font-medium">
              ✓ All requirements assessed
            </span>
          )}
          {genDone && (
            <button
              onClick={() => openTab('verify')}
              className="text-[10px] px-2.5 py-1 rounded border
                         border-lime-DEFAULT/40 text-lime-DEFAULT
                         bg-lime-DEFAULT/10 hover:bg-lime-DEFAULT/20
                         transition-colors font-medium"
            >
              → Go to Verify
            </button>
          )}
          <button
            onClick={handleExportCSV}
            className="text-[10px] px-2.5 py-1 rounded border
                       border-border-base text-text-muted
                       hover:text-text-secondary hover:border-border-bright
                       transition-colors font-medium"
          >
            📥 Export CSV
          </button>
          <button
            onClick={handleGenerateScript}
            disabled={!allComplete || genLoading}
            className={`
              text-[10px] px-2.5 py-1 rounded border font-medium
              transition-colors
              ${allComplete && !genLoading
                ? 'border-blue-DEFAULT/40 text-blue-DEFAULT bg-blue-dim hover:opacity-90'
                : 'border-border-base text-text-muted cursor-not-allowed opacity-50'}
            `}
          >
            {genLoading ? 'Generating…' : '⚡ Generate Test Script'}
          </button>
        </div>
        {genError && (
          <p className="w-full mt-1 text-[10px] text-red-400">{genError}</p>
        )}
      </div>

      {/* ── Table ───────────────────────────────────────── */}
      <div className="flex-1 overflow-auto px-6 py-4">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="border-b border-border-base">
              {[
                'ID', 'Type', 'Requirement Statement',
                'Impact to Product Quality / Patient Safety',
                'Implementation Method',
                'Risk Level',
                'Test Assurance',
              ].map(h => (
                <th
                  key={h}
                  className="text-left text-[10px] font-semibold text-text-muted
                             uppercase tracking-wide py-2 pr-4 whitespace-nowrap"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {activeRequirements.map((req, idx) => {
              const row      = getRow(req.id)
              const riskLevel = calcRisk(row.impact, row.implMethod)
              const isUR     = req.type === 'UR'

              return (
                <tr
                  key={req.id}
                  className={`
                    border-b transition-colors
                    ${isUR
                      ? 'border-border-bright bg-bg-surface/30'
                      : 'border-border-base bg-transparent'}
                    hover:bg-bg-hover/40
                  `}
                >
                  {/* ID */}
                  <td className="py-2.5 pr-4 font-mono font-medium text-text-secondary
                                 whitespace-nowrap">
                    {!isUR && (
                      <span className="mr-1 text-text-muted opacity-40">└</span>
                    )}
                    {req.id}
                  </td>

                  {/* Type badge */}
                  <td className="py-2.5 pr-4">
                    <span className={`
                      text-[9px] px-1.5 py-0.5 rounded font-semibold uppercase
                      ${isUR
                        ? 'bg-blue-dim text-blue-DEFAULT border border-blue-DEFAULT/30'
                        : 'bg-bg-card text-text-muted border border-border-base'}
                    `}>
                      {req.type}
                    </span>
                  </td>

                  {/* Statement */}
                  <td className="py-2.5 pr-6 text-text-secondary max-w-xs">
                    <span className="line-clamp-2 leading-relaxed">
                      {req.statement}
                    </span>
                  </td>

                  {/* Impact */}
                  <td className="py-2.5 pr-4">
                    <InlineSelect
                      value={row.impact}
                      options={IMPACT_OPTIONS}
                      placeholder="Select…"
                      onChange={v => handleChange(req.id, 'impact', v)}
                    />
                  </td>

                  {/* Implementation method */}
                  <td className="py-2.5 pr-4">
                    <InlineSelect
                      value={row.implMethod}
                      options={IMPL_OPTIONS}
                      placeholder="Select…"
                      onChange={v => handleChange(req.id, 'implMethod', v)}
                    />
                  </td>

                  {/* Risk level */}
                  <td className="py-2.5 pr-4 text-center">
                    <RiskBadge level={riskLevel} />
                  </td>

                  {/* Test assurance */}
                  <td className="py-2.5">
                    <InlineSelect
                      value={row.testAssurance}
                      options={TEST_OPTIONS}
                      placeholder="—"
                      onChange={v => handleChange(req.id, 'testAssurance', v)}
                    />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {/* Legend */}
        <div className="mt-6 flex items-center gap-6 text-[10px] text-text-muted">
          <span className="font-semibold uppercase tracking-wide">
            Risk Matrix:
          </span>
          {[
            ['GxP Direct × Custom/Configured', 'HIGH'],
            ['GxP Indirect × Configured', 'HIGH'],
            ['GxP Direct × OOB / GxP Indirect × Custom', 'MEDIUM'],
            ['No GxP or OOB+Indirect', 'LOW'],
          ].map(([rule, level]) => {
            const c = RISK_COLORS[level]
            return (
              <span key={rule} className="flex items-center gap-1.5">
                <span
                  className="px-1.5 py-0.5 rounded-full text-[9px] font-bold"
                  style={{ background: c.bg, color: c.text }}
                >
                  {level}
                </span>
                <span>{rule}</span>
              </span>
            )
          })}
        </div>
      </div>
    </div>
  )
}
