"""
SMART Requirements Engine — GxP Requirements Authoring Agent.

Guides users through fourteen GxP requirement categories, rewrites vague
input to SMART format via LLM (Claude preferred, OpenAI fallback), and
enforces FDA/EMA 2026 AI Guidance compliance by auto-generating Negative
Test Scenarios for high-risk requirements.

The engine supports two public methods:
  - ``refine_to_smart()``  — original 5-section interface (backward compat)
  - ``transform_to_smart()`` — full 14-category engine with context fields

:requirement: URS-21.1  - Accept multi-section requirement input.
:requirement: URS-21.2  - Detect FDA/EMA 2026 AI triggers.
:requirement: URS-21.3  - Rewrite vague text to SMART format.
:requirement: URS-21.4  - Generate Negative Test Scenarios.
:requirement: URS-21.5  - Support LLM and deterministic modes.
:requirement: URS-21.16 - Produce per-section SmartSection output.
:requirement: URS-21.17 - Return full SmartPackage result.
"""
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from Agents.integrity_manager import log_audit_event as _log

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

try:
    import anthropic as _anthropic_sdk
except ImportError:
    _anthropic_sdk = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_LLM_MODEL = "gpt-4o"
_CLAUDE_MODEL = "claude-sonnet-4-6"

# FDA/EMA 2026 AI Guidance trigger keyword sets
FDA_EMA_2026_TRIGGERS: Dict[str, List[str]] = {
    "AI Inference": [
        "ai", "ml", "machine learning", "model",
        "inference", "neural", "llm", "predict",
        "classify", "score",
    ],
    "Automated Decision": [
        "automated decision", "auto-approve",
        "autonomous", "without human review",
        "decision support", "algorithmic",
    ],
    "Patient Safety": [
        "patient", "clinical", "adverse event",
        "life-sustaining", "life-supporting", "dosing",
        "diagnosis", "treatment", "pharmacovigilance",
        "safety signal",
    ],
    "Bias Monitoring": [
        "bias", "fairness", "demographic", "equity",
        "disparity", "protected attribute",
    ],
    "PCCP": [
        "pccp", "predetermined change control", "model update",
        "retraining", "drift", "continuous learning",
    ],
}

# GxP Negative Test templates — one per FDA/EMA trigger category
_NEGATIVE_TEST_TEMPLATES: Dict[str, str] = {
    "AI Inference": (
        "Given out-of-distribution or adversarial input, "
        "when the AI/ML model processes the request, "
        "then the system shall reject or quarantine the input, "
        "log the anomaly to the audit trail, and NOT produce "
        "a clinical or regulatory decision without human review."
    ),
    "Automated Decision": (
        "Given conflicting or incomplete data presented to the "
        "automated decision engine, when the auto-decision "
        "threshold is reached, then the system shall escalate "
        "to a human reviewer rather than proceeding autonomously, "
        "and shall log the escalation event."
    ),
    "Patient Safety": (
        "Given a value outside validated clinical limits, "
        "when the safety-critical function is invoked, "
        "then the system shall halt processing, trigger an alert "
        "to responsible personnel, and log the safety override "
        "event per 21 CFR Part 11."
    ),
    "Bias Monitoring": (
        "Given two equivalent patient cohorts differing only "
        "in a protected demographic attribute, when the model "
        "generates predictions, then the disparity in output "
        "scores shall not exceed the pre-defined fairness "
        "threshold (demographic parity difference <= 0.05)."
    ),
    "PCCP": (
        "Given a PCCP model update deployed to production, "
        "when post-deployment performance monitoring detects "
        "metric degradation beyond the PCCP-specified drift "
        "threshold, then the system shall automatically rollback "
        "to the last approved model version and notify the "
        "validation team within 24 hours."
    ),
}

# Vague-word substitution map for deterministic refinement
_VAGUE_SUBSTITUTIONS: List[tuple] = [
    (r"\bshould\b", "shall"),
    (r"\bfast\b", "within 2 000 ms at P95"),
    (r"\bquickly\b", "within 2 000 ms at P95"),
    (r"\beasy\b", "achievable in <= 3 steps"),
    (r"\buser-friendly\b", "conforming to WCAG 2.1 AA"),
    (r"\bintuitive\b", "requiring no training beyond onboarding SOP"),
    (r"\brobust\b", "with >= 99.5% monthly uptime SLA"),
    (r"\bseamless\b", "without interruption of service"),
    (r"\bappropriate\b", "as defined in the validated specification"),
    (r"\badequate\b", "meeting the minimum threshold in Annex I"),
    (r"\btimely\b", "within the SLA-defined response window"),
    (r"\befficient\b", "consuming <= defined resource budget"),
    (r"\bflexible\b", "configurable without code changes"),
    (r"\bas needed\b", "per documented business rules"),
    (r"\bminimal\b", "not exceeding the validated threshold"),
    (r"\bproper\b", "per the applicable SOP"),
    (r"\bsufficient\b", "meeting the acceptance criteria"),
    (r"\ball\b", "every"),
    (r"\betc\.?\b", "(see Appendix A for full list)"),
    (r"\breasonable\b", "documented and risk-based"),
    # Modal-verb cleanup (before shall-prefix applied)
    (r"\bneeds to\b", ""),
    (r"\bhas to\b", ""),
    (r"\bmust be\b", "shall be"),
    (r"\bmust\b", "shall"),
]

# High-risk keywords for deterministic fallback classification
_HIGH_RISK_KW = {
    "patient", "safety", "sterile", "batch", "release",
    "audit", "validation", "gxp", "regulatory", "fda", "ema",
    "compliance", "traceability", "21 cfr", "adverse", "clinical",
    "pharmacovigilance", "life-sustaining", "life-supporting",
}

# Medium-risk keywords
_MEDIUM_RISK_KW = {
    "quality", "capa", "deviation", "change control",
    "training", "document", "temperature", "inventory",
    "calibration", "sop", "report", "export", "access",
    "authentication", "encryption", "backup", "recovery",
}

