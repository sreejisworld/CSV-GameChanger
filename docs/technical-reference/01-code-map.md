# 01 — Code Map

*Every significant file, what it does, and where to look. Grouped
by subsystem. LOC figures are approximate.*

---

## Agents/ — specialist functions (≈25.4k LOC, the core IP)

Deterministic unless marked **[LLM]**. Each has `:requirement:`
tags and routes state changes through the integrity manager.

### Lifecycle reasoning
| File | Purpose |
|---|---|
| `requirement_architect.py` **[LLM]** | Generates URS from natural language via RAG over the regulatory corpus; deterministic transform URS → UR/FR. The main authoring engine. |
| `verification_agent.py` **[LLM]** | Independent review of each URS draft against GAMP 5 text (criticality alignment, rationale relevance, contradiction scan). Rejections → Compliance Exceptions. |
| `risk_strategist.py` | GAMP 5 risk matrix: RPN = Severity × Occurrence × Detectability; patient-safety override; CSA testing-strategy selection. Pure functions. |
| `delta_agent.py` | CSA test-script generation from UR/FR (informal / OQ / UAT routing, setup vs execution steps, positive/negative/edge cases). Deterministic. |
| `test_authoring_engine.py` | Risk-adaptive test bundles with per-step regulatory citations (FULL/STANDARD/MEDIUM/CHARTER depth). |
| `test_generator.py` | Earlier LLM-based test-script generator (superseded by delta/test-authoring in the UI; retained). |
| `smart_requirements_engine.py` | Refines vague requirements into SMART format; FDA/EMA AI-guidance trigger detection. |
| `intelligence_engine.py` **[LLM]** | Requirements intelligence: Mermaid workflow diagram, criticality analysis, security-gap detection. |

### Change / state / continuity
| File | Purpose |
|---|---|
| `change_impact_agent.py` | Change Impact Assessment: given a CR + project snapshot, finds affected URs (token-overlap), inherited FRs, bundles needing revalidation, invalidated approvals. Includes `sign_ccr()`. |
| `validated_state_engine.py` | Per-UR "validated state confidence" score (0-100) from bundle staleness, defect pressure, CIA history, coverage. Green/yellow/red tiers. |
| `regulatory_drift_agent.py` | Detects when the regulatory corpus has diverged (new framework versions / guidance). |
| `sentinel/impact_engine.py`, `sentinel/justification_engine.py`, `sentinel_impact_agent.py` | Sentinel: blast-radius change-impact analysis + impact-assessment report generation. |

### Governance / trust (the "Govern/Assure" layer)
| File | Purpose |
|---|---|
| `integrity_manager.py` | **Central audit trail.** `log_audit_event()`, SHA-256 hash chaining, Logic Archive writing, `verify_audit_chain()`. Every other agent depends on this. |
| `agent_passports.py` | Machine-readable permission envelopes per agent (allowed/forbidden actions, data classes, human-signoff points). Self-validates at import. |
| `bounded_autonomy_profile.py` | BAP engine: Impact Class → Failure Envelope → Control Sustainability → tier (BAP-0…4 / BAP-X). Five hard exclusion rules (`EXCLUSION_RULES`). |
| `trustworthiness_report.py` | AI Trustworthiness Credibility Report — maps controls to NIST/FDA GMLP/ISO frameworks. |
| `policy_engine.py` | Deployment-context policy checks. |
| `compliance_context.py` | Deployment-context regulatory configuration (which frameworks apply). |
| `auditor_agent.py` | Auditor-facing review helper. |

### Evals / quality (self-testing)
| File | Purpose |
|---|---|
| `eval_suite.py` | **Trusted Evals** — 136 deterministic checks across 7 agents; optional LLM-as-judge; history persistence; CLI `python -m Agents.eval_suite`. |
| `agent_evals.py` | Golden-set eval engine for RequirementArchitect (skeleton the suite extends). |
| `customer_evals.py` | Bring-your-own-golden-set harness (customers test EVOLV on their data). |
| `reproducibility.py` | Proves deterministic engines are byte-identical across runs (output-consistency + OQ evidence). |
| `test_pilot.py` | Adversarial scenario runner (90+ scenarios against BAP/VSE/drift). |
| `self_validation.py` | Assembles EVOLV's own validation package (parses the URS index → VP + RTM + IQ + OQ). |
| `version_registry.py` | Component/model version registry + changelog + upstream-model drift detection. |

### Retrieval / ingestion / mapping
| File | Purpose |
|---|---|
| `ingestor_agent.py` | Ingests regulatory PDFs into Pinecone; gap analysis. |
| `regulatory_citations.py` | Archetype → citation map (21 CFR 11, Annex 11, ICH Q9, GAMP 5). |
| `metadata_mapper.py` | Tenant nomenclature mapping (per-customer label vocabulary). |

