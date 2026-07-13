# EVOLV 15-Minute Demo Script — Golden Path

**Goal of the call:** not to show every feature — to get the
prospect to say yes to a 6-week pilot. Everything in this script
drives to that ask.

**Audience calibration (first 60 seconds of small talk):**
- QA Head / CSV Manager → lead with inspection survival
- VP Regulatory Affairs → lead with framework citations
- CTO / CDO → lead with AI governance (BAP)

---

## Pre-demo checklist (5 min before the call)

- [ ] API server running (`uvicorn API.main:app --port 8000`)
- [ ] React platform running (port 5180), warm-light theme
- [ ] Demo project loaded (Cmd+K → "Open Demo project")
- [ ] One real-ish brief ready to paste (use their industry:
      LIMS for QC labs, eQMS for quality, CTMS for clinical)
- [ ] evolifeval.com open in a second tab (for the screener)
- [ ] Zoom screen share tested; font size A+ for readability

---

## Minute-by-minute

### 0:00–2:00 — Frame the problem in their words
> "Before I show anything: how long did your last validation
> package take, end to end?" *(let them answer — anchor on it)*
>
> "EVOLV's claim is simple: the authoring goes from months to
> minutes, and — this is the part that matters — every output is
> **more** defensible in an inspection, not less. If at any point
> you think 'my auditor would flag that', interrupt me. That's
> the conversation I want."

### 2:00–4:00 — Home: the V-model is the product
- Show Home. The V-model draws itself in.
- Type in the chat box: *"what's next?"* → it routes to the
  next incomplete phase.
> "Everything lives on the GAMP 5 V-model your team already
> thinks in. No new methodology to learn."

### 4:00–7:00 — The wow: Brief → Requirements
- Requirements phase → Brief mode. Paste the one-paragraph brief.
- While it generates (narration steps show), say:
> "It's querying the GAMP 5 corpus — the actual guidance text —
> not free-styling from an LLM's memory."
- When rows land: open one UR. Point at:
  - the **regulatory rationale with page-level citation**
  - the risk classification (GxP Direct/Indirect + matrix)
  - acceptance criteria in Given/When/Then
> "Every requirement cites its source. Your auditor can check the
> page number."

### 7:00–9:00 — Design: risk-adaptive test authoring
- Design → Test Authoring. Generate a bundle for a High-risk UR.
> "High risk gets full scripted depth — positive, negative, edge.
> Medium gets a leaner set. Low gets an exploratory charter.
> That's CSA — testing effort proportional to risk, automatically."
- Point at **per-step regulatory citations** (21 CFR 11, Annex 11,
  ICH Q9): "No other tool on the market does this per step."

### 9:00–11:00 — Verify: execution your QA will recognise
- Verify → run 2–3 steps (P/F keys), fail one, capture a defect
  inline, insert an adhoc step (⚡ badge — who/when/why recorded).
> "Testers stay in control. Every deviation from the script is
> captured, attributed, and audit-distinguishable — ALCOA+."

### 11:00–13:00 — The trust close: traceability + audit trail
- Traceability Matrix: one row per UR — risk → tests → runs →
  defects → release state. Click into the drawer.
- Audit Trail: open any AI action → **Logic Archive drill-down**.
> "This is the inspector view. Inputs, reasoning steps, outputs,
> hash-linked. They can re-derive the AI's decision. That's the
> difference between 'we use AI' and 'we can defend our AI'."

### 13:00–15:00 — The governance close + the ask
- Flip to evolifeval.com → run their use case through the
  **AI Screener** live.
> "This is our honesty contract. Five deployment shapes we refuse
> outright — AI signing signatures, releasing batches, closing
> CAPAs, clinical decisions, unsigned writes to validated records.
> A vendor who never says no isn't assessing your risk."

**The ask (verbatim):**
> "Here's what I'd propose: a 6-week pilot on one system you're
> validating anyway. Your team, your SOPs, our platform. Success
> criteria we agree on paper up front — if we miss them, you've
> lost nothing; the work product is yours either way. Can I send
> you the one-page pilot proposal today?"

---

## Objection handling

| Objection | Response |
|---|---|
| "Our auditors won't accept AI-generated docs." | "They accept consultant-generated docs your team signs. Same here — every artefact is human-signed; the AI is a drafting tool with a better paper trail than any consultant: the Logic Archive shows exactly how each draft was derived." |
| "How do we validate EVOLV itself?" | "EVOLV ships with its own validation evidence: agent passports, 90+ adversarial test scenarios run continuously, and the BAP self-assessment. We'll walk your CSV team through qualifying it like any Cat-4 tool." |
| "What about our data / IP?" | "Deployment options include your tenant. API-key gated, CORS locked, no training on your data. Security audit summary available — ask me for it." |
| "We already have ValGenesis / Kneat." | "Those digitised the paperwork. EVOLV drafts the content and keeps it in a validated state — per-step regulatory citations and AI change-impact assessment are things neither has. Run both in the pilot and compare outputs." |
| "Price?" | "Founding-tier pricing locked permanently for pilot customers. The pilot itself is [free / at cost — your call]. Let's see the fit first." |

---

## After the call (same day)

1. Send the leave-behind one-pager + pilot proposal
   (`docs/demo-kit/leave-behind.md`, `pilot-proposal-template.md`)
2. Include the ROI calculator link (`/roi.html` on the website)
   pre-framed with numbers from their answer at minute 0
3. Calendar invite for pilot-scoping call within 5 business days
