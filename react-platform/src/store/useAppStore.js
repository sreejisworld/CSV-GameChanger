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
import { buildDemoProject,
         DEMO_PROJECT_META } from '../data/demoProject.js'

const MAX_TABS = 8

// Recompute the 5-point quality checklist for a bundle's steps.
// Mirrors the checks used by the Python test_authoring_engine so
// manually authored bundles are scored the same way.
function _recomputeQuality(steps) {
  const exec = steps.filter(s => s.step_type === 'Execution')
  const nonEmpty = s => Boolean((s ?? '').toString().trim())
  const titles = steps.map(s => (s.step_title ?? '').trim())
    .filter(Boolean)
  return {
    all_steps_have_instructions:
      steps.length > 0
        && steps.every(s => nonEmpty(s.step_instruction)),
    execution_steps_have_expected_results:
      exec.length > 0
        && exec.every(s => nonEmpty(s.expected_result)),
    execution_steps_have_references:
      exec.length > 0
        && exec.every(s => nonEmpty(s.requirement_reference)),
    all_execution_steps_carry_citations:
      exec.length > 0
        && exec.every(s => (s.citations ?? []).length > 0),
    step_titles_unique:
      new Set(titles).size === titles.length,
  }
}

// Initial status badges — demo data so the feature is visible on load
const INITIAL_BADGES = {
  'home':         null,
  'plan':         null,
  'requirements': { type: 'info',    label: 'Ready' },
  // Risk badge is computed live from requirements/riskData
  // (see setRiskRow + the Risk-badge effect in App.jsx) — start clean
  // so we don't show stale "pending" counts before any UR exists.
  'risk':         null,
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
  qaReviews:           {},
  releaseData:  { approvals: [], released: false, releasedAt: null },
  retireData:   { checklist: {}, notes: '',
                   decommissionedAt: null,
                   decommissionedBy: '' },
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
    qaReviews:            state.qaReviews,
    releaseData:          state.releaseData,
    retireData:           state.retireData,
    designData:           state.designData,
    phaseCompletion:      state.phaseCompletion,
    statusBadges:         state.statusBadges,
    changeRecords:        state.changeRecords,
    validatedState:       state.validatedState,
    regulatoryDrift:      state.regulatoryDrift,
  }
}

