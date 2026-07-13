"""
Requirements Router — Data bridge between Streamlit and React,
plus the workshop-driven URS generation endpoint feeding the
React Validation Factory's Workshop intake form (Sprint 17.4).

POST /requirements/save     — Streamlit pushes UR/FR list here
                              after generation; replaces store.
GET  /requirements          — React polls this to get the latest
                              requirements as a flat list.
POST /requirements/generate — React Workshop form posts free-text
                              system / workshop / workflow inputs;
                              returns flat UR/FR rows + 3 Cs meta.

Uses a module-level in-memory store (sufficient for single-user
local dev; replace with a DB-backed store for multi-tenant prod).

:requirement: URS-26.1 - System shall expose requirements bridge
              endpoint for Streamlit → React data flow.
:requirement: URS-26.2 - System shall return requirements in flat
              format compatible with the Risk Matrix page.
:requirement: URS-26.5 - System shall generate UR/FR drafts from
              workshop intake (system description, workshop notes,
              diagram URL, workflow process) using the existing
              RequirementArchitect transform pipeline.
"""
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from Agents.integrity_manager import log_audit_event
from Agents.requirement_architect import (
    RegulatoryContextNotFoundError,
    RequirementArchitect,
)
from Agents.smart_requirements_engine import (
    SMARTEngineError,
    SMARTRequirementsEngine,
)


# ── Error codes ────────────────────────────────────────────────────
class RequirementsBridgeError(Exception):
    """Base exception for the requirements bridge router."""
    error_code = "CSV-026"


class WorkshopGenerationError(RequirementsBridgeError):
    """Error code: CSV-027 - Workshop URS/UR/FR generation failed."""
    error_code = "CSV-027"


class SmartRefinementError(RequirementsBridgeError):
    """Error code: CSV-028 - SMART refinement failed."""
    error_code = "CSV-028"


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

    Note — preserves the architect's local IDs. Most callers should
    instead use `_flatten_batch()` which guarantees globally-unique
    IDs across multi-URS batches.

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


def _flatten_batch(
    ur_frs: List[Dict[str, Any]],
) -> List[FlatRequirement]:
    """
    Flatten a list of UR/FR documents into Risk Matrix rows with
    globally-unique IDs.  `RequirementArchitect.transform_urs_to_ur_fr`
    independently emits "UR-1" / "FR-1" for every URS, so naive
    flattening across a multi-URS batch produces collisions that
    break React keys and the per-UR meta lookup.

    :requirement: URS-26.3 - System shall flatten UR/FR documents
                  into Risk Matrix compatible rows.
    """
    rows: List[FlatRequirement] = []
    ur_counter = 0
    fr_counter = 0
    for ur_fr in ur_frs:
        ur = ur_fr.get("user_requirement", {})
        urs_id = ur_fr.get("urs_id", "")
        new_ur_id: Optional[str] = None
        if ur:
            ur_counter += 1
            new_ur_id = f"UR-{ur_counter}"
            rows.append(FlatRequirement(
                id=new_ur_id,
                type="UR",
                statement=ur.get("statement", ""),
                urs_id=urs_id,
                risk_assessment=ur.get("risk_assessment"),
                implementation_method=ur.get("implementation_method"),
                risk_level=ur.get("risk_level"),
                test_strategy=ur.get("test_strategy"),
            ))
        for fr in ur_fr.get("functional_requirements", []):
            fr_counter += 1
            rows.append(FlatRequirement(
                id=f"FR-{fr_counter}",
                type="FR",
                statement=fr.get("statement", ""),
                parentId=new_ur_id,
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

    flat = _flatten_batch(body.requirements)

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
    flat = _flatten_batch(_store["requirements"])

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


# ── Workshop intake (Sprint 17.4) ──────────────────────────────────
class GenerateRequirementsRequest(BaseModel):
    """Workshop-driven URS/UR/FR generation request body.

    All fields are optional except `workflow_process` /
    `system_description` — at least one must yield parseable lines
    or the endpoint returns 422.
    """
    project_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Display name for the workshop project.",
    )
    system_description: Optional[str] = Field(
        default=None,
        max_length=20000,
        description=(
            "Free-text description of the system being validated."
        ),
    )
    workshop_notes: Optional[str] = Field(
        default=None,
        max_length=20000,
        description=(
            "Stakeholder workshop notes, process owner inputs, "
            "etc. Becomes part of additional_context."
        ),
    )
    lucidchart_url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Diagram URL (Lucid, Visio, draw.io, etc.).",
    )
    lucidchart_content: Optional[str] = Field(
        default=None,
        max_length=100000,
        description="Optional decoded text content from a diagram.",
    )
    workflow_process: Optional[str] = Field(
        default=None,
        max_length=20000,
        description=(
            "Bulleted/numbered list of workflow steps to translate "
            "into UR/FR rows."
        ),
    )
    role: Optional[str] = Field(
        default="User",
        max_length=100,
        description="UR persona (e.g. Lab Technician).",
    )
    risk_assessment: Optional[str] = Field(
        default="GxP Indirect",
        max_length=30,
        description=(
            "GxP Direct | GxP Indirect | GxP None — drives the "
            "UR/FR risk matrix."
        ),
    )
    implementation_method: Optional[str] = Field(
        default="Configured",
        max_length=30,
        description="Out of the Box | Configured | Custom.",
    )
    min_score: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Pinecone similarity floor for URS generation.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "project_name": "Sample Tracking System",
                "system_description": (
                    "LabCore LIMS v4.2 — cloud-hosted sample "
                    "tracking platform."
                ),
                "workshop_notes": (
                    "Chain-of-custody is safety-critical. "
                    "Disposal must be witnessed."
                ),
                "lucidchart_url": "https://lucid.app/example",
                "workflow_process": (
                    "- Register sample on receipt\n"
                    "- Track sample location\n"
                    "- Record disposal with witness"
                ),
                "role": "Lab Technician",
                "risk_assessment": "GxP Indirect",
                "implementation_method": "Configured",
            }
        }
    }


