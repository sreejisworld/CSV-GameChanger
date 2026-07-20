"""
version_registry.py - Model & Version Registry for EVOLV.

Sprint 48 ("The Governable Vendor"). Answers the vendor-AI
governance dealbreaker question a pharma sponsor must ask:

    "How will we be notified when the model is updated?"

This module is the machine-readable registry of every moving
part in EVOLV - deterministic engines, LLM-backed components,
upstream foundation models, the regulatory corpus, and the eval
suite - plus an append-only, customer-facing CHANGELOG of
behaviour-relevant changes.

It also implements **upstream model drift detection**: EVOLV
itself consumes foundation models (OpenAI embeddings, Anthropic
judges) that can change without notice. When an API response
reports a model ID different from the declared one, that is an
UNGOVERNED CHANGE by our own governance standard - it is logged
to the chained audit trail and surfaced here. We hold our
suppliers to the bar our customers hold us to.

:requirement: URS-48.1 - Machine-readable component/version
              registry with customer-facing changelog.
:requirement: URS-48.2 - Upstream foundation-model drift
              detection logged as audit events.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REGISTRY_SCHEMA_VERSION = "1.0.0"

# Platform version: MAJOR.SPRINT.PATCH - the middle number is
# the EVOLV sprint that last shipped behaviour-relevant change.
EVOLV_PLATFORM_VERSION = "1.48.0"

# Where runtime model observations are persisted (append-only
# JSON lines). Not the audit trail - that gets the event; this
# keeps the raw observations for trending.
_PROJECT_ROOT = Path(__file__).parent.parent
OBSERVATIONS_PATH = (
    _PROJECT_ROOT / "output" / "model_observations.jsonl"
)

_obs_lock = threading.Lock()


# ── Component registry ──────────────────────────────────────────────
# kind: deterministic-engine | llm-engine | upstream-model |
#       corpus | harness | integrity
# The 'governed_by' field names the mechanism a customer can use
# to independently verify the component.

COMPONENT_REGISTRY: List[Dict[str, Any]] = [
    {
        "component": "RiskStrategist",
        "kind": "deterministic-engine",
        "version": "1.0.0",
        "description":
            "GAMP 5 risk matrix (RPN + patient-safety override).",
        "governed_by": "12 evals in Trusted Evals suite (CI)",
    },
    {
        "component": "DeltaAgent",
        "kind": "deterministic-engine",
        "version": "1.0.0",
        "description":
            "CSA test-script routing and step construction.",
        "governed_by": "7 evals in Trusted Evals suite (CI)",
    },
    {
        "component": "ChangeImpactAgent",
        "kind": "deterministic-engine",
        "version": "1.0.0",
        "description":
            "Change Impact Assessment via token-overlap matching.",
        "governed_by": "6 evals + Logic Archive per assessment",
    },
    {
        "component": "ValidatedStateEngine",
        "kind": "deterministic-engine",
        "version": "1.0.0",
        "description":
            "Per-UR validated-state confidence scoring.",
        "governed_by": "5 evals + Logic Archive per assessment",
    },
    {
        "component": "BAP Exclusion Rules",
        "kind": "deterministic-engine",
        "version": "1.1.0",
        "description":
            "Five hard exclusion rules (BAP-X). v1.1.0 = Sprint "
            "44 hardening (subject widening, clause bounding).",
        "governed_by": "95 evals incl. generated adversarial set",
    },
    {
        "component": "IntegrityManager audit chain",
        "kind": "integrity",
        "version": "2.0.0",
        "description":
            "SHA-256 hash-chained audit trail (v2 = chained "
            "rows, Sprint 45). Logic Archive schema 1.0.0.",
        "governed_by":
            "verify_audit_chain() - CLI, API, and 6 evals",
    },
    {
        "component": "RequirementArchitect",
        "kind": "llm-engine",
        "version": "1.0.0",
        "description":
            "URS drafting via RAG over the regulatory corpus. "
            "Deterministic transform to UR/FR.",
        "governed_by":
            "10 golden evals + independent VerificationAgent "
            "review of every draft",
    },
    {
        "component": "VerificationAgent",
        "kind": "llm-engine",
        "version": "1.0.0",
        "description":
            "Independent review of drafts against the corpus; "
            "rejections logged as Compliance Exceptions.",
        "governed_by": "Audit-trail COMPLIANCE_EXCEPTION events",
    },
    {
        "component": "OpenAI text-embedding-3-small",
        "kind": "upstream-model",
        "version": "text-embedding-3-small",
        "description":
            "Embedding model for corpus retrieval. Supplied by "
            "OpenAI; subject to upstream change.",
        "governed_by":
            "Runtime model-ID observation (URS-48.2); mismatch "
            "raises UPSTREAM_MODEL_CHANGED audit event",
    },
    {
        "component": "Anthropic judge model",
        "kind": "upstream-model",
        "version": "claude-haiku-4-5-20251001",
        "description":
            "Optional LLM-as-judge in the eval suite. Pinned "
            "model ID; deterministic checks stand alone.",
        "governed_by":
            "Runtime model-ID observation (URS-48.2)",
    },
    {
        "component": "Regulatory corpus",
        "kind": "corpus",
        "version": "per-document reg_version metadata",
        "description":
            "GAMP 5 / 21 CFR Part 11 / EU Annex 11 / ICH Q9 "
            "chunks; every citation carries its reg_version.",
        "governed_by":
            "CORPUS_VERSION_BUMPED audit events + drift "
            "detection at ingestion, query, and verification",
    },
    {
        "component": "Trusted Evals suite",
        "kind": "harness",
        "version": REGISTRY_SCHEMA_VERSION,
        "description":
            "131 deterministic evals across 6 agents; runs in "
            "CI on every push and on demand from the Dev Portal.",
        "governed_by": "CI gate (blocking) + signed run reports",
    },
]


# ── Customer-facing changelog (append-only) ─────────────────────────
# Every entry is a behaviour-relevant change a deployed customer
# would want notified about. Newest first.

VERSION_CHANGELOG: List[Dict[str, str]] = [
    {
        "date": "2026-07-20",
        "component": "Platform / compliance gate",
        "change":
            "CI compliance gate rewritten (AST-based URS-tag "
            "verification); 35 traceability tags added.",
        "impact": "No runtime behaviour change.",
        "sprint": "47",
    },
    {
        "date": "2026-07-16",
        "component": "Dependencies",
        "change":
            "13 third-party packages upgraded for known CVEs; "
            "security floors pinned; pip-audit added to CI.",
        "impact": "No functional behaviour change.",
        "sprint": "46",
    },
    {
        "date": "2026-07-16",
        "component": "IntegrityManager audit chain",
        "change":
            "Audit rows now hash-chained (v2.0.0). Row format "
            "unchanged; hash semantics upgraded. Legacy rows "
            "verify under the original formula.",
        "impact":
            "Stronger tamper evidence; verification tooling "
            "added (CLI + API).",
        "sprint": "45",
    },
    {
        "date": "2026-07-12",
        "component": "BAP Exclusion Rules",
        "change":
            "v1.1.0 - subject widened to (ai|llm|model), "
            "clause-bounded matching, British verb forms, "
            "'without review' suppressor fix. Found by the "
            "eval suite (11 gaps), fixed same day.",
        "impact":
            "Screening verdicts may differ from v1.0.0 on "
            "edge-case phrasings - in the safe direction.",
        "sprint": "44",
    },
    {
        "date": "2026-07-12",
        "component": "Platform security",
        "change":
            "App-wide API-key gate, input length limits, "
            "filename sanitisation, CORS allow-list.",
        "impact":
            "Deployments must set EVOLV_API_KEY + "
            "EVOLV_CORS_ORIGINS in production.",
        "sprint": "43",
    },
]


def get_registry() -> Dict[str, Any]:
    """Return the full version registry snapshot.

    :return: Dict with schema/platform versions, component
             list, changelog, and generation timestamp.
    :requirement: URS-48.1 - Machine-readable version registry.
    """
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "platform_version": EVOLV_PLATFORM_VERSION,
        "generated_at":
            datetime.now(timezone.utc).isoformat(),
        "components": COMPONENT_REGISTRY,
        "changelog": VERSION_CHANGELOG,
        "notification_commitment": (
            "Behaviour-relevant changes are recorded in this "
            "changelog before or with release. Upstream "
            "foundation-model changes detected at runtime are "
            "logged as UPSTREAM_MODEL_CHANGED audit events. "
            "Deployed customers receive the changelog with "
            "every platform update."
        ),
    }


def get_declared_model(component: str) -> Optional[str]:
    """Return the declared version/model ID for a component.

    :param component: Registry component name.
    :return: Declared version string, or None if unknown.
    :requirement: URS-48.2 - Upstream model drift detection.
    """
    for entry in COMPONENT_REGISTRY:
        if entry["component"] == component:
            return str(entry["version"])
    return None


def record_model_observation(
    component: str,
    observed_model: str,
) -> bool:
    """Record a runtime model-ID observation and flag drift.

    Call this with the model ID reported by an upstream API
    response. If it differs from the declared registry entry,
    the mismatch is an UNGOVERNED CHANGE: it is appended to the
    chained audit trail (UPSTREAM_MODEL_CHANGED) and persisted
    to the observations log for trending.

    :param component: Registry component name (e.g.
                      "Anthropic judge model").
    :param observed_model: Model ID reported by the API.
    :return: True when observation matches the declaration,
             False when drift was detected and logged.
    :requirement: URS-48.2 - Upstream foundation-model drift
                  detection logged as audit events.
    """
    declared = get_declared_model(component)
    matches = (declared is not None
               and observed_model == declared)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "declared": declared,
        "observed": observed_model,
        "match": matches,
    }
    with _obs_lock:
        OBSERVATIONS_PATH.parent.mkdir(
            parents=True, exist_ok=True,
        )
        with open(
            OBSERVATIONS_PATH, "a", encoding="utf-8",
        ) as f:
            f.write(json.dumps(record) + "\n")

    if not matches:
        # Late import avoids a cycle at module load.
        from Agents.integrity_manager import log_audit_event
        log_audit_event(
            agent_name="VersionRegistry",
            action="UPSTREAM_MODEL_CHANGED",
            decision_logic=(
                f"{component}: declared "
                f"'{declared}', observed "
                f"'{observed_model}'. Ungoverned upstream "
                "change - review before relying on affected "
                "outputs."
            ),
        )
    return matches
