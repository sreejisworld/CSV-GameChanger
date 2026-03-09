"""
EVOLV API — The Compliance Nervous System for Life Sciences.

GAMP 5 and CSA Compliant EVOLV Engine.
Interactive documentation available at /docs (Swagger UI) and
/redoc (ReDoc).

:requirement: URS-27.1 - System shall expose interactive OpenAPI
              docs at /docs with title, version, and description.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
)
from pydantic import BaseModel, Field

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from API.agent_controller import AgentController
from API.middleware import TenantDictionaryMiddleware
from API.sandbox import AuditGuard, get_sandbox_mode
from API.key_store import (
    ScopedAPIKey,
    KeyStore,
    get_current_key,
    enforce_audit_only_scope,
)
from API.webhook_registry import (
    WebhookRegistry,
    schedule_webhook,
)
from API.job_store import JobStore, run_bulk_validate
from API.schemas import (
    BulkStatusResponse,
    BulkValidateRequest,
    ScopedAPIKeyIn,
    ScopedAPIKeyOut,
    WebhookRegistrationIn,
    WebhookRegistrationOut,
)
from Agents.sentinel_impact_agent import SentinelImpactAgent


# -----------------------------------------------------------------
# FastAPI application (Task 1 — OpenAPI 3.0 metadata)
# -----------------------------------------------------------------

app = FastAPI(
    title="EVOLV API",
    version="1.0.0",
    description=(
        "The Compliance Nervous System for Life Sciences.\n\n"
        "Enterprise-grade GAMP 5 / CSA / 21 CFR Part 11 "
        "compliant validation engine with attribute-based "
        "access control, tenant-specific nomenclature, "
        "and ServiceNow-style process mimicry.\n\n"
        "**Headers**\n"
        "- `X-API-Key` — Scoped API key for authenticated "
        "access.\n"
        "- `X-User-ID` — User identifier for audit trail "
        "attribution.\n"
        "- `X-EVOLV-MODE: Sandbox` — Process in developer "
        "sandbox; no production records are committed."
    ),
    contact={
        "name":  "WingstarTech Inc.",
        "email": "support@wingstartech.com",
    },
    license_info={
        "name": "Proprietary — WingstarTech Inc.",
    },
    openapi_tags=[
        {
            "name":        "Change Control",
            "description": "ServiceNow Change Request webhooks.",
        },
        {
            "name":        "Sentinel",
            "description": "Blast-radius impact analysis.",
        },
        {
            "name":        "Bulk",
            "description": "Batch requirement validation.",
        },
        {
            "name":        "Webhooks",
            "description": "Extension hook registry.",
        },
        {
            "name":        "Admin",
            "description": "API key management.",
        },
    ],
)

# TenantDictionaryMiddleware — rewrites JSON response labels
# to match the active tenant nomenclature map.
app.add_middleware(TenantDictionaryMiddleware)


# -----------------------------------------------------------------
# Centralized singletons
# -----------------------------------------------------------------

_controller = AgentController()

# Configure legacy file-based audit logger (21 CFR Part 11)
audit_logger = logging.getLogger("audit_trail")
audit_logger.setLevel(logging.INFO)
_log_handler = logging.FileHandler("audit_trail.log")
_log_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
)
audit_logger.addHandler(_log_handler)


# -----------------------------------------------------------------
# Internal exception classes (retain legacy error codes)
# -----------------------------------------------------------------

class CSVEngineError(Exception):
    """Base exception for CSV Engine errors."""


class ValidationError(CSVEngineError):
    """Error code: CSV-001 - Input validation failed."""

    error_code = "CSV-001"


class AuditLogError(CSVEngineError):
    """Error code: CSV-002 - Audit logging failed."""

    error_code = "CSV-002"


class ProcessingError(CSVEngineError):
    """Error code: CSV-003 - Change request processing failed."""

    error_code = "CSV-003"


# -----------------------------------------------------------------
# Legacy file-logger helper (kept separate from IntegrityManager)
# -----------------------------------------------------------------

def _file_log(
    user_id: str,
    action: str,
    details: Dict[str, Any],
) -> None:
    """
    Write a line to the file-based audit_trail.log.

    This is a lightweight companion to the CSV IntegrityManager
    trail and is never suppressed in Sandbox mode (file logs are
    not part of the GxP source-of-truth).

    :param user_id: Actor identifier.
    :param action: Action name.
    :param details: Key/value details dict.
    """
    try:
        audit_logger.info(
            f"user_id={user_id} | "
            f"timestamp={datetime.utcnow().isoformat()} | "
            f"action={action} | details={details}"
        )
    except Exception as exc:
        raise AuditLogError(
            f"Failed to write audit log: {exc}"
        ) from exc


# -----------------------------------------------------------------
# Task 1 — Pydantic request/response models
# -----------------------------------------------------------------

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
        "high", "critical",
        "medium", "moderate",
        "low", "minor",
    ] = Field(
        ...,
        description=(
            "System criticality level. "
            "Maps to GAMP 5 severity."
        ),
        examples=["high"],
    )
    change_type: Literal[
        "emergency", "expedited",
        "normal", "standard", "routine",
    ] = Field(
        ...,
        description=(
            "ServiceNow change type. "
            "Maps to GAMP 5 occurrence."
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
    occurrence: Literal[
        "RARE", "OCCASIONAL", "FREQUENT"
    ] = Field(
        ..., description="GAMP 5 occurrence classification."
    )
    detectability: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ..., description="GAMP 5 detectability classification."
    )
    rpn: int = Field(
        ...,
        ge=1,
        le=27,
        description="Risk Priority Number (1–27 scale).",
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
    :requirement: URS-31.3 - Sandbox flag on all responses.
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
    sandbox: bool = Field(
        default=False,
        description=(
            "True when processed in Sandbox mode — "
            "result not committed to production records."
        ),
    )


# -----------------------------------------------------------------
# Task 1 — Sentinel request/response models
# -----------------------------------------------------------------

class SentinelScanRequest(BaseModel):
    """
    Request model for the Sentinel blast-radius scan webhook.

    :requirement: URS-24.5 - Accept Sentinel scan triggers from
                  external source systems.
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
    :requirement: URS-31.3 - Sandbox flag on all responses.
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
    impact_score: int = Field(
        ..., ge=0, le=100,
        description="Composite impact score (0–100).",
    )
    rationalization_log: str = Field(
        ...,
        description="Natural-language audit of Sentinel logic.",
    )
    generated_at: str
    blast_radius_json: Dict[str, Any]
    impacted_items: List[ImpactItemResponse]
    sandbox: bool = Field(default=False)


