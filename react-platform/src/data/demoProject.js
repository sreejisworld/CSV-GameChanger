/**
 * demoProject.js — Pre-populated demo project state.
 *
 * Sprint 18.1: Demo Spine. One-click loader (`loadDemoProject` action)
 * pre-populates a believable, mid-flight CSV project across all 8
 * lifecycle phases so first-time visitors and live demo audiences can
 * walk the platform end-to-end without typing.
 *
 * Project: "LabCore LIMS v4.2 Migration"
 *  - GAMP 5 Category 4 (Configurable COTS)
 *  - Replaces legacy LabVantage with cloud LabCore
 *  - 7 user requirements, 12 functional requirements
 *  - 4 of 5 GxP-Direct URs have authored test bundles
 *  - 1 GxP-Direct UR (UR-5) deliberately has NO bundle so the
 *    Sprint 15.3 coverage-gap monitor + Design hard-gate demo works
 *  - Plan / Requirements / Risk phases marked complete
 *  - Design phase intentionally NOT complete (coverage gap blocks it)
 *
 * The export is a builder function so timestamps are fresh each call
 * and the underlying objects are not aliased across multiple loads.
 *
 * :requirement: URS-24.1 - One-click demo project hydrates the platform
 */

const now = () => new Date().toISOString()

// ── Plan ───────────────────────────────────────────────────────────
const planData = () => ({
  projectName:      'LabCore LIMS v4.2 Migration',
  gampCategory:     '4',
  systemDescription:
    'Replacement of legacy LabVantage LIMS with cloud-hosted LabCore '
    + 'v4.2. Scope covers sample chain-of-custody, batch records, '
    + 'electronic signatures on disposal, audit trail, and SAP '
    + 'integration. Migration window: Q3 2026. Two production sites '
    + '(Basel CH primary, Indianapolis US backup).',
  projectScope:
    'In scope: sample receipt → analysis → release → disposal '
    + 'workflow; e-sig events; SAP material master sync; audit '
    + 'trail per 21 CFR Part 11 §11.10. Out of scope: legacy '
    + 'LabVantage data archival (separate decommissioning project), '
    + 'instrument firmware upgrades.',
  regulatoryFrameworks: [
    '21 CFR Part 11', 'EU GMP Annex 11',
    'GAMP 5 (2nd Ed.)', 'FDA CSA Guidance',
  ],
  vmpCreated: true,
  vmpContent: {
    validationStrategy:
      'Risk-based validation per GAMP 5 Cat 4. Configuration-only '
      + 'changes verified via OQ; custom SAP adapter requires full '
      + 'PQ. CSA-aligned: scripted testing for HIGH-risk URs, '
      + 'unscripted exploratory for LOW-risk reporting features.',
    resourcesResponsibilities:
      'QA Lead: Sarah Chen (QA Director). Validation Lead: Marcus '
      + 'Webb. Lab SMEs: Dr. Priya Patel (Basel), Tom Rodriguez '
      + '(Indianapolis). IT: Anil Krishnan. Supplier: LabCore '
      + 'Solutions Inc. (CSV-qualified per SOP-VND-04).',
    timeline:
      'Plan & URS: complete. Risk & Design: in progress. OQ: '
      + '2026-W18 → W22. PQ: 2026-W23 → W26. Go-live: '
      + '2026-08-15. Hypercare: +6 weeks post go-live.',
  },
})

