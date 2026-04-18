/**
 * useAppStore — Zustand global store for the EVOLV Platform Shell.
 *
 * Responsibilities:
 *  - Tab management (open / close / switch, max 8 tabs, home pinned)
 *  - Draft state per app (text survives tab switches and re-opens)
 *  - Status badges per app (red/amber/green dot shown in Sidebar)
 *  - Phase completion tracking for the V-model lifecycle strip
 */
import { create }    from 'zustand'
import { persist }   from 'zustand/middleware'

const MAX_TABS = 8

// Initial status badges — demo data so the feature is visible on load
const INITIAL_BADGES = {
  'home':         null,
  'plan':         null,
  'requirements': { type: 'info',    label: 'Ready' },
  'risk':         { type: 'warning', label: '1 pending' },
  'design':       null,
  'verify':       null,
  'release':      null,
  'monitor':      { type: 'warning', label: '1 CR pending' },
  'retire':       null,
  'system-journey': { type: 'info',  label: 'New' },
  'portfolio':    { type: 'info',    label: 'New' },
  'governance':   { type: 'warning', label: '3 pending' },
  'navigator':    null,
  'dev-portal':   { type: 'success', label: 'Live' },
  'config':       null,
  'academy':      null,
  'impact-analytics': null,
  'docs':         null,
}

// Lifecycle phase order — used by LifecycleStrip
export const LIFECYCLE_PHASES = [
  'plan', 'requirements', 'risk', 'design',
  'verify', 'release', 'monitor', 'retire',
]

// ── Fresh project defaults ─────────────────────────────────────────
// Used when creating a new project or switching to one with no data yet.
const FRESH_PROJECT = {
  planData: {
    projectName: '', gampCategory: '', systemDescription: '',
    projectScope: '', regulatoryFrameworks: [], vmpCreated: false,
    vmpContent: {
      validationStrategy: '', resourcesResponsibilities: '', timeline: '',
    },
  },
  riskData:    {},
  requirements: [],
  testScripts:         {},
  testRuns:            {},
  activeRunId:         null,
  testBundles:         {},
  briefingAcknowledged: {},
  defects:             {},
  unscriptedSessions:  {},
  releaseData:  { approvals: [], released: false, releasedAt: null },
  designData: {
    architectureNotes: '', hldNotes: '', lldNotes: '',
    integrationNotes: '', diagramUrl: '', configItems: [],
  },
  phaseCompletion: {
    plan: false, requirements: false, risk: false, design: false,
    verify: false, release: false, monitor: false, retire: false,
  },
  statusBadges: {
    'home': null, 'plan': null, 'requirements': null, 'risk': null,
    'design': null, 'verify': null, 'release': null, 'monitor': null,
    'retire': null, 'system-journey': null, 'portfolio': null,
    'governance': null, 'navigator': null, 'dev-portal': null,
    'config': null, 'academy': null, 'impact-analytics': null,
    'docs': null,
  },
}

// Snapshot all phase-specific data from the flat store state
function extractProjectData(state) {
  return {
    planData:             state.planData,
    riskData:             state.riskData,
    requirements:         state.requirements,
    testScripts:          state.testScripts,
    testRuns:             state.testRuns,
    activeRunId:          state.activeRunId,
    testBundles:          state.testBundles,
    briefingAcknowledged: state.briefingAcknowledged,
    defects:              state.defects,
    unscriptedSessions:   state.unscriptedSessions,
    releaseData:          state.releaseData,
    designData:           state.designData,
    phaseCompletion:      state.phaseCompletion,
    statusBadges:         state.statusBadges,
  }
}

