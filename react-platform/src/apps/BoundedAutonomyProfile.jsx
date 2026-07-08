/**
 * BoundedAutonomyProfile.jsx — Sprint 40 Bounded Autonomy
 * Profile assessment UI.
 *
 * Single-page workflow:
 *   1. Fill the Context of Use form (defaults to demo COU)
 *   2. Click "Pre-flight check" - 30-second exclusion screen
 *      OR "Assess Profile" - full 3-layer diagnostic
 *   3. Inspect the tier badge, Failure Envelope scores,
 *      Assurance Argument, and Fragility Markers
 *   4. Click "Download signed PDF" to get the customer artefact
 *
 * Companion surface to the Sprint 39 Trustworthiness Report.
 * Both engines accept the same COU shape so a single React
 * call can drive both PDFs.
 *
 * :requirement: URS-40.12 - React UI for the Bounded Autonomy
 *               Profile assessment.
 */
import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { API_BASE } from '../config.js'

// ── Per-tier colour map (matches the PDF tier badge palette) ───────
const TIER_COLOR = {
  'BAP-0': { fg: '#6B7280', bg: 'rgba(107,114,128,0.10)' }, // grey
  'BAP-1': { fg: '#3B82F6', bg: 'rgba(59,130,246,0.10)'  }, // blue
  'BAP-2': { fg: '#10b981', bg: 'rgba(50,205,50,0.12)'   }, // lime
  'BAP-3': { fg: '#F59E0B', bg: 'rgba(245,158,11,0.12)'  }, // amber
  'BAP-4': { fg: '#A855F7', bg: 'rgba(168,85,247,0.12)'  }, // purple
  'BAP-X': { fg: '#EF4444', bg: 'rgba(239,68,68,0.12)'   }, // red
}

const DEFAULT_COU = {
  customer_name:       'Demo CDMO',
  statement:
    'EVOLV drafts URs and FRs for a GxP-Direct LIMS at a CDMO; '
    + 'outputs require QA sign-off before being persisted to Vault.',
  deployment_region:   'US',
  gxp_classification:  'GxP Direct',
  risk_level:          'High',
  decision_authority:  'AI proposes, human signs',
  target_system:       'LabCore LIMS v4.2',
  poc_or_production:   'POC',
}

const SAMPLE_BAD_COU =
  'AI signs the electronic signature on behalf of the QA reviewer'

