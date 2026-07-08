# EVOLV — The Trust Architecture

*A map of EVOLV's architecture against the most credible thinking in
agentic AI governance for regulated industries.*

---

## Why this document exists

Two voices have, independently, in the last six weeks, published the
clearest thinking on how regulated industries should adopt agentic AI:

- **Nuno Valério** (Head of Quality Digital Innovation, Merck
  Healthcare) — *"The Trust Architecture"* newsletter. Bounded
  autonomy. *"The validation surface is moving."* Every AI decision
  must be inspectable.
- **Salim Ismail** (Founder, ExO Works; co-author *Exponential
  Organizations*) — **ExO 3.0** framework. *"MTP encoded as protocol."*
  Six-layer Intelligence Stack wrapped by a Govern/Assure control
  plane. Four pillars: Trusted Evals, Searchable Logs, Granular
  Rollback, Human Review Queues.

EVOLV was not built downstream of either framework. The architecture
predates both. But the convergence is now explicit, and we should be
honest about where we sit on each map — including our gaps.

This document maps EVOLV's actual components to each framework, then
names the gaps we are actively closing.

---

## EVOLV in one sentence

> *EVOLV is the bounded-autonomy architecture for pharma Computer
> System Validation — where every AI proposal is independently
> verified against the regulatory corpus, every advance is
> human-signed, and every decision writes a tamper-evident reasoning
> chain that an inspector can re-derive.*

That sentence is the test. Every component below should be defensible
against it.

---

## The three pillars (ExO 3.0)

Salim's top-level architecture has three pillars. EVOLV maps as
follows.

### 1. MTP — The Protocol

> *"Encoded, not framed. Not a poster — a protocol."*

EVOLV's MTP equivalent: **the regulatory frameworks declared at the
Plan phase** (GAMP 5 edition, 21 CFR Part 11, EU GMP Annex 11, FDA CSA
Guidance, ICH Q9) plus the project's GAMP category, system
description, and scope.

| Salim's principle | EVOLV today | Verdict |
|---|---|---|
| Not a poster — a protocol | Regulatory corpus is *retrievable* by every agent via RAG; cited in every output | ✅ |
| Encoded so agents can execute it | RequirementArchitect, VerificationAgent, DeltaAgent all query the same corpus | ✅ |
| Detects stepping outside the cone | VerificationAgent rejects outputs that contradict the corpus | ✅ Post-hoc |
| **MTP as runtime constraint on every agent call** | Frameworks are *contextual* (retrieved), not *constitutional* (enforced as a gate) | ❌ **Gap — Sprint 41** |

### 2. DRIVE — The Intelligence Engine

> *"Five characteristics that convert purpose into shipped outcomes
> at machine speed."*

| Salim's characteristic | EVOLV today |
|---|---|
| **Decision Architecture** (automate two-way doors, gate one-way doors) | ✅ Every irreversible action — phase complete, CCR sign, release go-live — gates on human signature. Reversible decisions (drafts, suggestions) are AI-only. |
| **Recursive Learning** (improve faster than the environment changes) | ❌ **Major gap — Sprint 40.** No accept/edit/reject tracking; no prompt refinement based on outcomes; no drift detection over time. |
| **Intelligence Stack** (the six-layer cognitive core) | 🟡 See full map below |
| **Value Moat** (defensible when models are commodity) | ✅ The regulatory corpus + customer SOPs + audit-trail format are LLM-agnostic; the moat survives any model swap. |
| **Elastic Agency** (one pool of human + synthetic capability) | ✅ Adhoc step insertion, QA Review attestation, manual bundle authoring — humans and AI share the same surface. |

### 3. SHAPE — The Organizational Form

> *"Five characteristics that hold the engine without cracking at
> speed."*

| Salim's characteristic | EVOLV today |
|---|---|
| **Safe Autonomy** (protocol governance with named human accountability) | ✅ Every audit row carries `user_id`. Every approval has a signer. Every Logic Archive is hash-linked. |
| **Human Architecture** (engineer where human judgment is irreplaceable) | ✅ Risk acceptance, defect adjudication, release sign-off, QA review attestation — the human spots are named. |
| **Adaptive Architecture** (modularity and antifragility by design) | 🟡 LLM-agnostic + deployment-mode-flexible + open data formats — yes. But the six named specialist functions are hardcoded; no runtime protocol for swapping or adding them. |
| **Purpose Control** (MTP enforced operationally, not aspirationally) | ❌ Same gap as MTP-as-protocol. Sprint 41. |
| **Ecosystem Trust** (cryptographic trust across firm boundaries) | 🟡 SHA-256 audit chains exist. Not yet federated cross-org (your CMO's chain doesn't yet join yours). |

