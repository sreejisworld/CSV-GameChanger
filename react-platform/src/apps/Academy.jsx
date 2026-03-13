/**
 * Academy — Interactive learning hub.
 *
 * Layout:
 *  ┌───────────────────────┬──────────────────────────────┐
 *  │  Lesson Nav + Content │  Live EVOLV Sandbox          │
 *  │  (40%)                │  (60%)                       │
 *  └───────────────────────┴──────────────────────────────┘
 *
 * Features:
 *  - Step-by-step tutorial for Lesson 1: Data fundamentals
 *  - Live SMART transformer sandbox with Spotlight effect
 *  - Subsequent lessons locked until Lesson 1 is read
 */
import { useState, useRef } from 'react'
import { useAppStore } from '../store/useAppStore.js'

const LESSON_STEPS = [
  { id: 1, title: 'What is Data?',                    icon: '📦' },
  { id: 2, title: 'Data Retention Policies',           icon: '🗓️' },
  { id: 3, title: 'Data Archiving in GxP Systems',    icon: '🗄️' },
  { id: 4, title: 'Security Controls (21 CFR Part 11)', icon: '🔐' },
  { id: 5, title: 'Audit Trail Requirements',          icon: '📋' },
]

// ── Deterministic SMART transformer ───────────────────────────
function transformToSMART(raw) {
  const lower = raw.toLowerCase()
  const isData     = lower.includes('data') || lower.includes('store')
                     || lower.includes('record')
  const isSecurity = lower.includes('secur') || lower.includes('access')
                     || lower.includes('auth') || lower.includes('password')
  const isAudit    = lower.includes('audit') || lower.includes('log')
                     || lower.includes('trail')

  let smart = raw.trim()
  smart = smart.replace(
    /^(the system should|system should|should|the system must|must|it must|it should)/i,
    'The system shall'
  )
  if (!/^The system shall/i.test(smart)) smart = 'The system shall ' + smart

  if (isData && isSecurity) {
    smart = 'The system shall encrypt all regulated electronic records using '
          + 'AES-256 and enforce role-based access controls (RBAC) per '
          + '21 CFR Part 11 § 11.10(d), retaining an immutable audit log '
          + 'for a minimum of 3 years.'
  } else if (isAudit) {
    smart = 'The system shall maintain a time-stamped, user-attributed, '
          + 'tamper-evident audit trail for all create, modify, and delete '
          + 'actions on regulated records, retained for the product lifecycle '
          + 'duration plus 1 year, per 21 CFR Part 11 § 11.10(e).'
  } else if (isData) {
    smart = 'The system shall store all GxP-critical electronic records in an '
          + 'audit-trailed, tamper-evident repository, retaining complete records '
          + 'for the duration of the product lifecycle plus 1 year, per '
          + '21 CFR Part 211.68.'
  } else if (isSecurity) {
    smart = 'The system shall enforce multi-factor authentication (MFA) for all '
          + 'users with access to regulated data, logging each login attempt with '
          + 'timestamp and user ID per 21 CFR Part 11 § 11.10(d).'
  } else {
    smart = 'The system shall '
          + smart.replace(/^The system shall /i, '')
          + ' — with measurable acceptance criteria, defined regulatory '
          + 'traceability, and GAMP 5 risk classification.'
  }

  return {
    smart,
    tags: [
      { label: 'Criticality',    value: 'High (GxP Direct)' },
      { label: 'Regulation',     value: '21 CFR Part 11' },
      { label: 'Implementation', value: 'Configured' },
      { label: 'Test Strategy',  value: 'OQ and/or UAT' },
    ],
    ac: [
      'Given a user with write access, When they create a regulated record, '
      + 'Then the system shall generate an immutable audit entry within 1 second.',
      'Given a user attempts unauthorized access, When authentication fails '
      + '3 times, Then the system shall lock the account and notify the admin.',
      'Given the retention period expires, When an archive request is initiated, '
      + 'Then the system shall preserve the full record in tamper-evident format.',
    ],
  }
}

// Pre-filled "bad" requirement for the Try it Now button
const TRY_IT_NOW_PRESET =
  'The system should store data securely and make sure users can access it'

