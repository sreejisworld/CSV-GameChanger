"""
generate_script.py — FastAPI router for on-demand CSA test script generation.

Endpoint:
  POST /verify/generate-script  — Accept risk data rows, call DeltaAgent,
                                   and return a CSA test script.

:requirement: URS-17.1 - Generate CSA test scripts from UR/FR documents.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

router = APIRouter(tags=["Verify"])


class RiskRow(BaseModel):
    id:            str
    type:          str = "UR"
    statement:     str = ""
    impact:        str = "GxP Indirect"
    implMethod:    str = "Configured"
    testAssurance: str = "Scripted"
    riskLevel:     Optional[str] = None


class GenerateScriptRequest(BaseModel):
    """
    Request body for POST /verify/generate-script.

    Accepts the risk rows from the React Risk page and derives a
    UR/FR document, then generates a CSA test script via DeltaAgent.

    :requirement: URS-17.1 - Generate CSA test scripts from UR/FR documents.
    """
    project_name:  str = Field("Untitled Project")
    gamp_category: str = ""
    rows:          List[RiskRow] = Field(..., min_length=1)
    test_type:     str = "Informal"


def _calc_risk(impact: str, impl: str) -> str:
    if impact == "No GxP":
        return "Low"
    if impact == "GxP Direct":
        return "Medium" if impl == "Out of the Box" else "High"
    # GxP Indirect
    if impl == "Configured":
        return "High"
    if impl == "Custom":
        return "Medium"
    return "Low"


def _build_ur_fr(rows: List[RiskRow], project_name: str) -> dict:
    """Build a minimal UR/FR dict from risk rows for DeltaAgent."""
    ur_rows = [r for r in rows if r.type == "UR"]
    fr_rows = [r for r in rows if r.type == "FR"]

    if not ur_rows:
        ur_rows = rows[:1]

    ur       = ur_rows[0]
    risk_lvl = ur.riskLevel or _calc_risk(ur.impact, ur.implMethod)

    ur_fr = {
        "urs_id":             f"URS-{ur.id}",
        "requirement_summary": ur.statement or f"Requirement {ur.id}",
        "category":           "General",
        "user_requirement": {
            "ur_id":                ur.id,
            "statement":            (
                f"As a User, the system shall fulfil: {ur.statement}"
            ),
            "risk_assessment":      ur.impact,
            "implementation_method": ur.implMethod,
            "risk_level":           risk_lvl,
            "test_strategy": (
                "OQ and/or UAT" if risk_lvl == "High" else "Informal"
            ),
        },
        "functional_requirements": [
            {
                "fr_id":              fr.id,
                "parent_ur_id":       ur.id,
                "statement":          fr.statement or f"FR {fr.id}",
                "acceptance_criteria": [
                    f"Given the system is operational, "
                    f"When {fr.statement or fr.id} is executed, "
                    f"Then the expected outcome is achieved per "
                    f"{ur.impact} requirements.",
                ],
            }
            for fr in (fr_rows or [ur])
        ],
        "assumptions_and_dependencies": [
            f"Project: {project_name}",
        ],
        "compliance_notes": [
            f"Impact: {ur.impact} | Method: {ur.implMethod}",
        ],
        "reg_versions_cited": ["GAMP5_Rev2"],
    }
    return ur_fr


@router.post("/generate-script")
def generate_script(body: GenerateScriptRequest) -> dict:
    """
    Generate a CSA test script from Risk page data.

    Builds a UR/FR document from the risk rows, then calls
    DeltaAgent.generate_csa_test_from_ur_fr().

    :requirement: URS-17.1 - Generate CSA test scripts from UR/FR.
    """
    try:
        from Agents.delta_agent import DeltaAgent
        agent = DeltaAgent()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"DeltaAgent unavailable: {exc}",
        ) from exc

    ur_fr = _build_ur_fr(body.rows, body.project_name)

    try:
        script = agent.generate_csa_test_from_ur_fr(ur_fr, body.test_type)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Script generation failed: {exc}",
        ) from exc

    return script
