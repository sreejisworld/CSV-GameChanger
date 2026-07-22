# 02 — Agents (the specialist-function layer)

*Deep-dive on `Agents/`. For each agent: what it does, how it
works, key entry points, determinism, failure mode, and where
it's tested. Read `01-code-map.md` first for the index.*

Two rules hold across every agent:
- **Audit-first:** any state change calls
  `integrity_manager.log_audit_event(...)` (often a
  RECEIVED/COMPLETED/FAILED triplet) before returning.
- **Passport-bound:** each agent's authority is declared in
  `agent_passports.py`; the passport enumerates forbidden
  actions (e.g. "never signs", "never releases").

---

## integrity_manager.py — the foundation

Everything depends on this. It is the **only** writer to the
audit trail.

**Key functions**
- `log_audit_event(agent_name, action, user_id, decision_logic,
  compliance_impact=None, audit_path=…, thought_process=None) ->
  reasoning_hash`
  Appends one row to `output/audit_trail.csv`. Computes a
  **chained** SHA-256 hash: `hash = sha256(prev_hash | timestamp
  | user_id | agent | action | decision_logic | impact)`. If
  `thought_process` (dict with `inputs`/`steps`/`outputs`) is
  passed, also writes a hidden **Logic Archive** JSON to
  `output/logic_archives/`, cross-referenced by the row hash.
- `verify_audit_chain(audit_path) -> ChainVerificationReport`
  Walks the CSV, classifies each row CHAINED / LEGACY / TAMPERED,
  flags legacy-after-chained downgrades, returns the chain head
  hash for external anchoring.
- `_compute_chained_hash`, `_get_prev_hash`, `_read_last_row_hash`
  — the chaining internals; a per-file last-hash cache avoids
  re-reading the file on every append (guarded by `_write_lock`).

**Determinism / concurrency:** writes are serialized by a module-
level `threading.Lock`. The CSV is append-only by code; a hook
(`scripts/protect_audit_trail.py`) blocks direct writes.
**Tested by:** `eval_suite.run_integrity_manager_evals()` (6
evals: edit / mid-delete / reorder detection, legacy coexistence)
+ `scripts/verify_audit_chain.py`.
**Reviewer note:** tail-truncation is not detectable from the
file alone — see `05-audit-and-integrity.md` for the anchoring
mitigation.

## requirement_architect.py [LLM]

The main authoring engine. Turns natural language into a
structured URS, then deterministically into a UR/FR document.

**Flow**
1. `search(query, top_k, min_score)` — embeds the query
   (OpenAI `text-embedding-3-small`), queries Pinecone
   (`csv-knowledge-base`), returns `SearchResult`s with
   source doc + page + score + reg_version.
2. `generate_urs(requirement, min_score)` — retrieves GAMP 5
   context, classifies criticality (keyword indicators),
   assigns a URS id, builds a citation-anchored regulatory
   rationale. Raises `RegulatoryContextNotFoundError` (CSV-004)
   if nothing relevant is retrieved (no ungrounded URS).
3. `transform_urs_to_ur_fr(urs, role, category, risk_assessment,
   implementation_method, additional_context)` — **deterministic,
   no LLM.** Applies the UR/FR risk matrix + test-strategy matrix
   and decomposes into functional requirements with acceptance
   criteria.

**Determinism:** step 3 is byte-reproducible (proven in
`reproducibility.py`). Steps 1–2 depend on the LLM/embeddings but
are gated downstream by `verification_agent` + human sign-off.
**Tested by:** `agent_evals.py` golden set (10 entries) +
independent verification of every draft.

## verification_agent.py [LLM]

The independent check that makes the LLM output defensible. Runs
three checks per URS against retrieved GAMP 5 text:
1. **Criticality alignment** — scans for high-risk indicators the
   draft may have under-classified.
2. **Rationale relevance** — best retrieval score ≥ threshold.
3. **Contradiction scan** — known contradiction phrase-pairs
   (e.g. "skip validation" vs "validation is required").

Emits `URS_VERIFIED` or `COMPLIANCE_EXCEPTION` audit events.
`verify_batch()` for lists. **Design point:** a *separate* agent
verifies the authoring agent — the two never share state, so a
draft can't approve itself.

## risk_strategist.py — deterministic risk matrix

Pure functions, no external deps. GAMP 5 logic:
- `calculate_risk_score(sev, occ, det) -> (rpn, level)` where
  RPN = S×O×D (1-27); ≤4 Low, 5-12 Medium, >12 High.
- **Patient-safety override:** Severity HIGH ⇒ Risk HIGH
  regardless of RPN.
- `get_csa_testing_strategy(level)` → Unscripted / Hybrid /
  Rigorous Scripted.
- `assess_change_request(criticality, change_type, detectability)`
  maps ServiceNow fields → full assessment.

