"""
EVOLV API — The Compliance Nervous System for Life Sciences.

GAMP 5 and CSA Compliant EVOLV Engine.
Interactive documentation available at /docs (Swagger UI) and
/redoc (ReDoc).

:requirement: URS-27.1 - System shall expose interactive OpenAPI
              docs at /docs with title, version, and description.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from API.agent_controller import AgentController
from API.middleware import TenantDictionaryMiddleware
from API.sandbox import AuditGuard, get_sandbox_mode
from API.security import (
    get_cors_origins,
    require_platform_key,
    warn_if_auth_disabled,
)
from API.key_store import (
    ScopedAPIKey,
    KeyStore,
    get_current_key,
    enforce_audit_only_scope,
    require_api_key,
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
from API.project_store import ProjectStore, GAMP5_FOLDERS
from API.routers.verify           import router as verify_router
from API.routers.release          import router as release_router
from API.routers.monitor          import router as monitor_router
from API.routers.generate_script  import router as gen_script_router
from API.routers.requirements     import router as requirements_router
from API.routers.exports          import router as exports_router
from API.routers.plan             import router as plan_router
from API.routers.audit            import router as audit_router
from API.routers.governance       import router as governance_router
from API.routers.test_authoring   import router as test_authoring_router
from API.routers.traceability     import router as traceability_router
from API.routers.agents           import router as agents_router
from API.routers.change_control   import router as change_control_router
from API.routers.validated_state  import router as validated_state_router
from API.routers.regulatory_drift import router as regulatory_drift_router
from API.routers.trustworthiness  import router as trustworthiness_router
from API.routers.bap              import router as bap_router


def _validate_env() -> None:
    """Crash loudly at startup if required env vars are missing."""
    required = {
        "OPENAI_API_KEY":  (
            "OpenAI API key (for URS generation and embeddings)"
        ),
        "PINECONE_API_KEY": (
            "Pinecone API key (for GAMP 5 knowledge base)"
        ),
    }
    missing = [
        f"  {k}: {desc}"
        for k, desc in required.items()
        if not os.getenv(k)
    ]
    if missing:
        raise RuntimeError(
            "EVOLV startup failed — missing required "
            "environment variables:\n"
            + "\n".join(missing)
            + "\n\nSet these in your .env file or environment "
            "before starting."
        )


_validate_env()


# -----------------------------------------------------------------
# FastAPI application (Task 1 — OpenAPI 3.0 metadata)
# -----------------------------------------------------------------

_env = os.getenv("EVOLV_ENV", "development")
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
        {
            "name":        "Navigator",
            "description": (
                "Project Navigator — GAMP 5 hierarchical "
                "project / release / folder / item CRUD "
                "and HITL approval endpoints."
            ),
        },
    ],
    docs_url="/docs" if _env != "production" else None,
    redoc_url="/redoc" if _env != "production" else None,
    openapi_url=(
        "/openapi.json" if _env != "production" else None
    ),
    # Global optional API-key gate (2026-07-11 security audit).
    # When EVOLV_API_KEY is set, every path operation requires a
    # matching X-API-Key header; when unset (dev), requests pass
    # through and a startup warning is logged.
    dependencies=[Depends(require_platform_key)],
)

# Emit a loud warning when running with authentication disabled.
warn_if_auth_disabled()

# TenantDictionaryMiddleware — rewrites JSON response labels
# to match the active tenant nomenclature map.
app.add_middleware(TenantDictionaryMiddleware)

# ── Routers ────────────────────────────────────────────────────────
app.include_router(verify_router,        prefix="/verify")
app.include_router(gen_script_router,   prefix="/verify")
app.include_router(release_router,      prefix="/release")
app.include_router(monitor_router)
app.include_router(requirements_router)
app.include_router(exports_router)
app.include_router(plan_router)
app.include_router(audit_router)
app.include_router(governance_router)
app.include_router(test_authoring_router, prefix="/test-authoring")
app.include_router(traceability_router)
app.include_router(agents_router)
app.include_router(change_control_router)
app.include_router(validated_state_router)
app.include_router(regulatory_drift_router)
app.include_router(trustworthiness_router)
app.include_router(bap_router)

# CORSMiddleware — restricted to known dev origins (React on
# 5173/5174, legacy React on 3000).  Additional origins (extra
# worktree ports, Streamlit on 8501, or production frontends)
# must be supplied via the EVOLV_CORS_ORIGINS env var
# (comma-separated).  Wildcard origins are never permitted.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "X-API-Key",
        "Authorization",
        "Accept",
    ],
)


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
    # Webhook receivers are authenticated by the caller (ServiceNow
    # uses HMAC / IP-allowlist in production).  No API key required
    # here so the EVOLV demo panel and Streamlit can call this freely.
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
        # Details stay server-side (audit log); client gets a
        # generic message + error code only.
        raise HTTPException(
            status_code=500,
            detail=(
                f"[{exc.error_code}] Audit logging failed. "
                "See server audit log for details."
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
                "Change request processing failed. "
                "See server audit log for details."
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
                "Sentinel scan failed. "
                "See server audit log for details."
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
    dependencies=[Depends(require_api_key)],
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
    dependencies=[Depends(require_api_key)],
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


# =================================================================
# Project Navigator — Pydantic models
# =================================================================

class ProjectIn(BaseModel):
    """
    Request body for creating a project.

    :requirement: URS-32.1 - Accept project creation requests.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Human-readable project name.",
        examples=["LabCore LIMS v4.2 Validation"],
    )
    system_name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Name of the validated system.",
        examples=["LabCore LIMS"],
    )
    compliance_mode: str = Field(
        default="GMP",
        description="GMP | GCP | GLP | ISO13485",
        examples=["GMP"],
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Optional project description.",
    )


