"""
Audit trail read-only router.

:requirement: URS-2.1 - System shall maintain 21 CFR Part 11 compliant audit trail.
:requirement: URS-27.1 - System shall expose audit rows via JSON API for the
              React Audit Trail Viewer.
:requirement: URS-27.2 - System shall expose per-row logic-archive JSON
              for AI reasoning drill-down.
:requirement: URS-27.3 - System shall expose lifecycle timeline data
              (Mermaid source) for an audit slice.
:requirement: URS-27.4 - System shall produce a signed audit-trail
              export PDF from a filtered slice.

Read-only: the CSV is append-only and is never modified by this router.
All write paths must go through :pyfunc:`Agents.integrity_manager.log_audit_event`.
"""
from __future__ import annotations

import csv
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

_logger = logging.getLogger("evolv.audit")

# Reasoning-hash prefixes are hex only — reject anything else
# before it reaches the filesystem glob (path/glob injection).
_HASH_PREFIX_RE = re.compile(r"^[0-9a-f]{8,64}$")

router = APIRouter(tags=["Audit"])

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_AUDIT_CSV = _PROJECT_ROOT / "output" / "audit_trail.csv"
_ARCHIVE_DIR = _PROJECT_ROOT / "output" / "logic_archives"

# Impact -> severity bucket for colour-coding in the UI
_IMPACT_SEVERITY = {
    "Compliance Exception":   "error",
    "Regulatory Compliance":  "success",
    "Validation Evidence":    "success",
    "GxP Documentation":      "info",
    "Operational":            "info",
    "Key Management":         "warning",
    "Monitoring":             "info",
    "Release":                "success",
    "Electronic Signature":   "success",
    "Release Authorization":  "success",
    "Patient Safety":         "warning",
    "Change Control":         "info",
    "Data Integrity":         "info",
    "Reference Query":        "info",
}

# Lifecycle phase classification by action prefix / keyword.
# Used by the Mermaid timeline endpoint to bucket events into V-model phases.
_PHASE_BY_ACTION = {
    # Plan
    "VALIDATION_PLAN_EXPORT":         "Plan",
    "PLAN_":                          "Plan",
    # Requirements
    "URS_GENERATED":                  "Requirements",
    "URS_TRANSFORMED_TO_UR_FR":       "Requirements",
    "SMART_REQUIREMENTS_REFINED":     "Requirements",
    "SMART_REFINE":                   "Requirements",
    "WORKSHOP_GENERATE":              "Requirements",
    "INTELLIGENCE_GENERATED":         "Requirements",
    "REQUIREMENT_":                   "Requirements",
    # Risk
    "RISK_ASSESSMENT_COMPLETED":      "Risk",
    "GAP_ANALYSIS_COMPLETED":         "Risk",
    # Design
    "TEST_BUNDLE_GENERATED":          "Design",
    "DESIGN_SPEC_EXPORT":             "Design",
    "CSA_TEST_SCRIPT_GENERATED":      "Design",
    "CSA_TEST_CHARTER_GENERATED":     "Design",
    "CSA_TEST_BATCH_GENERATED":       "Design",
    "TEST_SCRIPT_GENERATED":          "Design",
    "TEST_BATCH_GENERATED":           "Design",
    "TEST_BUNDLE_REQUEST":            "Design",
    # Verify
    "TEST_RUN_SIGNED_OFF":            "Verify",
    "TEST_STEP_":                     "Verify",
    "DEFECT_":                        "Verify",
    "QA_REVIEW_":                     "Verify",
    # Release
    "RELEASE_APPROVAL_SIGNED":        "Release",
    "RELEASE_APPROVED":               "Release",
    "VALIDATION_SUMMARY_REPORT":      "Release",
    "VALIDATION_SUMMARY_EXPORT":      "Release",
    "AUDIT_EXPORT":                   "Monitor",
    "TRACEABILITY_EXPORT":            "Release",
    # Monitor
    "CHANGE_REQUEST_":                "Monitor",
    "DEVIATION_":                     "Monitor",
    # Cross-cutting
    "URS_VERIFIED":                   "Verify",
    "COMPLIANCE_EXCEPTION":           "Verify",
    "DOCUMENT_INGESTED":              "Requirements",
    "DOCUMENT_SIGN_OFF":              "Release",
}