// ── Lesson 1 content ───────────────────────────────────────────
function Lesson1({ onTryItNow }) {
  return (
    <div className="space-y-4 text-xs">
      <h2 className="text-white font-semibold text-sm">📦 What is Data?</h2>
      <p className="text-text-secondary leading-relaxed">
        In GxP-regulated environments, "data" is more than just numbers in a
        spreadsheet. It is the foundation of every regulatory decision.
      </p>

      {/* Data types */}
      <div className="glass rounded-xl p-4 space-y-2.5">
        <p className="text-purple-300 font-semibold mb-1">Types of Data</p>
        {[
          { type: 'Critical',     color: '#ef4444',
            desc: 'Directly affects patient safety or product quality — '
                  + 'batch records, temperature logs, clinical results.' },
          { type: 'Operational',  color: '#f59e0b',
            desc: 'Supports processes with indirect GxP impact — '
                  + 'inventory counts, scheduling, SOP acknowledgements.' },
          { type: 'Metadata',     color: '#007FFF',
            desc: 'Data about data: timestamps, user IDs, system '
                  + 'versions, change history.' },
        ].map(d => (
          <div key={d.type} className="flex items-start gap-2">
            <span className="text-[10px] font-bold mt-0.5 shrink-0"
                  style={{ color: d.color }}>■</span>
            <div>
              <span className="text-white text-[11px] font-medium">{d.type}</span>
              <span className="text-text-muted text-[11px]"> — {d.desc}</span>
            </div>
          </div>
        ))}
      </div>

      {/* ALCOA+ */}
      <div className="glass rounded-xl p-4">
        <p className="text-lime-DEFAULT font-semibold mb-2">FDA ALCOA+ Principle</p>
        {[
          ['A', 'Attributable',      'Who collected it?'],
          ['L', 'Legible',           'Can it be read clearly?'],
          ['C', 'Contemporaneous',   'Recorded at time of activity?'],
          ['O', 'Original',          'First capture of the data?'],
          ['A', 'Accurate',          'Reflects what actually occurred?'],
        ].map(([letter, word, desc]) => (
          <div key={word} className="flex items-center gap-2 mb-1.5">
            <span className="text-lime-DEFAULT font-bold text-sm w-4 shrink-0">
              {letter}
            </span>
            <span className="text-white text-[11px] font-medium w-28 shrink-0">
              {word}
            </span>
            <span className="text-text-muted text-[11px]">{desc}</span>
          </div>
        ))}
        <p className="text-text-muted text-[10px] mt-2 border-t border-border-base pt-2">
          + Complete, Consistent, Enduring, Available
        </p>
      </div>

      {/* Retention */}
      <div className="glass rounded-xl p-4">
        <p className="text-blue-DEFAULT font-semibold mb-2">Data Retention Requirements</p>
        {[
          { rule: '21 CFR Part 211.68', period: '1 year post product expiry' },
          { rule: 'GAMP 5 Appendix S2', period: 'Duration of system lifecycle' },
          { rule: 'FDA Guidance (2018)', period: '3 years min for electronic records' },
        ].map(r => (
          <div key={r.rule} className="flex justify-between text-[11px] mb-1.5">
            <span className="text-text-secondary">{r.rule}</span>
            <span className="text-blue-DEFAULT font-medium">{r.period}</span>
          </div>
        ))}
      </div>

      {/* Archiving vs Backup */}
      <div className="glass rounded-xl p-4">
        <p className="text-amber-400 font-semibold mb-2">Archiving vs. Backup</p>
        <div className="grid grid-cols-2 gap-3 text-[11px]">
          <div>
            <p className="text-white font-medium mb-1">Archive</p>
            <p className="text-text-secondary">
              Long-term, immutable. Regulatory requirement. Tamper-evident.
              Searchable. Compliant with 21 CFR Part 11.
            </p>
          </div>
          <div>
            <p className="text-white font-medium mb-1">Backup</p>
            <p className="text-text-secondary">
              Short-term, disaster recovery only. NOT a regulatory substitute
              for archiving. Cannot satisfy 21 CFR Part 211.68 alone.
            </p>
          </div>
        </div>
      </div>

      {/* Security */}
      <div className="glass rounded-xl p-4">
        <p className="text-red-400 font-semibold mb-2">Security Controls</p>
        {[
          'Role-Based Access Control (RBAC) — least-privilege principle',
          'Audit trail for every create, modify, delete action',
          'Encryption at rest (AES-256) and in transit (TLS 1.3)',
          'System access logs retained per 21 CFR Part 11 § 11.10(d)',
        ].map(item => (
          <div key={item} className="flex items-start gap-2 mb-1.5">
            <span className="text-red-400 text-[10px] mt-0.5 shrink-0">►</span>
            <span className="text-text-secondary text-[11px]">{item}</span>
          </div>
        ))}
      </div>

      {/* Try it Now CTA */}
      <div className="glass rounded-xl p-4 border border-lime-DEFAULT/25
                      bg-lime-DEFAULT/5">
        <p className="text-lime-DEFAULT text-[11px] font-semibold mb-1">
          ✓ You've covered Lesson 1!
        </p>
        <p className="text-text-muted text-[10px] mb-3">
          Ready to apply it? Click below and EVOLV will pre-load a bad requirement
          into the sandbox so you can hit the Transform button.
        </p>
        <button
          onClick={onTryItNow}
          className="w-full py-2 rounded-xl bg-lime-DEFAULT text-bg-base
                     text-xs font-semibold hover:brightness-110 transition-all
                     shadow-[0_0_16px_rgba(50,205,50,0.3)]"
        >
          ⚡ Try it Now
        </button>
      </div>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────
export default function Academy() {
  const { drafts, setDraft } = useAppStore()
  const [activeLesson, setActiveLesson] = useState(1)

  // Draft input lives in Zustand — survives tab switches
  const input    = drafts['academy']?.sandboxInput ?? ''
  const setInput = val => setDraft('academy', 'sandboxInput', val)

  const [result,    setResult]    = useState(null)
  const [spotlight, setSpotlight] = useState(false)
  const resultRef = useRef(null)

  const handleTransform = () => {
    if (!input.trim()) return
    const transformed = transformToSMART(input)
    setResult(transformed)
    setSpotlight(true)
    setTimeout(() => {
      resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)
  }

  const dismissSpotlight = () => setSpotlight(false)

  // "Try it Now" — pre-fills sandbox from lesson
  const tryItNow = preset => {
    setInput(preset)
    setResult(null)
    setSpotlight(false)
  }

  return (
    <div className="h-full flex flex-col bg-bg-base overflow-hidden">

      {/* Spotlight backdrop */}
      {spotlight && (
        <div
          className="fixed inset-0 bg-black/70 z-40 cursor-pointer
                     transition-opacity duration-300"
          onClick={dismissSpotlight}
        />
      )}

      {/* Header */}
      <div className="px-6 py-4 border-b border-border-base shrink-0">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-white font-bold text-lg">Academy</h1>
          <span className="text-[9px] px-2 py-0.5 rounded-full border
                           border-purple-500/40 text-purple-400 bg-purple-500/10">
            Beta
          </span>
          <span className="text-[9px] px-2 py-0.5 rounded-full border
                           border-border-base text-text-muted">
            Module 1 of 5 — Data Fundamentals
          </span>
        </div>
        <p className="text-text-secondary text-xs">
          GAMP 5 guided walkthroughs with live EVOLV sandbox practice.
        </p>
      </div>

      {/* Split screen */}
      <div className="flex flex-1 min-h-0">

        {/* ── Left: Tutorial guide ────────────────────── */}
        <div className="w-2/5 border-r border-border-base flex flex-col
                        overflow-hidden">

          {/* Lesson nav */}
          <div className="px-4 py-3 border-b border-border-base shrink-0 space-y-1">
            {LESSON_STEPS.map(step => {
              const locked = step.id > 1
              return (
                <button
                  key={step.id}
                  onClick={() => !locked && setActiveLesson(step.id)}
                  disabled={locked}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg
                             text-xs text-left transition-colors
                             ${activeLesson === step.id && !locked
                               ? 'bg-purple-500/15 text-purple-300 border border-purple-500/30'
                               : locked
                                 ? 'text-text-muted opacity-50 cursor-not-allowed'
                                 : 'text-text-muted hover:text-text-secondary hover:bg-bg-hover'
                             }`}
                >
                  <span>{step.icon}</span>
                  <span className="flex-1">{step.title}</span>
                  {locked && (
                    <span className="text-[9px] border border-border-base rounded
                                     px-1.5 py-0.5 text-text-muted">
                      Locked
                    </span>
                  )}
                </button>
              )
            })}
          </div>

          {/* Lesson content */}
          <div className="flex-1 overflow-y-auto p-5">
            {activeLesson === 1
              ? <Lesson1 onTryItNow={() => tryItNow(TRY_IT_NOW_PRESET)} />
              : (
              <div className="flex flex-col items-center justify-center h-full
                              text-center gap-3">
                <span className="text-5xl">🔒</span>
                <p className="text-text-secondary text-sm">
                  Complete Lesson 1 to unlock this module.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* ── Right: Live Sandbox ─────────────────────── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="px-5 py-3 border-b border-border-base shrink-0">
            <div className="flex items-center gap-2">
              <span className="text-lime-DEFAULT text-sm">⚡</span>
              <p className="text-white text-xs font-semibold">
                Live Sandbox — EVOLV SMART Transformer
              </p>
              <span className="ai-badge text-[9px]">EVOLV AI</span>
            </div>
            <p className="text-text-muted text-[11px] mt-1">
              Paste a vague requirement and watch EVOLV transform it into
              audit-ready, GAMP 5 compliant language.
            </p>
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-4">

            {/* Hint card */}
            <div className="glass rounded-xl p-3 border border-purple-500/20
                            bg-purple-500/5">
              <p className="text-purple-300 text-[11px] font-medium mb-1">
                💡 Try one of these:
              </p>
              <div className="space-y-1">
                {[
                  '"The system should store data securely"',
                  '"Users must be able to log in"',
                  '"We need an audit log"',
                ].map(hint => (
                  <button
                    key={hint}
                    onClick={() => setInput(hint.replace(/"/g, ''))}
                    className="block text-[11px] text-text-secondary
                               hover:text-purple-300 transition-colors text-left"
                  >
                    → {hint}
                  </button>
                ))}
              </div>
            </div>

            {/* Input */}
            <div>
              <label className="text-[10px] text-text-muted block mb-1.5">
                Your vague requirement
              </label>
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="e.g. The system should store data securely"
                className="w-full bg-bg-hover border border-border-base rounded-xl
                           px-4 py-3 text-xs text-text-primary outline-none
                           resize-none focus:border-purple-500/50 transition-colors"
                rows={4}
              />
            </div>

            {/* Transform button — raised above backdrop via z-50 */}
            <div className={`relative ${spotlight ? 'z-50' : ''}`}>
              <button
                onClick={handleTransform}
                disabled={!input.trim()}
                className="w-full flex items-center justify-center gap-2 py-3
                           rounded-xl text-sm font-semibold transition-all
                           disabled:opacity-40 bg-lime-DEFAULT text-bg-base
                           shadow-[0_0_24px_rgba(50,205,50,0.4)]
                           hover:shadow-[0_0_36px_rgba(50,205,50,0.6)]
                           hover:brightness-110"
              >
                <span>⚡</span>
                EVOLV Transform
              </button>
            </div>

            {/* Result panel — also raised above backdrop */}
            {result && (
              <div
                ref={resultRef}
                className={`animate-fade-in space-y-3 ${spotlight ? 'relative z-50' : ''}`}
              >
                <div className="glass-lime rounded-xl p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lime-DEFAULT text-sm">✓</span>
                    <p className="text-lime-DEFAULT text-xs font-semibold">
                      SMART Requirement Generated
                    </p>
                  </div>
                  <p className="text-white text-xs leading-relaxed font-medium mb-3">
                    {result.smart}
                  </p>
                  <div className="neon-sep mb-3" />
                  <div className="grid grid-cols-2 gap-2">
                    {result.tags.map(tag => (
                      <div key={tag.label} className="text-[11px]">
                        <span className="text-lime-DEFAULT font-semibold">
                          {tag.label}:{' '}
                        </span>
                        <span className="text-text-secondary">{tag.value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass rounded-xl p-4">
                  <p className="text-blue-DEFAULT text-xs font-semibold mb-2">
                    📋 Acceptance Criteria (Given / When / Then)
                  </p>
                  {result.ac.map((ac, i) => (
                    <p key={i}
                       className="text-text-secondary text-[11px] leading-relaxed mb-2">
                      <span className="text-blue-DEFAULT font-medium">{i + 1}. </span>
                      {ac}
                    </p>
                  ))}
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={dismissSpotlight}
                    className="flex-1 py-2 rounded-xl border border-border-base
                               text-xs text-text-muted hover:text-text-secondary
                               hover:bg-bg-hover transition-colors"
                  >
                    Continue learning →
                  </button>
                  <button
                    onClick={() => { setInput(''); setResult(null); setSpotlight(false) }}
                    className="flex-1 py-2 rounded-xl border border-purple-500/30
                               text-xs text-purple-300 hover:bg-purple-500/10
                               transition-colors"
                  >
                    Try another →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