# SMART guidance help text — 5 original sections (backward compat)
SMART_HELP_TEXT: Dict[str, Dict[str, str]] = {
    "Operational": {
        "Availability": (
            "Specify >= 99.5% uptime SLA measured monthly. "
            "Reference 21 CFR 211.68 for computerised systems."
        ),
        "Throughput": (
            "Define peak TPS with units. "
            "e.g. >= 500 req/min sustained over 1-hour load test."
        ),
        "Response Time": (
            "State P95 latency. "
            "e.g. <= 2 000 ms at P95 under 200 concurrent users."
        ),
        "User Workflow": (
            "Name role + steps. "
            "e.g. <= 3 clicks from dashboard for Analyst role."
        ),
    },
    "Data": {
        "Archiving": (
            "Cite 21 CFR 211.68 — >= 7-year retention for GxP records."
        ),
        "Readability": "PDF/A-1b or HL7 FHIR R4 open formats.",
        "Integrity": "SHA-256 checksum; ALCOA+ compliance required.",
        "Backup & Recovery": "RTO/RPO in hours (RTO 4h, RPO 1h).",
    },
    "Technical": {
        "API Versioning": "semver 2.0; prior version >= 6 months.",
        "Scalability": ">= 200 concurrent; <= 5% P95 degradation.",
        "Integration SLAs": "Timeout 30s; retry <= 3x back-off.",
        "Monitoring": "/health 200ms; alert >= 3 failures.",
    },
    "Security": {
        "Authentication": "TOTP MFA; NIST SP 800-63B AAL2.",
        "RBAC": ">= 4 roles; Privilege Matrix as GxP doc.",
        "Encryption": "AES-256 at rest; TLS 1.3 in transit.",
        "Audit Trail": "21 CFR Part 11.10(e): append-only log.",
    },
    "Lifecycle": {
        "Deployment": "Zero-downtime rolling; rollback RTO <= 4h.",
        "Versioning": "semver MAJOR.MINOR.PATCH; signed tags.",
        "Decommissioning": "GxP records migrated within 90 days.",
        "Change Management": "CAB sign-off + impact assessment.",
    },
}

