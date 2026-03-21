/**
 * Docs — EVOLV Next-Gen Documentation System.
 *
 * Layout:
 *  ┌──────────────────┬──────────────────────────────────────┐
 *  │ Searchable       │  Article: Overview / 100x / Steps /  │
 *  │ Sidebar          │  Regulatory Context / Try it         │
 *  │ (280px)          │  Live-Sync Version Badge             │
 *  └──────────────────┴──────────────────────────────────────┘
 */
import { useState, useMemo } from 'react'
import { useAppStore } from '../store/useAppStore.js'

// ── Live-Sync Version Map ──────────────────────────────────────
// Maps article ID → { version, date, verified }
// In production this would be fetched from /api/docs/versions
const VERSION_MAP = {
  'platform-overview':    { version: '1.1', date: '2026-03-13', verified: true },
  'quick-start':          { version: '1.1', date: '2026-03-13', verified: true },
  'key-concepts':         { version: '1.1', date: '2026-03-13', verified: true },
  'smart-requirements':   { version: '1.1', date: '2026-03-13', verified: true },
  'urs-generation':       { version: '1.1', date: '2026-03-13', verified: true },
  'ur-fr':                { version: '1.1', date: '2026-03-13', verified: true },
  'verification-agent':   { version: '1.1', date: '2026-03-13', verified: true },
  'csa-test-scripts':     { version: '1.1', date: '2026-03-13', verified: true },
  'validation-report':    { version: '1.1', date: '2026-03-13', verified: true },
  'api-keys':             { version: '1.1', date: '2026-03-13', verified: true },
  'evolv-connect':        { version: '1.1', date: '2026-03-13', verified: true },
  'webhooks':             { version: '1.1', date: '2026-03-13', verified: true },
  '21cfr11':              { version: '1.1', date: '2026-03-13', verified: true },
  'gamp5':                { version: '1.1', date: '2026-03-13', verified: true },
  'fda-ai-2026':          { version: '1.1', date: '2026-03-13', verified: true },
  'hitl':                 { version: '1.1', date: '2026-03-13', verified: true },
  'audit-trail':          { version: '1.1', date: '2026-03-13', verified: true },
  'glossary':             { version: '1.1', date: '2026-03-13', verified: true },
}

// ── Navigation structure ───────────────────────────────────────
const NAV = [
  {
    id: 'getting-started', title: 'Getting Started', icon: '🚀',
    articles: [
      { id: 'platform-overview', title: 'Platform Overview',  tags: ['intro', 'overview', 'what is evolv'] },
      { id: 'quick-start',       title: 'Quick Start Guide',  tags: ['setup', 'install', 'begin'] },
      { id: 'key-concepts',      title: 'Key Concepts',       tags: ['gamp', 'csa', 'concepts'] },
    ],
  },
  {
    id: 'verify', title: 'Validation Factory', icon: '🏭',
    articles: [
      { id: 'smart-requirements', title: 'SMART Requirements Engine', tags: ['smart', 'requirements', 'urs', 'ai'] },
      { id: 'urs-generation',     title: 'URS Generation',            tags: ['urs', 'generate', 'requirements'] },
      { id: 'ur-fr',              title: 'UR/FR Transformation',      tags: ['ur', 'fr', 'functional', 'risk'] },
      { id: 'verification-agent', title: 'Verification Agent',        tags: ['verify', 'compliance', 'gamp5'] },
      { id: 'csa-test-scripts',   title: 'CSA Test Scripts',          tags: ['test', 'csa', 'oq', 'uat', 'script'] },
      { id: 'validation-report',  title: 'Validation Report PDF',     tags: ['pdf', 'report', 'signature', 'export'] },
    ],
  },
  {
    id: 'dev-portal', title: 'Dev Portal', icon: '⚙️',
    articles: [
      { id: 'api-keys',      title: 'API Key Management',         tags: ['api', 'key', 'token', 'auth'] },
      { id: 'evolv-connect', title: 'EVOLV Connect Integrations', tags: ['sap', 'salesforce', 'veeva', 'integration'] },
      { id: 'webhooks',      title: 'Webhooks',                   tags: ['webhook', 'events', 'hmac'] },
    ],
  },
  {
    id: 'compliance', title: 'Compliance & Security', icon: '🛡️',
    articles: [
      { id: '21cfr11',    title: '21 CFR Part 11',       tags: ['cfr', 'fda', 'electronic records', 'signatures'] },
      { id: 'gamp5',      title: 'GAMP 5 Framework',     tags: ['gamp', 'category', 'risk', 'lifecycle'] },
      { id: 'fda-ai-2026',title: 'FDA AI Guidance 2026', tags: ['ai', 'fda', '2026', 'guidance', 'ml'] },
      { id: 'hitl',       title: 'HITL Requirements',    tags: ['human', 'loop', 'hitl', 'approval'] },
      { id: 'audit-trail',title: 'Audit Trail',          tags: ['audit', 'log', 'trail', 'sha256'] },
    ],
  },
  {
    id: 'glossary', title: 'Glossary', icon: '📖',
    articles: [
      { id: 'glossary', title: 'CSV Glossary 2026', tags: ['glossary', 'terms', 'definitions', 'csa'] },
    ],
  },
]

// Flat list for search
const ALL_ARTICLES = NAV.flatMap(s =>
  s.articles.map(a => ({ ...a, sectionTitle: s.title, sectionIcon: s.icon }))
)

