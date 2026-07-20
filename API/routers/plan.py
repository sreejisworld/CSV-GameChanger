"""
Plan Router — Data bridge between Streamlit and React.

POST /plan/save  — Streamlit Plan page pushes project metadata here.
GET  /plan       — React Plan page or useDataBridge polls this to
                   sync project name, GAMP category, and system
                   description back into Zustand.

Uses a module-level in-memory store (sufficient for single-user
local dev; replace with a DB-backed store for multi-tenant prod).

:requirement: URS-27.1 - System shall expose plan bridge endpoint
              for Streamlit → React data flow.
:requirement: URS-27.2 - System shall return plan metadata in a
              format compatible with the React Plan page.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["Plan Bridge"])

# ── In-memory store ─────────────────────────────────────────────────
_store: dict = {
    "plan":     {},
    "saved_at": None,
    "source":   None,
}


# ── Request / response models ────────────────────────────────────────
class SavePlanRequest(BaseModel):
    projectName:         Optional[str] = Field(
        None, max_length=200,
    )
    gampCategory:        Optional[str] = Field(
        None, max_length=60,
    )
    systemDescription:   Optional[str] = Field(
        None, max_length=20000,
    )
    projectScope:        Optional[str] = Field(
        None, max_length=20000,
    )
    regulatoryFrameworks: Optional[list] = None
    source:              Optional[str] = Field(
        "streamlit", max_length=60,
    )


class PlanResponse(BaseModel):
    plan:     dict
    saved_at: Optional[str]
    source:   Optional[str]


# ── Endpoints ────────────────────────────────────────────────────────
@router.post(
    "/plan/save",
    summary="Save plan metadata from Streamlit",
)
def save_plan(body: SavePlanRequest):
    """
    Accepts project metadata from the Streamlit Plan page and stores
    it so the React Plan page can sync it via useDataBridge.

    :requirement: URS-27.1 - System shall expose plan bridge endpoint
                  for Streamlit → React data flow.
    """
    payload = body.model_dump(exclude_none=True)
    payload.pop("source", None)

    _store["plan"]     = {**_store["plan"], **payload}
    _store["saved_at"] = datetime.now(timezone.utc).isoformat()
    _store["source"]   = body.source or "streamlit"

    return {
        "status":   "saved",
        "saved_at": _store["saved_at"],
        "fields":   list(payload.keys()),
    }


@router.get(
    "/plan",
    response_model=PlanResponse,
    summary="Get current plan metadata for React",
)
def get_plan():
    """
    Returns the latest plan metadata saved from Streamlit.
    useDataBridge polls this every 10 seconds.

    :requirement: URS-27.2 - System shall return plan metadata in a
                  format compatible with the React Plan page.
    """
    return PlanResponse(
        plan=_store["plan"],
        saved_at=_store["saved_at"],
        source=_store["source"],
    )


@router.delete(
    "/plan",
    summary="Clear saved plan metadata",
)
def clear_plan():
    """Resets the plan store.

    :requirement: URS-47.10 - Plan data lifecycle.
    """
    _store["plan"]     = {}
    _store["saved_at"] = None
    _store["source"]   = None
    return {"status": "cleared"}
