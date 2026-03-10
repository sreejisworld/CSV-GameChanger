# EVOLV — The Compliance Nervous System for Life Sciences
### Enterprise Platform Presentation | Confidential

---

## SLIDE 1 — Opening Statement

> **"Every drug that reaches a patient passes through a validated computer system.
> Until now, validating those systems has been a manual, expensive, and error-prone
> process. EVOLV changes that — permanently."**

**EVOLV** is not a validation tool.
It is a **compliance-native enterprise platform** — the operating system for
Computer System Validation (CSV) in Life Sciences.

Built for: **Pharmaceutical | Biotech | Medical Devices | Clinical Research**

---

## SLIDE 2 — The Problem We Solve

### What the Industry Does Today

| Step | Current Reality | Cost |
|---|---|---|
| Write requirements | Word documents, manually | 4–8 weeks per system |
| Risk assessment | Excel spreadsheets, subjective | Auditor-dependent |
| Generate test scripts | Copy-paste from templates | 3–6 weeks per validation |
| Verify compliance | Manual review against GAMP 5 PDFs | Expensive consultants |
| Track change impact | Email chains, meetings | Every change = full regression |
| Audit trail | Siloed logs, no integrity proof | FDA warning letters |

### The Cost of the Status Quo

- A **mid-size pharma company** runs 50–200 validated systems
- Each validation costs **$150K–$500K** and takes **6–18 months**
- Every change triggers a **partial or full re-validation**
- **21 CFR Part 11 failures** are the #1 cause of FDA warning letters
- Kneat, Veeva, ValGenesis are **document management tools**
  with a validation wrapper — they do not solve the intelligence problem

---

## SLIDE 3 — What EVOLV Is

### Platform, Not a Tool

```
┌─────────────────────────────────────────────────────────────────┐
│                         EVOLV PLATFORM                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Validation  │  │  Compliance  │  │   Enterprise API     │  │
│  │   Factory    │  │   Nervous    │  │   (OpenAPI 3.0)      │  │
│  │  (AI Engine) │  │   System     │  │   (REST + Webhooks)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  GAMP 5 RAG  │  │  Sentinel    │  │   Multi-Tenant       │  │
│  │  Knowledge   │  │  Blast       │  │   Nomenclature       │  │
│  │  Base        │  │  Radius      │  │   Engine             │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  ABAC Policy │  │  21 CFR      │  │   Site-Specific      │  │
│  │  Engine      │  │  Part 11     │  │   Compliance Mode    │  │
│  │  (DAC)       │  │  Audit Trail │  │   (GMP/GCP/GLP)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

    Powered by EVOLV | A WingstarTech Inc. Product
```

**EVOLV is to CSV what Salesforce is to CRM.**
An intelligent, extensible platform — not a form filler.

---

## SLIDE 4 — The 11 AI Agents

EVOLV runs **11 specialized AI agents** — each GAMP 5-aligned,
each audit-logged, each deterministic-first with LLM enhancement.

### Agent 1 — Risk Strategist
**Purpose:** Automates GAMP 5 risk assessment
**Input:** System criticality + change type (from ServiceNow, SAP, Jira)
**Output:** RPN (1–27), Severity/Occurrence/Detectability, CSA Testing Strategy
**Differentiator:** Patient Safety Override — any HIGH severity forces HIGH risk regardless of RPN

### Agent 2 — Requirement Architect
**Purpose:** Converts plain English to GxP-compliant URS documents
**Input:** "I want to track warehouse temperature"
**Output:** Structured URS with regulatory rationale citing GAMP 5 section and page
**Differentiator:** Pulls live context from a Pinecone GAMP 5 knowledge base — every requirement is grounded in regulation

### Agent 3 — Verification Agent
**Purpose:** Triple-check compliance of every generated requirement
**Checks:**
1. Criticality Alignment — detects under-classification (e.g., calling a patient safety req "Low")
2. Rationale Relevance — rejects if best GAMP 5 match score < 0.45
3. Contradiction Scan — rejects if requirement says "skip validation" but GAMP 5 says the opposite
**Differentiator:** Requirements that fail verification are **rejected with a Compliance Exception** — not just flagged

