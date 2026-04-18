"""
test_authoring.py \u2014 FastAPI router for risk-adaptive test bundle
generation.

Endpoints:
  POST /test-authoring/generate       \u2014 Generate one bundle.
  POST /test-authoring/generate-batch \u2014 Generate bundles for a
                                        full requirement set.
  GET  /test-authoring/bundles        \u2014 List persisted bundles.
  GET  /test-authoring/bundle/{id}    \u2014 Load one persisted bundle.

:requirement: URS-22.4 - System shall generate risk-adaptive test
              bundles from risk-ranked requirements.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Agents.integrity_manager import log_audit_event
from Agents.test_authoring_engine import (
    GenerationMode,
    TestAuthoringEngine,
    TestAuthoringError,
)


router = APIRouter(tags=["Test Authoring"])

_engine: Optional[TestAuthoringEngine] = None


def _get_engine() -> TestAuthoringEngine:
    """Lazily construct the singleton engine."""
    global _engine
    if _engine is None:
        _engine = TestAuthoringEngine()
    return _engine


# ----------------------------------------------------------------------
# Pydantic models
# ----------------------------------------------------------------------


class FunctionalRequirement(BaseModel):
    fr_id: str = Field(..., description="Functional requirement ID")
    statement: str = Field("", description="FR statement")


class RiskAssessment(BaseModel):
    impact: str = Field(
        "GxP Indirect",
        description=(
            "Impact rating: 'GxP Direct', 'GxP Indirect', "
            "'No GxP'."
        ),
    )
    implMethod: str = Field(
        "Configured",
        description=(
            "Implementation method: 'Custom', 'Configured', "
            "'Out of the Box'."
        ),
    )


class GenerateBundleRequest(BaseModel):
    """
    Request body for POST /test-authoring/generate.

    :requirement: URS-22.4 - Generate risk-adaptive test bundles.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_name": "ACME LIMS",
                "requirement_id": "UR-1",
                "statement": (
                    "The system shall capture electronic "
                    "signatures per 21 CFR Part 11."
                ),
                "functional_requirements": [
                    {
                        "fr_id": "FR-1",
                        "statement": (
                            "Require username and password for "
                            "every signature."
                        ),
                    }
                ],
                "risk_assessment": {
                    "impact": "GxP Direct",
                    "implMethod": "Custom",
                },
                "mode": "hybrid",
                "test_type": "Informal",
                "persist": True,
            }
        }
    )

    project_name: str = Field("Untitled Project")
    requirement_id: str = Field(...)
    statement: str = Field("")
    functional_requirements: List[FunctionalRequirement] = Field(
        default_factory=list,
    )
    risk_assessment: RiskAssessment = Field(
        default_factory=RiskAssessment,
    )
    mode: str = Field("hybrid")
    test_type: str = Field("Informal")
    persist: bool = Field(True)


class RequirementRow(BaseModel):
    id: str
    type: str = "UR"
    statement: str = ""
    parentId: Optional[str] = None


class GenerateBatchRequest(BaseModel):
    """
    Request body for POST /test-authoring/generate-batch.

    :requirement: URS-22.8 - Support batch test bundle generation.
    """

    project_name: str = Field("Untitled Project")
    requirements: List[RequirementRow] = Field(..., min_length=1)
    risk_data: Dict[str, RiskAssessment] = Field(
        default_factory=dict,
    )
    mode: str = Field("hybrid")
    test_type: str = Field("Informal")
    persist: bool = Field(True)


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------