## API/ — FastAPI backend (≈11.8k LOC)

| File | Purpose |
|---|---|
| `main.py` | App factory, router registration, CORS, the app-wide API-key dependency, ServiceNow webhook, admin key endpoints. |
| `security.py` | `require_platform_key` (API-key gate), `sanitize_filename_component`, `get_cors_origins`. CSV-050/051/052 errors. |
| `schemas.py` | Shared Pydantic request/response models. |
| `agent_controller.py` | Orchestrates agent calls for bulk operations. |
| `middleware.py` | `TenantDictionaryMiddleware` — rewrites response labels per tenant. |
| `sandbox.py` | Developer sandbox mode (`X-EVOLV-MODE: Sandbox`) — no production records committed. |
| **Stores (file-based):** | |
| `project_store.py` | Project/release/folder/item CRUD → `output/project_store.json`. |
| `key_store.py` | Scoped API keys (hashed) → JSON. |
| `job_store.py` | Bulk-job progress tracking. |
| `webhook_registry.py` | Webhook registration + signed delivery records. |
| **Routers (`API/routers/`, one per capability):** | |
| `plan / requirements / verify / release / monitor` | Lifecycle-phase endpoints. |
| `generate_script / test_authoring / traceability` | Design/test endpoints. |
| `change_control / validated_state / regulatory_drift` | Change + continuity endpoints. |
| `bap / trustworthiness / agents` | Governance endpoints (BAP assess, TWR, passports). |
| `evals` | Run the eval suite + history (`/evals/run`, `/evals/history`). |
| `versions` | Version registry, Transparency Dossier, self-validation package. |
| `audit` | Audit-trail JSON API + chain verification + PDF export. |
| `governance` | HITL decision queue. |
| `exports` | VP / DS / VSR PDF exports. |

## utils/ — document generation (≈5.1k LOC)

| File | Purpose |
|---|---|
| `pdf_generator.py` | All signed PDFs: URS, Validation Report, VP/DS/VSR, audit export, traceability matrix, TWR, BAP, **Transparency Dossier**, **Self-Validation package**. fpdf2. |
| `word_generator.py` | Word template injection ({{PLACEHOLDER}} replacement + tables). |
| `demo_comparison.py` | Side-by-side human-vs-AI requirement comparison (marketing/demo). |
| `audit_decorator.py` | `@audit_log` decorator wrapping functions with audit events. |

## react-platform/ — product UI (≈25.5k LOC, 23 app screens)

| Path | Purpose |
|---|---|
| `src/App.jsx` | Tab shell + renderer registry (maps appId → component). |
| `src/store/useAppStore.js` | **Zustand global store** — all cross-component state (project data, requirements, risk, bundles, runs, defects, approvals, change records, validated-state, nav, theme). Persisted via `partialize`. |
| `src/shell/` | `Sidebar.jsx`, `TopHeader.jsx`, `LifecycleStrip.jsx`, `vmodelGeometry.js` — chrome + V-model spine. |
| `src/apps/` | 23 screens: `Home, Plan, Requirements, Risk, Design, Verify, Release, Monitor, Retire` (lifecycle) + `TraceabilityMatrix, Portfolio, AuditTrail, DevPortal, BAP…` (tools). |
| `src/data/apps.js` | `APPS` + `NAV_GROUPS` — single source of truth for navigation. |
| `src/config.js` | `API_BASE` (defaults to `http://localhost:8000`). |

## scripts/ — tooling & CI hooks

| File | Purpose |
|---|---|
| `compliance_check.sh` | CI compliance gate (URS tags, error codes, type hints, audit-write protection, brand scan, hook presence). |
| `validate_urs_tag.py`, `protect_audit_trail.py`, `log_dev_change.py` | Claude Code / pre-commit hooks. |
| `verify_audit_chain.py` | CLI to walk + verify the audit hash chain. |
| `ingest_docs.py`, `setup_pinecone_index.py` | Corpus ingestion. |
| `draft_urs.py`, `draft_vsr.py`, `generate_vtm.py`, `sign_off.py` | CLI document generators. |
| `build_insights.py` | Static-site newsletter-archive generator. |

## .github/workflows/

| File | Purpose |
|---|---|
| `compliance-check.yml` | 5 jobs: compliance gate · dependency CVE audit (pip-audit) · Trusted Evals (136) · flake8 · React build. All blocking except lint. |
| `deploy-website.yml` | Deploys `website/` to GitHub Pages on push. |

## output/ — generated at runtime (git-ignored artefacts)

`audit_trail.csv` (hash-chained), `logic_archives/` (JSON
reasoning), `eval_history.jsonl`, `model_observations.jsonl`,
`project_store.json`, generated PDFs.
