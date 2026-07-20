# Newsletter #11 — We Built the Vendor Side of the Framework

*EVOLV build log · July 2026*

---

**TL;DR:** Nuno Valério's Trust Architecture #15 named the
largest unaddressed risk in pharma AI: sponsors are accountable
for vendor AI they cannot inspect. He listed five questions every
buyer should ask at procurement — and noted most vendors can't
answer them. We spent the week making EVOLV the vendor that
answers all five with product artifacts, not promises. This
issue walks through what shipped.

---

## The problem, in one anecdote that isn't ours

A clinical ops director deploys a CRO's AI tool for patient
matching. She asks for the validation documentation. The vendor
says it's proprietary. She is now accountable — under GxP, the
EU AI Act, the FDA-EMA principles — for the outputs of a system
she cannot inspect. "The vendor told us it's validated" is not
governance. It's faith.

That's the buyer's side. We're on the other side of that table:
EVOLV is an AI vendor selling into pharma. So we read the five
questions as a spec.

## Question 1: "How was it validated — can we review the documentation?"

**Shipped: the AI Vendor Transparency Dossier.** One API call
returns a signed PDF that answers all five questions — and
here's the part that matters: it's assembled from **live
platform data at generation time**. The eval suite actually
executes. The audit chain is actually verified. The version
registry is snapshotted. The document cannot be stale
marketing, because it isn't written — it's generated.

## Question 2: "How will we be notified when the model is updated?"

Nuno calls this the dealbreaker: *"You cannot do change control
on a system that changes without your knowledge."*

**Shipped: the Model & Version Registry.** Every moving part in
EVOLV — twelve components: deterministic engines, LLM-backed
functions, upstream foundation models, the regulatory corpus,
the eval harness — declared with a version and, crucially, a
**"governed by"** column naming the mechanism you can use to
verify it independently. Plus a customer-facing changelog of
behaviour-relevant changes, including the honest entries
("screening verdicts may differ from v1.0.0 on edge-case
phrasings — in the safe direction").

And the part we're proudest of: **upstream drift detection.**
EVOLV consumes foundation models that can change without notice
— the exact ungoverned-change problem, one level up the supply
chain. So every model API response is checked against the
registry declaration at runtime. A mismatch writes an
UPSTREAM_MODEL_CHANGED event to our hash-chained audit trail.
We govern our AI suppliers by the standard our customers govern
us. Ask your current vendors what happens in their stack when
OpenAI silently updates a model. Then ask us.

## Question 3: "Can we run independent testing on our own data?"

**Shipped: the bring-your-own-golden-set harness.** Write a JSON
file of YOUR requirements with YOUR expectations — keywords
that must appear, frameworks that must be cited, the
criticality you expect. Run one command in your deployment. You
get results in exactly the format our own Trusted Evals produce
— so your independent numbers and our claimed numbers are
directly comparable. No vendor involvement required. That's
what "independently verify their accuracy metrics in your
operational context" looks like as a shipped feature.

## Question 4: "What happens when the model is wrong in our process?"

**Shipped: the AI Incident & Deviation Runbook.** The ownership
split, in writing: you own the deviation (every EVOLV output
enters your validated record through a named human signature —
that accountability never transfers to the AI). We own the
investigation of the AI's contribution — and it's mechanical,
not forensic, because every AI decision already stored its full
reasoning chain, hash-linked to the audit trail. Replay the
Logic Archive, classify the root cause, assess the blast
radius. With SLAs.

Two clauses you won't find in most vendor runbooks: an incident
only closes when **a new eval pins the failure permanently**
(the bug becomes a regression test — exactly what happened
earlier this month when our own suite found 11 gaps in our
exclusion rules; all 11 are now permanent evals), and a written
**walk-away trigger**. A governance framework without a
walk-away threshold is a brochure.

## Question 5: "How does this comply with the EU AI Act?"

**Shipped: the mapping document.** Articles 9 through 15, 17,
and 72, each mapped to the specific EVOLV mechanism — risk
management to the Bounded Autonomy Profile, record-keeping to
the chained audit trail, human oversight to the signature
gates, accuracy to the CI-gated eval suite. And two items
marked as gaps with plans, because a compliance mapping with no
gaps is a compliance mapping nobody checked.

## One more thing: "validated" is now a time series

Every eval-suite run — from CI, from the Dev Portal, from
dossier generation — now appends to a history log with a trend
endpoint. Not "we passed validation once." A pass-rate curve
you can watch. If it ever dips, we'll know before you do — and
so will you, because you can query it.

## Why this matters beyond us

The regulatory trajectory is moving toward full lifecycle
transparency for AI in regulated environments. Vendors who
can't answer the five questions will eventually be locked out
of pharma — as they should be. We'd rather be early than
locked out. And frankly: we'd rather compete on evidence than
on demos.

**The current stack, in numbers:** 131 standing evals gating
every change · 12-component version registry · hash-chained
audit trail, verifiable by API · 4-page live-generated
Transparency Dossier · 10/10 security-audit findings closed.

---

*Evaluating AI vendors this quarter? Send the five questions to
all of them. Then ask us for the dossier — it's one API call,
generated fresh: sreejith@evolifeval.com*

---
*Sree · Founder, EVOLV | The Validation Factory*
*Powered by EVOLV | A WingstarTech Inc. Product*