### Agent 4 — Delta Agent (CSA Test Factory)
**Purpose:** Generates complete CSA test scripts from UR/FR documents
**Output:** Setup steps, positive/negative/edge-case execution steps, UAT business-process steps
**Differentiator:** Fully deterministic — no LLM needed. Always produces test scripts even without API keys

### Agent 5 — Sentinel Impact Agent
**Purpose:** Blast-radius analysis when a requirement changes
**Input:** Old requirement text + new requirement text
**Output:** Red/Yellow/Green impact scoring for every linked test case, risk, and regulatory clause
**Differentiator:** Semantic delta detection via Claude — distinguishes "structural" from "clarification" changes and calibrates impact accordingly. Calculates **hours saved vs. full regression**

### Agent 6 — SMART Requirements Engine
**Purpose:** Transforms vague, human-written requirements into audit-ready SMART format
**Embedded:** FDA/EMA 2026 AI Guidance triggers (PCCP detection, Negative Test Scenarios)
**Differentiator:** Detects phrases like "the system should be fast" and rewrites them with measurable acceptance criteria — automatically

### Agent 7 — Ingestor Agent
**Purpose:** Parses vendor documentation (PDFs, DOCX) and extracts structured data
**Output:** Sections, summary, GAMP 5 gap analysis, regulatory citations
**Differentiator:** Gap analysis identifies where a vendor's system description fails to address GAMP 5 requirements — before procurement

### Agent 8 — Intelligence Engine
**Purpose:** Generates project intelligence from requirement sets
**Output:** Mermaid.js workflow diagrams, categorized requirements, security gap identification, acceptance criteria
**Differentiator:** Produces a D3.js-compatible network graph showing requirement relationships and risk clusters

### Agent 9 — Policy Engine (ABAC)
**Purpose:** Dynamic Attribute-Based Access Control — the Veeva DAC equivalent
**Rules:**
1. Training Status Gate — untrained users cannot Approve (no exceptions)
2. Role Capability Check — Admin/QA/Author/Reviewer/Viewer roles
3. Lifecycle State Gate — Locked documents cannot be edited
4. Cross-Site Restriction — Author cannot modify another site's resources
5. GxP Criticality Gate — Viewers blocked from GxP Direct resources
**Differentiator:** Every access decision is logged to the immutable audit trail with full reasoning

### Agent 10 — Integrity Manager
**Purpose:** Central 21 CFR Part 11 audit trail
**Output:**
- Append-only CSV (`output/audit_trail.csv`) with SHA-256 reasoning hashes
- Optional JSON logic archives with tamper-evident integrity hashes
**Differentiator:** AI reasoning is archived alongside audit records — inspectors can see WHY a requirement was classified as High criticality, not just that it was

### Agent 11 — Auditor Agent
**Purpose:** Generates Validation Traceability Matrix (VTM) and Validation Summary Report (VSR)
**Output:** Formal validation deliverables ready for FDA inspection

---

## SLIDE 5 — The Validation Factory (Core Workflow)

### From Natural Language to Inspection-Ready Package in Minutes

```
User Input                    EVOLV Platform                    Output
──────────                    ──────────────                    ──────
"Track warehouse          →   Requirement Architect     →   URS-7.1 (GAMP 5 cited)
 temperature"                 ↓
                              Verification Agent        →   APPROVED / REJECTED
                              ↓
User selects:                 Requirement Architect     →   UR-1 + FR-1, FR-2, FR-3
  Role, GxP category          (UR/FR Transform)         →   Risk Level: High
  Implementation method       ↓                         →   Test Strategy: OQ/UAT
                              Delta Agent               →   Formal OQ Test Script
                              ↓                         →   Setup + Positive + Negative
                                                            + Edge Case steps
                              PDF Generator             →   Validation Report PDF
                              ↓                             (Cover + UR/FR table
                                                            + Test Script table
                                                            + Regulatory Justification
                                                            + Manifestation of Signature)
```

**Total time:** Minutes
**Old way:** 6–18 months

---

## SLIDE 6 — EVOLV Sentinel (The Most Powerful Feature)