export const useAppStore = create(
persist(
(set, get) => ({
  // ── Tab state ──────────────────────────────────────────────
  tabs:        [{ appId: 'home' }],
  activeTabId: 'home',

  openTab: appId => set(state => {
    const exists = state.tabs.find(t => t.appId === appId)
    return {
      tabs: exists
        ? state.tabs
        : state.tabs.length >= MAX_TABS
          ? state.tabs
          : [...state.tabs, { appId }],
      activeTabId: appId,
    }
  }),

  closeTab: appId => set(state => {
    if (appId === 'home') return {}
    const idx  = state.tabs.findIndex(t => t.appId === appId)
    const next = state.tabs.filter(t => t.appId !== appId)
    const newActive =
      state.activeTabId === appId && next.length > 0
        ? next[Math.min(idx, next.length - 1)].appId
        : state.activeTabId
    return { tabs: next, activeTabId: newActive }
  }),

  switchTab: appId => set({ activeTabId: appId }),

  // ── Draft state ────────────────────────────────────────────
  // Per-app key-value bag.  Components read/write here so draft
  // survives tab switches, tab close+reopen, and Framer unmounts.
  drafts: {
    'academy':            { sandboxInput: '' },
    'verify': {},
    'dev-portal':         {},
  },

  setDraft: (appId, key, value) => set(state => ({
    drafts: {
      ...state.drafts,
      [appId]: { ...(state.drafts[appId] ?? {}), [key]: value },
    },
  })),

  getDraft: (appId, key, fallback = '') => {
    return get().drafts[appId]?.[key] ?? fallback
  },

  // ── Status badges ──────────────────────────────────────────
  // type: 'error' | 'warning' | 'success' | 'info'
  statusBadges: INITIAL_BADGES,

  setStatusBadge: (appId, badge) => set(state => ({
    statusBadges: { ...state.statusBadges, [appId]: badge },
  })),

  clearStatusBadge: appId => set(state => ({
    statusBadges: { ...state.statusBadges, [appId]: null },
  })),

  // ── Phase completion (V-model lifecycle strip) ─────────────
  // Tracks which lifecycle phases have been visited / have data.
  // Persisted in localStorage via zustand/middleware (future).
  phaseCompletion: {
    plan:         false,
    requirements: false,
    risk:         false,
    design:       false,
    verify:       false,
    release:      false,
    monitor:      false,
    retire:       false,
  },

  setPhaseComplete: phaseId => set(state => ({
    phaseCompletion: {
      ...state.phaseCompletion,
      [phaseId]: true,
    },
  })),

  resetPhaseCompletion: () => set({
    phaseCompletion: {
      plan: false, requirements: false, risk: false,
      design: false, verify: false, release: false,
      monitor: false, retire: false,
    },
  }),

  // ── Theme ──────────────────────────────────────────────────
  theme: 'dark',  // 'dark' | 'light'
  toggleTheme: () => set(state => ({
    theme: state.theme === 'dark' ? 'light' : 'dark',
  })),

  // ── Font size ──────────────────────────────────────────────
  // 'normal' | 'large' | 'xl'  — applied as zoom on app root
  fontSize: 'normal',
  cycleFontSize: () => set(state => ({
    fontSize:
      state.fontSize === 'normal' ? 'large'
      : state.fontSize === 'large' ? 'xl'
      : 'normal',
  })),

  // ── Plan data ──────────────────────────────────────────────
  planData: {
    projectName:      '',
    gampCategory:     '',
    systemDescription:'',
    projectScope:     '',
    regulatoryFrameworks: [],
    vmpCreated:       false,
    vmpContent: {
      validationStrategy:     '',
      resourcesResponsibilities: '',
      timeline:               '',
    },
  },
  setPlanData: (key, value) => set(state => ({
    planData: { ...state.planData, [key]: value },
  })),
  setPlanVmp: (key, value) => set(state => ({
    planData: {
      ...state.planData,
      vmpContent: { ...state.planData.vmpContent, [key]: value },
    },
  })),

  // ── Risk data ──────────────────────────────────────────────
  // keyed by requirement ID, each entry: { impact, implMethod, testAssurance }
  riskData: {},
  setRiskRow: (reqId, field, value) => set(state => ({
    riskData: {
      ...state.riskData,
      [reqId]: { ...(state.riskData[reqId] ?? {}), [field]: value },
    },
  })),

  // ── Test scripts & runs ────────────────────────────────────
  // testScripts: keyed by script_id (shape = DeltaAgent output)
  // testRuns:    keyed by runId — execution state per script
  testScripts: {},
  testRuns:    {},
  activeRunId: null,

  setTestScript: (scriptId, script) => set(state => ({
    testScripts: { ...state.testScripts, [scriptId]: script },
  })),

  // Create a fresh TestRun from a TestScript (idempotent —
  // if an in-progress run already exists for this script, reuse it).
  initTestRun: script => set(state => {
    const existingRun = Object.values(state.testRuns)
      .find(r => r.scriptId === script.script_id
              && r.status !== 'locked')
    if (existingRun) return { activeRunId: existingRun.runId }

    const ts    = new Date().toISOString()
      .replace(/[:.]/g, '').slice(0, 15)
    const runId = `RUN-${script.script_id}-${ts}`
    const stepResults = {}
    ;(script.steps ?? []).forEach(step => {
      const key = `${step.step_number}_${step.step_type}`
      stepResults[key] = {
        verdict: null, actualResult: '', testerName: '',
        executedAt: null, evidence: null,
      }
    })
    const newRun = {
      runId,
      scriptId:       script.script_id,
      startedAt:      new Date().toISOString(),
      status:         'in_progress',
      lockedAt:       null,
      signerName:     '',
      signingMeaning: 'Approval of Test Execution',
      reasoningHash:  null,
      stepResults,
    }
    return {
      testRuns:    { ...state.testRuns, [runId]: newRun },
      activeRunId: runId,
    }
  }),

  setStepResult: (runId, stepKey, field, value) => set(state => {
    const run = state.testRuns[runId]
    if (!run || run.status === 'locked') return {}
    return {
      testRuns: {
        ...state.testRuns,
        [runId]: {
          ...run,
          stepResults: {
            ...run.stepResults,
            [stepKey]: {
              ...(run.stepResults[stepKey] ?? {}),
              [field]: value,
            },
          },
        },
      },
    }
  }),

  setRunMeta: (runId, field, value) => set(state => {
    const run = state.testRuns[runId]
    if (!run || run.status === 'locked') return {}
    return {
      testRuns: {
        ...state.testRuns,
        [runId]: { ...run, [field]: value },
      },
    }
  }),

  lockTestRun: (runId, reasoningHash) => set(state => {
    const run = state.testRuns[runId]
    if (!run) return {}
    return {
      testRuns: {
        ...state.testRuns,
        [runId]: {
          ...run,
          status:        'locked',
          lockedAt:      new Date().toISOString(),
          reasoningHash: reasoningHash ?? null,
        },
      },
    }
  }),

  // ── Test Bundles (Sprint 14 — Test Authoring) ──────────────────
  // testBundles: keyed by requirement_id (e.g. 'UR-1')
  // Shape per entry: full bundle dict from
  // POST /test-authoring/generate (bundle_id, depth, mode,
  // risk_level, steps[], bundle_citations[], quality_checklist).
  testBundles: {},

  setTestBundle: (reqId, bundle) => set(state => ({
    testBundles: { ...state.testBundles, [reqId]: bundle },
  })),

  removeTestBundle: reqId => set(state => {
    const { [reqId]: _, ...rest } = state.testBundles
    return { testBundles: rest }
  }),

  clearTestBundles: () => set({ testBundles: {} }),

  // Promote a bundle to a runnable testScript (so Verify can
  // load it via the existing testScripts/initTestRun pipeline).
  promoteBundleToScript: reqId => set(state => {
    const bundle = state.testBundles[reqId]
    if (!bundle) return {}
    // Strip authoring-only fields, keep the executable shape.
    const script = {
      script_id:               bundle.bundle_id,
      urs_id:                  bundle.requirement_id,
      ur_id:                   bundle.requirement_id,
      test_type:               bundle.test_type,
      risk_level:              bundle.risk_level,
      test_strategy:           bundle.depth,
      regulatory_justification: (bundle.bundle_citations ?? [])
        .map(c => `${c.regulation} ${c.section}: ${c.rationale}`)
        .join('\n\n'),
      generated_at:            bundle.generated_at,
      steps:                   bundle.steps,
      quality_checklist:       bundle.quality_checklist,
      depth:                   bundle.depth,
      mode:                    bundle.mode,
      requirement_summary:     bundle.requirement_summary,
    }
    return {
      testScripts: {
        ...state.testScripts,
        [script.script_id]: script,
      },
    }
  }),

  // ── Briefing config ────────────────────────────────────────────
  // risk-level defaults + per-script overrides set by test leads
  briefingConfig: {
    defaults: {
      High: [
        'I have read and understood the test script and all acceptance criteria.',
        'The test environment matches the validated configuration baseline.',
        'All required test data, accounts, and prerequisites are confirmed.',
        'I am authorised to execute this test per the Validation Master Plan.',
        'I understand this is a HIGH RISK test — all steps require recorded actual results.',
      ],
      Medium: [
        'I confirm the test environment is ready and I am prepared to execute this exploratory charter session.',
      ],
      Low: null,
    },
    overrides: {},
  },

  setBriefingOverride: (scriptId, items) => set(state => ({
    briefingConfig: {
      ...state.briefingConfig,
      overrides: {
        ...state.briefingConfig.overrides,
        [scriptId]: { items, editedAt: new Date().toISOString() },
      },
    },
  })),

  // ── Briefing acknowledgement (per run) ─────────────────────────
  briefingAcknowledged: {},
  setBriefingAcknowledged: (runId, data) => set(state => ({
    briefingAcknowledged: {
      ...state.briefingAcknowledged,
      [runId]: data,
    },
  })),

  // ── Defects (per run) ──────────────────────────────────────────
  // [{ id, stepKey, severity, description, assignee,
  //    fixDate, frRef, screenshotName, createdAt }]
  defects: {},
  addDefect: (runId, defect) => set(state => ({
    defects: {
      ...state.defects,
      [runId]: [...(state.defects[runId] ?? []), defect],
    },
  })),
  updateDefect: (runId, defectId, updates) => set(state => ({
    defects: {
      ...state.defects,
      [runId]: (state.defects[runId] ?? []).map(d =>
        d.id === defectId ? { ...d, ...updates } : d
      ),
    },
  })),

  // ── Unscripted charter sessions (per run) ─────────────────────
  // { startedAt, notes:[{timestamp,text}], findings:[...], verdict }
  unscriptedSessions: {},
  initUnscriptedSession: runId => set(state => {
    if (state.unscriptedSessions[runId]) return {}
    return {
      unscriptedSessions: {
        ...state.unscriptedSessions,
        [runId]: {
          startedAt: new Date().toISOString(),
          notes:     [],
          findings:  [],
          verdict:   null,
        },
      },
    }
  }),
  addSessionNote: (runId, text) => set(state => {
    const s = state.unscriptedSessions[runId]
    if (!s) return {}
    return {
      unscriptedSessions: {
        ...state.unscriptedSessions,
        [runId]: {
          ...s,
          notes: [
            ...s.notes,
            { timestamp: new Date().toISOString(), text },
          ],
        },
      },
    }
  }),
  addSessionFinding: (runId, finding) => set(state => {
    const s = state.unscriptedSessions[runId]
    if (!s) return {}
    return {
      unscriptedSessions: {
        ...state.unscriptedSessions,
        [runId]: { ...s, findings: [...s.findings, finding] },
      },
    }
  }),
  setSessionVerdict: (runId, verdict) => set(state => {
    const s = state.unscriptedSessions[runId]
    if (!s) return {}
    return {
      unscriptedSessions: {
        ...state.unscriptedSessions,
        [runId]: { ...s, verdict },
      },
    }
  }),

  // ── User profile ───────────────────────────────────────────────
  userProfile: {
    name: '',
    role: '',
    org:  '',
  },
  setUserProfile: (key, value) => set(state => ({
    userProfile: { ...state.userProfile, [key]: value },
  })),

  // ── Design data ────────────────────────────────────────────────
  designData: {
    architectureNotes: '',
    hldNotes:          '',
    lldNotes:          '',
    integrationNotes:  '',
    diagramUrl:        '',
    configItems:       [],   // [{ item, system, parameter, value, rationale }]
  },
  setDesignField: (key, value) => set(state => ({
    designData: { ...state.designData, [key]: value },
  })),
  addConfigItem: item => set(state => ({
    designData: {
      ...state.designData,
      configItems: [...state.designData.configItems, item],
    },
  })),
  removeConfigItem: idx => set(state => ({
    designData: {
      ...state.designData,
      configItems: state.designData.configItems.filter((_, i) => i !== idx),
    },
  })),

  // ── AI Governance queue (local, for AI model change decisions) ─
  // Items added by AIModelsTab when HIGH/MEDIUM risk changes are submitted.
  // Read by Governance.jsx and merged with API decisions.
  aiGovernanceQueue: [],
  addAIGovernanceItem: item => set(state => ({
    aiGovernanceQueue: [item, ...state.aiGovernanceQueue],
  })),
  updateAIGovernanceItem: (id, updates) => set(state => ({
    aiGovernanceQueue: state.aiGovernanceQueue.map(i =>
      i.id === id ? { ...i, ...updates } : i
    ),
  })),

  // ── Custom (user-classified) systems ──────────────────────────
  // Systems added via the GxP Classification Questionnaire in Dev Portal.
  // Merged with the built-in SYSTEMS registry for Portfolio and CR lookup.
  customSystems: [],
  addCustomSystem: system => set(state => ({
    customSystems: [
      ...state.customSystems.filter(s => s.id !== system.id),
      system,
    ],
  })),

  // ── Custom regulations (user-added via Regulatory Watch) ──────
  customRegulations: [],
  addCustomRegulation: reg => set(state => ({
    customRegulations: [
      ...state.customRegulations.filter(r => r.id !== reg.id),
      reg,
    ],
  })),
  deleteCustomRegulation: id => set(state => ({
    customRegulations: state.customRegulations.filter(r => r.id !== id),
  })),

  // ── Data bridge metadata ───────────────────────────────────────
  // Updated by useDataBridge whenever FastAPI returns fresh data.
  bridgeMeta: { reqCount: 0, reqSyncAt: null },
  setBridgeMeta: meta => set(state => ({
    bridgeMeta: { ...state.bridgeMeta, ...meta },
  })),

  // ── Requirements (from Streamlit data bridge) ──────────────────
  // Flat list of { id, type, statement, parentId?, urs_id?,
  //   risk_assessment?, implementation_method?, risk_level?,
  //   test_strategy? } rows. Empty = use Risk.jsx seed data.
  requirements: [],

  setRequirements: reqs => set({ requirements: reqs ?? [] }),

  clearRequirements: () => set({ requirements: [] }),

  // ── Release data ───────────────────────────────────────────────
  // approvals: list of signed approval objects
  // released:  true once formally released
  releaseData: {
    approvals:  [],
    released:   false,
    releasedAt: null,
  },

  addApproval: approval => set(state => ({
    releaseData: {
      ...state.releaseData,
      approvals: [...state.releaseData.approvals, approval],
    },
  })),

  setReleased: () => set(state => ({
    releaseData: {
      ...state.releaseData,
      released:   true,
      releasedAt: new Date().toISOString(),
    },
  })),

  // ── Project management ─────────────────────────────────────────
  // `projects` is keyed by projectId. Each entry holds metadata and
  // a `data` snapshot (null for the currently active project — its
  // live data is always in the flat store fields above).
  // On switch: snapshot current flat state → projects[current].data,
  //            then spread target.data back into the flat store.
  projects: {
    'proj-default': {
      id:        'proj-default',
      name:      'Default Project',
      createdAt: new Date().toISOString(),
      data:      null,
    },
  },
  activeProjectId: 'proj-default',

  createProject: name => set(state => {
    const id = `proj-${Date.now()}`
    return {
      projects: {
        ...state.projects,
        // Snapshot current project before leaving it
        [state.activeProjectId]: {
          ...state.projects[state.activeProjectId],
          data: extractProjectData(state),
        },
        [id]: { id, name, createdAt: new Date().toISOString(), data: null },
      },
      activeProjectId: id,
      // Reset flat store to a fresh project
      ...FRESH_PROJECT,
      planData: { ...FRESH_PROJECT.planData, projectName: name },
    }
  }),

  switchProject: projectId => set(state => {
    if (projectId === state.activeProjectId) return {}
    const proj   = state.projects[projectId]
    const target = proj?.data ?? {
      ...FRESH_PROJECT,
      planData: { ...FRESH_PROJECT.planData, projectName: proj?.name ?? '' },
    }
    return {
      projects: {
        ...state.projects,
        [state.activeProjectId]: {
          ...state.projects[state.activeProjectId],
          data: extractProjectData(state),
        },
      },
      activeProjectId: projectId,
      ...target,
    }
  }),

  deleteProject: projectId => set(state => {
    if (projectId === state.activeProjectId) return {}
    if (Object.keys(state.projects).length <= 1) return {}
    const { [projectId]: _, ...rest } = state.projects
    return { projects: rest }
  }),
}),
{
  name: 'evolv-platform',
  // Only persist data that should survive browser refresh.
  // Tabs and activeTabId intentionally reset on reload.
  partialize: state => ({
    theme:           state.theme,
    fontSize:        state.fontSize,
    phaseCompletion: state.phaseCompletion,
    planData:        state.planData,
    riskData:        state.riskData,
    testScripts:          state.testScripts,
    testRuns:             state.testRuns,
    activeRunId:          state.activeRunId,
    testBundles:          state.testBundles,
    briefingConfig:       state.briefingConfig,
    briefingAcknowledged: state.briefingAcknowledged,
    defects:              state.defects,
    unscriptedSessions:   state.unscriptedSessions,
    releaseData:          state.releaseData,
    requirements:         state.requirements,
    designData:           state.designData,
    userProfile:          state.userProfile,
    projects:             state.projects,
    activeProjectId:      state.activeProjectId,
    customSystems:        state.customSystems,
    customRegulations:    state.customRegulations,
    aiGovernanceQueue:    state.aiGovernanceQueue,
  }),
}
))

if (typeof window !== 'undefined' && import.meta.env.DEV) {
  window.useAppStore = useAppStore
}
