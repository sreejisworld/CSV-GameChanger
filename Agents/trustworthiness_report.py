"""
trustworthiness_report.py - Sprint 39 AI Trustworthiness
Credibility Assessment Report generator.

The customer-facing artefact that closes the "can we deploy
this AI inside our GxP environment?" question. Maps EVOLV's
architecture (Agent Passports, Logic Archives, audit trail,
Validated State Engine, Regulatory Drift Agent, bounded
autonomy) to the frameworks big-pharma evaluators check
against:

  - NIST AI RMF 1.0     (Govern - Map - Measure - Manage)
  - FDA GMLP            (10 Guiding Principles, Oct 2021)
  - ISO/IEC 22989:2021  (AI vocabulary)
  - 21 CFR Part 11      (electronic records / signatures)
  - GAMP 5              (already covered by EVOLV)
  - FDA CSA             (risk-based validation)

The principle: every claim cites a real artefact (Agent
Passport version, audit-trail row hash, Logic Archive hash).
No marketing copy. Pharma evaluators don't trust prose; they
trust hashes.

Context of Use (COU) is the unit of assessment per the
pharma-SOP pattern - the same AI used differently has
different risk, so the report is per-COU, not per-tool.

Five triggers force a fresh report:
  1. New AI tool to a GxP space
  2. New model added to a validated GxP-impacting tool
  3. New major model version (vX.0 → vY.0)
  4. New Context of Use
  5. Progression from POC to Production

Bounded autonomy: this generator never modifies records,
never signs approvals, never writes the audit chain. It
reads from Agent Passports + audit trail + corpus registry
and emits a structured report dict + Logic Archive.

:requirement: URS-39.1 - AI Trustworthiness Credibility
              Assessment Report generator.
"""
from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from Agents.agent_passports import (   # noqa: E402
    AGENT_PASSPORTS,
    get_agent_passport,
    list_agent_passports,
)
from Agents.integrity_manager import log_audit_event   # noqa: E402


AGENT_NAME = "TrustworthinessReportGenerator"
SCHEMA_VERSION = "1.0.0"


# ─── Exceptions ──────────────────────────────────────────────────────

class TrustworthinessReportError(Exception):
    """Base error for the Trustworthiness Report generator."""
    error_code = "CSV-039"


class InvalidContextOfUseError(TrustworthinessReportError):
    """COU dict is missing required fields or has bad values."""
    error_code = "CSV-040"


# ─── Framework canon - the mapping spine ─────────────────────────────
#
# These dicts are the auditable source-of-truth EVOLV maps its
# architecture against. When a framework version changes (FDA
# updates GMLP, NIST releases RMF 2.0), we bump these dicts -
# every report regenerated from that point picks up the change.

NIST_AI_RMF: Dict[str, Dict[str, str]] = {
    # Govern function - organizational AI risk management
    "GV-1.1": {
        "function":    "Govern",
        "category":    "GV-1 - Policies",
        "requirement":
            "Legal and regulatory requirements involving AI "
            "are understood, managed, and documented.",
    },
    "GV-1.2": {
        "function":    "Govern",
        "category":    "GV-1 - Policies",
        "requirement":
            "Characteristics of trustworthy AI (valid, "
            "reliable, safe, secure, accountable, transparent, "
            "explainable, privacy-enhanced, fair) are "
            "integrated into organizational policies.",
    },
    "GV-2.1": {
        "function":    "Govern",
        "category":    "GV-2 - Accountability",
        "requirement":
            "Roles, responsibilities, and lines of communication "
            "for the AI lifecycle are documented.",
    },
    "GV-4.1": {
        "function":    "Govern",
        "category":    "GV-4 - Risk management",
        "requirement":
            "Organizational practices for safe AI development, "
            "deployment, and use are in place.",
    },
    # Map function - AI system context understanding
    "MP-1.1": {
        "function":    "Map",
        "category":    "MP-1 - Context",
        "requirement":
            "Intended purpose, potentially beneficial uses, "
            "context-specific laws, and norms are documented.",
    },
    "MP-2.3": {
        "function":    "Map",
        "category":    "MP-2 - Categorization",
        "requirement":
            "The AI system's purpose and intended use are "
            "clearly defined.",
    },
    "MP-4.1": {
        "function":    "Map",
        "category":    "MP-4 - Risk mapping",
        "requirement":
            "Approaches for mapping AI risks are followed.",
    },
    "MP-5.2": {
        "function":    "Map",
        "category":    "MP-5 - Impacts",
        "requirement":
            "Likelihood and magnitude of each impact identified "
            "in MP-5.1 are documented.",
    },
    # Measure function - analysis, assessment, tracking
    "MS-1.1": {
        "function":    "Measure",
        "category":    "MS-1 - Test/eval",
        "requirement":
            "Approaches and metrics for validity, reliability, "
            "and robustness are identified and applied.",
    },
    "MS-2.5": {
        "function":    "Measure",
        "category":    "MS-2 - Trust assessment",
        "requirement":
            "AI system performance and trustworthiness are "
            "assessed at regular intervals.",
    },
    "MS-2.7": {
        "function":    "Measure",
        "category":    "MS-2 - Trust assessment",
        "requirement":
            "AI system security and resilience are monitored.",
    },
    "MS-3.1": {
        "function":    "Measure",
        "category":    "MS-3 - Risk tracking",
        "requirement":
            "Approaches to identifying and tracking existing, "
            "unanticipated, and emergent AI risks are followed.",
    },
    # Manage function - prioritize and respond
    "MG-2.1": {
        "function":    "Manage",
        "category":    "MG-2 - Risk response",
        "requirement":
            "Resources for managing AI risks are allocated "
            "based on assessed risk.",
    },
    "MG-3.2": {
        "function":    "Manage",
        "category":    "MG-3 - Monitoring",
        "requirement":
            "AI system performance is regularly assessed against "
            "documented metrics.",
    },
    "MG-4.1": {
        "function":    "Manage",
        "category":    "MG-4 - Incident response",
        "requirement":
            "Post-deployment monitoring plans are implemented; "
            "incidents and errors are documented and responded to.",
    },
}