---

## The Six-Layer Intelligence Stack

Salim's claim: *"If you build one thing first, build this."* EVOLV
has built most of it without naming it this way. Mapping below.

```
┌─────────────────────────────────────────────────────────────┐
│                  GOVERN / ASSURE (NEVER OFF)                │
│         Logic Archives · SHA-256 chained audit trail        │
│              VerificationAgent · Logic Archive              │
└─────────────────────────────────────────────────────────────┘
        ▲          ▲          ▲          ▲         ▲       ▲
        │          │          │          │         │       │
  ┌─────┴────┐ ┌──┴───┐ ┌────┴────┐ ┌───┴───┐ ┌──┴──┐ ┌──┴──┐
  │ PURPOSE  │ │SENSE │ │INTERPRET│ │DECIDE │ │ ORCH│ │LEARN│
  └──────────┘ └──────┘ └─────────┘ └───────┘ └─────┘ └─────┘
```

| Salim's layer | What it does | EVOLV's component |
|---|---|---|
| **1. Purpose** | Sets objectives and constraints from MTP. The constitutional layer. | Regulatory corpus + project `planData` (frameworks, scope, GAMP category) |
| **2. Sense** | Collects signals from environment, customers, operations, competitors. | Brief intake · Workshop intake · ServiceNow CR webhook · RegulatoryWatch (stub) |
| **3. Interpret** | Builds context, retrieves history, frames scenarios. *Salim: "the most important loop."* | RequirementArchitect + RAG over corpus + 3 Cs decomposition + SMART refinement |
| **4. Decide** | Generates options and commits within the Permission Envelope. | Risk matrix (deterministic) + Test depth selection + Change Impact Assessment + CCR sign-off |
| **5. Orchestrate / Act** | Executes through tools, workflows, APIs, humans, agents. | Test bundle → script → run → defect → approval pipeline |
| **6. Learn** | Evaluates outcomes, updates models, propagates improvements upstream. | Audit trail aggregation; defect closure feedback |

### Strongest layer: **Interpret (#3)**

EVOLV's RequirementArchitect with RAG over GAMP 5 + EU Annex 11 + FDA
CSA + ICH Q9 + customer SOPs is the deepest layer in the stack. Every
generated artifact cites its sources to page-and-paragraph precision.

### Weakest layer: **Learn (#6)**

EVOLV does not currently track which AI proposals were accepted as-is,
edited, or rejected. There is no recursive self-improvement loop. This
is Sprint 40 work.

---

## The Four Pillars of Govern / Assure

Salim's most actionable slide — the one a pharma CISO will recognize
on sight. EVOLV scores well here. It is also where EVOLV's deepest
moat lives.

| Salim's pillar | What it requires | EVOLV today | Sprint to close gap |
|---|---|---|---|
| **1. Trusted Evals** | Every agent runs continuously against a known test set. Drift flags alerts before customers see it. | VerificationAgent runs per-call. No continuous standing eval set. | Sprint 44 (skeleton lands in pre-June-3 polish) |
| **2. Searchable Logs** | Every decision traceable from a correlation ID. Immutable, hashed, cryptographically signed. | Logic Archives + `reasoning_hash` + SHA-256 chained CSV audit trail. | ✅ **Strongest — ships today** |
| **3. Granular Rollback** | Any agent revertible to last week's prompt, last month's model, last quarter's policy. | Audit trail captures prompt/model versions per call. No `revert_agent_to(date)` UI action. | Sprint 43 |
| **4. Human Review Queues** | Money, legal, brand, customers route to a named human with SLAs. *"Above the loop, not in it."* | Defects → assignee, approvals → signer. No SLA-tracked queue surface. | Sprint 42 (partial — Sprint 36 CCR sign extends this) |

---

## The Four Moats (defensibility when models are commodity)

Salim names four reasons a company stays defensible in the agentic
era. EVOLV's standing on each:

| Moat | What it means | EVOLV |
|---|---|---|
| **Proprietary data** | Data others cannot replicate | Regulatory corpus (ingested + curated) + each customer's ingested SOPs + each customer's accumulated audit trail. |
| **Regulatory** | Capture through compliance complexity | 21 CFR Part 11 + GAMP 5 + EU GMP Annex 11 + FDA CSA + ICH Q9 + 21 CFR Part 820 / QMSR + FDA PCCP (Aug 2025) — all ingested, cited, and version-tracked. |
| **Intelligence** | Learn faster than competitors | Today: **weak**. Sprint 40 closes this — accept/edit/reject tracking + prompt refinement + drift detection. |
| **Customer relationship / brand** | Emotional connection to the end user | Trust architecture published in 5-part LinkedIn series. Building this in public. |

