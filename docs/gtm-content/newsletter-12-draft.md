# Newsletter #12 — Who Validated the Tool That Validates Everything Else?

*EVOLV build log · July 2026*

---

**Update (after publication):** Following a sharp comment from
Dori Gonzalez (CEO, ProcellaRX), I've sharpened the GAMP-
classification language throughout this piece. The short version:
*how you classify a validation tool depends on which side of the
fence you stand on.* A customer deploying a SaaS tool runs a
risk-based supplier assessment (typically Category 3/4); a vendor
validating its own bespoke code is doing Category 5 work from its
own SDLC. The original draft blurred the two — thanks, Dori. The
distinction below is better for it.

---

**TL;DR:** A validation platform is software you have to trust
with your GxP records — so the fair question is whether its
vendor can show you real validation *evidence you can leverage*,
not a slide. Most hand you a supplier questionnaire and a SOC 2.
This week we made EVOLV generate its own complete validation
package — Validation Plan, IQ, OQ, and a 253-requirement
traceability matrix — on demand, from live evidence, so a
deploying customer can leverage our activities and do less. This
issue is about that recursive move, and why it's harder to fake
than a slide.

---

## The question nobody enjoys being asked

Here's an uncomfortable one for any validation-software vendor.
Your tool authors, executes, and stores GxP validation records.
That makes it a computer system in a regulated process, and its
outputs are ones an inspector can question.

One clarification up front — the one Dori pushed me to sharpen:
*classification depends on which side of the fence you stand on.*
When a **customer deploys** a SaaS validation tool, that's a
risk-based **supplier assessment plus validation of intended
use** — typically GAMP Category 3/4, and rightly a
leverage-the-supplier, least-burden exercise under GAMP 5's
second edition and FDA's CSA guidance. Nobody should be told they
owe a full Category 5 validation to switch on a SaaS tool. When a
**vendor validates its own bespoke code** — which is what this
piece is about — that's Category 5 work from *our* SDLC. Same
tool, two lenses. The question that holds across both is the same.

So: **who validated your tool, and can I leverage that
evidence?** Not "is it ISO-certified." Not
"here's our SOC 2." Show me the Installation Qualification, the
Operational Qualification, and the requirements traceability
matrix — for the software I'm about to let touch my quality
records.

Most vendors go quiet, or send a supplier-assessment
questionnaire and ask you to trust the answers. That's the same
"trust us, it's validated" posture that fails an inspection when
it's *your* AI vendor saying it — I wrote about that last month.
Turning it on ourselves felt only fair.

## What we built: EVOLV's own validation package, generated live

One API call now produces a signed, 12-page validation package
for the EVOLV platform itself:

- **Validation Plan** — our own bespoke software, validated by a
  risk-based V-model (Category 5 from *our* SDLC; a deploying
  customer's exercise is the risk-based Cat 3/4 one described
  above). The same lifecycle EVOLV runs for customers, run on
  EVOLV.
- **Installation Qualification** — the verifiable install
  baseline: pinned dependency manifest with security floors,
  container status, CVE-audit status (clean, re-checked in CI on
  every push), and the required environment.
- **Operational Qualification** — and this is the part that
  can't be faked: the **eval suite executes live at generation
  time**. 136 deterministic test cases across 7 specialist
  functions. The number in the document is the number from three
  seconds ago, not a screenshot from a good day.
- **Requirements Traceability Matrix** — all **253 requirements**
  from EVOLV's living URS index, each traced to its
  implementation *and* to its objective verification evidence
  (which eval group proves it). 82% map to a specific automated
  test; the rest to code review under the CI compliance gate.
- **21 CFR Part 11 manifestation of signature.**

The recursive part is the point: EVOLV is validated *by EVOLV's
own methodology* — traceability-first, risk-based, every claim
backed by executable evidence. If the methodology is good enough
to sell, it's good enough to survive being pointed at itself.

## The hardest requirement: same input, same output

For AI in a validated environment, one property matters more
than any feature: **reproducibility.** If the same input can
produce a different decision tomorrow, the system cannot be
validated — full stop.

So we built a harness that runs each deterministic engine
repeatedly on a fixed input and proves the output is
**byte-identical**, every time. It's now part of the eval suite,
so reproducibility is re-proven on every single CI run.

And here's the honest boundary, stated the way a validation
reviewer needs it: the **deterministic core** — risk scoring,
test-script construction, the exclusion screen, the UR/FR
transform, validated-state scoring — is provably
bit-reproducible. The **LLM-assisted parts** (drafting a
requirement, reviewing a draft) are deliberately *not* held to
bit-reproducibility, because that's not how you control them.
They're controlled by structured outputs, an independent
verification pass, and a human signature gate before anything
enters a validated record. We draw that line explicitly in the
package rather than pretending the whole system is deterministic.
The honesty is the control.

A small thing that made me smile: the reproducibility harness
found a difference on its very first run — a wall-clock timestamp
embedded in a reasoning narrative. Not a decision defect, just a
provenance stamp. But the harness flagged it, we looked, we
understood it, we handled it. That's the entire point of having
one.

## Why this is hard to fake

A validation package you *write* is a document. A validation
package that's **generated from the running system** — eval
suite executed, dependency baseline read off disk, traceability
parsed from the live requirements index — is evidence. The
difference is whether it's still true five minutes after you
wrote it. Ours is regenerated fresh on every request, and it's
signed.

## The line I'd put in front of any evaluator

Ask your current validation vendor for their tool's IQ and OQ —
built for their tool, by their tool's methodology, with the test
evidence executed live. Then ask us. The gap in the answers is
the whole pitch.

And to be clear about *why* it matters: this isn't "more
documents." It's the opposite. Real supplier evidence is
something you **leverage** — it lets your team do less,
risk-based, exactly the leverage principle GAMP 5's second
edition asks for. Evidence you can re-derive beats paperwork you
file.

**The stack, in numbers:** 253 requirements traced end-to-end ·
136 deterministic evals gating CI · deterministic engines proven
byte-reproducible · a 12-page validation package generated on
demand and signed.

---

*Evaluating validation platforms this quarter? Ask each vendor to
generate their own validation package on the spot. We can:
sreejith@evolifeval.com*

---
*With thanks to Dori Gonzalez (ProcellaRX) for the challenge that
sharpened the classification section — this is the conversation
the field needs more of.*

*Sree · Founder, EVOLV | The Validation Factory*
*Powered by EVOLV | A WingstarTech Inc. Product*