def _phase_of(action: str) -> str:
    """Bucket an action constant into a V-model phase label."""
    if not action:
        return "Other"
    for prefix, phase in _PHASE_BY_ACTION.items():
        if action.startswith(prefix):
            return phase
    return "Other"


def _read_all_rows() -> List[Dict[str, Any]]:
    """Read every row from the audit CSV, oldest first.

    :requirement: URS-27.1
    """
    if not _AUDIT_CSV.exists():
        return []
    with _AUDIT_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


# ── Models ──────────────────────────────────────────────────────────


class AuditRow(BaseModel):
    timestamp:  str
    user_id:    str
    agent:      str
    action:     str
    logic:      str
    impact:     str
    hash:       str
    severity:   str   # error | warning | success | info


class TimelineEvent(BaseModel):
    """A single event positioned in lifecycle phase + time."""
    timestamp: str
    phase:     str
    agent:     str
    action:    str
    logic:     str
    hash:      str


class TimelineResponse(BaseModel):
    events:   List[TimelineEvent]
    mermaid:  str = Field(
        ...,
        description="Mermaid.js journey-diagram source for this slice.",
    )
    phase_counts: Dict[str, int]
    total:    int


class AuditExportRequest(BaseModel):
    """Request body for filtered slice → signed PDF export."""
    rows: List[Dict[str, Any]] = Field(
        ...,
        max_length=10000,
        description="The filtered rows the user wants in the PDF.",
    )
    project_name: str = Field(
        default="Untitled Project",
        max_length=200,
        description="Project / system name for the cover page.",
    )
    signer_name:  str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Approver full name for Manifestation of Signature.",
    )
    meaning:      str = Field(
        default="Audit Trail Inspection Export",
        max_length=200,
        description="Meaning of the electronic signature.",
    )
    filter_summary: str = Field(
        default="",
        max_length=500,
        description="Human-readable summary of the active filters.",
    )


# ── Endpoints ───────────────────────────────────────────────────────


@router.get("/audit/recent", response_model=List[AuditRow])
def get_recent_audit(
    limit: int = Query(default=50, ge=1, le=500),
    agent: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
):
    """Return the most recent *limit* audit trail rows, newest first.

    Optional filters:
    - ``agent``    -- filter by Agent_Name (case-insensitive substring)
    - ``severity`` -- filter by severity bucket (error/warning/success/info)

    :requirement: URS-2.1
    :requirement: URS-27.1
    """
    rows: List[AuditRow] = []
    for row in _read_all_rows():
        impact   = row.get("Compliance_Impact", "Operational")
        sev      = _IMPACT_SEVERITY.get(impact, "info")
        agent_nm = row.get("Agent_Name", "")

        if agent and agent.lower() not in agent_nm.lower():
            continue
        if severity and sev != severity:
            continue

        rows.append(AuditRow(
            timestamp=row.get("Timestamp", ""),
            user_id=row.get("User_ID", "SYSTEM"),
            agent=agent_nm,
            action=row.get("Action_Performed", ""),
            logic=row.get("Decision_Logic", ""),
            impact=impact,
            hash=row.get("Reasoning_Hash", "")[:12],
            severity=sev,
        ))

    return rows[-limit:][::-1]