### "What breaks when I change this requirement?"

Every QA manager's nightmare: a requirement changes, but nobody knows which tests
are now invalid. EVOLV Sentinel answers this in **seconds**.

#### How It Works

```
Change Event (ServiceNow / SAP / Jira / Manual)
         │
         ▼
Semantic Delta Detection
  • LLM (Claude) classifies change as:
    Structural | Behavioural | Clarification | Regulatory
         │
         ▼
Traceability Matrix Crawl
  Tier 1: All linked Test Cases       → Red / Yellow / Green
  Tier 2: Linked Risks + Trace Matrix → Red / Yellow / Green
  Tier 3: Regulatory Clauses          → Red / Yellow / Green
         │
         ▼
Blast Radius Report
  • Impact Score: 0–100
  • Time saved vs. full regression: X hours
  • Network Graph (D3.js) — visual dependency map
  • Rationalization Log — natural language explanation
    of every decision, with regulatory basis cited
         │
         ▼
Webhook Fired → Your LIMS / ServiceNow / Slack
  (HMAC-SHA256 signed payload)
```

#### Real Example

```
Old: "The system shall log batch records."
New: "The system shall log and encrypt batch records per 21 CFR Part 211."

Sentinel Output:
  Change Category:  REGULATORY
  Impact Score:     73/100
  Test Cases:       TC-05 [RED], TC-06 [YELLOW], TC-09 [YELLOW]
  Risks:            RISK-02 [RED]
  Reg Clauses:      21 CFR Part 211 [RED]
  Time Saved:       2.5 hours vs. full regression
  Confidence:       HIGH
```

**No other platform in the market does this.**

---

## SLIDE 7 — Enterprise Architecture

### Built for the Enterprise. Clean Core. Extensible.

#### Multi-Tenancy with Process Mimicry (ServiceNow Style)

Client A calls it "User Need."
Client B calls it "System Requirement."
Client C calls it "Validation Specification."

**EVOLV calls it whatever the client calls it** — without a single line of code change.
The Tenant Nomenclature Engine rewrites every API response and UI label dynamically.

```json
// pharma_gmp.json (Client A config)
{
  "tenant_id": "pharma-corp-001",
  "labels": {
    "urs": "System Requirement",
    "test_case": "Verification Protocol",
    "approval": "QA Release Decision"
  }
}
```

#### Site-Specific Compliance Mode

Every facility type gets a different AI brain:

| Mode | Primary Regulation | Focus |
|------|-------------------|-------|
| GMP | 21 CFR Part 211 + GAMP 5 | Batch integrity, equipment calibration |
| GCP | ICH E6 (R2) + GDPR/HIPAA | Patient privacy, informed consent |
| GLP | 21 CFR Part 58 + OECD | Raw data integrity, ALCOA+ |
| ISO 13485 | ISO 13485 + 21 CFR Part 820 | Design controls, risk management |

Same platform. Four regulatory mindsets. Switchable per site.

#### Attribute-Based Access Control (Veeva DAC Style)

```
PolicyEngine.permit(user, action, resource)

Rule 1: training_status == False → Approve DENIED (always)
Rule 2: role not in allowed_actions → DENIED
Rule 3: document.lifecycle == LOCKED + action == edit → DENIED
Rule 4: user.site != resource.site + no QA role → DENIED
Rule 5: resource.gxp == Direct + user.role == Viewer → DENIED

Every decision → immutable audit trail
```

The "Wow" Rule: **No matter what role a user has, if their training
record is expired, they cannot approve a GxP document. Period.**
This is not configurable. It is hardcoded into the platform.

---

## SLIDE 8 — The API Layer (Developer Platform)

### OpenAPI 3.0 — The Compliance Nervous System Interface

EVOLV exposes a complete REST API that any enterprise system can integrate with.
Think of it as the **nervous system** — every system in your stack sends signals to EVOLV,
and EVOLV responds with compliance intelligence.

