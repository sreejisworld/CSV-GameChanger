"""
drift_scenarios.py - Deterministic test scenario library for the
Regulatory Drift Agent.

Detects when regulatory corpus has diverged from EVOLV's cached
knowledge - new framework versions, FDA guidance updates, or new
requirements emerging in the regulatory landscape. Serves as an
early warning system for compliance risk.

:requirement: URS-TBD - Regulatory Drift Agent test scenarios.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DriftScenario:
    """One Regulatory Drift detection test case."""
    scenario_id:     str
    category:        str      # "no-drift" | "minor-drift" |
                              # "major-drift" | "critical-drift"
    endpoint:        str      # "/regulatory-drift/detect"
    input_body:      Dict[str, Any]
    expected:        Dict[str, Any]
    tags:            List[str] = field(default_factory=list)
    notes:           str = ""


# ─── Category 1: No drift (cached knowledge still current) ───────

_DRIFT_NO_DRIFT = [
    {
        "description": "GAMP 5 Rev 2 still current (Oct 2024)",
        "framework": "GAMP 5",
        "last_ingested_version": "GAMP5_Guide_Rev2_Oct2024",
        "ingestion_date": "2024-10-15",
        "days_old": 30,
        "expect_drift": False,
    },
    {
        "description":
            "EU Annex 11 (2022 guidance) still primary reference",
        "framework": "EU Annex 11",
        "last_ingested_version": "Annex11_2022_Rev1",
        "ingestion_date": "2024-06-01",
        "days_old": 180,
        "expect_drift": False,
    },
    {
        "description": "21 CFR Part 11 (Oct 2023 update) recent",
        "framework": "21 CFR Part 11",
        "last_ingested_version": "CFR11_Oct2023",
        "ingestion_date": "2024-01-15",
        "days_old": 210,
        "expect_drift": False,
    },
]

_DRIFT_MINOR_DRIFT = [
    {
        "description":
            "GAMP 5 Rev 3 released but Rev 2 knowledge still 85% "
            "applicable",
        "framework": "GAMP 5",
        "last_ingested_version": "GAMP5_Guide_Rev2_Oct2024",
        "latest_available": "GAMP5_Guide_Rev3_May2026",
        "ingestion_date": "2024-10-15",
        "days_old": 210,
        "overlap_pct": 85,
        "expect_drift": True,
        "drift_level": "minor",
    },
    {
        "description":
            "FDA GMLP (2025 update) - new principle added but "
            "core 10 unchanged",
        "framework": "FDA GMLP",
        "last_ingested_version": "FDA_GMLP_Oct2021",
        "latest_available": "FDA_GMLP_Mar2025",
        "ingestion_date": "2021-10-20",
        "days_old": 1620,
        "new_guidance_lines": 8,
        "expect_drift": True,
        "drift_level": "minor",
    },
]

_DRIFT_MAJOR_DRIFT = [
    {
        "description":
            "NIST AI RMF 2.0 released - new Govern function, "
            "60% structural change",
        "framework": "NIST AI RMF",
        "last_ingested_version": "NIST_AI_RMF_v1.0_Jan2024",
        "latest_available": "NIST_AI_RMF_v2.0_Sep2025",
        "ingestion_date": "2024-01-15",
        "days_old": 605,
        "structural_change_pct": 60,
        "expect_drift": True,
        "drift_level": "major",
    },
    {
        "description":
            "EU AI Act regulatory framework appears (not in "
            "EVOLV corpus yet)",
        "framework": "EU AI Act",
        "last_ingested_version": None,
        "latest_available": "EU_AI_Act_Apr2025",
        "ingestion_date": None,
        "days_old": 0,
        "completeness_gap": "100%",
        "expect_drift": True,
        "drift_level": "major",
    },
]

_DRIFT_CRITICAL_DRIFT = [
    {
        "description":
            "FDA releases AI guidance directly impacting all "
            "GxP systems (March 2025)",
        "framework": "FDA GMLP + AI Guidance",
        "last_ingested_version": "FDA_GMLP_Oct2021 + Legacy_AI_2023",
        "latest_available": "FDA_GMLP_Mar2025 + New_AI_Guidance_Mar2025",
        "ingestion_date": "2021-10-20",
        "days_old": 1620,
        "compliance_impact": "high",
        "regulatory_shock": "breaking-change",
        "expect_drift": True,
        "drift_level": "critical",
    },
    {
        "description":
            "Multiple frameworks updated simultaneously; "
            "validation strategy must be re-assessed",
        "framework": "GAMP 5 + EU Annex 11 + 21 CFR 11",
        "frameworks_updated": 3,
        "ingestion_date": "2024-06-01",
        "days_old": 365,
        "harmonization_gap": True,
        "expect_drift": True,
        "drift_level": "critical",
    },
]


def _build_drift_scenarios() -> tuple:  # Tuple[List[DriftScenario], ...]
    """Assemble all Drift scenarios by severity."""

    no_drift_scenarios: List[DriftScenario] = []
    for i, spec in enumerate(_DRIFT_NO_DRIFT):
        no_drift_scenarios.append(DriftScenario(
            scenario_id=f"drift-none-{i + 1:03d}",
            category="no-drift",
            endpoint="/regulatory-drift/detect",
            input_body={
                "framework": spec["framework"],
                "last_ingested": {
                    "version": spec["last_ingested_version"],
                    "date": spec["ingestion_date"],
                    "days_ago": spec["days_old"],
                },
            },
            expected={"drift_detected": False, "status": "current"},
            tags=["drift-none", "compliant-corpus"],
            notes=spec["description"],
        ))

    minor_drift_scenarios: List[DriftScenario] = []
    for i, spec in enumerate(_DRIFT_MINOR_DRIFT):
        minor_drift_scenarios.append(DriftScenario(
            scenario_id=f"drift-minor-{i + 1:03d}",
            category="minor-drift",
            endpoint="/regulatory-drift/detect",
            input_body={
                "framework": spec["framework"],
                "last_ingested": {
                    "version": spec["last_ingested_version"],
                    "date": spec["ingestion_date"],
                    "days_ago": spec["days_old"],
                },
                "available": spec.get("latest_available"),
            },
            expected={
                "drift_detected": True,
                "severity": "minor",
                "action_required": "monitor",
            },
            tags=["drift-minor", "version-update"],
            notes=spec["description"],
        ))

    major_drift_scenarios: List[DriftScenario] = []
    for i, spec in enumerate(_DRIFT_MAJOR_DRIFT):
        major_drift_scenarios.append(DriftScenario(
            scenario_id=f"drift-major-{i + 1:03d}",
            category="major-drift",
            endpoint="/regulatory-drift/detect",
            input_body={
                "framework": spec["framework"],
                "last_ingested": {
                    "version": spec["last_ingested_version"],
                    "date": spec.get("ingestion_date"),
                    "days_ago": spec.get("days_old", 0),
                },
                "available": spec.get("latest_available"),
            },
            expected={
                "drift_detected": True,
                "severity": "major",
                "action_required": "schedule-ingestion",
            },
            tags=["drift-major", "framework-major-update"],
            notes=spec["description"],
        ))

    critical_drift_scenarios: List[DriftScenario] = []
    for i, spec in enumerate(_DRIFT_CRITICAL_DRIFT):
        critical_drift_scenarios.append(DriftScenario(
            scenario_id=f"drift-critical-{i + 1:03d}",
            category="critical-drift",
            endpoint="/regulatory-drift/detect",
            input_body={
                "frameworks": spec.get("frameworks_updated", 1),
                "last_ingested": {
                    "version": spec.get("last_ingested_version"),
                    "date": spec.get("ingestion_date"),
                    "days_ago": spec.get("days_old", 0),
                },
            },
            expected={
                "drift_detected": True,
                "severity": "critical",
                "action_required": "urgent-ingestion",
                "compliance_alert": True,
            },
            tags=["drift-critical", "regulatory-shock"],
            notes=spec["description"],
        ))

    return (no_drift_scenarios, minor_drift_scenarios,
            major_drift_scenarios, critical_drift_scenarios)


DRIFT_NO_DRIFT: List[DriftScenario]
DRIFT_MINOR_DRIFT: List[DriftScenario]
DRIFT_MAJOR_DRIFT: List[DriftScenario]
DRIFT_CRITICAL_DRIFT: List[DriftScenario]

(DRIFT_NO_DRIFT, DRIFT_MINOR_DRIFT, DRIFT_MAJOR_DRIFT,
 DRIFT_CRITICAL_DRIFT) = _build_drift_scenarios()


def all_drift_scenarios() -> List[DriftScenario]:
    """All Drift scenarios across every severity.

    :requirement: URS-TBD - Drift detection test scenarios.
    """
    return (
        DRIFT_NO_DRIFT
        + DRIFT_MINOR_DRIFT
        + DRIFT_MAJOR_DRIFT
        + DRIFT_CRITICAL_DRIFT
    )


def drift_scenarios_by_severity(
    severity: Optional[str] = None,
) -> List[DriftScenario]:
    """Return Drift scenarios filtered by severity.

    Severities: "no-drift" | "minor-drift" | "major-drift" |
    "critical-drift" | None (all)

    :requirement: URS-TBD - Filtered scenario lookup.
    """
    if severity is None:
        return all_drift_scenarios()
    lookup = {
        "no-drift":       DRIFT_NO_DRIFT,
        "minor-drift":    DRIFT_MINOR_DRIFT,
        "major-drift":    DRIFT_MAJOR_DRIFT,
        "critical-drift": DRIFT_CRITICAL_DRIFT,
    }
    return lookup.get(severity.lower(), [])


COUNTS = {
    "no-drift":       len(DRIFT_NO_DRIFT),
    "minor-drift":    len(DRIFT_MINOR_DRIFT),
    "major-drift":    len(DRIFT_MAJOR_DRIFT),
    "critical-drift": len(DRIFT_CRITICAL_DRIFT),
    "total":          len(all_drift_scenarios()),
}