// ── Requirements (URs + FRs) ───────────────────────────────────────
// IDs match the conventions from useAppStore.addRequirement so any
// follow-on UI edits stay collision-free.
const requirements = [
  // UR-1 / FR-1, FR-2 — Chain-of-custody (HIGH, GxP Direct)
  { id: 'UR-1', type: 'UR',
    statement: 'The system shall register, track, and dispose of '
      + 'laboratory samples with full chain-of-custody from receipt '
      + 'through analytical release and final disposal.' },
  { id: 'FR-1', type: 'FR', parentId: 'UR-1',
    statement: 'The system shall capture sample receipt with '
      + 'timestamp, originator, and sealed-container check within '
      + '30 seconds of barcode scan.' },
  { id: 'FR-2', type: 'FR', parentId: 'UR-1',
    statement: 'The system shall generate an immutable chain-of-'
      + 'custody record per sample, recording every handler '
      + 'transition and physical-state change.' },

  // UR-2 / FR-3, FR-4 — E-signature on disposal (HIGH, GxP Direct)
  { id: 'UR-2', type: 'UR',
    statement: 'The system shall enforce qualified electronic '
      + 'signatures on sample disposal events per 21 CFR Part 11 '
      + '§11.50 and §11.70.' },
  { id: 'FR-3', type: 'FR', parentId: 'UR-2',
    statement: 'The system shall require dual-factor reauthentication '
      + '(password + TOTP) before applying a disposal e-signature.' },
  { id: 'FR-4', type: 'FR', parentId: 'UR-2',
    statement: 'The system shall record signer name, timestamp, '
      + 'meaning of signature, and link the signature to the '
      + 'specific record being signed.' },

  // UR-3 / FR-5, FR-6 — SAP integration (MEDIUM, GxP Indirect, Custom)
  { id: 'UR-3', type: 'UR',
    statement: 'The system shall synchronise material master data '
      + 'and batch genealogy bidirectionally with SAP S/4HANA '
      + 'via a validated middleware adapter.' },
  { id: 'FR-5', type: 'FR', parentId: 'UR-3',
    statement: 'The system shall poll SAP for material master '
      + 'changes every 15 minutes and reconcile differences within '
      + 'the next 5-minute cycle.' },
  { id: 'FR-6', type: 'FR', parentId: 'UR-3',
    statement: 'The system shall raise a deviation-class alert when '
      + 'SAP-LIMS reconciliation fails for the same record on two '
      + 'consecutive cycles.' },

  // UR-4 / FR-7 — Audit trail (MEDIUM, GxP Direct, OOB)
  { id: 'UR-4', type: 'UR',
    statement: 'The system shall maintain a complete, computer-'
      + 'generated, time-stamped audit trail per 21 CFR Part 11 '
      + '§11.10(e) and EU Annex 11 §9.' },
  { id: 'FR-7', type: 'FR', parentId: 'UR-4',
    statement: 'The system shall record old value, new value, user, '
      + 'and reason on every GxP-relevant change event.' },

  // UR-5 / FR-8, FR-9 — Temperature monitoring (HIGH, GxP Direct)
  // ⚠ Deliberately has NO test bundle so coverage-gap monitor fires
  { id: 'UR-5', type: 'UR',
    statement: 'The system shall monitor sample-storage temperature '
      + 'continuously and raise a deviation alarm within 60 seconds '
      + 'of an out-of-range reading.' },
  { id: 'FR-8', type: 'FR', parentId: 'UR-5',
    statement: 'The system shall poll connected freezers every 60 '
      + 'seconds and store readings for at least 7 years.' },
  { id: 'FR-9', type: 'FR', parentId: 'UR-5',
    statement: 'The system shall page the on-call lab supervisor '
      + 'and log a Deviation Notification when temperature exceeds '
      + 'the validated range for >2 minutes.' },

  // UR-6 / FR-10 — RBAC (LOW, GxP Indirect, OOB)
  { id: 'UR-6', type: 'UR',
    statement: 'The system shall provide role-based access control '
      + 'aligned with the ten standard LabCore roles defined in '
      + 'the User Roles & Permissions matrix.' },
  { id: 'FR-10', type: 'FR', parentId: 'UR-6',
    statement: 'The system shall deny any action not explicitly '
      + 'permitted by the user\u2019s assigned role.' },

  // UR-7 / FR-11, FR-12 — Reporting dashboard (LOW, No GxP)
  { id: 'UR-7', type: 'UR',
    statement: 'The system shall provide an executive reporting '
      + 'dashboard summarising daily throughput and pending '
      + 'approvals for site directors.' },
  { id: 'FR-11', type: 'FR', parentId: 'UR-7',
    statement: 'The dashboard shall refresh on a 15-minute cadence '
      + 'or on-demand.' },
  { id: 'FR-12', type: 'FR', parentId: 'UR-7',
    statement: 'The dashboard shall export to PDF and CSV.' },
]

// ── Requirement metadata (3 Cs + stakeholder + req type) ───────────
const requirementMeta = {
  'UR-1': {
    capability: 'register, track, and dispose of laboratory samples',
    condition:  'from receipt through analytical release',
    constraint: 'with full chain-of-custody traceability',
    requirement_type: 'Functional',
    stakeholder: 'Lab',
  },
  'UR-2': {
    capability: 'enforce qualified electronic signatures',
    condition:  'on every sample-disposal event',
    constraint: 'per 21 CFR Part 11 §11.50 and §11.70',
    requirement_type: 'Functional',
    stakeholder: 'QA/ITQA',
  },
  'UR-3': {
    capability: 'synchronise material master and batch genealogy '
                + 'with SAP S/4HANA',
    condition:  'bidirectionally on a 15-minute cycle',
    constraint: 'via a validated middleware adapter',
    requirement_type: 'Non-Functional',
    stakeholder: 'IT',
  },
  'UR-4': {
    capability: 'maintain a computer-generated audit trail',
    condition:  'on every GxP-relevant create/update/delete',
    constraint: 'per 21 CFR Part 11 §11.10(e) and EU Annex 11 §9',
    requirement_type: 'Non-Functional',
    stakeholder: 'Data Owner',
  },
  'UR-5': {
    capability: 'monitor sample-storage temperature continuously',
    condition:  'and raise a deviation alarm within 60 seconds',
    constraint: 'of any out-of-range reading',
    requirement_type: 'Functional',
    stakeholder: 'Lab',
  },
  'UR-6': {
    capability: 'enforce role-based access control',
    condition:  'aligned with the ten LabCore standard roles',
    constraint: 'per the User Roles & Permissions matrix',
    requirement_type: 'Non-Functional',
    stakeholder: 'IT',
  },
  'UR-7': {
    capability: 'provide an executive reporting dashboard',
    condition:  'refreshing every 15 minutes',
    constraint: 'with PDF/CSV export',
    requirement_type: 'Functional',
    stakeholder: 'Senior Mgmt',
  },
}