```
ServiceNow ──────────► POST /webhook/sn-change ──► Risk Assessment
SAP Change Mgmt ──────► POST /webhook/sentinel-scan ► Blast Radius
LIMS ─────────────────► POST /bulk/validate ──────► 500 Reqs Batch
Your ERP ─────────────► GET  /bulk/status/{id} ───► Progress + Results
Any System ───────────► POST /webhooks/register ──► Event Subscription
```

#### Extension Hook Registry (ServiceNow IntegrationHub Style)

Customers register their endpoints. EVOLV fires signed events:

```
SENTINEL_SCAN_COMPLETED  → Your LIMS gets an immediate, signed alert
BULK_VALIDATE_COMPLETE   → Your quality system downloads results
CHANGE_REQUEST_ASSESSED  → Your ServiceNow ticket is auto-updated
```

**Retry Logic:** Immediate → 1 min → 5 min → 15 min
**Security:** Every payload signed with HMAC-SHA256

#### Scoped API Keys (Identity-Aware Tokens)

```
Key A: tenant=pharma-corp, scope=audit_only → READ ONLY
Key B: tenant=pharma-corp, scope=sentinel   → BLAST RADIUS ONLY
Key C: tenant=pharma-corp, scope=admin      → FULL ACCESS

audit_only key attempting POST → HTTP 403 Forbidden (enforced by PolicyEngine)
```

#### Sandbox Mode

```http
POST /bulk/validate
X-EVOLV-MODE: Sandbox
X-API-Key: your-key

{
  "requirements": [ ... ]
}

Response:
{
  "job_id": "abc-123",
  "status": "queued",
  "sandbox": true    ← All output isolated. Nothing touches production.
}
```

---

## SLIDE 9 — Compliance Standards (The Regulatory Moat)

EVOLV is the **only platform** built to natively satisfy all of these simultaneously:

### Regulatory Frameworks Embedded

| Standard | Coverage |
|---|---|
| **21 CFR Part 11** | Electronic records, e-signatures, audit trail, access control |
| **21 CFR Part 211** | GMP manufacturing, batch records, equipment calibration |
| **21 CFR Part 50** | Clinical human subject protection |
| **21 CFR Part 58** | Good Laboratory Practice |
| **21 CFR Part 820** | Medical device quality systems |
| **GAMP 5** | Risk-based approach, software categories, lifecycle |
| **EU GMP Annex 11** | Computerised systems for GMP |
| **ICH E6 (R2)** | Good Clinical Practice |
| **ICH Q9** | Quality risk management |
| **ISO 13485:2016** | Medical device QMS |
| **ISO 14971** | Medical device risk management |
| **GDPR / HIPAA** | Data privacy |
| **FDA CSA** | Computer Software Assurance |
| **FDA/EMA 2026 AI Guidance** | PCCP, Negative Test Scenarios, AI oversight |
| **OECD GLP** | Laboratory data integrity |
| **EU MDR 2017/745** | Medical device regulation |
| **ALCOA+** | Data integrity (Attributable, Legible, Contemporaneous, Original, Accurate) |

**16 regulatory frameworks. One platform.**

### 21 CFR Part 11 Compliance Architecture

```
Every action in EVOLV produces:

1. Timestamp (UTC ISO-8601)
2. User_ID
3. Agent_Name
4. Action_Performed
5. Decision_Logic (human-readable reasoning)
6. Reasoning_Hash (SHA-256 — tamper detection)
7. Compliance_Impact (GxP Documentation / Patient Safety / etc.)

Optional Logic Archive (JSON):
  inputs:  { what went in }
  steps:   [ every reasoning step ]
  outputs: { what came out }
  integrity: { archive_hash, algorithm: sha256 }
```

An FDA inspector can read exactly why EVOLV classified a requirement
as High criticality. Not just THAT it was classified — WHY.

---

## SLIDE 10 — Competitive Landscape

### EVOLV vs. The Market

