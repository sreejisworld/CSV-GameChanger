# AI GxP Governance Framework — Skeleton

*Working structure · v0.1 · built from public standards and
practitioner judgment only*

---

## What this is

A structure for governing AI-enabled computerised systems in a GxP
environment, designed to **extend an existing CSV/QMS rather than sit
beside it**.

It is organised by the *question each part answers*, not by control
domain — because the failure mode in the field isn't a missing control
domain, it's nobody being able to answer a question in the room.

**Provenance:** every element derives from public regulatory sources
(listed in §7) plus twenty years of implementation judgment. Nothing
here originates in any employer's internal documentation.

---

## Design principles

These are the positions the framework takes. They're arguable, which is
the point — a framework with no position is a table of contents.

1. **Extend, don't replace.** Organisations with mature GxP already have
   risk assessment, change control, supplier qualification, and periodic
   review. AI needs new *decision branches* inside those, not a parallel
   apparatus. This is also the only credible route to a short timeline.
2. **Proportionality is the product.** If governance doesn't let most
   low-risk uses through quickly, it will be routed around. Speed comes
   from proportionality, not from lowering the bar.
3. **Consequence, not category.** "Is this AI?" is a definitional debate
   with no regulatory consequence attached. What matters is what the
   output touches and what happens when it's wrong.
4. **The control must be evidenced, not asserted.** "Human in the loop"
   is not a control until you can say whether the human reviews every
   output, a sample, or none — and show the review is effective.
5. **Adoption is a first-class part of the framework.** Most frameworks
   fail on human factors, not design. Part 5 exists because of that.

---

## Part 1 — DECIDE
### *"Does this need governing, and how much?"*

The intake decision. Everything downstream is sized by this, and it must
produce the same answer regardless of who runs it.

| Component | Notes |
|---|---|
| **Scope trigger** | What brings a system into this framework at all — including AI arriving inside a vendor release that wasn't procured as AI |
| **Context of Use statement** | The unit of assessment. Intended use, user population, decision it supports, boundaries |
| **Classification** | Model influence × decision consequence, resolved by a fixed matrix rather than debate |
| **Proportional assurance tier** | The output: what depth of assurance this use case earns |
| **Hard exclusions** | Uses that are refused regardless of controls offered (e.g. AI executing an electronic signature, releasing a batch, closing a CAPA autonomously) |
| **Re-triage triggers** | Model retraining, changed intended use, **vendor-notified model change**, drift breach, related CAPA, new jurisdiction, final publication of pending regulatory texts |

**Integrates with:** the organisation's existing system risk assessment
questionnaire and GxP impact assessment — as added branches, not a new
form.

**Anchors:** GAMP 5 (2nd ed) risk-based approach · FDA context-of-use and
model-influence framing · ISPE GAMP AI Guide lifecycle entry.

---

## Part 2 — BUILD
### *"How do we specify, develop, and qualify it?"*

Lifecycle integration. Deliberately mapped onto **Concept → Project →
Operation → Retirement**, because that is the lifecycle a GxP
organisation already runs and the same one the ISPE AI Guide is
structured on.

**Concept** — business need, context of use, initial risk assessment,
feasibility, evaluation criteria agreed *before* a proof of concept
begins.

**Project** — requirements with **measurable acceptance criteria**
(the single most common gap); data and model specifications;
train/validation/test segregation; independent evaluation against a
held-out set; traceability from requirement to evidence.

**Operation** — handover, monitoring, incident and deviation handling,
change and configuration management, periodic review.

**Retirement** — data retention, model archival, evidence disposition.