// ── Risk assessments per UR ───────────────────────────────────────
// Matches Risk.jsx::calcRisk():
//   GxP Direct + Custom/Configured → HIGH
//   GxP Direct + OOB               → MEDIUM
//   GxP Indirect + Configured      → HIGH
//   GxP Indirect + Custom          → MEDIUM
//   GxP Indirect + OOB             → LOW
//   No GxP                         → LOW
const riskData = {
  'UR-1': { impact: 'GxP Direct',   implMethod: 'Configured',
            riskLevel: 'HIGH',   testAssurance: 'Scripted' },
  'UR-2': { impact: 'GxP Direct',   implMethod: 'Configured',
            riskLevel: 'HIGH',   testAssurance: 'Scripted' },
  'UR-3': { impact: 'GxP Indirect', implMethod: 'Custom',
            riskLevel: 'MEDIUM', testAssurance: 'Scripted' },
  'UR-4': { impact: 'GxP Direct',   implMethod: 'Out of the Box',
            riskLevel: 'MEDIUM', testAssurance: 'Scripted' },
  'UR-5': { impact: 'GxP Direct',   implMethod: 'Configured',
            riskLevel: 'HIGH',   testAssurance: 'Scripted' },
  'UR-6': { impact: 'GxP Indirect', implMethod: 'Out of the Box',
            riskLevel: 'LOW',    testAssurance: 'Unscripted' },
  'UR-7': { impact: 'No GxP',       implMethod: 'Out of the Box',
            riskLevel: 'LOW',    testAssurance: 'Unscripted' },
}

// ── Test bundle factory ────────────────────────────────────────────
// Builds a minimal but realistic bundle (4 setup + 3 execution steps)
// with regulatory citations attached per execution step. Matches the
// shape persisted by POST /test-authoring/generate so the existing
// preview / promote pipeline works without changes.
function makeBundle({
  reqId, requirement_summary, impact, implementation_method,
  risk_level, depth, test_type, mode, citations, executionSteps,
}) {
  return {
    bundle_id: `TB-${reqId}`,
    requirement_id: reqId,
    requirement_summary,
    project_name: 'LabCore LIMS v4.2 Migration',
    impact,
    implementation_method,
    risk_level,
    depth,
    test_type,
    mode,
    enrichment_applied: false,
    source: 'demo-seed',
    generated_at: now(),
    steps: [
      { step_type: 'Setup', step_number: 1,
        step_title: 'Login as System Owner',
        step_instruction:
          'Log into LabCore v4.2 with a System Owner account that '
          + 'has the validation test environment role enabled.',
        expected_result: '',
        archetype: 'setup',
        requirement_reference: '',
        citations: [], source: 'ai' },
      { step_type: 'Setup', step_number: 2,
        step_title: 'Navigate to functional area',
        step_instruction:
          'Open the relevant module (Samples / Disposal / Audit '
          + 'Trail / Integrations) and confirm the validated '
          + 'configuration baseline is loaded.',
        expected_result: '',
        archetype: 'setup',
        requirement_reference: '',
        citations: [], source: 'ai' },
      { step_type: 'Setup', step_number: 3,
        step_title: 'Confirm test data prerequisites',
        step_instruction:
          'Confirm pre-loaded test fixtures (sample IDs, user '
          + 'accounts, signature credentials) are available per '
          + 'the test data plan.',
        expected_result: '',
        archetype: 'setup',
        requirement_reference: '',
        citations: [], source: 'ai' },
      ...executionSteps.map((s, i) => ({
        step_type: 'Execution',
        step_number: i + 1,
        step_title: s.title,
        step_instruction: s.instruction,
        expected_result: s.expected,
        archetype: s.archetype,
        test_case_type: s.testCaseType,
        requirement_reference: s.frRef,
        citations: s.citations,
        source: 'ai',
      })),
    ],
    bundle_citations: citations,
    quality_checklist: {
      all_steps_have_instructions: true,
      execution_steps_have_expected_results: true,
      execution_steps_have_references: true,
      all_execution_steps_carry_citations: true,
      step_titles_unique: true,
    },
    schema_version: '1.0.0',
  }
}

