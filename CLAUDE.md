# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CSV-GameChanger is a GAMP 5 and CSA (Computer Software Assurance) compliant CSV (Computer System Validation) Engine.

## Build and Development Commands

```bash
# Install dependencies
pip install fastapi uvicorn pydantic pinecone openai langchain-community langchain-text-splitters fpdf2

# Run the API server
uvicorn API.main:app --reload

# Run from project root
cd C:\Users\sreej\OneDrive\Desktop\CSV-GameChanger
uvicorn API.main:app --reload --host 0.0.0.0 --port 8000

# Generate URS document (interactive mode)
python scripts/draft_urs.py

# Generate URS from file
python scripts/draft_urs.py -f requirements.txt -n "Project Name"
```

## Architecture

```
CSV-GameChanger/
├── Agents/
│   ├── __init__.py
│   ├── risk_strategist.py       # GAMP 5 risk assessment logic
│   ├── requirement_architect.py # URS generation from natural language
│   ├── verification_agent.py    # URS verification against GAMP 5 text
│   └── integrity_manager.py     # Central audit trail + logic archives
├── API/
│   ├── __init__.py
│   └── main.py                  # FastAPI app with ServiceNow webhook
├── scripts/
│   ├── setup_pinecone_index.py  # Creates Pinecone index
│   ├── ingest_docs.py           # Ingests GAMP 5 PDFs to Pinecone
│   └── draft_urs.py             # Generate URS documents from requirements
├── utils/
│   ├── __init__.py
│   └── pdf_generator.py         # URS PDF export with signature page
├── output/
│   ├── urs/                     # Generated URS Markdown/PDF files
│   └── logic_archives/          # Hidden JSON logic-archive files (generated)
├── audit_trail.log              # 21 CFR Part 11 compliant audit log (generated)
└── CLAUDE.md
```

## Current Implementation State

### API/main.py

**Endpoint:** `POST /webhook/sn-change`

Receives ServiceNow Change Requests and triggers automated risk assessment.

**Request Model (`ServiceNowChangeRequest`):**
```python
{
    "cr_id": str,              # Change Request ID
    "description": str,         # Change description
    "system_criticality": str,  # "high", "medium", "low", "critical", "minor"
    "change_type": str          # "emergency", "normal", "standard", "routine"
}
```

**Response Model (`ChangeRequestResponse`):**
```python
{
    "status": "assessed",
    "cr_id": str,
    "message": str,
    "timestamp": str,
    "risk_assessment": {
        "severity": str,           # HIGH, MEDIUM, LOW
        "occurrence": str,         # FREQUENT, OCCASIONAL, RARE
        "detectability": str,      # HIGH, MEDIUM, LOW
        "rpn": int,                # Risk Priority Number (1-27)
        "risk_level": str,         # "High", "Medium", "Low"
        "testing_strategy": str,   # CSA recommendation
        "patient_safety_override": bool
    }
}
```

**Audit Events Logged:**
1. `CHANGE_REQUEST_RECEIVED` - When CR arrives
2. `RISK_ASSESSMENT_COMPLETED` - After risk calculation
3. `CHANGE_REQUEST_FAILED` - On any error

**Exception Classes:**
- `CSVEngineError` - Base exception
- `ValidationError` (CSV-001) - Input validation failed
- `AuditLogError` (CSV-002) - Audit logging failed
- `ProcessingError` (CSV-003) - Processing failed

### Agents/risk_strategist.py

**Risk Strategist Agent** - Implements GAMP 5 risk-based approach.

**Enums:**
- `RiskLevel`: LOW, MEDIUM, HIGH
- `Severity`: LOW (1), MEDIUM (2), HIGH (3)
- `Occurrence`: RARE (1), OCCASIONAL (2), FREQUENT (3)
- `Detectability`: HIGH (1), MEDIUM (2), LOW (3)
- `TestingStrategy`: UNSCRIPTED, HYBRID, RIGOROUS_SCRIPTED

**Core Functions:**

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `calculate_risk_score()` | Severity, Occurrence, Detectability | (RPN, RiskLevel) | Calculates Risk Priority Number |
| `get_csa_testing_strategy()` | RiskLevel | TestingStrategy | Returns CSA testing recommendation |
| `assess_change_request()` | system_criticality, change_type | dict | Full assessment from ServiceNow fields |
| `map_criticality_to_severity()` | str | Severity | Maps ServiceNow criticality to GAMP 5 |
| `map_change_type_to_occurrence()` | str | Occurrence | Maps change type to occurrence |

