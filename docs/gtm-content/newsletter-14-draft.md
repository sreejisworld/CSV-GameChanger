# Newsletter #14 — What FDA Is Citing in 2026, and How EVOLV Prevents Each One by Design

*EVOLV build log · August 2026*

---

**TL;DR:** FDA's 2026 computer-system findings cluster into six
themes under 21 CFR 211.68 — shared logins, missing or disabled
audit trails, unvalidated systems, backdated records, deletable
data, and now AI used without controls. I mapped EVOLV against
every one. Four we already prevent structurally; two edges I found
while doing this analysis and closed this week — a unique-user
attribution guard and a startup audit-trail integrity check. The
point isn't "EVOLV can fix a finding." It's that the architecture
is built so most of these can't be committed on the platform in
the first place.

---

## The list nobody wants to be on

If you read FDA's 2026 drug-GMP warning letters, the
computer-related observations keep landing on the same handful of
themes — and they're almost always framed as a failure to
"exercise appropriate controls over computer or related systems"
under **21 CFR 211.68**. Industry analyses of 2026 letters put
data integrity in the majority of drug-GMP letters — often cited
in the **60–80%** range — and it's usually entangled with a
computer-system control that was missing or switched off.

So I did the uncomfortable exercise: take each recurring finding
and ask one blunt question of EVOLV — *can a user even commit this
mistake on our platform?*

## The six themes, and how EVOLV prevents each

| # | What FDA cites | 211.68 clause | How EVOLV prevents it |
|---|----------------|---------------|-----------------------|
| 1 | Shared logins, no unique IDs, unattributable changes | (b) — only authorized personnel | **Attribution guard (new this week):** EVOLV refuses to record a *human decision* (a signature/approval) against a shared or generic identity like "SYSTEM" or a role name. Plus attribute-based access control with a training-status gate, and Part 11 signatures capturing name · role · meaning · UTC. |
| 2 | Missing or disabled audit trails | (b) — changes documented | There is **no "off" switch.** Every action flows through one append-only, hash-chained trail; edit one row and every row after it breaks. A **startup integrity check (new this week)** verifies the chain at boot and, in enforce mode, refuses to run on a broken one. Full-chain verification is available on demand. |
| 3 | Unvalidated / poorly validated systems | (a) — appropriate controls | **EVOLV validates itself:** one call generates its own Validation Plan, IQ, OQ, and a full requirements-traceability matrix (270+ requirements) from live evidence. 159 deterministic checks gate CI on every push; the deterministic engines are proven byte-identical on repeat runs. |
| 4 | Falsified / backdated electronic records | 211.68 + .194 + .188 | You **cannot backdate.** Every record's timestamp is the server's own UTC clock, never a user-supplied value; any alteration to a past row breaks the hash chain and is caught by verification. |
| 5 | Deletable data / weak backup | (b) — backup, no loss | **Deletion can't hide.** Append-only writes plus hash-chaining mean a removed or altered row breaks the chain; record the chain-head hash externally (QA log, ticket) to detect even wholesale truncation. (Pair this with your infrastructure backup — that layer is yours.) |
| 6 | AI-assisted tools without controls | (a) + general CGMP | The entire platform. AI **drafts**, but a set of five hard exclusions means it may never execute a signature, release a batch, or close a CAPA. AI decisions are logged, the substantive ones with a **replayable reasoning archive**; an independent verification pass checks the draft; a human signature gate stands before anything enters a validated record; model versions sit in a registry with a change-notification commitment. |

## What I shipped this week (the two edges)

Being honest: doing this mapping, I found two places EVOLV wasn't
yet prevention-tight. So I closed them.

**1. Unique-user attribution.** EVOLV's API captured the actor from
a request header and, if it was missing, quietly defaulted to a
generic "SYSTEM" identity. Fine for automated plumbing — *not* fine
for a human sign-off, which is exactly the "shared login /
no attribution" finding. Now a signature or approval recorded
against a shared or generic identity is **refused** (enforce mode)
or **flagged** (warn mode) before it can ever enter the trail.

**2. Startup trail integrity.** The audit trail was tamper-evident,
but nothing verified it at boot — the platform would have happily
run on a truncated or altered trail. Now EVOLV **verifies its own
chain at startup** and, in enforce mode, refuses to serve on a
broken one. It checks its own memory before it opens the doors.

Both are covered by the standing eval suite — now **159
deterministic checks across 10 components** — so they don't quietly
regress. Building a control is easy; proving it still holds next
quarter is the job.

## The line that's coming for everyone: AI is now in scope

The newest thread in 2026 letters is FDA citing **AI-assisted tools
used in GMP decisions without validation, traceability, or
control** — no record of how an AI output was generated, what data
it used, or how it influenced a decision. Regulatory commentary is
explicit: AI tools are computerized systems under CGMP, so they owe
the same 211.68 controls as anything else — validation, traceability,
and no opaque decision paths.

That is the exact problem EVOLV was built around. AI doesn't sit
outside 211.68 — and on EVOLV, it doesn't sit outside the controls
either.

## Prevent, don't remediate

The pattern under every one of these findings is the same: a
control that would have prevented it either wasn't there, or wasn't
switched on. EVOLV's answer is to make the control **structural and
on by default** — so the mistake isn't something you remediate
after an inspector finds it. It's something the system won't let
you make.

**The stack, in numbers:** 6 FDA themes mapped · 4 prevented by
existing architecture · 2 edges closed this week · 159 deterministic
checks across 10 components · in enforce mode, 0 human decisions
recordable against a shared identity.

---

*Evaluating an AI or CSV tool this quarter? Ask it to show you which
of these six it prevents by design — and which it only helps you
document after an inspector finds it. sreejith@evolifeval.com*

*(This mapping is my own reading of how EVOLV's controls line up
against publicly discussed 211.68 themes; it isn't legal or
regulatory advice.)*

---
*Sree · Founder, EVOLV | The Validation Factory*
*Powered by EVOLV | A WingstarTech Inc. Product*
