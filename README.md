# CSV-GameChanger

A GAMP 5 and CSA (Computer Software Assurance) compliant CSV (Computer System Validation) engine. Automates risk assessment, URS generation, regulatory verification, and test script creation using AI agents backed by a Pinecone vector knowledge base of regulatory guidance documents.

## Architecture

```
CSV-GameChanger/
├── main.py                        # Root API server (health-check + URS generation)
├── Agents/
│   ├── risk_strategist.py         # GAMP 5 risk assessment and RPN calculation
│   ├── requirement_architect.py   # URS generation from natural language via Pinecone
│   ├── verification_agent.py      # URS verification against GAMP 5 regulatory text
│   ├── test_generator.py          # CSA-aligned test script generation
│   ├── ingestor_agent.py          # Vendor document ingestion and gap analysis
│   └── integrity_manager.py       # Central audit trail + logic archives
├── API/
│   └── main.py                    # FastAPI app with ServiceNow webhook
├── scripts/
│   ├── ingest_docs.py             # Ingest GAMP 5 PDFs into Pinecone
│   ├── draft_urs.py               # Generate URS documents (interactive/batch)
│   ├── draft_vsr.py               # Generate Validation Summary Reports
│   ├── generate_vtm.py            # Generate Validation Test Matrix
│   ├── setup_pinecone_index.py    # Create Pinecone index
│   ├── monitor_changes.py         # Monitor change requests
│   └── sign_off.py                # Sign-off workflow
├── templates/
│   └── enterprise_standards/      # Industry-specific URS templates
│       ├── pharma_standard.json
│       ├── medtech_standard.json
│       └── lab_systems.json
├── docs/raw/                      # Regulatory guidance PDFs (GAMP 5, FDA, EU AI Act)
├── input/vendor_docs/             # Vendor documents for ingestion
└── output/
    ├── urs/                       # Generated URS Markdown files
    ├── logic_archives/            # AI reasoning archives (JSON)
    └── audit_trail.csv            # 21 CFR Part 11 compliant audit log
```

## Quick Start

### Prerequisites

- Python 3.11+
- Pinecone account with an index named `csv-knowledge-base`
- OpenAI API key (for text-embedding-3-small)

### Installation

```bash
pip install fastapi uvicorn pydantic pinecone openai langchain-community langchain-text-splitters python-docx PyPDF2
```

### Environment Variables

```bash
export OPENAI_API_KEY="your-openai-key"
export PINECONE_API_KEY="your-pinecone-key"
```

### Ingest Regulatory Documents

Place GAMP 5 / CSA PDFs in `docs/raw/`, then run:

```bash
python scripts/ingest_docs.py
```

This chunks the PDFs, generates embeddings, and upserts them to Pinecone with `reg_version` metadata derived from each filename.

### Run the API Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Test the Endpoints

```bash
# Health check
curl http://localhost:8000/

# Generate a URS
curl -X POST http://localhost:8000/generate-urs \
  -H "Content-Type: application/json" \
  -d '{"requirement": "I want to track warehouse temperature"}'
```

API docs are available at `http://localhost:8000/docs`.

## Agents

| Agent | Purpose |
|-------|---------|
| **RiskStrategist** | Calculates Risk Priority Number (RPN) using GAMP 5 severity/occurrence/detectability matrix. Recommends CSA testing strategy. |
| **RequirementArchitect** | Generates structured URS documents from natural language by querying Pinecone for relevant GAMP 5 guidance. |
| **VerificationAgent** | Reviews URS output against GAMP 5 text. Runs criticality alignment, rationale relevance, and contradiction scan checks. |
| **TestGenerator** | Produces CSA-aligned test scripts (scripted, hybrid, or unscripted) based on requirement criticality. |
| **IngestorAgent** | Reads vendor .docx/.pdf files, extracts requirements, and performs GAMP 5 gap analysis against the knowledge base. |
| **IntegrityManager** | Maintains an append-only CSV audit trail and optional JSON logic archives with tamper-evident SHA-256 hashes. |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/ingest_docs.py` | Chunk and embed regulatory PDFs into Pinecone |
| `scripts/draft_urs.py` | Generate URS documents (interactive, file, or CLI input) |
| `scripts/draft_vsr.py` | Generate Validation Summary Reports |
| `scripts/generate_vtm.py` | Generate Validation Test Matrix |
| `scripts/setup_pinecone_index.py` | Create the Pinecone index |
| `scripts/monitor_changes.py` | Monitor ServiceNow change requests |
| `scripts/sign_off.py` | Document sign-off workflow |

## Enterprise Templates

Industry-specific URS formatting is supported via JSON templates in `templates/enterprise_standards/`:

- **pharma_standard** -- Pharmaceutical (GxP, FDA/EMA compliance)
- **medtech_standard** -- Medical devices (IEC 62304, ISO 13485)
- **lab_systems** -- Laboratory systems (ISO 17025)

```bash
python scripts/draft_urs.py -t pharma_standard -n "My Project" -r "Track batch release"
```

## Regulatory Version Tracking

Each Pinecone vector carries a `reg_version` metadata field derived from the source PDF filename. This version is:

- Cited in URS rationale strings (e.g., `Per GAMP5_Guide.pdf [GAMP5_Guide] (p.42): ...`)
- Included in verification findings
- Collected in the `Reg_Versions_Cited` field of each generated URS
- Printed in the footer of generated URS Markdown documents

When a new regulatory version is detected at ingestion or query time, the system prompts for re-evaluation of existing logic.

## Compliance

- **GAMP 5** -- Risk-based approach to computerized system validation
- **CSA (Computer Software Assurance)** -- FDA guidance on risk-based testing
- **21 CFR Part 11** -- Electronic records and audit trail requirements
- All agent actions are logged to `output/audit_trail.csv` with SHA-256 reasoning hashes
- Logic archives in `output/logic_archives/` provide full AI reasoning transparency
