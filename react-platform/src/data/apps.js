/**
 * EVOLV App Registry
 *
 * Apps are organised into three navigation groups:
 *   LIFECYCLE   — the 8-phase V-model (Plan → Retire)
 *   INTELLIGENCE — cross-cutting insight tools
 *   TOOLS        — developer, admin, learning, docs
 *
 * `locked: true`   — phase not yet applicable (shown dim, non-clickable)
 * `iframeUrl`      — Streamlit page to embed; omitted for locked/native apps
 * `phase`          — query-param value sent to Streamlit (?page=<phase>)
 */

export const APPS = [
  // ── Core ──────────────────────────────────────────────────
  {
    id:          'home',
    label:       'Home',
    icon:        '⚡',
    emoji:       '⚡',
    accentColor: '#007FFF',
    accentClass: 'blue',
    description: 'LaunchPad — your command centre for the EVOLV platform.',
    closeable:   false,
    defaultOpen: true,
    category:    'core',
  },

  // ── Lifecycle: Phase 1 ────────────────────────────────────
  {
    id:          'plan',
    label:       'Plan',
    icon:        '📋',
    emoji:       '📋',
    accentColor: '#007FFF',
    accentClass: 'blue',
    description: 'Validation Planning — define project scope, VMP, '
               + 'system description, and GAMP 5 category.',
    closeable:   true,
    category:    'lifecycle',
    phase:       'plan',
    iframeUrl:   'http://localhost:8501/?page=plan&embedded=true',
  },

  // ── Lifecycle: Phase 2 ────────────────────────────────────
  {
    id:          'requirements',
    label:       'Requirements',
    icon:        '📝',
    emoji:       '📝',
    accentColor: '#007FFF',
    accentClass: 'blue',
    description: 'Requirements Hub — ingest vendor docs, generate '
               + 'GAMP 5 URS, and refine to SMART format.',
    closeable:   true,
    category:    'lifecycle',
    phase:       'requirements',
    iframeUrl:   'http://localhost:8501/?page=requirements&embedded=true',
    badge:       'EVOLV AI',
  },

  // ── Lifecycle: Phase 3 ────────────────────────────────────
  {
    id:          'risk',
    label:       'Risk',
    icon:        '⚖️',
    emoji:       '⚖️',
    accentColor: '#f59e0b',
    accentClass: 'amber',
    description: 'Risk & Gap — GAMP 5 / ICH Q9 risk assessment, '
               + 'FMEA scoring, and regulatory gap analysis.',
    closeable:   true,
    category:    'lifecycle',
    phase:       'risk',
    iframeUrl:   'http://localhost:8501/?page=risk&embedded=true',
  },

  // ── Lifecycle: Phase 4 ────────────────────────────────────
  {
    id:          'design',
    label:       'Design',
    icon:        '🎨',
    emoji:       '🎨',
    accentColor: '#a855f7',
    accentClass: 'purple',
    description: 'Design Specifications — SDS, HLD/LLD, traceability '
               + 'matrix, and configuration specification.',
    closeable:   true,
    category:    'lifecycle',
    phase:       'design',
  },

  // ── Lifecycle: Phase 5 ────────────────────────────────────
  {
    id:          'verify',
    label:       'Verify',
    icon:        '🏭',
    emoji:       '🏭',
    accentColor: '#32CD32',
    accentClass: 'lime',
    description: 'Execute CSA test scripts step-by-step with Pass/Fail '
               + 'recording, evidence upload, and 21 CFR Part 11 sign-off.',
    closeable:   true,
    category:    'lifecycle',
    phase:       'verify',
    badge:       'EVOLV AI',
  },

  // ── Lifecycle: Phase 6 ────────────────────────────────────
  {
    id:          'release',
    label:       'Release',
    icon:        '📄',
    emoji:       '📄',
    accentColor: '#32CD32',
    accentClass: 'lime',
    description: 'Release Gate — go-live checklist, multi-approver '
               + 'sign-off, and formal system release.',
    closeable:   true,
    category:    'lifecycle',
    phase:       'release',
  },

  // ── Lifecycle: Phase 7 ────────────────────────────────────
  {
    id:          'monitor',
    label:       'Monitor',
    icon:        '📡',
    emoji:       '📡',
    accentColor: '#007FFF',
    accentClass: 'blue',
    description: 'Operations — live audit trail viewer, deviation '
               + 'tracker, and system health dashboard.',
    closeable:   true,
    category:    'lifecycle',
    phase:       'monitor',
  },

  // ── Lifecycle: Phase 8 (locked — requires active project) ─
  {
    id:          'retire',
    label:       'Retire',
    icon:        '🔒',
    emoji:       '🔒',
    accentColor: '#64748b',
    accentClass: 'slate',
    description: 'Decommission — controlled retirement plan, data '
               + 'archival, and final validation assessment.',
    closeable:   true,
    category:    'lifecycle',
    locked:      true,
    lockedReason: 'Requires a project in active validated state.',
  },

  // ── Intelligence ──────────────────────────────────────────
  {
    id:          'governance',
    label:       'AI Governance',
    icon:        '🛡️',
    emoji:       '🛡️',
    accentColor: '#007FFF',
    accentClass: 'blue',
    description: 'Human-in-the-Loop oversight — AI decision queue, '
               + 'override ledger, audit timeline, and transparency reports.',
    closeable:   true,
    category:    'intelligence',
    badge:       'HITL',
  },
  {
    id:          'navigator',
    label:       'Project Navigator',
    icon:        '🗺️',
    emoji:       '🗺️',
    accentColor: '#007FFF',
    accentClass: 'blue',
    description: 'GAMP 5 hierarchical project tree with Shadow '
               + 'Links, HITL badges, and Impact Heatmap.',
    closeable:   true,
    category:    'intelligence',
    iframeUrl:   'http://localhost:8000/navigator',
  },
  {
    id:          'impact-analytics',
    label:       'Impact Analytics',
    icon:        '📊',
    emoji:       '📊',
    accentColor: '#32CD32',
    accentClass: 'lime',
    description: 'Legacy vs. EVOLV comparison reports, ROI metrics, '
               + 'and compliance impact dashboards.',
    closeable:   true,
    category:    'intelligence',
    badge:       'New',
  },

  // ── Tools ─────────────────────────────────────────────────
  {
    id:          'dev-portal',
    label:       'Dev Portal',
    icon:        '⚙️',
    emoji:       '⚙️',
    accentColor: '#007FFF',
    accentClass: 'blue',
    description: 'Interactive API docs, scoped API key management, '
               + 'webhook registry, and sandbox testing.',
    closeable:   true,
    category:    'tools',
  },
  {
    id:          'config',
    label:       'Config',
    icon:        '🔧',
    emoji:       '🔧',
    accentColor: '#64748b',
    accentClass: 'slate',
    description: 'Tenant nomenclature engine, site-specific '
               + 'compliance modes, and ABAC policy editor.',
    closeable:   true,
    category:    'tools',
  },
  {
    id:          'academy',
    label:       'Academy',
    icon:        '🎓',
    emoji:       '🎓',
    accentColor: '#a855f7',
    accentClass: 'purple',
    description: 'GAMP 5 guided walkthroughs, 21 CFR Part 11 '
               + 'training modules, and EVOLV certification paths.',
    closeable:   true,
    category:    'tools',
    badge:       'Beta',
  },
  {
    id:          'docs',
    label:       'Documentation',
    icon:        '📚',
    emoji:       '📚',
    accentColor: '#007FFF',
    accentClass: 'blue',
    description: 'Next-gen audit-ready documentation with Live-Sync '
               + 'version badges, GAMP 5 glossary, and Try-it demos.',
    closeable:   true,
    category:    'tools',
    badge:       'Live-Sync',
  },
]

export const APP_MAP = Object.fromEntries(APPS.map(a => [a.id, a]))

// Sidebar nav grouping — lifecycle-first
export const NAV_GROUPS = [
  {
    label: 'Lifecycle',
    items: [
      'plan', 'requirements', 'risk', 'design',
      'verify', 'release', 'monitor', 'retire',
    ],
  },
  {
    label: 'Intelligence',
    items: ['governance', 'navigator', 'impact-analytics'],
  },
  {
    label: 'Tools',
    items: ['dev-portal', 'config', 'academy', 'docs'],
  },
]