**GAMP 5 Risk Logic:**
1. **Patient Safety Override:** If Severity = HIGH → Risk = HIGH (regardless of other factors)
2. **RPN Calculation:** Severity × Occurrence × Detectability (scale 1-27)
3. **Risk Thresholds:**
   - RPN ≤ 4 → LOW risk
   - RPN 5-12 → MEDIUM risk
   - RPN > 12 → HIGH risk

**CSA Testing Strategy:**
- LOW risk → Unscripted Testing
- MEDIUM risk → Hybrid Testing (Scripted + Unscripted)
- HIGH risk → Rigorous Scripted Testing

**ServiceNow Field Mappings:**

| system_criticality | → Severity |
|--------------------|------------|
| high, critical | HIGH |
| medium, moderate | MEDIUM |
| low, minor | LOW |

| change_type | → Occurrence |
|-------------|--------------|
| emergency, expedited | FREQUENT |
| normal | OCCASIONAL |
| standard, routine | RARE |

### Agents/requirement_architect.py

**Requirement Architect Agent** - Generates URS documents from natural language using GAMP 5 context.

**Class: `RequirementArchitect`**

Generates User Requirements Specifications by querying Pinecone for relevant GAMP 5 guidance.

**Enums:**
- `Criticality`: HIGH, MEDIUM, LOW
- `RiskAssessmentCategory`: GXP_DIRECT, GXP_INDIRECT, GXP_NONE
- `ImplementationMethod`: OUT_OF_THE_BOX, CONFIGURED, CUSTOM
- `URFRRiskLevel`: HIGH, MEDIUM, LOW
- `URFRTestStrategy`: OQ_UAT, INFORMAL, SUPPLIER_PROVIDED

**Data Classes:**
- `URSDocument`: Structured URS with urs_id, requirement_statement, criticality, regulatory_rationale

**Exception Classes:**
- `RegulatoryContextNotFoundError` (CSV-004) - No matching GAMP 5/CSA context found

**Data Classes:**
- `SearchResult`: chunk_id, text, source_document, page_number, similarity_score, reg_version
- `SearchResponse`: query, results, total_results

**Core Methods:**

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `search()` | query: str, top_k: int, min_score: float | SearchResponse | Queries Pinecone for GAMP 5/CSA chunks |
| `generate_urs()` | requirement: str, min_score: float | dict | Generates structured URS from natural language |
| `transform_urs_to_ur_fr()` | urs: dict, role, category, risk_assessment, implementation_method | dict | Transforms URS into UR/FR document (deterministic) |

**UR/FR Risk Matrix (RiskAssessmentCategory x ImplementationMethod → Risk Level):**

| IM \ RA | GxP Direct | GxP Indirect | GxP None |
|---------|-----------|-------------|---------|
| Custom | HIGH | MEDIUM | LOW |
| Configured | HIGH | HIGH | LOW |
| Out of the Box | MEDIUM | LOW | LOW |

**UR/FR Test Strategy Matrix (Risk Level x ImplementationMethod → Test Strategy):**

| Risk \ IM | Out of the Box | Configured | Custom |
|-----------|---------------|-----------|--------|
| HIGH | OQ and/or UAT | OQ and/or UAT | OQ and/or UAT |
| MEDIUM | Supplier Provided | Informal | Informal |
| LOW | Supplier Provided | Informal | Informal |

**URS Output Format:**
```python
{
    "URS_ID": "URS-7.1",
    "Requirement_Statement": "The system shall track warehouse temp.",
    "Criticality": "Medium",
    "Regulatory_Rationale": "Per GAMP5_Guide.pdf [GAMP5_Rev2] (p.42): ...",
    "Reg_Versions_Cited": ["GAMP5_Rev2"]
}
```

**Search Output Format:**
```python
{
    "query": "temperature monitoring",
    "total_results": 3,
    "results": [
        {
            "chunk_id": "abc123",
            "text": "Temperature monitoring is critical...",
            "source_document": "GAMP5_Guide.pdf",
            "page_number": 42,
            "similarity_score": 0.87,
            "reg_version": "GAMP5_Guide"
        }
    ]
}
```