// ── Article content database ───────────────────────────────────
const ARTICLES = {

  'platform-overview': {
    title: 'Platform Overview',
    subtitle: 'What is the EVOLV Platform and how does it work?',
    overview: `EVOLV is the world's first end-to-end AI-powered Computer System Validation (CSV) platform built for GAMP 5, CSA, and 21 CFR Part 11 compliance. It replaces fragmented toolchains (Word documents, Veeva Vault, Kneat, SAP GRC) with a single, audit-ready workspace that generates, verifies, tests, and archives validation artefacts in minutes — not weeks.

EVOLV is organised around six core applications, all accessible from a unified shell: Validation Factory, Project Navigator, Dev Portal, Academy, Config, and Impact Analytics.`,
    advantage: {
      headline: 'Why EVOLV replaces your entire legacy stack',
      points: [
        'One login. One audit trail. One source of truth across all validation artefacts.',
        'EVOLV AI generates requirements, test scripts, and reports — SMEs review and approve, not write.',
        'Every AI decision is SHA-256 hashed and archived with full reasoning chain for FDA inspection.',
        'Multi-site, multi-regulation: each site gets its own compliance mode, nomenclature, and ABAC policy.',
        'EVOLV Connect integrates natively with SAP S/4HANA, Salesforce Health Cloud, and Veeva Vault.',
      ],
    },
    steps: [
      { n: '1', title: 'Log in', desc: 'Access EVOLV at your tenant URL. MFA is enforced for all GxP users per 21 CFR Part 11 §11.10(d).' },
      { n: '2', title: 'Open Validation Factory', desc: 'Click the 🏭 icon on the Home LaunchPad or sidebar to open the Validation Factory in a new tab.' },
      { n: '3', title: 'Enter a requirement', desc: 'Type or paste a natural-language requirement. EVOLV AI queries the GAMP 5 knowledge base and returns an audit-ready URS in seconds.' },
      { n: '4', title: 'Review and approve', desc: 'A Human-in-the-Loop (HITL) approval step is required for all GxP-Direct requirements per FDA AI Guidance 2026.' },
      { n: '5', title: 'Export', desc: 'Download a 21 CFR Part 11 compliant Validation Report PDF with Manifestation of Signature.' },
    ],
    regulatory: [
      { ref: '21 CFR Part 11 §11.10', desc: 'Controls for closed electronic record systems — access control, audit trails, e-signatures.' },
      { ref: 'GAMP 5 Chapter 3',      desc: 'Risk-based approach to CSV; fit-for-purpose validation.' },
      { ref: 'FDA CSA Guidance 2022', desc: 'Computer Software Assurance — outcome-focused testing vs. scripted-only approach.' },
      { ref: 'FDA AI/ML Guidance 2026', desc: 'Human-in-the-Loop requirements for AI-assisted regulated decisions.' },
    ],
    tryIt: { label: 'Open Validation Factory', appId: 'verify' },
  },

  'quick-start': {
    title: 'Quick Start Guide',
    subtitle: 'From zero to your first AI-generated URS in under 5 minutes.',
    overview: `This guide walks you through generating your first GAMP 5-compliant User Requirements Specification (URS) using EVOLV AI. No prior experience with CSV documentation is required. EVOLV AI handles regulatory context retrieval, criticality classification, and rationale generation automatically.`,
    advantage: {
      headline: 'Traditional onboarding vs. EVOLV',
      points: [
        'Legacy: 2-day SME onboarding, GAMP 5 manual reading, template downloads.',
        'EVOLV: First audit-ready URS generated in under 5 minutes.',
        'EVOLV Academy embedded in-platform — learn GAMP 5 as you work.',
        'The SMART Transformer corrects vague requirements in real-time, training users by example.',
      ],
    },
    steps: [
      { n: '1', title: 'Open Validation Factory', desc: 'From the Home LaunchPad, click 🏭 Validation Factory.' },
      { n: '2', title: 'Navigate to "Generate Requirements"', desc: 'Select the "Generate Requirements" section from the left-hand page menu inside Validation Factory.' },
      { n: '3', title: 'Describe your system', desc: 'In the System Description field, enter a brief description of the system being validated (e.g., "LabCore LIMS v4.2 — cloud-hosted laboratory information management system").' },
      { n: '4', title: 'Enter a requirement', desc: 'Type a natural-language requirement: "The system should track warehouse temperature." EVOLV AI will transform and verify this against the GAMP 5 knowledge base.' },
      { n: '5', title: 'Select Risk Classification', desc: 'Choose the GxP category (Direct / Indirect / None) and Implementation Method (Configured / Custom / OotB).' },
      { n: '6', title: 'Generate URS', desc: 'Click "Generate URS." EVOLV AI returns a structured URS with Criticality, Regulatory Rationale, and Reg Versions Cited within 30 seconds.' },
      { n: '7', title: 'Download PDF', desc: 'Click "Download PDF" to receive a 21 CFR Part 11 compliant document with Manifestation of Signature.' },
    ],
    regulatory: [
      { ref: 'GAMP 5 §5.4', desc: 'User Requirements Specification must be defined before system design.' },
      { ref: '21 CFR Part 11 §11.50', desc: 'Electronic signatures must include signer name, date/time, and meaning of signature.' },
    ],
    tryIt: { label: 'Try it in Validation Factory', appId: 'verify' },
  },

  'smart-requirements': {
    title: 'SMART Requirements Engine',
    subtitle: 'Transform vague, ambiguous requirements into audit-ready GAMP 5 specifications.',
    overview: `The SMART Requirements Engine is an EVOLV AI module that detects ambiguous language, missing regulatory controls, and untestable criteria in user-written requirements — then rewrites them to SMART format (Specific, Measurable, Achievable, Relevant, Time-bound) with full GAMP 5 and 21 CFR Part 11 traceability embedded.

Every SMART requirement output includes: a measurable acceptance criterion in Given/When/Then format, a risk classification (GxP Direct / Indirect / None), an implementation method classification, and the applicable regulatory citation.`,
    advantage: {
      headline: 'Why EVOLV\'s approach is 100x better than manual rewrites',
      points: [
        'Legacy SME rewrite: 15–45 minutes per requirement, no regulatory cross-reference, inconsistent across authors.',
        'EVOLV SMART Engine: <30 seconds per requirement, GAMP 5 Pinecone context embedded, consistent every time.',
        'Negative test scenarios auto-generated for HIGH-risk requirements — something legacy tools never do.',
        'FDA/EMA 2026 AI Guidance trigger detection: automatically flags requirements that will need HITL approval.',
        'Side-by-side comparison mode shows exactly what changed and why — full audit trail of the transformation.',
      ],
    },
    steps: [
      { n: '1', title: 'Open SMART Requirements',       desc: 'Navigate to Validation Factory → Page 12 (SMART Requirements Engine).' },
      { n: '2', title: 'Enter your requirement',         desc: 'Type or paste a vague requirement into the input field. Example: "The system should handle user data safely."' },
      { n: '3', title: 'Select GxP Context',             desc: 'Choose your site\'s GxP classification and system category. This drives risk keyword detection.' },
      { n: '4', title: 'Click "EVOLV Transform"',        desc: 'EVOLV AI applies vague-word substitution, adds measurable thresholds, inserts the "The system shall" prefix, and retrieves regulatory citations from Pinecone.' },
      { n: '5', title: 'Review SMART output',            desc: 'Inspect the transformed requirement, acceptance criteria, and risk level. Edit inline if needed.' },
      { n: '6', title: 'HITL Approval',                 desc: 'For GxP-Direct requirements, a qualified reviewer must approve before the requirement is locked.' },
      { n: '7', title: 'Export to Generate Reqs',        desc: 'Click "Export to Generate Requirements" to pass the SMART requirement into the URS generation pipeline.' },
    ],
    regulatory: [
      { ref: 'GAMP 5 Chapter 5',       desc: 'Requirements must be unambiguous, testable, and traceable to business need.' },
      { ref: 'FDA CSA Guidance 2022',  desc: 'Outcomes-focused documentation; requirements must have measurable acceptance criteria.' },
      { ref: '21 CFR Part 11 §11.10(e)', desc: 'Audit trail must capture the original and revised requirement text with timestamp.' },
      { ref: 'FDA AI/ML Guidance 2026 §3.2', desc: 'AI-rewritten requirements for GxP-Direct systems require human review and documented approval.' },
    ],
    tryIt: { label: 'Open SMART Requirements Sandbox', appId: 'academy' },
    callouts: [
      { type: 'tip',     text: 'Use the Academy sandbox to practice the SMART Engine on bad requirements before working with real project data.' },
      { type: 'warning', text: 'Do not export a SMART requirement to URS generation without HITL approval for GxP-Direct items. This will create a compliance exception in the audit trail.' },
    ],
  },

  'urs-generation': {
    title: 'URS Generation',
    subtitle: 'AI-generated User Requirements Specifications grounded in live GAMP 5 regulatory context.',
    overview: `EVOLV's RequirementArchitect agent generates structured URS documents from natural-language input by querying a Pinecone vector database populated with GAMP 5 Rev 2 and CSA guidance. Every URS includes a Criticality classification (High/Medium/Low), a Regulatory Rationale with page-level citations, and a list of Regulatory Versions Cited.

Unlike Word template-based approaches, EVOLV URS documents are generated fresh from the knowledge base every time — ensuring regulatory currency regardless of when your GAMP 5 binder was last updated.`,
    advantage: {
      headline: 'Generated in seconds. Audit-ready by design.',
      points: [
        'Legacy: SME writes from memory. Regulatory rationale is often omitted or incorrect.',
        'EVOLV: Every URS rationale cites the specific GAMP 5 page and regulatory version — traceable to source.',
        'Pinecone similarity threshold 0.45 enforced — if GAMP 5 context score is below threshold, generation is blocked and RegulatoryContextNotFoundError is raised.',
        'Criticality auto-classified by keyword detection (patient, safety, batch release, clinical, GxP, etc.).',
        'Reg_Versions_Cited field tracks which regulatory document versions were consulted — essential for regulatory version change management.',
      ],
    },
    steps: [
      { n: '1', title: 'Describe your requirement',    desc: 'Enter a natural-language requirement. E.g., "The system shall track warehouse temperature with alerts for excursions above 25°C."' },
      { n: '2', title: 'EVOLV AI queries Pinecone',    desc: 'RequirementArchitect embeds your input using text-embedding-3-small and retrieves the top-5 GAMP 5 chunks above similarity threshold 0.45.' },
      { n: '3', title: 'Criticality classification',  desc: 'EVOLV classifies criticality by keyword scanning: HIGH (patient, batch, GxP), MEDIUM (quality, audit, CAPA), LOW (administrative).' },
      { n: '4', title: 'Rationale construction',      desc: 'Regulatory Rationale is built from retrieved chunks: "Per GAMP5_Guide.pdf [GAMP5_Rev2] (p.42): ..."' },
      { n: '5', title: 'URS output',                  desc: 'Returns structured URS_ID, Requirement_Statement, Criticality, Regulatory_Rationale, Reg_Versions_Cited.' },
      { n: '6', title: 'Verification (auto)',          desc: 'VerificationAgent automatically runs 3 checks: Criticality Alignment, Rationale Relevance, Contradiction Scan.' },
      { n: '7', title: 'Download PDF',                desc: 'Export the approved URS as a 21 CFR Part 11 compliant PDF with Manifestation of Signature.' },
    ],
    regulatory: [
      { ref: 'GAMP 5 §5.4.3',    desc: 'URS must define WHAT the system needs to do, not HOW it does it.' },
      { ref: 'GAMP 5 Appendix S2', desc: 'URS must be developed and approved before detailed design.' },
      { ref: 'FDA CSA §IV.A',    desc: 'Requirements must be traceable from business need through to testing.' },
    ],
    tryIt: { label: 'Open Validation Factory', appId: 'verify' },
  },

  'ur-fr': {
    title: 'UR/FR Transformation',
    subtitle: 'Deterministic decomposition of a URS into User Requirements and Functional Requirements with risk matrix.',
    overview: `The transform_urs_to_ur_fr() function takes an approved URS document and deterministically produces a structured UR/FR document — no LLM calls required. Risk level is computed from a 3×3 matrix (GxP category × Implementation Method). Test strategy is then derived from a Risk × Implementation Method matrix.

This deterministic approach is intentional: UR/FR transformation is a regulated artefact and must produce the same output for the same inputs, every time, without AI variance.`,
    advantage: {
      headline: '100% deterministic. Fully traceable. Zero variance.',
      points: [
        'Legacy: Protocol writers manually determine risk level — inconsistent across projects and authors.',
        'EVOLV: Risk level is computed from a defined matrix and logged to the audit trail — consistent, defensible, traceable.',
        'FR decomposition is rule-based: each URS generates at least one FR with Given/When/Then acceptance criteria.',
        'Shadow Links automatically created in Project Navigator when a URS is added to a project folder.',
        'Additional context (System Description, Workshop Notes, Lucidchart diagrams) is embedded in the UR/FR output.',
      ],
    },
    steps: [
      { n: '1', title: 'Select GxP Category',           desc: 'Choose: GxP Direct, GxP Indirect, or GxP None. This is the first axis of the risk matrix.' },
      { n: '2', title: 'Select Implementation Method',  desc: 'Choose: Custom, Configured, or Out-of-the-Box. This is the second axis.' },
      { n: '3', title: 'Risk level computed',           desc: 'EVOLV computes risk: Custom+GxP Direct=HIGH, Configured+GxP Direct=HIGH, OotB+GxP Indirect=LOW, etc.' },
      { n: '4', title: 'Test strategy derived',         desc: 'HIGH risk → OQ and/or UAT. MEDIUM/LOW → Supplier Provided or Informal testing.' },
      { n: '5', title: 'FR decomposition',              desc: 'Each URS statement is decomposed into functional requirements with acceptance criteria in Given/When/Then format.' },
      { n: '6', title: 'Review and export',             desc: 'Review the UR/FR document and export to Validation Report PDF or pass to DeltaAgent for test script generation.' },
    ],
    regulatory: [
      { ref: 'GAMP 5 Chapter 6',   desc: 'Functional Specifications describe HOW the system will meet the URS.' },
      { ref: 'GAMP 5 Appendix O4', desc: 'Risk assessment must be documented and linked to test strategy.' },
      { ref: 'FDA CSA §IV.B',      desc: 'Testing effort must be proportional to risk — high risk warrants scripted OQ/UAT.' },
    ],
    tryIt: { label: 'Open Validation Factory', appId: 'verify' },
  },

  'verification-agent': {
    title: 'Verification Agent',
    subtitle: 'Automated 3-point GAMP 5 compliance check on every generated URS.',
    overview: `The VerificationAgent runs three independent compliance checks against every URS before it can be approved: (1) Criticality Alignment — detects under-classification by scanning GAMP 5 chunks for high-risk indicators; (2) Rationale Relevance — verifies the Pinecone similarity score meets the relevance threshold of 0.45; (3) Contradiction Scan — matches known contradiction phrase pairs against GAMP 5 regulatory text.

A URS that fails any check receives Verdict: Rejected and a COMPLIANCE_EXCEPTION is logged to the audit trail. It cannot be exported until the finding is resolved.`,
    advantage: {
      headline: 'Zero compliance exceptions at inspection — guaranteed by design.',
      points: [
        'Legacy: Compliance exceptions discovered during FDA inspection — months after the URS was written.',
        'EVOLV: Compliance exceptions caught before the URS leaves the generation pipeline.',
        'Contradiction Scan blocks requirements that contain phrases like "skip validation" or "disable audit trail" — protecting against accidental non-compliance.',
        'All three check results are logged to the audit trail with GAMP 5 citations — inspection-ready by design.',
        'Batch verification supports entire URS sets: verify_batch([urs1, urs2, ...]).',
      ],
    },
    steps: [
      { n: '1', title: 'Automatic trigger',       desc: 'VerificationAgent runs automatically after every URS generation. No manual action required.' },
      { n: '2', title: 'Criticality Alignment',   desc: 'EVOLV scans retrieved GAMP 5 chunks for HIGH-risk indicators (patient, safety, batch release, 21 CFR Part 11). If found and criticality is Medium/Low, check FAILS.' },
      { n: '3', title: 'Rationale Relevance',     desc: 'Best Pinecone match score must be ≥ 0.45. Below threshold means the requirement has no credible GAMP 5 basis — check FAILS.' },
      { n: '4', title: 'Contradiction Scan',       desc: 'Requirement text is scanned for contradiction phrase pairs. "No audit trail" vs. GAMP 5 "audit trail required" → check FAILS.' },
      { n: '5', title: 'Verdict issued',           desc: 'APPROVED (all three pass) or REJECTED (any failure). Rejected URS shows findings with GAMP 5 citations.' },
      { n: '6', title: 'Resolve findings',         desc: 'Edit the requirement to address findings, then re-generate. New verification run is triggered automatically.' },
    ],
    regulatory: [
      { ref: 'GAMP 5 Chapter 5.4',    desc: 'Requirements must be verifiable and consistent with regulatory guidance.' },
      { ref: '21 CFR Part 11 §11.10(e)', desc: 'All changes to electronic records must be logged with prior and new value.' },
      { ref: 'FDA CSA §V',            desc: 'Verification activities must be documented and traceable.' },
    ],
    callouts: [
      { type: 'warning', text: 'A COMPLIANCE_EXCEPTION audit event is immutable. It cannot be deleted from the audit trail — only resolved by a new approved URS.' },
    ],
  },

  'csa-test-scripts': {
    title: 'CSA Test Scripts',
    subtitle: 'Risk-stratified test script generation aligned to FDA Computer Software Assurance guidance.',
    overview: `DeltaAgent generates CSA-aligned test scripts from UR/FR documents. Scripts are fully deterministic — no LLM calls — ensuring regulatory reproducibility. Test type is automatically routed by risk level: HIGH risk → Informal / Formal OQ / Formal UAT with positive, negative, and edge-case steps. MEDIUM/LOW risk → Unscripted Exploratory Charter with tester-expertise-guided steps.

Every step is structured: Type (Setup/Execution), Step Number, Title, Instruction, Expected Result, Test Case Type (Positive/Negative/Edge Case), and Requirement Reference (UR-1 / FR-1).`,
    advantage: {
      headline: 'Positive-only testing is a compliance risk. EVOLV eliminates it.',
      points: [
        'Legacy: Protocol writers generate positive-only test steps. Negative and edge-case coverage missing at OQ — caught at inspection.',
        'EVOLV: Every HIGH-risk UR/FR generates positive + negative + edge-case execution steps automatically.',
        'CSA routing: testing effort is proportional to risk — not driven by organisational habit.',
        'Script quality checklist embedded in every output: steps_clear_and_sequential, expected_results_observable, no_redundant_steps.',
        'Batch generation: generate_csa_test_batch([ur_fr_list]) for entire validation packages.',
      ],
    },
    steps: [
      { n: '1', title: 'Complete UR/FR Transformation',   desc: 'DeltaAgent requires a complete UR/FR document as input. Complete the UR/FR step first.' },
      { n: '2', title: 'Select test type',                desc: 'Choose: Informal, Formal OQ, or Formal UAT. EVOLV AI recommends based on risk level.' },
      { n: '3', title: 'Setup steps generated',           desc: 'Common setup steps: Login as System Owner, Navigate to module, Prepare test data.' },
      { n: '4', title: 'Execution steps generated',       desc: 'HIGH risk: positive + negative + edge case per FR. MEDIUM/LOW: exploratory charter steps.' },
      { n: '5', title: 'Review and annotate',             desc: 'Review each step. Add tester notes, expected result refinements, or screenshots.' },
      { n: '6', title: 'Export Validation Report',        desc: 'Pass the test script to generate_validation_report_pdf() for the complete 5-page Validation Report PDF.' },
    ],
    regulatory: [
      { ref: 'FDA CSA Guidance 2022 §IV.C', desc: 'Test effort must be proportional to risk. Scripted testing required only where risk justifies it.' },
      { ref: 'GAMP 5 Appendix O5',          desc: 'Test scripts must include expected results and pass/fail criteria.' },
      { ref: '21 CFR Part 11 §11.10(e)',    desc: 'Test execution records are electronic records subject to audit trail requirements.' },
    ],
    tryIt: { label: 'Open Validation Factory', appId: 'verify' },
  },

  'validation-report': {
    title: 'Validation Report PDF',
    subtitle: '5-page, 21 CFR Part 11 compliant Validation Report with Manifestation of Signature.',
    overview: `generate_validation_report_pdf() produces a complete validation package in under 3 seconds: Cover Page (portrait) with summary metadata → UR/FR Table (landscape) → Test Script Table (landscape) → Regulatory Justification (portrait) → Manifestation of Signature (portrait).

The Manifestation of Signature page satisfies 21 CFR Part 11 §11.50: it displays the document reference, signer full name, UTC timestamp, and the meaning of the electronic signature. This is the legally required "manifestation" that must accompany any electronic signature on a regulated document.`,
    advantage: {
      headline: '3 seconds. 5 pages. Inspection-ready.',
      points: [
        'Legacy: Validation report assembled manually — 2–3 days of copy-paste, formatting, and wet-signature scanning.',
        'EVOLV: 3 seconds. Branded, structured, tamper-evident PDF with embedded audit trail reference.',
        'Landscape UR/FR and test script tables — professional format that mirrors what regulators expect.',
        'Regulatory Justification page pulls the full GAMP 5 rationale from the URS — nothing needs to be re-typed.',
        'Signature page is audit-trailed: the signing event is logged to the CSV audit trail with SHA-256 hash.',
      ],
    },
    steps: [
      { n: '1', title: 'Complete the pipeline',    desc: 'Generate URS → UR/FR → Test Script. All three artefacts are required for the full Validation Report.' },
      { n: '2', title: 'Enter signer details',     desc: 'Enter the approver\'s full name and the meaning of the signature (e.g., "Approval of Validation Report").' },
      { n: '3', title: 'Click Download',           desc: 'Click "Download Validation Report PDF." The 5-page PDF is generated and the signing event is logged.' },
      { n: '4', title: 'File in system',           desc: 'Upload the signed PDF to your document management system (Veeva Vault, SharePoint, etc.). Cross-reference the audit trail hash.' },
    ],
    regulatory: [
      { ref: '21 CFR Part 11 §11.50', desc: 'Signed electronic records must display the signer\'s printed name, date and time, and meaning of signature.' },
      { ref: '21 CFR Part 11 §11.70', desc: 'Electronic signatures must be linked to their records to prevent excision, copying, or falsification.' },
      { ref: 'GAMP 5 §5.4.7',        desc: 'Validation documentation must be reviewed and approved before system go-live.' },
    ],
    tryIt: { label: 'Open Validation Factory', appId: 'verify' },
  },

  'api-keys': {
    title: 'API Key Management',
    subtitle: 'Scoped, environment-specific API keys with copy-once reveal and audit-trailed revocation.',
    overview: `EVOLV API keys are scoped (full_access, audit_only, bulk_only), environment-typed (Production or Sandbox), and tenant-specific. The raw key is shown exactly once after generation — it is never stored in EVOLV systems. Only key metadata (key_id, tenant_id, scopes, created_at) is persisted.

All key generation and revocation events are logged to the 21 CFR Part 11 audit trail. For regulated integrations, use Production keys only in validated, access-controlled environments.`,
    advantage: {
      headline: 'Never store a plaintext key. Never share a production key.',
      points: [
        'Copy-once reveal: raw key shown once, never retrievable again. Forces secure key management.',
        'Sandbox vs. Production environments: Sandbox keys hit demo data; Production keys access live regulated records.',
        'Scope restriction: audit_only keys can read but never modify regulated records — ideal for reporting integrations.',
        'Every key event (generate, revoke) is audit-trailed with user_id, timestamp, and tenant_id.',
      ],
    },
    steps: [
      { n: '1', title: 'Open Dev Portal → API Keys', desc: 'Navigate to Dev Portal from the sidebar. Select the "🔑 API Keys" tab.' },
      { n: '2', title: 'Select environment',          desc: 'Toggle between 🧪 Sandbox (for development) and 🔴 Production (for validated integrations).' },
      { n: '3', title: 'Set Tenant ID and Scope',    desc: 'Enter your tenant ID and select the minimum required scope for your integration.' },
      { n: '4', title: 'Generate Key',               desc: 'Click "⚡ Generate Key." The raw key appears once — copy it immediately.' },
      { n: '5', title: 'Store securely',             desc: 'Store the key in your secrets manager (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault). Never in source code.' },
      { n: '6', title: 'Revoke when done',           desc: 'Revoke keys that are no longer needed. Revocation is immediate and logged.' },
    ],
    regulatory: [
      { ref: '21 CFR Part 11 §11.10(d)', desc: 'System access must be limited to authorised individuals — API keys are access credentials.' },
      { ref: '21 CFR Part 11 §11.10(g)', desc: 'Authority checks must ensure only authorised individuals use the system.' },
    ],
    tryIt: { label: 'Open Dev Portal', appId: 'dev-portal' },
    callouts: [
      { type: 'warning', text: 'Never use Production keys in development or CI/CD pipelines. A Production key that touches live regulated data creates an audit trail entry for every API call.' },
    ],
  },

  'evolv-connect': {
    title: 'EVOLV Connect Integrations',
    subtitle: 'Pre-built, HMAC-signed integrations for the pharma and life-sciences tech stack.',
    overview: `EVOLV Connect provides production-ready integrations with SAP S/4HANA (via REST + OData), Salesforce Health Cloud (via REST + Apex), Veeva Vault (via Vault REST API), ServiceNow GRC (native webhook receiver), with Jira and Azure DevOps coming in Q3 2026.

All integration events are HMAC-SHA256 signed, ensuring payload integrity. Retry logic handles transient failures: 1 minute → 5 minutes → 15 minutes.`,
    advantage: {
      headline: 'Real-time. Bidirectional. Native.',
      points: [
        'Legacy: Weekly CSV exports between SAP and validation tools. Change requests arrive 3–5 days late.',
        'EVOLV: ServiceNow CRs assessed by EVOLV AI in <2 seconds via native webhook. Risk level returned before the CR is even triaged.',
        'Veeva Vault auto-filing: EVOLV-generated URS, test scripts, and reports filed directly into Vault document workflows.',
        'SAP GRC bidirectional sync: validation milestones and compliance status flow both ways.',
        'HMAC-SHA256 payload signing: every event payload is cryptographically verified — no spoofing possible.',
      ],
    },
    steps: [
      { n: '1', title: 'Open Dev Portal → EVOLV Connect', desc: 'Navigate to Dev Portal → "🔗 EVOLV Connect" tab.' },
      { n: '2', title: 'Select integration',              desc: 'Click "Connect" on the target system (e.g., SAP S/4HANA).' },
      { n: '3', title: 'Configure endpoints',             desc: 'Expand "Show config" to see the EVOLV inbound webhook URL and your system\'s outbound URL.' },
      { n: '4', title: 'Set HMAC secret',                 desc: 'Configure a shared HMAC-SHA256 secret in both EVOLV and the target system.' },
      { n: '5', title: 'Test with Sandbox key',           desc: 'Use a Sandbox API key to test the integration against demo data before enabling Production.' },
      { n: '6', title: 'Enable Production',               desc: 'Switch to a Production API key after validation testing is complete.' },
    ],
    regulatory: [
      { ref: '21 CFR Part 11 §11.10(h)', desc: 'System checks must ensure valid record transmission — HMAC signing satisfies this.' },
      { ref: 'GAMP 5 §4.3',             desc: 'Interfaces between validated systems must be assessed and documented.' },
    ],
    tryIt: { label: 'Open Dev Portal', appId: 'dev-portal' },
  },

  'webhooks': {
    title: 'Webhooks',
    subtitle: 'Register event-driven endpoints to receive real-time EVOLV notifications.',
    overview: `EVOLV webhooks deliver real-time event payloads to registered endpoints when key validation events occur. Supported events: SENTINEL_SCAN_COMPLETED, BULK_VALIDATE_COMPLETE, CHANGE_REQUEST_ASSESSED. Payloads are HMAC-SHA256 signed using the secret you register. Failed deliveries are retried at 1 minute, 5 minutes, and 15 minutes.`,
    advantage: {
      headline: 'Event-driven validation — no polling required.',
      points: [
        'Push-based: your system knows about a CHANGE_REQUEST_ASSESSED event in <100ms, not on next business day.',
        'HMAC signing: every payload includes an X-EVOLV-Signature header for cryptographic verification.',
        'Retry logic handles transient downstream failures without data loss.',
      ],
    },
    steps: [
      { n: '1', title: 'Register endpoint',    desc: 'Dev Portal → 🪝 Webhooks. Enter your HTTPS endpoint URL, select the event, and enter your HMAC secret.' },
      { n: '2', title: 'Verify signature',     desc: 'On receipt, compute HMAC-SHA256 of the raw payload body using your secret and compare to X-EVOLV-Signature header.' },
      { n: '3', title: 'Return 200 quickly',  desc: 'Return HTTP 200 within 5 seconds. Process the payload asynchronously. Slow responses trigger retries.' },
    ],
    regulatory: [
      { ref: '21 CFR Part 11 §11.10(h)', desc: 'System checks must ensure valid source and complete, unaltered transmission of records.' },
    ],
    tryIt: { label: 'Open Dev Portal', appId: 'dev-portal' },
  },

  '21cfr11': {
    title: '21 CFR Part 11',
    subtitle: 'FDA regulation governing electronic records and electronic signatures in regulated industries.',
    overview: `21 CFR Part 11 (Title 21, Code of Federal Regulations, Part 11) establishes the criteria under which the FDA considers electronic records, electronic signatures, and handwritten signatures executed to electronic records to be trustworthy, reliable, and equivalent to paper records and handwritten signatures.

EVOLV is designed from the ground up to satisfy every applicable §11.10 control for closed systems — the category that applies to all EVOLV-managed records.`,
    advantage: {
      headline: 'Every EVOLV record satisfies 21 CFR Part 11 by design.',
      points: [
        '§11.10(a) — Validation: EVOLV itself is validated per GAMP 5 Category 4 (Configured Software).',
        '§11.10(b) — Legibility: All records are stored in structured, human-readable format (JSON/CSV/PDF).',
        '§11.10(c) — Retrieval: All records retrievable by audit event, user_id, timestamp, and action.',
        '§11.10(d) — Access: RBAC + MFA enforced. API keys are scoped and revocable.',
        '§11.10(e) — Audit trail: SHA-256 hashed, append-only CSV audit trail. Every AI decision archived with reasoning chain.',
        '§11.10(g) — Authority checks: ABAC policy prevents unauthorised access regardless of role.',
        '§11.50 — Manifestation of Signature: Every PDF includes signer name, date/time, and meaning.',
      ],
    },
    steps: [
      { n: '1', title: 'Understand scope',         desc: '21 CFR Part 11 applies to electronic records that are: created, modified, maintained, archived, retrieved, or transmitted under FDA requirements.' },
      { n: '2', title: 'Confirm system category',  desc: 'EVOLV is a closed system (§11.10). Access is controlled by EVOLV — external users cannot directly access the records layer.' },
      { n: '3', title: 'Verify audit trail',       desc: 'Confirm the audit trail captures: who (user_id), what (action), when (timestamp), and why (decision_logic) for every regulated operation.' },
      { n: '4', title: 'Confirm e-signature setup', desc: 'All PDF exports include a Manifestation of Signature page. The signing event is logged to the audit trail.' },
    ],
    regulatory: [
      { ref: '21 CFR Part 11 §11.10', desc: 'Controls for closed systems — the section EVOLV fully implements.' },
      { ref: '21 CFR Part 11 §11.50', desc: 'Signed electronic records must display printed name, date/time, and meaning.' },
      { ref: 'FDA Guidance (2003)',    desc: 'FDA Guidance for Industry: Part 11, Electronic Records — Scope and Application.' },
    ],
  },

  'gamp5': {
    title: 'GAMP 5 Framework',
    subtitle: 'Risk-based approach to computer system validation from ISPE.',
    overview: `GAMP 5 (Good Automated Manufacturing Practice, 5th edition — updated as GAMP 5 Rev 2 in 2022) provides a pragmatic, risk-based framework for the validation of automated systems in regulated industries. The core principle: validation effort must be proportional to the risk the system poses to product quality and patient safety.

GAMP 5 classifies software into categories: Category 1 (Infrastructure), Category 3 (Non-configured products), Category 4 (Configured products), Category 5 (Custom software). EVOLV is Category 4.`,
    advantage: {
      headline: 'EVOLV speaks GAMP 5 natively.',
      points: [
        'Every URS, UR/FR, and test script is grounded in GAMP 5 guidance retrieved live from Pinecone.',
        'Risk classification uses GAMP 5 Severity × Occurrence × Detectability = RPN methodology.',
        'CSA testing strategies (Unscripted/Hybrid/Scripted) are mapped to GAMP 5 risk levels.',
        'Project Navigator folder structure mirrors GAMP 5 V-model lifecycle: URS → FS → CS → IQ/OQ/PQ.',
        'VerificationAgent checks every URS against GAMP 5 text — not against an SME\'s memory.',
      ],
    },
    steps: [
      { n: '1', title: 'Classify your system',   desc: 'Determine GAMP 5 category: Cat 1 (OS/network), Cat 3 (standard packages), Cat 4 (configured), Cat 5 (custom). Most validated LIMS/ERP systems are Cat 4.' },
      { n: '2', title: 'Define URS',             desc: 'Document WHAT the system must do. EVOLV generates this from natural language.' },
      { n: '3', title: 'Perform risk assessment', desc: 'Assess each requirement: Severity (impact on patient/quality), Occurrence (likelihood of failure), Detectability.' },
      { n: '4', title: 'Define test strategy',   desc: 'Higher RPN → more scripted testing. EVOLV automates this mapping via DeltaAgent.' },
      { n: '5', title: 'Execute and document',   desc: 'Execute test scripts, record results, and archive the Validation Report PDF.' },
    ],
    regulatory: [
      { ref: 'GAMP 5 Rev 2 (2022)', desc: 'Current ISPE GAMP 5 guidance — the version cited in all EVOLV-generated documents.' },
      { ref: 'GAMP 5 Chapter 5',    desc: 'Good Practice Guide: life cycle approach to GxP systems.' },
      { ref: 'ICH Q9',              desc: 'Quality Risk Management — underpins GAMP 5 risk methodology.' },
    ],
  },

  'fda-ai-2026': {
    title: 'FDA AI Guidance 2026',
    subtitle: 'Regulatory requirements for AI/ML-assisted decisions in FDA-regulated environments.',
    overview: `In 2026, the FDA issued comprehensive guidance on the use of Artificial Intelligence and Machine Learning in regulated industries. The guidance establishes mandatory Human-in-the-Loop (HITL) requirements for AI-assisted decisions that affect product quality, patient safety, or regulatory submissions. EVOLV implements these requirements natively.

Key requirement: any AI-generated artefact that is GxP-Direct must receive documented human review and approval before it is used in a regulated context. The AI reasoning must be transparent, auditable, and explainable.`,
    advantage: {
      headline: 'EVOLV was built for the AI regulation era.',
      points: [
        'AI reasoning transparency: every EVOLV AI decision includes full input → reasoning → output chain archived in a tamper-evident Logic Archive.',
        'HITL enforcement: GxP-Direct requirements cannot be exported without a human approval event logged in the audit trail.',
        'HITL badge pulsing in Project Navigator — visual indicator that an item awaits human review.',
        'No AI hallucination risk for URS: if Pinecone similarity score < 0.45, generation is blocked.',
        'EVOLV AI version tracking: every generated artefact records which model version produced it.',
      ],
    },
    steps: [
      { n: '1', title: 'Identify AI-assisted decisions', desc: 'Any EVOLV AI output used in a GxP context (URS, test script, risk assessment) is subject to FDA AI Guidance 2026.' },
      { n: '2', title: 'Ensure HITL approval',            desc: 'A qualified human must review and approve each GxP-Direct AI output. The approval is logged with user_id, timestamp, and approval statement.' },
      { n: '3', title: 'Document AI reasoning',           desc: 'The Logic Archive JSON file (generated by IntegrityManager) serves as the required AI reasoning documentation.' },
      { n: '4', title: 'Version tracking',                desc: 'Record which EVOLV version and which AI model version generated each artefact. This is embedded in every PDF footer.' },
    ],
    regulatory: [
      { ref: 'FDA AI/ML Guidance 2026 §3.2', desc: 'AI-assisted decisions affecting patient safety require documented human oversight.' },
      { ref: 'FDA AI/ML Guidance 2026 §4.1', desc: 'AI reasoning must be transparent, auditable, and explainable to regulators.' },
      { ref: 'FDA AI/ML Guidance 2026 §5',   desc: 'AI-generated regulated documents must track model version and generation parameters.' },
    ],
    callouts: [
      { type: 'warning', text: 'Using an EVOLV AI-generated URS in a GxP-Direct context without HITL approval creates a compliance exception. This is flagged in the audit trail and cannot be retroactively cleared.' },
      { type: 'tip',     text: 'Use the Project Navigator HITL badges to identify and action pending approvals before your next audit.' },
    ],
    tryIt: { label: 'Open Project Navigator', appId: 'navigator' },
  },

  'hitl': {
    title: 'HITL Requirements',
    subtitle: 'Human-in-the-Loop: mandatory human oversight for AI-assisted GxP decisions.',
    overview: `Human-in-the-Loop (HITL) is the FDA AI Guidance 2026 §3.2 requirement that a qualified human must review, evaluate, and explicitly approve any AI-generated artefact before it is used in a GxP-regulated context. In EVOLV, HITL is enforced at the system level — not left to organisational habit.

In Project Navigator, items awaiting HITL approval display a pulsing 🤖 badge. Approving an item via the PATCH /items/{id}/approve endpoint logs the event to the audit trail with the reviewer's user_id, timestamp, and approval statement.`,
    advantage: {
      headline: 'HITL is enforced. Not suggested.',
      points: [
        'GxP-Direct items cannot be exported, filed, or marked "approved" without a HITL event logged.',
        'Approval is recorded with: reviewer user_id, timestamp (UTC), decision ("Approved as generated" or custom statement).',
        'HITL events appear in the SHA-256 hashed audit trail — tamper-evident and inspection-ready.',
        'Batch approval is not permitted: each artefact requires individual human review — preventing rubber-stamping.',
        'EVOLV tracks HITL approval rate per project — low rates flag process risk.',
      ],
    },
    steps: [
      { n: '1', title: 'AI generates artefact',    desc: 'EVOLV AI generates a URS, UR/FR, or test script. Status: Draft. HITL badge (🤖) appears in Project Navigator.' },
      { n: '2', title: 'Reviewer notified',         desc: 'The assigned reviewer receives a notification. Only users with the "Validator" role can approve GxP-Direct items.' },
      { n: '3', title: 'Review the artefact',       desc: 'Reviewer reads the AI-generated output, cross-checks with the source requirement and GAMP 5 rationale.' },
      { n: '4', title: 'Approve or reject',         desc: 'Click "Approve" in Project Navigator. Status changes from Draft → Approved. HITL badge is removed.' },
      { n: '5', title: 'Audit trail updated',       desc: 'Approval logged: { user_id, timestamp, action: "ITEM_APPROVED", compliance_impact: "HITL Approval" }.' },
    ],
    regulatory: [
      { ref: 'FDA AI/ML Guidance 2026 §3.2', desc: 'Mandatory human oversight for AI decisions affecting regulated outcomes.' },
      { ref: '21 CFR Part 11 §11.10(e)',     desc: 'Audit trail must capture the identity of the individual making each change or approval.' },
    ],
    tryIt: { label: 'Open Project Navigator', appId: 'navigator' },
  },

  'audit-trail': {
    title: 'Audit Trail',
    subtitle: 'SHA-256 hashed, append-only 21 CFR Part 11 compliant audit trail with AI Logic Archives.',
    overview: `EVOLV's IntegrityManager maintains a central append-only CSV audit trail at output/audit_trail.csv. Every row is SHA-256 hashed over: timestamp, user_id, agent_name, action, decision_logic, compliance_impact. The hash makes each row tamper-evident — any modification changes the hash.

When EVOLV AI makes a decision, an optional Logic Archive JSON file is written to output/logic_archives/ — a hidden, dot-prefixed file containing the full AI reasoning chain (inputs, steps, outputs) cross-referenced to the CSV row by the SHA-256 hash. This is the EVOLV implementation of FDA AI Guidance 2026 §4.1 reasoning transparency.`,
    advantage: {
      headline: 'An FDA inspector can query any decision in 30 seconds.',
      points: [
        'Append-only: no row can be deleted or modified without the hash chain breaking.',
        'SHA-256 per row: tamper detection without requiring a blockchain.',
        'Logic Archives: full AI reasoning preserved alongside the audit record — unprecedented transparency.',
        'ALCOA+ compliant: Attributable (user_id), Legible, Contemporaneous (UTC timestamp), Original, Accurate.',
        'Every artefact type has a compliance_impact label: "Regulatory Compliance", "Validation Evidence", "HITL Approval", "Compliance Exception".',
      ],
    },
    steps: [
      { n: '1', title: 'Every action auto-logged',   desc: 'No configuration required. Every EVOLV agent action, user approval, and system event is logged automatically.' },
      { n: '2', title: 'Query by event type',         desc: 'Filter audit_trail.csv by action column: URS_GENERATED, HITL_APPROVED, COMPLIANCE_EXCEPTION, etc.' },
      { n: '3', title: 'Verify hash integrity',       desc: 'Re-compute SHA-256 for any row using the same fields. Match = row untampered. Mismatch = integrity violation.' },
      { n: '4', title: 'Access Logic Archives',       desc: 'For AI-generated artefacts, find the corresponding .{ACTION}_{timestamp}_{hash[:8]}.json in output/logic_archives/.' },
      { n: '5', title: 'Export for inspection',       desc: 'The audit_trail.csv is the primary inspection document. Present alongside Logic Archive files for AI decisions.' },
    ],
    regulatory: [
      { ref: '21 CFR Part 11 §11.10(e)', desc: 'Audit trail must be computer-generated, not user-alterable, and retained for the life of the record.' },
      { ref: 'FDA AI/ML Guidance 2026 §4.1', desc: 'AI reasoning must be documented and available to regulators on request.' },
      { ref: 'GAMP 5 §5.4.6',           desc: 'Audit trail must capture all GxP-relevant operations.' },
    ],
    callouts: [
      { type: 'info', text: 'Logic Archive files are hidden (dot-prefixed) by design — they cannot be accidentally opened or modified by end users. Use the EVOLV API or the Project Navigator to access them.' },
    ],
  },

  'glossary': { _special: 'glossary' },
}