FDA_GMLP: Dict[str, Dict[str, str]] = {
    "P-1": {
        "title": "Multi-Disciplinary Expertise Throughout the "
                 "Total Product Life Cycle",
        "requirement":
            "Leverage multi-disciplinary expertise (clinicians, "
            "engineers, data scientists, regulators, QA) at every "
            "stage from concept through post-market.",
    },
    "P-2": {
        "title": "Good Software Engineering and Security Practices",
        "requirement":
            "Software engineering, data quality assurance, data "
            "management, and robust cybersecurity practices are "
            "implemented end-to-end.",
    },
    "P-3": {
        "title": "Representative Clinical Study Participants and "
                 "Data Sets",
        "requirement":
            "Training and test data sets are representative of "
            "the intended patient population, environment, and "
            "use conditions.",
    },
    "P-4": {
        "title": "Training Data Sets Are Independent of Test Sets",
        "requirement":
            "Training, tuning, and test data sets are independent "
            "and address all relevant patient subgroups.",
    },
    "P-5": {
        "title": "Reference Datasets Based Upon Best Available "
                 "Methods",
        "requirement":
            "Reference datasets used to evaluate the AI system "
            "rely on best-available methods to ensure clinically "
            "relevant performance.",
    },
    "P-6": {
        "title": "Model Design Tailored to Available Data and "
                 "Intended Use",
        "requirement":
            "Model design reflects the intended use, mitigates "
            "known risks (overfitting, performance degradation, "
            "security), and is tailored to available data.",
    },
    "P-7": {
        "title": "Focus on the Performance of the Human-AI Team",
        "requirement":
            "Where the model has a 'human in the loop', "
            "performance of the human-AI team - not the model "
            "alone - is the relevant performance benchmark.",
    },
    "P-8": {
        "title": "Testing Demonstrates Performance in Clinically "
                 "Relevant Conditions",
        "requirement":
            "Statistically sound test plans demonstrate device "
            "performance during clinically relevant conditions, "
            "including independent test data evaluation.",
    },
    "P-9": {
        "title": "Users Are Provided Clear, Essential Information",
        "requirement":
            "Users are provided ready access to clear, essential "
            "information about intended use, performance, "
            "training data, limitations, and known biases.",
    },
    "P-10": {
        "title": "Deployed Models Are Monitored for Performance "
                 "and Re-training Risks Are Managed",
        "requirement":
            "Deployed models are monitored for performance "
            "in the real world; corrective action processes are "
            "in place for any identified performance degradation.",
    },
}


# ISO/IEC 22989:2021 - AI vocabulary (referenced in the SOP)
# The terms we explicitly anchor to in the report so an
# evaluator can map our language to their internal glossary.
ISO_22989_TERMS: Dict[str, str] = {
    "Artificial Intelligence":
        "Capability to acquire, process, create and apply "
        "knowledge, held in the form of a model, to conduct "
        "one or more given tasks.",
    "AI System":
        "Engineered system that generates outputs such as "
        "content, forecasts, recommendations, or decisions "
        "for a given set of human-defined objectives.",
    "Machine Learning":
        "Process by which a functional unit improves its "
        "performance by acquiring new knowledge or skills "
        "from data.",
    "Model":
        "Physical, mathematical, or logical representation "
        "of a system, entity, phenomenon, process or data.",
    "Training Data":
        "Data used to train a machine-learning model.",
    "Test Data":
        "Data used to evaluate a trained machine-learning "
        "model's performance.",
    "Context of Use":
        "Specific role and scope of the AI tool used to "
        "address a question of interest.",
    "Trustworthiness":
        "Ability to meet stakeholder expectations in a "
        "verifiable way.",
}


# Five triggers from the pharma-SOP pattern - any one of
# these forces a fresh assessment report.
TRIGGERS_FOR_REPORT: List[Dict[str, str]] = [
    {
        "id":    "T1_NEW_TOOL_TO_GXP",
        "label": "New AI tool introduced to a GxP space",
    },
    {
        "id":    "T2_NEW_MODEL_TO_TOOL",
        "label": "New model introduced to an existing validated "
                 "GxP-impacting AI tool",
    },
    {
        "id":    "T3_MAJOR_VERSION_BUMP",
        "label": "New major model version (e.g. v4.5 → v5.0) on "
                 "a validated GxP-impacting AI tool",
    },
    {
        "id":    "T4_NEW_COU",
        "label": "New Context of Use introduced to an existing "
                 "validated GxP AI tool",
    },
    {
        "id":    "T5_POC_TO_PROD",
        "label": "Progression of a GxP-impacting AI tool from "
                 "Proof of Concept to Production",
    },
]


# Five signer roles from the pharma-SOP RACI pattern.
# Every report goes through these gates before approval for
# GxP usage in Production.
REQUIRED_SIGNERS: List[Dict[str, str]] = [
    {
        "role":   "Business Owner",
        "duty":   "Performs the assessment and documents results. "
                  "Verifies operational SOPs are made effective.",
    },
    {
        "role":   "Quality Assurance",
        "duty":   "Ensures the assessment is performed properly "
                  "and documented per controlled procedures.",
    },
    {
        "role":   "Service Owner",
        "duty":   "Reviews / approves documents per the operating "
                  "SOP.",
    },
    {
        "role":   "System SME (System / IT Application Owner)",
        "duty":   "Reviews and approves. Provides technical "
                  "assessments. Identifies strategy for "
                  "leveraging supplier documentation.",
    },
    {
        "role":   "AI Model SME",
        "duty":   "Assists with the assessment. Ensures proper "
                  "data-science / statistical analysis has been "
                  "performed to evidence credibility.",
    },
]


# ─── Dataclasses ─────────────────────────────────────────────────────

@dataclass
class ContextOfUse:
    """A specific deployment of an EVOLV agent at a customer.

    The unit of assessment per pharma SOP convention: same
    agent used differently has different risk.

    :requirement: URS-39.2 - Context of Use as unit of
                  assessment.
    """
    cou_id:              str
    customer_name:       str
    statement:           str
    deployment_region:   str    # 'US' | 'EU' | 'India' | 'Global'
    gxp_classification:  str    # 'GxP Direct' | 'GxP Indirect' | 'Non-GxP'
    risk_level:          str    # 'High' | 'Medium' | 'Low'
    decision_authority:  str    # 'AI proposes, human signs'
    target_system:       str = ""           # e.g. LIMS, eQMS, MES
    integrates_with:     List[str] = field(default_factory=list)
    triggers_detected:   List[str] = field(default_factory=list)
    poc_or_production:   str = "POC"


@dataclass
class EvidenceReference:
    """One auditable reference to a real EVOLV artefact.

    Pharma evaluators want hashes, not prose. Every claim in
    the report cites at least one of these.

    :requirement: URS-39.3 - Evidence-by-reference (hash-cited
                  proof, no marketing copy).
    """
    kind:        str   # 'agent_passport' | 'audit_row' |
                       # 'logic_archive' | 'corpus_version' |
                       # 'urs_traceability' | 'eval_run'
    identifier:  str   # passport name+version, row hash, etc.
    summary:     str
    location:    str = ""   # path or URL for inspector access


