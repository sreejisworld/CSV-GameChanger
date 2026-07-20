# EVOLV × EU AI Act — High-Risk Requirements Mapping

**Answers the vendor-governance question:** *"How does this
system comply with the EU AI Act's high-risk requirements?"*
Version 1.0 · Sprint 49. Honest inventory: ✅ implemented ·
🟡 partial · ❌ gap with plan.

**Classification position:** EVOLV drafts validation artefacts
that qualified humans review and sign (BAP-2, Controlled
Drafting). It does not make autonomous decisions affecting
health or safety; five hard exclusions structurally prevent
the shapes (AI signing, batch release, CAPA closure, clinical
decisions, unsigned validated-record writes) that would move it
up the risk ladder. We nonetheless map against the high-risk
(Chapter III, Section 2) requirements because our pharma
customers' contexts may be high-risk and their vendor diligence
will use this lens.

| EU AI Act requirement | EVOLV implementation | Status |
|---|---|---|
| **Art. 9 — Risk management system** (continuous, iterative) | Bounded Autonomy Profile engine: impact class → failure envelope → control sustainability per deployment; 5 exclusion rules; tier-graduated control catalogue; fragility markers naming assumptions that would invalidate the safety case | ✅ |
| **Art. 10 — Data & data governance** | Regulatory corpus versioned per document (`reg_version` on every chunk + citation); ingestion / query / verification drift detection; no training on customer data (retrieval-augmented, not fine-tuned) | ✅ |
| **Art. 11 + Annex IV — Technical documentation** | AI Vendor Transparency Dossier (`POST /versions/dossier`) generated from live platform data; Agent Passports; architecture docs; this mapping | ✅ |
| **Art. 12 — Record-keeping / logging** | Hash-chained append-only audit trail (edits/deletions/reorders detectable); Logic Archives storing full reasoning chains per AI decision, re-derivable by an inspector | ✅ |
| **Art. 13 — Transparency & provision of information to deployers** | Version Registry + customer changelog + notification commitment (`GET /versions/registry`); per-step regulatory citations on outputs; incident runbook (docs/ai-incident-runbook.md) | ✅ |
| **Art. 14 — Human oversight** | Every irreversible action gates on a named human signature (Part 11 manifestation pages); Agent Passports enforce forbidden actions at the engine level; QA review attestation independent of executor | ✅ |
| **Art. 15 — Accuracy, robustness, cybersecurity** | 131 deterministic evals gating CI on every change + 90 adversarial Test Pilot scenarios; eval history trending (`/evals/history`); security hardening (API-key gate, input limits, pip-audit in CI, 10/10 audit findings closed) | ✅ |
| **Art. 17 — Quality management system (provider)** | Compliance gate in CI (URS traceability, error codes, audit-write protection); incident runbook; changelog discipline | 🟡 QMS exists as engineering practice; formal ISO-style QMS documentation is pre-revenue roadmap |
| **Art. 49/71 — Registration (EU database)** | Not applicable until EU deployment of a high-risk classification; position documented above | 🟡 monitor |
| **Art. 72 — Post-market monitoring** | ValidatedStateEngine (continuous validated-state scoring), regulatory drift scans, upstream model drift detection (`UPSTREAM_MODEL_CHANGED`) | ✅ |
| **EU AI Act corpus in retrieval knowledge base** | The Act's text is not yet an ingested corpus source (flagged in our own drift scenarios) | ❌ **Gap — ingest planned; tracked in registry changelog when landed** |

## Summary for a diligence reviewer

EVOLV was not retrofitted for the AI Act — the bounded-autonomy
architecture (human signature gates, chained logging, versioned
corpus, standing evals) happens to be what Articles 9–15 ask
for. The honest gaps are formal QMS documentation and Act-text
corpus ingestion, both named above with plans. Ask us for the
Transparency Dossier for the live-data version of this mapping.