**Criticality Classification Logic:**

| Criticality | Indicators |
|-------------|------------|
| HIGH | patient, safety, critical, gxp, compliance, validation, sterile, batch, release, adverse, pharmacovigilance, clinical, regulatory, fda, ema |
| MEDIUM | quality, audit, traceability, calibration, deviation, capa, change control, training, document, sop, warehouse, inventory, temperature |
| LOW | Administrative functions, non-GxP systems, convenience features |

**Dependencies:**
- Pinecone (csv-knowledge-base index)
- OpenAI (text-embedding-3-small)

**Usage Example:**
```python
from Agents.requirement_architect import (
    RequirementArchitect,
    RegulatoryContextNotFoundError
)

architect = RequirementArchitect()

# Search for relevant GAMP 5/CSA content
results = architect.search("temperature monitoring requirements")
for r in results.results:
    print(f"{r.source_document} (p.{r.page_number}): {r.text[:100]}...")

# Generate URS (requires at least one matching chunk)
try:
    urs = architect.generate_urs("I want to track warehouse temp")
    print(urs)
except RegulatoryContextNotFoundError as e:
    print(f"Error: {e}")

# Transform URS to UR/FR (deterministic, no LLM calls)
ur_fr = architect.transform_urs_to_ur_fr(
    urs=urs,
    role="Lab Technician",
    category="General",
    risk_assessment="GxP Indirect",
    implementation_method="Configured",
)
print(ur_fr["user_requirement"]["risk_level"])   # "High"
print(ur_fr["user_requirement"]["test_strategy"]) # "OQ and/or UAT"
```

**UR/FR Output Format:**
```python
{
    "urs_id": "URS-7.1",
    "requirement_summary": "The system shall track warehouse temperature.",
    "category": "General",
    "user_requirement": {
        "ur_id": "UR-1",
        "statement": "As a User, there will be track warehouse temperature so that the requirement is fulfilled.",
        "risk_assessment": "GxP Indirect",
        "implementation_method": "Configured",
        "risk_level": "High",
        "test_strategy": "OQ and/or UAT",
        "risk_note": "Final Risk Profiling will be decided with stakeholders..."
    },
    "functional_requirements": [
        {
            "fr_id": "FR-1",
            "parent_ur_id": "UR-1",
            "statement": "The system shall track warehouse temperature",
            "acceptance_criteria": ["Given/When/Then..."]
        }
    ],
    "assumptions_and_dependencies": ["..."],
    "compliance_notes": ["Cross-reference SOP-436231...", "..."],
    "implementation_notes": ["..."],
    "reg_versions_cited": ["GAMP5_Rev2"]
}
```

### Agents/verification_agent.py

**Verification Agent** - Reviews URS output from the RequirementArchitect against GAMP 5 regulatory text in Pinecone. Rejects non-compliant drafts and logs Compliance Exceptions.

**Class: `VerificationAgent`**

Runs three independent checks on each URS document:

1. **Criticality Alignment** - Detects under-classification by scanning GAMP 5 chunks for high-risk indicators when criticality is Low or Medium.
2. **Rationale Relevance** - Verifies the best Pinecone match score meets the relevance threshold (0.45).
3. **Contradiction Scan** - Matches known contradiction phrase pairs (e.g. "skip validation" vs. GAMP 5 "validation is required") across validation, testing, audit trail, and change control domains.

**Enums:**
- `Verdict`: APPROVED, REJECTED
- `CheckStatus`: PASS, FAIL

**Data Classes:**
- `VerificationFinding`: check_name, status, detail, gamp5_reference
- `VerificationResult`: urs_id, verdict, findings

**Exception Classes:**
- `VerificationError` (CSV-010) - Base verification error
- `InvalidURSError` (CSV-011) - URS missing required fields

**Core Methods:**

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `verify_urs()` | urs: dict, min_score: float | VerificationResult | Verify a single URS against GAMP 5 text |
| `verify_batch()` | urs_list: List[dict], min_score: float | List[VerificationResult] | Verify multiple URS documents |

**Configuration Constants:**

| Constant | Value | Purpose |
|----------|-------|---------|
| `VERIFICATION_TOP_K` | 5 | Max Pinecone results per query |
| `VERIFICATION_MIN_SCORE` | 0.35 | Minimum similarity score for retrieved chunks |
| `RATIONALE_RELEVANCE_THRESHOLD` | 0.45 | Minimum score for rationale to be considered relevant |

