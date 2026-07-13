# Newsletter #10 — Our Test Suite Found 11 Holes in Our Own Safety Rules. Good.

*EVOLV build log · July 2026*

---

**TL;DR:** We shipped a standing eval suite that attacks every EVOLV
agent with 125 deterministic checks on every change. Its first full run
found 11 real gaps in our five hard-exclusion rules — the rules that
stop AI from signing signatures, releasing batches, or writing to
validated records. All 11 were fixed the same day. This issue is the
unedited story, because how a vendor finds their own holes tells you
more than any brochure.

---

## The setup

If you've read this newsletter before, you know EVOLV's exclusion list:
five deployment shapes we refuse regardless of revenue. AI executing an
e-signature (21 CFR §11.50). AI releasing a batch (QP responsibility).
AI closing a CAPA (§820.100). AI making clinical decisions (SaMD — not
our product). AI writing to validated records without a human gate
(§11.10(e)).

Those rules are enforced in code — pattern matching over the customer's
own description of what they want the AI to do. Type "AI closes CAPAs
automatically" into our screener and rule EX-3 fires, with the citation.

Rules enforced in code have a failure mode: the code.

## The bet

Salim Ismail calls the first pillar of trustable agentic systems
"Trusted Evals" — every agent runs continuously against a known test
set, so drift gets flagged before customers see it.

We'd built a skeleton of this months ago for one agent. This sprint we
extended it to all of them: 125 deterministic checks — the risk engine's
full mapping matrix including the patient-safety override, the test
generator's routing depths, the change-impact logic, the validated-state
scoring tiers, and 95 adversarial scenarios thrown at the exclusion
rules, half of them machine-generated variations designed to sneak past.

First full run: **114 of 125 passed.**

Eleven didn't.

## The eleven

Three categories, each more instructive than the last.

**1. The vocabulary hole.** Our rules looked for the word "AI."
*"The LLM alters each validated record"* sailed through. So did "the
model." The intent was identical; the noun was different. If your
guardrails are keyword-based and your keywords are narrow, your
guardrails are decorative.

**2. The grammar holes.** *"The AI authorises the electronic
signature"* — missed, because we'd only listed the American spelling.
*"The AI signs off the deviation"* — missed; we had "closes" and
"resolves" but not "signs off." *"AI recommends treatment"* — missed,
because a previous fix had added "recommend treatment" but not the
third-person form. Every one of these is the kind of gap you only find
by generating hostile variations at scale — which is exactly what the
eval factory does.

**3. The scary one.** *"AI writes to the controlled document without
review."* Our EX-5 rule has a suppressor: if the statement describes a
human gate ("...after QA sign-off"), it shouldn't fire. The suppressor
looked for the word "with" followed by words like "review" or
"approval."

"with**out** review" contains "with." Followed by "review."

The rule saw a human gate in a sentence that explicitly said there was
none. A statement describing the exact violation the rule exists to
catch was being waved through *by the safety mechanism itself.*

We also found the mirror image: two false positives, where the rules
fired on safe statements like "AI signs a summary email; the CSV lead
signs the electronic signature" — matching across the sentence boundary
and attributing the human's action to the AI. Guardrails that cry wolf
get disabled; that failure mode matters too.

## The fixes

Same day: subjects widened (ai / llm / model), all matching bounded
inside a single clause so rules can't straddle sentences, the missing
verb forms added, and the suppressor now requires "with" as a whole
word. The suite re-ran: 125/125. The 84 scenarios that passed before
still pass — that's the other job of an eval suite, catching the fix
that breaks something else.

And because our public website runs the same rules in its live
screener, the browser version was updated in the same commit. If the
engine and the demo can drift apart, one of them is lying.

## Why publish this

Because the alternative is the industry default: "our AI is safe," full
stop, and the holes get found by an inspector in your data instead of a
test suite in ours.

The honest claim was never "no holes." It's: the holes get hunted,
found, fixed, and pinned by a regression suite that runs on every
change — and the whole loop is visible to you. That's what
"validated" has always meant. We're just applying it to ourselves.

**The current number: 215+ standing checks across every EVOLV agent,
100% passing, re-run on every change.** When that number dips, we'll
know before you do. That's the whole point.

---

*Want to attack the rules yourself? The screener on evolifeval.com runs
them live in your browser — several readers will try "AI closes CAPAs
when the fix is verified." EX-3 is waiting for you.*

*Evaluating AI for your validation workflow? 15 minutes, bring your
hardest use case: sreejith@evolifeval.com*

---
*Sree · Founder, EVOLV | The Validation Factory*
*Powered by EVOLV | A WingstarTech Inc. Product*
