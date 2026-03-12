/**
 * EVOLV App Registry
 *
 * Each entry describes one "app" that can be opened as a tab
 * in the Platform Shell.  The `component` field is resolved
 * lazily in App.jsx to keep this file import-free.
 */

export const APPS = [
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
  {
    id:          'validation-factory',
    label:       'Validation Factory',
    icon:        '🏭',
    emoji:       '🏭',
    accentColor: '#32CD32',
    accentClass: 'lime',
    description: 'AI-powered GAMP 5 / CSA requirement generation, risk assessment, and test script automation.',
    closeable:   true,
    category:    'core',
    iframeUrl:   'http://localhost:8501',
    badge:       'EVOLV AI',
  },
  {
    id:          'navigator',
    label:       'Project Navigator',
    icon:        '🗺️',
    emoji:       '🗺️',
    accentColor: '#007FFF',
    accentClass: 'blue',
    description: 'GAMP 5 hierarchical project tree with Shadow Links, HITL badges, and Impact Heatmap.',
    closeable:   true,
    category:    'core',
    iframeUrl:   'http://localhost:8000/navigator',
  },
  {
    id:          'dev-portal',
    label:       'Dev Portal',
    icon:        '⚙️',
    emoji:       '⚙️',
    accentColor: '#007FFF',
    accentClass: 'blue',
    description: 'Interactive API docs, scoped API key management, webhook registry, and sandbox testing.',
    closeable:   true,
    category:    'developer',
  },
  {
    id:          'config',
    label:       'Config',
    icon:        '🔧',
    emoji:       '🔧',
    accentColor: '#64748b',
    accentClass: 'slate',
    description: 'Tenant nomenclature engine, site-specific compliance modes, and ABAC policy editor.',
    closeable:   true,
    category:    'admin',
  },
  {
    id:          'academy',
    label:       'Academy',
    icon:        '🎓',
    emoji:       '🎓',
    accentColor: '#a855f7',
    accentClass: 'purple',
    description: 'GAMP 5 guided walkthroughs, 21 CFR Part 11 training modules, and EVOLV certification paths.',
    closeable:   true,
    category:    'learning',
    badge:       'Coming Soon',
  },
]

export const APP_MAP = Object.fromEntries(APPS.map(a => [a.id, a]))

// Sidebar nav grouping
export const NAV_GROUPS = [
  {
    label: 'Platform',
    items: ['home', 'validation-factory', 'navigator'],
  },
  {
    label: 'Developer',
    items: ['dev-portal'],
  },
  {
    label: 'Administration',
    items: ['config'],
  },
  {
    label: 'Learning',
    items: ['academy'],
  },
]