| Capability | EVOLV | Veeva Vault | Kneat | ValGenesis |
|---|---|---|---|---|
| **AI Requirement Generation** | Native + GAMP 5 RAG | None | None | Template only |
| **Semantic Blast Radius** | Full (Red/Yellow/Green) | Manual | Manual | Offline |
| **ABAC + Training Gate** | 5-rule engine, hardcoded training override | Role-based only | Role-based only | Role-based only |
| **Multi-Tenant Nomenclature** | Dynamic, runtime, no code change | Hardcoded | Hardcoded | Hardcoded |
| **Site-Specific AI Modes** | GMP/GCP/GLP/ISO13485 per site | None | None | None |
| **FDA/EMA 2026 AI Guidance** | Embedded (PCCP, Negative Tests) | Not addressed | Not addressed | Not addressed |
| **API-First Architecture** | OpenAPI 3.0, 12 endpoints | Limited API | Limited API | Limited API |
| **Webhook Extension Hooks** | HMAC-signed, tiered retry | Basic | None | None |
| **Bulk Batch Processing** | 500 reqs/batch, 202 Accepted | None | None | None |
| **Sandbox Mode** | Built-in, header-driven | None | None | None |
| **Logic Archive Transparency** | AI reasoning + tamper proof | None | None | None |
| **CSA Test Script Generation** | Deterministic, Informal/OQ/UAT | Manual | Template | Template |
| **Time-Saved Calculation** | Automatic, per change | None | None | None |
| **Deployment** | Cloud / On-prem / Hybrid | Cloud only | Cloud only | Cloud only |
| **Business Model** | Platform (like SAP/Salesforce) | SaaS tool | SaaS tool | SaaS tool |

### The Strategic Verdict

**Veeva, Kneat, and ValGenesis are validation document managers.**
EVOLV is a **compliance intelligence platform**.

The difference: They store and route paperwork.
EVOLV **generates, verifies, scores, and monitors** compliance — autonomously.

---

## SLIDE 11 — ROI Model

### The Business Case

**Current state (typical mid-size pharma):**
- 80 validated systems in scope
- Average validation cost: $200,000 per system
- Average validation time: 9 months
- Annual re-validation spend: $4–6M
- Change impact assessment: 2–4 weeks per change event

**With EVOLV:**

| Activity | Before | After | Saving |
|---|---|---|---|
| URS generation | 4–8 weeks | 30 minutes | 95% |
| Test script generation | 3–6 weeks | 2 minutes | 98% |
| Change impact assessment | 2–4 weeks | 2 seconds (Sentinel) | 99.9% |
| Compliance verification | Manual review | Automated triple-check | 80% |
| Audit preparation | 3–6 months | Continuous | 90% |

**Conservative estimate:** EVOLV reduces validation lifecycle costs by **60–80%**.

For a company spending $5M/year on CSV:
**EVOLV ROI: $3M–$4M per year.**

---

## SLIDE 12 — The Technical Differentiators (For the CTO)

### Why This Cannot Be Replicated Quickly

**1. The GAMP 5 Knowledge Base**
Pinecone vector database populated with GAMP 5, ICH, FDA CSA.
Every requirement generated is grounded in a specific regulatory section.
Not a chatbot. A compliance-grounded reasoning engine.

**2. Deterministic + LLM Hybrid Architecture**
EVOLV never fails because an API is unavailable.
Every agent has a deterministic fallback mode.
LLM enhances. It does not gate.

**3. Tamper-Evident Logic Archives**
SHA-256 hash chain connecting every AI decision to its reasoning.
No other platform in the market has this.
FDA inspectors cannot reject EVOLV output as "unexplainable AI."

**4. The Policy Engine Rule Chain**
5 rules evaluated in strict priority order.
Rule 1 (Training Status) cannot be bypassed by any other rule.
This is not a configuration. It is architectural.

**5. Clean Core Design**
The backend has zero hardcoded client terminology.
Any UI string, label, or document heading is tenant-configurable.
Add a new client: add a JSON file. Zero code changes.

**6. FDA/EMA 2026 AI Guidance Ready**
Negative Test Scenarios are auto-generated for high-risk requirements.
Predetermined Change Control Plan (PCCP) triggers are detected.
EVOLV is the only platform designed for the regulatory future, not just today.

---

## SLIDE 13 — Deployment Options

### How EVOLV Fits Into Your Stack

