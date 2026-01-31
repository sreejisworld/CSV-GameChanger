# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CSV-GameChanger is a GAMP 5 and CSA (Computer Software Assurance) compliant CSV (Computer System Validation) Engine.

## Build and Development Commands

```bash
# Install dependencies
pip install fastapi uvicorn pydantic pinecone openai langchain-community langchain-text-splitters

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
│   └── requirement_architect.py # URS generation from natural language
├── API/
│   ├── __init__.py
│   └── main.py                  # FastAPI app with ServiceNow webhook
├── scripts/
│   ├── setup_pinecone_index.py  # Creates Pinecone index
│   ├── ingest_docs.py           # Ingests GAMP 5 PDFs to Pinecone
│   └── draft_urs.py             # Generate URS documents from requirements
├── output/
│   └── urs/                     # Generated URS Markdown files
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

**Data Classes:**
- `URSDocument`: Structured URS with urs_id, requirement_statement, criticality, regulatory_rationale

**Exception Classes:**
- `RegulatoryContextNotFoundError` (CSV-004) - No matching GAMP 5/CSA context found

**Data Classes:**
- `SearchResult`: chunk_id, text, source_document, page_number, similarity_score
- `SearchResponse`: query, results, total_results

**Core Methods:**

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `search()` | query: str, top_k: int, min_score: float | SearchResponse | Queries Pinecone for GAMP 5/CSA chunks |
| `generate_urs()` | requirement: str, min_score: float | dict | Generates structured URS from natural language |

**URS Output Format:**
```python
{
    "URS_ID": "URS-7.1",
    "Requirement_Statement": "The system shall track warehouse temp.",
    "Criticality": "Medium",
    "Regulatory_Rationale": "Per GAMP 5 Guide (p.42): ..."
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
            "similarity_score": 0.87
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
