# EVOLV Video Scripts

---

# VIDEO 1 — Slide Presentation Script
### "EVOLV: The Compliance Nervous System for Life Sciences"
**Estimated Duration:** 12–15 minutes
**Audience:** CTOs, CSV Heads, QA Directors, VP of Quality

---

## [SLIDE 1 — Opening Statement]

**[Pause 2 seconds. Speak slowly and with weight.]**

Every single drug that reaches a patient —
every device implanted in a human body —
every clinical trial that runs anywhere in the world —

passes through a validated computer system.

The FDA requires it. ISO requires it. GAMP 5 requires it.

And yet — the way the industry validates those systems today
is still built on Word documents, Excel spreadsheets,
and months of manual effort.

We built EVOLV to change that. Permanently.

EVOLV is not a validation tool.

It is the **compliance operating system** for Life Sciences.

---

## [SLIDE 2 — The Problem We Solve]

**[Shift tone to matter-of-fact, slightly frustrated — like you've lived this problem.]**

Let me show you what a validation project looks like today.

A QA team gets a new system — say, a LIMS or a manufacturing execution system.
They open a blank Word document and start writing requirements. That takes four to eight weeks.

Then they take those requirements and manually assess risk — usually in Excel,
usually based on whatever the senior consultant thinks that day.

Then they generate test scripts. Copy, paste, rename. Three to six weeks.

Then they review everything against GAMP 5 PDFs. Manually. With consultants billing by the hour.

Then a change comes in — one change to one requirement —
and they go back to the beginning.

For a mid-size pharma company running 50 validated systems,
this process costs between $150,000 and $500,000 per system.
And takes six to eighteen months.

And the tools the industry uses today — Kneat, Veeva Vault QMS, ValGenesis —
they are better versions of the same filing cabinet.
They manage documents. They do not solve the intelligence problem.

EVOLV solves the intelligence problem.

---

## [SLIDE 3 — What EVOLV Is]

**[Confident. Direct. One comparison that lands.]*

Think about what Salesforce did to CRM.
Before Salesforce, every company built their own customer tracking in Excel.
After Salesforce — there's a platform. An operating system for sales.

That's what EVOLV is to Computer System Validation.

We are not a template. We are not a document manager. We are not a form filler.

EVOLV is a platform with nine interconnected capabilities — all running simultaneously, all feeding each other, all producing audit-ready evidence.

A GAMP 5 knowledge base that every AI agent draws from.
An enterprise API that your ServiceNow, SAP, or LIMS can talk to.
A Sentinel engine that knows what breaks when something changes.
A 21 CFR Part 11 audit trail where every decision is hashed, signed, and immutable.

One platform. Every compliance domain. Every site. Every tenant.

---

## [SLIDE 4 — The 11 AI Agents]

**[Structured delivery. Name each agent cleanly, don't rush.]**

EVOLV runs eleven specialized AI agents.
Not one general-purpose AI — eleven purpose-built agents,
each GAMP 5-aligned, each traceable, each audit-logged.

Let me walk you through the key ones.

**Agent One — Risk Strategist.**
You give it a system criticality and a change type.
It returns a GAMP 5 Risk Priority Number, severity, occurrence, detectability,
and a CSA-aligned testing strategy. Automatically.
And here's the important part — if any factor touches patient safety,
the risk is forced to HIGH. No override. No bypass. By design.

**Agent Two — Requirement Architect.**
You type: "I want to track warehouse temperature."
The agent queries a live GAMP 5 knowledge base,
pulls the relevant regulatory sections, and produces a fully structured URS —
with the GAMP 5 page number cited.

**Agent Three — Verification Agent.**
Every requirement generated is triple-checked.
Is the criticality correct? Is the regulatory rationale actually relevant?
Does the requirement contradict anything in GAMP 5?
If any check fails — the requirement is rejected. Not flagged. Rejected.
A Compliance Exception is logged to the audit trail.

**Agent Four — Delta Agent.**
Give it a UR/FR document.
It produces a complete test script — setup steps, positive cases, negative cases, edge cases, UAT steps — with zero LLM calls needed. Fully deterministic.

**Agent Five — Sentinel.**
I'll dedicate an entire slide to this one. It's the most powerful thing we've built.

**And then six more** — a SMART Requirements Engine that rewrites vague language into measurable acceptance criteria, an Ingestor that parses vendor documents and runs gap analysis, an Intelligence Engine that generates workflow diagrams and risk clusters, a Policy Engine for dynamic access control, an Integrity Manager that is your 21 CFR Part 11 backbone, and an Auditor that produces your Validation Traceability Matrix and Validation Summary Report.

Eleven agents. One platform. No handoffs. No re-entry.

---

## [SLIDE 5 — The Validation Factory Workflow]

**[Walk through it like a process story. Slow down on the time comparison.]**

Let me show you what a real validation looks like inside EVOLV.

A validation engineer sits down.
They type a plain English requirement.
"Track warehouse temperature."

The Requirement Architect agent goes to work.
It queries our GAMP 5 knowledge base.
It classifies the criticality.
It writes the formal URS statement — citing the exact GAMP 5 page.

Before that URS is accepted, the Verification Agent runs three checks.
Criticality alignment. Rationale relevance. Contradiction scan.
The requirement comes back: Approved.

Now the engineer fills in three dropdowns:
What is the user's role? What GxP category does this fall under? What's the implementation method?

EVOLV's risk matrix runs. Risk level: High. Test strategy: OQ and UAT.

The Delta Agent generates the test script. Setup steps. Positive execution. Negative cases. Edge cases.

The PDF Generator produces a complete Validation Report.
Cover page. UR/FR table. Test Script table. Regulatory Justification. Manifestation of Signature for 21 CFR Part 11.

**Total time: minutes.**

Old way: six to eighteen months.

That's not an improvement. That's a different category.

---

## [SLIDE 6 — EVOLV Sentinel]

**[Lean in. This is your differentiator slide. Speak with genuine conviction.]**

Now I want to show you the feature that we believe has no equivalent in the market.

Every QA manager has lived this moment.
A requirement changes — someone adds a single word to a specification —
and you don't know what you've broken.
Which tests are now invalid? Which risks are affected? Which regulatory clauses need re-review?

The answer today is: you run a full regression. Every time. No matter how small the change.

Sentinel changes this.

When a requirement changes, Sentinel performs a semantic delta.
Claude — our AI backbone — reads the old and new text and classifies the change.
Is it structural? Behavioral? Just a clarification? A regulatory update?

Then Sentinel crawls your traceability matrix.
Every linked test case gets scored: Red, Yellow, or Green.
Every linked risk. Every regulatory clause.

It produces a Blast Radius Report.
An impact score from zero to one hundred.
A visual network graph of every affected component.
And — this is important — a rationalization log.
Every single scoring decision is explained in plain language, with the regulatory basis cited.

Let me give you a real example.

Old requirement: "The system shall log batch records."
New requirement: "The system shall log and encrypt batch records per 21 CFR Part 211."

That's a regulatory update. Sentinel sees that immediately.
Impact score: 73 out of 100.
Test Case 5: Red — needs full re-execution.
Test Cases 6 and 9: Yellow — needs targeted review.
Risk 2: Red.
21 CFR Part 211 clause: Red.
Time saved versus full regression: 2.5 hours.

And when Sentinel completes, it fires a signed webhook — to your LIMS, your ServiceNow, your Slack — in real time.

**No other platform does this.**

---

## [SLIDE 7 — Enterprise Architecture]

**[Speak like a CTO explaining to another CTO. Precise, architectural.]**

Let me address something that enterprise buyers always ask:
"How does this fit into our existing stack? And does it work for us specifically?"

Three answers.

**First — Multi-Tenancy with Process Mimicry.**

Client A calls it a "User Need."
Client B calls it a "System Requirement."
Client C calls it a "Validation Specification."

EVOLV calls it whatever the client calls it — without a single code change.
Our Tenant Nomenclature Engine rewrites every API response and every UI label dynamically, based on a JSON configuration file.
This is what ServiceNow calls Process Mimicry. We built it into the core.

**Second — Site-Specific Compliance Modes.**

A company running a GMP manufacturing site, a GCP clinical site, and an ISO 13485 device site
does not have one regulatory brain. It has three.

EVOLV lets you switch the AI's context per site.
GMP mode activates 21 CFR Part 211 and batch integrity logic.
GCP mode activates ICH E6, GDPR, and patient privacy priorities.
GLP mode activates ALCOA+ and raw data integrity.
ISO 13485 mode activates design controls and risk management per 21 CFR Part 820.

Same platform. Four regulatory mindsets. Switchable.

**Third — Attribute-Based Access Control.**

Our Policy Engine runs a five-rule chain on every action.
Role check. Training status. Document lifecycle state. Cross-site restriction. GxP criticality gate.

And here's the rule that always gets a reaction in the room:

No matter what role a user has — Admin, QA Head, CTO —
if their training record is not current, they cannot approve a GxP document.
Period. Not configurable. Hardcoded into the platform.

Because in a regulated environment, a training gap is a compliance gap.
And no amount of seniority changes that.

---

## [SLIDE 8 — The API Layer]

**[Slightly faster pace here. Technical audience will get it quickly.]**

EVOLV is not just a UI. It's a platform with a full enterprise API.

Think of it as the nervous system for your compliance stack.
Every system in your enterprise sends signals to EVOLV,
and EVOLV responds with compliance intelligence.

ServiceNow fires a change request — EVOLV runs the risk assessment and updates the ticket.
SAP detects a configuration change — EVOLV runs a Sentinel blast radius scan.
Your LIMS sends 500 requirements — EVOLV validates them in bulk, asynchronously, and calls you back when done.
Any system registers for events — EVOLV fires signed, HMAC-SHA256 authenticated webhooks in real time.

Our API keys are identity-aware and scoped.
An audit-only key can read everything but cannot write anything — enforced at the API layer.
A sentinel key can only trigger blast radius scans.
An admin key has full access.
And every key is stored as a SHA-256 hash — the raw key is shown once and never stored.

We also have a Sandbox mode.
Add a single header — X-EVOLV-MODE: Sandbox —
and every operation runs in full fidelity, but nothing hits the audit trail.
Your integration team can develop against a production-equivalent API without contaminating your GxP records.

---

## [SLIDE 9 — Compliance Standards]

**[Confident list. Don't rush. Each standard matters to someone in the room.]**

EVOLV is not compliance-adjacent. It is compliance-native.

The platform is aligned to:
GAMP 5 — our primary validation methodology, embedded in every AI query.
21 CFR Part 11 — every audit record hashed, append-only, tamper-evident.
21 CFR Part 211 — GMP manufacturing, batch integrity, equipment.
21 CFR Part 820 — medical device design controls.
ICH E6 R2 — GCP clinical trial data integrity.
21 CFR Part 58 — GLP, raw data, ALCOA+.
ISO 13485 — quality management for medical devices.
GDPR and HIPAA — data privacy in clinical contexts.
FDA's 2026 AI Guidance — PCCP framework, Predetermined Change Control Plans, AI-specific negative test scenarios.
EU AI Act alignment — explainability, human oversight, risk classification.
OECD Principles on AI — transparency and accountability.

We do not bolt compliance on after the fact. It is the foundation.

---

## [SLIDE 10 — vs. The Competition]

**[Calm, factual, not arrogant. Let the comparison speak.]**

Let me address the tools the industry is using today.

Kneat is a test execution platform with strong IQ/OQ/PQ workflow management. It does not generate requirements. It does not assess risk. It does not tell you what breaks when something changes.

Veeva Vault QMS is a document management system with e-signature workflows. It is excellent at storing and routing documents. It is not an intelligence engine.

ValGenesis is a validation lifecycle management tool. It tracks validation status across a portfolio. It requires manual input at every step.

None of them generate requirements from plain language.
None of them run blast-radius analysis on requirement changes.
None of them have a GAMP 5 knowledge base that AI agents query in real time.
None of them can tell an auditor why a requirement was classified as High criticality — with the reasoning archived alongside the audit record.

EVOLV does all of this.
And it exposes all of it as an API that your existing systems can call.

We are not competing with Kneat or Veeva.
We are the platform that sits above them.

---

## [SLIDE 11 — ROI and Business Case]

**[Speak to the CFO in the room. Concrete numbers.]**

Let me put a number on what this means.

A mid-size pharmaceutical company runs approximately 100 validated systems.
Each validation today costs between $150,000 and $500,000 and takes six to eighteen months.
Every change event triggers partial or full re-validation.

With EVOLV:
Requirement generation time drops from weeks to hours.
Test script generation is automated — what took three to six weeks is done in minutes.
Sentinel eliminates full regression testing for low-impact changes — replacing it with targeted, evidence-backed re-testing.
Bulk validation processes 500 requirements simultaneously, asynchronously.

Our customers see sixty to seventy percent reduction in validation cycle time.
And they go into FDA inspections with an audit trail that has cryptographic integrity —
every decision hashed, every AI reasoning step archived, every access event logged.

That is not just speed. That is a defensible compliance posture.

---

## [SLIDE 12 — Technical Differentiators]

**[Engineering credibility slide. Speak with pride of craft.]*

A few things our engineering team built that are worth calling out.

The Integrity Manager produces a dual-layer audit trail.
Layer one: an append-only CSV with SHA-256 reasoning hashes on every row — tamper-evident by design.
Layer two: a JSON logic archive alongside each audit record — containing the full AI reasoning chain, inputs, intermediate steps, and outputs — also with its own integrity hash.

When an FDA inspector asks "why did the system classify this as High criticality?" —
you don't say "the AI decided." You open the logic archive and show them exactly what the system saw, what it considered, and what it concluded.

Our deterministic-first architecture means the platform works without an LLM connection.
The Delta Agent, the UR/FR transformer, the SMART engine's core rewrites — all deterministic.
LLM enhancement is additive, not a dependency.

And the Sandbox mode is not a fake environment. It runs the full stack — real validation, real scoring, real test scripts — with one difference: nothing touches the audit trail. Your developers can integrate against production behavior without compliance risk.

---

## [SLIDE 13 — Deployment]

**[Practical. Procurement-friendly.]**

EVOLV deploys the way your organization needs.

Cloud-native SaaS — multi-tenant, managed, auto-scaled on AWS with Kubernetes.
Private cloud — your AWS, Azure, or GCP account, our platform.
On-premises — fully containerized, runs behind your firewall, no data leaves your environment.
Hybrid — data residency in your infrastructure, platform services in the cloud.

Every deployment option supports the same API, the same audit trail, the same compliance posture.

---

## [SLIDE 14 — Roadmap]

**[Forward-looking. Build excitement about where this is going.]**

We are already in market. The platform you've seen today is running.

In the near term, we're completing direct integrations with ServiceNow, Jira, and SAP Change Management — so EVOLV plugs into your existing change control flow natively.

We're building a Validation Summary Report generator — FDA inspection-ready documentation, produced automatically from your EVOLV data.

We're adding an Auditor Dashboard — a real-time view of your validation portfolio status, risk distribution, and open compliance exceptions.

And we're building cross-tenant intelligence — anonymized, privacy-preserving benchmarks that tell you how your validation efficiency compares to the industry.

---

## [SLIDE 15 — Close / Call to Action]

**[Pause before this one. Speak from conviction, not pitch mode.]*

I want to leave you with one thought.

The pharmaceutical industry has accepted that validation is slow, expensive, and painful —
because that's always been true.

EVOLV is the argument that it doesn't have to be.

Intelligence is now available to do what six consultants and three months of effort used to do — in minutes, with a cryptographic audit trail that holds up to FDA scrutiny.

If you're carrying a portfolio of validated systems, and you're tired of the validation tax —
let's show you what EVOLV looks like on your next project.

We are not asking you to replace your existing infrastructure.
We are asking you to give your validation team a platform that works for them —
instead of the other way around.

Thank you.

---
---

# VIDEO 2 — Live Demo Script
### "A Real Validation Project, Start to Finish — Inside EVOLV"
**Estimated Duration:** 18–22 minutes
**Format:** Screen recording with narration
**Scenario:** A pharmaceutical company is implementing a new LIMS (Lab Information Management System). This is the validation project from day one to inspection-ready package.

---

## [INTRO — Set the Scene]

**[Show the EVOLV login screen / sidebar. Speak casually but with authority.]**

What I'm going to show you today is a real project.
Not a demo with fake data. An actual GAMP 5 Computer System Validation project —
for a new LIMS being implemented at a pharmaceutical manufacturing site.

We're going to go from blank page to inspection-ready validation package —
using EVOLV the way a validation engineer would use it on a real project.

This is the Validation Factory.

---

## [SCENE 1 — The Brief — 2 minutes]

**[Navigate to the Streamlit frontend. Show the sidebar. Orient the viewer.]**

The project manager has given us a brief.
We're validating LabCore LIMS v4.2.
It's a GMP site. The system will manage sample tracking, chain of custody, temperature monitoring, and analyst access controls.

Our first job is to ingest the vendor's system description documentation.

**[Navigate to the Ingestor / Document Ingestion page.]**

I'll upload the vendor's system description PDF here.

**[Upload the document.]**

EVOLV parses this document, extracts structured sections, and — here's the important part —
runs a GAMP 5 gap analysis.

**[Show the gap analysis output.]**

Look at this. The vendor's documentation covers sample tracking and storage.
But it doesn't address audit trail configuration — which 21 CFR Part 11 requires.
It doesn't mention chain-of-custody logging. And it's silent on temperature alarm event handling.

This is your procurement intelligence.
Before you've written a single requirement, you know where the vendor's documentation falls short of your regulatory obligations.

---

## [SCENE 2 — Writing Requirements — 4 minutes]

**[Navigate to Page 12 — SMART Requirements Engine first.]**

Now let's build the requirements.

Most validation teams at this point open a Word document and start typing.
We're going to do something different.

The project manager has given us a rough list — the way requirements always arrive in real projects.
Raw, vague, written by someone who knows the business but not the regulatory standard.

Let me paste these in.

**[Paste requirements like:]**
- "System should be fast when loading records"
- "Samples need to be tracked"
- "Temperature monitoring should work"
- "Only certain people can approve results"

**[Click Refine to SMART.]**

Watch what happens.

**[Show SMART output.]**

"System should be fast when loading records" —
EVOLV flags this as ambiguous. It rewrites it to:
"The system shall retrieve sample records within 3 seconds for 95% of queries under standard load conditions, as measured by performance testing."

Measurable. Testable. Audit-ready.

"Only certain people can approve results" —
EVOLV detects this is a GxP access control requirement and rewrites it to:
"The system shall restrict the Approve Result action to users with the role of Analyst Supervisor or QA Lead, as configured in the system's role-based access control module."

And here — it also detects an FDA 2026 AI Guidance trigger.
Because this requirement involves automated result evaluation.
It flags this for a Predetermined Change Control Plan review.

**[Export the SMART requirements to the Validation Factory page.]**

Now let's generate the formal URS.

**[Navigate to the Validation Factory — Page 6.]**

**[Show the Generate URS workflow. Type in the first requirement.]**

I'll start with the temperature monitoring requirement.

"The system shall monitor and record temperature readings for all sample storage units and generate an alert when temperature exceeds defined thresholds."

**[Click Generate URS.]**

The Requirement Architect queries the GAMP 5 knowledge base.
It pulls relevant sections. Here — it's citing GAMP 5 Guide, page 42, on environmental monitoring requirements.

URS generated. Criticality: Medium.

**[Show the Verification Agent result panel.]**

Now the Verification Agent runs automatically.
Three checks. Criticality Alignment — Pass. Rationale Relevance — Pass. Contradiction Scan — Pass.

**Verdict: Approved.**

This requirement is now compliant, traced, and ready for UR/FR transformation.

**[Now generate a patient safety requirement.]**

Let me try a higher-stakes one.
"The system shall enforce chain of custody tracking for all controlled substance samples."

**[Generate URS. Show High criticality output.]**

Criticality: High. Regulatory Rationale citing 21 CFR Part 11 and GAMP 5 on data integrity.

Verification Agent: Pass, Pass, Pass. Approved.

---

## [SCENE 3 — Building the UR/FR Document — 3 minutes]

**[Show the UR/FR Transform section on the Validation Factory page.]**

Now I have my approved URS. Let's build the UR/FR document.

This is where the validation engineer adds their professional judgment.

**[Fill in the dropdown fields on screen:]**
- User Role: Lab Analyst
- GxP Category: GxP Direct
- Implementation Method: Configured
- System Description: LabCore LIMS v4.2, cloud-hosted, validated vendor
- Workshop Notes: Chain of custody is safety-critical for controlled substance samples

**[Click Transform to UR/FR.]**

EVOLV's risk matrix runs. GxP Direct + Configured = High risk. Test strategy: OQ and/or UAT.

**[Show the UR/FR output.]**

Here's what we get.
UR-1: the user requirement statement.
FR-1, FR-2, FR-3: the functional requirements decomposed from the URS.
Each FR has acceptance criteria — written in Given/When/Then format.
Assumptions and dependencies — including the system description I typed in.
Compliance notes — including the role-based access control information.
And a Regulatory Justification section.

This document would take a validation consultant half a day to write.
EVOLV just did it in seconds.

---

## [SCENE 4 — Generating the Test Script — 3 minutes]

**[Show the CSA Test Script generation section.]**

Now — the test scripts.

The Delta Agent takes the UR/FR document and generates a complete CSA test script.

**[Select test type: Formal OQ. Click Generate.]**

**[Show the test script output — step table.]**

Look at this structure.

Setup steps first: Login as System Owner. Navigate to the sample management module. Prepare test data — controlled substance sample IDs.

Then execution steps.
Step 1, Positive: Initiate chain-of-custody transfer. Enter source, destination, analyst ID. Verify system creates a timestamped, signed audit entry. Expected result: transfer logged with analyst ID, timestamp, and digital signature.

Step 2, Negative: Attempt to transfer without analyst ID. Expected result: system rejects the action with an error message. Audit trail records the attempted access.

Step 3, Edge case: Transfer during system alert condition. Expected result: system correctly handles the concurrent event and logs both records independently.

Every step. Every expected result. Every test case type classified.

And a Quality Checklist at the bottom — confirming the script meets internal quality standards.

---

## [SCENE 5 — The Validation Report PDF — 1 minute]

**[Show the PDF download section.]**

Now let's produce the deliverable.

**[Click Download Validation Report. Open the PDF.]**

This is what goes into your validation binder — or your Kneat, or your Veeva, or whatever document management system you use.

Cover page with the project metadata.
UR/FR table — landscape format, fully formatted.
Test Script table — step by step, with all columns.
Regulatory Justification page — the GAMP 5 citations that back every decision.
And the Manifestation of Signature page — the 21 CFR Part 11 electronic signature record.

Signer name. Timestamp in UTC. Meaning of signature. Compliance note referencing 21 CFR Part 11, Subpart C.

From requirement to signed validation report. In one workflow.

---

## [SCENE 6 — A Change Comes In — Sentinel — 4 minutes]

**[Navigate to the Sentinel page. Set the scene narratively first.]**

Three months into the project.
The vendor releases a patch.
The change affects how temperature alarms are logged — they've added an encryption layer
and changed the storage format.

The requirement that was approved is now potentially out of sync with what the system does.
This is the moment that historically causes weeks of rework.

**[Navigate to Sentinel. Paste the old and new requirement text.]**

Old: "The system shall monitor and record temperature readings for all sample storage units and generate an alert when temperature exceeds defined thresholds."

New: "The system shall monitor, record, and encrypt temperature readings and alerts per 21 CFR Part 211.68, storing all records in an auditable, tamper-evident format."

**[Click Run Sentinel Scan.]**

Sentinel classifies this change: **Regulatory**. A new regulatory citation has been added, and the storage behavior has materially changed.

**[Show the Blast Radius Report.]**

Impact score: 68 out of 100.

Test Case TC-03 — the environmental monitoring script — Red. Needs full re-execution because the storage format has changed.
Test Case TC-07 — the audit trail script — Yellow. The existing test covers logging but not encryption. Needs targeted update.
Test Case TC-11 — the alert generation test — Green. Unaffected.

Risk RISK-04 — Red. The data integrity risk now has a new regulatory hook.
21 CFR Part 211.68 clause — Red. New regulatory scope introduced.

Time saved versus full regression: 4.2 hours.

**[Show the Rationalization Log.]**

And here — every single decision explained.
"TC-03 scored Red because the change introduces a new storage format that the existing test steps do not validate. The test must be re-executed against the new encrypted format per GAMP 5 Chapter 8.3."

This is the rationalization log. This is what you show an auditor when they ask
"why didn't you re-run all your tests when the vendor patched the system?"

Because Sentinel analyzed it. And here is the documented rationale.

**[Show the webhook section briefly.]**

And the moment the scan completes — a signed webhook fires.
In this demo, it would notify your LIMS, update your ServiceNow ticket,
and post to the QA team's Slack channel.

---

## [SCENE 7 — Access Control in Action — 2 minutes]

**[Navigate to or describe the Policy Engine behavior — can show via API call or UI context.]**

Let me show you one more thing that's running silently through everything we've just done.

Every action in EVOLV passes through the Policy Engine.

In our project, the validation engineer wants to approve the UR/FR document.
But this engineer's training record expired last week.

**[Show the access denied result or describe it verbally with audit trail.]**

Policy Engine: Access Denied.
Rule triggered: Training Status Gate.
Action: Approve. Training status: Incomplete. Decision: DENY.

And this decision is logged to the audit trail with the full reasoning.

It doesn't matter that this person is a senior validation engineer.
It doesn't matter that they're the one who wrote the requirement.
In a GxP environment, a lapsed training record is a compliance event.
EVOLV enforces it. Automatically. Every time.

**[Show the audit trail CSV briefly.]**

Here's the audit trail.
Every action from the past forty minutes, logged.
Timestamp. User ID. Agent. Action. Decision logic. SHA-256 reasoning hash. Compliance impact classification.

Append-only. Tamper-evident. 21 CFR Part 11 compliant.

---

## [SCENE 8 — Closing the Demo]

**[Stop sharing screen or hold on the audit trail. Speak directly to camera.]**

What you just watched was one validation engineer.
One project. One LIMS.

Going from a vendor document and a rough requirement list —
to an approved URS, a UR/FR document with functional requirements and acceptance criteria,
a formal OQ test script, a signed Validation Report PDF,
and a change impact analysis that saved four hours of regression testing —

in under thirty minutes.

The audit trail captures every decision. Every AI reasoning step is archived.
Every access control event is logged. Every document is traceable back to GAMP 5.

This is EVOLV.

This is what Computer System Validation looks like when you stop doing it manually.

If you want to run this against one of your own requirements —
a system you're validating right now —
reach out. We'll run a live session with your data.

Thank you.

---

## PRODUCTION NOTES

### Video 1 (Slides)
- Record at 1080p. Use the HTML presentation full-screen.
- Advance slides on cue words (underlined in script = advance).
- Background music: light ambient, fade to zero during speaking.
- Recommended pacing: 12–15 minutes total.
- End card: logo + contact info + "Powered by EVOLV | WingstarTech Inc."

### Video 2 (Demo)
- Record screen at 1920×1080. Use OBS or Loom.
- Have all sample data pre-loaded (vendor PDF, requirement list).
- Keep Streamlit sidebar collapsed for maximum canvas space.
- Scene transitions: brief cut to black (0.5s) between each Scene.
- Recommended pacing: 18–22 minutes total.
- Cut any loading spinners > 3 seconds in post.
- Closing 10 seconds: logo + LinkedIn / email CTA.

### Key Phrases to Emphasize (slow down / pause after these)
- "Every drug that reaches a patient..."
- "Six to eighteen months → minutes"
- "No other platform does this" (Sentinel slide)
- "No matter what role they have — if training is expired, they cannot approve"
- "This is what you show an auditor"
- "We are not asking you to replace your infrastructure"
