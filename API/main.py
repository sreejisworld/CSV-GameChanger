"""
CSV-GameChanger API Module.

GAMP 5 and CSA Compliant EVOLV Engine - API Endpoints.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from API.agent_controller import AgentController
from API.middleware import TenantDictionaryMiddleware
from Agents.sentinel_impact_agent import (
    SentinelImpactAgent,
    BlastRadiusReport,
)


# Centralized agent controller — all agent calls go through here.
_controller = AgentController()


# Configure audit logger for 21 CFR Part 11 compliance
audit_logger = logging.getLogger("audit_trail")
audit_logger.setLevel(logging.INFO)
handler = logging.FileHandler("audit_trail.log")
handler.setFormatter(
    logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
)
audit_logger.addHandler(handler)


class CSVEngineError(Exception):
    """Base exception for CSV Engine errors."""

    pass


class ValidationError(CSVEngineError):
    """Error code: CSV-001 - Input validation failed."""

    error_code = "CSV-001"


class AuditLogError(CSVEngineError):
    """Error code: CSV-002 - Audit logging failed."""

    error_code = "CSV-002"


class ProcessingError(CSVEngineError):
    """Error code: CSV-003 - Change request processing failed."""

    error_code = "CSV-003"


app = FastAPI(
    title="CSV-GameChanger",
    description="GAMP 5 and CSA Compliant EVOLV Engine",
    version="0.2.0"
)

# Register TenantDictionary middleware — must be added after
# app creation so it wraps all routes.
app.add_middleware(TenantDictionaryMiddleware)


class ServiceNowChangeRequest(BaseModel):
    """
    Pydantic model for ServiceNow Change Request payload.

    :requirement: URS-1.1 - System shall accept change requests
                  from ServiceNow.
    """

    cr_id: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="ServiceNow Change Request ID.",
        examples=["CHG0012345"],
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Change description.",
        examples=["Upgrade firmware on temperature sensors"],
    )
    system_criticality: Literal[
        "high", "critical", "medium", "moderate", "low", "minor"
    ] = Field(
        ...,
        description=(
            "System criticality level. Maps to GAMP 5 severity."
        ),
        examples=["high"],
    )
    change_type: Literal[
        "emergency", "expedited", "normal", "standard", "routine"
    ] = Field(
        ...,
        description=(
            "ServiceNow change type. Maps to GAMP 5 occurrence."
        ),
        examples=["normal"],
    )


class RiskAssessmentResult(BaseModel):
    """
    Risk assessment result from the Risk Strategist Agent.

    :requirement: URS-4.7 - System shall return risk assessment
                  results.
    """

    severity: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        ..., description="GAMP 5 severity classification."
    )
    occurrence: Literal["RARE", "OCCASIONAL", "FREQUENT"] = Field(
        ..., description="GAMP 5 occurrence classification."
    )
    detectability: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ..., description="GAMP 5 detectability classification."
    )
    rpn: int = Field(
        ...,
        ge=1,
        le=27,
        description="Risk Priority Number (1-27 scale).",
    )
    risk_level: Literal["Low", "Medium", "High"] = Field(
        ..., description="Overall risk level."
    )
    testing_strategy: str = Field(
        ..., description="CSA testing recommendation."
    )
    patient_safety_override: bool = Field(
        ...,
        description=(
            "True when severity is HIGH, forcing risk to HIGH."
        ),
    )


class ChangeRequestResponse(BaseModel):
    """
    Response model for change request acknowledgment.

    :requirement: URS-1.2 - System shall acknowledge receipt of
                  change requests.
    """

    status: Literal["assessed", "error"] = Field(
        ..., description="Processing outcome."
    )
    cr_id: str = Field(
        ..., description="Echo of the submitted CR ID."
    )
    message: str = Field(
        ..., description="Human-readable status message."
    )
    timestamp: str = Field(
        ..., description="ISO-8601 timestamp of processing."
    )
    risk_assessment: Optional[RiskAssessmentResult] = Field(
        default=None,
        description="Risk assessment (present on success).",
    )


def log_audit_event(
    user_id: str,
    action: str,
    details: Dict[str, Any]
) -> None:
    """
    Log an event to the immutable audit trail.

    :param user_id: Identifier of the user performing the action.
    :param action: The action being performed.
    :param details: Additional details about the action.
    :return: None
    :requirement: URS-2.1 - System shall maintain 21 CFR Part 11 compliant audit trail.
    :raises AuditLogError: If audit logging fails.
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        audit_logger.info(
            f"user_id={user_id} | timestamp={timestamp} | "
            f"action={action} | details={details}"
        )
    except Exception as e:
        raise AuditLogError(f"Failed to write audit log: {str(e)}") from e


