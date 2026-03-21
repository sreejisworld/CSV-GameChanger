"""
Requirements Router — Data bridge between Streamlit and React.

POST /requirements/save  — Streamlit pushes UR/FR list here after
                           generation; replaces the current store.
GET  /requirements       — React Risk page polls this to get the
                           latest requirements as a flat list.

Uses a module-level in-memory store (sufficient for single-user
local dev; replace with a DB-backed store for multi-tenant prod).

:requirement: URS-26.1 - System shall expose requirements bridge
              endpoint for Streamlit → React data flow.
:requirement: URS-26.2 - System shall return requirements in flat
              format compatible with the Risk Matrix page.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Requirements Bridge"])

# ── In-memory store ────────────────────────────────────────────────
_store: Dict[str, Any] = {
    "requirements": [],   # list of UR/FR dicts from Streamlit
    "saved_at":     None,
    "source":       None,
}


# ── Request / response models ──────────────────────────────────────
class SaveRequirementsRequest(BaseModel):
    requirements: List[Dict[str, Any]]
    source: Optional[str] = "streamlit"


class FlatRequirement(BaseModel):
    id:        str
    type:      str          # "UR" | "FR"
    statement: str
    parentId:  Optional[str] = None
    urs_id:    Optional[str] = None
    risk_assessment:    Optional[str] = None
    implementation_method: Optional[str] = None
    risk_level:         Optional[str] = None
    test_strategy:      Optional[str] = None


class RequirementsResponse(BaseModel):
    requirements: List[FlatRequirement]
    raw:          List[Dict[str, Any]]
    saved_at:     Optional[str]
    source:       Optional[str]
    count:        int


# ── Helper: flatten UR/FR dict → Risk.jsx rows ─────────────────────
def _flatten(ur_fr: Dict[str, Any]) -> List[FlatRequirement]:
    """
    Convert one UR/FR document from RequirementArchitect into the
    flat requirement rows consumed by the React Risk Matrix page.

    :requirement: URS-26.3 - System shall flatten UR/FR documents
                  into Risk Matrix compatible rows.
    """
    rows: List[FlatRequirement] = []
    ur = ur_fr.get("user_requirement", {})
    urs_id = ur_fr.get("urs_id", "")

    if ur:
        rows.append(FlatRequirement(
            id=ur.get("ur_id", "UR-?"),
            type="UR",
            statement=ur.get("statement", ""),
            urs_id=urs_id,
            risk_assessment=ur.get("risk_assessment"),
            implementation_method=ur.get("implementation_method"),
            risk_level=ur.get("risk_level"),
            test_strategy=ur.get("test_strategy"),
        ))

    for fr in ur_fr.get("functional_requirements", []):
        rows.append(FlatRequirement(
            id=fr.get("fr_id", "FR-?"),
            type="FR",
            statement=fr.get("statement", ""),
            parentId=fr.get("parent_ur_id") or ur.get("ur_id"),
            urs_id=urs_id,
        ))

    return rows


# ── Endpoints ──────────────────────────────────────────────────────
@router.post(
    "/requirements/save",
    summary="Save UR/FR requirements from Streamlit",
)
def save_requirements(body: SaveRequirementsRequest):
    """
    Accepts a list of UR/FR dicts from the Streamlit Validation
    Factory and stores them so the React Risk Matrix page can
    consume them.

    :requirement: URS-26.1 - System shall expose requirements bridge
                  endpoint for Streamlit → React data flow.
    """
    if not body.requirements:
        raise HTTPException(
            status_code=422,
            detail="requirements list must not be empty.",
        )

    _store["requirements"] = body.requirements
    _store["saved_at"] = datetime.now(timezone.utc).isoformat()
    _store["source"] = body.source or "streamlit"

    flat = []
    for ur_fr in body.requirements:
        flat.extend(_flatten(ur_fr))

    return {
        "status":     "saved",
        "saved_at":   _store["saved_at"],
        "count":      len(flat),
        "flat_count": len(flat),
    }


@router.get(
    "/requirements",
    response_model=RequirementsResponse,
    summary="Get current requirements for Risk Matrix",
)
def get_requirements():
    """
    Returns the latest saved requirements as both a flat list
    (for Risk.jsx) and the raw UR/FR dicts (for other consumers).

    :requirement: URS-26.2 - System shall return requirements in flat
                  format compatible with the Risk Matrix page.
    """
    flat: List[FlatRequirement] = []
    for ur_fr in _store["requirements"]:
        flat.extend(_flatten(ur_fr))

    return RequirementsResponse(
        requirements=flat,
        raw=_store["requirements"],
        saved_at=_store["saved_at"],
        source=_store["source"],
        count=len(flat),
    )


@router.delete(
    "/requirements",
    summary="Clear saved requirements (resets to seed data)",
)
def clear_requirements():
    """
    Clears the requirements store, causing the Risk Matrix to
    fall back to its built-in seed data.

    :requirement: URS-26.4 - System shall allow resetting the
                  requirements store to seed data.
    """
    _store["requirements"] = []
    _store["saved_at"] = None
    _store["source"] = None
    return {"status": "cleared"}
