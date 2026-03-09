"""
EVOLV API — OpenAPI 3.0 Pydantic Schema Registry.

Centralises all request/response models so ``main.py`` stays thin
and every new endpoint can import its types from one place.

Field descriptions are pulled from the active ``ConfigService``
so tenant-specific label overrides (e.g. "User Need" instead of
"Requirement") appear correctly in the generated ``/docs`` UI.

:requirement: URS-27.1 - System shall expose interactive OpenAPI
              docs at /docs.
:requirement: URS-27.2 - All endpoints shall use typed Pydantic
              schemas with MetadataDictionary-sourced labels.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from Agents.metadata_mapper import ConfigService


def _lbl(key: str) -> str:
    """
    Return the tenant-specific label for an internal key.

    Delegates to the ConfigService singleton so all Swagger
    field descriptions reflect the active nomenclature map.

    :param key: Internal label key (e.g. "requirement").
    :return: Display label string.
    :requirement: URS-27.2
    """
    return ConfigService.get_instance().label(key)


# -----------------------------------------------------------------
# Requirement schemas
# -----------------------------------------------------------------

class RequirementIn(BaseModel):
    """
    Input body for single-requirement generation.

    :requirement: URS-27.2
    """

    text: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description=(
            f"Plain-English {_lbl('requirement')} statement "
            "to generate a URS document from."
        ),
        examples=["The system shall track warehouse temperature."],
    )
    min_score: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum Pinecone similarity score for GAMP 5 "
            "context retrieval."
        ),
    )
    expert_mode: bool = Field(
        default=False,
        description=(
            "When True, skip Pinecone lookup and use "
            "deterministic logic only."
        ),
    )
    additional_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional project context (system_description, "
            "workshop_notes, roles_and_permissions, "
            "lucidchart_url)."
        ),
    )


class RequirementOut(BaseModel):
    """
    Output of a single-requirement URS generation.

    :requirement: URS-27.2
    """

    urs_id: str = Field(
        ...,
        description=f"{_lbl('urs')} identifier.",
    )
    requirement_statement: str = Field(
        ...,
        description=f"Formatted {_lbl('requirement')} statement.",
    )
    criticality: Literal["High", "Medium", "Low"] = Field(
        ...,
        description="GAMP 5 criticality classification.",
    )
    regulatory_rationale: str = Field(
        ...,
        description="Regulatory rationale with citation.",
    )
    reg_versions_cited: List[str] = Field(
        default_factory=list,
        description="Regulatory document versions cited.",
    )
    sandbox: bool = Field(
        default=False,
        description=(
            "True when request was processed in Sandbox mode — "
            "result is not committed to production records."
        ),
    )


# -----------------------------------------------------------------
# Sentinel / blast-radius schemas
# -----------------------------------------------------------------

class ImpactItemOut(BaseModel):
    """Single impacted item in a blast-radius report."""

    item_id: str
    item_type: str
    title: str
    severity: Literal["Red", "Yellow", "Green"]
    tier: int
    reason: str
    linked_requirement: str


class SentinelReportOut(BaseModel):
    """
    Rich Sentinel blast-radius report.

    :requirement: URS-27.2
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
        ...,
        ge=0,
        le=100,
        description="Composite impact score (0–100).",
    )
    rationalization_log: str = Field(
        ...,
        description="Natural-language audit of Sentinel decisions.",
    )
    generated_at: str
    blast_radius_json: Dict[str, Any]
    impacted_items: List[ImpactItemOut]
    sandbox: bool = Field(default=False)


# -----------------------------------------------------------------
# Bulk processing schemas
# -----------------------------------------------------------------

class BulkValidateRequest(BaseModel):
    """
    Batch validation request — up to 500 requirements.

    :requirement: URS-30.1 - System shall accept batch
                  requirement submissions.
    """

    requirements: List[RequirementIn] = Field(
        ...,
        min_length=1,
        max_length=500,
        description=(
            f"List of {_lbl('requirement')} items to validate. "
            "Maximum 500 per request."
        ),
    )
    expert_mode: bool = Field(
        default=False,
        description=(
            "Apply expert (deterministic) mode to all items."
        ),
    )