# ---------------------------------------------------------------------------
# 14 GxP Requirement Types — definitions, examples, GAMP 5 refs, help content
# ---------------------------------------------------------------------------
REQUIREMENT_TYPES: Dict[str, Dict[str, Any]] = {
    "Functional": {
        "number": "01",
        "icon": "\u2699",
        "tagline": "What the system must DO",
        "definition": (
            "Functional requirements define specific behaviours, "
            "features, and capabilities the system must perform. "
            "Each describes an observable action or response to "
            "a trigger or event."
        ),
        "examples": [
            "The system shall create an electronic batch record "
            "upon initiation of a manufacturing order.",
            "The system shall prevent batch release if any "
            "out-of-specification result remains unresolved.",
            "The system shall send a QA alert within 60 seconds "
            "of a critical deviation being raised.",
        ],
        "gamp5_ref": "GAMP 5, 5th Ed. \u00a73.2 \u2014 Software Categorisation",
        "ai_triggers": [
            "automated", "auto-", "decision", "predict",
            "recommend", "classify", "model",
        ],
        "pitfalls": [
            "Vague verbs (handle, manage) \u2014 use specific actions.",
            "Missing actor \u2014 specify what triggers the function.",
        ],
    },
    "Operational": {
        "number": "02",
        "icon": "\U0001f504",
        "tagline": "Day-to-day runtime and user workflows",
        "definition": (
            "Operational requirements cover availability, uptime "
            "SLAs, and day-to-day workflows users must complete "
            "in steady-state production use."
        ),
        "examples": [
            "The system shall achieve >= 99.5% monthly uptime, "
            "excluding scheduled maintenance windows.",
            "The system shall allow a Lab Analyst to complete a "
            "sample result entry in <= 3 screen interactions.",
            "Scheduled maintenance windows shall not exceed "
            "4 hours per calendar month.",
        ],
        "gamp5_ref": "GAMP 5 \u00a77.1 \u2014 Operational Use",
        "ai_triggers": ["auto-schedule", "automated workflow"],
        "pitfalls": [
            "Uptime without measurement window \u2014 specify monthly.",
            "No SLA owner defined \u2014 name the responsible team.",
        ],
    },
    "Performance": {
        "number": "03",
        "icon": "\u26a1",
        "tagline": "Speed, throughput and capacity",
        "definition": (
            "Performance requirements specify measurable speed, "
            "throughput, capacity, and reliability targets under "
            "expected and peak load conditions."
        ),
        "examples": [
            "The system shall return search results in <= 2 000 ms "
            "at P95 under 200 concurrent users.",
            "The system shall support >= 500 API requests/minute "
            "sustained over a 1-hour load test.",
            "The system shall recover from a single-node failure "
            "within 30 seconds without data loss.",
        ],
        "gamp5_ref": "GAMP 5 Appendix M4 \u2014 Performance Testing",
        "ai_triggers": ["inference time", "model latency", "batch scoring"],
        "pitfalls": [
            "No percentile stated \u2014 always specify P95 or P99.",
            "No baseline load \u2014 state concurrent user count.",
        ],
    },
    "Data": {
        "number": "04",
        "icon": "\U0001f5c4",
        "tagline": "Retention, integrity and ALCOA+",
        "definition": (
            "Data requirements govern retention periods, archiving "
            "formats, integrity controls (ALCOA+), and backup and "
            "recovery procedures for all GxP records."
        ),
        "examples": [
            "The system shall retain GxP electronic records for "
            "a minimum of 7 years per 21 CFR 211.68.",
            "The system shall verify SHA-256 checksums on every "
            "data export and log mismatches to the audit trail.",
            "The system shall achieve RTO <= 4 h and RPO <= 1 h "
            "for GxP data restoration.",
        ],
        "gamp5_ref": "GAMP 5 App. A3.4; 21 CFR 211.68; ALCOA+",
        "ai_triggers": [
            "training data", "model data", "prediction logs",
            "dataset", "ml pipeline",
        ],
        "pitfalls": [
            "No retention period \u2014 cite applicable regulation.",
            "Backup not validated \u2014 include restoration test.",
        ],
    },
    "Security": {
        "number": "05",
        "icon": "\U0001f512",
        "tagline": "Access control, encryption and Part 11",
        "definition": (
            "Security requirements cover authentication, role-based "
            "access control, encryption standards, and the audit "
            "trail mandated by 21 CFR Part 11."
        ),
        "examples": [
            "The system shall enforce TOTP MFA for every user, "
            "meeting NIST SP 800-63B AAL2.",
            "The system shall encrypt all GxP data at rest using "
            "AES-256 and in transit using TLS 1.3.",
            "The system shall maintain >= 4 RBAC roles with a "
            "Privilege Matrix as a controlled document.",
        ],
        "gamp5_ref": "GAMP 5 App. A3.3; 21 CFR Part 11.10",
        "ai_triggers": [
            "ai api key", "model access", "api security",
        ],
        "pitfalls": [
            "MFA without assurance level \u2014 cite NIST AAL.",
            "TLS without version \u2014 specify TLS 1.3 minimum.",
        ],
    },
    "Integration": {
        "number": "06",
        "icon": "\U0001f517",
        "tagline": "APIs, interfaces and data exchange",
        "definition": (
            "Integration requirements describe all APIs, external "
            "system connections, data exchange protocols, and "
            "error-handling behaviours for interfaces."
        ),
        "examples": [
            "The system shall expose a versioned REST API (semver "
            "2.0) with the prior major version supported >= 6 "
            "months after deprecation notice.",
            "The system shall implement a 30-second timeout and "
            "exponential back-off with <= 3 retries for all "
            "outbound API calls.",
        ],
        "gamp5_ref": "GAMP 5 \u00a76.7 \u2014 Interface Specification",
        "ai_triggers": [
            "ai api", "model endpoint", "prediction service",
            "ml api", "external model",
        ],
        "pitfalls": [
            "No version lifecycle \u2014 define deprecation notice period.",
            "No error handling \u2014 specify retry and circuit-breaker.",
        ],
    },
    "User Interface": {
        "number": "07",
        "icon": "\U0001f5a5",
        "tagline": "UI standards, accessibility and workflows",
        "definition": (
            "UI requirements define accessibility standards, "
            "usability targets, user workflow constraints, and "
            "interface design guidelines."
        ),
        "examples": [
            "The system shall conform to WCAG 2.1 Level AA for "
            "every user-facing screen.",
            "The system shall allow a Reviewer to approve a batch "
            "record in <= 3 sequential screen interactions.",
        ],
        "gamp5_ref": "GAMP 5 App. A3.2 \u2014 Interface Design",
        "ai_triggers": [
            "ai-assisted ui", "recommendation widget",
            "ai chatbot", "copilot",
        ],
        "pitfalls": [
            "No accessibility standard \u2014 specify WCAG level.",
            "No user role defined \u2014 specify who performs the task.",
        ],
    },
    "Regulatory Compliance": {
        "number": "08",
        "icon": "\U0001f4dc",
        "tagline": "FDA, EMA, ICH Q10 and GAMP 5 mandates",
        "definition": (
            "Regulatory compliance requirements are derived from "
            "applicable regulations and guidance documents. "
            "Each requirement must cite the specific clause."
        ),
        "examples": [
            "The system shall comply with 21 CFR Part 11 \u00a711.10 "
            "for all electronic records and signatures.",
            "The system shall comply with EU Annex 11 for "
            "computerised systems in GMP environments.",
            "The system shall support GAMP 5 Category 4 "
            "configured product validation approach.",
        ],
        "gamp5_ref": "GAMP 5 \u00a72 \u2014 Regulatory Overview",
        "ai_triggers": [
            "samd", "ai regulation", "2026 ai guidance",
            "fda ai", "ema ai",
        ],
        "pitfalls": [
            "Citing regulation without specific clause.",
            "No regulatory version or year cited.",
        ],
    },
    "Audit & Traceability": {
        "number": "09",
        "icon": "\U0001f50d",
        "tagline": "Audit trail, e-signatures and data lineage",
        "definition": (
            "Audit and traceability requirements ensure all GxP "
            "actions are recorded with who, what, when, and "
            "before/after values; e-signatures comply with "
            "21 CFR Part 11."
        ),
        "examples": [
            "The system shall maintain an append-only audit trail "
            "recording user ID, action, UTC timestamp, and "
            "before/after values for every GxP record change.",
            "The system shall capture e-signatures with name, "
            "date/time, and meaning per 21 CFR Part 11.50.",
        ],
        "gamp5_ref": "GAMP 5 App. A3.6; 21 CFR Part 11.10(e)",
        "ai_triggers": [
            "ai decision audit", "model prediction audit",
            "automated action log",
        ],
        "pitfalls": [
            "No before/after values \u2014 required for GxP changes.",
            "Timestamp without UTC \u2014 always specify timezone.",
        ],
    },
    "Configuration Management": {
        "number": "10",
        "icon": "\U0001f527",
        "tagline": "Config control and parameter validation",
        "definition": (
            "Configuration management requirements ensure all "
            "system parameters are version-controlled, validated "
            "before deployment, and subject to change control."
        ),
        "examples": [
            "The system shall store all GxP configuration "
            "parameters in a version-controlled repository with "
            "a change approval workflow.",
            "The system shall validate configuration parameters "
            "against a defined acceptable range before deployment.",
        ],
        "gamp5_ref": "GAMP 5 \u00a78 \u2014 Configuration Management",
        "ai_triggers": [
            "model hyperparameter", "ai configuration",
            "ml config", "model parameter",
        ],
        "pitfalls": [
            "Config not version-controlled \u2014 required for GxP.",
            "No change impact assessment required.",
        ],
    },
    "Reporting & Analytics": {
        "number": "11",
        "icon": "\U0001f4ca",
        "tagline": "Reports, exports and dashboards",
        "definition": (
            "Reporting requirements define report formats, export "
            "standards, dashboard capabilities, and submission "
            "requirements for regulatory agencies."
        ),
        "examples": [
            "The system shall export batch records in PDF/A-1b "
            "format with a digital signature.",
            "The system shall generate a GAMP 5-compliant "
            "Validation Summary Report on demand.",
        ],
        "gamp5_ref": "GAMP 5 App. A3.5 \u2014 Reporting",
        "ai_triggers": [
            "ai-generated report", "predictive analytics",
            "ml dashboard", "automated report",
        ],
        "pitfalls": [
            "No output format standard \u2014 specify PDF/A or FHIR.",
            "No approval workflow for GxP reports.",
        ],
    },
    "Training & Support": {
        "number": "12",
        "icon": "\U0001f393",
        "tagline": "User training, SOPs and qualification",
        "definition": (
            "Training requirements define user training curricula, "
            "SOP documentation, qualification activities, and "
            "ongoing competency assessment."
        ),
        "examples": [
            "The system shall require completion of a 4-hour "
            "onboarding training programme before system access.",
            "The system shall maintain training records per user "
            "as controlled GxP documents.",
        ],
        "gamp5_ref": "GAMP 5 \u00a710 \u2014 Training",
        "ai_triggers": [
            "ai system training for users",
            "model explainability training",
        ],
        "pitfalls": [
            "No training record requirement \u2014 records are GxP docs.",
            "No qualification criteria \u2014 define pass/fail thresholds.",
        ],
    },
    "Technical Infrastructure": {
        "number": "13",
        "icon": "\U0001f3d7",
        "tagline": "Architecture, scalability and monitoring",
        "definition": (
            "Technical infrastructure requirements cover system "
            "architecture, scalability, health monitoring, "
            "alerting, and deployment pipeline standards."
        ),
        "examples": [
            "The system shall expose a /health endpoint returning "
            "HTTP 200 in <= 200 ms; alert after >= 3 failures.",
            "The system shall support >= 200 concurrent users "
            "with <= 5% P95 latency degradation vs baseline.",
        ],
        "gamp5_ref": "GAMP 5 \u00a76.3 \u2014 Infrastructure Qualification",
        "ai_triggers": [
            "gpu infrastructure", "model hosting", "mlops",
            "model serving", "ai compute",
        ],
        "pitfalls": [
            "No scalability metric \u2014 define concurrent user count.",
            "No alerting threshold \u2014 specify failure count.",
        ],
    },
    "Lifecycle Management": {
        "number": "14",
        "icon": "\u267b",
        "tagline": "Deployment, change control and decommissioning",
        "definition": (
            "Lifecycle management requirements cover deployment "
            "procedures, versioning conventions, change control, "
            "and decommissioning including GxP data migration."
        ),
        "examples": [
            "The system shall use semver MAJOR.MINOR.PATCH with "
            "signed, immutable release tags in VCS.",
            "The system shall complete GxP record migration "
            "within 90 days of decommissioning and notify the "
            "regulator.",
        ],
        "gamp5_ref": "GAMP 5 \u00a75 \u2014 Software Life Cycle",
        "ai_triggers": [
            "model retraining", "pccp", "continuous learning",
            "model lifecycle", "model versioning",
        ],
        "pitfalls": [
            "No rollback plan \u2014 define rollback RTO and test SOP.",
            "No decommissioning data migration plan.",
        ],
    },
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class SMARTRequirement:
    """
    Single SMART-refined requirement with compliance metadata.

    :requirement: URS-21.6 - Engine shall produce structured SMART output.
    """

    original: str
    smart_text: str
    category: str
    risk_level: str          # High | Medium | Low
    fda_ema_flags: List[str]
    acceptance_criteria: Dict[str, List[str]]
    negative_test_scenario: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to plain dict."""
        return {
            "original": self.original,
            "smart_text": self.smart_text,
            "category": self.category,
            "risk_level": self.risk_level,
            "fda_ema_flags": self.fda_ema_flags,
            "acceptance_criteria": self.acceptance_criteria,
            "negative_test_scenario": self.negative_test_scenario,
        }


@dataclass
class SMARTResult:
    """
    Collection of SMART requirements with aggregate statistics.

    :requirement: URS-21.7 - Engine shall return summary statistics.
    """

    requirements: List[SMARTRequirement] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to plain dict."""
        return {
            "requirements": [r.to_dict() for r in self.requirements],
            "summary_stats": self.summary_stats,
        }


@dataclass
class SmartSection:
    """
    SMART-refined requirements for a single GxP category (14-type engine).

    :requirement: URS-21.16 - Engine shall produce per-section output.
    """

    type_name: str
    requirements: List[Dict[str, Any]]
    ai_guidance_tagged: bool
    raw_notes: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to plain dict."""
        return {
            "type_name": self.type_name,
            "requirements": self.requirements,
            "ai_guidance_tagged": self.ai_guidance_tagged,
            "raw_notes": self.raw_notes,
        }


@dataclass
class SmartPackage:
    """
    Full SMART requirements package for a validation project.

    :requirement: URS-21.17 - Engine shall return full package result.
    """

    sections: List[SmartSection] = field(default_factory=list)
    context: Dict[str, str] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to plain dict."""
        return {
            "sections": [s.to_dict() for s in self.sections],
            "context": self.context,
            "stats": self.stats,
        }


class SMARTEngineError(Exception):
    """Base error for the SMART Requirements Engine.

    :requirement: URS-21.8 - Engine shall raise typed errors.
    """

    error_code = "CSV-021"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SMARTRequirementsEngine:
    """
    SMART Requirements Authoring Engine.

    Rewrites vague GxP requirements to SMART format, enforces FDA/EMA 2026
    AI Guidance compliance, and supports 14 GxP requirement categories with
    inline help content.

    Primary method: ``transform_to_smart()`` — full 14-category engine.
    Legacy method:  ``refine_to_smart()``    — 5-section backward compat.

    LLM cascade: Claude (claude-sonnet-4-6) → OpenAI (gpt-4o) →
    deterministic fallback (no API key required).

    :requirement: URS-21.1  - Accept multi-section input.
    :requirement: URS-21.2  - Detect FDA/EMA 2026 triggers.
    :requirement: URS-21.3  - Rewrite to SMART format.
    :requirement: URS-21.4  - Generate Negative Test Scenarios.
    :requirement: URS-21.5  - Support LLM + deterministic modes.
    :requirement: URS-21.16 - Produce SmartSection output.
    :requirement: URS-21.17 - Return SmartPackage result.
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        model: str = _LLM_MODEL,
    ) -> None:
        """
        Initialise the engine.

        Claude is tried first; OpenAI is the fallback; deterministic
        mode is the final fallback (no keys needed).

        :param openai_api_key: OpenAI API key (or OPENAI_API_KEY env var).
        :param anthropic_api_key: Anthropic key (or ANTHROPIC_API_KEY).
        :param model: OpenAI model used in legacy refine_to_smart().
        :requirement: URS-21.5 - Support LLM and deterministic modes.
        """
        self._model = model

        # ── Claude (preferred) ────────────────────────────────────
        self._claude_available = False
        self._claude_client = None
        _claude_key = (
            anthropic_api_key
            or os.getenv("ANTHROPIC_API_KEY", "")
        )
        if (
            _claude_key
            and _claude_key not in ("", "DUMMY_SKIP")
            and _anthropic_sdk is not None
        ):
            try:
                self._claude_client = _anthropic_sdk.Anthropic(
                    api_key=_claude_key
                )
                self._claude_available = True
            except Exception:
                pass

        # ── OpenAI (fallback) ─────────────────────────────────────
        self._llm_available = False
        self._client = None
        _openai_key = (
            openai_api_key
            or os.getenv("OPENAI_API_KEY", "")
        )
        if (
            _openai_key
            and _openai_key not in ("", "DUMMY_SKIP")
            and OpenAI is not None
        ):
            try:
                self._client = OpenAI(api_key=_openai_key)
                self._llm_available = True
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Public: 14-category engine (primary)
    # ------------------------------------------------------------------

    def transform_to_smart(
        self,
        context: Dict[str, str],
        notes_by_type: Dict[str, str],
        risk_level: str = "Medium",
        has_ai: bool = False,
    ) -> SmartPackage:
        """
        Transform raw user notes into SMART requirements across 14 types.

        :param context: Dict with system_name, process_map, data_flow,
            overall_risk.
        :param notes_by_type: Mapping of requirement type name → raw
            free-text notes (one or more lines).
        :param risk_level: Overall project risk level (High/Medium/Low).
        :param has_ai: If True, AI Inference trigger is applied globally.
        :return: SmartPackage containing SmartSections and stats.
        :requirement: URS-21.1  - Accept multi-section input.
        :requirement: URS-21.17 - Return full SmartPackage.
        """
        active_notes = {
            k: v.strip()
            for k, v in notes_by_type.items()
            if v.strip()
        }

        if not active_notes:
            return SmartPackage(
                sections=[],
                context=context,
                stats={
                    "total": 0,
                    "high_risk": 0,
                    "fda_ema_flagged": 0,
                    "sections_populated": 0,
                },
            )

        # LLM cascade
        if self._claude_available:
            try:
                sections = self._claude_transform(
                    context, active_notes, has_ai, risk_level
                )
            except Exception:
                sections = self._deterministic_transform(
                    active_notes, has_ai
                )
        elif self._llm_available:
            try:
                sections = self._openai_transform(
                    context, active_notes, has_ai, risk_level
                )
            except Exception:
                sections = self._deterministic_transform(
                    active_notes, has_ai
                )
        else:
            sections = self._deterministic_transform(
                active_notes, has_ai
            )

        stats = self._compute_package_stats(sections)
        _log(
            agent_name="SMARTRequirementsEngine",
            action="SMART_REQUIREMENTS_REFINED",
            decision_logic=(
                f"Transformed {stats['total']} requirements across "
                f"{stats['sections_populated']} sections; "
                f"high_risk={stats['high_risk']}; "
                f"fda_ema={stats['fda_ema_flagged']}; "
                f"llm="
                + (
                    "claude"
                    if self._claude_available
                    else ("openai" if self._llm_available else "det.")
                )
            ),
            thought_process={
                "inputs": {
                    "sections": list(active_notes.keys()),
                    "total_sections": len(active_notes),
                    "has_ai": has_ai,
                    "risk_level": risk_level,
                    "system_name": context.get("system_name", "")[:80],
                },
                "steps": [
                    "Filtered sections with non-empty notes",
                    "Detected FDA/EMA 2026 flags per section",
                    "Transformed via "
                    + (
                        "Claude (claude-sonnet-4-6)"
                        if self._claude_available
                        else (
                            "OpenAI (gpt-4o)"
                            if self._llm_available
                            else "deterministic fallback"
                        )
                    ),
                    "Computed package statistics",
                ],
                "outputs": stats,
            },
        )
        return SmartPackage(
            sections=sections, context=context, stats=stats
        )

    # ------------------------------------------------------------------
    # Public: 5-section engine (backward compat)
    # ------------------------------------------------------------------

    def refine_to_smart(
        self,
        sections: Dict[str, List[str]],
        system_description: str = "",
        has_ai_components: bool = False,
    ) -> SMARTResult:
        """
        Refine raw requirements across 5 GxP sections to SMART format.

        Legacy method kept for backward compatibility.

        :param sections: Mapping of section name -> list of raw reqs.
        :param system_description: Optional system context.
        :param has_ai_components: If True, AI Inference flag applied.
        :return: SMARTResult containing refined requirements and stats.
        :requirement: URS-21.1 - Accept multi-section input.
        :requirement: URS-21.3 - Rewrite to SMART format.
        """
        flat: List[tuple] = []
        for category, reqs in sections.items():
            for raw in reqs:
                raw = raw.strip()
                if raw:
                    flat.append((category, raw))

        if not flat:
            return SMARTResult(
                requirements=[],
                summary_stats={
                    "total": 0,
                    "high_risk": 0,
                    "fda_ema_flagged": 0,
                    "categories": {},
                },
            )

        flags_by_index = [
            self._detect_fda_ema_flags(raw, has_ai_components)
            for _, raw in flat
        ]

        if self._llm_available:
            try:
                smart_rows = self._llm_refine(
                    flat, system_description, flags_by_index
                )
            except Exception:
                smart_rows = self._deterministic_refine(
                    flat, flags_by_index
                )
        else:
            smart_rows = self._deterministic_refine(
                flat, flags_by_index
            )

        stats = self._compute_stats(smart_rows)
        _log(
            agent_name="SMARTRequirementsEngine",
            action="SMART_REQUIREMENTS_REFINED",
            decision_logic=(
                f"Refined {stats['total']} requirements across "
                f"{len(sections)} sections; "
                f"high_risk={stats['high_risk']}; "
                f"fda_ema_flagged={stats['fda_ema_flagged']}"
            ),
            thought_process={
                "inputs": {
                    "sections": list(sections.keys()),
                    "total_raw": stats["total"],
                    "has_ai_components": has_ai_components,
                },
                "steps": [
                    "Flattened section requirements",
                    "Detected FDA/EMA 2026 flags",
                    "Refined via "
                    + (
                        "LLM"
                        if self._llm_available
                        else "deterministic"
                    ),
                ],
                "outputs": stats,
            },
        )
        return SMARTResult(requirements=smart_rows, summary_stats=stats)

    # ------------------------------------------------------------------
    # Private — Claude path (primary LLM)
    # ------------------------------------------------------------------

    def _build_transform_prompt(
        self,
        context: Dict[str, str],
        notes_by_type: Dict[str, str],
        has_ai: bool,
        risk_level: str,
    ) -> str:
        """
        Build the LLM prompt for the 14-type transform operation.

        :param context: System context dict.
        :param notes_by_type: Notes per requirement type.
        :param has_ai: Whether the system uses AI/ML.
        :param risk_level: Overall project risk level.
        :return: Formatted prompt string.
        :requirement: URS-21.3 - Rewrite to SMART format.
        """
        lines = [
            "You are an expert GxP validation consultant (GAMP 5, "
            "21 CFR Part 11, ICH Q10).",
            "",
            "Transform the user notes below into formal SMART "
            "requirements.",
            "SMART = Specific, Measurable, Achievable, Relevant, "
            "Testable.",
            "",
            "System Context:",
            f"  System Name:    {context.get('system_name', 'N/A')}",
            f"  Process Map:    {context.get('process_map', 'N/A')[:200]}",
            f"  Data Flow:      {context.get('data_flow', 'N/A')[:200]}",
            f"  Overall Risk:   {risk_level}",
            f"  AI/ML Present:  {'Yes' if has_ai else 'No'}",
            "",
            "Rules:",
            "1. Begin every requirement with 'The system shall'.",
            "2. Replace every vague word (should, fast, easy, robust, "
            "   adequate, timely) with a measurable threshold.",
            "3. risk_level: 'High' for patient/safety/regulatory impact; "
            "   'Medium' for quality/audit; 'Low' for admin.",
            "4. Set ai_guidance_tagged=true if the requirement involves "
            "   AI/ML inference, automated decisions, predictive models, "
            "   or any FDA/EMA 2026 AI Guidance trigger.",
            "5. Generate exactly 3 acceptance criteria per requirement:",
            "   positive (Given/When/Then — happy path),",
            "   negative (Given/When/Then — invalid input or boundary),",
            "   edge     (Given/When/Then — concurrent load or limits).",
            "6. If ai_guidance_tagged=true, generate a Negative Test "
            "   Scenario specifically addressing the AI/ML risk.",
            "",
            "Return ONLY valid JSON in this exact shape:",
            "{",
            '  "sections": {',
            '    "<TypeName>": {',
            '      "requirements": [',
            "        {",
            '          "smart_text": "The system shall...",',
            '          "risk_level": "High|Medium|Low",',
            '          "ai_guidance_tagged": true|false,',
            '          "acceptance_criteria": {',
            '            "positive": ["Given ..."],',
            '            "negative": ["Given ..."],',
            '            "edge":     ["Given ..."]',
            "          },",
            '          "negative_test_scenario": "Given...|null"',
            "        }",
            "      ]",
            "    }",
            "  }",
            "}",
            "",
            "User Notes by Requirement Type:",
        ]
        for idx, (type_name, notes) in enumerate(
            notes_by_type.items(), start=1
        ):
            lines.append(
                f"{idx:02d}. [{type_name}]\n{notes}"
            )
        return "\n".join(lines)

    def _claude_transform(
        self,
        context: Dict[str, str],
        notes_by_type: Dict[str, str],
        has_ai: bool,
        risk_level: str,
    ) -> List[SmartSection]:
        """
        Call Claude to transform notes to SMART requirements.

        :param context: System context dict.
        :param notes_by_type: Notes per requirement type.
        :param has_ai: Whether the system uses AI/ML.
        :param risk_level: Overall project risk level.
        :return: List of SmartSection objects.
        :requirement: URS-21.5 - Support LLM mode (Claude).
        """
        prompt = self._build_transform_prompt(
            context, notes_by_type, has_ai, risk_level
        )
        response = self._claude_client.messages.create(  # type: ignore
            model=_CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        return self._parse_llm_sections(
            data, notes_by_type, has_ai
        )

    def _openai_transform(
        self,
        context: Dict[str, str],
        notes_by_type: Dict[str, str],
        has_ai: bool,
        risk_level: str,
    ) -> List[SmartSection]:
        """
        Call OpenAI to transform notes to SMART requirements.

        :param context: System context dict.
        :param notes_by_type: Notes per requirement type.
        :param has_ai: Whether the system uses AI/ML.
        :param risk_level: Overall project risk level.
        :return: List of SmartSection objects.
        :requirement: URS-21.5 - Support LLM mode (OpenAI fallback).
        """
        prompt = self._build_transform_prompt(
            context, notes_by_type, has_ai, risk_level
        )
        response = self._client.chat.completions.create(  # type: ignore
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return self._parse_llm_sections(
            data, notes_by_type, has_ai
        )

    def _parse_llm_sections(
        self,
        data: Dict[str, Any],
        notes_by_type: Dict[str, str],
        has_ai: bool,
    ) -> List[SmartSection]:
        """
        Parse LLM JSON response into SmartSection objects.

        Falls back to deterministic for any missing section.

        :param data: Parsed JSON dict from LLM.
        :param notes_by_type: Original notes (for fallback).
        :param has_ai: Global AI flag.
        :return: List of SmartSection objects.
        :requirement: URS-21.16 - Produce per-section output.
        """
        sections_data = data.get("sections", {})
        result: List[SmartSection] = []
        det = self._deterministic_transform(notes_by_type, has_ai)
        det_map = {s.type_name: s for s in det}

        for type_name, raw_notes in notes_by_type.items():
            llm_sec = sections_data.get(type_name, {})
            llm_reqs = llm_sec.get("requirements", [])

            if llm_reqs:
                ai_tagged = any(
                    r.get("ai_guidance_tagged", False)
                    for r in llm_reqs
                )
                result.append(
                    SmartSection(
                        type_name=type_name,
                        requirements=llm_reqs,
                        ai_guidance_tagged=ai_tagged,
                        raw_notes=raw_notes,
                    )
                )
            else:
                # Fallback to deterministic for this section
                result.append(
                    det_map.get(
                        type_name,
                        SmartSection(
                            type_name=type_name,
                            requirements=[],
                            ai_guidance_tagged=False,
                            raw_notes=raw_notes,
                        ),
                    )
                )
        return result

    # ------------------------------------------------------------------
    # Private — Deterministic transform (14-type)
    # ------------------------------------------------------------------

    def _deterministic_transform(
        self,
        notes_by_type: Dict[str, str],
        has_ai: bool,
    ) -> List[SmartSection]:
        """
        Produce SMART requirements deterministically for all note types.

        :param notes_by_type: Notes per requirement type.
        :param has_ai: Global AI flag.
        :return: List of SmartSection objects.
        :requirement: URS-21.5 - Support deterministic mode.
        """
        result: List[SmartSection] = []
        for type_name, raw_notes in notes_by_type.items():
            lines = [
                ln.strip()
                for ln in raw_notes.splitlines()
                if ln.strip()
            ]
            reqs: List[Dict[str, Any]] = []
            section_ai_tagged = False

            for line in lines:
                flags = self._detect_fda_ema_flags(line, has_ai)
                smart = self._apply_vague_substitutions(line)
                smart = self._ensure_shall_prefix(smart)
                smart = self._post_clean(smart)
                risk = self._keyword_risk(line)
                if flags and risk != "High":
                    risk = "High"
                ai_tag = bool(flags)
                if ai_tag:
                    section_ai_tagged = True

                neg_test: Optional[str] = None
                if flags:
                    neg_test = _NEGATIVE_TEST_TEMPLATES.get(flags[0])

                ac = self._build_template_ac(smart, type_name)
                reqs.append({
                    "smart_text": smart,
                    "risk_level": risk,
                    "ai_guidance_tagged": ai_tag,
                    "acceptance_criteria": ac,
                    "negative_test_scenario": neg_test,
                    "fda_ema_flags": flags,
                })
            result.append(
                SmartSection(
                    type_name=type_name,
                    requirements=reqs,
                    ai_guidance_tagged=section_ai_tagged,
                    raw_notes=raw_notes,
                )
            )
        return result

    # ------------------------------------------------------------------
    # Private — Legacy LLM path (refine_to_smart)
    # ------------------------------------------------------------------

    def _build_llm_prompt(
        self,
        flat: List[tuple],
        system_description: str,
        flags_by_index: List[List[str]],
    ) -> str:
        """
        Build the numbered LLM prompt for legacy SMART refinement.

        :param flat: List of (category, raw_text) tuples.
        :param system_description: System context string.
        :param flags_by_index: Per-requirement FDA/EMA flag lists.
        :return: Formatted prompt string.
        :requirement: URS-21.3 - Rewrite to SMART format.
        """
        lines = [
            "You are a GxP regulatory validation expert.",
            "Rewrite each numbered requirement to SMART format.",
            "Return ONLY valid JSON with key 'requirements' "
            "containing an array.",
            "Each item: index (int), smart_text (str), "
            "risk_level (High|Medium|Low), "
            "acceptance_criteria {positive, negative, edge "
            "— each a list}, negative_test_scenario (str|null).",
            "",
        ]
        if system_description:
            lines.append(f"System context: {system_description}")
            lines.append("")
        lines.append("Requirements:")
        for idx, (cat, raw) in enumerate(flat):
            flag_str = (
                ", ".join(flags_by_index[idx])
                if flags_by_index[idx]
                else "None"
            )
            lines.append(
                f"{idx}. [Category: {cat}] "
                f"[FDA/EMA: {flag_str}] {raw}"
            )
        lines += [
            "",
            "Rules: start every smart_text with 'The system shall'; "
            "replace vague words; negative_test_scenario required "
            "when FDA/EMA flag present.",
        ]
        return "\n".join(lines)

    def _llm_refine(
        self,
        flat: List[tuple],
        system_description: str,
        flags_by_index: List[List[str]],
    ) -> List[SMARTRequirement]:
        """
        Call OpenAI for legacy SMART refinement.

        :param flat: List of (category, raw_text) tuples.
        :param system_description: System context string.
        :param flags_by_index: Per-requirement FDA/EMA flag lists.
        :return: List of SMARTRequirement objects.
        :requirement: URS-21.5 - Support LLM mode.
        """
        prompt = self._build_llm_prompt(
            flat, system_description, flags_by_index
        )
        response = self._client.chat.completions.create(  # type: ignore
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )
        raw_json = response.choices[0].message.content or "{}"
        data = json.loads(raw_json)
        items = data.get("requirements", [])

        result: List[SMARTRequirement] = []
        for item in items:
            idx = item.get("index", 0)
            if idx >= len(flat):
                continue
            category, original = flat[idx]
            ac = item.get("acceptance_criteria", {})
            result.append(
                SMARTRequirement(
                    original=original,
                    smart_text=item.get("smart_text", original),
                    category=category,
                    risk_level=item.get("risk_level", "Medium"),
                    fda_ema_flags=flags_by_index[idx],
                    acceptance_criteria={
                        "positive": ac.get("positive", []),
                        "negative": ac.get("negative", []),
                        "edge": ac.get("edge", []),
                    },
                    negative_test_scenario=item.get(
                        "negative_test_scenario"
                    ),
                )
            )
        returned_idx = {item.get("index", -1) for item in items}
        fallback = self._deterministic_refine(flat, flags_by_index)
        for i, req in enumerate(fallback):
            if i not in returned_idx:
                result.append(req)
        return result

    # ------------------------------------------------------------------
    # Private — Deterministic refine (legacy)
    # ------------------------------------------------------------------

    def _deterministic_refine(
        self,
        flat: List[tuple],
        flags_by_index: List[List[str]],
    ) -> List[SMARTRequirement]:
        """
        Produce SMART requirements without any LLM call (legacy).

        :param flat: List of (category, raw_text) tuples.
        :param flags_by_index: Per-requirement FDA/EMA flag lists.
        :return: List of SMARTRequirement objects.
        :requirement: URS-21.5 - Support deterministic mode.
        """
        result: List[SMARTRequirement] = []
        for idx, (category, original) in enumerate(flat):
            smart = self._apply_vague_substitutions(original)
            smart = self._ensure_shall_prefix(smart)
            smart = self._post_clean(smart)
            flags = flags_by_index[idx]
            risk = self._keyword_risk(original)
            if flags and risk != "High":
                risk = "High"
            ac = self._build_template_ac(smart, category)
            neg_test: Optional[str] = None
            if flags:
                neg_test = _NEGATIVE_TEST_TEMPLATES.get(flags[0])
            result.append(
                SMARTRequirement(
                    original=original,
                    smart_text=smart,
                    category=category,
                    risk_level=risk,
                    fda_ema_flags=flags,
                    acceptance_criteria=ac,
                    negative_test_scenario=neg_test,
                )
            )
        return result

    # ------------------------------------------------------------------
    # Private — Shared helpers
    # ------------------------------------------------------------------

    def _post_clean(self, text: str) -> str:
        """
        Collapse multiple spaces left by modal-verb removal.

        :param text: Partially refined requirement text.
        :return: Text with redundant whitespace removed.
        """
        return re.sub(r" {2,}", " ", text).strip()

    def _apply_vague_substitutions(self, text: str) -> str:
        """
        Replace vague words with measurable SMART equivalents.

        :param text: Raw requirement text.
        :return: Requirement with vague terms substituted.
        :requirement: URS-21.11 - Apply vague-word substitution.
        """
        for pattern, replacement in _VAGUE_SUBSTITUTIONS:
            text = re.sub(
                pattern, replacement, text, flags=re.IGNORECASE
            )
        return text

    def _ensure_shall_prefix(self, text: str) -> str:
        """
        Ensure requirement starts with 'The system shall'.

        Handles cases where vague-substitution already introduced
        'shall' mid-sentence by extracting the predicate clause.

        :param text: Requirement text (after vague substitution).
        :return: Text starting with 'The system shall'.
        :requirement: URS-21.12 - Ensure 'The system shall' prefix.
        """
        t = text.strip()
        lower = t.lower()

        # Already correct — leave unchanged
        if lower.startswith("the system shall"):
            return t

        # Known subject prefixes — replace subject, keep predicate
        for prefix in ("the system shall ", "the system ",
                       "system shall ", "system ",
                       "the "):
            if lower.startswith(prefix):
                remainder = t[len(prefix):]
                rem_lower = remainder.lower()
                # Drop a duplicate leading "shall " if present
                if rem_lower.startswith("shall "):
                    remainder = remainder[6:]
                else:
                    # Remainder may be "response time shall be…"
                    # — extract predicate after the mid-remainder shall
                    _sh2 = rem_lower.find(" shall ")
                    if _sh2 >= 0:
                        remainder = remainder[_sh2 + 7:]
                return "The system shall " + remainder

        # Text starts with bare "shall" (from substitution)
        if lower.startswith("shall "):
            return "The system shall " + t[6:]

        # "shall" appears mid-sentence (e.g. "Users shall …")
        # — extract predicate after the first "shall"
        _sh = lower.find(" shall ")
        if _sh >= 0:
            predicate = t[_sh + 7:]
            return "The system shall " + predicate

        # Fallback — prepend blindly
        return (
            "The system shall "
            + t[0].lower() + t[1:]
        )

    def _keyword_risk(self, text: str) -> str:
        """
        Classify risk level by keyword matching.

        :param text: Requirement text.
        :return: 'High', 'Medium', or 'Low'.
        :requirement: URS-21.9 - Classify requirement risk by keyword.
        """
        lower = text.lower()
        for kw in _HIGH_RISK_KW:
            if kw in lower:
                return "High"
        for kw in _MEDIUM_RISK_KW:
            if kw in lower:
                return "Medium"
        return "Low"

    def _build_template_ac(
        self, smart: str, category: str
    ) -> Dict[str, List[str]]:
        """
        Build template acceptance criteria for deterministic mode.

        :param smart: SMART requirement text.
        :param category: GxP requirement category.
        :return: Dict with positive, negative, edge lists.
        :requirement: URS-21.10 - Generate acceptance criteria.
        """
        short = smart[:80].rstrip(".")
        return {
            "positive": [
                f"Given a valid user session, "
                f"when the operation is performed, "
                f"then {short} is satisfied and logged to the "
                f"audit trail."
            ],
            "negative": [
                f"Given an invalid or boundary input, "
                f"when the operation is attempted, "
                f"then the system shall reject the input and "
                f"display a validated error message without data "
                f"corruption."
            ],
            "edge": [
                f"Given a concurrent load of >= 200 users, "
                f"when {category.lower()} functions are exercised, "
                f"then system behaviour remains within validated "
                f"performance thresholds."
            ],
        }

    def _detect_fda_ema_flags(
        self,
        raw: str,
        has_ai_components: bool = False,
    ) -> List[str]:
        """
        Scan raw text for FDA/EMA 2026 AI Guidance trigger keywords.

        :param raw: Raw requirement text.
        :param has_ai_components: If True, prepend 'AI Inference'.
        :return: List of trigger category names found.
        :requirement: URS-21.2 - Detect FDA/EMA 2026 triggers.
        """
        lower = raw.lower()
        found: List[str] = []
        for category, keywords in FDA_EMA_2026_TRIGGERS.items():
            for kw in keywords:
                if kw in lower:
                    if category not in found:
                        found.append(category)
                    break
        if has_ai_components and "AI Inference" not in found:
            found.insert(0, "AI Inference")
        return found

    def _compute_stats(
        self, rows: List[SMARTRequirement]
    ) -> Dict[str, Any]:
        """
        Compute statistics for a list of SMARTRequirement objects.

        :param rows: List of SMARTRequirement objects.
        :return: Stats dict (total, high_risk, fda_ema_flagged, cats).
        :requirement: URS-21.7 - Return summary statistics.
        """
        total = len(rows)
        high_risk = sum(1 for r in rows if r.risk_level == "High")
        fda_ema_flagged = sum(
            1 for r in rows if r.fda_ema_flags
        )
        categories: Dict[str, int] = {}
        for r in rows:
            categories[r.category] = (
                categories.get(r.category, 0) + 1
            )
        return {
            "total": total,
            "high_risk": high_risk,
            "fda_ema_flagged": fda_ema_flagged,
            "categories": categories,
        }

    def _compute_package_stats(
        self, sections: List[SmartSection]
    ) -> Dict[str, Any]:
        """
        Compute statistics for a list of SmartSection objects.

        :param sections: List of SmartSection objects.
        :return: Stats dict for SmartPackage.
        :requirement: URS-21.7 - Return summary statistics.
        """
        total = sum(len(s.requirements) for s in sections)
        high_risk = sum(
            1
            for s in sections
            for r in s.requirements
            if r.get("risk_level") == "High"
        )
        fda_ema_flagged = sum(
            1 for s in sections if s.ai_guidance_tagged
        )
        return {
            "total": total,
            "high_risk": high_risk,
            "fda_ema_flagged": fda_ema_flagged,
            "sections_populated": len(sections),
        }