#### Option A — SaaS Platform
- Hosted on AWS / Azure / GCP
- Customer brings their API keys (OpenAI, Pinecone)
- Multi-tenant, per-site compliance mode
- Start generating requirements on Day 1

#### Option B — On-Premises (Air-Gapped)
- Deployed inside the customer's network
- No data leaves the firewall
- Compatible with private LLM deployments
- Meets FDA data residency requirements

#### Option C — Hybrid (Most Common)
- EVOLV Platform: cloud
- Customer data: stays on-prem
- API calls: customer's Pinecone/OpenAI keys
- Audit trail: customer-controlled storage

#### Integration Connectors

```
ServiceNow   ──► POST /webhook/sn-change    (native)
SAP          ──► POST /webhook/sentinel-scan (native)
Jira         ──► POST /bulk/validate        (native)
Veeva Vault  ──► Webhook Extension Hook     (outbound)
MasterControl──► Webhook Extension Hook     (outbound)
LIMS systems ──► Any endpoint               (via API keys)
SharePoint   ──► PDF export integration     (via download)
```

---

## SLIDE 14 — Roadmap (Coming Next)

| Quarter | Feature | Impact |
|---|---|---|
| Q1 2026 | ServiceNow native app packaging | Zero-integration deployment |
| Q1 2026 | Veeva Vault connector (inbound URS sync) | Replace Vault's req module |
| Q2 2026 | Regulatory intelligence updates (live FDA/EMA feed) | Always current |
| Q2 2026 | Visual Traceability Matrix (interactive D3.js) | Inspection-ready dashboard |
| Q3 2026 | Periodic Review automation | Annual review in minutes |
| Q3 2026 | Electronic Signature workflow (21 CFR Part 11) | Full e-sig lifecycle |
| Q4 2026 | ISO 27001 certification | Enterprise security tier |
| Q4 2026 | Multi-LLM support (Azure OpenAI, private models) | Air-gapped AI |

---

## SLIDE 15 — Call to Action

### What We're Asking For

**Pilot Program (90 days):**
1. Select 2–3 validated systems currently in scope for validation
2. Run EVOLV alongside your existing process
3. Compare output quality, speed, and audit-readiness
4. Measure actual time/cost savings

**What you get:**
- Full platform access (all 11 agents)
- Dedicated technical onboarding
- Custom tenant nomenclature configuration
- Side-by-side comparison with your current tools

**What we need:**
- Access to 2–3 example validation projects
- 1 QA lead + 1 CSV consultant as pilot contacts
- 90 days commitment

> "If EVOLV doesn't reduce your validation cycle by at least 50%,
> we walk away. No invoice."

---

---
---

# DEMO SCRIPT — For CTO / CSV Head Audience

## Setup Before the Meeting
- Run: `uvicorn API.main:app --reload --host 0.0.0.0 --port 8000`
- Run: `streamlit run frontend/app.py`
- Open: `http://localhost:8501` (Streamlit UI — full screen)
- Open: `http://localhost:8000/docs` (Swagger UI — minimised, ready to switch to)
- Have a blank Word doc open for the "before" moment
- Prepare: a printed FDA warning letter (for visual impact)

---

## DEMO ACT 1 — "The Problem" (3 minutes)

**Say:**
> "Before I show you EVOLV, I want to show you what your team is doing right now."

Show the blank Word document.

> "Your CSV consultant opens this document. They spend 3 days writing requirements in Word.
> Another 2 weeks writing test scripts. Another week getting approvals.
> Then the system changes — and they do it all again."

Show the FDA warning letter.

> "This is what happens when that process breaks down.
> This warning letter is from an FDA inspection that found audit trail gaps.
> The company paid $12 million in remediation costs."

**Pause. Let it land.**

> "EVOLV exists so this never happens to you."

---

## DEMO ACT 2 — "The Intelligence Engine" (5 minutes)

Go to the Streamlit UI. Navigate to **Page 2 — Generate Requirements**.

**Say:**
> "I'm going to type a plain English description of a system. Watch what happens."

Type in the text area:
```
I need a system to manage laboratory samples — track chain of custody,
record temperature at every transfer, log who handled each sample and when,
and alert if temperature exceeds 2–8°C.
```

