"""
vse_scenarios.py - Deterministic test scenario library for the
Validated State Engine (VSE).

Sprint 37 flagship capability: per-UR Validated State Confidence
score derived from bundle staleness, open defect pressure, CIA
change-history, and coverage gaps. No LLM in the loop - all
deterministic signal aggregation.

:requirement: URS-37.1 - Per-UR Validated State Confidence engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VSEScenario:
    """One VSE test case - a project snapshot with expected signal
    breakdown and score tier."""
    scenario_id:     str
    category:        str      # "green" | "yellow" | "red" | "no-bundle"
    endpoint:        str      # "/validated-state/assess"
    input_body:      Dict[str, Any]
    expected:        Dict[str, Any]  # expected fields in response
    tags:            List[str] = field(default_factory=list)
    notes:           str = ""


# ─── Category 1: Green tier scenarios (score >= 80) ──────────────

_VSE_GREEN = [
    {
        "description":
            "Fresh bundle (< 7 days), no open defects, no CIAs, "
            "all FRs covered",
        "ur_count": 1,
        "bundle_age_days": 2,
        "open_defects": 0,
        "cia_count": 0,
        "fr_coverage": 100,
        "expected_min_score": 80,
    },
    {
        "description":
            "Recent bundle (< 14 days), 1 minor defect, no CIAs, "
            "full coverage",
        "ur_count": 1,
        "bundle_age_days": 10,
        "open_defects": 1,
        "cia_count": 0,
        "fr_coverage": 100,
        "expected_min_score": 75,
    },
    {
        "description":
            "Bundle 20 days old, zero defects, no CIA activity, "
            "all FRs covered, re-verified in last 7 days",
        "ur_count": 2,
        "bundle_age_days": 20,
        "open_defects": 0,
        "cia_count": 0,
        "fr_coverage": 100,
        "recent_reverify": True,
        "expected_min_score": 80,
    },
]

_VSE_YELLOW = [
    {
        "description":
            "Bundle 45 days old (near stale threshold), 2 open "
            "defects, no CIAs, full coverage",
        "ur_count": 1,
        "bundle_age_days": 45,
        "open_defects": 2,
        "cia_count": 0,
        "fr_coverage": 100,
        "expected_max_score": 79,
        "expected_min_score": 50,
    },
    {
        "description":
            "Bundle 30 days old, 3 open defects, 1 recent CIA, "
            "95% FR coverage",
        "ur_count": 3,
        "bundle_age_days": 30,
        "open_defects": 3,
        "cia_count": 1,
        "cia_days_ago": 5,
        "fr_coverage": 95,
        "expected_max_score": 79,
        "expected_min_score": 50,
    },
    {
        "description":
            "Bundle 60 days old (stale), 1 defect, 2 CIAs in past "
            "30 days, full coverage",
        "ur_count": 1,
        "bundle_age_days": 60,
        "open_defects": 1,
        "cia_count": 2,
        "cia_days_ago": 15,
        "fr_coverage": 100,
        "expected_max_score": 79,
        "expected_min_score": 40,
    },
]

_VSE_RED = [
    {
        "description":
            "Bundle 90+ days old (very stale), 5 open defects, "
            "no recent revalidation",
        "ur_count": 1,
        "bundle_age_days": 95,
        "open_defects": 5,
        "cia_count": 0,
        "fr_coverage": 100,
        "expected_max_score": 49,
    },
    {
        "description":
            "Bundle 45 days old, 10 critical defects, 3 active "
            "CIAs, only 80% FR coverage",
        "ur_count": 2,
        "bundle_age_days": 45,
        "open_defects": 10,
        "cia_count": 3,
        "fr_coverage": 80,
        "expected_max_score": 49,
    },
    {
        "description":
            "Bundle 120 days old (critical age), 3 defects, "
            "2 recent CIAs, gaps in coverage",
        "ur_count": 1,
        "bundle_age_days": 120,
        "open_defects": 3,
        "cia_count": 2,
        "fr_coverage": 90,
        "expected_max_score": 49,
    },
]

_VSE_NO_BUNDLE = [
    {
        "description":
            "UR has zero test bundles (no validation coverage at "
            "all)",
        "ur_count": 1,
        "bundle_age_days": None,
        "open_defects": 0,
        "cia_count": 0,
        "fr_coverage": 0,
        "expected_penalty": -30,
    },
    {
        "description":
            "GxP Direct UR with no bundle - high compliance "
            "pressure",
        "ur_count": 1,
        "ur_gxp_class": "GxP Direct",
        "bundle_age_days": None,
        "expected_penalty": -30,
    },
]


def _build_vse_scenarios(
) -> tuple:  # Tuple[List[VSEScenario], ...]
    """Assemble all VSE scenarios by tier."""

    green_scenarios: List[VSEScenario] = []
    for i, spec in enumerate(_VSE_GREEN):
        green_scenarios.append(VSEScenario(
            scenario_id=f"vse-green-{i + 1:03d}",
            category="green",
            endpoint="/validated-state/assess",
            input_body={
                "project_snapshot": {
                    "project_name": f"Test Project {i}",
                    "requirements": [
                        {"ur_id": f"UR-{j}", "gxp_class": "GxP Direct"}
                        for j in range(1, spec["ur_count"] + 1)
                    ],
                    "test_bundles": [
                        {
                            "bundle_id": f"B-{j}",
                            "ur_id": f"UR-{j}",
                            "created_at": f"{-spec['bundle_age_days']} days ago",
                        }
                        for j in range(1, spec["ur_count"] + 1)
                    ],
                    "defects": [
                        {"id": f"D-{j}", "ur_id": f"UR-{(j % spec['ur_count']) + 1}"}
                        for j in range(1, spec["open_defects"] + 1)
                    ] if spec["open_defects"] > 0 else [],
                    "change_records": [],
                }
            },
            expected={
                "aggregate_score": {
                    "min": spec["expected_min_score"],
                    "max": 100,
                }
            },
            tags=["vse-green", "fresh-validation"],
            notes=spec["description"],
        ))

    yellow_scenarios: List[VSEScenario] = []
    for i, spec in enumerate(_VSE_YELLOW):
        yellow_scenarios.append(VSEScenario(
            scenario_id=f"vse-yellow-{i + 1:03d}",
            category="yellow",
            endpoint="/validated-state/assess",
            input_body={"project_snapshot": {}},  # Placeholder
            expected={
                "aggregate_score": {
                    "min": spec.get("expected_min_score", 50),
                    "max": spec.get("expected_max_score", 79),
                }
            },
            tags=["vse-yellow", "aging-validation"],
            notes=spec["description"],
        ))

    red_scenarios: List[VSEScenario] = []
    for i, spec in enumerate(_VSE_RED):
        red_scenarios.append(VSEScenario(
            scenario_id=f"vse-red-{i + 1:03d}",
            category="red",
            endpoint="/validated-state/assess",
            input_body={"project_snapshot": {}},
            expected={
                "aggregate_score": {
                    "min": 0,
                    "max": spec.get("expected_max_score", 49),
                }
            },
            tags=["vse-red", "stale-validation"],
            notes=spec["description"],
        ))

    no_bundle_scenarios: List[VSEScenario] = []
    for i, spec in enumerate(_VSE_NO_BUNDLE):
        no_bundle_scenarios.append(VSEScenario(
            scenario_id=f"vse-no-bundle-{i + 1:03d}",
            category="no-bundle",
            endpoint="/validated-state/assess",
            input_body={"project_snapshot": {}},
            expected={
                "aggregate_score": {
                    "max": 55,
                }
            },
            tags=["vse-gap", "no-test-coverage"],
            notes=spec["description"],
        ))

    return green_scenarios, yellow_scenarios, red_scenarios, no_bundle_scenarios


VSE_GREEN_TIER: List[VSEScenario]
VSE_YELLOW_TIER: List[VSEScenario]
VSE_RED_TIER: List[VSEScenario]
VSE_NO_BUNDLE_SCENARIOS: List[VSEScenario]

(VSE_GREEN_TIER, VSE_YELLOW_TIER, VSE_RED_TIER,
 VSE_NO_BUNDLE_SCENARIOS) = _build_vse_scenarios()


def all_vse_scenarios() -> List[VSEScenario]:
    """All VSE scenarios across every tier.

    :requirement: URS-37.1 - VSE test scenario library.
    """
    return (
        VSE_GREEN_TIER
        + VSE_YELLOW_TIER
        + VSE_RED_TIER
        + VSE_NO_BUNDLE_SCENARIOS
    )


def vse_scenarios_by_tier(
    tier: Optional[str] = None,
) -> List[VSEScenario]:
    """Return VSE scenarios filtered by tier.

    Tiers: "green" | "yellow" | "red" | "no-bundle" | None (all)

    :requirement: URS-37.1 - Filtered scenario lookup.
    """
    if tier is None:
        return all_vse_scenarios()
    lookup = {
        "green":     VSE_GREEN_TIER,
        "yellow":    VSE_YELLOW_TIER,
        "red":       VSE_RED_TIER,
        "no-bundle": VSE_NO_BUNDLE_SCENARIOS,
    }
    return lookup.get(tier.lower(), [])


COUNTS = {
    "green":     len(VSE_GREEN_TIER),
    "yellow":    len(VSE_YELLOW_TIER),
    "red":       len(VSE_RED_TIER),
    "no-bundle": len(VSE_NO_BUNDLE_SCENARIOS),
    "total":     len(all_vse_scenarios()),
}