@router.get("/audit/all", response_model=List[Dict[str, Any]])
def get_all_audit():
    """Return every audit row (newest first), full untruncated fields.

    Used by the React Audit Trail Viewer for client-side sort + filter.
    Each row carries an extra ``severity`` and ``phase`` field computed
    server-side so the UI never has to repeat the bucket mapping.

    :requirement: URS-27.1
    """
    raw = _read_all_rows()
    enriched: List[Dict[str, Any]] = []
    for row in raw:
        impact = row.get("Compliance_Impact", "Operational")
        action = row.get("Action_Performed", "")
        enriched.append({
            "timestamp":         row.get("Timestamp", ""),
            "user_id":           row.get("User_ID", "SYSTEM"),
            "agent_name":        row.get("Agent_Name", ""),
            "action":            action,
            "decision_logic":    row.get("Decision_Logic", ""),
            "compliance_impact": impact,
            "reasoning_hash":    row.get("Reasoning_Hash", ""),
            "severity":          _IMPACT_SEVERITY.get(impact, "info"),
            "phase":             _phase_of(action),
        })
    enriched.reverse()  # newest first
    return enriched


@router.get("/audit/archive/{hash_prefix}")
def get_logic_archive(hash_prefix: str):
    """Return the matching logic_archive JSON for a reasoning hash.

    Logic-archive filenames follow the pattern::

        .{ACTION}_{YYYYMMDDTHHMMSSZ}_{hash[:8]}.json

    The ``hash_prefix`` may be any prefix of the SHA-256 reasoning hash
    of length >= 8 (the same prefix embedded in the filename).
    Returns ``404`` if no matching archive is found.

    :requirement: URS-27.2
    """
    prefix = (hash_prefix or "").strip().lower()
    if not _HASH_PREFIX_RE.match(prefix):
        raise HTTPException(
            status_code=400,
            detail=(
                "hash_prefix must be 8-64 hexadecimal "
                "characters."
            ),
        )

    short = prefix[:8]
    if not _ARCHIVE_DIR.exists():
        raise HTTPException(
            status_code=404,
            detail="No logic archives directory on disk yet.",
        )

    # Filenames embed the short hash before .json
    matches = sorted(_ARCHIVE_DIR.glob(f"*_{short}.json"))
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"No logic archive found for hash prefix '{short}'.",
        )

    # Pick the most recent if multiple share an 8-char prefix collision
    chosen = matches[-1]
    try:
        payload = json.loads(chosen.read_text(encoding="utf-8"))
    except Exception as exc:
        _logger.exception(
            "[CSV-003] Could not parse logic archive %s: %s",
            chosen.name, exc,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Logic archive could not be parsed. "
                "See server log for details."
            ),
        )

    return {
        "archive_filename": chosen.name,
        "matched_prefix":   short,
        "archive":          payload,
    }