Click Generate.

**While it generates, say:**
> "EVOLV is now querying its GAMP 5 knowledge base — a vector database populated
> with every page of GAMP 5, FDA CSA guidance, and ICH guidelines.
> It's not making requirements up. It's grounding every requirement in actual regulation."

Show the output:
- Point to the URS ID: "Every requirement gets a unique, traceable identifier."
- Point to Criticality: "It classified this as HIGH — because temperature monitoring
  is directly linked to product quality and patient safety."
- Point to Regulatory Rationale: "Look at this. It cites the specific page of GAMP 5
  that justifies this classification. An FDA inspector can verify this in 30 seconds."

**Say:**
> "A consultant would take 4 hours to write this one requirement correctly.
> EVOLV did it in 12 seconds."

---

## DEMO ACT 3 — "Sentinel Blast Radius" (5 minutes)

Navigate to the Sentinel page.

**Say:**
> "Now here's where EVOLV does something no other platform in the world can do."

Enter:
- Old requirement: `The system shall log sample transfers.`
- New requirement: `The system shall log and encrypt all sample transfers using AES-256 per 21 CFR Part 11.`

Click Analyze.

Show the output:

**Say:**
> "Sentinel detected this as a REGULATORY change — not just a wording tweak.
> Look at what it found:
> - TC-05 is RED — it directly tests this requirement and must be re-executed.
> - TC-06 is YELLOW — boundary conditions need review before execution.
> - RISK-02 is RED — the data integrity risk assessment must be re-run.
> - The 21 CFR Part 11 clause is flagged RED because the regulation reference changed.
>
> And it tells us: instead of re-running 6 test cases at 30 minutes each — 3 hours —
> we only need to re-run the 2 Red items. We save 1 hour. Every time a change happens."

Point to the Rationalization Log:

> "This is what makes EVOLV defensible in an inspection.
> An FDA auditor says 'why did you only re-run 2 test cases?'
> You show them this. Natural language. Regulatory basis cited. Signed.
> Case closed."

---

## DEMO ACT 4 — "The Enterprise API" (3 minutes)

Switch to the Swagger UI at `http://localhost:8000/docs`.

**Say:**
> "EVOLV is not just a UI. It's an enterprise platform with a full API.
> This is what your LIMS, your ServiceNow, your SAP talks to."

Click on **POST /bulk/validate**. Click "Try it out."

Enter:
```json
{
  "requirements": [
    {"text": "The system shall track sample temperature", "min_score": 0.35},
    {"text": "The system shall generate batch records", "min_score": 0.35},
    {"text": "The system shall provide audit trail for all user actions", "min_score": 0.35}
  ],
  "expert_mode": false
}
```

Add header: `X-EVOLV-MODE: Sandbox`

Execute.

**Say:**
> "202 Accepted. We got a job ID back in milliseconds.
> The platform is processing 3 requirements in the background.
> In production, you can submit 500 at once."

Point to the sandbox flag:
> "See this — `'sandbox': true`. We added that header to tell EVOLV
> this is a test run. Nothing was written to the production audit trail.
> Your developers can build integrations without ever touching real validation data."

Click **GET /bulk/status/{job_id}**. Enter the job_id.

> "Real-time progress. Every item individually tracked.
> If item 3 fails, items 1 and 2 are still delivered.
> No batch failures. No lost work."

---

## DEMO ACT 5 — "The Wow Rule" (2 minutes)

Go back to the Swagger UI.

**Say:**
> "Let me show you one more thing. This is the feature that makes our compliance
> officers genuinely emotional."

Explain the Policy Engine:

> "In EVOLV, if you try to approve a GxP document —
> a URS, a test script, a validation report —
> and your training record has expired,
> the platform will not let you.
>
> Not 'it will warn you.' Not 'it will ask for a reason.'
> It will **deny the action**. Full stop. No exceptions.
>
> It doesn't matter if you're the VP of Quality.
> It doesn't matter if you're the system owner.
> If your training is expired, you cannot approve a GxP document.
>
> This one rule eliminates an entire category of FDA 483 observations:
> 'Approvals obtained from personnel without current training records.'
> We hardcoded it into the platform so no one can turn it off."