**Tested by:** 12 evals (full matrix + override + boundaries).
Fully byte-reproducible.

## delta_agent.py — CSA test generation

Deterministic (no LLM/Pinecone). `generate_csa_test_from_ur_fr(
ur_fr, test_type)` routes by risk level:
- High + Informal → setup + positive + negative + edge per FR
- High + Formal OQ → setup + positive only
- High + Formal UAT → business-process steps
- Medium/Low → exploratory charter steps

Returns a step table (script_id `TS-`/`TC-` prefix, setup vs
execution, test-case type, requirement reference) + a self-check
quality checklist. **Tested by:** 7 evals. Reproducible modulo
`generated_at` timestamp.

## bounded_autonomy_profile.py — the governance engine

Classifies an AI "Context of Use" into an assurance tier.

**Pipeline:** `assess(cou)` → Impact Class → Failure Envelope →
Control Sustainability → `_assign_tier()` → BAP-0…BAP-4, or
**BAP-X** if any of five `EXCLUSION_RULES` fire.

**The five exclusion rules** (regex over statement +
decision_authority): AI executing a signature (§11.50), releasing
a batch (QP duty), closing a CAPA (§820.100), making a clinical
decision (SaMD), or writing to a validated record without a human
gate (§11.10(e)). Subject widened to (ai|llm|model); clause-
bounded matching so a rule can't straddle sentences.
**This same rule set is mirrored client-side in
`website/index.html`** (the live screener) — keep them in sync.
**Tested by:** 95 evals incl. 40 generated adversarial variants.
**Product surfaces:** `API/routers/bap.py`, the website screener.

## change_impact_agent.py — change control

`assess(cr_id, cr_text, project_snapshot) ->
ChangeImpactAssessment`. Deterministic token-overlap (Jaccard,
threshold 0.15) to find affected URs; inherits their FRs; names
bundles needing revalidation and approvals needing re-attestation;
emits a `reasoning_chain` for explainability. **Never modifies
records** — the CIA is a proposal; `sign_ccr()` is the human gate
that authorises revalidation. CIA_RECEIVED/GENERATED/FAILED
triplet + Logic Archive. **Tested by:** 6 evals.

## validated_state_engine.py — continuous validation

`assess(project_snapshot) -> ValidatedStateReport`. Scores every
UR 0-100 from deterministic signals: bundle staleness
(−0.1/day, cap −25), open defects (−5 each, cap −25), CIA density
(cap −20), no-bundle (−30), no-risk (−15); bonuses for recent
re-verification (+10) and full FR coverage (+5). Tiers: green ≥80,
yellow 50-79, red <50. **Never triggers revalidation** — score is
advisory. **Tested by:** 5 evals.

## The evals / quality quartet

| Agent | Role |
|---|---|
| `eval_suite.py` | Runs 136 deterministic checks across 7 agents; `run_suite()`, `summarise_suite()`, LLM-as-judge, history to `output/eval_history.jsonl`. Gates CI. |
| `reproducibility.py` | `run_reproducibility()` runs each deterministic engine K times, normalises provenance timestamps (incl. ISO stamps in narrative strings), asserts byte-identity. Wired in as the 7th eval agent. |
| `customer_evals.py` | Customers validate their own golden sets through the same engine; `--validate-only` needs no credentials. CSV-061. |
| `test_pilot.py` | 90+ adversarial scenarios against BAP/VSE/drift endpoints. |

## The vendor-governance trio (Sprint 48-50)

| Agent | Role |
|---|---|
| `version_registry.py` | `get_registry()` — 12-component version registry + customer changelog; `record_model_observation()` detects upstream foundation-model drift → `UPSTREAM_MODEL_CHANGED` audit event. |
| `self_validation.py` | `generate_self_validation_package()` — parses the 253-req URS index from `CLAUDE.md`, attaches verification evidence, assembles VP + IQ + OQ (eval suite run live) + RTM. `redacted=True` gives a public-safe variant. |
| `agent_passports.py` | `AGENT_PASSPORTS` — per-agent permission envelopes; `validate_passport_shape()` self-checks at import (malformed passport crashes the server loudly). |

---

## Reviewer checklist for this layer

- [ ] Confirm no agent writes to `output/audit_trail.csv`
      directly (all via `log_audit_event`).
- [ ] Confirm LLM-backed agents (`requirement_architect`,
      `verification_agent`, `intelligence_engine`) are the only
      ones importing `openai` / `pinecone`; the rest are pure.
- [ ] Confirm the website screener rules match
      `bounded_autonomy_profile.EXCLUSION_RULES`.
- [ ] Run `python -m Agents.eval_suite` — expect 136/136.
- [ ] Run `python -m Agents.reproducibility` — expect all engines
      byte-identical.