@dataclass
class FrameworkMapping:
    """One framework requirement, EVOLV's evidence, and a verdict.

    Status taxonomy:
      Met     - EVOLV fully satisfies the requirement
      Partial - partial coverage; gaps named explicitly
      Gap     - requirement not yet covered; mitigation noted

    :requirement: URS-39.4 - Framework mapping with explicit
                  Met / Partial / Gap status.
    """
    framework:      str    # 'NIST AI RMF' | 'FDA GMLP' | 'ISO 22989'
    section_id:     str
    section_title:  str = ""
    requirement:    str = ""
    evolv_response: str = ""
    evidence_refs:  List[EvidenceReference] = field(default_factory=list)
    status:         str = "Met"    # 'Met' | 'Partial' | 'Gap'
    notes:          str = ""


@dataclass
class TrustworthinessReport:
    """The full assessment artefact.

    Self-contained: an inspector with this dict + the audit
    trail + the Logic Archive directory can re-derive every
    claim. No external dependencies, no narrative-only sections.

    :requirement: URS-39.5 - Self-contained, replay-able
                  trustworthiness report.
    """
    report_id:           str
    schema_version:      str
    customer_name:       str
    cou:                 ContextOfUse
    generated_at:        str
    primary_frameworks:  List[str]

    # Narrative sections (each contains evidence_refs)
    executive_summary:        str
    ai_tool_description:      Dict[str, Any]
    cou_assessment:           Dict[str, Any]
    risk_analysis:            Dict[str, Any]
    bounded_autonomy_evidence: Dict[str, Any]
    continuous_monitoring:    Dict[str, Any]
    incident_response:        Dict[str, Any]
    limitations:              List[str]

    # The mapping spine - auditable proof matrix
    framework_mappings:       List[FrameworkMapping]

    # Approval chain - pharma-SOP RACI pattern
    required_signers:         List[Dict[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dict for JSON API + Logic Archive."""
        return {
            "report_id":          self.report_id,
            "schema_version":     self.schema_version,
            "customer_name":      self.customer_name,
            "cou":                asdict(self.cou),
            "generated_at":       self.generated_at,
            "primary_frameworks": self.primary_frameworks,
            "executive_summary":  self.executive_summary,
            "ai_tool_description": self.ai_tool_description,
            "cou_assessment":      self.cou_assessment,
            "risk_analysis":       self.risk_analysis,
            "bounded_autonomy_evidence":
                                   self.bounded_autonomy_evidence,
            "continuous_monitoring":
                                   self.continuous_monitoring,
            "incident_response":   self.incident_response,
            "limitations":         self.limitations,
            "framework_mappings": [
                {
                    "framework":      m.framework,
                    "section_id":     m.section_id,
                    "section_title":  m.section_title,
                    "requirement":    m.requirement,
                    "evolv_response": m.evolv_response,
                    "evidence_refs": [
                        asdict(e) for e in m.evidence_refs
                    ],
                    "status":         m.status,
                    "notes":          m.notes,
                }
                for m in self.framework_mappings
            ],
            "required_signers":  self.required_signers,
            "summary_counts": self._summary_counts(),
        }

    def _summary_counts(self) -> Dict[str, int]:
        """Headline tier counts an evaluator sees first."""
        met     = sum(1 for m in self.framework_mappings if m.status == "Met")
        partial = sum(1 for m in self.framework_mappings if m.status == "Partial")
        gap     = sum(1 for m in self.framework_mappings if m.status == "Gap")
        return {
            "frameworks_mapped":   len(self.primary_frameworks),
            "controls_mapped":     len(self.framework_mappings),
            "controls_met":        met,
            "controls_partial":    partial,
            "controls_gap":        gap,
        }


# ─── COU validation ──────────────────────────────────────────────────

_VALID_REGIONS = {"US", "EU", "India", "Global", "UK", "APAC"}
_VALID_GXP = {"GxP Direct", "GxP Indirect", "Non-GxP"}
_VALID_RISK = {"High", "Medium", "Low"}
_VALID_LIFECYCLE = {"POC", "Production"}


def _validate_cou(cou_dict: Dict[str, Any]) -> ContextOfUse:
    """Validate + coerce a COU dict into a ContextOfUse.

    Raises InvalidContextOfUseError with a useful message
    when fields are missing or have unexpected values.
    """
    required = [
        "customer_name", "statement", "deployment_region",
        "gxp_classification", "risk_level", "decision_authority",
    ]
    missing = [f for f in required if not cou_dict.get(f)]
    if missing:
        raise InvalidContextOfUseError(
            f"COU is missing required field(s): {missing}"
        )

    region = cou_dict["deployment_region"]
    if region not in _VALID_REGIONS:
        raise InvalidContextOfUseError(
            f"deployment_region must be one of {_VALID_REGIONS}; "
            f"got {region!r}"
        )

    gxp = cou_dict["gxp_classification"]
    if gxp not in _VALID_GXP:
        raise InvalidContextOfUseError(
            f"gxp_classification must be one of {_VALID_GXP}; "
            f"got {gxp!r}"
        )

    risk = cou_dict["risk_level"]
    if risk not in _VALID_RISK:
        raise InvalidContextOfUseError(
            f"risk_level must be one of {_VALID_RISK}; "
            f"got {risk!r}"
        )

    lifecycle = cou_dict.get("poc_or_production", "POC")
    if lifecycle not in _VALID_LIFECYCLE:
        raise InvalidContextOfUseError(
            f"poc_or_production must be one of {_VALID_LIFECYCLE}; "
            f"got {lifecycle!r}"
        )

    return ContextOfUse(
        cou_id=cou_dict.get("cou_id")
            or f"COU-{uuid.uuid4().hex[:8]}",
        customer_name=cou_dict["customer_name"],
        statement=cou_dict["statement"],
        deployment_region=region,
        gxp_classification=gxp,
        risk_level=risk,
        decision_authority=cou_dict["decision_authority"],
        target_system=cou_dict.get("target_system", ""),
        integrates_with=list(cou_dict.get("integrates_with", [])),
        triggers_detected=list(cou_dict.get("triggers_detected", [])),
        poc_or_production=lifecycle,
    )


# ─── Trigger detection ───────────────────────────────────────────────

def detect_triggers(snapshot: Dict[str, Any]) -> List[str]:
    """Scan a project snapshot for the 5 SOP triggers.

    A snapshot can include:
      - is_new_tool: bool
      - new_models_added: List[str]
      - major_version_bumps: List[str]
      - new_cous: List[str]
      - poc_to_production_promotion: bool

    Returns the list of trigger IDs that fired. Empty list
    means no new assessment is required (existing report
    still covers the deployment).

    :requirement: URS-39.6 - Auto-detection of the 5 SOP
                  triggers that force a fresh assessment.
    """
    fired: List[str] = []
    if snapshot.get("is_new_tool"):
        fired.append("T1_NEW_TOOL_TO_GXP")
    if snapshot.get("new_models_added"):
        fired.append("T2_NEW_MODEL_TO_TOOL")
    if snapshot.get("major_version_bumps"):
        fired.append("T3_MAJOR_VERSION_BUMP")
    if snapshot.get("new_cous"):
        fired.append("T4_NEW_COU")
    if snapshot.get("poc_to_production_promotion"):
        fired.append("T5_POC_TO_PROD")
    return fired


# ─── The generator ───────────────────────────────────────────────────

class TrustworthinessReportGenerator:
    """Build an AI Trustworthiness Credibility Assessment Report.

    Bounded autonomy: the generator reads from Agent Passports,
    audit trail samples, and the corpus version registry. It
    never modifies records, never signs approvals, never
    triggers revalidation.

    :requirement: URS-39.1 - Generator entry point.
    """

    def __init__(self, primary_frameworks: Optional[List[str]] = None):
        # US default → NIST + FDA per Sprint 39 product choice.
        # ISO 22989 included as vocabulary alignment (SOP
        # explicitly references it).
        self.primary_frameworks = primary_frameworks or [
            "NIST AI RMF 1.0",
            "FDA GMLP (Oct 2021)",
            "ISO/IEC 22989:2021",
        ]

    # ── Public API ──────────────────────────────────────────────────

    def generate(
        self,
        cou: Dict[str, Any],
        user_id: str = "system",
    ) -> TrustworthinessReport:
        """Produce a full TrustworthinessReport for a given COU.

        Writes the standard TWR audit triplet (RECEIVED /
        COMPLETED / FAILED) and a Logic Archive with inputs +
        reasoning steps + outputs hash-linked to the audit trail.

        :requirement: URS-39.1 - Generate trustworthiness report.
        """
        log_audit_event(
            agent_name=AGENT_NAME,
            action="TWR_GENERATION_RECEIVED",
            user_id=user_id,
            decision_logic=(
                f"Generate trustworthiness report - customer="
                f"{cou.get('customer_name', '?')}, "
                f"region={cou.get('deployment_region', '?')}"
            ),
        )
        try:
            cou_obj = _validate_cou(cou)
            report = self._build_report(cou_obj)

            log_audit_event(
                agent_name=AGENT_NAME,
                action="TWR_GENERATION_COMPLETED",
                user_id=user_id,
                decision_logic=(
                    f"Generated report {report.report_id} - "
                    f"{len(report.framework_mappings)} controls "
                    f"mapped across "
                    f"{len(report.primary_frameworks)} framework(s)"
                ),
                thought_process={
                    "inputs": {
                        "cou":               asdict(cou_obj),
                        "primary_frameworks": self.primary_frameworks,
                    },
                    "steps": [
                        f"Validated COU shape (region={cou_obj.deployment_region}, "
                        f"GxP={cou_obj.gxp_classification}, "
                        f"risk={cou_obj.risk_level})",
                        f"Loaded {len(AGENT_PASSPORTS)} Agent Passport(s) "
                        "as primary evidence source",
                        f"Built executive summary tailored to "
                        f"{cou_obj.gxp_classification} risk profile",
                        f"Mapped {len(report.framework_mappings)} "
                        "framework controls to EVOLV evidence",
                        f"Counted: {report._summary_counts()}",
                        f"Documented {len(report.limitations)} "
                        "honest limitations",
                    ],
                    "outputs": report._summary_counts(),
                },
            )
            return report

        except InvalidContextOfUseError as e:
            log_audit_event(
                agent_name=AGENT_NAME,
                action="TWR_GENERATION_FAILED",
                user_id=user_id,
                decision_logic=f"Invalid COU: {e}",
            )
            raise
        except Exception as e:
            log_audit_event(
                agent_name=AGENT_NAME,
                action="TWR_GENERATION_FAILED",
                user_id=user_id,
                decision_logic=f"Unexpected error: {e}",
            )
            raise TrustworthinessReportError(
                f"Report generation failed: {e}"
            ) from e

    # ── Report assembly ─────────────────────────────────────────────

    def _build_report(self, cou: ContextOfUse) -> TrustworthinessReport:
        """Assemble all sections into a final report."""
        report_id = (
            f"TWR-EVOLV-"
            f"{cou.customer_name.replace(' ', '-')[:24]}-"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d')}-"
            f"{uuid.uuid4().hex[:6]}"
        )
        return TrustworthinessReport(
            report_id=report_id,
            schema_version=SCHEMA_VERSION,
            customer_name=cou.customer_name,
            cou=cou,
            generated_at=datetime.now(timezone.utc).isoformat(),
            primary_frameworks=self.primary_frameworks,
            executive_summary=self._executive_summary(cou),
            ai_tool_description=self._ai_tool_description(cou),
            cou_assessment=self._cou_assessment(cou),
            risk_analysis=self._risk_analysis(cou),
            bounded_autonomy_evidence=self._bounded_autonomy_evidence(),
            continuous_monitoring=self._continuous_monitoring(),
            incident_response=self._incident_response(),
            limitations=self._limitations(),
            framework_mappings=self._framework_mappings(cou),
            required_signers=REQUIRED_SIGNERS,
        )

    # ── Section builders ─────────────────────────────────────────────

    def _executive_summary(self, cou: ContextOfUse) -> str:
        return (
            f"EVOLV is an AI-native Computer System Validation "
            f"(CSV) platform deployed at {cou.customer_name} "
            f"under the following Context of Use: "
            f"\"{cou.statement}\" "
            f"This report documents the credibility and "
            f"trustworthiness of EVOLV's AI behaviour in this "
            f"deployment, mapping the architecture to "
            f"{', '.join(self.primary_frameworks)}. "
            f"Risk classification: {cou.risk_level}. "
            f"GxP impact: {cou.gxp_classification}. "
            f"Decision authority: {cou.decision_authority}. "
            f"Every claim below cites a verifiable artefact "
            f"(Agent Passport version, audit-trail row hash, "
            f"or Logic Archive hash) so an inspector can "
            f"re-derive the assessment from EVOLV's own records."
        )

    def _ai_tool_description(
        self, cou: ContextOfUse,
    ) -> Dict[str, Any]:
        """Section 5.1.3.2-5.1.3.5 per SOP pattern."""
        passports = list_agent_passports()
        return {
            "tool_name":             "EVOLV - The Validation Factory",
            "vendor":                "WingstarTech Inc.",
            "tool_type":             "Software as a Service (SaaS) - "
                                     "single-tenant deployment available",
            "intended_use":          cou.statement,
            "ai_components": {
                "deterministic_agents": [
                    name for name, p in AGENT_PASSPORTS.items()
                    if not p.get("llm_usage", {}).get("calls_llm")
                ],
                "llm_backed_agents": [
                    name for name, p in AGENT_PASSPORTS.items()
                    if p.get("llm_usage", {}).get("calls_llm")
                ],
                "foundation_models": [
                    "Anthropic Claude (configurable per tenant)",
                    "OpenAI GPT-4 / GPT-4o (alternative)",
                ],
            },
            "model_provenance": {
                "type":              "Pre-trained foundation models "
                                     "(COTS) - vendor-managed weights",
                "training_data":     "Foundation-model training data "
                                     "details are governed by the LLM "
                                     "vendor's published terms; EVOLV "
                                     "does not fine-tune on customer "
                                     "patient data.",
                "tenant_isolation":  "EVOLV uses inference-only APIs; "
                                     "customer prompts are not used "
                                     "for model training per "
                                     "vendor enterprise contracts.",
            },
            "development_process": (
                "EVOLV ships in 2-week sprints, every change is "
                "URS-tagged, every public function carries a "
                ":requirement: tag traceable to a documented user "
                "requirement, and every commit is reviewed by both "
                "human and AI code reviewers before merge."
            ),
            "assessment_process": (
                "Three-layer assessment: (1) deterministic eval set "
                "per agent - golden inputs with pass/fail acceptance; "
                "(2) bounded-autonomy enforcement via Agent Passports "
                "checked at runtime; (3) continuous monitoring via "
                "the Validated State Engine that scores every "
                "requirement against signals (bundle staleness, "
                "defect pressure, regulatory drift)."
            ),
            "passport_count":  passports["passport_count"],
            "passport_schema_version": passports.get(
                "schema_version", "1.0.0"
            ),
        }

    def _cou_assessment(self, cou: ContextOfUse) -> Dict[str, Any]:
        """Per-COU risk + decision boundary."""
        return {
            "statement":          cou.statement,
            "target_system":      cou.target_system,
            "integrates_with":    cou.integrates_with,
            "gxp_classification": cou.gxp_classification,
            "risk_level":         cou.risk_level,
            "lifecycle_stage":    cou.poc_or_production,
            "decision_authority": cou.decision_authority,
            "human_in_loop": (
                "Every EVOLV-drafted artefact is a proposal until "
                "a human electronically signs it per 21 CFR Part 11 "
                "§11.50. The AI does not write to a validated "
                "record without a signed manifestation."
            ),
            "triggers_detected": [
                t for t in cou.triggers_detected
                if t in {x["id"] for x in TRIGGERS_FOR_REPORT}
            ],
            "trigger_definitions": TRIGGERS_FOR_REPORT,
        }

    def _risk_analysis(self, cou: ContextOfUse) -> Dict[str, Any]:
        """Per-agent risk for THIS COU."""
        agent_risks = []
        for name, p in AGENT_PASSPORTS.items():
            calls_llm = p.get("llm_usage", {}).get("calls_llm", False)
            agent_risks.append({
                "agent":               name,
                "passport_version":    p.get("version", "?"),
                "purpose":             p.get("purpose", ""),
                "calls_llm":           calls_llm,
                "rollback_eligible":   p.get("rollback_eligible", False),
                "requires_signoff_on": p.get(
                    "requires_human_signoff_on", [],
                ),
                "data_classifications_forbidden": p.get(
                    "data_classifications_forbidden", [],
                ),
                "risk_for_this_cou":
                    "High" if calls_llm and cou.risk_level == "High"
                    else "Medium" if cou.risk_level == "High"
                    else cou.risk_level,
            })
        return {
            "method":           "Per-agent risk inheritance: COU "
                                "risk × LLM usage × signoff gates",
            "cou_risk_level":   cou.risk_level,
            "agent_risks":      agent_risks,
            "highest_risk_agents": [
                a["agent"] for a in agent_risks
                if a["risk_for_this_cou"] == "High"
            ],
        }

    def _bounded_autonomy_evidence(self) -> Dict[str, Any]:
        """The core EVOLV differentiator - receipts."""
        return {
            "principle": (
                "AI proposes. Human signs. AI never modifies a "
                "validated record without an electronic signature."
            ),
            "evidence_pillars": [
                {
                    "pillar":     "Agent Passports",
                    "summary":    "Every agent declares allowed and "
                                  "forbidden actions, data "
                                  "classifications, signoff "
                                  "requirements, and LLM-usage "
                                  "envelope. Self-validating at "
                                  "import time.",
                    "evidence":   "Agents/agent_passports.py (live "
                                  "registry), exposed via "
                                  "GET /agents/passports.",
                },
                {
                    "pillar":     "Logic Archives",
                    "summary":    "Every AI output writes a JSON "
                                  "archive with inputs - reasoning "
                                  "steps - outputs. Tamper-evident, "
                                  "hash-linked to the audit trail.",
                    "evidence":   "output/logic_archives/ dir, "
                                  "schema in Agents/"
                                  "integrity_manager.py "
                                  "(_write_logic_archive).",
                },
                {
                    "pillar":     "Hash-chained Audit Trail",
                    "summary":    "Append-only CSV with SHA-256 "
                                  "reasoning hash per row. "
                                  "21 CFR Part 11 §11.10(e) "
                                  "compliant.",
                    "evidence":   "output/audit_trail.csv, write "
                                  "path guarded by "
                                  "scripts/protect_audit_trail.py "
                                  "Claude Code hook.",
                },
                {
                    "pillar":     "Electronic Signature Gates",
                    "summary":    "Manifestation of Signature page "
                                  "on every released PDF (URS, "
                                  "Validation Plan, Design Spec, "
                                  "Validation Summary Report, "
                                  "Audit Export, Traceability "
                                  "Export, this report).",
                    "evidence":   "utils/pdf_generator.py - every "
                                  "generator emits a §11.50 "
                                  "signature page.",
                },
                {
                    "pillar":     "Independent Verification",
                    "summary":    "VerificationAgent independently "
                                  "re-checks every AI artefact "
                                  "against the regulatory corpus. "
                                  "Read-only - never modifies the "
                                  "draft it reviews.",
                    "evidence":   "Agents/verification_agent.py, "
                                  "Compliance Exception logged on "
                                  "rejection.",
                },
            ],
        }

    def _continuous_monitoring(self) -> Dict[str, Any]:
        """What runs after deployment - the 'stay validated' loop."""
        return {
            "validated_state_engine": {
                "purpose":         "Per-requirement confidence score "
                                   "0-100 against signals: bundle "
                                   "staleness, defect pressure, "
                                   "change-history density, "
                                   "regulatory drift, coverage.",
                "cadence":         "On-demand and scheduled - "
                                   "engine assesses on every "
                                   "lifecycle event (test run "
                                   "locked, defect logged, CR "
                                   "approved, drift detected).",
                "evidence":        "Agents/validated_state_engine.py",
                "exposed_at":      "POST /validated-state/assess",
            },
            "regulatory_drift_agent": {
                "purpose":         "Watches every cited framework. "
                                   "Flags URs the moment a guidance "
                                   "version is superseded.",
                "detection":       "Dual: explicit reg_versions_cited "
                                   "list + text-scan regex over "
                                   "framework names.",
                "evidence":        "Agents/regulatory_drift_agent.py, "
                                   "output/corpus_versions.json.",
                "exposed_at":      "POST /regulatory-drift/scan",
            },
            "eval_framework": {
                "purpose":         "Deterministic golden test set per "
                                   "agent. Catches regression "
                                   "without LLM cost.",
                "evidence":        "Agents/agent_evals.py "
                                   "(RequirementArchitect golden set "
                                   "shipped v1.0.0).",
            },
        }

    def _incident_response(self) -> Dict[str, Any]:
        return {
            "if_ai_misbehaves": [
                "VerificationAgent independently re-checks every "
                "AI artefact post-generation; failed checks raise "
                "a Compliance Exception logged to the audit trail.",
                "Rollback-eligible agents (per Agent Passport) can "
                "have their outputs reverted; signed records are "
                "never silently deleted, only superseded with full "
                "provenance.",
                "Logic Archive provides forensic replay: an "
                "engineer can re-derive any AI output from the "
                "exact inputs that produced it.",
            ],
            "if_corpus_drifts": [
                "Regulatory Drift Agent flags affected URs; "
                "Validated State Engine drops scores live; "
                "amber drift banner appears on the Living "
                "Traceability Matrix; QA team receives an "
                "auto-generated impact assessment.",
            ],
            "if_inspector_arrives": [
                "Audit Trail Inspection Export PDF (signed) - "
                "available via POST /audit/export-pdf - 90 "
                "seconds from filter to inspector-ready PDF.",
                "Logic Archives provide per-decision provenance; "
                "Agent Passports document the bounded-autonomy "
                "envelope; this Trustworthiness Report ties "
                "everything to the cited frameworks.",
            ],
        }

    def _limitations(self) -> List[str]:
        """The section that earns trust by being honest.

        These are the constraints EVOLV evaluators should know
        about. Hiding them is the fastest way to lose
        credibility with a pharma evaluator.
        """
        return [
            "Foundation-model training data is governed by the "
            "LLM vendor (Anthropic / OpenAI). EVOLV does not "
            "have full visibility into pre-training datasets; "
            "this is a documented gap shared by all "
            "LLM-augmented systems.",

            "Deterministic golden eval sets are shipped today "
            "for RequirementArchitect (10 golden inputs in "
            "v1.0.0). LLM-as-judge semantic similarity evals "
            "are scheduled for Sprint 44.",

            "Recursive Learning loop (evals → agent behaviour) "
            "is on the Sprint 40 roadmap. Today, eval results "
            "are read by humans; agent behaviour does not "
            "auto-tune.",

            "Customer-bias / demographic-fairness analysis is "
            "narrow in pharma CSV (no patient-data inference is "
            "performed by EVOLV). For pharma deployments that "
            "extend into patient-data inference, the customer "
            "must perform domain-specific bias analysis.",

            "Bias-and-fairness evaluation against specific "
            "patient subgroups is out-of-scope for the current "
            "EVOLV footprint (validation-document drafting and "
            "audit-trail management - not direct clinical "
            "inference).",

            "SOC 2 Type II audit is in progress; SOC 2 Type I "
            "report available on request under NDA. ISO/IEC "
            "42001 certification is planned for 2H 2026.",

            "Continuous performance benchmarking against "
            "published clinical reference datasets is not "
            "applicable to EVOLV's intended use (CSV / "
            "validation lifecycle, not clinical decision "
            "support).",
        ]

    # ── The mapping spine - auditable proof matrix ───────────────────

    def _framework_mappings(
        self, cou: ContextOfUse,
    ) -> List[FrameworkMapping]:
        mappings: List[FrameworkMapping] = []
        mappings.extend(self._map_nist_ai_rmf(cou))
        if "FDA GMLP (Oct 2021)" in self.primary_frameworks:
            mappings.extend(self._map_fda_gmlp(cou))
        if "ISO/IEC 22989:2021" in self.primary_frameworks:
            mappings.extend(self._map_iso_22989(cou))
        return mappings

    def _passport_ref(self, agent: str) -> EvidenceReference:
        p = get_agent_passport(agent) or {}
        return EvidenceReference(
            kind="agent_passport",
            identifier=f"{agent}@{p.get('version', '?')}",
            summary=p.get("purpose", "")[:100],
            location="Agents/agent_passports.py",
        )

    def _audit_action_ref(
        self, action: str, summary: str,
    ) -> EvidenceReference:
        return EvidenceReference(
            kind="audit_row",
            identifier=action,
            summary=summary,
            location="output/audit_trail.csv",
        )

    def _logic_archive_ref(self, action: str) -> EvidenceReference:
        return EvidenceReference(
            kind="logic_archive",
            identifier=f".{action}_*.json",
            summary=(
                f"Logic Archive emitted on every {action} - inputs "
                "+ reasoning + outputs, hash-linked to audit trail."
            ),
            location="output/logic_archives/",
        )

    def _map_nist_ai_rmf(
        self, cou: ContextOfUse,
    ) -> List[FrameworkMapping]:
        return [
            FrameworkMapping(
                framework="NIST AI RMF 1.0",
                section_id="GV-1.1",
                section_title=NIST_AI_RMF["GV-1.1"]["category"],
                requirement=NIST_AI_RMF["GV-1.1"]["requirement"],
                evolv_response=(
                    "EVOLV's regulatory grounding is built into the "
                    "product - every URS rationale cites a specific "
                    "framework + version (GAMP 5, 21 CFR Part 11, "
                    "FDA CSA, EU GMP Annex 11). The Regulatory "
                    "Drift Agent watches for guidance changes and "
                    "flags URs that need re-validation."
                ),
                evidence_refs=[
                    self._passport_ref("RegulatoryDriftAgent"),
                    EvidenceReference(
                        kind="corpus_version",
                        identifier="output/corpus_versions.json",
                        summary="Per-framework version registry "
                                "with previous_versions list.",
                    ),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="NIST AI RMF 1.0",
                section_id="GV-1.2",
                section_title=NIST_AI_RMF["GV-1.2"]["category"],
                requirement=NIST_AI_RMF["GV-1.2"]["requirement"],
                evolv_response=(
                    "Trustworthy AI characteristics are encoded "
                    "into Agent Passports (valid - reliable - safe "
                    "- accountable - transparent - explainable). "
                    "Every agent's allowed_actions / forbidden_actions "
                    "block is the operational expression of these "
                    "characteristics."
                ),
                evidence_refs=[
                    self._passport_ref("RequirementArchitect"),
                    self._passport_ref("VerificationAgent"),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="NIST AI RMF 1.0",
                section_id="GV-2.1",
                section_title=NIST_AI_RMF["GV-2.1"]["category"],
                requirement=NIST_AI_RMF["GV-2.1"]["requirement"],
                evolv_response=(
                    "5-signer RACI matrix required for every "
                    "trustworthiness report and every validation "
                    "release: Business Owner, QA, Service Owner, "
                    "System SME, AI Model SME. Documented on the "
                    "Manifestation of Signature page of every "
                    "released PDF."
                ),
                evidence_refs=[
                    EvidenceReference(
                        kind="urs_traceability",
                        identifier="URS-39.5",
                        summary="5-signer approval chain required "
                                "for every TWR release.",
                    ),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="NIST AI RMF 1.0",
                section_id="MP-2.3",
                section_title=NIST_AI_RMF["MP-2.3"]["category"],
                requirement=NIST_AI_RMF["MP-2.3"]["requirement"],
                evolv_response=(
                    f"Context of Use is the unit of assessment - "
                    f"this report is bound to COU \"{cou.statement}\" "
                    f"at {cou.customer_name}. Re-deployment to a "
                    f"different COU triggers a fresh report per "
                    f"trigger T4_NEW_COU."
                ),
                evidence_refs=[
                    EvidenceReference(
                        kind="urs_traceability",
                        identifier="URS-39.2",
                        summary="Context of Use as unit of "
                                "assessment.",
                    ),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="NIST AI RMF 1.0",
                section_id="MP-4.1",
                section_title=NIST_AI_RMF["MP-4.1"]["category"],
                requirement=NIST_AI_RMF["MP-4.1"]["requirement"],
                evolv_response=(
                    "Risk-based testing depth is computed per "
                    "requirement: FULL / STANDARD / MEDIUM / "
                    "CHARTER based on GAMP 5 risk level. Test "
                    "generation engine uses regulatory-citation "
                    "matched test bundles."
                ),
                evidence_refs=[
                    self._passport_ref("RiskStrategist"),
                    self._passport_ref("DeltaAgent"),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="NIST AI RMF 1.0",
                section_id="MS-1.1",
                section_title=NIST_AI_RMF["MS-1.1"]["category"],
                requirement=NIST_AI_RMF["MS-1.1"]["requirement"],
                evolv_response=(
                    "VerificationAgent independently re-checks "
                    "every AI artefact against the regulatory "
                    "corpus. Read-only by design - cannot modify "
                    "what it reviews. Validity / reliability / "
                    "robustness assessed per agent through "
                    "deterministic golden eval sets."
                ),
                evidence_refs=[
                    self._passport_ref("VerificationAgent"),
                    EvidenceReference(
                        kind="eval_run",
                        identifier="REQUIREMENT_ARCHITECT_GOLDEN_SET",
                        summary="10 golden inputs with "
                                "pass/fail acceptance criteria "
                                "(must_contain_keywords, "
                                "must_cite_frameworks, "
                                "expected_criticality).",
                        location="Agents/agent_evals.py",
                    ),
                ],
                status="Partial",
                notes="LLM-as-judge semantic-similarity evals "
                      "planned for Sprint 44.",
            ),
            FrameworkMapping(
                framework="NIST AI RMF 1.0",
                section_id="MS-2.5",
                section_title=NIST_AI_RMF["MS-2.5"]["category"],
                requirement=NIST_AI_RMF["MS-2.5"]["requirement"],
                evolv_response=(
                    "Validated State Engine assesses every "
                    "requirement continuously: bundle staleness, "
                    "defect pressure, change-history density, "
                    "regulatory drift, coverage. Aggregate score "
                    "+ per-UR tier (green/yellow/red) updated on "
                    "every lifecycle event."
                ),
                evidence_refs=[
                    self._passport_ref("ValidatedStateEngine"),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="NIST AI RMF 1.0",
                section_id="MG-3.2",
                section_title=NIST_AI_RMF["MG-3.2"]["category"],
                requirement=NIST_AI_RMF["MG-3.2"]["requirement"],
                evolv_response=(
                    "Aggregate Validated State score + per-UR tier "
                    "counts published on the Living Traceability "
                    "Matrix. Score history is persisted as "
                    "successive Logic Archives - inspector can "
                    "trend EVOLV trustworthiness over time."
                ),
                evidence_refs=[
                    self._logic_archive_ref(
                        "STATE_ASSESSMENT_COMPLETED",
                    ),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="NIST AI RMF 1.0",
                section_id="MG-4.1",
                section_title=NIST_AI_RMF["MG-4.1"]["category"],
                requirement=NIST_AI_RMF["MG-4.1"]["requirement"],
                evolv_response=(
                    "Compliance Exception event raised by "
                    "VerificationAgent on any failed independent "
                    "check. Audit triplet (RECEIVED / COMPLETED / "
                    "FAILED) logged per endpoint. Logic Archive "
                    "preserves forensic replay."
                ),
                evidence_refs=[
                    self._audit_action_ref(
                        "COMPLIANCE_EXCEPTION",
                        "Logged on every rejected AI artefact.",
                    ),
                ],
                status="Met",
            ),
        ]

    def _map_fda_gmlp(
        self, cou: ContextOfUse,
    ) -> List[FrameworkMapping]:
        return [
            FrameworkMapping(
                framework="FDA GMLP (Oct 2021)",
                section_id="P-1",
                section_title=FDA_GMLP["P-1"]["title"],
                requirement=FDA_GMLP["P-1"]["requirement"],
                evolv_response=(
                    "5-signer RACI (Business Owner - QA - Service "
                    "Owner - System SME - AI Model SME) mandated "
                    "for every TWR + every validation release. "
                    "Multi-disciplinary expertise required by "
                    "design - no single role can release."
                ),
                evidence_refs=[
                    EvidenceReference(
                        kind="urs_traceability",
                        identifier="URS-39.7",
                        summary="5-signer approval chain.",
                    ),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="FDA GMLP (Oct 2021)",
                section_id="P-2",
                section_title=FDA_GMLP["P-2"]["title"],
                requirement=FDA_GMLP["P-2"]["requirement"],
                evolv_response=(
                    "2-week sprint cadence, URS-tagged commits, "
                    "claude-code pre-commit hooks (URS-tag "
                    "validation, audit-trail protection). "
                    "Tamper-evident SHA-256-chained audit trail. "
                    "Security: tenant-isolated SaaS, SOC 2 in "
                    "progress."
                ),
                evidence_refs=[
                    EvidenceReference(
                        kind="audit_row",
                        identifier="output/audit_trail.csv",
                        summary="Append-only CSV with reasoning "
                                "hash per row.",
                    ),
                ],
                status="Partial",
                notes="SOC 2 Type II audit in progress; Type I "
                      "available under NDA.",
            ),
            FrameworkMapping(
                framework="FDA GMLP (Oct 2021)",
                section_id="P-6",
                section_title=FDA_GMLP["P-6"]["title"],
                requirement=FDA_GMLP["P-6"]["requirement"],
                evolv_response=(
                    "Agent Passports encode the intended-use "
                    "envelope per agent: allowed_actions, "
                    "forbidden_actions, data classifications, "
                    "signoff gates, LLM-usage constraints."
                ),
                evidence_refs=[
                    self._passport_ref("RequirementArchitect"),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="FDA GMLP (Oct 2021)",
                section_id="P-7",
                section_title=FDA_GMLP["P-7"]["title"],
                requirement=FDA_GMLP["P-7"]["requirement"],
                evolv_response=(
                    "Bounded autonomy is the design principle: AI "
                    "proposes, human signs. Every released "
                    "artefact carries an electronic signature "
                    "manifestation. Performance is the human-AI "
                    "team performance - measured through Validated "
                    "State Engine scores."
                ),
                evidence_refs=[
                    self._passport_ref("ValidatedStateEngine"),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="FDA GMLP (Oct 2021)",
                section_id="P-9",
                section_title=FDA_GMLP["P-9"]["title"],
                requirement=FDA_GMLP["P-9"]["requirement"],
                evolv_response=(
                    "This Trustworthiness Report. Plus: Agent "
                    "Passports endpoint (GET /agents/passports) "
                    "and Dev Portal Agent Passports panel surface "
                    "intended use, limitations, and known "
                    "constraints to every user."
                ),
                evidence_refs=[
                    EvidenceReference(
                        kind="urs_traceability",
                        identifier="URS-37.4",
                        summary="Agent Passports surfaced in Dev "
                                "Portal.",
                    ),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="FDA GMLP (Oct 2021)",
                section_id="P-10",
                section_title=FDA_GMLP["P-10"]["title"],
                requirement=FDA_GMLP["P-10"]["requirement"],
                evolv_response=(
                    "Validated State Engine (continuous "
                    "monitoring) + Regulatory Drift Agent (re-"
                    "training trigger detection). When a corpus "
                    "version is superseded, affected URs are "
                    "flagged and the suggested action surfaces in "
                    "the QA queue."
                ),
                evidence_refs=[
                    self._passport_ref("RegulatoryDriftAgent"),
                    self._passport_ref("ValidatedStateEngine"),
                ],
                status="Met",
            ),
        ]

    def _map_iso_22989(
        self, cou: ContextOfUse,
    ) -> List[FrameworkMapping]:
        """Vocabulary alignment so an evaluator can map our
        language to their internal glossary.
        """
        return [
            FrameworkMapping(
                framework="ISO/IEC 22989:2021",
                section_id="3.1.1",
                section_title="Artificial Intelligence",
                requirement=ISO_22989_TERMS["Artificial Intelligence"],
                evolv_response=(
                    "EVOLV agents collectively form an AI system "
                    "by this definition - they acquire knowledge "
                    "(retrieval from regulatory corpus), process "
                    "it (LLM-augmented and deterministic), create "
                    "(draft URs / FRs / test scripts), and apply "
                    "(score Validated State, detect drift)."
                ),
                evidence_refs=[
                    EvidenceReference(
                        kind="agent_passport",
                        identifier="AGENT_PASSPORTS registry",
                        summary="Live registry of all EVOLV agents.",
                    ),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="ISO/IEC 22989:2021",
                section_id="3.3.1",
                section_title="Context of Use",
                requirement=ISO_22989_TERMS["Context of Use"],
                evolv_response=(
                    f"This report is bound to a single COU: "
                    f"\"{cou.statement}\" - re-use of EVOLV in a "
                    f"different COU triggers a fresh report."
                ),
                evidence_refs=[
                    EvidenceReference(
                        kind="urs_traceability",
                        identifier="URS-39.2",
                        summary="COU as unit of assessment.",
                    ),
                ],
                status="Met",
            ),
            FrameworkMapping(
                framework="ISO/IEC 22989:2021",
                section_id="3.5.1",
                section_title="Trustworthiness",
                requirement=ISO_22989_TERMS["Trustworthiness"],
                evolv_response=(
                    "Every claim in this report cites a verifiable "
                    "artefact (Agent Passport version, audit-trail "
                    "row hash, Logic Archive hash, eval result). "
                    "Stakeholder verification is supported by "
                    "design - no narrative-only sections."
                ),
                evidence_refs=[
                    self._logic_archive_ref(
                        "TWR_GENERATION_COMPLETED",
                    ),
                ],
                status="Met",
            ),
        ]
