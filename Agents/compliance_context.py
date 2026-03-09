"""
Compliance Context — Site-Specific Regulatory Mode.

Provides ComplianceMode enum and ComplianceContext dataclass
that adapt AI system prompts and Pinecone metadata filters based
on the active facility type (GMP, GCP, GLP, ISO 13485).

:requirement: URS-23.1 - System shall support site-specific
              compliance modes.
:requirement: URS-23.2 - AI prompts must reflect the active
              site compliance context.
:requirement: URS-23.3 - RAG (Pinecone) queries must use
              mode-specific metadata filters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from string import Template
from typing import Dict, List


# -----------------------------------------------------------------
# Prompt Template (Task 3 — Context-Injection)
# -----------------------------------------------------------------

#: Context-aware prompt template.  Variables: site_type,
#: reg_list, risk_threshold, sop_block.
PROMPT_TEMPLATE = Template(
    "You are a regulatory compliance advisor for a "
    "$site_type facility. "
    "Ensure all requirements, tests, and risk assessments "
    "comply with $reg_list. "
    "Your risk appetite is $risk_threshold. "
    "$sop_block"
)

_SITE_TYPES: Dict[str, str] = {
    "GMP":      "pharmaceutical manufacturing (GMP)",
    "GCP":      "clinical trial (GCP)",
    "GLP":      "laboratory research (GLP)",
    "ISO13485": "medical device (ISO 13485)",
}

_RISK_THRESHOLDS: Dict[str, str] = {
    "GMP": (
        "conservative — zero tolerance for manufacturing "
        "deviations; all changes require documented impact "
        "assessment"
    ),
    "GCP": (
        "moderate — patient safety is paramount; data "
        "integrity for clinical decisions is non-negotiable"
    ),
    "GLP": (
        "rigorous — raw data integrity under ALCOA+ is "
        "mandatory; every observation must be contemporaneous"
    ),
    "ISO13485": (
        "risk-based per ISO 14971 — systematic identification "
        "and mitigation of device hazards required"
    ),
}


class ComplianceMode(str, Enum):
    """
    Site-specific compliance mode selector.

    :requirement: URS-23.1
    """

    GMP = "GMP"          # 21 CFR Part 211 — Manufacturing
    GCP = "GCP"          # ICH E6 — Clinical
    GLP = "GLP"          # 21 CFR Part 58 — Laboratory
    ISO13485 = "ISO13485"  # ISO 13485 — Medical Devices


# -----------------------------------------------------------------
# Internal regulation profile (not public)
# -----------------------------------------------------------------

@dataclass
class _RegulationProfile:
    primary: str
    secondary: List[str]
    focus_keywords: List[str]
    system_prompt_injection: str
    pinecone_filter: Dict[str, str]
    description: str


_PROFILES: Dict[ComplianceMode, _RegulationProfile] = {
    ComplianceMode.GMP: _RegulationProfile(
        primary="21 CFR Part 211",
        secondary=[
            "GAMP 5", "21 CFR Part 11", "EU GMP Annex 11",
        ],
        focus_keywords=[
            "batch release", "manufacturing controls",
            "data integrity", "equipment calibration",
            "process validation", "batch records",
        ],
        system_prompt_injection=(
            "You are operating in GMP (Good Manufacturing Practice)"
            " mode. Prioritize 21 CFR Part 211 standards and focus"
            " on equipment calibration, batch record integrity, and"
            " manufacturing process validation. All requirements"
            " must align with FDA manufacturing site expectations."
            " Reference EU GMP Annex 11 for computerised systems."
        ),
        pinecone_filter={"compliance_mode": "GMP"},
        description=(
            "Good Manufacturing Practice — 21 CFR Part 211 + GAMP 5"
        ),
    ),

    ComplianceMode.GCP: _RegulationProfile(
        primary="ICH E6 (R2)",
        secondary=[
            "21 CFR Part 50", "21 CFR Part 11",
            "GDPR", "HIPAA", "ISO 14155",
        ],
        focus_keywords=[
            "patient privacy", "informed consent",
            "clinical data", "investigator site",
            "adverse events", "protocol deviation",
            "data monitoring", "randomisation",
        ],
        system_prompt_injection=(
            "You are operating in GCP (Good Clinical Practice) mode."
            " Prioritize ICH E6 (R2) and 21 CFR Part 11; focus on"
            " patient data privacy (GDPR/HIPAA), informed consent,"
            " and investigator site oversight. All requirements must"
            " protect patient safety and ensure clinical data"
            " integrity in line with FDA and EMA expectations."
        ),
        pinecone_filter={"compliance_mode": "GCP"},
        description=(
            "Good Clinical Practice — ICH E6 (R2) + GDPR/HIPAA"
        ),
    ),

    ComplianceMode.GLP: _RegulationProfile(
        primary="21 CFR Part 58",
        secondary=["OECD GLP Principles", "21 CFR Part 11"],
        focus_keywords=[
            "laboratory data", "study director",
            "raw data integrity", "test facility",
            "quality assurance unit", "archive",
        ],
        system_prompt_injection=(
            "You are operating in GLP (Good Laboratory Practice)"
            " mode. Prioritize 21 CFR Part 58 and OECD GLP"
            " Principles; focus on study data integrity, quality"
            " assurance unit oversight, and raw data archival."
            " Requirements must ensure laboratory data is"
            " attributable, legible, contemporaneous, original,"
            " and accurate (ALCOA+)."
        ),
        pinecone_filter={"compliance_mode": "GLP"},
        description=(
            "Good Laboratory Practice — 21 CFR Part 58 + OECD GLP"
        ),
    ),

    ComplianceMode.ISO13485: _RegulationProfile(
        primary="ISO 13485:2016",
        secondary=[
            "21 CFR Part 820", "EU MDR 2017/745", "IEC 62304",
        ],
        focus_keywords=[
            "design controls", "risk management",
            "complaint handling", "post-market surveillance",
            "device history record", "design transfer",
        ],
        system_prompt_injection=(
            "You are operating in ISO 13485 (Medical Device Quality"
            " Management) mode. Prioritize ISO 13485:2016 and"
            " 21 CFR Part 820; focus on design controls, risk"
            " management (ISO 14971), and complaint handling."
            " Requirements must support CE marking under EU MDR"
            " 2017/745 and FDA 510(k)/PMA submissions."
        ),
        pinecone_filter={"compliance_mode": "ISO13485"},
        description=(
            "Medical Device QMS — ISO 13485 + 21 CFR Part 820"
        ),
    ),
}


# -----------------------------------------------------------------
# ComplianceContext
# -----------------------------------------------------------------

@dataclass
class ComplianceContext:
    """
    Active site-specific compliance configuration.

    Holds the selected ComplianceMode and exposes helpers for
    injecting regulatory context into AI prompts and Pinecone
    metadata filters.

    :requirement: URS-23.1 - Site-specific compliance toggle.
    :requirement: URS-23.2 - AI prompts must reflect site context.
    :requirement: URS-23.3 - RAG queries must use metadata filters.
    """

    mode: ComplianceMode = ComplianceMode.GMP
    site_name: str = "Default Site"
    # Client SOP text forwarded from TenantConfig / Task 4
    sop_guidelines: str = ""

    def _profile(self) -> _RegulationProfile:
        return _PROFILES[self.mode]

    # ----------------------------------------------------------
    # Prompt & filter helpers
    # ----------------------------------------------------------

    def get_system_prompt_injection(
        self,
        extra_context: str = "",
    ) -> str:
        """
        Return the regulatory preamble to prepend to AI prompts.

        Merges the mode-specific prompt, any client SOP
        guidelines, and optional extra context in that order.

        :param extra_context: Optional free-text context.
        :return: Formatted system prompt string.
        :requirement: URS-23.2
        """
        parts = [self._profile().system_prompt_injection]
        if self.sop_guidelines:
            parts.append(
                "\n\nAdditional Client Quality Guidelines:\n"
                + self.sop_guidelines
            )
        if extra_context:
            parts.append(
                "\n\nAdditional Context:\n" + extra_context
            )
        return "\n".join(parts)

    def render_prompt(
        self,
        extra_context: str = "",
    ) -> str:
        """
        Render the context-aware prompt template for this mode.

        Fills ``PROMPT_TEMPLATE`` with site_type, reg_list,
        risk_threshold, and optional SOP / extra context so
        every AI call uses the correct regulatory mindset.

        Template variables::

            $site_type       — e.g. "pharmaceutical manufacturing (GMP)"
            $reg_list        — primary + secondary regulations
            $risk_threshold  — mode-specific risk appetite
            $sop_block       — client SOP + extra context (optional)

        :param extra_context: Optional free-text appended after SOP.
        :return: Rendered prompt string.
        :requirement: URS-23.4 - Context-aware prompt template.
        """
        profile = self._profile()
        reg_list = ", ".join(
            [profile.primary] + profile.secondary
        )
        site_type = _SITE_TYPES.get(
            self.mode.value,
            self.mode.value + " facility",
        )
        risk_threshold = _RISK_THRESHOLDS.get(
            self.mode.value, "standard"
        )
        sop_parts = []
        if self.sop_guidelines:
            sop_parts.append(
                "Additional Client Quality Guidelines:\n"
                + self.sop_guidelines
            )
        if extra_context:
            sop_parts.append(
                "Additional Context:\n" + extra_context
            )
        sop_block = (
            "\n\n" + "\n\n".join(sop_parts)
            if sop_parts else ""
        )
        return PROMPT_TEMPLATE.substitute(
            site_type=site_type,
            reg_list=reg_list,
            risk_threshold=risk_threshold,
            sop_block=sop_block,
        )

    def get_pinecone_filter(self) -> Dict[str, str]:
        """
        Return the Pinecone metadata filter for this mode.

        Pass this dict as the ``filter`` argument in Pinecone
        query calls to restrict results to mode-relevant chunks.

        :return: Pinecone-compatible filter dict.
        :requirement: URS-23.3
        """
        return dict(self._profile().pinecone_filter)

    # ----------------------------------------------------------
    # Read-only properties
    # ----------------------------------------------------------

    def get_primary_regulation(self) -> str:
        """Return the primary regulation citation string."""
        return self._profile().primary

    def get_secondary_regulations(self) -> List[str]:
        """Return list of secondary regulation citations."""
        return list(self._profile().secondary)

    def get_focus_keywords(self) -> List[str]:
        """Return focus keywords for this compliance mode."""
        return list(self._profile().focus_keywords)

    def get_description(self) -> str:
        """Return a one-line description of this mode."""
        return self._profile().description

    def to_dict(self) -> Dict:
        """Serialise to a plain dictionary."""
        return {
            "mode":                  self.mode.value,
            "site_name":             self.site_name,
            "primary_regulation":    self.get_primary_regulation(),
            "secondary_regulations": (
                self.get_secondary_regulations()
            ),
            "description":           self.get_description(),
        }