# -----------------------------------------------------------------
# Lazy singleton — Sentinel agent
# -----------------------------------------------------------------

_sentinel_agent: Optional[SentinelImpactAgent] = None


def _get_sentinel() -> SentinelImpactAgent:
    global _sentinel_agent
    if _sentinel_agent is None:
        _sentinel_agent = SentinelImpactAgent()
    return _sentinel_agent


# =================================================================
# Endpoints
# =================================================================

# -----------------------------------------------------------------
# Change Control — ServiceNow webhook
# -----------------------------------------------------------------

@app.post(
    "/webhook/sn-change",
    response_model=ChangeRequestResponse,
    tags=["Change Control"],
    summary="Receive a ServiceNow Change Request",
    response_description=(
        "Risk assessment for the submitted change request."
    ),
    dependencies=[Depends(enforce_audit_only_scope)],
)
async def receive_servicenow_change(
    change_request: ServiceNowChangeRequest,
    request: Request,
    sandbox: bool = Depends(get_sandbox_mode),
) -> ChangeRequestResponse:
    """
    Webhook endpoint to receive ServiceNow Change Requests.

    Triggers GAMP 5 risk assessment via the Risk Strategist Agent
    and returns a structured risk report.

    Add ``X-EVOLV-MODE: Sandbox`` to test without committing any
    records to the production audit trail.

    :param change_request: Incoming ServiceNow CR payload.
    :param request: FastAPI request for header extraction.
    :param sandbox: True when X-EVOLV-MODE: Sandbox header present.
    :return: ChangeRequestResponse with risk assessment.
    :requirement: URS-1.1 - Accept ServiceNow change requests.
    :requirement: URS-31.1 - Sandbox mode support.
    """
    user_id = request.headers.get("X-User-ID", "SYSTEM")
    timestamp = datetime.utcnow().isoformat()
    guard = AuditGuard(sandbox)

    try:
        _file_log(
            user_id=user_id,
            action="CHANGE_REQUEST_RECEIVED",
            details={
                "cr_id":               change_request.cr_id,
                "system_criticality":  (
                    change_request.system_criticality
                ),
                "change_type":         change_request.change_type,
                "sandbox":             sandbox,
            },
        )

        guard.log(
            agent_name="API",
            action="CHANGE_REQUEST_RECEIVED",
            user_id=user_id,
            decision_logic=(
                f"cr_id={change_request.cr_id}"
            ),
        )

        risk_result = _controller.assess_risk(
            system_criticality=(
                change_request.system_criticality
            ),
            change_type=change_request.change_type,
        )

        _file_log(
            user_id=user_id,
            action="RISK_ASSESSMENT_COMPLETED",
            details={
                "cr_id":                  change_request.cr_id,
                "risk_level":             risk_result["risk_level"],
                "rpn":                    risk_result["rpn"],
                "testing_strategy":       (
                    risk_result["testing_strategy"]
                ),
                "patient_safety_override": (
                    risk_result["patient_safety_override"]
                ),
            },
        )

        guard.log(
            agent_name="API",
            action="CHANGE_REQUEST_ASSESSED",
            user_id=user_id,
            decision_logic=(
                f"cr_id={change_request.cr_id}, "
                f"risk={risk_result['risk_level']}"
            ),
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
            sandbox=sandbox,
        )

    except AuditLogError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"[{exc.error_code}] Audit logging failed: "
                f"{exc}"
            ),
        ) from exc
    except Exception as exc:
        _file_log(
            user_id=user_id,
            action="CHANGE_REQUEST_FAILED",
            details={"cr_id": change_request.cr_id,
                     "error": str(exc)},
        )
        guard.log(
            agent_name="API",
            action="CHANGE_REQUEST_FAILED",
            user_id=user_id,
            decision_logic=str(exc)[:200],
        )
        raise HTTPException(
            status_code=500,
            detail=(
                f"[{ProcessingError.error_code}] "
                f"Processing failed: {exc}"
            ),
        ) from exc