@app.post("/webhook/sn-change", response_model=ChangeRequestResponse)
async def receive_servicenow_change(
    change_request: ServiceNowChangeRequest,
    request: Request
) -> ChangeRequestResponse:
    """
    Webhook endpoint to receive ServiceNow Change Requests.

    :param change_request: The incoming ServiceNow change request payload.
    :param request: The FastAPI request object for extracting client info.
    :return: ChangeRequestResponse acknowledging receipt.
    :requirement: URS-1.1 - System shall accept change requests from ServiceNow.
    :raises HTTPException: If processing fails with appropriate error code.
    """
    user_id = request.headers.get("X-User-ID", "SYSTEM")
    timestamp = datetime.utcnow().isoformat()

    try:
        log_audit_event(
            user_id=user_id,
            action="CHANGE_REQUEST_RECEIVED",
            details={
                "cr_id": change_request.cr_id,
                "system_criticality": (
                    change_request.system_criticality
                ),
                "change_type": change_request.change_type,
            },
        )

        _controller.log_event(
            agent_name="API",
            action="CHANGE_REQUEST_RECEIVED",
            user_id=user_id,
        )

        # Trigger Risk Strategist via controller
        risk_result = _controller.assess_risk(
            system_criticality=(
                change_request.system_criticality
            ),
            change_type=change_request.change_type,
        )

        # Log risk assessment to audit trail
        log_audit_event(
            user_id=user_id,
            action="RISK_ASSESSMENT_COMPLETED",
            details={
                "cr_id": change_request.cr_id,
                "risk_level": risk_result["risk_level"],
                "rpn": risk_result["rpn"],
                "testing_strategy": (
                    risk_result["testing_strategy"]
                ),
                "patient_safety_override": (
                    risk_result["patient_safety_override"]
                ),
            },
        )

        _controller.log_event(
            agent_name="API",
            action="CHANGE_REQUEST_ASSESSED",
            user_id=user_id,
        )

        return ChangeRequestResponse(
            status="assessed",
            cr_id=change_request.cr_id,
            message=(
                "Risk assessment complete: "
                f"{risk_result['risk_level']} risk"
            ),
            timestamp=timestamp,
            risk_assessment=RiskAssessmentResult(
                **risk_result
            ),
        )

    except AuditLogError as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"[{e.error_code}] Audit logging failed: "
                f"{str(e)}"
            ),
        ) from e
    except Exception as e:
        log_audit_event(
            user_id=user_id,
            action="CHANGE_REQUEST_FAILED",
            details={
                "cr_id": change_request.cr_id,
                "error": str(e),
            },
        )
        _controller.log_event(
            agent_name="API",
            action="CHANGE_REQUEST_FAILED",
            user_id=user_id,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                f"[{ProcessingError.error_code}] "
                f"Processing failed: {str(e)}"
            ),
        ) from e


# =============================================================
# Clean Core — Sentinel Scan Webhook
# =============================================================

class SentinelScanRequest(BaseModel):
    """
    Request model for the Sentinel blast-radius scan webhook.

    Accepts a requirement change from any external system
    (ServiceNow, SAP, Jira, etc.) and triggers an automated
    impact analysis.

    :requirement: URS-24.5 - System shall accept Sentinel scan
                  triggers from external source systems.
    """

    change_id: Optional[str] = Field(
        default=None,
        description=(
            "External change identifier (CR, ECO, issue key). "
            "Auto-generated when omitted."
        ),
        examples=["CHG0012345"],
    )
    requirement_id: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Identifier of the changed requirement.",
        examples=["URS-7.1"],
    )
    old_text: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Original requirement text.",
        examples=[
            "The system shall track warehouse temperature."
        ],
    )
    new_text: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Updated requirement text.",
        examples=[
            "The system shall monitor and alert on warehouse "
            "temperature using 21 CFR Part 211 thresholds."
        ],
    )
    source_system: Literal[
        "servicenow", "sap", "jira", "manual", "other"
    ] = Field(
        default="manual",
        description="Source system that triggered the scan.",
        examples=["servicenow"],
    )
    traceability_matrix: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional trace matrix keyed by requirement_id. "
            "Falls back to demo data when omitted."
        ),
    )


