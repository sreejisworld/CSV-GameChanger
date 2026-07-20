# EVOLV AI Incident & Deviation Runbook

**Answers the vendor-governance question:** *"What happens when
the model produces an incorrect output in our process? Who
investigates? Who owns the deviation?"*

**Scope:** any EVOLV AI output that is wrong, misleading, or
unexpected in a customer's validated workflow. Version 1.0 ·
Sprint 49 · owned by WingstarTech Inc.

---

## 1. Definitions

| Term | Meaning |
|---|---|
| AI Incident | An EVOLV AI-drafted artefact (UR/FR, risk class, test step, CIA, score) that is incorrect or unsafe, discovered at any point |
| Blocked incident | Caught by a platform control (VerificationAgent rejection, BAP exclusion, human reviewer refusal) **before** entering the validated record |
| Escaped incident | Human-signed into the validated record before discovery — a customer deviation AND a vendor incident |

## 2. Ownership (the non-negotiable)

- **The customer owns the deviation.** Every EVOLV output enters
  a validated record only through a named human signature
  (21 CFR §11.50). The signer's accountability is not
  transferred to the AI or to EVOLV — this is by design.
- **EVOLV owns the investigation of the AI's contribution**:
  why the draft was wrong, whether the class of error is
  systemic, and what changes (rules, evals, prompts) prevent
  recurrence.
- Neither party may close an incident unilaterally: customer
  closes the deviation; EVOLV closes the vendor incident with a
  documented correction (see §5).

## 3. Detection channels

1. VerificationAgent rejection → logged `COMPLIANCE_EXCEPTION`
   (blocked; review weekly for patterns, no per-event SLA).
2. Human reviewer edit/rejection during signing (blocked).
3. Test execution failure / defect traced to an AI-drafted
   artefact (escaped).
4. Customer report via sreejith@evolifeval.com (escaped).
5. `UPSTREAM_MODEL_CHANGED` audit event — treat as a potential
   incident trigger: review outputs generated since the change.

## 4. Investigation protocol (escaped incidents)

| Step | Action | Owner | Target |
|---|---|---|---|
| 1 | Acknowledge report, assign incident ID | EVOLV | 1 business day |
| 2 | **Logic Archive replay** — pull the hash-linked reasoning chain for the exact output; re-derive the decision from recorded inputs | EVOLV | 3 business days |
| 3 | Classify root cause: corpus gap · retrieval miss · rule/matrix defect · upstream model change · input ambiguity | EVOLV | with step 2 |
| 4 | Blast radius: query the audit trail for other outputs sharing the root cause; notify customer of affected artefacts | EVOLV | 5 business days |
| 5 | Customer disposition of affected records (re-review / re-validate per their SOP) | Customer | per their QMS |

The Logic Archive makes step 2 mechanical, not forensic: every
AI decision already stores inputs, steps, and outputs,
hash-chained to the audit trail.

## 5. Correction & closure

An EVOLV incident closes only when ALL of:
1. Root cause documented and shared with the customer.
2. **A new eval pinning the failure** is added to the Trusted
   Evals suite (the bug becomes a permanent regression test —
   see Sprint 44 precedent: 11 gaps → 11 evals → fixed).
3. The fix ships and the changelog entry lands in the Version
   Registry (`/versions/registry`).
4. Customer confirms disposition of affected records.

## 6. Escalation & walk-away trigger

If the same root-cause class recurs after correction, the
customer is entitled to: a joint review with the founder, the
full eval history for the affected component
(`/evals/history`), and — per the pilot agreement — exit with
all work product. We put this in writing because a governance
framework without a walk-away threshold is a brochure.
