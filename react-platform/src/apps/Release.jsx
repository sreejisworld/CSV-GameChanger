/**
 * Release — Lifecycle Phase 6: Release Gate
 *
 * React-native page with:
 *  - Go-live readiness checklist (pulls from Zustand lifecycle state)
 *  - Multi-approver sign-off (up to 3, each calls POST /release/approve)
 *  - Formal go-live button (calls POST /release/go-live)
 *  - Release summary panel showing all lifecycle artefacts
 */
import { useState, useCallback } from 'react'
import { useAppStore } from '../store/useAppStore.js'
import { API_BASE } from '../config.js'

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

async function downloadPDF(url, body, filename) {
  const res = await fetch(url, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  const blob = await res.blob()
  const burl = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = burl; a.download = filename; a.click()
  URL.revokeObjectURL(burl)
}

const API = API_BASE

const ROLES = [
  'System Owner',
  'QA Lead',
  'Business Owner',
  'Validation Lead',
  'IT Manager',
]

const MEANINGS = [
  'Approval for Release',
  'QA Review and Approval',
  'Business Sign-off',
  'Witnessed Approval',
]

const GAMP_LABELS = {
  '1': 'Cat 1 — Infrastructure Software',
  '3': 'Cat 3 — Non-Configured Software',
  '4': 'Cat 4 — Configured Software',
  '5': 'Cat 5 — Custom Software',
}

// ── Readiness check row ───────────────────────────────────────────
function CheckRow({ label, done, detail }) {
  return (
    <div className={`
      flex items-start gap-3 px-4 py-3 rounded-lg border
      ${done
        ? 'border-lime-DEFAULT/20 bg-lime-DEFAULT/5'
        : 'border-border-base bg-bg-card'}
    `}>
      <span className={`
        text-base shrink-0 mt-0.5
        ${done ? 'text-lime-DEFAULT' : 'text-text-muted opacity-40'}
      `}>
        {done ? '✓' : '○'}
      </span>
      <div className="min-w-0">
        <p className={`text-xs font-medium ${done ? 'text-white' : 'text-text-muted'}`}>
          {label}
        </p>
        {detail && (
          <p className="text-[10px] text-text-muted mt-0.5 truncate">
            {detail}
          </p>
        )}
      </div>
    </div>
  )
}

// ── Approval card ─────────────────────────────────────────────────
function ApprovalCard({ approval, index }) {
  return (
    <div className="p-3 rounded-lg border border-lime-DEFAULT/20
                    bg-lime-DEFAULT/5">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lime-DEFAULT text-xs font-bold">
          ✓ Approval {index + 1}
        </span>
        <span className="text-[9px] text-text-muted">
          {new Date(approval.signedAt).toLocaleString()}
        </span>
      </div>
      <p className="text-xs text-white font-medium">{approval.name}</p>
      <p className="text-[10px] text-text-muted">{approval.role} — {approval.meaning}</p>
      <p className="font-mono text-[9px] text-text-muted mt-1 truncate">
        {approval.reasoningHash}
      </p>
    </div>
  )
}

// ── Approver form ─────────────────────────────────────────────────
function ApproverForm({ index, planData, testRuns, activeRunId,
                        releaseData, onApproved, disabled }) {
  const { userProfile } = useAppStore()
  const [name,    setName]    = useState(userProfile?.name ?? '')
  const [role,    setRole]    = useState(ROLES[0])
  const [meaning, setMeaning] = useState(MEANINGS[0])
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')
  const [done,    setDone]    = useState(false)

  const run         = activeRunId ? testRuns[activeRunId] : null
  const testVerdict = run
    ? (run.status === 'locked' ? 'SIGNED OFF' : 'IN PROGRESS')
    : 'NOT STARTED'

  const handleSign = async () => {
    if (!name.trim()) { setError('Name is required.'); return }
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API}/release/approve`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name:  planData.projectName || 'Untitled Project',
          gamp_category: planData.gampCategory || '',
          approver_name: name.trim(),
          approver_role: role,
          meaning,
          test_verdict:  testVerdict,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail ?? 'Approval failed')
      }
      const data = await res.json()
      onApproved({
        approverId:    data.approver_id,
        name:          name.trim(),
        role,
        meaning,
        signedAt:      data.signed_at,
        reasoningHash: data.reasoning_hash,
      })
      setDone(true)
    } catch (err) {
      setError(`${err.message}. Ensure FastAPI is running on port 8000.`)
    } finally {
      setLoading(false)
    }
  }

  if (done) return null

  return (
    <div className="p-4 rounded-lg border border-border-base bg-bg-card">
      <p className="text-[10px] text-text-muted mb-3 font-semibold uppercase
                    tracking-wide">
        Approver {index + 1}
      </p>
      <div className="flex flex-wrap gap-3 items-end">
        <div className="flex flex-col gap-1">
          <label className="text-[10px] text-text-muted">Full Name</label>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Approver name…"
            disabled={disabled}
            className="evolv-input text-xs px-2 py-1.5 w-44"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[10px] text-text-muted">Role</label>
          <select
            value={role}
            onChange={e => setRole(e.target.value)}
            disabled={disabled}
            className="evolv-input evolv-select text-xs px-2 py-1.5"
          >
            {ROLES.map(r => <option key={r}>{r}</option>)}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[10px] text-text-muted">Meaning</label>
          <select
            value={meaning}
            onChange={e => setMeaning(e.target.value)}
            disabled={disabled}
            className="evolv-input evolv-select text-xs px-2 py-1.5"
          >
            {MEANINGS.map(m => <option key={m}>{m}</option>)}
          </select>
        </div>
        <button
          onClick={handleSign}
          disabled={loading || disabled}
          className={`
            px-4 py-1.5 rounded text-xs font-semibold transition-opacity
            bg-blue-DEFAULT text-white
            ${loading || disabled ? 'opacity-40 cursor-not-allowed' : 'hover:opacity-90'}
          `}
        >
          {loading ? 'Signing…' : 'Sign'}
        </button>
      </div>
      {error && (
        <p className="mt-2 text-[10px] text-red-400">{error}</p>
      )}
    </div>
  )
}

// ── Main Release page ─────────────────────────────────────────────
export default function Release() {
  const {
    planData, phaseCompletion,
    testRuns, activeRunId,
    releaseData, addApproval, setReleased,
    setPhaseComplete, setStatusBadge,
    riskData,
  } = useAppStore()

  const [goLiveLoading, setGoLiveLoading] = useState(false)
  const [goLiveError,   setGoLiveError]   = useState('')
  const [pkgLoading,    setPkgLoading]    = useState(false)
  const [pkgError,      setPkgError]      = useState('')

  const run          = activeRunId ? testRuns[activeRunId] : null
  const testSigned   = run?.status === 'locked'
  const approvals    = releaseData.approvals
  const released     = releaseData.released
  const maxApprovers = 3

  // Risk summary
  const riskRows   = Object.values(riskData)
  const highCount  = riskRows.filter(r => {
    if (!r.impact || !r.implMethod) return false
    if (r.impact === 'No GxP') return false
    if (r.impact === 'GxP Direct' && r.implMethod !== 'Out of the Box') return true
    if (r.impact === 'GxP Indirect' && r.implMethod === 'Configured') return true
    return false
  }).length

  const handleExportCSV = useCallback(() => {
    const headers = [
      'approver_index', 'name', 'role',
      'meaning', 'signed_at', 'reasoning_hash',
    ]
    const rows = approvals.map((a, i) => ({
      approver_index: i + 1,
      name:           a.name,
      role:           a.role,
      meaning:        a.meaning,
      signed_at:      a.signedAt,
      reasoning_hash: a.reasoningHash,
    }))
    downloadCSV('release-approvals.csv', headers, rows)
  }, [approvals])

  const handleExportPDF = useCallback(async () => {
    setPkgLoading(true)
    setPkgError('')
    try {
      await downloadPDF(
        `${API_BASE}/exports/release-package`,
        {
          project_name:     planData.projectName || 'Untitled Project',
          gamp_category:    planData.gampCategory || '',
          released_at:      releaseData.releasedAt,
          approvals:        approvals.map(a => ({
            name:           a.name,
            role:           a.role,
            meaning:        a.meaning,
            signed_at:      a.signedAt,
            reasoning_hash: a.reasoningHash,
          })),
          phase_completion: phaseCompletion,
          test_verdict:     run?.status === 'locked'
            ? 'SIGNED OFF' : 'NOT SIGNED',
          frameworks:       planData.regulatoryFrameworks ?? [],
        },
        `release-package-${
          (planData.projectName || 'project')
            .replace(/\s+/g, '-')}.pdf`,
      )
    } catch (err) {
      setPkgError(
        `PDF export failed: ${err.message}. ` +
        'Ensure FastAPI is running on port 8000.'
      )
    } finally {
      setPkgLoading(false)
    }
  }, [planData, releaseData, approvals, phaseCompletion, run])

  // Go-live checklist items
  const checks = [
    {
      label:  'Plan defined',
      done:   phaseCompletion.plan,
      detail: planData.projectName
        ? `${planData.projectName} · ${GAMP_LABELS[planData.gampCategory] ?? 'GAMP category not set'}`
        : 'No project name set',
    },
    {
      label:  'Requirements complete',
      done:   phaseCompletion.requirements,
      detail: 'Requirements and SMART engine phase visited',
    },
    {
      label:  'Risk assessed',
      done:   phaseCompletion.risk,
      detail: riskRows.length > 0
        ? `${riskRows.length} requirements assessed · ${highCount} HIGH risk`
        : 'No risk data yet',
    },
    {
      label:  'Tests executed & signed',
      done:   testSigned,
      detail: run
        ? `Run ${run.runId} · ${run.signerName || 'unsigned'}`
        : 'No test run found — complete Verify phase first',
    },
    {
      label:  'At least one approval signed',
      done:   approvals.length > 0,
      detail: approvals.length > 0
        ? `${approvals.length} of ${maxApprovers} approvers signed`
        : 'No approvals yet',
    },
  ]

  const allChecksDone = checks.every(c => c.done)

  const handleGoLive = async () => {
    setGoLiveLoading(true)
    setGoLiveError('')
    try {
      const res = await fetch(`${API}/release/go-live`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name:    planData.projectName || 'Untitled Project',
          gamp_category:   planData.gampCategory || '',
          approvals_count: approvals.length,
          test_verdict:    testSigned ? 'SIGNED OFF' : 'NOT SIGNED',
          released_by:     approvals[0]?.name ?? 'System',
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail ?? 'Go-live failed')
      }
      setReleased()
      setPhaseComplete('release')
      setStatusBadge('release', { type: 'success', label: 'Released' })
    } catch (err) {
      setGoLiveError(
        `${err.message}. Ensure FastAPI is running on port 8000.`
      )
    } finally {
      setGoLiveLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-bg-base overflow-hidden">

      {/* ── Header strip ─────────────────────────────────── */}
      <div className="flex items-center gap-3 px-6 py-2.5
                      bg-lime-dim border-b border-lime-DEFAULT/20 shrink-0">
        <span className="text-xs font-semibold text-lime-DEFAULT">
          Release Gate
        </span>
        <span className="text-text-muted text-xs">
          {planData.projectName || 'No project name set'}
        </span>
        {planData.gampCategory && (
          <span className="text-[10px] text-text-muted px-2 py-0.5 rounded
                           border border-border-base">
            {GAMP_LABELS[planData.gampCategory] ?? ''}
          </span>
        )}
        <div className="ml-auto flex items-center gap-2">
          {approvals.length > 0 && (
            <button
              onClick={handleExportCSV}
              className="text-[10px] px-2 py-1 rounded border
                         border-border-base text-text-muted
                         hover:text-text-secondary
                         hover:border-border-bright transition-colors"
            >
              📥 Approvals CSV
            </button>
          )}
          {released && (
            <button
              onClick={handleExportPDF}
              disabled={pkgLoading}
              className={`
                text-[10px] px-2 py-1 rounded border font-medium
                transition-colors
                ${pkgLoading
                  ? 'border-border-base text-text-muted opacity-50'
                  : 'border-lime-DEFAULT/40 text-lime-DEFAULT bg-lime-DEFAULT/10'}
              `}
            >
              {pkgLoading ? 'Generating…' : '📄 Release Package PDF'}
            </button>
          )}
          {released && (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded
                             text-lime-DEFAULT border border-lime-DEFAULT/30
                             bg-lime-DEFAULT/10">
              ✓ RELEASED
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto px-6 py-5 space-y-6">

        {/* ── Go-live checklist ─────────────────────────── */}
        <section>
          <h2 className="text-[10px] font-semibold text-text-muted uppercase
                         tracking-widest mb-3">
            Go-Live Readiness
          </h2>
          <div className="grid grid-cols-1 gap-2">
            {checks.map(c => (
              <CheckRow key={c.label} {...c} />
            ))}
          </div>
        </section>

        {/* ── Approver sign-offs ────────────────────────── */}
        <section>
          <h2 className="text-[10px] font-semibold text-text-muted uppercase
                         tracking-widest mb-3">
            Electronic Approvals
            <span className="ml-2 normal-case font-normal">
              ({approvals.length}/{maxApprovers} signed)
            </span>
          </h2>

          {/* Signed approvals */}
          {approvals.length > 0 && (
            <div className="space-y-2 mb-4">
              {approvals.map((a, i) => (
                <ApprovalCard key={a.approverId} approval={a} index={i} />
              ))}
            </div>
          )}

          {/* Approval forms — show unfilled slots up to max */}
          {!released && approvals.length < maxApprovers && (
            <div className="space-y-3">
              {Array.from({
                length: maxApprovers - approvals.length,
              }).map((_, i) => (
                <ApproverForm
                  key={approvals.length + i}
                  index={approvals.length + i}
                  planData={planData}
                  testRuns={testRuns}
                  activeRunId={activeRunId}
                  releaseData={releaseData}
                  onApproved={addApproval}
                  disabled={released}
                />
              ))}
            </div>
          )}
        </section>

        {/* ── Release summary ───────────────────────────── */}
        {released && (
          <section className="p-4 rounded-xl border border-lime-DEFAULT/30
                              bg-lime-DEFAULT/5">
            <h2 className="text-sm font-bold text-lime-DEFAULT mb-3">
              ✓ System Released
            </h2>
            <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-[11px]">
              <div>
                <span className="text-text-muted">Project</span>
                <p className="text-white font-medium mt-0.5">
                  {planData.projectName || '—'}
                </p>
              </div>
              <div>
                <span className="text-text-muted">GAMP Category</span>
                <p className="text-white font-medium mt-0.5">
                  {GAMP_LABELS[planData.gampCategory] ?? '—'}
                </p>
              </div>
              <div>
                <span className="text-text-muted">Released At</span>
                <p className="text-white font-medium mt-0.5">
                  {releaseData.releasedAt
                    ? new Date(releaseData.releasedAt).toLocaleString()
                    : '—'}
                </p>
              </div>
              <div>
                <span className="text-text-muted">Approvers</span>
                <p className="text-white font-medium mt-0.5">
                  {approvals.map(a => a.name).join(', ')}
                </p>
              </div>
              <div>
                <span className="text-text-muted">Test Verdict</span>
                <p className="text-lime-DEFAULT font-bold mt-0.5">
                  {run?.status === 'locked' ? 'SIGNED OFF' : '—'}
                </p>
              </div>
              <div>
                <span className="text-text-muted">Frameworks</span>
                <p className="text-white font-medium mt-0.5">
                  {planData.regulatoryFrameworks?.join(', ') || '—'}
                </p>
              </div>
            </div>
          </section>
        )}

        {/* ── Export error ──────────────────────────────── */}
        {pkgError && (
          <div className="px-4 py-2 rounded border border-red-500/30
                          bg-red-500/10 text-[11px] text-red-400">
            {pkgError}
          </div>
        )}

        {/* ── Go-live button ────────────────────────────── */}
        {!released && (
          <section>
            {goLiveError && (
              <div className="mb-3 px-4 py-2 rounded border border-red-500/30
                              bg-red-500/10 text-[11px] text-red-400">
                {goLiveError}
              </div>
            )}
            <div className="flex items-center gap-4">
              <button
                onClick={handleGoLive}
                disabled={!allChecksDone || goLiveLoading}
                className={`
                  px-6 py-2.5 rounded-lg text-sm font-bold transition-all
                  ${allChecksDone && !goLiveLoading
                    ? 'bg-lime-DEFAULT text-bg-base hover:opacity-90 shadow-[0_0_20px_rgba(50,205,50,0.3)]'
                    : 'bg-bg-card text-text-muted border border-border-base cursor-not-allowed'}
                `}
              >
                {goLiveLoading ? 'Releasing…' : '🚀 Approve for Release'}
              </button>
              {!allChecksDone && (
                <p className="text-[10px] text-text-muted">
                  Complete all checklist items to enable release.
                </p>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
