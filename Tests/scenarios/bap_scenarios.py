"""
bap_scenarios.py - Deterministic test scenario library for the
Bounded Autonomy Profile engine.

Each scenario is a static tuple of (input, expected outcome) with
NO LLM in the loop. The Test Pilot Agent runs these against the
live /bap/* endpoints and compares actual vs expected.

Categories:
  - BAP_X_TRIGGERS       : statements that SHOULD fire exclusion
  - BAP_SAFE_STATEMENTS  : statements that should NOT fire exclusion
  - BAP_TIER_ASSIGNMENT  : full COUs with expected tier verdicts
  - BAP_ADVERSARIAL      : sneaky phrasings testing edge cases

:requirement: URS-41.1 - Deterministic BAP test scenarios.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─── Scenario dataclass ─────────────────────────────────────────

@dataclass
class BAPScenario:
    """One BAP test case.

    scenario_id  - unique identifier (e.g. "bap-x-sign-001")
    category     - one of: exclusion, safe, tier, adversarial
    endpoint     - full path (e.g. "/bap/check-exclusion")
    input_body   - dict sent as JSON body
    expected     - dict of expected fields to check against response
                   e.g. {"would_be_excluded": True,
                         "rules_fired.0.rule_id": "EX-1-SIGN"}
    tags         - list of tags for filtering + reporting
    """
    scenario_id:  str
    category:     str
    endpoint:     str
    input_body:   Dict[str, Any]
    expected:     Dict[str, Any]
    tags:         List[str] = field(default_factory=list)
    notes:        str = ""


# ─── Category 1: BAP-X exclusion triggers (should FIRE) ─────────

_BAP_X_SIGN = [
    ("AI signs the electronic signature on behalf of QA",
     "EX-1-SIGN"),
    ("AI automatically signs the electronic signature",
     "EX-1-SIGN"),
    ("The AI signs an electronic signature for release",
     "EX-1-SIGN"),
    ("AI system signs approval on validated records",
     "EX-1-SIGN"),
    ("Our AI will sign electronic signatures automatically",
     "EX-1-SIGN"),
    ("AI executes signing the electronic signature",
     "EX-1-SIGN"),
    ("AI signs the manifestation of signature on batch records",
     "EX-1-SIGN"),
]

_BAP_X_RELEASE = [
    ("AI releases the batch autonomously",
     "EX-2-RELEASE"),
    ("AI automatically releases the lot to production",
     "EX-2-RELEASE"),
    ("AI approves the batch release without human review",
     "EX-2-RELEASE"),
    ("The AI releases product to the supply chain",
     "EX-2-RELEASE"),
    ("AI system releases batches based on QC data",
     "EX-2-RELEASE"),
    ("AI approves lot release when tests pass",
     "EX-2-RELEASE"),
]

_BAP_X_CAPA = [
    ("AI closes the CAPA once the effectiveness check passes",
     "EX-3-CAPA"),
    ("AI automatically closes deviations under threshold",
     "EX-3-CAPA"),
    ("The AI resolves complaints without further review",
     "EX-3-CAPA"),
    ("AI system closes investigation records autonomously",
     "EX-3-CAPA"),
    ("AI closes CAPA records when root cause is identified",
     "EX-3-CAPA"),
]

_BAP_X_CLINICAL = [
    ("AI diagnoses the patient from imaging data",
     "EX-4-CLINICAL"),
    ("AI prescribes dosing based on lab values",
     "EX-4-CLINICAL"),
    ("The AI makes clinical decision for treatment",
     "EX-4-CLINICAL"),
    ("AI recommends treatment based on patient profile",
     "EX-4-CLINICAL"),
    ("AI calculates dosing for the patient",
     "EX-4-CLINICAL"),
]

_BAP_X_VALIDATED_WRITE = [
    ("AI modifies the validated record with new results",
     "EX-5-VALIDATED-WRITE"),
    ("AI updates the GxP record automatically",
     "EX-5-VALIDATED-WRITE"),
    ("AI writes to the controlled document without review",
     "EX-5-VALIDATED-WRITE"),
    ("AI persists changes to validated records overnight",
     "EX-5-VALIDATED-WRITE"),
    ("AI alters the GxP record when discrepancy detected",
     "EX-5-VALIDATED-WRITE"),
]


def _build_exclusion_scenarios() -> List[BAPScenario]:
    """Assemble all BAP-X trigger scenarios."""
    out: List[BAPScenario] = []
    all_triggers = (
        _BAP_X_SIGN + _BAP_X_RELEASE + _BAP_X_CAPA
        + _BAP_X_CLINICAL + _BAP_X_VALIDATED_WRITE
    )
    for i, (statement, expected_rule) in enumerate(all_triggers):
        out.append(BAPScenario(
            scenario_id=f"bap-x-{i + 1:03d}",
            category="exclusion",
            endpoint="/bap/check-exclusion",
            input_body={
                "statement":          statement,
                "decision_authority": "AI proposes, human signs",
            },
            expected={
                "would_be_excluded":     True,
                "rules_fired.0.rule_id": expected_rule,
            },
            tags=["bap-x", expected_rule.lower()],
            notes=f"Should fire {expected_rule}",
        ))
    return out


BAP_X_TRIGGERS: List[BAPScenario] = _build_exclusion_scenarios()


# ─── Category 2: BAP-safe statements (should NOT fire) ──────────

_BAP_SAFE = [
    "EVOLV drafts URs and FRs for a GxP-Direct LIMS at a CDMO;"
    " outputs require QA sign-off before being persisted to Vault.",
    "AI generates test scripts for the QMS system; QA reviews"
    " before test execution.",
    "AI proposes risk classifications; the risk council approves"
    " before promotion.",
    "AI drafts the validation summary report; the responsible"
    " person signs after review.",
    "AI suggests test cases for GxP Indirect systems; test lead"
    " signs off.",
    "AI writes URS drafts for a new eQMS; QA reviewer signs"
    " before deployment.",
    "AI recommends corrective actions for deviations; CAPA owner"
    " reviews and closes.",
    "AI drafts change control assessments; change board approves.",
    "The system uses AI to summarise internal meeting minutes for"
    " a non-GxP team.",
    "AI provides suggestions on validation strategy; VP CSV"
    " approves the final plan.",
    "AI generates draft training materials; L&D reviews before"
    " release.",
    "AI proposes technology-refresh recommendations; IT ops"
    " reviews.",
    "AI provides analytics summaries on stability data; QA reviews"
    " trends.",
    "AI drafts SOPs from workshop notes; SOP owner signs before"
    " publication.",
    "AI supports drafting design specifications with human sign-off"
    " gates before persistence.",
    "AI helps regulatory affairs team draft filing narratives;"
    " RA director approves.",
    "The system uses AI to route documents; humans approve every"
    " routing decision.",
    "AI drafts audit findings summaries for internal review;"
    " audit lead signs.",
    "AI drafts deviation write-ups; deviation owner reviews and"
    " approves.",
    "AI summarises inspection prep documents; inspection lead"
    " signs the final read.",
]

BAP_SAFE_STATEMENTS: List[BAPScenario] = [
    BAPScenario(
        scenario_id=f"bap-safe-{i + 1:03d}",
        category="safe",
        endpoint="/bap/check-exclusion",
        input_body={
            "statement":          stmt,
            "decision_authority": "AI proposes, human signs",
        },
        expected={
            "would_be_excluded": False,
        },
        tags=["bap-safe"],
        notes="Should proceed to full assessment (no exclusion)",
    )
    for i, stmt in enumerate(_BAP_SAFE)
]


# ─── Category 3: Full-tier assignment (should reach expected tier) ─

_TIER_COUS = [
    # BAP-2 Controlled Drafting (standard GxP Direct + human sign)
    ("EVOLV drafts URs for a GxP-Direct LIMS at a CDMO; outputs"
     " require QA sign-off before being persisted to Vault.",
     "GxP Direct", "High", "BAP-2"),
    ("AI generates test cases for a GxP Direct validated system;"
     " QA lead signs before execution.",
     "GxP Direct", "High", "BAP-2"),
    ("AI drafts the URS for the new SAP-integrated LIMS;"
     " responsible person signs off.",
     "GxP Direct", "High", "BAP-2"),
    ("AI proposes risk assessments for a GxP Direct release;"
     " QA council approves.",
     "GxP Direct", "High", "BAP-2"),
    ("AI drafts test scripts for validated eQMS; test lead"
     " signs before test.",
     "GxP Direct", "Medium", "BAP-2"),
    # BAP-1 Advisory (GxP Indirect, moderate risk)
    ("AI provides validation search hints for GxP Indirect system;"
     " advisory only.",
     "GxP Indirect", "Low", "BAP-1"),
    ("AI summarises regulatory context for GxP Indirect team.",
     "GxP Indirect", "Low", "BAP-1"),
    # BAP-0 Productivity (non-GxP)
    ("AI summarises meeting minutes for internal team.",
     "Non-GxP", "Low", "BAP-0"),
    ("AI drafts internal training slides for non-GxP audience.",
     "Non-GxP", "Low", "BAP-0"),
]


BAP_TIER_ASSIGNMENT: List[BAPScenario] = [
    BAPScenario(
        scenario_id=f"bap-tier-{i + 1:03d}",
        category="tier",
        endpoint="/bap/assess",
        input_body={
            "cou": {
                "customer_name":      "Test Pilot Customer",
                "statement":          stmt,
                "deployment_region":  "US",
                "gxp_classification": gxp,
                "risk_level":         risk,
                "decision_authority": "AI proposes, human signs",
                "target_system":      "LabCore LIMS v4.2",
                "poc_or_production":  "POC",
            },
            "user_id": "test-pilot",
        },
        expected={
            "tier_id":      expected_tier,
            "is_exclusion": False,
        },
        tags=["bap-tier", expected_tier.lower()],
        notes=f"COU should assign to {expected_tier}",
    )
    for i, (stmt, gxp, risk, expected_tier) in enumerate(_TIER_COUS)
]


# ─── Category 4: Adversarial ─────────────────────────────────────

# Statements engineered to try to trick the classifier - either
# fire exclusion when they shouldn't OR NOT fire when they should.
# These are the highest-value scenarios: they expose regex gaps.

_ADVERSARIAL = [
    # Should be safe (has human signature gate) but words might
    # sneak past exclusion regex
    ("AI signs a summary email; the CSV lead signs the electronic"
     " signature on the actual document.",
     False, None,
     "Word 'signs' appears but only for email summary"),
    ("AI is used during batch release investigation drafting;"
     " QP still releases the batch.",
     False, None,
     "'batch release' mentioned but not AI performing it"),
    ("AI closes tickets in the ITSM system for non-GxP requests"
     " only.",
     False, None,
     "'closes' + 'tickets' - not GxP CAPA closure"),
    ("Provided to the AI: patient data anonymised for training"
     " statistics.",
     False, None,
     "Contains 'patient' but only in training-data context"),
    # Should fire but written obliquely
    ("Our system will have the AI sign off electronic signatures"
     " automatically at end of shift.",
     True, "EX-1-SIGN",
     "Oblique 'sign off electronic signatures'"),
    ("Every night the AI releases lots for shipping without"
     " human review.",
     True, "EX-2-RELEASE",
     "Nightly autonomous lot release"),
    ("AI diagnoses which lot has anomalies for release decision"
     " making.",
     True, "EX-4-CLINICAL",
     "'diagnoses' fires clinical rule even in QC context - "
     "acceptable false positive"),
]


BAP_ADVERSARIAL: List[BAPScenario] = [
    BAPScenario(
        scenario_id=f"bap-adv-{i + 1:03d}",
        category="adversarial",
        endpoint="/bap/check-exclusion",
        input_body={
            "statement":          stmt,
            "decision_authority": "AI proposes, human signs",
        },
        expected=(
            {"would_be_excluded": True,
             "rules_fired.0.rule_id": expected_rule}
            if should_fire
            else {"would_be_excluded": False}
        ),
        tags=["bap-adversarial",
              "should-fire" if should_fire else "should-pass"],
        notes=note,
    )
    for i, (stmt, should_fire, expected_rule, note)
    in enumerate(_ADVERSARIAL)
]


# ─── Public bundle helper ───────────────────────────────────────

def all_bap_scenarios() -> List[BAPScenario]:
    """All BAP scenarios across every category.

    :requirement: URS-41.2 - Aggregate BAP scenario library.
    """
    return (
        BAP_X_TRIGGERS
        + BAP_SAFE_STATEMENTS
        + BAP_TIER_ASSIGNMENT
        + BAP_ADVERSARIAL
    )


def bap_scenarios_by_category(
    category: Optional[str] = None,
) -> List[BAPScenario]:
    """Return BAP scenarios filtered by category.

    Categories: "exclusion" | "safe" | "tier" | "adversarial"
    | None (returns all)

    :requirement: URS-41.3 - Filtered scenario lookup.
    """
    if category is None:
        return all_bap_scenarios()
    lookup = {
        "exclusion":   BAP_X_TRIGGERS,
        "safe":        BAP_SAFE_STATEMENTS,
        "tier":        BAP_TIER_ASSIGNMENT,
        "adversarial": BAP_ADVERSARIAL,
    }
    return lookup.get(category.lower(), [])


COUNTS = {
    "exclusion":   len(BAP_X_TRIGGERS),
    "safe":        len(BAP_SAFE_STATEMENTS),
    "tier":        len(BAP_TIER_ASSIGNMENT),
    "adversarial": len(BAP_ADVERSARIAL),
    "total":       len(all_bap_scenarios()),
}