---

## Agent Passports — the Permission Envelope, made explicit

Salim's recommendation: every agent should carry metadata declaring
what it is **allowed** to do, what data it can see, what outputs
require human sign-off. Borrowed from smart-contract patterns in
Web3.

EVOLV's implementation lives in `Agents/agent_passports.py`. Each
agent has a passport with:

- `purpose` — single-sentence statement of intent
- `allowed_actions` — explicit list of action verbs the agent may take
- `forbidden_actions` — explicit list of actions the agent must NEVER take
- `data_classifications_allowed` — types of data the agent may read
- `data_classifications_forbidden` — types of data the agent must never see
- `requires_human_signoff_on` — outputs gated on human signature before propagation
- `outputs_audited_via` — the audit event triplet the agent triggers
- `rollback_eligible` — whether the agent's outputs can be reverted

A pharma customer can read every passport. An auditor can read every
passport. An inspector can ask "*what is RequirementArchitect allowed
to do?*" and we hand them the file.

This is the explicit version of bounded autonomy. It is also exactly
the kind of artifact Nuno's *"5 questions every pharma-vendor
contract should have from Q3 onward"* will demand.

---

## What the gaps look like, named honestly

Because honesty is the practice, not the slogan. Six known gaps,
ranked by strategic value, with sprint targets:

| # | Gap | Salim framework piece | EVOLV sprint |
|---|---|---|---|
| 🔴 1 | **Recursive Learning Loop** — no accept/edit/reject tracking; no drift detection on agent outputs | DRIVE characteristic #2 | Sprint 40 |
| 🔴 2 | **MTP as Runtime Constraint** — frameworks contextual, not constitutional | Pillar 1 (MTP) + SHAPE #4 | Sprint 41 |
| 🟡 3 | **Sense Layer continuous feeds** — no auto-detect of LLM-version, regulatory-update, or SOP-update events | Intelligence Stack layer 2 | Sprint 42 |
| 🟡 4 | **Agent Passports surfaced** | DRIVE — Permission Envelope | **Ships now** (this commit) |
| 🟢 5 | **Granular Rollback UI action** | Govern/Assure pillar 3 | Sprint 43 |
| 🟢 6 | **Continuous Trusted Evals (full version)** | Govern/Assure pillar 1 | Sprint 44 (skeleton ships now) |

After Sprint 44 (~6 weeks out), EVOLV is a literal embodiment of
ExO 3.0 applied to pharma CSV. Demo-able to any board, defensible to
any inspector.

---

## How this connects to two recent thought-leaders

This is not a position EVOLV claims unilaterally. It is the
intersection where two independent voices are converging.

**Nuno Valério (Merck Healthcare, *The Trust Architecture*):**

> *"When the system you're qualifying is the kind of system that
> changes between qualifications, what does qualification mean? …
> What sat inside your QMS is becoming a configuration choice inside
> the vendor's platform. The vendor is, quietly, making more of the
> trust architecture than they used to."*

EVOLV's answer: the customer keeps the trust architecture. The audit
trail is in the customer's region. The Logic Archives are in the
customer's S3. The Permission Envelopes are published. The LLM is
the customer's qualified provider. The vendor (us) provides the
architecture; the customer keeps the truth.

**Salim Ismail (ExO Works, *Organizational Singularity*):**

> *"The central thing to think about is all of our organizational
> structures in the past were organized around hierarchy. Now they
> need to be architected around intelligence, not around
> hierarchy."*

EVOLV's answer: every phase of pharma CSV is restructured around the
Intelligence Stack instead of the org chart. No middle management.
No quarterly review cycle. Phase-to-phase advance gated on signed
artifacts, not on meetings.

---

## What this document is, and what it is not

This document is an honest map of where EVOLV sits relative to the
most credible AI-architecture thinking in regulated industries as of
May 2026. It will be wrong in three months. The pace of change in
this space is faster than any document can keep up with.

This document is **not** a marketing claim. Every check mark is
defensible against code on disk. Every red dot is a real gap with a
sprint number against it. Every link to an external framework cites
the public source.

This document **is** the architecture that pharma teams can read
before they sign an NDA. If you have questions, the answers should
get stronger by the next time you check.

---

*EVOLV · WingstarTech Inc. · May 2026*
*This document evolves. Last updated when the sprint shipped that
closed the gap.*
