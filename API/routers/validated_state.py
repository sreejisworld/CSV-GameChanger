"""
validated_state.py — Sprint 37 FastAPI router for the Validated
State Confidence Engine.

Endpoint
========
- POST /validated-state/assess
       Run the engine across the current project snapshot; return
       per-UR confidence scores + aggregate report + suggested
       actions for tier yellow/red URs.

The principle: AI proposes the score and the suggested actions;
the human QA team decides whether to act. The engine never modifies
records, never triggers revalidation. Bounded autonomy applied to
the validation-continuity loop.

:requirement: URS-37.7 - Expose Validated State assessment via JSON API.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from Agents.validated_state_engine import (   # noqa: E402
    ValidatedStateEngine,
    ValidatedStateError,
    InvalidProjectSnapshotError,
)


router = APIRouter(tags=["Validated State"])


class _RequirementInSnapshot(BaseModel):
    id:        str
    type:      str = Field(description="'UR' or 'FR'")
    statement: str = ""
    parentId:  Optional[str] = None


class StateAssessRequest(BaseModel):
    """POST /validated-state/assess request body."""
    project_name:   str
    requirements:   List[_RequirementInSnapshot] = Field(
        default_factory=list,
        description="UR + FR records to assess.",
    )
    risk_data:      Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    test_bundles:   Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    test_runs:      Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    defects:        Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
    )
    change_records: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    current_corpus_versions: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Optional · current ingested corpus versions keyed by "
            "framework name (e.g. {'GAMP 5': 'Rev 2', "
            "'21 CFR Part 11': '2024'}). Sprint 38 will detect "
            "drift against these."
        ),
    )
    drift_report:   Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Sprint 38 — optional RegulatoryDriftAgent scan report "
            "dict. When provided, the citation_drift signal slot "
            "in the scoring formula fires (−15 per affected "
            "citation, capped at −30). Caller is responsible for "
            "running POST /regulatory-drift/scan first and passing "
            "the returned report here."
        ),
    )
    user_id:        str = "demo"

    model_config = {
        "json_schema_extra": {
            "example": {
                "project_name": "LabCore LIMS v4.2 Migration",
                "requirements": [
                    {
                        "id":        "UR-1",
                        "type":      "UR",
                        "statement": "The system shall enforce e-signatures.",
                    },
                ],
                "risk_data":    {
                    "UR-1": {"riskLevel": "HIGH"},
                },
                "test_bundles": {
                    "UR-1": {"bundle_id": "TB-UR-1"},
                },
                "test_runs":    {},
                "defects":      {},
                "change_records": {},
                "user_id":      "demo",
            },
        },
    }


@router.post("/validated-state/assess")
def assess_validated_state(payload: StateAssessRequest) -> JSONResponse:
    """Score every UR in the project for current Validated State
    confidence and propose actions for any drifting URs.

    Every assessment writes a Logic Archive with inputs, per-UR
    scoring steps, and aggregate outputs — hash-linked to the audit
    trail so an inspector can re-derive any score from the
    snapshot inputs.

    :requirement: URS-37.7 - Validated State assessment via JSON API.
    """
    try:
        engine = ValidatedStateEngine()
        snap = {
            "project_name":  payload.project_name,
            "requirements":  [
                r.model_dump() for r in payload.requirements
            ],
            "risk_data":     payload.risk_data,
            "test_bundles":  payload.test_bundles,
            "test_runs":     payload.test_runs,
            "defects":       payload.defects,
            "change_records": payload.change_records,
            "current_corpus_versions":
                payload.current_corpus_versions,
        }
        report = engine.assess(
            project_snapshot=snap,
            user_id=payload.user_id,
            drift_report=payload.drift_report,
        )
        return JSONResponse(report.to_dict())

    except InvalidProjectSnapshotError as e:
        # Audit triplet logged inside the engine
        raise HTTPException(
            status_code=400,
            detail=f"Invalid project snapshot: {e}",
        )
    except ValidatedStateError as e:
        raise HTTPException(
            status_code=500,
            detail=f"State assessment failed: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected VSE error: {e}",
        )
