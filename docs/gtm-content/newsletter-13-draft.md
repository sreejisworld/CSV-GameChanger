# Newsletter #13 — I Graded EVOLV Against a Big Pharma's AI Rulebook. Here Are the Lines We Failed.

*EVOLV build log · July 2026*

---

**TL;DR:** A top-tier pharma's internal standard for putting AI
agents into GxP systems is, if you read it honestly, a vendor
acceptance test. So I graded EVOLV against every line — gaps
included. We were strong on the hard, un-fakeable part (guardrails,
access control, tamper-evident audit, 130+ standing evals,
reproducibility) and had two real gaps at the edges: input PII
screening and dependency resilience. (Anonymised throughout — a
buyer's internal document isn't mine to name.) This week we closed
both and
wired them into the eval suite so they *stay* closed. Below: the
scorecard, the gaps I'm not hiding, and why "grade us against your
own rulebook" is the most honest pitch I can make.

---

## The rulebook nobody publishes

Every serious pharma is quietly writing the same document right
now: an internal standard for how AI agents may be built, secured,
observed, and deployed inside GxP systems. Which frameworks are
allowed. What guardrails are mandatory. How every input, output,
and decision gets logged. What must be in a registry before it
touches production. And a sober table of failure modes — tool
misuse, hallucination, prompt injection, sensitive-data
disclosure — each with the control expected against it.

I got to study one of these standards in detail. And here's the
thing: it isn't a philosophy deck. It's an acceptance test. Every
line is something a buyer will eventually hold a vendor to.

Most vendors would skim it and nod. I decided to do the
uncomfortable thing instead — score EVOLV against every line, and
publish where we fell short.

## Where EVOLV was already strong

The good news first, because it's the part that's hard to fake:

- **Guardrails.** Bounded-autonomy exclusions that refuse the
  deployments no control should allow (an AI executing a signature,
  releasing a batch, closing a CAPA).
- **Access control.** Attribute-based, not just role-based — a
  training-status gate that revokes "approve" the moment training
  lapses; locked records that can't be edited after signature.
- **Observability & audit.** A hash-chained, tamper-evident audit
  trail where every AI decision carries a replayable reasoning
  archive. Edit one row and every row after it breaks.
- **Standing evals + reproducibility.** 130+ deterministic checks
  gating CI, plus a harness proving the deterministic engines give
  byte-identical output on the same input.

That's the spine most tools are thin on. EVOLV isn't. But the
edges are where honesty lives.

## Where it failed — and I'm telling you

Two gaps. Real ones.

**1. Real-time PII/PHI screening on inputs.** EVOLV sends
requirement text to external models for embeddings and retrieval.
Nothing was scanning that text for a patient name, an MRN, or an
SSN *before* it left the tenant. In a GxP shop that's exactly the
"sensitive-input disclosure" line on the standard — and we didn't
have a control on it.

**2. Dependency resilience.** Around those same external calls sat
a single generic error handler. No retry on a transient network
blip. No circuit breaker when the provider was down — just a
request hanging behind a timeout, one after another. Fine in a
demo. Not fine in production, and the standard says so plainly.

There's a third, an interop bridge into a specific observability
stack, that I'm still closing. Named, planned, not done. I'd
rather tell you that here than let you find it in an evaluation.

## What I shipped this week

**The PII shield.** A deterministic screen that runs at the tenant
boundary, before any text reaches an external model. It detects
email, phone, SSN, card numbers, IP, date of birth, medical record
numbers, and patient names, with four modes — off, warn, redact,
block. Default is *warn*, so nothing changes until you choose to
enforce. The part I care about most: it records **category counts
only, never the raw value** — so the safety log never becomes a
second copy of the very PII it's protecting. A control that leaks
what it guards isn't a control.

**The resilience layer.** Retry with bounded exponential backoff —
but only on *transient* errors, because you don't retry a bad
request. A circuit breaker per dependency that fails fast when a
provider is down and recovers on a single trial call. And a health
signal derived from breaker state. Hand-rolled, zero new
dependencies — in a validated system, every library you add is one
more thing you have to qualify and CVE-scan forever.

And the part that separates a claim from evidence: **both are now
covered by the standing eval suite — 153 deterministic checks
across 9 specialist functions — re-proven on every CI run.**
Building a control is easy. Proving it still works next quarter is
the actual job.

## Why I'm publishing the gaps

Naming your own open gaps is the most trust-building thing a vendor
can do. Anyone can send a glossy compliance matrix with every box
green. Almost no one will hand you the exact line items where they
fell short — and the commit that fixed them, days later.

It's the same move as making EVOLV generate its own validation
package: if a standard is good enough to sell against, it's good
enough to be graded by, in public. A tool that can't survive being
pointed at itself shouldn't be pointed at your quality records.

## The offer

Have your own internal standard for agentic AI in GxP — even a
rough draft? **Send it.** I'll score EVOLV against it line by line
and show you exactly where we're green, where we're a gap, and what
closing each gap would take. Not a slide. A scorecard, with the
gaps left in. sreejith@evolifeval.com

**The stack, in numbers:** 153 deterministic evals across 9
specialist functions · 0 raw PII values ever written to the audit
trail · 2 gaps found and closed this week · 1 named and still open.

---

*Evaluating AI for a GxP system this quarter? Hold every vendor —
EVOLV included — to your own internal standard, and ask them to
show you the lines they fail. sreejith@evolifeval.com*

---
*Sree · Founder, EVOLV | The Validation Factory*
*Powered by EVOLV | A WingstarTech Inc. Product*
