/**
 * Home — LaunchPad with Bento Grid layout.
 *
 * Each card has a 3D glassmorphism icon that floats on hover.
 * Clicking a card opens that app in a new tab.
 *
 * Grid layout (4-column):
 *   [Validation Factory — 2×2] [Dev Portal — 1×1] [Navigator — 1×1]
 *   [Academy — 1×2]            [Config — 1×1]     [Stats — 2×1]
 */
import { APPS } from '../data/apps.js'

// Bento grid slot config — [appId, colSpan, rowSpan, extraClass]
const BENTO = [
  ['validation-factory', 2, 2, 'bento-hero-bg lime'],
  ['dev-portal',         1, 1, ''],
  ['navigator',          1, 1, ''],
  ['academy',            1, 2, ''],
  ['config',             1, 1, ''],
]

const STATS = [
  { label: 'AI Requirements Generated', value: '2,847', color: '#32CD32', icon: '📋' },
  { label: 'Test Scripts Created',       value: '1,203', color: '#007FFF', icon: '🧪' },
  { label: 'Audit Events Logged',        value: '48,921', color: '#a855f7', icon: '📊' },
  { label: 'Active Validation Projects', value: '7',      color: '#f59e0b', icon: '🏭' },
]

export default function Home({ openTab }) {
  return (
    <div className="h-full overflow-y-auto bg-bg-base">
      <div className="max-w-6xl mx-auto px-6 py-8">

        {/* ── Hero header ─────────────────────────────── */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold text-white">
              EVOLV Platform
            </h1>
            <span className="ai-badge animate-pulse-lime text-sm px-2 py-1">
              EVOLV AI Active
            </span>
          </div>
          <p className="text-text-secondary text-sm">
            The Validation Factory — GAMP 5 · CSA · 21 CFR Part 11 · FDA AI Guidance 2026
          </p>
          <div className="neon-sep mt-4" />
        </div>

        {/* ── Stats row ───────────────────────────────── */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          {STATS.map(stat => (
            <div key={stat.label}
              className="glass rounded-xl p-4 flex items-center gap-3">
              <span className="text-2xl">{stat.icon}</span>
              <div>
                <p className="text-xs text-text-muted">{stat.label}</p>
                <p className="text-xl font-bold" style={{ color: stat.color }}>
                  {stat.value}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* ── Bento Grid ──────────────────────────────── */}
        <div
          className="grid gap-3"
          style={{
            gridTemplateColumns: 'repeat(4, 1fr)',
            gridAutoRows: '160px',
          }}
        >
          {BENTO.map(([appId, colSpan, rowSpan, extra]) => {
            const app = APPS.find(a => a.id === appId)
            if (!app) return null
            return (
              <BentoCard
                key={appId}
                app={app}
                colSpan={colSpan}
                rowSpan={rowSpan}
                extra={extra}
                onClick={() => openTab(appId)}
              />
            )
          })}

          {/* Compliance card (decorative) */}
          <div
            className="glass rounded-2xl p-5 flex flex-col justify-between"
            style={{ gridColumn: 'span 2', gridRow: 'span 1' }}
          >
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">🛡️</span>
              <p className="text-text-secondary text-xs font-semibold uppercase tracking-wider">
                Compliance Status
              </p>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: '21 CFR Part 11', ok: true },
                { label: 'GAMP 5 Rev 2',  ok: true },
                { label: 'FDA AI 2026',    ok: true },
                { label: 'ISO 13485',      ok: true },
                { label: 'GMP Mode',       ok: true },
                { label: 'Audit Trail',    ok: true },
              ].map(c => (
                <div key={c.label}
                  className="flex items-center gap-1.5 text-[10px]">
                  <span className={c.ok ? 'text-lime-DEFAULT' : 'text-red-400'}>
                    {c.ok ? '✓' : '✗'}
                  </span>
                  <span className="text-text-secondary">{c.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* EVOLV AI status card (decorative) */}
          <div
            className="glass-lime rounded-2xl p-5 flex flex-col justify-between"
            style={{ gridColumn: 'span 2', gridRow: 'span 1' }}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-xl">🤖</span>
                <p className="text-lime-DEFAULT text-xs font-semibold uppercase tracking-wider">
                  EVOLV AI Engine
                </p>
              </div>
              <span className="text-[9px] text-lime-DEFAULT border border-lime-DEFAULT/30
                               bg-lime-dim rounded-full px-2 py-0.5 animate-pulse-lime">
                Online
              </span>
            </div>
            <div className="space-y-1.5 text-[11px] text-text-secondary">
              {[
                'RequirementArchitect — GAMP 5 URS generation',
                'VerificationAgent — Regulatory compliance check',
                'DeltaAgent — CSA test script generation',
                'SentinelImpactAgent — Blast radius analysis',
              ].map(agent => (
                <div key={agent} className="flex items-center gap-2">
                  <span className="text-lime-DEFAULT text-[9px]">●</span>
                  <span>{agent}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Bottom tagline ───────────────────────────── */}
        <p className="text-center text-text-muted text-xs mt-8">
          Powered by EVOLV | WingstarTech Inc. — AI-assisted, human-approved.
        </p>
      </div>
    </div>
  )
}

function BentoCard({ app, colSpan, rowSpan, extra, onClick }) {
  return (
    <div
      className={`glass rounded-2xl p-5 bento-card ${extra} flex flex-col justify-between`}
      style={{
        gridColumn: `span ${colSpan}`,
        gridRow:    `span ${rowSpan}`,
      }}
      onClick={onClick}
    >
      {/* Top section */}
      <div className="flex items-start justify-between">
        <span
          className="app-icon-3d leading-none"
          style={{ fontSize: colSpan > 1 ? '3rem' : '2rem' }}
        >
          {app.emoji}
        </span>
        {app.badge && (
          <span className={`
            text-[9px] px-1.5 py-0.5 rounded border
            ${app.accentClass === 'lime'
              ? 'bg-lime-dim border-lime-DEFAULT/30 text-lime-DEFAULT'
              : 'bg-blue-dim border-blue-DEFAULT/30 text-blue-DEFAULT'}
          `}>
            {app.badge}
          </span>
        )}
      </div>

      {/* Bottom section */}
      <div>
        <h3 className={`font-semibold text-white mb-1
                        ${colSpan > 1 ? 'text-lg' : 'text-sm'}`}>
          {app.label}
        </h3>
        {(colSpan > 1 || rowSpan > 1) && (
          <p className="text-text-secondary text-xs leading-relaxed">
            {app.description}
          </p>
        )}
        <div className="flex items-center gap-1.5 mt-2">
          <span
            className="text-xs font-medium"
            style={{ color: app.accentColor }}
          >
            Open →
          </span>
        </div>
      </div>
    </div>
  )
}