@router.get("/audit/timeline", response_model=TimelineResponse)
def get_audit_timeline(
    since: Optional[str] = Query(
        default=None,
        description="ISO-8601 lower bound (inclusive). E.g. 2026-04-01T00:00:00Z",
    ),
    until: Optional[str] = Query(
        default=None,
        description="ISO-8601 upper bound (inclusive).",
    ),
    agent: Optional[str] = Query(default=None),
    action_prefix: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
):
    """Return a Mermaid.js journey diagram + raw events for the audit slice.

    Bucketing rule: each action is bucketed into one of
    Plan / Requirements / Risk / Design / Verify / Release / Monitor / Other
    via the ``_PHASE_BY_ACTION`` map. The journey shows phase counts in
    chronological order so a reviewer can see the system's lifecycle path.

    :requirement: URS-27.3
    """
    events: List[TimelineEvent] = []

    def _in_window(ts: str) -> bool:
        if not ts:
            return False
        try:
            t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return False
        if since:
            try:
                lo = datetime.fromisoformat(
                    since.replace("Z", "+00:00")
                )
                if t < lo:
                    return False
            except ValueError:
                pass
        if until:
            try:
                hi = datetime.fromisoformat(
                    until.replace("Z", "+00:00")
                )
                if t > hi:
                    return False
            except ValueError:
                pass
        return True

    for row in _read_all_rows():
        ts     = row.get("Timestamp", "")
        action = row.get("Action_Performed", "")
        ag     = row.get("Agent_Name", "")
        if not _in_window(ts):
            continue
        if agent and agent.lower() not in ag.lower():
            continue
        if action_prefix and not action.startswith(action_prefix):
            continue
        events.append(TimelineEvent(
            timestamp=ts,
            phase=_phase_of(action),
            agent=ag,
            action=action,
            logic=row.get("Decision_Logic", ""),
            hash=row.get("Reasoning_Hash", "")[:12],
        ))

    # Truncate to most-recent ``limit`` events (chronological list ->
    # take the tail). phase_counts and Mermaid are computed AFTER
    # truncation so the visualisation always matches the events the
    # caller actually receives.
    if len(events) > limit:
        events = events[-limit:]
    phase_counts: Dict[str, int] = {}
    for ev in events:
        phase_counts[ev.phase] = phase_counts.get(ev.phase, 0) + 1

    # Build Mermaid journey diagram. Score = # events in that phase
    # (clamped to 5 for journey-diagram readability; 5 is "great").
    phase_order = [
        "Plan", "Requirements", "Risk", "Design",
        "Verify", "Release", "Monitor", "Other",
    ]
    journey_lines = [
        "journey",
        "  title  EVOLV Lifecycle Audit Journey",
        "  section Validation Lifecycle",
    ]
    for ph in phase_order:
        cnt = phase_counts.get(ph, 0)
        if cnt == 0:
            continue
        score = min(5, max(1, cnt))
        # Mermaid journey: "Phase: score: Actor"
        journey_lines.append(
            f"    {ph} ({cnt} events): {score}: System"
        )
    mermaid = "\n".join(journey_lines)

    return TimelineResponse(
        events=events,
        mermaid=mermaid,
        phase_counts=phase_counts,
        total=len(events),
    )


@router.post("/audit/export-pdf")
def export_audit_slice_pdf(body: AuditExportRequest):
    """Render a filtered slice of the audit trail as a signed PDF.

    Lazy-imports the PDF generator and the audit logger so the router
    module stays cheap to import. Emits the standard 3-event audit
    triplet (RECEIVED / COMPLETED / FAILED) per the EVOLV API rules.

    :requirement: URS-27.4
    """
    from Agents.integrity_manager import log_audit_event
    from utils.pdf_generator import generate_audit_export_pdf

    log_audit_event(
        agent_name="AuditRouter",
        action="AUDIT_EXPORT_RECEIVED",
        decision_logic=(
            f"Audit export requested by {body.signer_name} "
            f"({len(body.rows)} rows) for '{body.project_name}'"
        ),
    )

    try:
        pdf_bytes = generate_audit_export_pdf(
            rows=body.rows,
            project_name=body.project_name,
            signer_name=body.signer_name,
            meaning=body.meaning or "Audit Trail Inspection Export",
            filter_summary=body.filter_summary,
        )
    except Exception as exc:
        log_audit_event(
            agent_name="AuditRouter",
            action="AUDIT_EXPORT_FAILED",
            decision_logic=(
                f"Audit export failed for '{body.project_name}': "
                f"{type(exc).__name__}: {exc}"
            ),
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-003] Audit export failed. "
                "See server audit log for details."
            ),
        )

    log_audit_event(
        agent_name="AuditRouter",
        action="AUDIT_EXPORT_COMPLETED",
        decision_logic=(
            f"Audit export PDF generated for '{body.project_name}' "
            f"signed by {body.signer_name} "
            f"({len(body.rows)} rows, {len(pdf_bytes)} bytes)"
        ),
    )

    safe_proj = "".join(
        c if c.isalnum() else "-"
        for c in body.project_name.lower()
    ).strip("-") or "project"
    filename = f"audit-trail-{safe_proj}.pdf"
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