**High-Risk Indicators:**
patient, safety, critical, gxp, sterile, batch release, adverse event, pharmacovigilance, clinical, life-sustaining, life-supporting, validated, 21 cfr part 11

**Contradiction Pairs:**

| Requirement Phrase | Opposing GAMP 5 Keyword |
|--------------------|------------------------|
| skip validation, no validation required | validation, shall be validated |
| skip testing, no testing required | testing, shall be tested, test plan |
| no audit trail, disable audit | audit trail, traceability, 21 cfr part 11 |
| no change control, bypass change control | change control, change management |

**Audit Events Logged:**
1. `URS_VERIFIED` - URS passed all three checks (Compliance Impact: Regulatory Compliance)
2. `COMPLIANCE_EXCEPTION` - URS rejected due to check failure (Compliance Impact: Compliance Exception)
3. `URS_BATCH_VERIFIED` - Batch verification completed (Compliance Impact: Regulatory Compliance)

**Verification Result Output Format:**
```python
{
    "URS_ID": "URS-7.1",
    "Verdict": "Approved",  # or "Rejected"
    "Findings": [
        {
            "check_name": "Criticality Alignment",
            "status": "Pass",
            "detail": "Criticality Medium is consistent with ...",
            "gamp5_reference": "Per GAMP5_Guide.pdf [GAMP5_Guide] (p.42): ..."
        },
        {
            "check_name": "Rationale Relevance",
            "status": "Pass",
            "detail": "Best GAMP 5 match score is 0.87, above ...",
            "gamp5_reference": "Per GAMP5_Guide.pdf [GAMP5_Guide] (p.42): ..."
        },
        {
            "check_name": "Contradiction Scan",
            "status": "Pass",
            "detail": "No contradictions detected ...",
            "gamp5_reference": "Per GAMP5_Guide.pdf [GAMP5_Guide] (p.42): ..."
        }
    ]
}
```

**Dependencies:**
- Pinecone (csv-knowledge-base index)
- OpenAI (text-embedding-3-small)

**Usage Example:**
```python
from Agents.verification_agent import (
    VerificationAgent,
    InvalidURSError
)

agent = VerificationAgent()

# Verify a single URS from RequirementArchitect
urs = {
    "URS_ID": "URS-7.1",
    "Requirement_Statement": "The system shall track warehouse temperature.",
    "Criticality": "Medium",
    "Regulatory_Rationale": "Per GAMP 5 Guide (p.42): ..."
}

result = agent.verify_urs(urs)
print(result.verdict)       # "Approved" or "Rejected"
print(result.is_rejected)   # True/False

for finding in result.findings:
    print(f"{finding.check_name}: {finding.status} - {finding.detail}")

# Batch verification
results = agent.verify_batch([urs1, urs2, urs3])
rejected = [r for r in results if r.is_rejected]
```

### Agents/integrity_manager.py

**Integrity Manager Module** - Provides a central, append-only CSV audit trail and optional logic archives for AI reasoning transparency.

**Constants:**

| Constant | Value | Purpose |
|----------|-------|---------|
| `AUDIT_TRAIL_PATH` | `output/audit_trail.csv` | Central CSV audit trail |
| `LOGIC_ARCHIVE_DIR` | `output/logic_archives/` | Directory for JSON logic-archive files |
| `_ARCHIVE_SCHEMA_VERSION` | `"1.0.0"` | Schema version embedded in each archive |

**Core Functions:**

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `log_audit_event()` | agent_name, action, user_id, decision_logic, compliance_impact, audit_path, thought_process | str (SHA-256 hash) | Append audit record to CSV; optionally write logic archive |
| `_compute_reasoning_hash()` | timestamp, user_id, agent_name, action, decision_logic, compliance_impact | str (SHA-256 hex) | Tamper-evident hash over audit row fields |
| `_validate_thought_process()` | thought_process: Dict | None | Validates dict has `inputs`, `steps` (list), `outputs` keys |
| `_write_logic_archive()` | timestamp, agent_name, action, user_id, compliance_impact, decision_logic, audit_trail_hash, thought_process | Path | Write hidden JSON archive cross-referenced to CSV row |
| `_ensure_csv_header()` | path: Path | None | Write CSV header if file is new or empty |