**Pause.**

> "That's EVOLV. Not a validation tool. A compliance platform with opinions."

---

## DEMO ACT 6 — Close (2 minutes)

**Say:**
> "Let me summarise what you've seen in the last 15 minutes:
>
> 1. A plain English description became a GAMP 5-compliant URS
>    with regulatory rationale in 12 seconds.
>
> 2. A requirement change was analyzed for impact across the entire
>    validation package — test cases, risks, regulatory clauses —
>    with a natural language explanation that would satisfy an FDA inspector.
>
> 3. 500 requirements can be processed in a single API call while your LIMS
>    continues working, with real-time progress and per-item error isolation.
>
> 4. A developer cannot accidentally corrupt production audit data
>    because Sandbox mode is built into the protocol.
>
> 5. An untrained user cannot approve a GxP document.
>    This is not a policy. It is architecture.
>
> Your competitors — Kneat, Veeva, ValGenesis — do none of this.
> They are document managers with a validation-shaped interface.
>
> EVOLV is what happens when you build a compliance platform
> with the same engineering discipline you'd apply to SAP or Salesforce —
> but for the most regulated industry in the world.
>
> What questions do you have?"

---

## Anticipated Tough Questions & Answers

**Q: "How do we know the AI output is accurate?"**
A: Every output is grounded in a specific page and section of GAMP 5 via our knowledge base.
The Verification Agent triple-checks every generated requirement.
And the Logic Archive tells you exactly why every decision was made — SHA-256 signed.
If you can't audit the reasoning, we don't ship the output.

**Q: "What if the AI hallucinates a wrong regulatory citation?"**
A: The Verification Agent runs a Rationale Relevance check.
If the best GAMP 5 match score is below 0.45, the requirement is **rejected** — not delivered.
EVOLV fails loudly, not silently.

**Q: "Can we deploy this on-premises? Our data cannot leave our network."**
A: Yes. EVOLV supports full on-premises deployment.
Your OpenAI calls stay inside your Azure subscription.
Your Pinecone index stays in your private cloud.
Audit data stays in your data centre.
We deploy the platform. Your data stays yours.

**Q: "How is this different from ChatGPT with a prompt?"**
A: ChatGPT doesn't know what GAMP 5 says.
ChatGPT doesn't reject outputs that contradict regulatory guidance.
ChatGPT doesn't produce SHA-256 signed audit trails.
ChatGPT doesn't enforce training records.
ChatGPT is a language model. EVOLV is a compliance platform.
One of them you can use in an FDA inspection. One of them you cannot.

**Q: "What's the validation status of EVOLV itself?"**
A: EVOLV is built on the same framework it validates.
Every EVOLV function has a URS requirement, a verification check, and a test script.
We eat our own cooking. Our own validation package is generated by EVOLV.

**Q: "How long does implementation take?"**
A: Tenant configuration: 1 day.
Pinecone knowledge base with your SOPs: 3–5 days.
First validated system through EVOLV: within 2 weeks.
Full deployment across your portfolio: 60–90 days.

---

## Key Numbers to Drop in the Room

| Stat | Value |
|---|---|
| Requirement generation time | 12 seconds (vs. 4 hours manual) |
| Test script generation | 2 minutes (vs. 3 weeks manual) |
| Change impact assessment | 2 seconds (vs. 2 weeks manual) |
| Regulatory frameworks embedded | 16 |
| AI agents in the platform | 11 |
| Max batch size | 500 requirements |
| Compliance checks per requirement | 3 (criticality, relevance, contradiction) |
| Audit trail integrity method | SHA-256 hash chain |
| Retry attempts for webhooks | 4 (immediate + 1min + 5min + 15min) |
| ABAC policy rules | 5 (strict priority chain) |
| Document types generated | URS, UR/FR, Test Script, Validation Report, VTM, VSR |
| Estimated ROI (mid-size pharma) | $3M–$4M per year |

---

*EVOLV | The Validation Factory*
*Powered by EVOLV | A WingstarTech Inc. Product*
*Confidential — For Discussion Purposes Only*
