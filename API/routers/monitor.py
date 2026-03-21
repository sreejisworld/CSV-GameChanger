"""
monitor.py — FastAPI router for the Monitor phase.

Endpoints:
  GET /audit-trail   — Return all rows from output/audit_trail.csv as JSON.

:requirement: URS-2.1 - System shall maintain 21 CFR Part 11 compliant
              audit trail.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter
from fastapi.responses import JSONResponse

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_CSV    = PROJECT_ROOT / "output" / "audit_trail.csv"

router = APIRouter(tags=["Monitor"])


@router.get("/audit-trail")
def get_audit_trail() -> JSONResponse:
    """
    Return all rows from the EVOLV audit trail CSV as JSON.

    Reads output/audit_trail.csv. Returns an empty list if the file
    does not exist yet (no audit events have been written).

    :requirement: URS-2.1 - Maintain 21 CFR Part 11 compliant audit trail.
    """
    if not AUDIT_CSV.exists():
        return JSONResponse({"records": [], "total": 0})

    records: List[Dict[str, Any]] = []
    with open(AUDIT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))

    # Return newest first
    records.reverse()

    return JSONResponse({"records": records, "total": len(records)})
