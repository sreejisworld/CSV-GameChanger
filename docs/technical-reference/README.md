# EVOLV — Technical Reference

*A reviewer's guide to the EVOLV codebase. Written for an
engineer doing a technical / security review who has never seen
this repo before. Start here.*

**Version:** platform v1.48 · reference compiled 2026-07-22
**Scale:** ~68,000 LOC — Agents 25.4k · API 11.8k · utils 5.1k ·
React platform 25.5k.

---

## 1. What EVOLV is, in one paragraph

EVOLV is an AI-assisted **Computer System Validation (CSV)**
platform for pharma/biotech. It runs the full GAMP 5 V-model
lifecycle: AI drafts requirements, risk assessments, and test
scripts; an **independent verification agent** checks every draft
against a regulatory knowledge base; every state-changing action
is written to a **hash-chained, tamper-evident audit trail**; and
every irreversible step (phase completion, release, change
control) gates on a **named human electronic signature**. The
design invariant is: *AI proposes, a qualified human signs, and
an inspector can re-derive any decision from its recorded
inputs.*

## 2. The mental model (read this before the code)

Three ideas explain 90% of the architecture:

1. **Specialist functions ("agents").** Each unit of AI or
   deterministic reasoning is a self-contained module in
   `Agents/`. Most are **fully deterministic** (risk matrix, test
   routing, exclusion screening); a few are **LLM-backed**
   (requirement drafting, verification) and always have an
   independent check + human gate around them. Every agent
   declares a machine-readable **Agent Passport**
   (`Agents/agent_passports.py`) stating what it may and may not
   do.

2. **Everything is audited.** No agent changes state silently.
   All writes go through `Agents/integrity_manager.log_audit_event()`,
   which appends a SHA-256 **hash-chained** row to
   `output/audit_trail.csv` and optionally a **Logic Archive**
   JSON capturing the full reasoning chain. The chain is
   independently verifiable (`verify_audit_chain()`).

3. **Bounded autonomy.** The `BoundedAutonomyProfile` engine
   classifies any AI deployment into a tier (BAP-0…BAP-4) or
   refuses it outright (BAP-X) via five hard exclusion rules.
   This is both a product feature and the governing philosophy of
   the codebase.

## 3. Tech stack

| Layer | Tech |
|---|---|
| Backend API | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| AI / retrieval | OpenAI (embeddings), Pinecone (vector store), Anthropic (optional LLM-as-judge) |
| Documents | fpdf2 (PDFs), python-docx (Word) |
| Frontend | React 18 + Vite, Zustand (state), Tailwind, Framer Motion |
| Persistence | **File-based** — CSV audit trail, JSON stores (see §6) |
| CI | GitHub Actions — compliance gate, pip-audit, 136-eval suite, React build |
| Marketing site | Static HTML in `website/`, GitHub Pages auto-deploy |

## 4. Repository layout (top level)

```
Agents/          32 specialist-function modules (the core IP)
  sentinel/      change-impact sub-package
API/             FastAPI app + 21 routers + stores + security
  routers/       one router per lifecycle phase / capability
utils/           PDF + Word generation, audit decorator
scripts/         CLI tools, CI hooks, ingestion, build helpers
react-platform/  React 18 SPA (the product UI)
  src/apps/      23 phase/tool screens
  src/store/     Zustand global store
  src/shell/     sidebar, header, lifecycle spine
frontend/        legacy Streamlit UI (secondary; not primary)
website/         static marketing site (evolifeval.com)
docs/            architecture, sprint notes, this reference
output/          generated artefacts (audit trail, archives, PDFs)
Tests/           scenario libraries for the eval/test-pilot suites
.github/workflows/ CI pipelines
```

## 5. How to navigate this reference

| Doc | Covers |
|---|---|
| [`01-code-map.md`](01-code-map.md) | Every significant file and what it does |
| [`02-agents.md`](02-agents.md) | The `Agents/` subsystem — per-agent deep-dive |
| [`03-api.md`](03-api.md) | FastAPI app, routers, stores, request lifecycle *(forthcoming)* |
| [`04-react-platform.md`](04-react-platform.md) | Frontend structure + state model *(forthcoming)* |
| [`05-audit-and-integrity.md`](05-audit-and-integrity.md) | Audit chain, Logic Archives, tamper evidence *(forthcoming)* |
| [`06-evals-and-quality.md`](06-evals-and-quality.md) | Trusted Evals, reproducibility, CI gates *(forthcoming)* |
| [`07-security.md`](07-security.md) | Auth, CORS, input validation, threat model *(forthcoming)* |
| [`08-deployment.md`](08-deployment.md) | Config, env vars, Docker, hosting *(forthcoming)* |

The single most authoritative artefact for **requirement →
implementation** traceability is the **URS Traceability Index**
in `CLAUDE.md` (253 requirements, each mapped to the exact file
and function that implements it). A reviewer should keep it open
alongside this reference.

## 6. Conventions a reviewer must know

These are enforced (some by CI) and explain patterns you'll see
everywhere:

- **Traceability tags.** Every public function has a docstring
  `:requirement: URS-X.Y` tag linking it to the URS index. The CI
  compliance gate (`scripts/compliance_check.sh`) fails the build
  if a public function is untagged. Boilerplate (`to_dict`,
  properties, `@overload`) is exempt.
- **Typed errors with codes.** Exceptions carry an `error_code`
  class attribute (format `CSV-NNN`). No bare `except: pass`.
- **Audit-first.** Any state change calls `log_audit_event()`.
  Direct writes to `output/audit_trail.csv` are forbidden and
  blocked by a pre-commit-style hook.
- **API triplet.** Each endpoint logs `<RESOURCE>_RECEIVED`,
  `<RESOURCE>_COMPLETED`, and `<RESOURCE>_FAILED`.
- **Type hints everywhere;** PEP 8, 79-char lines.
- **Determinism where it matters.** Reasoning that feeds a GxP
  decision is deterministic and byte-reproducible
  (`Agents/reproducibility.py` proves it in CI). LLM output is
  confined to drafting/advisory roles behind a human gate.
- **Branding.** "EVOLV" = product; "Validation Factory" =
  functional label. Internal class names like `CSVEngineError`
  are legacy and intentionally retained.

## 7. Known limitations (stated honestly for the reviewer)

- **Persistence is file-based** (CSV + JSON), not a database.
  Fine for single-tenant / pilot; a real DB is required before
  multi-tenant SaaS. Concurrency is guarded by in-process locks
  only.
- **Auth is an API-key gate** (`API/security.py`), not per-user
  identity / RBAC / SSO. It authenticates the client, not the
  user; per-user attribution rides in `user_id` fields.
- **Upstream data residency.** Requirement text is sent to OpenAI
  (embeddings) and Pinecone (US cloud). A self-hostable option is
  roadmap, not shipped.
- **Audit-chain tail truncation** is not detectable from the file
  alone; mitigated by external head-hash anchoring (documented in
  `05-audit-and-integrity.md`).

None of these are hidden — they are the honest gaps between
"pilot-ready" and "multi-tenant production."