class GeneratedMeta3Cs(BaseModel):
    """Per-UR 3 Cs split (capability / condition / constraint).

    Returned alongside the flat UR rows so the React Workshop form
    can pre-fill the inline editor.
    """
    capability: str = ""
    condition: str = ""
    constraint: str = ""
    requirement_type: str = "Functional"
    stakeholder: str = "Lab"


class GenerateRequirementsResponse(BaseModel):
    """Workshop generation response."""
    requirements: List[FlatRequirement]
    raw: List[Dict[str, Any]]
    meta: Dict[str, GeneratedMeta3Cs]
    skipped: List[Dict[str, str]]
    project_name: Optional[str] = None
    generated_at: str
    count: int


_BULLET_RE = re.compile(r"^[\-\*\u2022]\s*")
_NUMBERED_RE = re.compile(r"^\d+[.)]\s*")
_CONDITION_HINTS = (
    "when ", "if ", "while ", "during ", "after ", "before ",
    "given ", "for every ", "for each ", "on receipt", "upon ",
)
_CONSTRAINT_HINTS = (
    " per ", " in accordance with ", " 21 cfr ", " annex 11",
    " gamp ", " iso ", " sop ", " within ", " ≤ ", " ≥ ",
    " <= ", " >= ", " ± ", " <", " >",
)


def _parse_lines(text: Optional[str]) -> List[str]:
    """Split free text into clean requirement-line strings.

    Drops bullets / numbering / very short lines (likely headers).
    Mirrors `scripts/draft_urs.py:parse_requirements()`.
    """
    if not text:
        return []
    out: List[str] = []
    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = _BULLET_RE.sub("", line)
        line = _NUMBERED_RE.sub("", line)
        if len(line) < 10:
            continue
        out.append(line)
    return out


def _split_3cs(statement: str) -> Dict[str, str]:
    """Best-effort 3 Cs split for the React inline editor.

    Heuristic only — the user is expected to refine each cell.
    Looks for condition keywords (when / if / while / per) and
    constraint hints (regulation citations, numeric tolerances).

    :return: dict with capability, condition, constraint keys.
    """
    if not statement:
        return {"capability": "", "condition": "", "constraint": ""}

    text = statement.strip()
    lower = " " + text.lower() + " "
    capability = text
    condition = ""
    constraint = ""

    # Pull off a constraint clause (regulation / measurable
    # threshold) — split on the first hint occurrence.
    for hint in _CONSTRAINT_HINTS:
        idx = lower.find(hint)
        if idx > 0:
            split_at = idx - 1  # account for leading space pad
            constraint = text[split_at:].lstrip(", ;.").strip()
            capability = text[:split_at].rstrip(", ;.").strip()
            lower = " " + capability.lower() + " "
            break

    # Pull off a condition clause from whatever's left as the
    # capability — splits at "when / if / while / per …".
    for hint in _CONDITION_HINTS:
        idx = lower.find(" " + hint)
        if idx > 0:
            split_at = idx
            condition = capability[split_at:].strip(", ;.").strip()
            capability = capability[:split_at].rstrip(", ;.").strip()
            break

    # Strip a leading "The system shall " from capability so the
    # editor cell holds the action verb only.
    capability = re.sub(
        r"^[Tt]he system shall\s+", "", capability,
    ).strip()

    return {
        "capability": capability,
        "condition": condition,
        "constraint": constraint,
    }