// ── Glossary terms ─────────────────────────────────────────────
const GLOSSARY = [
  { term: 'CSV',         full: 'Computer System Validation',           def: 'The documented process of demonstrating that a computerised system consistently meets its intended use and specifications in a regulated environment.' },
  { term: 'CSA',         full: 'Computer Software Assurance',          def: 'FDA\'s 2022 risk-based approach to CSV: outcome-focused, proportional testing. Replaces scripted-only validation where risk doesn\'t justify it.' },
  { term: 'GAMP 5',      full: 'Good Automated Manufacturing Practice', def: 'ISPE guidance (Rev 2, 2022) for risk-based validation of automated systems. Classifies software Cat 1–5. EVOLV is Category 4.' },
  { term: 'HITL',        full: 'Human-in-the-Loop',                    def: 'FDA AI Guidance 2026 §3.2 requirement: a qualified human must review and approve AI-generated GxP artefacts before regulated use.' },
  { term: 'URS',         full: 'User Requirements Specification',       def: 'A regulated document defining WHAT a system must do. Generated by EVOLV RequirementArchitect with live GAMP 5 context.' },
  { term: 'UR/FR',       full: 'User Requirement / Functional Requirement', def: 'Structured decomposition of a URS into user-level requirements (UR) and system-level functional requirements (FR) with risk classification.' },
  { term: 'RPN',         full: 'Risk Priority Number',                  def: 'Severity × Occurrence × Detectability (scale 1–27). EVOLV: RPN ≤ 4 = LOW, 5–12 = MEDIUM, > 12 = HIGH.' },
  { term: 'IQ/OQ/PQ',   full: 'Installation / Operational / Performance Qualification', def: 'Three-phase qualification protocol: IQ verifies installation, OQ verifies operation against specs, PQ verifies performance in actual use.' },
  { term: 'ALCOA+',      full: 'Attributable, Legible, Contemporaneous, Original, Accurate +', def: 'FDA data integrity framework. + Complete, Consistent, Enduring, Available. All EVOLV records satisfy ALCOA+.' },
  { term: 'GxP',         full: 'Good Practice (x = M/L/C/P)',           def: 'Collective term for Good Manufacturing Practice (GMP), Good Laboratory Practice (GLP), Good Clinical Practice (GCP), and Good Pharmacovigilance Practice (GPvP).' },
  { term: 'ABAC',        full: 'Attribute-Based Access Control',        def: 'Access control model that evaluates user attributes (role, training status, site) against policy rules. More flexible than RBAC.' },
  { term: 'RBAC',        full: 'Role-Based Access Control',             def: 'Access model where permissions are assigned to roles, not individuals. 21 CFR Part 11 §11.10(d) requires access limited to authorised individuals.' },
  { term: 'Shadow Link', full: 'EVOLV Traceability Shadow Link',        def: 'Auto-created link in the Project Navigator Traceability Matrix when a URS is added to a project folder. Ensures no requirement exists without a traceability record.' },
  { term: 'Pinecone',    full: 'Pinecone Vector Database',              def: 'EVOLV\'s regulatory knowledge base. GAMP 5 Rev 2 and CSA guidance is ingested as vector embeddings. Minimum similarity score 0.45 enforced for URS generation.' },
  { term: 'Logic Archive', full: 'EVOLV AI Logic Archive',             def: 'Hidden JSON file in output/logic_archives/ containing full AI reasoning chain (inputs, steps, outputs) cross-referenced to the audit trail by SHA-256 hash.' },
  { term: 'SMART',       full: 'Specific, Measurable, Achievable, Relevant, Time-bound', def: 'Requirement quality framework applied by EVOLV\'s SMARTRequirementsEngine. All EVOLV-generated requirements satisfy SMART criteria by design.' },
  { term: 'HMAC',        full: 'Hash-based Message Authentication Code', def: 'Cryptographic signature used by EVOLV webhooks and EVOLV Connect payloads. Verifies that a payload was sent by EVOLV and was not modified in transit.' },
  { term: 'OQ',          full: 'Operational Qualification',             def: 'Testing phase that verifies the system operates according to its functional specifications under all anticipated operating conditions.' },
  { term: 'UAT',         full: 'User Acceptance Testing',               def: 'Business-process-level testing performed by end users to confirm the system meets their requirements in a real-use scenario.' },
  { term: 'V-Model',     full: 'Verification and Validation V-Model',   def: 'GAMP 5 lifecycle model mapping requirements documents to qualification phases: URS→PQ, FS→OQ, DS→IQ.' },
  { term: 'E-Signature', full: 'Electronic Signature (21 CFR Part 11)', def: 'A computer data compilation that is the legally binding equivalent of a handwritten signature, governed by 21 CFR Part 11 §11.50.' },
  { term: 'Blast Radius', full: 'EVOLV Blast Radius Analysis',         def: 'SentinelImpactAgent assessment of how many linked requirements, test scripts, and documents are affected by a given change — propagated via Shadow Links.' },
]