// ── Pre-built bundles (4 of 5 GxP-Direct URs covered) ─────────────
// UR-5 is intentionally absent so the coverage-gap monitor has
// something to flag — that's the customer-demo teaching moment.
const testBundles = {
  'UR-1': makeBundle({
    reqId: 'UR-1',
    requirement_summary:
      'Sample chain-of-custody from receipt to disposal',
    impact: 'GxP Direct',
    implementation_method: 'Configured',
    risk_level: 'High',
    depth: 'FULL',
    test_type: 'Informal',
    mode: 'hybrid',
    citations: [
      { regulation: '21 CFR Part 11', section: '§11.10(b)',
        rationale: 'Chain-of-custody is a record subject to '
          + 'protection, retention, and accurate-reproduction '
          + 'requirements.' },
      { regulation: 'EU GMP Annex 11', section: '§9 (Audit Trails)',
        rationale: 'GMP-relevant changes must be traceable.' },
      { regulation: 'GAMP 5 (2nd Ed.)', section: 'Appendix M3',
        rationale: 'Risk-based testing for Cat 4 configured '
          + 'systems requires functional verification of '
          + 'configured workflows.' },
    ],
    executionSteps: [
      { title: 'Verify FR-1 — sample receipt within 30 seconds',
        instruction:
          'Scan a pre-prepared sample barcode. Observe the '
          + 'receipt-record dialog timestamp and originator '
          + 'auto-fill from the logged-in user.',
        expected:
          'Receipt record is created within 30 seconds. '
          + 'Timestamp matches scanner clock; originator equals '
          + 'logged-in user; sealed-container checkbox defaults '
          + 'to "verified".',
        testCaseType: 'Positive',
        archetype: 'positive',
        frRef: 'UR-1 / FR-1',
        citations: [
          { regulation: '21 CFR Part 11', section: '§11.10(b)' },
        ] },
      { title: 'Verify FR-2 — chain-of-custody immutability',
        instruction:
          'Attempt to edit the chain-of-custody record from '
          + 'a non-System-Admin account.',
        expected:
          'Edit is denied with the message "Chain-of-custody '
          + 'records are immutable. Use the corrective-action '
          + 'workflow." No row in the COC table is altered.',
        testCaseType: 'Negative',
        archetype: 'negative',
        frRef: 'UR-1 / FR-2',
        citations: [
          { regulation: '21 CFR Part 11', section: '§11.10(c)' },
        ] },
      { title: 'Verify chain-of-custody handler transitions',
        instruction:
          'Transfer the sample to a second handler. Confirm a '
          + 'new COC row is appended.',
        expected:
          'COC table shows the original row plus a new row '
          + 'with the new handler, prior handler reference, and '
          + 'transition timestamp. No prior row is mutated.',
        testCaseType: 'Positive',
        archetype: 'positive',
        frRef: 'UR-1 / FR-2',
        citations: [
          { regulation: 'EU GMP Annex 11', section: '§9' },
        ] },
    ],
  }),

  'UR-2': makeBundle({
    reqId: 'UR-2',
    requirement_summary:
      'Qualified electronic signatures on sample disposal',
    impact: 'GxP Direct',
    implementation_method: 'Configured',
    risk_level: 'High',
    depth: 'FULL',
    test_type: 'Formal OQ',
    mode: 'hybrid',
    citations: [
      { regulation: '21 CFR Part 11', section: '§11.50',
        rationale: 'Signed records must include printed signer '
          + 'name, date/time, and meaning.' },
      { regulation: '21 CFR Part 11', section: '§11.70',
        rationale: 'Signature must be linked to the record '
          + 'being signed.' },
      { regulation: '21 CFR Part 11', section: '§11.200(a)',
        rationale: 'Two distinct identification components '
          + 'required for non-biometric e-signatures.' },
    ],
    executionSteps: [
      { title: 'Verify FR-3 — dual-factor reauthentication',
        instruction:
          'Initiate a sample disposal. When prompted, enter '
          + 'a valid password but cancel the TOTP prompt.',
        expected:
          'Disposal is rejected with the message "E-signature '
          + 'cancelled — second factor required." No disposal '
          + 'record is created.',
        testCaseType: 'Negative',
        archetype: 'negative',
        frRef: 'UR-2 / FR-3',
        citations: [
          { regulation: '21 CFR Part 11', section: '§11.200(a)' },
        ] },
      { title: 'Verify FR-4 — signature linkage',
        instruction:
          'Complete a successful disposal e-signature. Open the '
          + 'audit trail entry for the signed record.',
        expected:
          'Audit trail shows: signer printed name, UTC '
          + 'timestamp, meaning ("Approval of Disposal"), and '
          + 'a hash linking the signature to the record id.',
        testCaseType: 'Positive',
        archetype: 'positive',
        frRef: 'UR-2 / FR-4',
        citations: [
          { regulation: '21 CFR Part 11', section: '§11.50' },
          { regulation: '21 CFR Part 11', section: '§11.70' },
        ] },
    ],
  }),

  'UR-3': makeBundle({
    reqId: 'UR-3',
    requirement_summary:
      'SAP material master + batch genealogy bidirectional sync',
    impact: 'GxP Indirect',
    implementation_method: 'Custom',
    risk_level: 'Medium',
    depth: 'STANDARD',
    test_type: 'Formal OQ',
    mode: 'deterministic',
    citations: [
      { regulation: 'GAMP 5 (2nd Ed.)', section: 'Appendix D9',
        rationale: 'Custom-developed integrations require formal '
          + 'specification and testing of interface behaviour.' },
      { regulation: 'EU GMP Annex 11', section: '§5 (Data)',
        rationale: 'Data exchanged between systems must be '
          + 'verified for accuracy.' },
    ],
    executionSteps: [
      { title: 'Verify FR-5 — 15-minute reconciliation cycle',
        instruction:
          'Modify a material master attribute in SAP test '
          + 'sandbox. Wait one polling interval (15 min, may '
          + 'be force-triggered via /admin/sync/run).',
        expected:
          'LabCore material master record reflects the SAP '
          + 'change within 5 minutes of the next poll. A sync '
          + 'log entry is created with source=SAP and '
          + 'reconciled=true.',
        testCaseType: 'Positive',
        archetype: 'positive',
        frRef: 'UR-3 / FR-5',
        citations: [
          { regulation: 'EU GMP Annex 11', section: '§5' },
        ] },
      { title: 'Verify FR-6 — deviation alert on consecutive fail',
        instruction:
          'Configure SAP test sandbox to return a 500 error on '
          + 'two consecutive sync attempts. Wait two cycles.',
        expected:
          'A deviation-class alert is raised with severity '
          + '"Major" and routed to the LIMS Operations queue. '
          + 'The sync log shows two failure entries with '
          + 'reconciled=false.',
        testCaseType: 'Edge case',
        archetype: 'edge_case',
        frRef: 'UR-3 / FR-6',
        citations: [
          { regulation: 'GAMP 5 (2nd Ed.)', section: 'Appendix D9' },
        ] },
    ],
  }),

  'UR-4': makeBundle({
    reqId: 'UR-4',
    requirement_summary:
      'Audit trail per 21 CFR Part 11 §11.10(e) + EU Annex 11 §9',
    impact: 'GxP Direct',
    implementation_method: 'Out of the Box',
    risk_level: 'Medium',
    depth: 'MEDIUM',
    test_type: 'Formal OQ',
    mode: 'deterministic',
    citations: [
      { regulation: '21 CFR Part 11', section: '§11.10(e)',
        rationale: 'Audit trail must record operator entries and '
          + 'actions that create, modify, or delete electronic '
          + 'records.' },
      { regulation: 'EU GMP Annex 11', section: '§9',
        rationale: 'Audit trail must capture all GMP-relevant '
          + 'changes and deletions.' },
    ],
    executionSteps: [
      { title: 'Verify FR-7 — change capture (old/new/user/reason)',
        instruction:
          'Modify a GxP-relevant field on a sample record. '
          + 'Provide a reason in the prompt. Open the audit '
          + 'trail viewer.',
        expected:
          'Audit trail row shows: old value, new value, '
          + 'logged-in user, UTC timestamp, and the entered '
          + 'reason. Row cannot be edited or deleted from any '
          + 'role including System Admin.',
        testCaseType: 'Positive',
        archetype: 'positive',
        frRef: 'UR-4 / FR-7',
        citations: [
          { regulation: '21 CFR Part 11', section: '§11.10(e)' },
          { regulation: 'EU GMP Annex 11', section: '§9' },
        ] },
    ],
  }),

  'UR-6': makeBundle({
    reqId: 'UR-6',
    requirement_summary:
      'Role-based access control per LabCore role matrix',
    impact: 'GxP Indirect',
    implementation_method: 'Out of the Box',
    risk_level: 'Low',
    depth: 'CHARTER',
    test_type: 'Informal',
    mode: 'deterministic',
    citations: [
      { regulation: 'GAMP 5 (2nd Ed.)', section: 'Appendix M3',
        rationale: 'Cat 1/3 OOB security controls verified by '
          + 'risk-based unscripted exploration.' },
      { regulation: '21 CFR Part 11', section: '§11.10(d)',
        rationale: 'System access must be limited to authorised '
          + 'individuals.' },
    ],
    executionSteps: [
      { title: 'Charter — explore RBAC enforcement',
        instruction:
          'As a Lab Technician, attempt to access the Disposal '
          + 'Authorisation screen, the Audit Trail viewer, and '
          + 'the System Admin panel. Document outcome of each.',
        expected:
          'Disposal Authorisation: denied (role gate). Audit '
          + 'Trail: read-only access granted. System Admin: '
          + 'denied. No silent failures; all denials show a '
          + 'clear "Access denied — role X required" message.',
        testCaseType: 'Positive',
        archetype: 'charter',
        frRef: 'UR-6 / FR-10',
        citations: [
          { regulation: '21 CFR Part 11', section: '§11.10(d)' },
        ] },
    ],
  }),

  'UR-7': makeBundle({
    reqId: 'UR-7',
    requirement_summary:
      'Executive reporting dashboard (non-GxP)',
    impact: 'No GxP',
    implementation_method: 'Out of the Box',
    risk_level: 'Low',
    depth: 'CHARTER',
    test_type: 'Informal',
    mode: 'deterministic',
    citations: [
      { regulation: 'FDA CSA Guidance (Sept 2022)',
        section: 'Section IV — Risk-Based Approach',
        rationale: 'Non-GxP convenience features qualify for '
          + 'unscripted/exploratory assurance.' },
    ],
    executionSteps: [
      { title: 'Charter — exercise reporting dashboard',
        instruction:
          'As a Site Director, navigate to the dashboard, '
          + 'inspect throughput tile, trigger PDF + CSV exports, '
          + 'force a 15-minute refresh.',
        expected:
          'Tiles render with current-shift figures; PDF + CSV '
          + 'exports download with matching values; refresh '
          + 'updates timestamps. No GxP data exposed beyond '
          + 'role permissions.',
        testCaseType: 'Positive',
        archetype: 'charter',
        frRef: 'UR-7 / FR-11',
        citations: [
          { regulation: 'FDA CSA Guidance (Sept 2022)',
            section: 'Section IV' },
        ] },
    ],
  }),
}