def _classify_type(statement: str) -> str:
    """Route obvious non-functional markers to Non-Functional.

    Looks for performance / security / availability keywords.
    """
    nf_markers = (
        "performance", "availability", "uptime", "latency",
        "throughput", "scalab", "security", "encryption",
        "backup", "recovery", "rto", "rpo", "audit trail",
        "21 cfr part 11", "annex 11", "data integrity",
    )
    lower = (statement or "").lower()
    return (
        "Non-Functional"
        if any(m in lower for m in nf_markers)
        else "Functional"
    )


@router.post(
    "/requirements/generate",
    response_model=GenerateRequirementsResponse,
    summary=(
        "Generate UR/FR drafts from workshop intake "
        "(Sprint 17.4)"
    ),
)
def generate_from_workshop(body: GenerateRequirementsRequest):
    """Workshop-driven URS → UR/FR generation.

    Accepts the four React Workshop inputs (system description,
    workshop notes, diagram URL/content, workflow process), parses
    each non-empty section into raw requirement lines, runs each
    line through `RequirementArchitect.generate_urs()` then
    `transform_urs_to_ur_fr()`, and returns flat UR/FR rows ready
    for the React Risk Matrix plus per-UR 3 Cs metadata for the
    inline editor.

    Lines that fail GAMP 5 context lookup are skipped — they go
    into `skipped` with a reason — rather than failing the whole
    batch, so the user always gets at least a partial draft.

    :requirement: URS-26.5 - System shall generate UR/FR drafts
                  from workshop intake.
    """
    lines = (
        _parse_lines(body.workflow_process)
        + _parse_lines(body.system_description)
    )

    log_audit_event(
        agent_name="RequirementsBridge",
        action="WORKSHOP_GENERATE_RECEIVED",
        decision_logic=(
            f"Workshop intake received: project={body.project_name!r}, "
            f"line_count={len(lines)}, "
            f"role={body.role!r}, "
            f"risk_assessment={body.risk_assessment!r}, "
            f"implementation_method={body.implementation_method!r}"
        ),
        compliance_impact="Audit Trail",
    )

    if not lines:
        raise HTTPException(
            status_code=422,
            detail=(
                "No parseable requirement lines found. Provide a "
                "workflow_process or system_description with one "
                "requirement per line."
            ),
        )

    additional_context: Dict[str, str] = {}
    if body.system_description:
        additional_context["system_description"] = body.system_description
    if body.workshop_notes:
        additional_context["workshop_notes"] = body.workshop_notes
    if body.lucidchart_url:
        additional_context["lucidchart_url"] = body.lucidchart_url
    if body.lucidchart_content:
        additional_context["lucidchart_content"] = body.lucidchart_content

    raw_ur_frs: List[Dict[str, Any]] = []
    skipped: List[Dict[str, str]] = []

    try:
        architect = RequirementArchitect()
    except Exception as exc:
        log_audit_event(
            agent_name="RequirementsBridge",
            action="WORKSHOP_GENERATE_FAILED",
            decision_logic=(
                f"Architect init failed: {type(exc).__name__}: "
                f"{exc} [CSV-027]"
            ),
            compliance_impact="Audit Trail",
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "RequirementArchitect unavailable — confirm "
                "OPENAI_API_KEY and PINECONE_API_KEY are set."
            ),
        ) from exc

    for raw_line in lines:
        try:
            urs = architect.generate_urs(
                requirement=raw_line,
                min_score=body.min_score,
            )
        except RegulatoryContextNotFoundError as exc:
            skipped.append({
                "line": raw_line,
                "reason": f"No GAMP 5 context found: {exc}",
            })
            continue
        except Exception as exc:
            # Internal error details stay server-side only.
            log_audit_event(
                agent_name="RequirementsBridge",
                action="WORKSHOP_GENERATE_FAILED",
                decision_logic=(
                    f"generate_urs failed for line "
                    f"{raw_line[:80]!r}: "
                    f"{type(exc).__name__}: {exc} [CSV-027]"
                ),
                compliance_impact="Audit Trail",
            )
            skipped.append({
                "line": raw_line,
                "reason": (
                    "[CSV-027] URS generation failed for this "
                    "line. See server audit log for details."
                ),
            })
            continue

        try:
            ur_fr = architect.transform_urs_to_ur_fr(
                urs=urs,
                role=body.role or "User",
                category="General",
                risk_assessment=body.risk_assessment or "GxP Indirect",
                implementation_method=(
                    body.implementation_method or "Configured"
                ),
                additional_context=additional_context or None,
            )
        except Exception as exc:
            log_audit_event(
                agent_name="RequirementsBridge",
                action="WORKSHOP_GENERATE_FAILED",
                decision_logic=(
                    f"transform_urs_to_ur_fr failed for line "
                    f"{raw_line[:80]!r}: "
                    f"{type(exc).__name__}: {exc} [CSV-027]"
                ),
                compliance_impact="Audit Trail",
            )
            skipped.append({
                "line": raw_line,
                "reason": (
                    "[CSV-027] UR/FR transformation failed for "
                    "this line. See server audit log for details."
                ),
            })
            continue

        raw_ur_frs.append(ur_fr)

    if not raw_ur_frs:
        log_audit_event(
            agent_name="RequirementsBridge",
            action="WORKSHOP_GENERATE_FAILED",
            decision_logic=(
                f"All {len(lines)} lines skipped — no UR/FR "
                f"drafts generated [CSV-027]"
            ),
            compliance_impact="Audit Trail",
        )
        raise HTTPException(
            status_code=422,
            detail={
                "message": (
                    "No requirement lines could be transformed "
                    "into UR/FR drafts. See `skipped` for reasons."
                ),
                "skipped": skipped,
            },
        )

    # Replace the in-memory store so the React Risk page picks up
    # the generated drafts on its next poll, same as the Streamlit
    # save flow.
    saved_at = datetime.now(timezone.utc).isoformat()
    _store["requirements"] = raw_ur_frs
    _store["saved_at"] = saved_at
    _store["source"] = (
        f"workshop:{body.project_name}"
        if body.project_name else "workshop"
    )

    # Flatten with globally-unique IDs (shared with GET /requirements
    # so the React store sees the same IDs whichever endpoint
    # populated it).
    flat = _flatten_batch(raw_ur_frs)

    # Build the per-UR 3 Cs metadata, keyed by the same renumbered
    # UR IDs the flattener just produced. Walk the batch in lockstep
    # — each ur_fr that has a user_requirement consumes one UR id.
    meta: Dict[str, GeneratedMeta3Cs] = {}
    ur_counter = 0
    for ur_fr in raw_ur_frs:
        ur = ur_fr.get("user_requirement", {})
        if not ur:
            continue
        ur_counter += 1
        ur_id = f"UR-{ur_counter}"
        # Prefer the clean "The system shall ..." summary for the
        # 3 Cs split — the user-story-form `statement` from the
        # architect is too noisy to chunk reliably.
        summary_for_split = (
            ur_fr.get("requirement_summary")
            or ur.get("statement", "")
        )
        split = _split_3cs(summary_for_split)
        meta[ur_id] = GeneratedMeta3Cs(
            capability=split["capability"],
            condition=split["condition"],
            constraint=split["constraint"],
            requirement_type=_classify_type(summary_for_split),
            stakeholder="Lab",
        )

    log_audit_event(
        agent_name="RequirementsBridge",
        action="WORKSHOP_GENERATE_COMPLETED",
        decision_logic=(
            f"Generated {len(raw_ur_frs)} UR/FR drafts "
            f"({len(flat)} flat rows) from {len(lines)} lines, "
            f"skipped {len(skipped)}"
        ),
        compliance_impact="Regulatory Compliance",
    )

    return GenerateRequirementsResponse(
        requirements=flat,
        raw=raw_ur_frs,
        meta=meta,
        skipped=skipped,
        project_name=body.project_name,
        generated_at=saved_at,
        count=len(flat),
    )