export const useAppStore = create(
persist(
(set, get) => ({
  // ── Tab state ──────────────────────────────────────────────
  tabs:        [{ appId: 'home' }],
  activeTabId: 'home',

  // Sprint 31.2 — track last-opened apps for the Cmd+K "Recent"
  // section. FIFO, deduped, capped at 5. Home is excluded (it's
  // always pinned, so it never feels like a "recently visited"
  // item to the user).
  recentApps: [],

  openTab: appId => set(state => {
    const exists = state.tabs.find(t => t.appId === appId)
    const nextRecent = appId === 'home'
      ? state.recentApps
      : [appId, ...state.recentApps.filter(id => id !== appId)].slice(0, 5)
    return {
      tabs: exists
        ? state.tabs
        : state.tabs.length >= MAX_TABS
          ? state.tabs
          : [...state.tabs, { appId }],
      activeTabId: appId,
      recentApps: nextRecent,
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

  // ── Theme (Sprint 29 — single light theme) ────────────────
  // Sprint 29 deleted dark mode in favour of a single warm-off-white
  // palette inspired by Claude.ai. Pharma QA/validation pros at the
  // April 2026 demos consistently asked for a lighter UI for long
  // audit sessions, and 2026 users are most familiar with AI-tool-
  // style warm neutrals (Claude, ChatGPT).
  //
  // `toggleTheme` is kept as a public action for backward compatibility
  // — any old caller (e.g. a stale TopHeader.jsx import on disk) becomes
  // a harmless no-op that re-asserts light. Persisted `theme: 'dark'`
  // from pre-Sprint-29 stores is healed to 'light' on next mutation.
  theme: 'light',
  toggleTheme: () => set({ theme: 'light' }),

  // ── Font size ──────────────────────────────────────────────
  // 'normal' | 'large' | 'xl'  — applied as zoom on app root
  fontSize: 'normal',
  cycleFontSize: () => set(state => ({
    fontSize:
      state.fontSize === 'normal' ? 'large'
      : state.fontSize === 'large' ? 'xl'
      : 'normal',
  })),

  // ── Sidebar nav-group collapse (Sprint 30 + 35.5 revision) ────
  // Sprint 30 (April demos): pharma QA pros said the sidebar felt
  // busy. Original fix collapsed Intelligence + Tools by default so
  // first paint showed only the 8 lifecycle phases.
  //
  // Sprint 35.5 revision: Traceability Matrix (the flagship audit-
  // readiness artefact, Sprint 28) ended up hidden behind the
  // Intelligence chevron — pharma QA leads who walked the platform
  // in pre-launch validation kept asking "where's traceability?"
  // Intelligence is now default-EXPANDED (7 apps visible) so the
  // Living Traceability Matrix, Portfolio, Audit Trail and the
  // other read-side dashboards land in first paint. Tools stays
  // collapsed (admin/secondary surfaces — Dev Portal, Config,
  // Academy, Docs — none of which a QA lead needs in first 30s).
  //
  // State is still persisted (zustand partialize) so the user's
  // own collapse/expand choices survive reload.
  navGroupsCollapsed: {
    Lifecycle:    false,
    Intelligence: false,
    Tools:        true,
  },
  toggleNavGroup: label => set(state => ({
    navGroupsCollapsed: {
      ...state.navGroupsCollapsed,
      [label]: !state.navGroupsCollapsed?.[label],
    },
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
  setRiskRow: (reqId, field, value) => set(state => {
    const nextRiskData = {
      ...state.riskData,
      [reqId]: { ...(state.riskData[reqId] ?? {}), [field]: value },
    }
    // Recompute the Risk sidebar badge so it reflects live state
    // rather than the stale "1 pending" demo seed.
    const urs = (state.requirements ?? []).filter(
      r => (r.type ?? 'UR') === 'UR',
    )
    const ranked = urs.filter(u => {
      const row = nextRiskData[u.id]
      return row && row.impact && row.implMethod
    }).length
    const pending = urs.length - ranked
    let nextRiskBadge
    if (urs.length === 0) {
      nextRiskBadge = null
    } else if (pending === 0) {
      nextRiskBadge = { type: 'success', label: 'All ranked' }
    } else {
      nextRiskBadge = {
        type: 'warning',
        label: `${pending} pending`,
      }
    }
    return {
      riskData: nextRiskData,
      statusBadges: { ...state.statusBadges, risk: nextRiskBadge },
    }
  }),

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

  // ── Adhoc step insertion during execution (Sprint 15.2) ────────
  // Inserts a tester-authored step into a TestScript mid-run.
  // The step is tagged source='tester-adhoc' so ALCOA report and
  // exports can distinguish it from AI-generated / authored steps.
  // Numbering is hierarchical (e.g. 3.1, 3.2 after step 3) so that
  // the original step_number keys for prior results stay stable.
  insertAdhocStep: (scriptId, runId, afterStepKey, draft) =>
    set(state => {
      const script = state.testScripts[scriptId]
      if (!script) return {}
      const run = runId ? state.testRuns[runId] : null
      if (run && run.status === 'locked') return {}

      const idx = (script.steps ?? []).findIndex(
        s => `${s.step_number}_${s.step_type}` === afterStepKey,
      )
      if (idx === -1) return {}
      const prev = script.steps[idx]

      // Hierarchical numbering: count siblings already inserted
      // under the same prefix so 3.1, 3.2, 3.3 stay monotonic.
      const prefix = String(prev.step_number).split('.')[0]
      const siblings = (script.steps ?? []).filter(
        s => s.step_type === 'Execution'
          && String(s.step_number).startsWith(`${prefix}.`),
      )
      const newNumber = `${prefix}.${siblings.length + 1}`

      const newStep = {
        step_type:             'Execution',
        step_number:           newNumber,
        step_title:            draft.stepTitle ?? '',
        step_instruction:      draft.instruction ?? '',
        expected_result:       draft.expectedResult ?? '',
        test_case_type:        draft.testCaseType ?? 'Positive',
        requirement_reference: draft.frRef ?? '',
        archetype:             'tester-adhoc',
        citations:             [],
        source:                'tester-adhoc',
        inserted_at:           new Date().toISOString(),
        inserted_by:           draft.testerName ?? '',
        adhoc_reason:          draft.reason ?? '',
      }

      // Place new step after the trigger + any earlier siblings
      // (keeps adhoc steps clustered right after their parent).
      const insertAt = idx + 1 + siblings.length
      const newSteps = [
        ...script.steps.slice(0, insertAt),
        newStep,
        ...script.steps.slice(insertAt),
      ]

      // Seed an empty stepResults entry on the active run.
      const newKey = `${newNumber}_Execution`
      const updatedRun = run ? {
        ...run,
        stepResults: {
          ...run.stepResults,
          [newKey]: {
            verdict:      null,
            actualResult: '',
            testerName:   draft.testerName ?? '',
            executedAt:   null,
            evidence:     null,
          },
        },
      } : null

      return {
        testScripts: {
          ...state.testScripts,
          [scriptId]: { ...script, steps: newSteps },
        },
        ...(updatedRun ? {
          testRuns: { ...state.testRuns, [runId]: updatedRun },
        } : {}),
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

  // ── Manual-authoring actions (Sprint 15) ───────────────────────
  // Create an empty bundle skeleton for manual authoring.
  // Mirrors the shape returned by POST /test-authoring/generate
  // so the rest of the pipeline (preview, promote) is unchanged.
  createManualBundle: (reqId, { riskLevel, testType,
                                 requirementSummary,
                                 projectName }) => set(state => {
    if (state.testBundles[reqId]) return {}  // idempotent
    const bundle = {
      bundle_id:            `TB-${reqId}`,
      requirement_id:       reqId,
      requirement_summary:  requirementSummary ?? '',
      project_name:         projectName ?? 'Untitled Project',
      impact:               '',
      implementation_method:'',
      risk_level:           riskLevel ?? 'Low',
      depth:                'manual',
      test_type:            testType ?? 'Informal',
      mode:                 'manual',
      enrichment_applied:   false,
      source:               'manual',
      generated_at:         new Date().toISOString(),
      steps:                [],
      bundle_citations:     [],
      quality_checklist: {
        all_steps_have_instructions:        false,
        execution_steps_have_expected_results: false,
        execution_steps_have_references:    false,
        all_execution_steps_carry_citations: false,
        step_titles_unique:                 true,
      },
      schema_version:       '1.0.0',
    }
    return {
      testBundles: { ...state.testBundles, [reqId]: bundle },
    }
  }),

  // Append a step to a bundle (manual or AI-generated).
  // stepType = 'Setup' | 'Execution'; archetype is optional.
  addBundleStep: (reqId, { stepType, archetype } = {}) =>
    set(state => {
      const bundle = state.testBundles[reqId]
      if (!bundle) return {}
      const type = stepType || 'Execution'
      const arch = archetype
        || (type === 'Setup' ? 'setup' : 'positive')
      const sameType = bundle.steps.filter(s => s.step_type === type)
      const next = {
        step_type:             type,
        step_number:           sameType.length + 1,
        step_title:            '',
        step_instruction:      '',
        expected_result:       type === 'Execution' ? '' : '',
        archetype:             arch,
        requirement_reference: '',
        citations:             [],
        source:                'manual',
      }
      const steps = [...bundle.steps, next]
      return {
        testBundles: {
          ...state.testBundles,
          [reqId]: {
            ...bundle,
            steps,
            quality_checklist:
              _recomputeQuality(steps),
          },
        },
      }
    }),

  // Update a single field on a step (by absolute index in bundle.steps).
  updateBundleStep: (reqId, stepIdx, field, value) => set(state => {
    const bundle = state.testBundles[reqId]
    if (!bundle || !bundle.steps[stepIdx]) return {}
    const steps = bundle.steps.map((s, i) =>
      i === stepIdx ? { ...s, [field]: value } : s,
    )
    return {
      testBundles: {
        ...state.testBundles,
        [reqId]: {
          ...bundle,
          steps,
          quality_checklist: _recomputeQuality(steps),
        },
      },
    }
  }),

  // Remove a step by absolute index; re-numbers within its type.
  removeBundleStep: (reqId, stepIdx) => set(state => {
    const bundle = state.testBundles[reqId]
    if (!bundle || !bundle.steps[stepIdx]) return {}
    const filtered = bundle.steps.filter((_, i) => i !== stepIdx)
    const counters = { Setup: 0, Execution: 0 }
    const steps = filtered.map(s => ({
      ...s,
      step_number: ++counters[s.step_type],
    }))
    return {
      testBundles: {
        ...state.testBundles,
        [reqId]: {
          ...bundle,
          steps,
          quality_checklist: _recomputeQuality(steps),
        },
      },
    }
  }),

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

  // ── QA Review (Sprint 15.4 — pre-lock review screen) ──────────
  // Per-run reviewer record built before electronic sign-off.
  // Shape per entry:
  //   {
  //     reviewerName, comments,
  //     checks: { actualResultsComplete, defectsLogged,
  //               evidenceAttached, adhocStepsJustified },
  //     reviewedAt: ISO|null
  //   }
  // We deliberately do NOT lock anything here — the sign-off
  // panel still owns the legal lock. This screen exists so a QA
  // lead can attest "I reviewed the failed steps + defects + adhoc
  // inserts" before the executor signs.
  qaReviews: {},

  setQaReview: (runId, field, value) => set(state => {
    if (!runId) return {}
    const prev = state.qaReviews[runId] ?? {
      reviewerName: '',
      comments:     '',
      checks: {
        actualResultsComplete: false,
        defectsLogged:         false,
        evidenceAttached:      false,
        adhocStepsJustified:   false,
      },
      reviewedAt:   null,
    }
    return {
      qaReviews: {
        ...state.qaReviews,
        [runId]: { ...prev, [field]: value },
      },
    }
  }),

  setQaReviewCheck: (runId, checkKey, value) => set(state => {
    if (!runId) return {}
    const prev = state.qaReviews[runId] ?? {
      reviewerName: '',
      comments:     '',
      checks: {
        actualResultsComplete: false,
        defectsLogged:         false,
        evidenceAttached:      false,
        adhocStepsJustified:   false,
      },
      reviewedAt:   null,
    }
    return {
      qaReviews: {
        ...state.qaReviews,
        [runId]: {
          ...prev,
          checks: { ...prev.checks, [checkKey]: value },
        },
      },
    }
  }),

  markQaReviewSigned: runId => set(state => {
    const prev = state.qaReviews[runId]
    if (!prev) return {}
    return {
      qaReviews: {
        ...state.qaReviews,
        [runId]: { ...prev, reviewedAt: new Date().toISOString() },
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

  // ── Manual-authoring CRUD (Sprint 17.6) ────────────────────────
  // Hand-typed entry path. Auto-generates a globally-unique id of
  // the form `UR-N` / `FR-N` by scanning existing rows so it never
  // collides with workshop-generated rows (which already use the
  // backend `_flatten_batch` numbering scheme).
  //
  // :requirement: URS-23.1 (manual authoring extends to URs/FRs)
  addRequirement: req => set(state => {
    const type = req?.type ?? 'UR'
    const prefix = type === 'FR' ? 'FR' : 'UR'
    const usedNums = new Set(
      state.requirements
        .filter(r => r.type === type)
        .map(r => {
          const m = String(r.id ?? '').match(/^(?:UR|FR)-(\d+)$/i)
          return m ? Number(m[1]) : NaN
        })
        .filter(n => Number.isFinite(n))
    )
    let n = 1
    while (usedNums.has(n)) n += 1
    const id = `${prefix}-${n}`
    const newReq = {
      id,
      type,
      statement: req?.statement ?? '',
      parentId:  req?.parentId ?? null,
      ...req,
      // Force the canonical id/type AFTER spread so caller can't
      // smuggle a duplicate id in.
      id,
      type,
    }
    return { requirements: [...state.requirements, newReq] }
  }),

  removeRequirement: id => set(state => {
    const remaining = state.requirements.filter(r => r.id !== id)
    // Also clear orphaned FRs whose parent UR is being removed —
    // otherwise the table renders dangling rows with broken parent
    // references and the AI Sidekick chips reference a stale id.
    const removed = state.requirements.find(r => r.id === id)
    const finalReqs = removed?.type === 'UR'
      ? remaining.filter(r => r.parentId !== id)
      : remaining
    // Drop any meta entries for ids that no longer exist
    const keepIds = new Set(finalReqs.map(r => r.id))
    const nextMeta = {}
    for (const [metaId, m] of Object.entries(state.requirementMeta)) {
      if (keepIds.has(metaId)) nextMeta[metaId] = m
    }
    return { requirements: finalReqs, requirementMeta: nextMeta }
  }),

  updateRequirementStatement: (id, statement) => set(state => ({
    requirements: state.requirements.map(r =>
      r.id === id ? { ...r, statement } : r
    ),
  })),

  // ── Requirement metadata (Sprint 17.2 / 17.3) ──────────────────
  // Per-requirement editor state, keyed by requirement id.
  // Schema: { capability, condition, constraint,
  //           requirement_type ('Functional' | 'Non-Functional'),
  //           stakeholder ('Senior Mgmt' | 'Lab' | 'IT' | 'QA/ITQA'
  //                       | 'Procurement' | 'Supplier' | 'Data Owner'),
  //           override_justification }
  // Survives FastAPI re-syncs of the `requirements` list because it
  // lives in its own slice keyed by id (same pattern as riskData).
  requirementMeta: {},

  setRequirementMeta: (id, field, value) => set(state => ({
    requirementMeta: {
      ...state.requirementMeta,
      [id]: {
        ...(state.requirementMeta[id] ?? {}),
        [field]: value,
      },
    },
  })),

  bulkSetRequirementMeta: (id, patch) => set(state => ({
    requirementMeta: {
      ...state.requirementMeta,
      [id]: { ...(state.requirementMeta[id] ?? {}), ...patch },
    },
  })),

  clearRequirementMeta: () => set({ requirementMeta: {} }),

  // ── SMART refinements (Sprint 17.7) ────────────────────────────
  // Cache of POST /requirements/refine-smart responses keyed by req
  // id, plus per-row UI state (loading | error | suggestion). Lives
  // outside requirementMeta so applying a suggestion can patch
  // capability/condition/constraint without colliding with the user's
  // hand-typed values.
  //
  // Schema per row id:
  //   { status:   'idle'|'loading'|'ready'|'error',
  //     error:    string | null,
  //     suggestion: {
  //       original, smart_text, risk_level, fda_ema_flags,
  //       acceptance_criteria, negative_test_scenario,
  //       engine_mode, refined_at,
  //     } | null }
  //
  // Deliberately NOT persisted — refinements are advisory, ephemeral,
  // and cheap to regenerate. Persisting would risk showing stale
  // suggestions after the user edits the row.
  requirementRefinements: {},

  setRefinementLoading: id => set(state => ({
    requirementRefinements: {
      ...state.requirementRefinements,
      [id]: {
        ...(state.requirementRefinements[id] ?? {}),
        status: 'loading', error: null,
      },
    },
  })),

  setRefinementSuggestion: (id, suggestion) => set(state => ({
    requirementRefinements: {
      ...state.requirementRefinements,
      [id]: { status: 'ready', error: null, suggestion },
    },
  })),

  setRefinementError: (id, error) => set(state => ({
    requirementRefinements: {
      ...state.requirementRefinements,
      [id]: {
        ...(state.requirementRefinements[id] ?? {}),
        status: 'error',
        error: String(error ?? 'Refinement failed'),
      },
    },
  })),

  clearRefinement: id => set(state => {
    const next = { ...state.requirementRefinements }
    delete next[id]
    return { requirementRefinements: next }
  }),

  // Apply a cached SMART suggestion back into the row.
  //
  //  - statement  ← smart_text  (so the canonical text reflects the
  //                              accepted rewrite for downstream sync)
  //  - capability ← smart_text  (so the 3 Cs editor cell stays the
  //                              source of truth the user can refine)
  //
  // Condition / constraint are intentionally left alone — the user
  // may have already typed measurable values there and the SMART
  // engine's section split is heuristic.
  applyRefinementSuggestion: id => set(state => {
    const entry = state.requirementRefinements[id]
    const suggestion = entry?.suggestion
    if (!suggestion?.smart_text) return state

    const text = suggestion.smart_text
    const nextRefinements = { ...state.requirementRefinements }
    delete nextRefinements[id]

    return {
      requirements: state.requirements.map(r =>
        r.id === id ? { ...r, statement: text } : r
      ),
      requirementMeta: {
        ...state.requirementMeta,
        [id]: {
          ...(state.requirementMeta[id] ?? {}),
          capability: text,
        },
      },
      requirementRefinements: nextRefinements,
    }
  }),

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

  // ── Change Records (Sprint 36 — Change Impact Assessment) ──────
  // Keyed by cr_id. Each record holds:
  //   { cr_id, cr_text, project_name, createdAt,
  //     cia: { ...CIA dict from backend },
  //     ccr: { ...signed CCR | null },
  //     status: 'received' | 'cia_generated' | 'ccr_signed'
  //             | 'revalidating' | 'closed' }
  //
  // The principle: AI proposes the CIA, human signs the CCR, then
  // the revalidation sub-run spawns. Every transition is auditable.
  changeRecords: {},

  // Record the initial CR (before the CIA generates). Used for
  // optimistic UI — the row appears as soon as the user submits.
  addChangeRecord: (crId, payload) => set(state => ({
    changeRecords: {
      ...state.changeRecords,
      [crId]: {
        cr_id:        crId,
        cr_text:      payload?.cr_text       ?? '',
        project_name: payload?.project_name  ?? '',
        createdAt:    new Date().toISOString(),
        cia:          null,
        ccr:          null,
        status:       'received',
      },
    },
  })),

  // Attach the generated CIA dict to a change record. Status moves
  // to 'cia_generated' — Sign CCR button now becomes active.
  attachCIA: (crId, cia) => set(state => {
    const existing = state.changeRecords[crId]
    if (!existing) return {}
    return {
      changeRecords: {
        ...state.changeRecords,
        [crId]: {
          ...existing,
          cia,
          status: 'cia_generated',
        },
      },
    }
  }),

  // Record the signed CCR against a change record. Status moves to
  // 'ccr_signed' — the next event (revalidation sub-run spawn) is
  // Sprint 37 work; for now we stop at the human signature gate.
  signCCR: (crId, ccr) => set(state => {
    const existing = state.changeRecords[crId]
    if (!existing) return {}
    return {
      changeRecords: {
        ...state.changeRecords,
        [crId]: {
          ...existing,
          ccr,
          status: 'ccr_signed',
        },
      },
    }
  }),

  // Reset the entire change-records slice. Primarily used in the
  // demo project loader.
  clearChangeRecords: () => set({ changeRecords: {} }),

  // ── Validated State (Sprint 37 — Confidence Engine) ───────────
  // The "EVOLV helps you STAY validated" surface. Holds the latest
  // ValidatedStateReport returned from POST /validated-state/assess
  // plus per-UR drill-down. Loading + error tracked separately so
  // the UI can show a spinner without losing the prior report.
  //
  // Shape:
  //   validatedState.report:    full ValidatedStateReport dict
  //                             from the engine (or null)
  //   validatedState.byUrId:    { [urId]: URStateAssessment } map
  //                             for fast Traceability Matrix lookup
  //   validatedState.loading:   bool
  //   validatedState.error:     string | null
  //   validatedState.lastFetched: ISO timestamp | null
  validatedState: {
    report:      null,
    byUrId:      {},
    loading:     false,
    error:       null,
    lastFetched: null,
  },

  setValidatedStateLoading: loading => set(state => ({
    validatedState: { ...state.validatedState, loading,
                      error: loading ? null : state.validatedState.error },
  })),

  // Persist a fresh report. `byUrId` is denormalised at write time
  // so the Traceability Matrix doesn't have to re-build it per
  // render.
  setValidatedStateReport: report => set(() => {
    const byUrId = {}
    for (const a of (report?.assessments ?? [])) {
      if (a?.ur_id) byUrId[a.ur_id] = a
    }
    return {
      validatedState: {
        report,
        byUrId,
        loading:     false,
        error:       null,
        lastFetched: new Date().toISOString(),
      },
    }
  }),

  setValidatedStateError: error => set(state => ({
    validatedState: { ...state.validatedState, loading: false, error },
  })),

  clearValidatedState: () => set({
    validatedState: {
      report: null, byUrId: {}, loading: false,
      error: null, lastFetched: null,
    },
  }),

  // ── Regulatory Drift (Sprint 38 — drift scan results) ─────────
  // Drift detection identifies URs that cite a superseded version
  // of any framework in the corpus registry. The scan result is
  // denormalised into byUrId for fast per-row lookup on the
  // Living Traceability Matrix (drift banner + per-UR drift
  // indicator + drift_report forwarded into the VSE assess call
  // so the citation-drift signal slot fires).
  //
  //   regulatoryDrift.report:    full DriftScanReport dict (or null)
  //   regulatoryDrift.byUrId:    { [urId]: AffectedUR } — only
  //                              affected URs present; clean URs
  //                              return undefined
  //   regulatoryDrift.loading:   bool
  //   regulatoryDrift.error:     string | null
  //   regulatoryDrift.lastFetched: ISO timestamp | null
  //
  // :requirement: URS-38.9 - Persist drift-scan results in store
  //               for cross-page reuse (RegulatoryWatch +
  //               TraceabilityMatrix + VSE assess wire-through).
  regulatoryDrift: {
    report:      null,
    byUrId:      {},
    loading:     false,
    error:       null,
    lastFetched: null,
  },

  setRegulatoryDriftLoading: loading => set(state => ({
    regulatoryDrift: {
      ...state.regulatoryDrift,
      loading,
      error: loading ? null : state.regulatoryDrift.error,
    },
  })),

  // Persist a fresh scan. `byUrId` is denormalised at write time
  // so the Traceability Matrix doesn't have to re-walk the
  // affected_urs array on every render.
  setRegulatoryDriftReport: report => set(() => {
    const byUrId = {}
    for (const u of (report?.affected_urs ?? [])) {
      if (u?.ur_id) byUrId[u.ur_id] = u
    }
    return {
      regulatoryDrift: {
        report,
        byUrId,
        loading:     false,
        error:       null,
        lastFetched: new Date().toISOString(),
      },
    }
  }),

  setRegulatoryDriftError: error => set(state => ({
    regulatoryDrift: {
      ...state.regulatoryDrift, loading: false, error,
    },
  })),

  clearRegulatoryDrift: () => set({
    regulatoryDrift: {
      report: null, byUrId: {}, loading: false,
      error: null, lastFetched: null,
    },
  }),

  // ── Retire data (Sprint 18.1 — Decommissioning Checklist) ─────
  // checklist: keyed by item id → bool. Items, regulatory citations,
  // and tooltips are defined in Retire.jsx (DECOM_CHECKLIST).
  // decommissionedAt is set when the user formally retires the
  // system after all checklist items pass.
  //
  // :requirement: URS-24.2 - Decommissioning checklist grounded in
  //               21 CFR Part 11 §11.10(c) retention requirements.
  retireData: {
    checklist:        {},
    notes:            '',
    decommissionedAt: null,
    decommissionedBy: '',
  },

  setRetireCheck: (itemId, value) => set(state => ({
    retireData: {
      ...state.retireData,
      checklist: { ...state.retireData.checklist, [itemId]: value },
    },
  })),

  setRetireNotes: text => set(state => ({
    retireData: { ...state.retireData, notes: text },
  })),

  markDecommissioned: signerName => set(state => ({
    retireData: {
      ...state.retireData,
      decommissionedAt: new Date().toISOString(),
      decommissionedBy: signerName ?? '',
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

  // ── Demo project hydration (Sprint 18.1) ───────────────────────
  // One-click loader for first-time visitors and live demos.
  // Snapshots whatever the user currently has open (so it isn't lost
  // when they switch back), registers a `proj-demo-labcore` entry,
  // and replaces the flat store with the LabCore LIMS demo seed.
  //
  // Idempotent: re-running while already on the demo project resets
  // the demo data to its pristine state (useful after a tester walks
  // the script and wants a clean slate again).
  //
  // :requirement: URS-24.1 - One-click demo project hydrates platform
  loadDemoProject: () => set(state => {
    const seed = buildDemoProject()
    const demoId = DEMO_PROJECT_META.id
    const isAlreadyOnDemo = state.activeProjectId === demoId

    // Always snapshot the *previous* (non-demo) project before
    // leaving it, so the user can return to their work.
    const projectsAfterSnapshot = isAlreadyOnDemo
      ? state.projects
      : {
          ...state.projects,
          [state.activeProjectId]: {
            ...state.projects[state.activeProjectId],
            data: extractProjectData(state),
          },
        }

    return {
      projects: {
        ...projectsAfterSnapshot,
        [demoId]: {
          id:        demoId,
          name:      DEMO_PROJECT_META.name,
          createdAt: state.projects[demoId]?.createdAt
                       ?? new Date().toISOString(),
          data:      null,  // live project — data is in flat store
          isDemo:    true,
        },
      },
      activeProjectId: demoId,
      // Spread the seed into the flat store
      ...seed,
    }
  }),
}),
{
  name: 'evolv-platform',
  // Bump this version whenever a persisted slice's shape changes
  // in a way that old data can't be safely merged into.
  // Mismatched versions trigger the migrate() path below.
  version: 38,
  // Schema-evolution guard. When new slices are added to the store
  // (e.g. Sprint 37 validatedState, Sprint 38 regulatoryDrift), old
  // persisted state in users' browsers won't have those keys. Without
  // this merge, accessing `s.validatedState.report` throws because
  // `s.validatedState` itself is undefined → component crashes silently
  // → page goes blank. This deep-merge keeps every key from the live
  // initial state, with persisted values overriding only for keys
  // that actually exist in storage. Safe for ALL future slice adds.
  merge: (persistedState, currentState) => {
    const p = persistedState ?? {}
    const merged = { ...currentState }
    for (const key of Object.keys(currentState)) {
      const live = currentState[key]
      const stored = p[key]
      // Deep-merge plain-object slices so new sub-keys land too;
      // overwrite primitives and arrays whole.
      if (
        stored !== undefined &&
        live && typeof live === 'object' && !Array.isArray(live) &&
        stored && typeof stored === 'object' && !Array.isArray(stored)
      ) {
        merged[key] = { ...live, ...stored }
      } else if (stored !== undefined) {
        merged[key] = stored
      }
    }
    return merged
  },
  // Migration path for hard schema breaks. Returning the persisted
  // state as-is means the merge() function above handles defaults.
  migrate: (persistedState, _version) => persistedState,
  // Only persist data that should survive browser refresh.
  // Tabs and activeTabId intentionally reset on reload.
  partialize: state => ({
    theme:           state.theme,
    fontSize:        state.fontSize,
    navGroupsCollapsed: state.navGroupsCollapsed,
    recentApps:      state.recentApps,
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
    qaReviews:            state.qaReviews,
    releaseData:          state.releaseData,
    retireData:           state.retireData,
    requirements:         state.requirements,
    requirementMeta:      state.requirementMeta,
    designData:           state.designData,
    userProfile:          state.userProfile,
    projects:             state.projects,
    changeRecords:        state.changeRecords,
    validatedState:       state.validatedState,
    regulatoryDrift:      state.regulatoryDrift,
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