**Logic Archive Feature:**

When `thought_process` is passed to `log_audit_event()`, a hidden dot-prefixed JSON file is written to `output/logic_archives/` containing the full AI reasoning chain (inputs, intermediate steps, outputs). The archive is cross-referenced to the CSV audit trail row via the SHA-256 reasoning hash and includes its own tamper-evident integrity hash.

**`thought_process` Required Shape:**
```python
{
    "inputs": { ... },   # Dict - agent inputs
    "steps": [ ... ],    # List - intermediate reasoning steps
    "outputs": { ... },  # Dict - agent outputs
}
```

**Logic Archive JSON Schema:**
```json
{
    "$schema_version": "1.0.0",
    "archive_type": "logic_archive",
    "audit_trail_hash": "<SHA-256 from CSV row>",
    "timestamp": "<ISO-8601>",
    "agent_name": "...",
    "action": "...",
    "user_id": "...",
    "compliance_impact": "...",
    "decision_logic_summary": "...",
    "inputs": { },
    "steps": [ ],
    "outputs": { },
    "integrity": {
        "archive_hash": "<SHA-256 of JSON content>",
        "algorithm": "sha256"
    }
}
```

**Archive Filename Convention:** `.{ACTION}_{YYYYMMDDTHHMMSSZ}_{hash[:8]}.json`

**Backward Compatibility:** The `thought_process` parameter defaults to `None`. All existing callers of `log_audit_event()` are unaffected.

**Thread Safety:** Archive writes occur inside the same `_write_lock` as CSV writes, ensuring the CSV row and JSON file are atomically paired.

**Audit Events Logged:**
All agent actions across the system are logged through this module. See `_IMPACT_MAP` for the full action-to-compliance-impact mapping.

**Usage Example:**
```python
from Agents.integrity_manager import log_audit_event

# Without logic archive (existing behavior)
reasoning_hash = log_audit_event(
    agent_name="RiskStrategist",
    action="RISK_ASSESSMENT_COMPLETED",
    decision_logic="RPN=6, Medium risk",
)

# With logic archive
reasoning_hash = log_audit_event(
    agent_name="RequirementArchitect",
    action="URS_GENERATED",
    decision_logic="Generated URS-7.1 from warehouse temp requirement",
    thought_process={
        "inputs": {"requirement": "Track warehouse temperature"},
        "steps": [
            "Queried Pinecone for GAMP 5 context",
            "Classified criticality as Medium",
            "Built regulatory rationale from page 42",
        ],
        "outputs": {"urs_id": "URS-7.1", "criticality": "Medium"},
    },
)
```

### scripts/draft_urs.py

**URS Drafting Script** - Generates complete URS documents from project descriptions.

**Features:**
- Interactive mode for entering requirements
- File input mode for batch processing
- Command-line arguments for automation
- Outputs Markdown files to `output/urs/`

**Core Functions:**

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `draft_urs()` | project_name, project_description | dict | Main entry point for URS generation |
| `parse_requirements()` | project_description | List[str] | Parses bullets/numbered lists into requirements |
| `generate_urs_table()` | requirements, project_name | str | Generates Markdown table format |
| `save_urs_document()` | content, project_name | Path | Saves to output/urs/ directory |

**Usage:**
```bash
# Interactive mode
python scripts/draft_urs.py

# From file
python scripts/draft_urs.py -f requirements.txt -n "My Project"

# Direct input
python scripts/draft_urs.py -n "Warehouse System" -r "Track temperature" "Monitor humidity"

# With custom similarity threshold
python scripts/draft_urs.py -n "Project" -r "requirement" --min-score 0.4
```

**Output Format:**
Generates a Markdown file with:
- Header with project name and timestamp
- Requirements table (URS ID, Statement, Criticality, Rationale)
- Detailed requirements section with full regulatory rationale
- List of failed requirements (if any)

**Example Output File:** `output/urs/URS_Warehouse_System_20240115_143022.md`

### utils/pdf_generator.py

**URS PDF Generator** - Converts approved URS dictionaries into professional two-page PDFs with a Manifestation of Signature page for 21 CFR Part 11 compliance.

**Core Function:**

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `generate_urs_pdf()` | urs: dict, signer_name: str, meaning: str | bytes | Generate a two-page PDF from an approved URS |