class ProjectOut(BaseModel):
    """
    Project summary returned by Navigator list/create.

    :requirement: URS-32.1
    """

    project_id: str
    name: str
    system_name: str
    compliance_mode: str
    description: str
    created_at: str
    release_count: int


class ReleaseIn(BaseModel):
    """
    Request body for creating a release.

    :requirement: URS-32.2 - Accept release creation with
                  GAMP 5 folder template.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Release name.",
        examples=["v1.0 Validation"],
    )
    version: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Version string.",
        examples=["1.0"],
    )
    description: str = Field(
        default="",
        max_length=500,
    )
    status: str = Field(
        default="Planned",
        description=(
            "Planned | In Progress | Released | Archived"
        ),
    )
    folder_template: Optional[List[str]] = Field(
        default=None,
        description=(
            "Custom folder list. Defaults to GAMP 5 "
            "standard folders when omitted."
        ),
    )


class ReleaseOut(BaseModel):
    """
    Release summary returned by Navigator endpoints.

    :requirement: URS-32.2
    """

    release_id: str
    name: str
    version: str
    status: str
    description: str
    created_at: str
    folders: Dict[str, List[Dict[str, Any]]]
    item_count: int


class ItemIn(BaseModel):
    """
    Request body for adding an item to a release folder.

    :requirement: URS-32.3 - Accept item creation requests.
    """

    folder: str = Field(
        ...,
        description="Target folder name within the release.",
        examples=["URS"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name for the item.",
        examples=["URS-008 Temperature Alert SLA"],
    )
    item_type: str = Field(
        default="urs",
        description=(
            "urs | test_script | risk | traceability | "
            "report | note | supplier_doc"
        ),
    )
    artifact_id: str = Field(
        default="",
        max_length=40,
        description="Optional EVOLV artefact ID.",
    )
    notes: str = Field(
        default="",
        max_length=1000,
    )
    status: str = Field(
        default="Draft",
        description=(
            "Draft | In Review | Approved | "
            "Rejected | Retired"
        ),
    )


class ItemOut(BaseModel):
    """
    Item detail returned by Navigator endpoints.

    :requirement: URS-32.3
    """

    item_id: str
    name: str
    item_type: str
    status: str
    artifact_id: str
    notes: str
    created_at: str
    updated_at: str


class MoveItemIn(BaseModel):
    """
    Request body for moving an item between folders/releases.

    :requirement: URS-32.4 - Move items between releases.
    """

    src_folder: str = Field(
        ..., description="Source folder name."
    )
    dst_release_id: str = Field(
        ..., description="Destination release UUID."
    )
    dst_folder: str = Field(
        ..., description="Destination folder name."
    )


class LibraryEntryIn(BaseModel):
    """
    Request body for adding a Global Library entry.

    :requirement: URS-32.5 - Accept Global Library entries.
    """

    name: str = Field(
        ..., min_length=1, max_length=200
    )
    entry_type: str = Field(
        ...,
        description=(
            "system_description | risk_matrix"
        ),
        examples=["system_description"],
    )
    content: str = Field(
        ..., min_length=1, max_length=10000
    )
    tags: Optional[List[str]] = Field(default=None)


class LibraryEntryOut(BaseModel):
    """
    Global Library entry returned by Navigator endpoints.

    :requirement: URS-32.5
    """

    entry_id: str
    name: str
    entry_type: str
    content: str
    tags: List[str]
    created_at: str
    updated_at: str


# =================================================================
# Project Navigator — Endpoints
# =================================================================

# -----------------------------------------------------------------
# Projects
# -----------------------------------------------------------------

@app.get(
    "/api/navigator/projects",
    response_model=List[ProjectOut],
    tags=["Navigator"],
    summary="List all projects",
)
async def list_projects() -> List[ProjectOut]:
    """
    Return all projects with their release counts.

    Used by the React Project Navigator on initial load to
    populate the top-level tree.

    :return: List of ProjectOut summaries.
    :requirement: URS-32.1 - List all projects.
    """
    store = ProjectStore.get_instance()
    return [
        ProjectOut(
            project_id=p.project_id,
            name=p.name,
            system_name=p.system_name,
            compliance_mode=p.compliance_mode,
            description=p.description,
            created_at=p.created_at,
            release_count=len(p.releases),
        )
        for p in store.list_projects()
    ]


@app.post(
    "/api/navigator/projects",
    response_model=ProjectOut,
    status_code=201,
    tags=["Navigator"],
    summary="Create a project",
)
async def create_project(
    payload: ProjectIn,
    request: Request,
) -> ProjectOut:
    """
    Create a new top-level validation project.

    :param payload: ProjectIn body.
    :param request: FastAPI request for audit attribution.
    :return: Created ProjectOut.
    :requirement: URS-32.1 - Create project.
    """
    user_id = request.headers.get(
        "X-User-ID", "SYSTEM"
    )
    store = ProjectStore.get_instance()
    proj = store.create_project(
        name=payload.name,
        system_name=payload.system_name,
        compliance_mode=payload.compliance_mode,
        description=payload.description,
    )
    _file_log(
        user_id=user_id,
        action="NAVIGATOR_PROJECT_CREATED",
        details={
            "project_id": proj.project_id,
            "name": proj.name,
        },
    )
    return ProjectOut(
        project_id=proj.project_id,
        name=proj.name,
        system_name=proj.system_name,
        compliance_mode=proj.compliance_mode,
        description=proj.description,
        created_at=proj.created_at,
        release_count=0,
    )


@app.get(
    "/api/navigator/projects/{project_id}",
    response_model=Dict[str, Any],
    tags=["Navigator"],
    summary="Get full project tree",
)
async def get_project(
    project_id: str,
) -> Dict[str, Any]:
    """
    Return a project with all releases and their folder
    contents — the full tree for the Navigator.

    :param project_id: UUID of the project.
    :return: Full project dict including releases.
    :requirement: URS-32.1 - Return full project tree.
    """
    store = ProjectStore.get_instance()
    proj = store.get_project(project_id)
    if proj is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Project '{project_id}' not found."
            ),
        )
    return proj.to_dict()


@app.delete(
    "/api/navigator/projects/{project_id}",
    status_code=204,
    tags=["Navigator"],
    summary="Delete a project",
)
async def delete_project(
    project_id: str,
    request: Request,
) -> None:
    """
    Delete a project and all its releases.

    :param project_id: UUID of the project.
    :requirement: URS-32.1 - Delete project.
    """
    user_id = request.headers.get(
        "X-User-ID", "SYSTEM"
    )
    store = ProjectStore.get_instance()
    deleted = store.delete_project(project_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Project '{project_id}' not found."
            ),
        )
    _file_log(
        user_id=user_id,
        action="NAVIGATOR_PROJECT_DELETED",
        details={"project_id": project_id},
    )


# -----------------------------------------------------------------
# Releases
# -----------------------------------------------------------------

@app.post(
    "/api/navigator/projects/{project_id}/releases",
    response_model=ReleaseOut,
    status_code=201,
    tags=["Navigator"],
    summary="Create a release with GAMP 5 folders",
)
async def create_release(
    project_id: str,
    payload: ReleaseIn,
    request: Request,
) -> ReleaseOut:
    """
    Create a versioned release inside a project.

    Auto-populates GAMP 5 standard folders unless a custom
    ``folder_template`` list is provided in the request body.

    :param project_id: Parent project UUID.
    :param payload: ReleaseIn body.
    :param request: FastAPI request for audit attribution.
    :return: Created ReleaseOut with empty folders.
    :requirement: URS-32.2 - Create release with folders.
    """
    user_id = request.headers.get(
        "X-User-ID", "SYSTEM"
    )
    store = ProjectStore.get_instance()
    try:
        rel = store.create_release(
            project_id=project_id,
            name=payload.name,
            version=payload.version,
            description=payload.description,
            status=payload.status,
            folder_template=payload.folder_template,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=str(exc)
        ) from exc

    _file_log(
        user_id=user_id,
        action="NAVIGATOR_RELEASE_CREATED",
        details={
            "project_id": project_id,
            "release_id": rel.release_id,
            "version": rel.version,
        },
    )
    return ReleaseOut(
        release_id=rel.release_id,
        name=rel.name,
        version=rel.version,
        status=rel.status,
        description=rel.description,
        created_at=rel.created_at,
        folders=rel.folders,
        item_count=0,
    )


@app.patch(
    "/api/navigator/projects/{project_id}"
    "/releases/{release_id}/status",
    status_code=204,
    tags=["Navigator"],
    summary="Update release status",
)
async def update_release_status(
    project_id: str,
    release_id: str,
    request: Request,
) -> None:
    """
    Update the lifecycle status of a release.

    Send ``{"status": "Released"}`` in the request body.

    :param project_id: Parent project UUID.
    :param release_id: Target release UUID.
    :requirement: URS-32.2 - Update release status.
    """
    user_id = request.headers.get(
        "X-User-ID", "SYSTEM"
    )
    body = await request.json()
    status = body.get("status", "")
    store = ProjectStore.get_instance()
    try:
        store.update_release_status(
            project_id=project_id,
            release_id=release_id,
            status=status,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=str(exc)
        ) from exc
    _file_log(
        user_id=user_id,
        action="NAVIGATOR_RELEASE_STATUS_UPDATED",
        details={
            "release_id": release_id,
            "status": status,
        },
    )


# -----------------------------------------------------------------
# Items
# -----------------------------------------------------------------

@app.post(
    "/api/navigator/projects/{project_id}"
    "/releases/{release_id}/items",
    response_model=ItemOut,
    status_code=201,
    tags=["Navigator"],
    summary="Add an item to a release folder",
)
async def add_item(
    project_id: str,
    release_id: str,
    payload: ItemIn,
    request: Request,
) -> ItemOut:
    """
    Add a validation artefact (requirement, test script,
    risk, etc.) to a folder within a release.

    :param project_id: Parent project UUID.
    :param release_id: Target release UUID.
    :param payload: ItemIn body including folder name.
    :param request: FastAPI request for audit attribution.
    :return: Created ItemOut.
    :requirement: URS-32.3 - Add item to folder.
    """
    user_id = request.headers.get(
        "X-User-ID", "SYSTEM"
    )
    store = ProjectStore.get_instance()
    try:
        item = store.add_item(
            project_id=project_id,
            release_id=release_id,
            folder=payload.folder,
            name=payload.name,
            item_type=payload.item_type,
            artifact_id=payload.artifact_id,
            notes=payload.notes,
            status=payload.status,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=str(exc)
        ) from exc

    _file_log(
        user_id=user_id,
        action="NAVIGATOR_ITEM_ADDED",
        details={
            "release_id": release_id,
            "folder": payload.folder,
            "item_id": item.item_id,
            "name": item.name,
        },
    )
    return ItemOut(
        item_id=item.item_id,
        name=item.name,
        item_type=item.item_type,
        status=item.status,
        artifact_id=item.artifact_id,
        notes=item.notes,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@app.patch(
    "/api/navigator/projects/{project_id}"
    "/releases/{release_id}"
    "/items/{item_id}/approve",
    response_model=ItemOut,
    tags=["Navigator"],
    summary="HITL-approve an item (FDA AI §3.2)",
)
async def approve_item(
    project_id: str,
    release_id: str,
    item_id: str,
    request: Request,
) -> ItemOut:
    """
    Mark an AI-generated artefact as human-approved.

    Clears the HITL (Human-in-the-Loop) badge in the React
    Navigator and sets item status to ``Approved``.  Logs a
    ``HITL_APPROVAL`` event to the 21 CFR Part 11 audit trail.

    Send ``{"folder": "<folder_name>"}`` in the request body
    to identify which folder contains the item.

    :param project_id: Parent project UUID.
    :param release_id: Parent release UUID.
    :param item_id: UUID of the item to approve.
    :param request: FastAPI request for audit attribution.
    :return: Updated ItemOut with status ``Approved``.
    :requirement: URS-32.6 - HITL approval with audit log.
    """
    user_id = request.headers.get(
        "X-User-ID", "SYSTEM"
    )
    body = await request.json()
    folder = body.get("folder", "")
    if not folder:
        raise HTTPException(
            status_code=422,
            detail=(
                "Request body must include 'folder' key."
            ),
        )

    store = ProjectStore.get_instance()
    try:
        store.update_item_status(
            project_id=project_id,
            release_id=release_id,
            folder=folder,
            item_id=item_id,
            status="Approved",
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=str(exc)
        ) from exc

    # Log HITL approval to 21 CFR Part 11 audit trail
    _file_log(
        user_id=user_id,
        action="HITL_APPROVAL",
        details={
            "project_id": project_id,
            "release_id": release_id,
            "folder": folder,
            "item_id": item_id,
            "compliance": "FDA AI Guidance 2026 §3.2",
        },
    )

    # Retrieve updated item to return
    proj = store.get_project(project_id)
    if proj is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Project '{project_id}' not found."
            ),
        )
    rel = proj.get_release(release_id)
    if rel is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Release '{release_id}' not found."
            ),
        )
    for it in rel.get_items(folder):
        if it.item_id == item_id:
            return ItemOut(
                item_id=it.item_id,
                name=it.name,
                item_type=it.item_type,
                status=it.status,
                artifact_id=it.artifact_id,
                notes=it.notes,
                created_at=it.created_at,
                updated_at=it.updated_at,
            )

    raise HTTPException(
        status_code=404,
        detail=f"Item '{item_id}' not found.",
    )


@app.post(
    "/api/navigator/projects/{project_id}"
    "/releases/{release_id}"
    "/items/{item_id}/move",
    response_model=ItemOut,
    tags=["Navigator"],
    summary="Move an item between folders or releases",
)
async def move_item(
    project_id: str,
    release_id: str,
    item_id: str,
    payload: MoveItemIn,
    request: Request,
) -> ItemOut:
    """
    Move a validation artefact to a different folder or
    release, atomically under the write lock.

    :param project_id: Parent project UUID.
    :param release_id: Source release UUID.
    :param item_id: UUID of the item to move.
    :param payload: MoveItemIn with src_folder, dst_release_id,
                    dst_folder.
    :param request: FastAPI request for audit attribution.
    :return: Moved ItemOut at its new location.
    :requirement: URS-32.4 - Move items between releases.
    """
    user_id = request.headers.get(
        "X-User-ID", "SYSTEM"
    )
    store = ProjectStore.get_instance()
    try:
        item = store.move_item(
            project_id=project_id,
            src_release_id=release_id,
            src_folder=payload.src_folder,
            item_id=item_id,
            dst_release_id=payload.dst_release_id,
            dst_folder=payload.dst_folder,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=str(exc)
        ) from exc

    _file_log(
        user_id=user_id,
        action="NAVIGATOR_ITEM_MOVED",
        details={
            "project_id": project_id,
            "item_id": item_id,
            "from": (
                f"{release_id}/{payload.src_folder}"
            ),
            "to": (
                f"{payload.dst_release_id}"
                f"/{payload.dst_folder}"
            ),
        },
    )
    return ItemOut(
        item_id=item.item_id,
        name=item.name,
        item_type=item.item_type,
        status=item.status,
        artifact_id=item.artifact_id,
        notes=item.notes,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@app.delete(
    "/api/navigator/projects/{project_id}"
    "/releases/{release_id}"
    "/items/{item_id}",
    status_code=204,
    tags=["Navigator"],
    summary="Delete an item from a release folder",
)
async def delete_item(
    project_id: str,
    release_id: str,
    item_id: str,
    request: Request,
) -> None:
    """
    Permanently delete an item from a release folder.

    Send ``{"folder": "<folder_name>"}`` in the request body.

    :param project_id: Parent project UUID.
    :param release_id: Parent release UUID.
    :param item_id: UUID of the item to delete.
    :requirement: URS-32.3 - Delete item.
    """
    user_id = request.headers.get(
        "X-User-ID", "SYSTEM"
    )
    body = await request.json()
    folder = body.get("folder", "")
    store = ProjectStore.get_instance()
    deleted = store.delete_item(
        project_id=project_id,
        release_id=release_id,
        folder=folder,
        item_id=item_id,
    )
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Item '{item_id}' not found.",
        )
    _file_log(
        user_id=user_id,
        action="NAVIGATOR_ITEM_DELETED",
        details={
            "release_id": release_id,
            "folder": folder,
            "item_id": item_id,
        },
    )


# -----------------------------------------------------------------
# Global Library
# -----------------------------------------------------------------

@app.get(
    "/api/navigator/library",
    response_model=List[LibraryEntryOut],
    tags=["Navigator"],
    summary="List Global Library entries",
)
async def list_library(
    entry_type: Optional[str] = None,
) -> List[LibraryEntryOut]:
    """
    Return Global Library entries, optionally filtered by
    ``entry_type`` query parameter
    (``system_description`` or ``risk_matrix``).

    :param entry_type: Optional filter by type.
    :return: List of LibraryEntryOut.
    :requirement: URS-32.5 - List Global Library.
    """
    store = ProjectStore.get_instance()
    return [
        LibraryEntryOut(
            entry_id=e.entry_id,
            name=e.name,
            entry_type=e.entry_type,
            content=e.content,
            tags=e.tags,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in store.list_library(
            entry_type=entry_type
        )
    ]


@app.post(
    "/api/navigator/library",
    response_model=LibraryEntryOut,
    status_code=201,
    tags=["Navigator"],
    summary="Add a Global Library entry",
)
async def add_library_entry(
    payload: LibraryEntryIn,
    request: Request,
) -> LibraryEntryOut:
    """
    Add a reusable System Description or Risk Matrix to the
    Global Library, shared across all projects.

    :param payload: LibraryEntryIn body.
    :param request: FastAPI request for audit attribution.
    :return: Created LibraryEntryOut.
    :requirement: URS-32.5 - Add Global Library entry.
    """
    user_id = request.headers.get(
        "X-User-ID", "SYSTEM"
    )
    store = ProjectStore.get_instance()
    entry = store.add_library_entry(
        name=payload.name,
        entry_type=payload.entry_type,
        content=payload.content,
        tags=payload.tags,
    )
    _file_log(
        user_id=user_id,
        action="NAVIGATOR_LIBRARY_ENTRY_ADDED",
        details={
            "entry_id": entry.entry_id,
            "name": entry.name,
            "entry_type": entry.entry_type,
        },
    )
    return LibraryEntryOut(
        entry_id=entry.entry_id,
        name=entry.name,
        entry_type=entry.entry_type,
        content=entry.content,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@app.delete(
    "/api/navigator/library/{entry_id}",
    status_code=204,
    tags=["Navigator"],
    summary="Delete a Global Library entry",
)
async def delete_library_entry(
    entry_id: str,
    request: Request,
) -> None:
    """
    Permanently delete a Global Library entry.

    :param entry_id: UUID of the entry to delete.
    :requirement: URS-32.5 - Delete Global Library entry.
    """
    user_id = request.headers.get(
        "X-User-ID", "SYSTEM"
    )
    store = ProjectStore.get_instance()
    deleted = store.delete_library_entry(entry_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Library entry '{entry_id}' not found."
            ),
        )
    _file_log(
        user_id=user_id,
        action="NAVIGATOR_LIBRARY_ENTRY_DELETED",
        details={"entry_id": entry_id},
    )


# =================================================================
# React Project Navigator — Static file serving
#
# The production build of react-navigator/ is served at /navigator.
# FastAPI routes defined above (/api/...) always take precedence
# over the static mount.
#
# To rebuild after UI changes:
#   cd react-navigator && npm run build
# =================================================================

_REACT_DIST = (
    Path(__file__).parent.parent
    / "react-navigator"
    / "dist"
)

_PLATFORM_DIST = (
    Path(__file__).parent.parent
    / "react-platform"
    / "dist"
)


@app.get(
    "/navigator",
    include_in_schema=False,
    tags=["Navigator"],
)
async def navigator_root() -> FileResponse:
    """
    Redirect bare /navigator to /navigator/ so relative
    asset paths resolve correctly.

    :requirement: URS-32.7 - Serve React Navigator from FastAPI.
    """
    return FileResponse(_REACT_DIST / "index.html")


if _REACT_DIST.exists():
    # Serve /navigator/assets/* and all other static files.
    # html=True makes StaticFiles return index.html for any
    # unmatched path, enabling React client-side navigation.
    app.mount(
        "/navigator",
        StaticFiles(directory=_REACT_DIST, html=True),
        name="react-navigator",
    )


# =================================================================
# EVOLV Platform Shell — Static file serving
#
# The production build of react-platform/ is served at /platform.
# This is the unified UI shell wrapping all EVOLV apps.
#
# To rebuild after UI changes:
#   cd react-platform && npm run build
# =================================================================

@app.get("/platform", include_in_schema=False)
async def platform_root() -> FileResponse:
    """
    Serve the EVOLV Platform Shell index for bare /platform path.

    :requirement: URS-33.1 - Serve Platform Shell from FastAPI.
    """
    return FileResponse(_PLATFORM_DIST / "index.html")


if _PLATFORM_DIST.exists():
    app.mount(
        "/platform",
        StaticFiles(directory=_PLATFORM_DIST, html=True),
        name="evolv-platform",
    )