# -----------------------------------------------------------------
# Sentinel — blast-radius scan (Task 2 webhook firing)
# -----------------------------------------------------------------

@app.post(
    "/webhook/sentinel-scan",
    response_model=SentinelScanResponse,
    tags=["Sentinel"],
    summary="Run a Sentinel blast-radius scan",
    response_description=(
        "Full blast-radius report with Red/Yellow/Green items."
    ),
    dependencies=[Depends(enforce_audit_only_scope)],
)
async def trigger_sentinel_scan(
    scan_request: SentinelScanRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    sandbox: bool = Depends(get_sandbox_mode),
) -> SentinelScanResponse:
    """
    Trigger an automated Sentinel blast-radius scan.

    Accepts a requirement change from any external system and
    returns the full impact analysis.  On success, registered
    tenant webhooks for ``SENTINEL_SCAN_COMPLETED`` are fired
    asynchronously with HMAC-SHA256 signed payloads.

    :param scan_request: Sentinel scan request payload.
    :param request: FastAPI request for header extraction.
    :param background_tasks: FastAPI background task queue.
    :param sandbox: True when X-EVOLV-MODE: Sandbox header present.
    :return: SentinelScanResponse with impact report.
    :requirement: URS-24.5 - Accept Sentinel triggers.
    :requirement: URS-28.1 - Fire registered tenant webhooks.
    :requirement: URS-31.1 - Sandbox mode support.
    """
    user_id = request.headers.get("X-User-ID", "SYSTEM")
    guard = AuditGuard(sandbox)

    try:
        _file_log(
            user_id=user_id,
            action="SENTINEL_SCAN_RECEIVED",
            details={
                "requirement_id": scan_request.requirement_id,
                "source_system":  scan_request.source_system,
                "sandbox":        sandbox,
            },
        )

        guard.log(
            agent_name="API",
            action="SENTINEL_SCAN_RECEIVED",
            user_id=user_id,
            decision_logic=(
                f"req={scan_request.requirement_id}"
            ),
        )

        agent = _get_sentinel()
        report = agent.analyze_blast_radius(
            old_requirement=scan_request.old_text,
            new_requirement=scan_request.new_text,
            requirement_id=scan_request.requirement_id,
            traceability_matrix=(
                scan_request.traceability_matrix or {}
            ),
            change_id=scan_request.change_id,
        )

        _file_log(
            user_id=user_id,
            action="SENTINEL_SCAN_COMPLETED",
            details={
                "requirement_id":  scan_request.requirement_id,
                "change_category": report.change_category.value,
                "red_count":       report.red_count,
                "yellow_count":    report.yellow_count,
                "time_saved_h":    report.time_saved_hours,
            },
        )

        guard.log(
            agent_name="API",
            action="SENTINEL_SCAN_COMPLETED",
            user_id=user_id,
            decision_logic=(
                f"req={scan_request.requirement_id}, "
                f"category={report.change_category.value}, "
                f"score={report.impact_score}"
            ),
        )

        # Task 2 — fire registered tenant webhooks
        if not sandbox:
            hooks = (
                WebhookRegistry
                .get_instance()
                .get_hooks_for_event("SENTINEL_SCAN_COMPLETED")
            )
            for hook in hooks:
                schedule_webhook(
                    record=hook,
                    event_name="SENTINEL_SCAN_COMPLETED",
                    payload=report.blast_radius_json,
                    background_tasks=background_tasks,
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
            impact_score=report.impact_score,
            rationalization_log=report.rationalization_log,
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
            sandbox=sandbox,
        )

    except Exception as exc:
        _file_log(
            user_id=user_id,
            action="SENTINEL_SCAN_FAILED",
            details={
                "requirement_id": scan_request.requirement_id,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=500,
            detail=(
                f"[{ProcessingError.error_code}] "
                f"Sentinel scan failed: {exc}"
            ),
        ) from exc


# =================================================================
# Task 4 — Bulk / Batch Processing
# =================================================================

@app.post(
    "/bulk/validate",
    status_code=202,
    response_model=BulkStatusResponse,
    tags=["Bulk"],
    summary="Submit a batch of requirements for validation",
    response_description=(
        "202 Accepted with a job_id to poll for status."
    ),
    dependencies=[Depends(enforce_audit_only_scope)],
)
async def bulk_validate(
    payload: BulkValidateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    sandbox: bool = Depends(get_sandbox_mode),
) -> BulkStatusResponse:
    """
    Submit up to 500 requirements for background validation.

    Returns **202 Accepted** immediately with a ``job_id``.
    Poll ``GET /bulk/status/{job_id}`` to track progress and
    retrieve partial or complete results.

    Each item is processed through:
    1. URS generation (RequirementArchitect)
    2. URS verification (VerificationAgent)

    Sandbox mode: outputs are generated but not committed to
    the production audit trail.

    :param payload: BulkValidateRequest with up to 500 items.
    :param background_tasks: FastAPI background task queue.
    :param request: FastAPI request for header extraction.
    :param sandbox: True when X-EVOLV-MODE: Sandbox header present.
    :return: BulkStatusResponse with job_id and 'queued' status.
    :requirement: URS-30.1 - Accept batch of up to 500 requirements.
    :requirement: URS-31.1 - Sandbox mode support.
    """
    user_id = request.headers.get("X-User-ID", "SYSTEM")
    guard = AuditGuard(sandbox)

    items = [
        {
            "text":        req.text,
            "min_score":   req.min_score,
            "expert_mode": (
                req.expert_mode or payload.expert_mode
            ),
        }
        for req in payload.requirements
    ]

    job = JobStore.get_instance().create_job(
        total=len(items), sandbox=sandbox
    )

    background_tasks.add_task(
        run_bulk_validate,
        job.job_id,
        items,
        _controller,
        sandbox,
    )

    guard.log(
        agent_name="API",
        action="BULK_VALIDATE_STARTED",
        user_id=user_id,
        decision_logic=(
            f"job_id={job.job_id}, total={len(items)}"
        ),
    )

    return BulkStatusResponse(
        job_id=job.job_id,
        status="queued",
        total=job.total,
        completed=0,
        progress_pct=0.0,
        results=[],
        sandbox=sandbox,
    )


@app.get(
    "/bulk/status/{job_id}",
    response_model=BulkStatusResponse,
    tags=["Bulk"],
    summary="Poll the status of a bulk validation job",
)
async def bulk_status(job_id: str) -> BulkStatusResponse:
    """
    Return the current status and partial results for a job.

    Poll this endpoint after submitting a ``POST /bulk/validate``
    request.  When ``status`` is ``complete`` or ``failed``,
    the job will not change further.

    :param job_id: Job identifier returned by /bulk/validate.
    :return: BulkStatusResponse with progress and results.
    :requirement: URS-30.3 - Expose job status via GET.
    """
    job = JobStore.get_instance().get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )
    return BulkStatusResponse(
        job_id=job.job_id,
        status=job.status,
        total=job.total,
        completed=job.completed,
        progress_pct=job.progress_pct(),
        results=job.results,
        error=job.error,
        sandbox=job.sandbox,
    )


