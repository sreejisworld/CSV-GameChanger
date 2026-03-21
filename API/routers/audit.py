"""
Audit trail read-only router.

:requirement: URS-2.1 - System shall maintain 21 CFR Part 11 compliant audit trail.

Exposes recent audit trail rows for the React live-feed panel.
The CSV is append-only and never modified by this router.
"""
import csv
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(tags=["Audit"])

_AUDIT_CSV = Path(__file__).parent.parent.parent / "output" / "audit_trail.csv"

# Impact → severity bucket for colour-coding in the UI
_IMPACT_SEVERITY = {
    "Compliance Exception":    "error",
    "Regulatory Compliance":   "success",
    "Validation Evidence":     "success",
    "GxP Documentation":       "info",
    "Operational":             "info",
    "Key Management":          "warning",
    "Monitoring":              "info",
    "Release":                 "success",
}


class AuditRow(BaseModel):
    timestamp:  str
    user_id:    str
    agent:      str
    action:     str
    logic:      str
    impact:     str
    hash:       str
    severity:   str   # error | warning | success | info


@router.get("/audit/recent", response_model=List[AuditRow])
def get_recent_audit(
    limit: int = Query(default=50, ge=1, le=500),
    agent: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
):
    """
    Return the most recent *limit* audit trail rows, newest first.

    Optional filters:
    - ``agent``    — filter by Agent_Name (case-insensitive substring)
    - ``severity`` — filter by severity bucket (error/warning/success/info)

    :requirement: URS-2.1
    """
    if not _AUDIT_CSV.exists():
        return []

    rows: List[AuditRow] = []
    with _AUDIT_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            impact   = row.get("Compliance_Impact", "Operational")
            sev      = _IMPACT_SEVERITY.get(impact, "info")
            agent_nm = row.get("Agent_Name", "")

            if agent and agent.lower() not in agent_nm.lower():
                continue
            if severity and sev != severity:
                continue

            rows.append(AuditRow(
                timestamp = row.get("Timestamp", ""),
                user_id   = row.get("User_ID", "SYSTEM"),
                agent     = agent_nm,
                action    = row.get("Action_Performed", ""),
                logic     = row.get("Decision_Logic", ""),
                impact    = impact,
                hash      = row.get("Reasoning_Hash", "")[:12],
                severity  = sev,
            ))

    # Newest first: take the most recent `limit` rows then reverse
    return rows[-limit:][::-1]