class BulkStatusResponse(BaseModel):
    """
    Job status and partial results for a bulk validate job.

    :requirement: URS-30.2 - System shall track per-item progress.
    :requirement: URS-30.3 - System shall expose job status via GET.
    """

    job_id: str = Field(
        ..., description="Unique job identifier."
    )
    status: Literal[
        "queued", "running", "complete", "failed"
    ] = Field(..., description="Current job state.")
    total: int = Field(
        ...,
        description=f"Total {_lbl('requirement')} items submitted.",
    )
    completed: int = Field(
        ..., description="Items processed so far."
    )
    progress_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage complete.",
    )
    results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Partial or complete results.",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if status is 'failed'.",
    )
    sandbox: bool = Field(default=False)


# -----------------------------------------------------------------
# Webhook schemas
# -----------------------------------------------------------------

class WebhookRegistrationIn(BaseModel):
    """
    Request body for registering an outbound webhook.

    :requirement: URS-28.1 - System shall allow tenants to
                  register webhooks for EVOLV events.
    """

    tenant_id: str = Field(
        ...,
        min_length=1,
        max_length=80,
        description="Tenant identifier.",
        examples=["pharma-corp-001"],
    )
    url: str = Field(
        ...,
        min_length=8,
        description="HTTPS endpoint to receive event payloads.",
        examples=["https://hooks.my-lims.com/evolv"],
    )
    events: List[str] = Field(
        ...,
        min_length=1,
        description=(
            "Event names to subscribe to, e.g. "
            "['SENTINEL_SCAN_COMPLETED', 'BULK_VALIDATE_COMPLETE']."
        ),
        examples=[["SENTINEL_SCAN_COMPLETED"]],
    )
    secret: str = Field(
        ...,
        min_length=16,
        max_length=128,
        description=(
            "Shared secret for HMAC-SHA256 payload signing. "
            "Shown only at registration; store securely."
        ),
        examples=["my-super-secret-key-32chars-long!!"],
    )

    @field_validator("url")
    @classmethod
    def _https_only(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError(
                "Webhook URL must use HTTPS."
            )
        return v


class WebhookRegistrationOut(BaseModel):
    """
    Response after successful webhook registration.

    :requirement: URS-28.1
    """

    webhook_id: str
    tenant_id: str
    url: str
    events: List[str]
    created_at: str
    active: bool


# -----------------------------------------------------------------
# API Key schemas
# -----------------------------------------------------------------

class ScopedAPIKeyIn(BaseModel):
    """
    Request body for creating a scoped API key.

    :requirement: URS-29.1 - API keys must be linked to a
                  Tenant_ID and a DAC policy.
    """

    tenant_id: str = Field(
        ...,
        min_length=1,
        max_length=80,
        description="Tenant this key belongs to.",
        examples=["pharma-corp-001"],
    )
    scopes: List[str] = Field(
        ...,
        min_length=1,
        description=(
            "Permission scopes. Use 'audit_only' to restrict "
            "to read-only audit access. Other scopes: "
            "'requirements', 'sentinel', 'bulk', 'admin'."
        ),
        examples=[["audit_only"]],
    )
    dac_policy: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional DAC policy dict forwarded to PolicyEngine "
            "for attribute-based access decisions."
        ),
    )


class ScopedAPIKeyOut(BaseModel):
    """
    Response after API key creation.  The raw key is shown
    exactly once; it cannot be recovered afterwards.

    :requirement: URS-29.1
    """

    key_id: str
    tenant_id: str
    scopes: List[str]
    raw_key: Optional[str] = Field(
        default=None,
        description=(
            "Raw API key — shown only at creation. "
            "Store securely and treat as a password."
        ),
    )
    created_at: str
    active: bool