**Parameters:**

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `urs` | Dict[str, Any] | required | URS dict with URS_ID, Requirement_Statement, Criticality, Regulatory_Rationale, Reg_Versions_Cited |
| `signer_name` | str | required | Full name of the approver |
| `meaning` | str | "Approval of Requirements" | Meaning of the electronic signature |

**PDF Structure:**

- **Page 1 — URS Document:**
  - Branded header (TRUSTME AI | CSV Engine)
  - URS ID and generation timestamp
  - Requirement Statement
  - Criticality (color-coded: High=red, Medium=amber, Low=green)
  - Regulatory Rationale (split by citation)
  - Regulatory Versions Cited
  - Page footer with page number and date

- **Page 2 — Manifestation of Signature:**
  - Title: "Manifestation of Signature"
  - Signature table with Document, Signer Name, Timestamp (UTC), Meaning
  - Signature and date lines
  - 21 CFR Part 11 compliance note

**Dependencies:**
- fpdf2

**Usage Example:**
```python
from utils.pdf_generator import generate_urs_pdf

urs = {
    "URS_ID": "URS-7.1",
    "Requirement_Statement": "The system shall track warehouse temperature.",
    "Criticality": "Medium",
    "Regulatory_Rationale": "Per GAMP5_Guide.pdf [GAMP5_Rev2] (p.42): ...",
    "Reg_Versions_Cited": ["GAMP5_Rev2"],
}

pdf_bytes = generate_urs_pdf(
    urs=urs,
    signer_name="Jane Smith",
    meaning="Approval of Requirements",
)

# Write to file
with open("URS-7.1.pdf", "wb") as f:
    f.write(pdf_bytes)

# Or use with Streamlit
st.download_button("Download PDF", data=pdf_bytes, file_name="URS-7.1.pdf", mime="application/pdf")
```

## URS Traceability Index