# =================================================================
# Task 2 — Webhook Registry
# =================================================================

@app.post(
    "/webhooks/register",
    response_model=WebhookRegistrationOut,
    status_code=201,
    tags=["Webhooks"],
    summary="Register a tenant webhook endpoint",
    dependencies=[Depends(enforce_audit_only_scope)],
)
async def register_webhook(
    payload: WebhookRegistrationIn,
    request: Request,
) -> WebhookRegistrationOut:
    """
    Register an HTTPS endpoint to receive EVOLV event payloads.

    Outbound requests are signed with HMAC-SHA256 using the
    provided secret.  Failed deliveries are retried at 1 min,
    5 min, and 15 min intervals.

    Available event names:
    - ``SENTINEL_SCAN_COMPLETED``
    - ``BULK_VALIDATE_COMPLETE``
    - ``CHANGE_REQUEST_ASSESSED``

    :param payload: WebhookRegistrationIn body.
    :param request: FastAPI request for audit attribution.
    :return: WebhookRegistrationOut with webhook_id.
    :requirement: URS-28.1 - Allow tenants to register webhooks.
    :requirement: URS-28.2 - HMAC-SHA256 payload signing.
    """
    record = WebhookRegistry.get_instance().register(
        tenant_id=payload.tenant_id,
        url=payload.url,
        events=payload.events,
        secret=payload.secret,
    )
    return WebhookRegistrationOut(
        webhook_id=record.webhook_id,
        tenant_id=record.tenant_id,
        url=record.url,
        events=record.events,
        created_at=record.created_at,
        active=record.active,
    )