@router.post("/generate")
def generate_bundle(body: GenerateBundleRequest) -> Dict[str, Any]:
    """
    Generate a single risk-adaptive test bundle.

    :param body: Request payload.
    :return: Bundle dict.
    :raises HTTPException: 400 on bad input, 500 on engine failure.
    :requirement: URS-22.4 - Generate risk-adaptive test bundles.
    """
    log_audit_event(
        agent_name="API.test_authoring",
        action="TEST_BUNDLE_REQUEST_RECEIVED",
        decision_logic=(
            f"req_id={body.requirement_id} "
            f"mode={body.mode} type={body.test_type}"
        ),
    )

    if body.mode not in {m.value for m in GenerationMode}:
        log_audit_event(
            agent_name="API.test_authoring",
            action="TEST_BUNDLE_REQUEST_FAILED",
            decision_logic=f"Invalid mode {body.mode!r}",
        )
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid mode {body.mode!r}; expected one of "
                f"{[m.value for m in GenerationMode]}"
            ),
        )

    requirement = {
        "id": body.requirement_id,
        "type": "UR",
        "statement": body.statement,
        "functional_requirements": [
            fr.model_dump() for fr in body.functional_requirements
        ],
    }

    try:
        bundle = _get_engine().generate_bundle(
            requirement=requirement,
            risk_assessment=body.risk_assessment.model_dump(),
            mode=body.mode,
            test_type=body.test_type,
            project_name=body.project_name,
            persist=body.persist,
        )
    except TestAuthoringError as exc:
        log_audit_event(
            agent_name="API.test_authoring",
            action="TEST_BUNDLE_REQUEST_FAILED",
            decision_logic=str(exc),
        )
        raise HTTPException(
            status_code=500, detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        log_audit_event(
            agent_name="API.test_authoring",
            action="TEST_BUNDLE_REQUEST_FAILED",
            decision_logic=f"Unexpected error: {exc}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc

    log_audit_event(
        agent_name="API.test_authoring",
        action="TEST_BUNDLE_REQUEST_COMPLETED",
        decision_logic=(
            f"bundle_id={bundle['bundle_id']} "
            f"depth={bundle['depth']} "
            f"steps={len(bundle['steps'])}"
        ),
    )
    return bundle


@router.post("/generate-batch")
def generate_batch(body: GenerateBatchRequest) -> Dict[str, Any]:
    """
    Generate bundles for an entire requirement set.

    :param body: Request payload.
    :return: ``{"bundles": [...], "count": N}`` dict.
    :raises HTTPException: 500 on engine failure.
    :requirement: URS-22.8 - Support batch test bundle generation.
    """
    log_audit_event(
        agent_name="API.test_authoring",
        action="TEST_BUNDLE_BATCH_RECEIVED",
        decision_logic=(
            f"requirement_count={len(body.requirements)} "
            f"mode={body.mode} type={body.test_type}"
        ),
    )

    requirements = [r.model_dump() for r in body.requirements]
    risk_data = {
        k: v.model_dump() for k, v in body.risk_data.items()
    }

    try:
        bundles = _get_engine().generate_batch(
            requirements=requirements,
            risk_data=risk_data,
            mode=body.mode,
            test_type=body.test_type,
            project_name=body.project_name,
            persist=body.persist,
        )
    except Exception as exc:
        log_audit_event(
            agent_name="API.test_authoring",
            action="TEST_BUNDLE_BATCH_FAILED",
            decision_logic=str(exc),
        )
        raise HTTPException(
            status_code=500, detail=str(exc),
        ) from exc

    log_audit_event(
        agent_name="API.test_authoring",
        action="TEST_BUNDLE_BATCH_COMPLETED",
        decision_logic=f"Generated {len(bundles)} bundles",
    )
    return {"bundles": bundles, "count": len(bundles)}


@router.get("/bundles")
def list_bundles() -> Dict[str, Any]:
    """
    List all persisted test bundles by id.

    :return: ``{"bundles": [...ids...], "count": N}``.
    :requirement: URS-22.9 - Persist test bundles.
    """
    ids = _get_engine().list_bundles()
    return {"bundles": ids, "count": len(ids)}


@router.get("/bundle/{bundle_id}")
def get_bundle(bundle_id: str) -> Dict[str, Any]:
    """
    Load a persisted bundle by id.

    :param bundle_id: Bundle identifier.
    :return: Bundle dict.
    :raises HTTPException: 404 if bundle not found.
    :requirement: URS-22.9 - Persist test bundles.
    """
    bundle = _get_engine().load_bundle(bundle_id)
    if bundle is None:
        raise HTTPException(
            status_code=404,
            detail=f"Bundle {bundle_id!r} not found",
        )
    return bundle