class ImpactItemResponse(BaseModel):
    """Single impacted item within the blast-radius response."""

    item_id: str
    item_type: str
    title: str
    severity: Literal["Red", "Yellow", "Green"]
    tier: int
    reason: str
    linked_requirement: str


class SentinelScanResponse(BaseModel):
    """
    Response model for the Sentinel scan webhook.

    :requirement: URS-24.5 - Return structured blast-radius JSON.
    """

    change_id: str
    requirement_id: str
    source_system: str
    change_category: str
    semantic_delta: str
    red_count: int
    yellow_count: int
    green_count: int
    total_test_cases: int
    optimized_test_cases: int
    time_saved_hours: float
    generated_at: str
    blast_radius_json: Dict[str, Any]
    impacted_items: List[ImpactItemResponse]


# Lazy singleton for the Sentinel agent
_sentinel_agent: Optional[SentinelImpactAgent] = None


def _get_sentinel_agent() -> SentinelImpactAgent:
    global _sentinel_agent
    if _sentinel_agent is None:
        _sentinel_agent = SentinelImpactAgent()
    return _sentinel_agent


@app.post(
    "/webhook/sentinel-scan",
    response_model=SentinelScanResponse,
)
async def trigger_sentinel_scan(
    scan_request: SentinelScanRequest,
    request: Request,
) -> SentinelScanResponse:
    """
    Webhook endpoint for automated Sentinel blast-radius scans.

    Accepts a requirement change from any external system and
    returns the full impact analysis as structured JSON.

    :param scan_request: Sentinel scan request payload.
    :param request: FastAPI request object.
    :return: SentinelScanResponse with blast-radius data.
    :requirement: URS-24.5 - Accept Sentinel triggers from
                  external systems.
    :raises HTTPException: On processing failure.
    """
    user_id = request.headers.get("X-User-ID", "SYSTEM")

    try:
        log_audit_event(
            user_id=user_id,
            action="SENTINEL_SCAN_RECEIVED",
            details={
                "requirement_id": scan_request.requirement_id,
                "source_system":  scan_request.source_system,
                "change_id":      scan_request.change_id,
            },
        )

        agent = _get_sentinel_agent()
        report = agent.analyze_blast_radius(
            old_requirement=scan_request.old_text,
            new_requirement=scan_request.new_text,
            requirement_id=scan_request.requirement_id,
            traceability_matrix=(
                scan_request.traceability_matrix or {}
            ),
            change_id=scan_request.change_id,
        )

        log_audit_event(
            user_id=user_id,
            action="SENTINEL_SCAN_COMPLETED",
            details={
                "requirement_id": scan_request.requirement_id,
                "change_category": (
                    report.change_category.value
                ),
                "red_count":     report.red_count,
                "yellow_count":  report.yellow_count,
                "green_count":   report.green_count,
                "time_saved_h":  report.time_saved_hours,
            },
        )

        return SentinelScanResponse(
            change_id=report.change_id,
            requirement_id=report.requirement_id,
            source_system=scan_request.source_system,
            change_category=report.change_category.value,
            semantic_delta=report.semantic_delta,
            red_count=report.red_count,
            yellow_count=report.yellow_count,
            green_count=report.green_count,
            total_test_cases=report.total_test_cases,
            optimized_test_cases=report.optimized_test_cases,
            time_saved_hours=report.time_saved_hours,
            generated_at=report.generated_at,
            blast_radius_json=report.blast_radius_json,
            impacted_items=[
                ImpactItemResponse(
                    item_id=i.item_id,
                    item_type=i.item_type,
                    title=i.title,
                    severity=i.severity.value,
                    tier=i.tier.value,
                    reason=i.reason,
                    linked_requirement=i.linked_requirement,
                )
                for i in report.impacted_items
            ],
        )

    except Exception as e:
        log_audit_event(
            user_id=user_id,
            action="SENTINEL_SCAN_FAILED",
            details={
                "requirement_id": scan_request.requirement_id,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=500,
            detail=(
                f"[{ProcessingError.error_code}] "
                f"Sentinel scan failed: {str(e)}"
            ),
        ) from e
