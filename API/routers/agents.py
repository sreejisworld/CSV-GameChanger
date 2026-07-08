"""
agents.py — FastAPI router for Agent Passports.

Surfaces the explicit Permission Envelopes from
`Agents/agent_passports.py` to the React Dev Portal panel, the
customer-facing Trust Center (when it ships), and any downstream
auditor tooling.

Endpoints
=========
- GET /agents/passports                 — full passport registry
- GET /agents/passports/{agent_name}    — single agent passport

:requirement: URS-37.4 - Surface agent passports via JSON API for
              customer / auditor inspection.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

# Project root on sys.path so Agents/ imports resolve when this
# router is loaded by main.py via include_router().
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from Agents.agent_passports import (   # noqa: E402
    list_agent_passports,
    get_agent_passport,
)
from Agents.integrity_manager import log_audit_event  # noqa: E402


router = APIRouter(tags=["Agents"])


@router.get("/agents/passports")
def get_all_passports() -> JSONResponse:
    """
    Return the full registry of Agent Passports with schema-version
    envelope.

    Permission Envelopes are the explicit version of EVOLV's bounded-
    autonomy principle — every specialist function carries machine-
    readable metadata declaring what it may do, what data it may see,
    and what outputs require human sign-off. Pharma customers can
    read this. Auditors can read this.

    Emits the standard 3-event audit triplet per the EVOLV API rules.

    :requirement: URS-37.4 - Full passport registry via JSON API.
    """
    user_id = "system"
    log_audit_event(
        agent_name="API",
        action="AGENT_PASSPORTS_RECEIVED",
        user_id=user_id,
        decision_logic="GET /agents/passports request received",
        compliance_impact="System Transparency",
    )
    try:
        payload: Dict[str, Any] = list_agent_passports()
        log_audit_event(
            agent_name="API",
            action="AGENT_PASSPORTS_COMPLETED",
            user_id=user_id,
            decision_logic=(
                f"Returned {payload['passport_count']} agent passport(s) "
                f"at schema version {payload['schema_version']}"
            ),
            compliance_impact="System Transparency",
        )
        return JSONResponse(payload)
    except Exception as e:
        log_audit_event(
            agent_name="API",
            action="AGENT_PASSPORTS_FAILED",
            user_id=user_id,
            decision_logic=f"Passport list failed: {e}",
            compliance_impact="System Transparency",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list agent passports: {e}",
        )


@router.get("/agents/passports/{agent_name}")
def get_passport(agent_name: str) -> JSONResponse:
    """
    Return a single agent's Permission Envelope by name.

    404 if the agent is not registered. Callers must handle the
    missing case explicitly — silent fallback is precisely the kind
    of opaque behaviour pharma auditors check for.

    :param agent_name: Stable identifier (e.g. "RequirementArchitect").
    :requirement: URS-37.4 - Per-agent passport lookup via JSON API.
    """
    user_id = "system"
    log_audit_event(
        agent_name="API",
        action="AGENT_PASSPORT_LOOKUP_RECEIVED",
        user_id=user_id,
        decision_logic=f"Passport lookup for agent='{agent_name}'",
        compliance_impact="System Transparency",
    )
    try:
        passport = get_agent_passport(agent_name)
        if passport is None:
            log_audit_event(
                agent_name="API",
                action="AGENT_PASSPORT_LOOKUP_FAILED",
                user_id=user_id,
                decision_logic=(
                    f"No passport registered for '{agent_name}'"
                ),
                compliance_impact="System Transparency",
            )
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No agent passport registered for '{agent_name}'. "
                    "Check Agents/agent_passports.py for the canonical "
                    "list of registered specialist functions."
                ),
            )
        log_audit_event(
            agent_name="API",
            action="AGENT_PASSPORT_LOOKUP_COMPLETED",
            user_id=user_id,
            decision_logic=(
                f"Returned passport for '{agent_name}' "
                f"at version {passport.get('version', '?')}"
            ),
            compliance_impact="System Transparency",
        )
        return JSONResponse({
            "agent_name": agent_name,
            "passport":   passport,
        })
    except HTTPException:
        raise
    except Exception as e:
        log_audit_event(
            agent_name="API",
            action="AGENT_PASSPORT_LOOKUP_FAILED",
            user_id=user_id,
            decision_logic=f"Passport lookup error: {e}",
            compliance_impact="System Transparency",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to look up passport: {e}",
        )