**The recurring gap:** requirements written as intentions ("the system
shall be accurate") rather than as testable statements with thresholds.
An AI requirement that can't be failed can't be validated.

---

## Part 3 — CONTROL
### *"What does AI need that conventional CSV doesn't cover?"*

Four control sets that are genuinely new. Everything else is CSV you
already do.

**3.1 Data governance** — provenance and lineage; curation, labelling,
versioning; representativeness for the target population; ALCOA+ applied
to inputs, training data, **prompts**, and outputs; cross-border transfer.

**3.2 Model governance** — model registry and versioning; a model
documentation standard; performance thresholds defined in advance;
baseline freeze at qualification; explainability evidence proportionate
to tier.

**3.3 Human oversight design** — decision rights; what the human
actually does; **automation-bias controls**. A confident, fluent,
well-formatted wrong answer is the failure mode conventional CSV never
had to handle.

**3.4 Supplier and third-party oversight** — qualification of
AI-as-a-service; **contractual model-change notification**; audit
rights and evidence expectations; sub-processor and model supply chain.

> **3.4 is the one most frameworks under-serve and most organisations
> most need.** In a vendor-hosted estate, the model underneath a
> validated system can change on the vendor's release cycle with no
> notification, no change control trigger, and no visible difference in
> the interface. Sponsor responsibility is not delegable.

---

## Part 4 — SUSTAIN
### *"How do we stay validated?"*

Frameworks decay, and AI frameworks decay faster than conventional CSV
for four reasons worth stating explicitly in the document:

1. **The regulatory baseline moves** — pending Annex texts, FDA
   finalisation, EU AI Act phase-ins. Expect substantive revision.
2. **The estate grows faster than the governance** — every vendor
   release can introduce AI that wasn't procured as AI, so the inventory
   goes stale silently.
3. **Models degrade quietly** — conventional software fails loudly; a
   drifting model keeps producing plausible output.
4. **Knowledge concentrates in two or three people** — and surfaces as a
   single point of failure during an inspection.

**Components:** performance and drift monitoring with defined thresholds
· revalidation triggers · periodic review by tier · inventory
reconciliation · regulatory horizon-scanning with a re-triage trigger on
publication of final texts.

---

## Part 5 — ADOPT
### *"Will people actually work this way?"*

**The part most frameworks skip, and the one that decides whether the
rest of it matters.**

A framework that is technically correct and behaviourally ignored has
failed. The observed failure pattern in small and mid-size organisations
is not an absent model — it's imported habit: experienced people
applying the defaults of a larger organisation to a context with
different constraints.

| Component | What it addresses |
|---|---|
| **Role-based capability** | What QA, CSV, IT, system owners, and business users each need to know — different depths, not one training deck |
| **Explicit unlearning** | Naming the big-organisation defaults that don't transfer: validate everything · a team exists for that · the SOP will say · vendor evidence isn't enough |
| **Decision rights & escalation** | Who decides, who is consulted, and what happens at disagreement |
| **First decisions in a room** | The first three classifications run live, together, not circulated as a document |
| **Governance body** | Council or equivalent — sized to the organisation. Effectiveness varies materially with company size; a big-pharma council structure transplanted into a mid-size org is friction, not control |

---

## Part 6 — PROVE
### *"What do we hand an inspector?"*

Evidence and inspection readiness — the framework's output, not an
afterthought.

Inventory of AI-enabled systems with classification · classification
records with reasoning · specification-to-evidence traceability ·
independent evaluation results · monitoring records and threshold
breaches · change control and re-triage history · supplier
qualification evidence including model-change notifications · training
records · periodic review outcomes.

**Plus a standards mapping** for procurement and executive audiences —
useful for credibility, but not the spine of the framework.

---

## §7 — Sources

Public regulatory and standards sources this structure is built on:

- **ISPE GAMP 5: A Risk-Based Approach to Compliant GxP Computerized
  Systems (2nd Edition)**
- **ISPE GAMP Guide: Artificial Intelligence** — lifecycle-structured,
  which is the basis for the integrate-don't-replace position
- **FDA draft guidance** on AI to support regulatory decision-making for
  drug and biological products — context of use, risk-based credibility
  assessment, model influence × decision consequence
- **EMA Reflection Paper** on AI in the medicinal product lifecycle
- **Joint FDA–EMA Guiding Principles of Good AI Practice in Drug
  Development**
- **EU GMP Annex 11 (revision) and draft Annex 22** on AI
- **ICH E6(R3)** — computerised systems, data governance, and
  non-delegable sponsor oversight of service providers
- **ISO/IEC 42001** (AI management system), **42005** (impact
  assessment), **23894** (AI risk management)
- **EU AI Act** — horizontal obligations and phase-in dates
- **NIST AI Risk Management Framework**

> **Before any client use:** verify the current status, version, and
> publication date of every source above. Several are drafts with moving
> finalisation dates, and citing a superseded version is the fastest way
> to lose a technical audience.

---

## §8 — Deliberately out of scope

Stating exclusions is what makes a framework usable rather than
aspirational.

- **Tool and platform selection** — process first; tooling follows
- **Model development methodology** — this governs, it doesn't teach
  data science
- **Non-GxP AI** — referenced for inventory completeness only
- **Cybersecurity** — interfaces with, does not replace, the existing
  security programme

---

## §9 — Content harvest map

Each part yields publishable material in the three-beat format
(*what the standard says → what actually happens → what to do instead*).
One pass, two outputs.

| Part | Post |
|---|---|
| 1 | "Is this AI?" is the wrong question ✅ *published* |
| 5 | Big-pharma governance breaks at mid-size ✅ *scheduled* |
| 3.4 | Your vendor is going to change the model ✅ *published* |
| 2 | An AI requirement that can't be failed can't be validated |
| 1 | The five things that should refuse an AI use case outright |
| 3.3 | "Human in the loop" is not a control |
| 4 | Why AI frameworks decay faster than CSV |
| 6 | What an inspector will actually ask for |
| 5 | Governance councils don't transplant between company sizes |