// ── Callout box ────────────────────────────────────────────────
function Callout({ type, text }) {
  const styles = {
    tip:     { bg: 'rgba(50,205,50,0.08)',  border: '#32CD32', icon: '💡', label: 'Tip',     labelColor: '#32CD32' },
    warning: { bg: 'rgba(239,68,68,0.08)', border: '#ef4444', icon: '⚠',  label: 'Warning', labelColor: '#ef4444' },
    info:    { bg: 'rgba(0,127,255,0.08)', border: '#007FFF', icon: 'ℹ',  label: 'Info',    labelColor: '#007FFF' },
  }
  const s = styles[type] || styles.info
  return (
    <div className="rounded-xl p-4 flex gap-3 my-4"
         style={{ background: s.bg, border: `1px solid ${s.border}40` }}>
      <span className="text-base shrink-0 mt-0.5">{s.icon}</span>
      <div>
        <span className="text-[11px] font-bold mr-2" style={{ color: s.labelColor }}>
          {s.label}
        </span>
        <span className="text-text-secondary text-[11px] leading-relaxed">{text}</span>
      </div>
    </div>
  )
}

// ── Live-Sync Badge ────────────────────────────────────────────
function LiveSyncBadge({ articleId }) {
  const v = VERSION_MAP[articleId]
  if (!v) return null
  return (
    <div className="flex items-center gap-2 mb-6 p-3 rounded-xl"
         style={{ background: 'rgba(50,205,50,0.07)', border: '1px solid rgba(50,205,50,0.25)' }}>
      <svg width="14" height="14" viewBox="0 0 14 14">
        <circle cx="7" cy="7" r="6" stroke="#32CD32" strokeWidth="1.5" fill="none"/>
        <path d="M4 7 L6.5 9.5 L10 5" stroke="#32CD32" strokeWidth="1.5"
              strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      <span className="text-lime-DEFAULT text-[11px] font-semibold">
        Verified for v{v.version}
      </span>
      <span className="text-text-muted text-[10px]">·</span>
      <span className="text-text-muted text-[10px]">
        Docs match codebase as of {v.date}
      </span>
      <span className="ml-auto text-[9px] text-text-muted border border-border-base
                       rounded px-1.5 py-0.5 bg-bg-hover">
        Live-Sync
      </span>
    </div>
  )
}