# ── SMART refinement (Sprint 17.7) ─────────────────────────────────
class RefineSmartRequest(BaseModel):
    """Single-statement SMART refinement request body.

    Wraps the multi-section `SMARTRequirementsEngine.refine_to_smart`
    so the React AI Sidekick can call it per row on demand.
    """
    requirement: str = Field(
        ...,
        min_length=3,
        max_length=4000,
        description="Raw requirement text to refine to SMART format.",
    )
    requirement_id: Optional[str] = Field(
        default=None,
        max_length=60,
        description=(
            "Originating row id (UR-1 / FR-2 / etc.) — echoed back "
            "so the React store can patch the right row."
        ),
    )
    category: Optional[str] = Field(
        default="general",
        max_length=60,
        description=(
            "GxP category bucket (general | functional | data | "
            "security | etc.). Drives the acceptance-criteria template."
        ),
    )
    system_description: Optional[str] = Field(
        default="",
        max_length=20000,
        description=(
            "Optional system context to pass to the engine for richer "
            "rewrites (only used when LLM mode is available)."
        ),
    )
    has_ai_components: Optional[bool] = Field(
        default=False,
        description=(
            "Set true if the requirement covers an ML/LLM/AI feature — "
            "triggers the FDA/EMA 2026 AI Guidance flag."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "requirement": (
                    "system shall be 21 CFR Part 11 compliant and "
                    "user-friendly"
                ),
                "requirement_id": "UR-1",
                "category": "general",
                "system_description": (
                    "LabCore LIMS v4.2 — cloud-hosted lab system."
                ),
                "has_ai_components": False,
            }
        }
    }