// ── Phase completion ──────────────────────────────────────────────
// Plan/Reqs/Risk done. Design intentionally NOT done — the coverage
// gap on UR-5 hard-blocks Design completion (Sprint 15.3 gate), which
// is the demo teaching moment for first-time visitors.
const phaseCompletion = {
  plan: true, requirements: true, risk: true,
  design: false, verify: false, release: false,
  monitor: false, retire: false,
}

// ── Status badges ─────────────────────────────────────────────────
const statusBadges = {
  'home':         null,
  'plan':         { type: 'success', label: 'Complete' },
  'requirements': { type: 'success', label: '7 URs · 12 FRs' },
  'risk':         { type: 'success', label: '3 High · 2 Med' },
  'design':       { type: 'error',   label: 'Coverage gap' },
  'verify':       { type: 'warning', label: '3 locked · 1 in-flight' },
  'release':      { type: 'info',    label: '2 of 3 signed' },
  'monitor':      { type: 'warning', label: '1 CR pending' },
  'retire':       null,
  'system-journey': { type: 'info', label: 'Demo loaded' },
  'portfolio':    { type: 'info',   label: 'New' },
  'governance':   { type: 'warning', label: '3 pending' },
  'navigator':    null,
  'dev-portal':   { type: 'success', label: 'Live' },
  'config':       null,
  'academy':      null,
  'impact-analytics': null,
  'docs':         null,
}

