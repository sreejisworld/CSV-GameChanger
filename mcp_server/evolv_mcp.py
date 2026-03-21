"""
evolv_mcp.py — EVOLV MCP Server.

Exposes EVOLV's core validation agents as native Claude tools via the
Model Context Protocol (MCP). Claude can call these tools directly
without copy-pasting JSON between API calls.

Tools exposed:
  - generate_urs        : RequirementArchitect.generate_urs()
  - verify_urs          : VerificationAgent.verify_urs()
  - transform_ur_fr     : RequirementArchitect.transform_urs_to_ur_fr()
  - generate_csa_test   : DeltaAgent.generate_csa_test_from_ur_fr()
  - assess_risk         : RiskStrategist.assess_change_request()
  - refine_smart        : SMARTRequirementsEngine.refine_to_smart()
  - query_knowledge_base: RequirementArchitect.search()

Run with:
  python -m mcp_server.evolv_mcp

Or via MCP CLI:
  mcp dev mcp_server/evolv_mcp.py

:requirement: URS-6.1 - Generate URS from natural language input.
:requirement: URS-12.1 - Verify generated URS against GAMP 5 text.
:requirement: URS-17.1 - Generate CSA test scripts from UR/FR documents.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise SystemExit(
        "fastmcp not installed. Run: pip install fastmcp"
    ) from exc


# ── MCP server instance ────────────────────────────────────────────
mcp = FastMCP(
    name="EVOLV Validation Engine",
    instructions=(
        "You have access to EVOLV — a GAMP 5 / 21 CFR Part 11 compliant "
        "Computer System Validation Engine. Use these tools to generate "
        "URS documents, verify compliance, assess risk, and build "
        "full CSA test scripts from natural-language requirements."
    ),
)


# ── Lazy agent imports (avoid slow startup if env vars missing) ────
def _get_architect():
    from Agents.requirement_architect import RequirementArchitect
    return RequirementArchitect()


def _get_verifier():
    from Agents.verification_agent import VerificationAgent
    return VerificationAgent()


def _get_delta():
    from Agents.delta_agent import DeltaAgent
    return DeltaAgent()


def _get_risk():
    from Agents.risk_strategist import assess_change_request
    return assess_change_request


def _get_smart():
    from Agents.smart_requirements_engine import SMARTRequirementsEngine
    return SMARTRequirementsEngine()


# ── Tool: generate_urs ─────────────────────────────────────────────
@mcp.tool()
def generate_urs(requirement: str, min_score: float = 0.35) -> dict:
    """
    Generate a GAMP 5-compliant User Requirements Specification (URS)
    from a plain-English requirement statement.

    Returns a structured URS dict with URS_ID, Requirement_Statement,
    Criticality, Regulatory_Rationale, and Reg_Versions_Cited.

    :requirement: URS-6.1 - Generate URS from natural language input.
    """
    architect = _get_architect()
    return architect.generate_urs(requirement, min_score=min_score)


# ── Tool: verify_urs ──────────────────────────────────────────────
@mcp.tool()
def verify_urs(urs: dict) -> dict:
    """
    Verify a URS dict against the GAMP 5 knowledge base.

    Runs three checks: Criticality Alignment, Rationale Relevance,
    and Contradiction Scan. Returns verdict (Approved / Rejected)
    and structured findings per check.

    :requirement: URS-12.1 - Verify generated URS against GAMP 5 text.
    """
    verifier = _get_verifier()
    result = verifier.verify_urs(urs)
    return {
        "URS_ID":   result.urs_id,
        "Verdict":  result.verdict.value,
        "Findings": [
            {
                "check_name":      f.check_name,
                "status":          f.status.value,
                "detail":          f.detail,
                "gamp5_reference": f.gamp5_reference,
            }
            for f in result.findings
        ],
    }


# ── Tool: transform_ur_fr ─────────────────────────────────────────
@mcp.tool()
def transform_ur_fr(
    urs: dict,
    role: str = "User",
    category: str = "General",
    risk_assessment: str = "GxP Indirect",
    implementation_method: str = "Configured",
    additional_context: dict | None = None,
) -> dict:
    """
    Transform an approved URS into a structured UR/FR document.

    Applies the GAMP 5 risk matrix (GxP category × implementation
    method → risk level) and derives the CSA test strategy.

    :requirement: URS-16.6 - Transform URS to UR/FR document.
    """
    architect = _get_architect()
    return architect.transform_urs_to_ur_fr(
        urs=urs,
        role=role,
        category=category,
        risk_assessment=risk_assessment,
        implementation_method=implementation_method,
        additional_context=additional_context,
    )


# ── Tool: generate_csa_test ───────────────────────────────────────
@mcp.tool()
def generate_csa_test(
    ur_fr: dict,
    test_type: str = "Informal",
) -> dict:
    """
    Generate a CSA test script from a UR/FR document.

    test_type must be one of: "Informal", "Formal OQ", "Formal UAT".

    High-risk: returns scripted steps (setup + positive + negative +
    edge cases or UAT business process).
    Medium/Low-risk: returns an exploratory test charter.

    :requirement: URS-17.1 - Generate CSA test scripts from UR/FR documents.
    """
    delta = _get_delta()
    return delta.generate_csa_test_from_ur_fr(ur_fr, test_type)


# ── Tool: assess_risk ─────────────────────────────────────────────
@mcp.tool()
def assess_risk(
    system_criticality: str,
    change_type: str,
    cr_id: str = "CR-MCP",
) -> dict:
    """
    Assess the GAMP 5 risk level for a change request.

    system_criticality: "high" | "critical" | "medium" | "low" | "minor"
    change_type:        "emergency" | "normal" | "standard" | "routine"

    Returns risk assessment with severity, occurrence, detectability,
    RPN, risk level, testing strategy, and patient safety override flag.

    :requirement: URS-4.7 - Assess risk for all change requests.
    """
    assess = _get_risk()
    return assess(
        system_criticality=system_criticality,
        change_type=change_type,
    )


# ── Tool: refine_smart ────────────────────────────────────────────
@mcp.tool()
def refine_smart(
    requirements: list[str],
    use_llm: bool = False,
) -> dict:
    """
    Refine vague requirements to SMART (Specific, Measurable, Achievable,
    Relevant, Time-bound) format with GAMP 5 / FDA CSA alignment.

    Detects FDA/EMA 2026 AI Guidance triggers, rewrites vague language,
    generates acceptance criteria, and classifies risk level per requirement.

    Returns aggregate stats and a list of refined SMART requirement objects.

    :requirement: URS-21.3 - Rewrite vague requirements to SMART format.
    """
    engine = _get_smart()
    result = engine.refine_to_smart(requirements, use_llm=use_llm)
    return {
        "stats":        result.stats,
        "requirements": [
            {
                "original":            r.original,
                "smart":               r.smart,
                "risk_level":          r.risk_level,
                "acceptance_criteria": r.acceptance_criteria,
                "fda_ema_flags":       r.fda_ema_flags,
                "negative_tests":      r.negative_tests,
            }
            for r in result.requirements
        ],
    }


# ── Tool: query_knowledge_base ────────────────────────────────────
@mcp.tool()
def query_knowledge_base(
    query: str,
    top_k: int = 5,
    min_score: float = 0.35,
) -> dict:
    """
    Search the GAMP 5 / CSA Pinecone knowledge base for relevant
    regulatory guidance chunks.

    Returns matching chunks with source document, page number,
    similarity score, and regulatory version tag.

    :requirement: URS-6.15 - Search knowledge base for context.
    """
    architect = _get_architect()
    result = architect.search(query, top_k=top_k, min_score=min_score)
    return {
        "query":        result.query,
        "total_results": result.total_results,
        "results": [
            {
                "chunk_id":        r.chunk_id,
                "text":            r.text,
                "source_document": r.source_document,
                "page_number":     r.page_number,
                "similarity_score": r.similarity_score,
                "reg_version":     r.reg_version,
            }
            for r in result.results
        ],
    }


# ── Entry point ────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