export default function BoundedAutonomyProfile() {
  const [cou,      setCou]      = useState(DEFAULT_COU)
  const [profile,  setProfile]  = useState(null)
  const [exclCheck, setExclCheck] = useState(null)
  const [loading,  setLoading]  = useState('')   // 'check' | 'assess' | 'pdf'
  const [error,    setError]    = useState('')

  const onChange = (k, v) =>
    setCou(prev => ({ ...prev, [k]: v }))

  // ── Pre-flight exclusion check ────────────────────────────────
  const runExclusionCheck = useCallback(async () => {
    setLoading('check'); setError(''); setExclCheck(null)
    try {
      const res = await fetch(
        `${API_BASE}/bap/check-exclusion`,
        {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            statement:          cou.statement,
            decision_authority: cou.decision_authority,
          }),
          signal: AbortSignal.timeout(10000),
        },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setExclCheck(await res.json())
    } catch (e) {
      setError(
        e.message ?? 'Pre-flight check failed. '
        + 'Ensure FastAPI is running on port 8000.',
      )
    } finally {
      setLoading('')
    }
  }, [cou.statement, cou.decision_authority])

  // ── Full BAP assessment ────────────────────────────────────────
  const runAssess = useCallback(async () => {
    setLoading('assess'); setError(''); setProfile(null)
    try {
      const res = await fetch(`${API_BASE}/bap/assess`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ cou, user_id: 'demo' }),
        signal:  AbortSignal.timeout(20000),
      })
      if (!res.ok) {
        const eb = await res.json().catch(() => ({}))
        throw new Error(eb.detail ?? `HTTP ${res.status}`)
      }
      setProfile(await res.json())
    } catch (e) {
      setError(
        e.message ?? 'Assessment failed. '
        + 'Ensure FastAPI is running on port 8000.',
      )
    } finally {
      setLoading('')
    }
  }, [cou])

  // ── PDF download ───────────────────────────────────────────────
  const downloadPdf = useCallback(async () => {
    setLoading('pdf'); setError('')
    try {
      const res = await fetch(`${API_BASE}/bap/pdf`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cou,
          user_id: 'demo',
          meaning: 'Approval of Bounded Autonomy Profile',
          signers: {
            ai_model_sme:   'Sreejith Sreedharan',
          },
        }),
        signal: AbortSignal.timeout(30000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href = url
      a.download = `${profile?.profile_id ?? 'BAP-EVOLV'}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e.message ?? 'PDF download failed.')
    } finally {
      setLoading('')
    }
  }, [cou, profile])

  // ── Demo helper buttons ────────────────────────────────────────
  const loadBadSample = () =>
    setCou(prev => ({ ...prev, statement: SAMPLE_BAD_COU }))
  const reset = () => {
    setCou(DEFAULT_COU); setProfile(null); setExclCheck(null)
    setError('')
  }

  return (
    <div className="flex flex-col h-full bg-bg-base overflow-hidden">

      {/* ── Header strip ─────────────────────────────────────── */}
      <div className="flex items-center gap-3 px-6 py-2.5
                      bg-blue-dim border-b border-blue-DEFAULT/20
                      shrink-0">
        <span className="text-xs font-semibold text-blue-DEFAULT">
          Bounded Autonomy Profile
        </span>
        <span className="text-text-muted text-xs">
          Sprint 40 — proportional assurance tier from a
          3-layer diagnostic
        </span>
        <div className="ml-auto flex gap-2">
          <button onClick={loadBadSample}
            className="px-2.5 py-1 text-[10px] rounded-lg
                       border border-border-base text-text-muted
                       hover:text-text-secondary
                       hover:border-border-bright transition-colors">
            🧪 Load BAP-X sample
          </button>
          <button onClick={reset}
            className="px-2.5 py-1 text-[10px] rounded-lg
                       border border-border-base text-text-muted
                       hover:text-text-secondary
                       hover:border-border-bright transition-colors">
            ↺ Reset
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

        {/* ── Intro ────────────────────────────────────────── */}
        <div>
          <h2 className="text-text-primary font-semibold text-sm mb-1">
            Which assurance tier is appropriate for this AI deployment?
          </h2>
          <p className="text-text-secondary text-xs leading-relaxed">
            Fill in the Context of Use below. EVOLV runs it through
            three diagnostic layers — Impact Class, Failure Envelope,
            Control Sustainability — and returns a proportional tier
            (BAP-0 through BAP-4, or BAP-X exclusion) plus the
            7-question Assurance Argument that a qualified human
            signs.
          </p>
        </div>

        {/* ── COU form ─────────────────────────────────────── */}
        <div className="glass rounded-xl p-4 space-y-3">
          <p className="text-text-primary text-[12px] font-semibold">
            🛡️ Context of Use
          </p>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Customer name">
              <input className="evolv-input w-full text-xs px-3 py-2"
                value={cou.customer_name}
                onChange={e => onChange('customer_name', e.target.value)}
              />
            </Field>
            <Field label="Target system (optional)">
              <input className="evolv-input w-full text-xs px-3 py-2"
                value={cou.target_system}
                onChange={e => onChange('target_system', e.target.value)}
              />
            </Field>
          </div>

          <Field label="Deployment statement"
                 hint="One sentence — include who signs">
            <textarea rows={3}
              className="evolv-input w-full text-xs px-3 py-2 resize-none"
              value={cou.statement}
              onChange={e => onChange('statement', e.target.value)}
            />
          </Field>

          <div className="grid grid-cols-3 gap-3">
            <Field label="Region">
              <select className="evolv-input w-full text-xs px-3 py-2"
                value={cou.deployment_region}
                onChange={e =>
                  onChange('deployment_region', e.target.value)}>
                {['US', 'EU', 'UK', 'India', 'APAC', 'Global']
                  .map(r => <option key={r}>{r}</option>)}
              </select>
            </Field>
            <Field label="GxP class">
              <select className="evolv-input w-full text-xs px-3 py-2"
                value={cou.gxp_classification}
                onChange={e =>
                  onChange('gxp_classification', e.target.value)}>
                {['GxP Direct', 'GxP Indirect', 'Non-GxP']
                  .map(r => <option key={r}>{r}</option>)}
              </select>
            </Field>
            <Field label="Risk level">
              <select className="evolv-input w-full text-xs px-3 py-2"
                value={cou.risk_level}
                onChange={e =>
                  onChange('risk_level', e.target.value)}>
                {['High', 'Medium', 'Low']
                  .map(r => <option key={r}>{r}</option>)}
              </select>
            </Field>
          </div>

          <Field label="Decision authority">
            <input className="evolv-input w-full text-xs px-3 py-2"
              value={cou.decision_authority}
              onChange={e =>
                onChange('decision_authority', e.target.value)}
            />
          </Field>

          {/* Action row */}
          <div className="flex flex-wrap gap-2 pt-2">
            <button onClick={runExclusionCheck}
              disabled={loading !== '' || !cou.statement.trim()}
              className="px-3 py-1.5 text-xs rounded border
                         border-border-base text-text-primary
                         hover:border-border-bright
                         disabled:opacity-40 transition-colors">
              {loading === 'check' ? '🔍 Checking…' : '🔍 Pre-flight check (30 sec)'}
            </button>
            <button onClick={runAssess}
              disabled={loading !== '' || !cou.statement.trim()}
              className="px-3 py-1.5 text-xs rounded font-semibold
                         text-white shadow-sm
                         disabled:opacity-40 disabled:cursor-not-allowed
                         transition-opacity hover:opacity-90"
              style={{ background:
                'linear-gradient(90deg, #007FFF, #32CD32)' }}>
              {loading === 'assess'
                ? '🛡️ Running 3-layer diagnostic…'
                : '🛡️ Assess Profile (full)'}
            </button>
            {profile && (
              <button onClick={downloadPdf}
                disabled={loading !== ''}
                className="px-3 py-1.5 text-xs rounded
                           border border-border-base text-text-primary
                           hover:border-border-bright
                           disabled:opacity-40 transition-colors ml-auto">
                {loading === 'pdf'
                  ? '📑 Generating PDF…'
                  : '📑 Download signed PDF'}
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="px-3 py-2 rounded-lg text-[11px]
                          border border-red-500/30
                          bg-red-500/10 text-red-400">
            {error}
          </div>
        )}

        {/* ── Pre-flight check result ───────────────────── */}
        <AnimatePresence>
          {exclCheck && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              className="glass rounded-xl p-4 space-y-2"
              style={{
                borderLeft: `3px solid ${
                  exclCheck.would_be_excluded ? '#EF4444' : '#10b981'
                }`,
              }}>
              <p className="text-text-primary text-[12px] font-semibold">
                {exclCheck.would_be_excluded
                  ? '🚫 Would be excluded (BAP-X)'
                  : '✅ Would proceed to full assessment'}
              </p>
              <p className="text-text-secondary text-[11px]
                            leading-relaxed">
                {exclCheck.verdict}
              </p>
              {exclCheck.rules_fired?.length > 0 && (
                <div className="space-y-1.5 mt-2">
                  {exclCheck.rules_fired.map(r => (
                    <div key={r.rule_id}
                      className="text-[10px] text-text-secondary
                                 bg-bg-base/40 rounded px-2.5 py-1.5">
                      <strong className="text-red-400">
                        {r.rule_id}
                      </strong> · {r.violation} — <em>{r.why}</em>
                    </div>
                  ))}
                </div>
              )}
              <p className="text-[10px] text-text-muted italic
                            leading-relaxed mt-2">
                {exclCheck.principle}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Full assessment result ────────────────────── */}
        <AnimatePresence>
          {profile && (
            <motion.div
              key={profile.profile_id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4">

              {/* Tier badge card */}
              <div className="glass rounded-xl p-4 flex items-center
                              gap-4 flex-wrap">
                <span className="text-[10px] uppercase tracking-wider
                                 text-text-muted font-semibold">
                  Verdict
                </span>
                <TierBadge
                  tierId={profile.tier_id}
                  tierName={profile.tier_name}
                />
                <span className="text-text-secondary text-[11px]
                                 flex-1 min-w-[200px]">
                  {profile.tier_summary}
                </span>
                <span className="text-[9px] font-mono text-text-muted">
                  {profile.profile_id}
                </span>
              </div>

              {/* Three-layer score row */}
              <div className="grid grid-cols-3 gap-3">
                <ScoreCard label="Impact Class"
                  primary={profile.impact_class?.class_id}
                  secondary={profile.impact_class?.name} />
                <ScoreCard label="Failure Envelope coverage"
                  primary={`${profile.failure_envelope
                    ?.coverage_score ?? 0}`}
                  secondary="/100" />
                <ScoreCard label="Control Sustainability"
                  primary={`${profile.control_sustainability
                    ?.capability_score ?? 0}`}
                  secondary="/100" />
              </div>

              {/* Tier rationale */}
              <Section title="Tier Rationale Chain">
                <ul className="space-y-1">
                  {profile.tier_rationale?.map((r, i) => (
                    <li key={i}
                      className="text-[11px] text-text-secondary
                                 leading-relaxed pl-3 border-l-2
                                 border-border-base">
                      {r}
                    </li>
                  ))}
                </ul>
              </Section>

              {/* Fragility Markers (the differentiator) */}
              <Section title="Q7 Fragility Markers"
                       subtitle="Standing assumptions that would
                       invalidate the safety case if they shift.
                       Each names an owner role + watch signal.">
                <div className="grid grid-cols-1 gap-3">
                  {profile.assurance_argument?.q7_fragility_markers
                    ?.map((fm, i) => (
                    <div key={i}
                      className="bg-bg-base/40 rounded-lg p-3
                                 space-y-1.5 border-l-2 border-blue-DEFAULT">
                      <p className="text-[10px] uppercase
                                    tracking-wider text-blue-DEFAULT
                                    font-semibold">
                        Marker {i + 1}
                      </p>
                      <p className="text-[11px] text-text-primary
                                    leading-relaxed">
                        <strong>Assumption:</strong> {fm.assumption}
                      </p>
                      <p className="text-[11px] text-text-secondary
                                    leading-relaxed">
                        <strong>If broken:</strong> {fm.if_broken_then}
                      </p>
                      <p className="text-[10px] text-text-secondary
                                    leading-relaxed">
                        <strong>Watch signal:</strong> {fm.watch_signal}
                      </p>
                      <p className="text-[10px] text-text-muted">
                        Owner: <strong>{fm.owner_role}</strong>
                      </p>
                    </div>
                  ))}
                </div>
              </Section>

              {/* Required controls + next actions */}
              <div className="grid grid-cols-2 gap-3">
                <Section
                  title={`Required Controls at ${profile.tier_id}`}>
                  <ul className="space-y-1">
                    {profile.required_controls_at_tier?.map((c, i) => (
                      <li key={i}
                        className="text-[11px] text-text-secondary">
                        • {c}
                      </li>
                    ))}
                  </ul>
                </Section>
                <Section title="Next Actions">
                  <ul className="space-y-1">
                    {profile.next_actions?.map((a, i) => (
                      <li key={i}
                        className="text-[11px] text-text-secondary">
                        → {a}
                      </li>
                    ))}
                  </ul>
                </Section>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

// ── Helpers ────────────────────────────────────────────────────────

function Field({ label, hint, children }) {
  return (
    <div>
      <label className="text-[10px] uppercase tracking-wider
                        text-text-muted block mb-1 font-semibold">
        {label}
        {hint && (
          <span className="ml-2 text-text-muted normal-case
                           tracking-normal font-normal">
            {hint}
          </span>
        )}
      </label>
      {children}
    </div>
  )
}

function TierBadge({ tierId, tierName }) {
  const colors = TIER_COLOR[tierId] ?? TIER_COLOR['BAP-0']
  return (
    <span className="px-3 py-1.5 rounded-lg font-bold text-[12px]
                     shrink-0"
          style={{
            background: colors.bg,
            color:      colors.fg,
            border:     `1px solid ${colors.fg}40`,
          }}>
      {tierId} — {tierName}
    </span>
  )
}

function ScoreCard({ label, primary, secondary }) {
  return (
    <div className="glass rounded-xl p-3 text-center">
      <p className="text-[9px] uppercase tracking-wider
                    text-text-muted font-semibold mb-1">
        {label}
      </p>
      <p className="text-text-primary text-lg font-bold leading-none">
        {primary}
        <span className="text-text-muted text-xs ml-1">
          {secondary}
        </span>
      </p>
    </div>
  )
}

function Section({ title, subtitle, children }) {
  return (
    <div className="glass rounded-xl p-4 space-y-2">
      <div>
        <p className="text-text-primary text-[12px] font-semibold">
          {title}
        </p>
        {subtitle && (
          <p className="text-text-muted text-[10px] mt-0.5
                        leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>
      {children}
    </div>
  )
}
