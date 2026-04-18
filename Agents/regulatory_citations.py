"""
Regulatory Citations Module.

Maps each test-step archetype (Setup, Positive, Negative, Boundary,
Recovery, Security, UAT, Charter) to the specific regulatory
controls it satisfies.

The citations are surfaced in test scripts so that auditors and
testers can see, at the step level, which regulation justifies each
verification activity.

References:
- 21 CFR Part 11 (FDA, electronic records / signatures)
- EU GMP Annex 11 (computerised systems)
- GAMP 5 Second Edition (ISPE, risk-based validation)
- FDA CSA Draft Guidance 2022 (Computer Software Assurance)
- ICH Q9(R1) (Quality Risk Management)

:requirement: URS-22.1 - System shall surface regulatory citations
              per test step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class RegulatoryCitation:
    """
    Immutable citation record for a single regulation/section.

    :requirement: URS-22.1 - System shall surface regulatory
                  citations per test step.
    """

    regulation: str
    section: str
    rationale: str

    def to_dict(self) -> Dict[str, str]:
        """
        Serialise to a JSON-safe dict.

        :return: Dict with regulation, section, rationale keys.
        """
        return {
            "regulation": self.regulation,
            "section":    self.section,
            "rationale":  self.rationale,
        }


# ------------------------------------------------------------------
# Citation library
# ------------------------------------------------------------------

C_SETUP = RegulatoryCitation(
    regulation="GAMP 5 Second Edition",
    section="Appendix M5",
    rationale=(
        "Test prerequisites and baseline state must be documented "
        "before execution to ensure reproducibility."
    ),
)

C_AUDIT_TRAIL = RegulatoryCitation(
    regulation="21 CFR Part 11",
    section="\u00a711.10(e)",
    rationale=(
        "Use of secure, computer-generated, time-stamped audit "
        "trails to independently record the date and time of "
        "operator entries and actions."
    ),
)

C_ESIG = RegulatoryCitation(
    regulation="21 CFR Part 11",
    section="\u00a711.50 / \u00a711.70",
    rationale=(
        "Signed electronic records must contain the printed name "
        "of the signer, date and time, and meaning of signature; "
        "signatures must be linked to records to prevent excision.",
    )[0],
)

C_ANNEX11_TEST = RegulatoryCitation(
    regulation="EU GMP Annex 11",
    section="\u00a74.4 (Validation)",
    rationale=(
        "Validation documentation should include evidence of "
        "tests performed, with results and conclusions, "
        "demonstrating fitness for intended use."
    ),
)

C_ANNEX11_DATA_INTEGRITY = RegulatoryCitation(
    regulation="EU GMP Annex 11",
    section="\u00a77.1 (Data Storage)",
    rationale=(
        "Data should be secured from damage by both physical and "
        "electronic means; integrity must be checked periodically."
    ),
)

C_NEGATIVE_INPUT = RegulatoryCitation(
    regulation="GAMP 5 Second Edition",
    section="Section 8.4 (Negative Testing)",
    rationale=(
        "Test cases must include invalid input handling to "
        "demonstrate the system rejects out-of-spec data and "
        "preserves data integrity under error conditions."
    ),
)

C_BOUNDARY = RegulatoryCitation(
    regulation="ICH Q9(R1)",
    section="Annex I.6 (Risk Control)",
    rationale=(
        "Boundary and edge-case testing demonstrates that "
        "control measures remain effective at the limits of "
        "operating range \u2014 essential for risk reduction."
    ),
)

C_RECOVERY = RegulatoryCitation(
    regulation="EU GMP Annex 11",
    section="\u00a716 (Business Continuity)",
    rationale=(
        "For the availability of computerised systems supporting "
        "critical processes, provisions should be made to ensure "
        "continuity of support after system breakdown."
    ),
)

C_SECURITY = RegulatoryCitation(
    regulation="21 CFR Part 11",
    section="\u00a711.10(d) / \u00a711.300",
    rationale=(
        "Limit system access to authorised individuals; "
        "controls must include unique identification, "
        "authentication, and authorisation checks."
    ),
)

C_UAT = RegulatoryCitation(
    regulation="GAMP 5 Second Edition",
    section="Appendix D7 (User Acceptance)",
    rationale=(
        "User Acceptance Testing demonstrates that the system "
        "meets defined business requirements in the intended "
        "operational environment."
    ),
)

C_CSA_UNSCRIPTED = RegulatoryCitation(
    regulation="FDA CSA Draft Guidance (2022)",
    section="Section IV.B (Unscripted Testing)",
    rationale=(
        "For low-risk features, unscripted exploratory testing "
        "by qualified testers is acceptable when scripted "
        "protocols are disproportionate to risk."
    ),
)

C_PATIENT_SAFETY = RegulatoryCitation(
    regulation="ICH Q9(R1)",
    section="Section 4 (Risk Assessment)",
    rationale=(
        "The level of effort, formality and documentation of "
        "the quality risk management process should be "
        "commensurate with the level of risk to patient safety."
    ),
)


# ------------------------------------------------------------------
# Step-archetype \u2192 citations map
# ------------------------------------------------------------------

@dataclass(frozen=True)
class CitationBundle:
    """
    A bundle of citations attached to a step archetype.

    :requirement: URS-22.2 - System shall map step types to
                  regulatory citations.
    """

    archetype: str
    citations: List[RegulatoryCitation] = field(default_factory=list)

    def to_list(self) -> List[Dict[str, str]]:
        """
        Serialise the bundled citations to a list of dicts.

        :return: List of citation dicts for JSON output.
        """
        return [c.to_dict() for c in self.citations]


CITATION_MAP: Dict[str, CitationBundle] = {
    "setup": CitationBundle(
        archetype="setup",
        citations=[C_SETUP],
    ),
    "positive": CitationBundle(
        archetype="positive",
        citations=[C_ANNEX11_TEST, C_AUDIT_TRAIL],
    ),
    "negative": CitationBundle(
        archetype="negative",
        citations=[C_NEGATIVE_INPUT, C_ANNEX11_DATA_INTEGRITY],
    ),
    "boundary": CitationBundle(
        archetype="boundary",
        citations=[C_BOUNDARY, C_ANNEX11_TEST],
    ),
    "edge_case": CitationBundle(
        archetype="edge_case",
        citations=[C_BOUNDARY, C_NEGATIVE_INPUT],
    ),
    "recovery": CitationBundle(
        archetype="recovery",
        citations=[C_RECOVERY, C_AUDIT_TRAIL],
    ),
    "security": CitationBundle(
        archetype="security",
        citations=[C_SECURITY, C_AUDIT_TRAIL],
    ),
    "esignature": CitationBundle(
        archetype="esignature",
        citations=[C_ESIG, C_AUDIT_TRAIL],
    ),
    "uat": CitationBundle(
        archetype="uat",
        citations=[C_UAT, C_PATIENT_SAFETY],
    ),
    "charter": CitationBundle(
        archetype="charter",
        citations=[C_CSA_UNSCRIPTED],
    ),
}


def citations_for(archetype: str) -> List[Dict[str, str]]:
    """
    Look up the citation list for a given step archetype.

    Returns an empty list if the archetype is unknown so callers
    never get a ``KeyError``.

    :param archetype: Step archetype key (e.g. ``"positive"``).
    :return: List of citation dicts, possibly empty.
    :requirement: URS-22.2 - System shall map step types to
                  regulatory citations.
    """
    bundle = CITATION_MAP.get(archetype.lower())
    if bundle is None:
        return []
    return bundle.to_list()


def citations_for_risk_level(risk_level: str) -> List[Dict[str, str]]:
    """
    Return high-level citations summarising why a particular risk
    level is being addressed (for the bundle header).

    :param risk_level: ``"High"``, ``"Medium"``, or ``"Low"``.
    :return: List of citation dicts.
    :requirement: URS-22.3 - System shall surface risk-level
                  regulatory rationale.
    """
    base = [C_PATIENT_SAFETY.to_dict()]
    if risk_level == "High":
        return base + [
            C_ANNEX11_TEST.to_dict(),
            C_AUDIT_TRAIL.to_dict(),
        ]
    if risk_level == "Medium":
        return base + [C_ANNEX11_TEST.to_dict()]
    return base + [C_CSA_UNSCRIPTED.to_dict()]