| URS ID | Requirement | Implemented In |
|--------|-------------|----------------|
| URS-1.1 | Accept change requests from ServiceNow | `API/main.py:receive_servicenow_change()` |
| URS-1.2 | Acknowledge receipt of change requests | `API/main.py:ChangeRequestResponse` |
| URS-2.1 | Maintain 21 CFR Part 11 compliant audit trail | `API/main.py:log_audit_event()` |
| URS-3.1 | Classify risk as Low, Medium, or High | `Agents/risk_strategist.py:RiskLevel` |
| URS-3.2 | Assess severity based on patient impact | `Agents/risk_strategist.py:Severity` |
| URS-3.3 | Assess occurrence likelihood | `Agents/risk_strategist.py:Occurrence` |
| URS-3.4 | Assess detectability of failures | `Agents/risk_strategist.py:Detectability` |
| URS-4.1 | Recommend testing strategy per CSA | `Agents/risk_strategist.py:TestingStrategy` |
| URS-4.2 | Calculate risk using GAMP 5 methodology | `Agents/risk_strategist.py:calculate_risk_score()` |
| URS-4.3 | Classify RPN into risk categories | `Agents/risk_strategist.py:_determine_risk_level()` |
| URS-4.4 | Recommend CSA testing strategy | `Agents/risk_strategist.py:get_csa_testing_strategy()` |
| URS-4.5 | Map external criticality to severity | `Agents/risk_strategist.py:map_criticality_to_severity()` |
| URS-4.6 | Map change type to occurrence | `Agents/risk_strategist.py:map_change_type_to_occurrence()` |
| URS-4.7 | Assess risk for all change requests | `Agents/risk_strategist.py:assess_change_request()` |
| URS-6.1 | Generate URS from natural language input | `Agents/requirement_architect.py:generate_urs()` |
| URS-6.2 | Classify requirements as High/Med/Low | `Agents/requirement_architect.py:Criticality` |
| URS-6.3 | Output structured URS documents | `Agents/requirement_architect.py:URSDocument` |
| URS-6.4 | Provide JSON output format | `Agents/requirement_architect.py:URSDocument.to_dict()` |
| URS-6.5 | Connect to Pinecone knowledge base | `Agents/requirement_architect.py:RequirementArchitect.__init__()` |
| URS-6.6 | Validate environment before processing | `Agents/requirement_architect.py:_validate_dependencies()` |
| URS-6.7 | Embed user input for similarity search | `Agents/requirement_architect.py:_get_embedding()` |
| URS-6.8 | Retrieve relevant GAMP 5 sections | `Agents/requirement_architect.py:_query_pinecone()` |
| URS-6.9 | Assess requirement criticality | `Agents/requirement_architect.py:_determine_criticality()` |
| URS-6.10 | Assign unique URS identifiers | `Agents/requirement_architect.py:_generate_urs_id()` |
| URS-6.11 | Provide regulatory justification | `Agents/requirement_architect.py:_build_regulatory_rationale()` |
| URS-6.12 | Format requirements per standards | `Agents/requirement_architect.py:_format_requirement_statement()` |
| URS-6.13 | Require regulatory context for URS | `Agents/requirement_architect.py:RegulatoryContextNotFoundError` |
| URS-6.14 | Return structured search results | `Agents/requirement_architect.py:SearchResult` |
| URS-6.15 | Search knowledge base for context | `Agents/requirement_architect.py:search()` |
| URS-7.1 | Generate URS documents from project input | `scripts/draft_urs.py:draft_urs()` |
| URS-7.2 | Parse requirements from description | `scripts/draft_urs.py:parse_requirements()` |
| URS-7.3 | Output URS as Markdown table | `scripts/draft_urs.py:generate_urs_table()` |
| URS-7.4 | Save URS to output/urs directory | `scripts/draft_urs.py:save_urs_document()` |
| URS-7.5 | Accept interactive user input | `scripts/draft_urs.py:interactive_input()` |
| URS-12.1 | Verify generated URS against GAMP 5 text | `Agents/verification_agent.py:VerificationAgent.verify_urs()` |
| URS-12.2 | Reject URS drafts that contradict regulatory guidance | `Agents/verification_agent.py:VerificationAgent.verify_urs()` |
| URS-12.3 | Report verification errors | `Agents/verification_agent.py:VerificationError` |
| URS-12.4 | Produce structured verification findings | `Agents/verification_agent.py:VerificationFinding` |
| URS-12.5 | Connect to Pinecone for verification queries | `Agents/verification_agent.py:VerificationAgent.__init__()` |
| URS-12.6 | Validate environment before verification | `Agents/verification_agent.py:VerificationAgent._validate_dependencies()` |
| URS-12.7 | Embed text for verification queries | `Agents/verification_agent.py:VerificationAgent._get_embedding()` |
| URS-12.8 | Retrieve GAMP 5 text for verification | `Agents/verification_agent.py:VerificationAgent._query_pinecone()` |
| URS-12.9 | Validate URS input before verification | `Agents/verification_agent.py:VerificationAgent._validate_urs()` |
| URS-12.10 | Detect criticality misclassification | `Agents/verification_agent.py:VerificationAgent._check_criticality_alignment()` |
| URS-12.11 | Verify rationale relevance | `Agents/verification_agent.py:VerificationAgent._check_rationale_relevance()` |
| URS-12.12 | Detect contradictions between URS and GAMP 5 | `Agents/verification_agent.py:VerificationAgent._check_contradictions()` |
| URS-12.13 | Support batch verification | `Agents/verification_agent.py:VerificationAgent.verify_batch()` |
| URS-13.1 | Archive AI reasoning alongside audit records | `Agents/integrity_manager.py:log_audit_event()` |
| URS-13.2 | Validate thought-process payload shape | `Agents/integrity_manager.py:_validate_thought_process()` |
| URS-13.3 | Write tamper-evident logic-archive JSON | `Agents/integrity_manager.py:_write_logic_archive()` |
| URS-13.4 | Cross-reference archive to CSV audit row | `Agents/integrity_manager.py:_write_logic_archive()` |
| URS-13.5 | Compute integrity hash for archive file | `Agents/integrity_manager.py:_write_logic_archive()` |
| URS-15.1 | Generate URS as professional PDF | `utils/pdf_generator.py:generate_urs_pdf()` |
| URS-15.2 | Append Manifestation of Signature page | `utils/pdf_generator.py:generate_urs_pdf()` |
| URS-15.3 | Include signer name, timestamp, and meaning | `utils/pdf_generator.py:generate_urs_pdf()` |
| URS-15.4 | Provide PDF download from Streamlit UI | `frontend/app.py` (Page 2) |
| URS-14.1 | Derive reg version from PDF filename at ingestion | `scripts/ingest_docs.py:_derive_reg_version()` |
| URS-14.2 | Store reg_version in Pinecone chunk metadata | `scripts/ingest_docs.py:DocumentChunk.to_metadata()` |
| URS-14.3 | Propagate reg_version through search results | `Agents/requirement_architect.py:SearchResult` |
| URS-14.4 | Include reg version in verification citations | `Agents/verification_agent.py:_format_gamp5_ref()` |
| URS-14.5 | Include reg version in URS rationale citations | `Agents/requirement_architect.py:_build_regulatory_rationale()` |
| URS-14.6 | Collect Reg_Versions_Cited per URS | `Agents/requirement_architect.py:generate_urs()` |
| URS-14.7 | Include regulatory version footer in URS document | `scripts/draft_urs.py:generate_urs_table()` |
| URS-14.8 | Detect new regulatory versions at ingestion | `scripts/ingest_docs.py:ingest_documents()` |
| URS-14.9 | Detect new regulatory versions at query time | `Agents/requirement_architect.py:search()` |
| URS-14.10 | Detect new regulatory versions during verification | `Agents/verification_agent.py:verify_urs()` |
| URS-14.11 | Include reg version in gap analysis citations | `Agents/ingestor_agent.py:analyze_gaps()` |
| URS-16.1 | Classify UR risk assessment and implementation method | `Agents/requirement_architect.py:RiskAssessmentCategory, ImplementationMethod` |
| URS-16.2 | Determine UR/FR risk level from matrix | `Agents/requirement_architect.py:_determine_ur_fr_risk_level()` |
| URS-16.3 | Determine UR/FR test strategy from matrix | `Agents/requirement_architect.py:_determine_ur_fr_test_strategy()` |
| URS-16.4 | Decompose URS into functional requirements | `Agents/requirement_architect.py:_split_requirement_to_frs()` |
| URS-16.5 | Generate acceptance criteria for FRs | `Agents/requirement_architect.py:_generate_acceptance_criteria()` |
| URS-16.6 | Transform URS to UR/FR document | `Agents/requirement_architect.py:transform_urs_to_ur_fr()` |
| URS-16.7 | Log UR/FR transformation to audit trail | `Agents/requirement_architect.py:transform_urs_to_ur_fr()` |