// ── Section heading ────────────────────────────────────────────
function H2({ children }) {
  return (
    <h2 className="text-white font-bold text-base mt-8 mb-3 flex items-center gap-2">
      {children}
    </h2>
  )
}

// ── Article renderer ───────────────────────────────────────────
function ArticleView({ articleId }) {
  const { openTab } = useAppStore()
  const data = ARTICLES[articleId]

  if (!data) return (
    <div className="flex items-center justify-center h-full text-text-muted text-sm">
      Article not found.
    </div>
  )

  // Special: Glossary
  if (data._special === 'glossary') {
    return (
      <div className="max-w-4xl mx-auto px-8 py-8">
        <LiveSyncBadge articleId={articleId} />
        <h1 className="text-white font-black text-2xl mb-1">CSV Glossary 2026</h1>
        <p className="text-text-secondary text-sm mb-2">
          Definitive reference for Computer System Validation, CSA, and EVOLV-specific terminology.
        </p>
        <div className="neon-sep mb-6" />
        <div className="grid grid-cols-1 gap-3">
          {GLOSSARY.map(g => (
            <div key={g.term}
                 className="glass rounded-xl p-4 flex gap-4">
              <div className="shrink-0 w-24">
                <span className="text-lime-DEFAULT font-black text-sm">{g.term}</span>
                <p className="text-text-muted text-[9px] mt-0.5 leading-tight">{g.full}</p>
              </div>
              <p className="text-text-secondary text-xs leading-relaxed flex-1">
                {g.def}
              </p>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-8 py-8">
      <LiveSyncBadge articleId={articleId} />

      {/* Title */}
      <h1 className="text-white font-black text-2xl mb-1">{data.title}</h1>
      <p className="text-text-secondary text-sm mb-2">{data.subtitle}</p>
      <div className="neon-sep mb-6" />

      {/* Overview */}
      <H2>📋 Overview</H2>
      <p className="text-text-secondary text-sm leading-relaxed whitespace-pre-line">
        {data.overview}
      </p>

      {/* 100x Advantage */}
      {data.advantage && (
        <>
          <H2>⚡ The 100x Advantage</H2>
          <div className="glass rounded-xl p-5">
            <p className="text-white font-semibold text-sm mb-3">{data.advantage.headline}</p>
            <div className="space-y-2">
              {data.advantage.points.map((p, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <span className="text-lime-DEFAULT text-[10px] mt-1 shrink-0">✓</span>
                  <p className="text-text-secondary text-xs leading-relaxed">{p}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Callouts (before steps) */}
      {data.callouts?.map((c, i) => <Callout key={i} type={c.type} text={c.text} />)}

      {/* Step-by-Step */}
      {data.steps && (
        <>
          <H2>🔢 Step-by-Step</H2>
          <div className="space-y-3">
            {data.steps.map(s => (
              <div key={s.n} className="flex gap-4">
                <span className="w-7 h-7 rounded-full bg-blue-DEFAULT/15 border
                                 border-blue-DEFAULT/30 text-blue-DEFAULT text-xs
                                 font-bold flex items-center justify-center shrink-0 mt-0.5">
                  {s.n}
                </span>
                <div>
                  <p className="text-white text-xs font-semibold mb-0.5">{s.title}</p>
                  <p className="text-text-secondary text-xs leading-relaxed">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Regulatory Context */}
      {data.regulatory && (
        <>
          <H2>🛡️ Regulatory Context</H2>
          <div className="glass rounded-xl overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border-base">
                  <th className="text-left px-4 py-2.5 text-text-muted font-medium w-44">
                    Reference
                  </th>
                  <th className="text-left px-4 py-2.5 text-text-muted font-medium">
                    Requirement
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.regulatory.map((r, i) => (
                  <tr key={i}
                      className="border-b border-border-base/50 last:border-0">
                    <td className="px-4 py-2.5 text-blue-DEFAULT font-mono text-[11px]">
                      {r.ref}
                    </td>
                    <td className="px-4 py-2.5 text-text-secondary leading-relaxed">
                      {r.desc}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Try it button */}
      {data.tryIt && (
        <div className="mt-8 p-5 rounded-xl border border-lime-DEFAULT/25
                        bg-lime-DEFAULT/5 flex items-center justify-between gap-4">
          <div>
            <p className="text-lime-DEFAULT text-sm font-semibold mb-0.5">
              Interactive Demo
            </p>
            <p className="text-text-muted text-xs">
              Try this feature live inside the EVOLV platform.
            </p>
          </div>
          <button
            onClick={() => openTab(data.tryIt.appId)}
            className="shrink-0 flex items-center gap-2 px-5 py-2.5 rounded-xl
                       bg-lime-DEFAULT text-bg-base text-xs font-bold
                       hover:brightness-110 transition-all
                       shadow-[0_0_20px_rgba(50,205,50,0.3)]"
          >
            ⚡ {data.tryIt.label}
          </button>
        </div>
      )}

      {/* Bottom padding */}
      <div className="h-16" />
    </div>
  )
}

// ── Main Docs component ────────────────────────────────────────
export default function Docs() {
  const [activeId,  setActiveId]  = useState('platform-overview')
  const [query,     setQuery]     = useState('')

  const filtered = useMemo(() => {
    if (!query.trim()) return null   // null = show full nav tree
    const q = query.toLowerCase()
    return ALL_ARTICLES.filter(a =>
      a.title.toLowerCase().includes(q) ||
      a.tags.some(t => t.includes(q))
    )
  }, [query])

  return (
    <div className="h-full flex bg-bg-base overflow-hidden">

      {/* ── Sidebar ───────────────────────────────── */}
      <div className="w-72 shrink-0 border-r border-border-base flex flex-col
                      overflow-hidden bg-bg-surface">

        {/* Header */}
        <div className="px-4 py-4 border-b border-border-base shrink-0">
          <div className="flex items-center gap-2 mb-3">
            <h2 className="text-white font-bold text-sm">Documentation</h2>
            <span className="text-[9px] px-1.5 py-0.5 rounded border border-border-base
                             text-text-muted">v1.1</span>
          </div>
          {/* Search */}
          <div className="flex items-center gap-2 bg-bg-hover border border-border-base
                          rounded-lg px-3 py-2">
            <svg width="12" height="12" viewBox="0 0 12 12" className="shrink-0 opacity-40">
              <circle cx="5" cy="5" r="4" stroke="currentColor" strokeWidth="1.5" fill="none"/>
              <line x1="8" y1="8" x2="11" y2="11" stroke="currentColor" strokeWidth="1.5"
                    strokeLinecap="round"/>
            </svg>
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search docs…"
              className="flex-1 bg-transparent text-xs text-text-primary
                         placeholder:text-text-muted outline-none"
            />
            {query && (
              <button onClick={() => setQuery('')}
                      className="text-text-muted hover:text-text-secondary text-xs">
                ×
              </button>
            )}
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-3">
          {filtered ? (
            // Search results
            <div className="px-3">
              <p className="text-[9px] text-text-muted uppercase tracking-widest px-2 mb-2">
                {filtered.length} result{filtered.length !== 1 ? 's' : ''}
              </p>
              {filtered.map(a => (
                <button
                  key={a.id}
                  onClick={() => { setActiveId(a.id); setQuery('') }}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs mb-0.5
                    transition-colors
                    ${activeId === a.id
                      ? 'bg-blue-dim border border-border-blue text-white'
                      : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
                    }`}
                >
                  <span className="text-text-muted text-[10px] block mb-0.5">
                    {a.sectionIcon} {a.sectionTitle}
                  </span>
                  {a.title}
                </button>
              ))}
            </div>
          ) : (
            // Full tree
            NAV.map(section => (
              <div key={section.id} className="mb-4">
                <p className="px-5 text-[9px] text-text-muted uppercase tracking-widest mb-1">
                  {section.icon} {section.title}
                </p>
                <div className="px-2 space-y-0.5">
                  {section.articles.map(article => {
                    const ver = VERSION_MAP[article.id]
                    return (
                      <button
                        key={article.id}
                        onClick={() => setActiveId(article.id)}
                        className={`w-full text-left flex items-center gap-2 px-3 py-2
                          rounded-lg text-xs transition-colors
                          ${activeId === article.id
                            ? 'bg-blue-dim border border-border-blue text-white'
                            : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
                          }`}
                      >
                        <span className="flex-1 truncate">{article.title}</span>
                        {ver?.verified && (
                          <svg width="10" height="10" viewBox="0 0 10 10" className="shrink-0 opacity-60">
                            <circle cx="5" cy="5" r="4.5" stroke="#32CD32" strokeWidth="1" fill="none"/>
                            <path d="M3 5 L4.5 6.5 L7 4" stroke="#32CD32" strokeWidth="1"
                                  strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))
          )}
        </nav>

        {/* Footer */}
        <div className="border-t border-border-base px-4 py-3 shrink-0">
          <p className="text-[9px] text-text-muted text-center">
            EVOLV Docs · 21 CFR Part 11 Compliant
          </p>
        </div>
      </div>

      {/* ── Article content ───────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        <ArticleView articleId={activeId} />
      </div>
    </div>
  )
}