// ── Design data (architecture notes, partial) ─────────────────────
const designData = () => ({
  architectureNotes:
    'LabCore v4.2 SaaS (AWS eu-central-1, multi-AZ). Custom SAP '
    + 'adapter deployed as containerised middleware in customer '
    + 'VPC. Read replicas in Indianapolis for DR.',
  hldNotes:
    'Three layers: (1) LabCore SaaS — sample/COC/disposal/audit; '
    + '(2) SAP adapter — bidirectional sync; (3) Reporting '
    + 'service — read-only dashboard.',
  lldNotes:
    'In progress — pending coverage-gap closure on UR-5 '
    + '(temperature monitoring) before LLD sign-off.',
  integrationNotes:
    'Inbound: SAP IDoc → adapter → LabCore REST. Outbound: '
    + 'LabCore webhooks → adapter → SAP RFC. Adapter retains 7 '
    + 'days of message journal for replay.',
  diagramUrl: 'https://lucid.app/labcore-architecture',
  configItems: [
    { item: 'E-signature timeout', system: 'LabCore',
      parameter: 'esign.session.timeout_minutes', value: '5',
      rationale: '21 CFR Part 11 §11.300(d) — limit re-use window.' },
    { item: 'Audit trail retention', system: 'LabCore',
      parameter: 'audit.retention_years', value: '7',
      rationale: '21 CFR Part 11 §11.10(c) + GMP retention.' },
    { item: 'SAP poll interval', system: 'SAP Adapter',
      parameter: 'sap.poll.interval_minutes', value: '15',
      rationale: 'Per UR-3 spec.' },
  ],
})

// ── Showcase test execution data (Sprint 28-LinkedIn screenshot) ──
// Populates the Living Traceability Matrix so a CSV leader can see
// the full UR → Risk → Bundle → Run → Defect → Approval chain rendered
// across multiple status states in a single screenshot:
//
//   UR-1 → Passed         (HIGH GxP Direct, 3/3 pass, signed)
//   UR-2 → Passed         (HIGH GxP Direct, 2/2 pass, signed)
//   UR-3 → Failed         (MED GxP Indirect, 1 fail + open defect)
//   UR-4 → In Progress    (MED GxP Direct OOB, 1/1 pass, unlocked)
//   UR-5 → No Bundle      (HIGH coverage gap — teaching moment)
//   UR-6 → Authored       (LOW GxP Indirect, charter ready)
//   UR-7 → Authored       (LOW No GxP, charter ready)
//
// `releaseData.released` is intentionally false so the per-row status
// pills render distinctly. Approvals[] is populated to show the
// release packet is mid-flight (visible in the drill-down drawer).

// Helper — promote a bundle dict into the lean script shape
// produced by the live `promoteBundleToScript` action.
function _bundleToScript(bundle) {
  return {
    script_id:                bundle.bundle_id,
    urs_id:                   bundle.requirement_id,
    ur_id:                    bundle.requirement_id,
    test_type:                bundle.test_type,
    risk_level:               bundle.risk_level,
    test_strategy:            bundle.depth,
    regulatory_justification: (bundle.bundle_citations ?? [])
      .map(c => `${c.regulation} ${c.section}: ${c.rationale}`)
      .join('\n\n'),
    generated_at:             bundle.generated_at,
    steps:                    bundle.steps,
    quality_checklist:        bundle.quality_checklist,
    depth:                    bundle.depth,
    mode:                     bundle.mode,
    requirement_summary:      bundle.requirement_summary,
  }
}

