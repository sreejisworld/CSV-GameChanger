/**
 * V-model geometry — single source of truth for the V-shape used by:
 *   • VModelHero  (Home.jsx, Sprint 32) — full-size landing hero, animated draw-in
 *   • LifecycleStrip (Sprint 33)        — compact persistent spine above phase pages
 *
 * Both consumers import the same `PHASE_ORDER` so they can never drift,
 * and pick the geometry variant (HERO vs SPINE) appropriate to their
 * vertical real estate. Keeping the spine's V-shape visually consistent
 * with the hero makes the V-model the platform's spine — the user sees
 * the same brand visual on Home and again above every phase page.
 */

// ── Phase order — left arm descends (Plan→Design), right arm ascends
//    (Verify→Retire). Design + Verify form the apex.
export const PHASE_ORDER = [
  'plan', 'requirements', 'risk', 'design',
  'verify', 'release', 'monitor', 'retire',
]

// Short labels that fit under compact strip nodes.
export const PHASE_SHORT = {
  plan:         'Plan',
  requirements: 'Reqs',
  risk:         'Risk',
  design:       'Design',
  verify:       'Verify',
  release:      'Release',
  monitor:      'Monitor',
  retire:       'Retire',
}

// ── Hero geometry (720×170 viewBox) ──────────────────────────────────
// Used by Home.jsx VModelHero. Generous vertical depth (105px) so the
// V-shape reads strongly from across the room on landing.
export const V_NODES = [
  { id: 'plan',         label: 'Plan',         short: 'Plan',    x: 50,  y: 35  },
  { id: 'requirements', label: 'Requirements', short: 'Reqs',    x: 140, y: 70  },
  { id: 'risk',         label: 'Risk',         short: 'Risk',    x: 230, y: 105 },
  { id: 'design',       label: 'Design',       short: 'Design',  x: 320, y: 140 },
  { id: 'verify',       label: 'Verify',       short: 'Verify',  x: 400, y: 140 },
  { id: 'release',      label: 'Release',      short: 'Release', x: 490, y: 105 },
  { id: 'monitor',      label: 'Monitor',      short: 'Monitor', x: 580, y: 70  },
  { id: 'retire',       label: 'Retire',       short: 'Retire',  x: 670, y: 35  },
]

export const V_PATH = V_NODES.reduce(
  (acc, n, i) => acc + (i === 0 ? `M ${n.x},${n.y}` : ` L ${n.x},${n.y}`),
  '',
)

// ── Spine geometry (720×64 viewBox) ──────────────────────────────────
// Used by LifecycleStrip. Compresses the 105px depth → 32px so the V is
// still readable as a V but fits under the TopHeader without eating
// content area. Y values map linearly: 35→16, 140→48.
const SPINE_TOP = 16
const SPINE_DEPTH = 32  // 32px from top-row to apex
export const V_NODES_SPINE = V_NODES.map(n => ({
  ...n,
  y: SPINE_TOP + ((n.y - 35) / 105) * SPINE_DEPTH,
}))

export const V_PATH_SPINE = V_NODES_SPINE.reduce(
  (acc, n, i) => acc + (i === 0 ? `M ${n.x},${n.y}` : ` L ${n.x},${n.y}`),
  '',
)