## Coding Standards (GAMP 5 / CSA / 21 CFR Part 11)

### 1. Type Safety
Use Python type hints for every function. This prevents data integrity errors before they happen.

```python
# Correct
def calculate_risk(score: int, category: str) -> RiskLevel:
    ...

# Incorrect
def calculate_risk(score, category):
    ...
```

### 2. Documentation (The Traceability Rule)
Every function must have a docstring that includes a `:requirement:` tag linking it back to User Requirements (URS).

```python
def assess_change_risk(change_request: ServiceNowChangeRequest) -> RiskAssessment:
    """
    Evaluate the risk level of a ServiceNow change request.

    :param change_request: The incoming change request to assess.
    :return: RiskAssessment with level and justification.
    :requirement: URS-4.2 - System shall assess risk for all change requests.
    """
    ...
```

### 3. Audit Readiness
All API endpoints must log `user_id`, `timestamp`, and `action` to an immutable audit trail. No operation should occur without a traceable record.

```python
audit_logger.info(
    "API_CALL",
    user_id=user_id,
    timestamp=datetime.utcnow().isoformat(),
    action="CHANGE_REQUEST_RECEIVED",
    details={"cr_id": change_request.cr_id}
)
```

### 4. Error Handling
Use graceful exception handling with specific error codes. Silent failures are prohibited in a validated system.

```python
class CSVEngineError(Exception):
    """Base exception for CSV Engine errors."""
    pass

class ValidationError(CSVEngineError):
    """Error code: CSV-001 - Input validation failed."""
    error_code = "CSV-001"

class AuditLogError(CSVEngineError):
    """Error code: CSV-002 - Audit logging failed."""
    error_code = "CSV-002"
```

### 5. Style
Follow PEP 8 strictly. Readable code is auditable code.

- 4 spaces for indentation
- Maximum line length: 79 characters
- Two blank lines between top-level definitions
- One blank line between method definitions
- Use snake_case for functions and variables
- Use PascalCase for classes