// Build a per-step results map for a script. `verdicts` is a list
// of verdicts in execution-step order (e.g. ['Pass','Fail']); setup
// steps default to Pass + the same tester. Results match the shape
// produced by `setStepResult` in the live store so any UI that reads
// stepResults (Verify, ALCOA report, drawer) renders identically.
function _buildStepResults(script, executionVerdicts, tester, baseDate) {
  const results = {}
  let stepClock = new Date(baseDate).getTime()
  let execIdx   = 0
  for (const step of script.steps ?? []) {
    const key = `${step.step_number}_${step.step_type}`
    stepClock += 90_000  // +1.5 min per step
    if (step.step_type === 'Setup') {
      results[key] = {
        verdict:      'Pass',
        actualResult: 'Setup completed per instruction.',
        testerName:   tester,
        executedAt:   new Date(stepClock).toISOString(),
        evidence:     null,
      }
    } else {
      const verdict = executionVerdicts[execIdx] ?? null
      execIdx += 1
      if (verdict === null) {
        results[key] = {
          verdict: null, actualResult: '', testerName: '',
          executedAt: null, evidence: null,
        }
      } else {
        results[key] = {
          verdict,
          actualResult: verdict === 'Pass'
            ? 'Observed result matched expected outcome. '
              + 'Screenshot + system log captured.'
            : verdict === 'Fail'
              ? 'Observed result did NOT match expected outcome. '
                + 'Defect raised — see defect log.'
              : 'Step blocked — pending dependency resolution.',
          testerName: tester,
          executedAt: new Date(stepClock).toISOString(),
          evidence:   { kind: 'screenshot',
                        name: `evidence_${key}.png` },
        }
      }
    }
  }
  return results
}

// Build a TestRun matching the live `initTestRun` shape so the
// Verify page, ALCOA report, and Traceability Matrix all read it
// without conditionals.
function _buildRun({
  scriptId, runId, tester, signerName, status, startedAt,
  lockedAt, results,
}) {
  return {
    runId,
    scriptId,
    startedAt,
    status,                       // 'in_progress' | 'locked'
    lockedAt:       lockedAt ?? null,
    signerName:     signerName ?? '',
    signingMeaning: 'Approval of Test Execution',
    reasoningHash:  status === 'locked'
      ? `sha256:${runId.slice(-12)}-mock`
      : null,
    stepResults:    results,
    initialTester:  tester,
  }
}

