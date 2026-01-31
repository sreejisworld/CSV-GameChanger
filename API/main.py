"""
CSV-GameChanger API Module.

GAMP 5 and CSA Compliant CSV Engine - API Endpoints.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Agents.risk_strategist import assess_change_request


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
    description="GAMP 5 and CSA Compliant CSV Engine",
    version="0.1.0"
)


class ServiceNowChangeRequest(BaseModel):
    """
    Pydantic model for ServiceNow Change Request payload.

    :requirement: URS-1.1 - System shall accept change requests from ServiceNow.
    """

    cr_id: str
    description: str
    system_criticality: str
    change_type: str


class RiskAssessmentResult(BaseModel):
    """
    Risk assessment result from the Risk Strategist Agent.

    :requirement: URS-4.7 - System shall return risk assessment results.
    """

    severity: str
    occurrence: str
    detectability: str
    rpn: int
    risk_level: str
    testing_strategy: str
    patient_safety_override: bool


class ChangeRequestResponse(BaseModel):
    """
    Response model for change request acknowledgment.

    :requirement: URS-1.2 - System shall acknowledge receipt of change requests.
    """

    status: str
    cr_id: str
    message: str
    timestamp: str
    risk_assessment: Optional[RiskAssessmentResult] = None


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
                "system_criticality": change_request.system_criticality,
                "change_type": change_request.change_type
            }
        )

        # Trigger Risk Strategist Agent
        risk_result = assess_change_request(
            system_criticality=change_request.system_criticality,
            change_type=change_request.change_type
        )

        # Log risk assessment to audit trail
        log_audit_event(
            user_id=user_id,
            action="RISK_ASSESSMENT_COMPLETED",
            details={
                "cr_id": change_request.cr_id,
                "risk_level": risk_result["risk_level"],
                "rpn": risk_result["rpn"],
                "testing_strategy": risk_result["testing_strategy"],
                "patient_safety_override": risk_result["patient_safety_override"]
            }
        )

        return ChangeRequestResponse(
            status="assessed",
            cr_id=change_request.cr_id,
            message=f"Risk assessment complete: {risk_result['risk_level']} risk",
            timestamp=timestamp,
            risk_assessment=RiskAssessmentResult(**risk_result)
        )

    except AuditLogError as e:
        raise HTTPException(
            status_code=500,
            detail=f"[{e.error_code}] Audit logging failed: {str(e)}"
        ) from e
    except Exception as e:
        log_audit_event(
            user_id=user_id,
            action="CHANGE_REQUEST_FAILED",
            details={"cr_id": change_request.cr_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=500,
            detail=f"[{ProcessingError.error_code}] Processing failed: {str(e)}"
        ) from e