class RefineSmartResponse(BaseModel):
    """SMART refinement response (single requirement)."""
    requirement_id: Optional[str]
    original: str
    smart_text: str
    category: str
    risk_level: str          # High | Medium | Low
    fda_ema_flags: List[str]
    acceptance_criteria: Dict[str, List[str]]
    negative_test_scenario: Optional[str] = None
    engine_mode: str         # "llm" | "deterministic"
    refined_at: str


@router.post(
    "/requirements/refine-smart",
    response_model=RefineSmartResponse,
    summary=(
        "Refine a single requirement to SMART format "
        "(Sprint 17.7)"
    ),
)
def refine_to_smart(body: RefineSmartRequest):
    """Single-statement SMART refinement for the React AI Sidekick.

    Wraps `SMARTRequirementsEngine.refine_to_smart` with a single-item
    section so the per-row "✨ Refine with SMART" button can call it
    on demand without triggering the full multi-section batch flow.

    Falls back to the engine's deterministic path automatically when
    LLM mode is unavailable — the response shape stays identical.

    :requirement: URS-27.1 - System shall expose single-statement SMART
                  refinement endpoint for the AI Sidekick rail.
    :requirement: URS-27.2 - System shall return refined text plus
                  FDA/EMA flags and negative test scenarios.
    """
    log_audit_event(
        agent_name="RequirementsBridge",
        action="SMART_REFINE_RECEIVED",
        decision_logic=(
            f"SMART refinement requested for "
            f"requirement_id={body.requirement_id!r}, "
            f"category={body.category!r}, "
            f"has_ai_components={body.has_ai_components}, "
            f"length={len(body.requirement)}"
        ),
        compliance_impact="Audit Trail",
    )

    try:
        engine = SMARTRequirementsEngine()
    except SMARTEngineError as exc:
        log_audit_event(
            agent_name="RequirementsBridge",
            action="SMART_REFINE_FAILED",
            decision_logic=(
                f"SMART engine init failed: {type(exc).__name__}: "
                f"{exc} [CSV-028]"
            ),
            compliance_impact="Audit Trail",
        )
        raise HTTPException(
            status_code=503,
            detail="SMART Requirements Engine unavailable.",
        ) from exc

    category = (body.category or "general").strip() or "general"

    try:
        result = engine.refine_to_smart(
            sections={category: [body.requirement]},
            system_description=body.system_description or "",
            has_ai_components=bool(body.has_ai_components),
        )
    except Exception as exc:
        log_audit_event(
            agent_name="RequirementsBridge",
            action="SMART_REFINE_FAILED",
            decision_logic=(
                f"refine_to_smart raised: {type(exc).__name__}: "
                f"{exc} [CSV-028]"
            ),
            compliance_impact="Audit Trail",
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-028] SMART refinement failed. "
                "See server audit log for details."
            ),
        ) from exc

    if not result.requirements:
        raise HTTPException(
            status_code=422,
            detail=(
                "Engine returned no SMART requirement — input may be "
                "empty after stripping."
            ),
        )

    refined = result.requirements[0]
    refined_at = datetime.now(timezone.utc).isoformat()
    engine_mode = "llm" if engine._llm_available else "deterministic"

    log_audit_event(
        agent_name="RequirementsBridge",
        action="SMART_REFINE_COMPLETED",
        decision_logic=(
            f"SMART refinement completed for "
            f"requirement_id={body.requirement_id!r}: "
            f"risk={refined.risk_level}, "
            f"fda_ema_flags={refined.fda_ema_flags}, "
            f"engine_mode={engine_mode}"
        ),
        compliance_impact="Regulatory Compliance",
    )

    return RefineSmartResponse(
        requirement_id=body.requirement_id,
        original=refined.original,
        smart_text=refined.smart_text,
        category=refined.category,
        risk_level=refined.risk_level,
        fda_ema_flags=refined.fda_ema_flags,
        acceptance_criteria=refined.acceptance_criteria,
        negative_test_scenario=refined.negative_test_scenario,
        engine_mode=engine_mode,
        refined_at=refined_at,
    )