// Pre-built scripts (4 of 7 URs have promoted bundles → runnable).
// UR-1, UR-2, UR-3 are locked; UR-4 is mid-flight (in_progress).
function buildShowcaseExecution() {
  const scripts = {
    'TB-UR-1': _bundleToScript(testBundles['UR-1']),
    'TB-UR-2': _bundleToScript(testBundles['UR-2']),
    'TB-UR-3': _bundleToScript(testBundles['UR-3']),
    'TB-UR-4': _bundleToScript(testBundles['UR-4']),
  }

  const runs = {
    // ── UR-1: Passed (3/3) ──
    'RUN-TB-UR-1-20260505T093000Z': _buildRun({
      scriptId:   'TB-UR-1',
      runId:      'RUN-TB-UR-1-20260505T093000Z',
      tester:     'Sarah Chen',
      signerName: 'Sarah Chen, QA Director',
      status:     'locked',
      startedAt:  '2026-05-05T09:30:00.000Z',
      lockedAt:   '2026-05-05T11:42:00.000Z',
      results:    _buildStepResults(
        scripts['TB-UR-1'],
        ['Pass', 'Pass', 'Pass'],
        'Sarah Chen',
        '2026-05-05T09:30:00.000Z',
      ),
    }),

    // ── UR-2: Passed (2/2) ──
    'RUN-TB-UR-2-20260506T140500Z': _buildRun({
      scriptId:   'TB-UR-2',
      runId:      'RUN-TB-UR-2-20260506T140500Z',
      tester:     'Marcus Webb',
      signerName: 'Marcus Webb, Validation Lead',
      status:     'locked',
      startedAt:  '2026-05-06T14:05:00.000Z',
      lockedAt:   '2026-05-06T15:48:00.000Z',
      results:    _buildStepResults(
        scripts['TB-UR-2'],
        ['Pass', 'Pass'],
        'Marcus Webb',
        '2026-05-06T14:05:00.000Z',
      ),
    }),

    // ── UR-3: Failed (1 pass, 1 fail) → open defect DEF-001 ──
    'RUN-TB-UR-3-20260504T101500Z': _buildRun({
      scriptId:   'TB-UR-3',
      runId:      'RUN-TB-UR-3-20260504T101500Z',
      tester:     'Dr. Priya Patel',
      signerName: 'Dr. Priya Patel, Lab SME (Basel)',
      status:     'locked',
      startedAt:  '2026-05-04T10:15:00.000Z',
      lockedAt:   '2026-05-04T12:30:00.000Z',
      results:    _buildStepResults(
        scripts['TB-UR-3'],
        ['Pass', 'Fail'],
        'Dr. Priya Patel',
        '2026-05-04T10:15:00.000Z',
      ),
    }),

    // ── UR-4: In Progress (1/1 pass, unlocked) ──
    'RUN-TB-UR-4-20260507T080000Z': _buildRun({
      scriptId:   'TB-UR-4',
      runId:      'RUN-TB-UR-4-20260507T080000Z',
      tester:     'Tom Rodriguez',
      signerName: '',
      status:     'in_progress',
      startedAt:  '2026-05-07T08:00:00.000Z',
      lockedAt:   null,
      results:    _buildStepResults(
        scripts['TB-UR-4'],
        ['Pass'],
        'Tom Rodriguez',
        '2026-05-07T08:00:00.000Z',
      ),
    }),
  }

  // ── Defects keyed by runId ──
  const defects = {
    'RUN-TB-UR-3-20260504T101500Z': [
      {
        id:           'DEF-001',
        stepKey:      '2_Execution',
        severity:     'High',
        status:       'Open',
        description:
          'SAP adapter does not raise a Major-class deviation '
          + 'alert after two consecutive 500-error sync attempts. '
          + 'Adapter log shows the failures but the alert queue '
          + 'is silent. Reproduces consistently with /admin/sync/'
          + 'force-fail. Blocks UR-3 acceptance.',
        assignee:     'Anil Krishnan, IT',
        fixDate:      '2026-05-14',
        frRef:        'UR-3 / FR-6',
        screenshotName: 'def001-adapter-log.png',
        createdAt:    '2026-05-04T12:08:00.000Z',
      },
      {
        id:           'DEF-002',
        stepKey:      '1_Execution',
        severity:     'Low',
        status:       'Closed',
        description:
          'Sync log timestamps were displayed in local browser '
          + 'time instead of UTC. Fixed in adapter v0.4.2 — '
          + 'verified by re-execution.',
        assignee:     'Anil Krishnan, IT',
        fixDate:      '2026-05-04',
        frRef:        'UR-3 / FR-5',
        screenshotName: 'def002-tz-fix.png',
        createdAt:    '2026-05-04T11:20:00.000Z',
      },
    ],
  }

  // ── Release approvals (released = false → still mid-flight) ──
  // Two reviewers have already signed; QA Head sign-off is pending,
  // so the global release flag stays false and per-row status pills
  // render their actual workflow state.
  const releaseData = {
    approvals: [
      {
        signerName: 'Marcus Webb',
        role:       'Validation Lead',
        meaning:    'Validation evidence reviewed and accepted',
        signedAt:   '2026-05-06T16:10:00.000Z',
      },
      {
        signerName: 'Anil Krishnan',
        role:       'IT Lead',
        meaning:    'System readiness confirmed (infra + integration)',
        signedAt:   '2026-05-06T17:42:00.000Z',
      },
    ],
    released:   false,
    releasedAt: null,
  }

  return { scripts, runs, defects, releaseData }
}

export function buildDemoProject() {
  const exec = buildShowcaseExecution()
  return {
    planData: planData(),
    requirements: requirements.map(r => ({ ...r })),
    requirementMeta: JSON.parse(JSON.stringify(requirementMeta)),
    riskData: JSON.parse(JSON.stringify(riskData)),
    testBundles: JSON.parse(JSON.stringify(testBundles)),
    testScripts: JSON.parse(JSON.stringify(exec.scripts)),
    testRuns:    JSON.parse(JSON.stringify(exec.runs)),
    activeRunId: null,
    briefingAcknowledged: {},
    defects:     JSON.parse(JSON.stringify(exec.defects)),
    unscriptedSessions: {},
    qaReviews: {},
    releaseData: JSON.parse(JSON.stringify(exec.releaseData)),
    retireData:  { checklist: {}, notes: '',
                   decommissionedAt: null, decommissionedBy: '' },
    designData: designData(),
    phaseCompletion: { ...phaseCompletion },
    statusBadges: { ...statusBadges },
    requirementRefinements: {},
    // Sprint 36 — start the demo with no change records so the
    // CIA flow demos cleanly from a fresh inbox state.
    changeRecords: {},
    // Sprint 37 — Validated State Engine. Empty on demo load; the
    // user clicks "Assess Validated State" in Traceability Matrix
    // (or Monitor → System Health) to compute the first report.
    validatedState: {
      report: null, byUrId: {}, loading: false,
      error: null, lastFetched: null,
    },
  }
}

// Convenience metadata used by the Home banner
export const DEMO_PROJECT_META = {
  id:   'proj-demo-labcore',
  name: 'LabCore LIMS v4.2 Migration',
  tagline:
    'Mid-flight LIMS migration. GAMP 5 Cat 4. Demonstrates the '
    + 'end-to-end EVOLV lifecycle including coverage-gap detection.',
}