@app.delete(
    "/webhooks/{webhook_id}",
    status_code=204,
    tags=["Webhooks"],
    summary="Deregister a tenant webhook",
    dependencies=[Depends(enforce_audit_only_scope)],
)
async def deregister_webhook(webhook_id: str) -> None:
    """
    Deactivate a previously registered webhook.

    The webhook record is retained in the store with
    ``active=False`` for audit purposes but will no longer
    receive event deliveries.

    :param webhook_id: UUID of the webhook to deregister.
    :return: 204 No Content on success.
    :requirement: URS-28.1
    """
    found = WebhookRegistry.get_instance().deregister(
        webhook_id
    )
    if not found:
        raise HTTPException(
            status_code=404,
            detail=f"Webhook '{webhook_id}' not found.",
        )


# =================================================================
# Task 3 — Scoped API Key Management
# =================================================================

@app.post(
    "/admin/api-keys",
    response_model=ScopedAPIKeyOut,
    status_code=201,
    tags=["Admin"],
    summary="Create a scoped API key",
)
async def create_api_key(
    payload: ScopedAPIKeyIn,
    request: Request,
    current_key: Optional[ScopedAPIKey] = Depends(
        get_current_key
    ),
) -> ScopedAPIKeyOut:
    """
    Generate a new identity-aware API key for a tenant.

    The raw key is returned **exactly once** in the
    ``raw_key`` field.  Store it securely — it cannot be
    recovered after this response.

    Keys with ``scope: audit_only`` are automatically blocked
    from any POST, PUT, PATCH, or DELETE request by the
    ``enforce_audit_only_scope`` dependency.

    :param payload: ScopedAPIKeyIn with tenant, scopes, policy.
    :param request: FastAPI request for audit attribution.
    :param current_key: Resolved API key (may be None for admin).
    :return: ScopedAPIKeyOut with raw_key shown once.
    :requirement: URS-29.1 - Keys linked to Tenant_ID + DAC policy.
    """
    record, raw_key = KeyStore.get_instance().create_key(
        tenant_id=payload.tenant_id,
        scopes=payload.scopes,
        dac_policy=payload.dac_policy,
    )
    return ScopedAPIKeyOut(
        key_id=record.key_id,
        tenant_id=record.tenant_id,
        scopes=record.scopes,
        raw_key=raw_key,
        created_at=record.created_at,
        active=record.active,
    )


@app.get(
    "/admin/api-keys/{key_id}",
    response_model=ScopedAPIKeyOut,
    tags=["Admin"],
    summary="Retrieve API key metadata",
)
async def get_api_key(
    key_id: str,
    current_key: Optional[ScopedAPIKey] = Depends(
        get_current_key
    ),
) -> ScopedAPIKeyOut:
    """
    Retrieve metadata for an API key by its key_id.

    The raw key is **never** returned by this endpoint.
    Only non-sensitive metadata (tenant, scopes, created_at)
    is exposed.

    :param key_id: UUID of the key to retrieve.
    :param current_key: Resolved from X-API-Key header.
    :return: ScopedAPIKeyOut without raw_key.
    :requirement: URS-29.1
    """
    record = KeyStore.get_instance().get_by_id(key_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"API key '{key_id}' not found.",
        )
    return ScopedAPIKeyOut(
        key_id=record.key_id,
        tenant_id=record.tenant_id,
        scopes=record.scopes,
        raw_key=None,  # Never exposed after creation
        created_at=record.created_at,
        active=record.active,
    )
