"""
bounded_autonomy_profile.py - Sprint 40 Bounded Autonomy
Profile (BAP) engine.

The diagnostic layer that wraps EVOLV's Trustworthiness
Report. Where the TWR organises evidence around external
frameworks (NIST / FDA GMLP / ISO 22989), the BAP runs a
Context of Use through three diagnostic layers and outputs
a proportional assurance tier - so the question stops being
"did the system pass validation" and becomes "which controls
actually matter for this specific deployment."

The three layers:

  1. Impact Class      - what is the consequence ceiling if
                         this deployment fails?
  2. Failure Envelope  - how can this specific deployment
                         fail, under what conditions, and
                         where is the safe operating boundary?
                         (The layer most current pharma AI
                         governance skips.)
  3. Control            - can the organisation actually
     Sustainability     maintain the controls that matter for
                        this hazard envelope, over time?

Output: the Bounded Autonomy Profile - a tier (BAP-0 through
BAP-4, or BAP-X for Out-of-Envelope exclusion) plus an
inspectable Assurance Argument with named Fragility Markers.

The BAP-X tier is an EXCLUSION, not a higher tier. Some use
cases shouldn't run in their current shape; the temptation in
pharma is always to control upward (more documentation, more
review), but some risks don't yield to that. EVOLV is the
only platform that will tell a customer "this use case
shouldn't exist in this shape" - that honesty is the moat.

Bounded autonomy: this engine never modifies records, never
signs approvals, never triggers revalidation. It reads from
the Context of Use, Agent Passports, audit trail, and
corpus version registry, and emits a proposed BAP + Assurance
Argument that a human approver signs.

:requirement: URS-40.1 - Bounded Autonomy Profile engine.
"""
from __future__ import annotations

import re
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
)
from Agents.integrity_manager import log_audit_event   # noqa: E402


AGENT_NAME = "BoundedAutonomyProfileEngine"
SCHEMA_VERSION = "1.0.0"


# --- Exceptions ------------------------------------------------------

class BoundedAutonomyProfileError(Exception):
    """Base error for the Bounded Autonomy Profile engine."""
    error_code = "CSV-041"


class InvalidProfileInputError(BoundedAutonomyProfileError):
    """COU dict is missing required fields or has bad values."""
    error_code = "CSV-042"


# --- The tier ladder -------------------------------------------------
# Defined as our own scale - EVOLV owns this taxonomy and will
# expand it as the framework matures with each customer
# engagement.

BAP_TIERS: Dict[str, Dict[str, str]] = {
    "BAP-0": {
        "name":     "Productivity",
        "summary":
            "Non-GxP productivity use. Output never enters a "
            "validated workflow. No quality decision is "
            "influenced. Lowest control surface.",
        "examples":
            "Internal meeting summarisation, ad-hoc internal "
            "drafting, productivity assistance.",
    },
    "BAP-1": {
        "name":     "Advisory",
        "summary":
            "GxP-adjacent advisory use. Output informs a "
            "human but does not enter the validated record. "
            "No decision authority delegated to the AI.",
        "examples":
            "Search across regulatory corpus, suggestion of "
            "related URs, exploratory analysis.",
    },
    "BAP-2": {
        "name":     "Controlled Drafting",
        "summary":
            "AI drafts an artefact that enters the validated "
            "workflow ONLY after a qualified human reviews "
            "and signs. AI is a proposing tool; human owns "
            "the record.",
        "examples":
            "Drafting URS / FR / test scripts that flow into "
            "Vault after QA sign-off (EVOLV's typical CoU).",
    },
    "BAP-3": {
        "name":     "Decision-Support",
        "summary":
            "AI output influences a quality judgement. Human "
            "remains the decision-maker but is materially "
            "informed by the AI. Automation bias risk is "
            "elevated; controls scale accordingly.",
        "examples":
            "Per-UR confidence score that gates a release "
            "decision, drift-detection that triggers a CCR.",
    },
    "BAP-4": {
        "name":     "Bounded Action",
        "summary":
            "AI takes action autonomously within a strictly-"
            "deterministic envelope. Action is reversible. "
            "Human oversight is by exception, not by signature.",
        "examples":
            "Auto-grouping audit rows for an inspection export, "
            "auto-tagging of corpus chunks during ingestion.",
    },
    "BAP-X": {
        "name":     "Out-of-Envelope (Exclusion)",
        "summary":
            "Use case should not run in its current shape. "
            "No tier of paperwork rescues it. This is an "
            "EXCLUSION, not a higher tier - the temptation "
            "in pharma is always to control upward; some "
            "risks don't yield to that.",
        "examples":
            "AI signs an electronic signature, AI releases a "
            "batch independently, AI closes a CAPA without "
            "independent review, AI makes a clinical decision.",
    },
}


# --- Hard exclusion rules (BAP-X triggers) ---------------------------
# Pattern matches against the COU statement + decision_authority.
# If any rule fires, the profile is BAP-X regardless of other
# inputs. We DON'T offer to "control upward" - the right move is
# to refuse the shape of the deployment.
#
# Each rule has: pattern (regex), violation (named hazard), why
# (one-line rationale shown to the customer).

# Matching notes (Sprint 44 Trusted Evals hardening):
# - Subject widened from \bai\b to (ai|llm|model) so "The LLM
#   alters each validated record" fires like its AI twin.
# - Middles use [^.;|]*? (clause-bounded) instead of .*? so a
#   rule can never straddle a sentence boundary or leak into the
#   appended decision_authority segment ("... | AI proposes,
#   human signs"). Fixes false positives like "AI signs a
#   summary email; the CSV lead signs the electronic signature."
# - EX-5's human-gate suppressor is clause-bounded too, and
#   'with' is word-bounded so "withOUT review" no longer
#   suppresses the rule.

_SUBJ = r"\b(?:ai|llm|model)\b"

EXCLUSION_RULES: List[Dict[str, Any]] = [
    {
        "id":       "EX-1-SIGN",
        "pattern":  re.compile(
            _SUBJ + r"[^.;|]*?"
            r"\b(sign|signs|signing|signed|authorize|"
            r"authorizes|authorizing|authorized|authorise|"
            r"authorises|authorising|authorised|puts?|"
            r"places?|placing|apply|applies|applying)\b"
            r"[^.;|]*?"
            r"(electronic signature|e-signature|"
            r"approval signature|manifestation of signature|"
            r"digital signature|approvals?\b|signatures?\b)",
            re.IGNORECASE,
        ),
        "violation": "AI executes an electronic signature",
        "why":
            "21 CFR Part 11 Sec.11.50 binds an electronic "
            "signature to a named human. An AI cannot be the "
            "named signatory.",
    },
    {
        "id":       "EX-2-RELEASE",
        "pattern":  re.compile(
            _SUBJ + r"[^.;|]*?"
            r"\b(release|releases|releasing|released|"
            r"approve|approves|approving|approved|authorization|"
            r"authorizes? release|authorises? release)\b"
            r"[^.;|]*?"
            r"(batch|lot|product|manufacturing)",
            re.IGNORECASE,
        ),
        "violation": "AI releases a batch / lot autonomously",
        "why":
            "Batch / lot release is a Qualified Person (QP) "
            "responsibility under GMP. Cannot be delegated to "
            "an AI in any shape.",
    },
    {
        "id":       "EX-3-CAPA",
        "pattern":  re.compile(
            _SUBJ + r"[^.;|]*?"
            r"\b(close|closes|closing|closed|resolve|"
            r"resolves|resolving|resolved|marks? complete|"
            r"closes? out|signs? off|signing off|signed off)\b"
            r"[^.;|]*?"
            r"(capa|deviation|complaint|investigation|"
            r"effectiveness)",
            re.IGNORECASE,
        ),
        "violation": "AI closes a CAPA / deviation autonomously",
        "why":
            "CAPA closure requires independent review and "
            "effectiveness assessment under 21 CFR Part 820 "
            "Sec.820.100. Cannot be the AI's decision.",
    },
    {
        "id":       "EX-4-CLINICAL",
        "pattern":  re.compile(
            _SUBJ + r"[^.;|]*?"
            r"\b(diagnose|diagnoses|diagnosed|diagnosing|"
            r"prescribe|prescribes|prescribed|prescribing|"
            r"dose|dosing|dosed|dosage|calculates? dosing|"
            r"sets? dosing|makes? treatment|"
            r"recommends? treatment|recommended treatment|"
            r"recommending treatment|"
            r"makes? clinical decisions?|determines? therapy|"
            r"clinical decision|clinical judgment|"
            r"patient decision)",
            re.IGNORECASE,
        ),
        "violation": "AI makes a clinical decision affecting a patient",
        "why":
            "Direct clinical decision-making is FDA SaMD "
            "territory and outside EVOLV's intended use. "
            "Different product, different regulatory pathway.",
    },
    {
        "id":       "EX-5-VALIDATED-WRITE",
        "pattern":  re.compile(
            _SUBJ + r"[^.;|]*?"
            r"\b(modify|modifies|modified|modifying|"
            r"alter|alters|altered|altering|update|updates|"
            r"updated|updating|writes? to|written to|persist|"
            r"persists|persisted|auto-corrects?|corrects?)\b"
            r"[^.;|]*?"
            r"(validated record|gxp record|controlled document|"
            r"controlled records|batch record|validated records)"
            r"(?![^.;|]*?(?:after|\bwith\b|requires?|prior to)"
            r"[^.;|]*?(?:human|review|sign-?off|signature|"
            r"approval|qa))",
            re.IGNORECASE,
        ),
        "violation":
            "AI writes directly to a validated record without "
            "human signature gate",
        "why":
            "21 CFR Part 11 Sec.11.10(e) requires that every "
            "modification to a controlled record carries an "
            "accountable signature.",
    },
]


# --- Scenario buckets (Failure Envelope) -----------------------------
# Our own naming - EVOLV's 4-bucket scenario coverage
# classification. Conceptually parallel to common assurance
# vocabulary in regulated industries; the names + thresholds are
# ours to evolve.

SCENARIO_BUCKETS = [
    "Verified Safe",
    "Verified Unsafe (Blocked)",
    "Unmapped",
    "Insufficient Evidence",
]


# --- Dataclasses -----------------------------------------------------

@dataclass
class ImpactClass:
    """Layer 1 - consequence ceiling.

    What is the worst-case consequence if this specific
    deployment fails? The ceiling is set by the COU's GxP
    classification, decision authority, and target system.
    """
    class_id:              str        # IC-0 to IC-4 or IC-X
    name:                  str
    consequence_ceiling:   str
    drivers:               List[str]  # which COU fields drove this
    rationale:             str


@dataclass
class ScenarioBucketEntry:
    """One bucket in the 4-bucket Failure Envelope coverage map."""
    bucket:    str
    count:     int
    examples:  List[str]


@dataclass
class FailureEnvelope:
    """Layer 2 - the diagnostic gap most pharma AI governance
    skips. Names how this specific deployment can fail, under
    what conditions, and where the boundary sits.
    """
    approved_operating_envelope: Dict[str, Any]
    scenario_coverage:           List[ScenarioBucketEntry]
    automation_bias_indicators:  List[str]
    open_hazards:                List[str]
    coverage_score:              int   # 0-100


@dataclass
class ControlSustainability:
    """Layer 3 - whether the organisation can actually maintain
    the controls required for this tier, over time. The argument
    isn't 'do you have controls' (everyone says yes); it's 'can
    you maintain THESE controls for THIS tier'.
    """
    corpus_owner_named:               bool
    vendor_model_change_control_armed: bool
    reviewer_qualification_documented: bool
    deviation_handling_latency_days:   Optional[int]
    drift_monitoring_active:           bool
    capability_score:                  int   # 0-100
    gaps:                              List[str]


@dataclass
class FragilityMarker:
    """The 7th-question answer: what assumption could break and
    invalidate the whole assurance argument.

    Each Fragility Marker is a named assumption + an explicit
    watch signal + a named owner. This is the standing-monitoring
    contract that prevents a safety argument from becoming a
    fossil six months after deployment.
    """
    assumption:     str
    if_broken_then: str
    watch_signal:   str
    owner_role:     str       # who watches this signal


@dataclass
class AssuranceArgument:
    """The integrated 7-question argument structure.

    A qualified human stands in front of QA / inspector and
    walks this chain. It's not paperwork; it's defensibility.

    Differs from a traditional validation summary in that it
    names its own fragility (Q7) - the assumptions that, if
    they shift, would invalidate the argument.
    """
    q1_approved_purpose:       str
    q2_out_of_scope:           List[str]
    q3_hazard_mechanisms:      List[str]
    q4_controls_per_hazard:    List[Dict[str, str]]
    q5_evidence_per_control:   List[Dict[str, str]]
    q6_residual_risk_owners:   List[Dict[str, str]]
    q7_fragility_markers:      List[FragilityMarker]


@dataclass
class BoundedAutonomyProfile:
    """The full BAP output - the diagnostic engine's verdict.

    Self-contained: an inspector with this dict + the audit
    trail + the Logic Archive directory can re-derive every
    claim. The tier is the result; the three-layer stack is
    the diagnostic.
    """
    profile_id:               str
    schema_version:           str
    cou:                      Dict[str, Any]   # full COU dict
    generated_at:             str

    # The three-layer stack outputs
    impact_class:             ImpactClass
    failure_envelope:         FailureEnvelope
    control_sustainability:   ControlSustainability

    # The output tier
    tier_id:                  str
    tier_name:                str
    tier_summary:             str
    tier_rationale:           List[str]
    is_exclusion:             bool   # True iff BAP-X

    # The integrated assurance argument
    assurance_argument:       AssuranceArgument

    # Operational outputs
    required_controls_at_tier: List[str]
    next_actions:             List[str]
    reasoning_chain:          List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id":               self.profile_id,
            "schema_version":           self.schema_version,
            "cou":                      self.cou,
            "generated_at":             self.generated_at,
            "impact_class":             asdict(self.impact_class),
            "failure_envelope":         {
                "approved_operating_envelope":
                    self.failure_envelope.approved_operating_envelope,
                "scenario_coverage": [
                    asdict(b)
                    for b in self.failure_envelope.scenario_coverage
                ],
                "automation_bias_indicators":
                    self.failure_envelope.automation_bias_indicators,
                "open_hazards": self.failure_envelope.open_hazards,
                "coverage_score": self.failure_envelope.coverage_score,
            },
            "control_sustainability": asdict(self.control_sustainability),
            "tier_id":                self.tier_id,
            "tier_name":              self.tier_name,
            "tier_summary":           self.tier_summary,
            "tier_rationale":         self.tier_rationale,
            "is_exclusion":           self.is_exclusion,
            "assurance_argument": {
                "q1_approved_purpose":
                    self.assurance_argument.q1_approved_purpose,
                "q2_out_of_scope":
                    self.assurance_argument.q2_out_of_scope,
                "q3_hazard_mechanisms":
                    self.assurance_argument.q3_hazard_mechanisms,
                "q4_controls_per_hazard":
                    self.assurance_argument.q4_controls_per_hazard,
                "q5_evidence_per_control":
                    self.assurance_argument.q5_evidence_per_control,
                "q6_residual_risk_owners":
                    self.assurance_argument.q6_residual_risk_owners,
                "q7_fragility_markers": [
                    asdict(f)
                    for f in
                    self.assurance_argument.q7_fragility_markers
                ],
            },
            "required_controls_at_tier":
                self.required_controls_at_tier,
            "next_actions":           self.next_actions,
            "reasoning_chain":        self.reasoning_chain,
        }


# --- Per-tier required-control catalogue -----------------------------
# What controls actually matter at each tier? Customer's most
# common question: "what do I need by Monday?" - this is the
# answer.

REQUIRED_CONTROLS_BY_TIER: Dict[str, List[str]] = {
    "BAP-0": [
        "Acceptable-use policy covering productivity AI",
        "Annual user training on AI safe-use",
    ],
    "BAP-1": [
        "Acceptable-use policy",
        "Annual user training",
        "Audit-trail logging of advisory queries and responses",
        "Quarterly spot-check of output quality by SME",
    ],
    "BAP-2": [
        "Acceptable-use policy",
        "Annual user training including failure-mode awareness",
        "Audit-trail logging of every AI draft + reviewer change",
        "Mandatory human sign-off before record persistence",
        "Independent verification of AI output against regulatory corpus",
        "Per-draft Logic Archive (replayable reasoning chain)",
        "Quarterly eval set + regression check",
        "Named corpus owner with standing responsibility",
        "Vendor-model-change assessment process (active)",
    ],
    "BAP-3": [
        "Everything BAP-2 plus:",
        "Statistical acceptance criteria with numerical thresholds",
        "Automation-bias monitoring (reviewer modification rate)",
        "Bimonthly review of AI influence on quality outcomes",
        "Documented decision boundary (when does AI input override / inform / advise)",
        "Hallucination rate measurement per LLM-backed agent",
    ],
    "BAP-4": [
        "Everything BAP-3 plus:",
        "Cryptographically-bounded action envelope (programmatic enforcement)",
        "Auto-rollback path for every autonomous action",
        "Real-time anomaly detection on action stream",
        "Independent reviewer audit of action stream (weekly minimum)",
    ],
    "BAP-X": [
        "REFUSE the deployment in current shape",
        "Re-scope to a tier with an acceptable control surface",
        "Document the refusal + the re-scope path",
    ],
}


# --- The engine ------------------------------------------------------

class BoundedAutonomyProfileEngine:
    """Three-layer diagnostic engine.

    Deterministic in v1.0.0 (predictable for demos and for
    audit). The three layer outputs are produced by rule-based
    analysis over the COU + Agent Passports + audit trail
    samples. LLM-augmented scenario discovery lands Sprint 42.

    :requirement: URS-40.1 - BAP engine.
    """

    # -- Public API -------------------------------------------------

    def assess(
        self,
        cou: Dict[str, Any],
        user_id: str = "system",
    ) -> BoundedAutonomyProfile:
        """Run a Context of Use through the three-layer stack and
        emit a Bounded Autonomy Profile.

        Writes the standard BAP_ASSESSMENT triplet (RECEIVED /
        COMPLETED / FAILED) and a Logic Archive with the full
        reasoning chain hash-linked to the audit trail.

        :requirement: URS-40.1 - Generate BAP via three-layer
                      diagnostic.
        """
        log_audit_event(
            agent_name=AGENT_NAME,
            action="BAP_ASSESSMENT_RECEIVED",
            user_id=user_id,
            decision_logic=(
                f"BAP assessment for "
                f"customer={cou.get('customer_name', '?')}, "
                f"region={cou.get('deployment_region', '?')}"
            ),
        )
        try:
            self._validate_cou(cou)
            profile = self._build_profile(cou)

            log_audit_event(
                agent_name=AGENT_NAME,
                action="BAP_ASSESSMENT_COMPLETED",
                user_id=user_id,
                decision_logic=(
                    f"Profile {profile.profile_id} -> "
                    f"{profile.tier_id} ({profile.tier_name})"
                ),
                thought_process={
                    "inputs": {"cou": cou},
                    "steps":  profile.reasoning_chain,
                    "outputs": {
                        "tier_id":         profile.tier_id,
                        "tier_name":       profile.tier_name,
                        "is_exclusion":    profile.is_exclusion,
                        "coverage_score":
                            profile.failure_envelope.coverage_score,
                        "capability_score":
                            profile.control_sustainability
                            .capability_score,
                    },
                },
            )
            return profile

        except InvalidProfileInputError as e:
            log_audit_event(
                agent_name=AGENT_NAME,
                action="BAP_ASSESSMENT_FAILED",
                user_id=user_id,
                decision_logic=f"Invalid COU: {e}",
            )
            raise
        except Exception as e:
            log_audit_event(
                agent_name=AGENT_NAME,
                action="BAP_ASSESSMENT_FAILED",
                user_id=user_id,
                decision_logic=f"Unexpected error: {e}",
            )
            raise BoundedAutonomyProfileError(
                f"BAP assessment failed: {e}"
            ) from e

    # -- Validation -------------------------------------------------

    @staticmethod
    def _validate_cou(cou: Dict[str, Any]) -> None:
        required = [
            "customer_name", "statement", "gxp_classification",
            "risk_level", "decision_authority",
        ]
        missing = [f for f in required if not cou.get(f)]
        if missing:
            raise InvalidProfileInputError(
                f"COU is missing required field(s): {missing}"
            )

    # -- Assembly ---------------------------------------------------

    def _build_profile(
        self, cou: Dict[str, Any],
    ) -> BoundedAutonomyProfile:
        reasoning: List[str] = []

        # ---- Hard-exclusion check FIRST ----
        exclusion_hits = self._check_exclusion_rules(cou, reasoning)

        # ---- Layer 1: Impact Class ----
        impact = self._impact_class(cou, reasoning, exclusion_hits)

        # ---- Layer 2: Failure Envelope ----
        envelope = self._failure_envelope(cou, reasoning)

        # ---- Layer 3: Control Sustainability ----
        sustainability = self._control_sustainability(cou, reasoning)

        # ---- Output tier ----
        tier_id, rationale_chain = self._assign_tier(
            cou, impact, envelope, sustainability, exclusion_hits,
        )
        tier_meta = BAP_TIERS[tier_id]
        reasoning.extend([f"Tier decision: {r}" for r in rationale_chain])

        # ---- Assurance Argument ----
        argument = self._assurance_argument(
            cou, tier_id, envelope, sustainability, exclusion_hits,
        )

        # ---- Required controls + next actions ----
        required = REQUIRED_CONTROLS_BY_TIER.get(tier_id, [])
        next_actions = self._next_actions(
            cou, tier_id, envelope, sustainability, exclusion_hits,
        )

        profile_id = (
            f"BAP-EVOLV-"
            f"{str(cou.get('customer_name', 'x')).replace(' ', '-')[:24]}-"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d')}-"
            f"{uuid.uuid4().hex[:6]}"
        )

        return BoundedAutonomyProfile(
            profile_id=profile_id,
            schema_version=SCHEMA_VERSION,
            cou=cou,
            generated_at=datetime.now(timezone.utc).isoformat(),
            impact_class=impact,
            failure_envelope=envelope,
            control_sustainability=sustainability,
            tier_id=tier_id,
            tier_name=tier_meta["name"],
            tier_summary=tier_meta["summary"],
            tier_rationale=rationale_chain,
            is_exclusion=(tier_id == "BAP-X"),
            assurance_argument=argument,
            required_controls_at_tier=required,
            next_actions=next_actions,
            reasoning_chain=reasoning,
        )

    # -- Exclusion (BAP-X) detection --------------------------------

    @staticmethod
    def _check_exclusion_rules(
        cou: Dict[str, Any], reasoning: List[str],
    ) -> List[Dict[str, Any]]:
        """Apply hard exclusion rules. Any hit forces BAP-X."""
        hits: List[Dict[str, Any]] = []
        statement = str(cou.get("statement", ""))
        authority = str(cou.get("decision_authority", ""))
        haystack = f"{statement} | {authority}"
        for rule in EXCLUSION_RULES:
            if rule["pattern"].search(haystack):
                hits.append({
                    "rule_id":   rule["id"],
                    "violation": rule["violation"],
                    "why":       rule["why"],
                })
                reasoning.append(
                    f"Exclusion rule {rule['id']} fired: "
                    f"{rule['violation']}"
                )
        if not hits:
            reasoning.append(
                "No exclusion rules fired - deployment shape "
                "is acceptable in principle; tier set by "
                "impact + envelope + sustainability."
            )
        return hits

    # -- Layer 1: Impact Class --------------------------------------

    @staticmethod
    def _impact_class(
        cou: Dict[str, Any],
        reasoning: List[str],
        exclusion_hits: List[Dict[str, Any]],
    ) -> ImpactClass:
        gxp = str(cou.get("gxp_classification", ""))
        risk = str(cou.get("risk_level", ""))
        statement = str(cou.get("statement", "")).lower()
        drivers: List[str] = []

        if exclusion_hits:
            reasoning.append(
                "Impact Class: IC-X - one or more hard "
                "exclusion rules fired; deployment shape is "
                "out-of-envelope."
            )
            return ImpactClass(
                class_id="IC-X",
                name="Out-of-Envelope",
                consequence_ceiling=(
                    "Exclusion - deployment cannot proceed in "
                    "this shape regardless of controls applied."
                ),
                drivers=[h["violation"] for h in exclusion_hits],
                rationale=(
                    "Hard exclusion rule fired; bypassing "
                    "consequence-ceiling computation."
                ),
            )

        # Standard mapping
        if gxp == "Non-GxP":
            cid, name = "IC-0", "Productivity"
            ceiling = "Internal-only impact, no regulatory exposure."
        elif gxp == "GxP Indirect":
            cid, name = "IC-1", "Indirect Regulatory"
            ceiling = (
                "Could affect a downstream validated record; "
                "no direct quality decision."
            )
        elif gxp == "GxP Direct" and risk == "Low":
            cid, name = "IC-2", "Direct - Low Risk"
            ceiling = (
                "Touches the validated workflow; failure "
                "produces a documented deviation but not a "
                "quality event."
            )
        elif gxp == "GxP Direct" and risk == "Medium":
            cid, name = "IC-3", "Direct - Medium Risk"
            ceiling = (
                "Failure could lead to product-quality "
                "investigation; reportable deviation likely."
            )
        else:   # GxP Direct + High
            cid, name = "IC-4", "Direct - High Risk"
            ceiling = (
                "Failure could affect patient safety, "
                "regulatory compliance, or product release; "
                "highest consequence ceiling."
            )

        drivers.append(f"GxP classification: {gxp}")
        drivers.append(f"Risk level: {risk}")

        # Bump up if certain keywords present
        if any(k in statement for k in
               ["batch release", "release decision", "qp",
                "qualified person"]):
            drivers.append(
                "Statement mentions batch / release decision"
            )

        reasoning.append(
            f"Impact Class: {cid} ({name}) - drivers={drivers}"
        )
        return ImpactClass(
            class_id=cid,
            name=name,
            consequence_ceiling=ceiling,
            drivers=drivers,
            rationale=(
                f"Mapped from GxP={gxp}, risk={risk}, plus "
                f"statement keyword scan."
            ),
        )

    # -- Layer 2: Failure Envelope ----------------------------------

    def _failure_envelope(
        self, cou: Dict[str, Any], reasoning: List[str],
    ) -> FailureEnvelope:
        statement = str(cou.get("statement", "")).lower()

        # Build the Approved Operating Envelope (AOE) from
        # Agent Passport allowed_actions union, scoped to this
        # COU's target system.
        allowed_actions: List[str] = []
        forbidden_actions: List[str] = []
        for name, passport in AGENT_PASSPORTS.items():
            allowed_actions.extend(passport.get("allowed_actions", []))
            forbidden_actions.extend(
                passport.get("forbidden_actions", [])
            )
        aoe = {
            "target_system":     cou.get("target_system", ""),
            "deployment_region": cou.get("deployment_region", ""),
            "in_scope_actions": sorted(set(allowed_actions)),
            "out_of_scope_actions":
                sorted(set(forbidden_actions)),
            "in_scope_data_classifications": [
                "regulatory_corpus", "project_planData",
                "requirement_meta", "user_prompt",
                "urs_output_under_review",
            ],
            "out_of_scope_data_classifications": [
                "patient_data", "audit_trail_raw",
                "signature_secrets",
                "other_customers_tenant_data",
            ],
        }

        # Scenario coverage map (4 buckets).
        scenario_coverage: List[ScenarioBucketEntry] = []

        # Verified Safe - things our eval sets cover
        verified_safe_examples: List[str] = []
        if "ur" in statement or "urs" in statement \
                or "requirement" in statement:
            verified_safe_examples.append(
                "URS drafting from natural-language brief "
                "(REQUIREMENT_ARCHITECT_GOLDEN_SET, 10 inputs)"
            )
        verified_safe_examples.append(
            "Independent re-check via VerificationAgent "
            "(3 deterministic checks per artefact)"
        )
        verified_safe_examples.append(
            "Per-UR confidence scoring via Validated State Engine"
        )
        scenario_coverage.append(ScenarioBucketEntry(
            bucket="Verified Safe",
            count=len(verified_safe_examples),
            examples=verified_safe_examples,
        ))

        # Verified Unsafe (Blocked) - via Agent Passport
        # forbidden_actions
        scenario_coverage.append(ScenarioBucketEntry(
            bucket="Verified Unsafe (Blocked)",
            count=len(set(forbidden_actions)),
            examples=sorted(set(forbidden_actions))[:8],
        ))

        # Unmapped - failure modes we haven't characterised
        unmapped: List[str] = [
            "Hallucination rate per LLM-backed agent (not yet "
            "measured numerically - Sprint 44 deliverable)",
            "Adversarial-prompt resilience (not yet eval-covered)",
            "Multi-source citation conflict resolution (relies "
            "on most-recent corpus version, not explicit "
            "disagreement detection)",
        ]
        scenario_coverage.append(ScenarioBucketEntry(
            bucket="Unmapped",
            count=len(unmapped),
            examples=unmapped,
        ))

        # Insufficient Evidence - may be fine, lack proof
        insufficient: List[str] = [
            "Performance under high-concurrency multi-tenant "
            "load (single-tenant pilots only to date)",
            "Behaviour on non-English regulatory corpus "
            "(English-only ingestion currently)",
            "Reviewer-modification rate as proxy for "
            "automation bias (telemetry not yet captured)",
        ]
        scenario_coverage.append(ScenarioBucketEntry(
            bucket="Insufficient Evidence",
            count=len(insufficient),
            examples=insufficient,
        ))

        # Automation bias indicators - structural, not measured
        # yet (Sprint 41 measurement work)
        automation_bias: List[str] = [
            "Per-Logic-Archive reviewer-modification-rate not "
            "yet captured as telemetry",
            "Reviewer time-to-sign not yet measured per draft",
            "Streak detection (reviewer signs N drafts in a "
            "row without modification) not yet implemented",
        ]

        # Open hazards - named, not controlled
        open_hazards: List[str] = []
        if cou.get("gxp_classification") == "GxP Direct":
            open_hazards.append(
                "Reviewer treats AI draft as recommendation "
                "rather than draft (automation bias) - "
                "structural risk at GxP Direct"
            )
        if cou.get("risk_level") == "High":
            open_hazards.append(
                "Foundation-model behaviour shift on vendor "
                "update could change output distribution - "
                "Sprint 41 vendor-change-control work pending"
            )

        # Coverage score - 0-100, rewarding verified-safe and
        # verified-unsafe, penalising unmapped and insufficient
        v_safe = scenario_coverage[0].count
        v_unsafe = scenario_coverage[1].count
        unmapped_count = scenario_coverage[2].count
        insufficient_count = scenario_coverage[3].count
        positive = (v_safe * 8) + (v_unsafe * 4)
        negative = (unmapped_count * 6) + (insufficient_count * 5)
        coverage_score = max(0, min(100, positive - negative + 50))

        reasoning.append(
            f"Failure Envelope: coverage_score={coverage_score}/100, "
            f"open_hazards={len(open_hazards)}, "
            f"automation_bias_indicators={len(automation_bias)}"
        )

        return FailureEnvelope(
            approved_operating_envelope=aoe,
            scenario_coverage=scenario_coverage,
            automation_bias_indicators=automation_bias,
            open_hazards=open_hazards,
            coverage_score=coverage_score,
        )

    # -- Layer 3: Control Sustainability ----------------------------

    def _control_sustainability(
        self, cou: Dict[str, Any], reasoning: List[str],
    ) -> ControlSustainability:
        # In v1.0.0 these are signal-driven defaults. The next
        # sprint wires them to actual observability (audit
        # trail row patterns, corpus_versions.json owner field,
        # vendor-change records).
        corpus_owner_named = False
        vendor_change_armed = False
        reviewer_qualification = False
        deviation_latency = None
        drift_monitoring_active = True   # Drift Agent shipped

        gaps: List[str] = []
        if not corpus_owner_named:
            gaps.append(
                "Standing corpus owner not yet named in "
                "output/corpus_versions.json"
            )
        if not vendor_change_armed:
            gaps.append(
                "Vendor (Anthropic / OpenAI) model-update "
                "change-control process not formally documented"
            )
        if not reviewer_qualification:
            gaps.append(
                "Reviewer qualification per failure mode not "
                "yet tracked - reviewers currently treated as "
                "uniformly qualified"
            )
        if deviation_latency is None:
            gaps.append(
                "Deviation-to-CAPA latency not yet measured "
                "(no telemetry hook in change-control router)"
            )

        positives = (
            (50 if drift_monitoring_active else 0)
            + (10 if corpus_owner_named else 0)
            + (10 if vendor_change_armed else 0)
            + (10 if reviewer_qualification else 0)
            + (20 if deviation_latency is not None else 0)
        )

        reasoning.append(
            f"Control Sustainability: capability_score="
            f"{positives}/100, gaps={len(gaps)}"
        )
        return ControlSustainability(
            corpus_owner_named=corpus_owner_named,
            vendor_model_change_control_armed=vendor_change_armed,
            reviewer_qualification_documented=reviewer_qualification,
            deviation_handling_latency_days=deviation_latency,
            drift_monitoring_active=drift_monitoring_active,
            capability_score=positives,
            gaps=gaps,
        )

    # -- Tier assignment --------------------------------------------

    @staticmethod
    def _assign_tier(
        cou: Dict[str, Any],
        impact: ImpactClass,
        envelope: FailureEnvelope,
        sustainability: ControlSustainability,
        exclusion_hits: List[Dict[str, Any]],
    ) -> Tuple[str, List[str]]:
        rationale: List[str] = []

        # Exclusion override
        if exclusion_hits:
            rationale.append(
                "One or more hard exclusion rules fired - "
                "tier is BAP-X regardless of other inputs."
            )
            for h in exclusion_hits:
                rationale.append(
                    f"  - {h['rule_id']}: {h['violation']}"
                )
            return "BAP-X", rationale

        # Base tier from Impact Class
        impact_to_base = {
            "IC-0": "BAP-0",
            "IC-1": "BAP-1",
            "IC-2": "BAP-2",
            "IC-3": "BAP-2",
            "IC-4": "BAP-2",
        }
        base = impact_to_base.get(impact.class_id, "BAP-2")
        rationale.append(
            f"Base tier from Impact Class {impact.class_id}: {base}"
        )

        # Promote on decision-authority signals
        statement = str(cou.get("statement", "")).lower()
        authority = str(cou.get("decision_authority", "")).lower()
        promote_to_3 = False
        promote_to_4 = False

        if any(k in statement for k in
               ["confidence score", "drift", "gates a release",
                "influences", "informs quality"]):
            promote_to_3 = True
            rationale.append(
                "Statement suggests AI output materially "
                "informs a quality judgement - promote to BAP-3."
            )
        if "autonomous" in authority and "human" not in authority:
            promote_to_4 = True
            rationale.append(
                "Decision authority is autonomous-without-human - "
                "promote to BAP-4 (still bounded; otherwise BAP-X)."
            )

        if promote_to_4:
            tier = "BAP-4"
        elif promote_to_3:
            tier = "BAP-3"
        else:
            tier = base

        # Demote if coverage_score is very low (envelope is wide
        # open - can't justify higher tier)
        if envelope.coverage_score < 30 and tier in ("BAP-3", "BAP-4"):
            rationale.append(
                f"Coverage score {envelope.coverage_score}/100 "
                "too low for proposed tier - demote one level."
            )
            tier = "BAP-2" if tier == "BAP-3" else "BAP-3"

        # Flag if sustainability is too low for the tier
        if sustainability.capability_score < 60 \
                and tier in ("BAP-3", "BAP-4"):
            rationale.append(
                f"Control Sustainability {sustainability.capability_score}"
                f"/100 below threshold for {tier} - flag for "
                "remediation but tier holds."
            )

        return tier, rationale

    # -- Assurance Argument (7 questions) ---------------------------

    @staticmethod
    def _assurance_argument(
        cou: Dict[str, Any],
        tier_id: str,
        envelope: FailureEnvelope,
        sustainability: ControlSustainability,
        exclusion_hits: List[Dict[str, Any]],
    ) -> AssuranceArgument:
        statement = cou.get("statement", "")

        # Q1 - approved purpose
        q1 = statement

        # Q2 - explicitly out of scope
        q2 = list(envelope.approved_operating_envelope
                  .get("out_of_scope_actions", []))[:6]
        if exclusion_hits:
            q2.append(
                "Per hard exclusion rule(s) fired: "
                + ", ".join(h["violation"] for h in exclusion_hits)
            )

        # Q3 - hazard mechanisms
        q3: List[str] = list(envelope.open_hazards)
        for bucket in envelope.scenario_coverage:
            if bucket.bucket in ("Unmapped", "Insufficient Evidence"):
                q3.extend(bucket.examples)

        # Q4 - controls per hazard
        q4: List[Dict[str, str]] = [
            {
                "hazard": "Output contradicts regulatory corpus",
                "control": "VerificationAgent independent re-check",
            },
            {
                "hazard": "Output enters validated record without review",
                "control": "Mandatory human electronic signature gate "
                           "(21 CFR Part 11 Sec.11.50)",
            },
            {
                "hazard": "Cited regulatory version drifts",
                "control": "RegulatoryDriftAgent + corpus version registry",
            },
            {
                "hazard": "Reviewer signs without engaging "
                          "(automation bias)",
                "control": "Reviewer-modification-rate telemetry "
                           "(Sprint 41 deliverable)",
            },
        ]

        # Q5 - evidence per control
        q5: List[Dict[str, str]] = [
            {
                "control": "VerificationAgent independent re-check",
                "evidence": "Per-artefact Compliance Exception audit "
                            "row + Logic Archive",
            },
            {
                "control": "21 CFR Part 11 Sec.11.50 signature gate",
                "evidence": "Manifestation of Signature page on every "
                            "released PDF + SHA-256 chained audit trail",
            },
            {
                "control": "RegulatoryDriftAgent",
                "evidence": "DRIFT_SCAN_COMPLETED audit rows + "
                            "DriftScanReport persisted as Logic Archive",
            },
        ]

        # Q6 - residual risk owners
        q6: List[Dict[str, str]] = [
            {
                "residual_risk":
                    "Hallucination rate per LLM-backed agent not "
                    "yet measured numerically",
                "owner_role": "AI Model SME at EVOLV",
            },
            {
                "residual_risk":
                    "Multi-source corpus disagreement handling "
                    "relies on most-recent version, no explicit "
                    "conflict detection",
                "owner_role": "AI Model SME at EVOLV",
            },
        ]

        # Q7 - Fragility Markers (the assumption-watch contract)
        q7: List[FragilityMarker] = [
            FragilityMarker(
                assumption=(
                    "The LLM vendor (Anthropic / OpenAI) does not "
                    "silently change model behaviour in a way that "
                    "shifts our output distribution."
                ),
                if_broken_then=(
                    "Output distribution drift could invalidate all "
                    "prior eval-set results; trustworthiness claims "
                    "become stale."
                ),
                watch_signal=(
                    "Vendor model version field on every API call "
                    "+ regression-eval re-run on version change."
                ),
                owner_role="AI Model SME at EVOLV",
            ),
            FragilityMarker(
                assumption=(
                    "Reviewers approving AI drafts engage critically "
                    "rather than rubber-stamping (automation bias "
                    "remains below threshold)."
                ),
                if_broken_then=(
                    "AI errors flow into validated records uncaught; "
                    "trust degrades silently; eventual audit finding."
                ),
                watch_signal=(
                    "Reviewer-modification-rate per Logic Archive + "
                    "reviewer-time-to-sign + streak detection "
                    "(Sprint 41 deliverable)."
                ),
                owner_role=(
                    "Customer QA Lead - shared with EVOLV AI Model SME"
                ),
            ),
            FragilityMarker(
                assumption=(
                    "The regulatory corpus EVOLV is grounded against "
                    "remains the version cited in approved URs."
                ),
                if_broken_then=(
                    "URs cite superseded guidance; inspector finds "
                    "outdated grounding; revalidation required."
                ),
                watch_signal=(
                    "Regulatory Drift Agent scan results + "
                    "corpus_versions.json change history."
                ),
                owner_role="Customer Corpus Owner (standing role)",
            ),
            FragilityMarker(
                assumption=(
                    "EVOLV's bounded-autonomy envelope as encoded in "
                    "Agent Passports is enforced at runtime."
                ),
                if_broken_then=(
                    "An agent could perform a forbidden_action "
                    "without runtime check; entire trustworthiness "
                    "argument collapses."
                ),
                watch_signal=(
                    "Self-validation on import (already shipping) + "
                    "runtime-action vs Agent Passport check "
                    "(Sprint 41 deliverable)."
                ),
                owner_role="EVOLV Engineering Lead",
            ),
        ]

        return AssuranceArgument(
            q1_approved_purpose=q1,
            q2_out_of_scope=q2,
            q3_hazard_mechanisms=q3,
            q4_controls_per_hazard=q4,
            q5_evidence_per_control=q5,
            q6_residual_risk_owners=q6,
            q7_fragility_markers=q7,
        )

    # -- Next actions -----------------------------------------------

    @staticmethod
    def _next_actions(
        cou: Dict[str, Any],
        tier_id: str,
        envelope: FailureEnvelope,
        sustainability: ControlSustainability,
        exclusion_hits: List[Dict[str, Any]],
    ) -> List[str]:
        actions: List[str] = []
        if exclusion_hits:
            actions.append(
                "REFUSE deployment in current shape. Re-scope "
                "the CoU to remove the exclusion trigger and "
                "re-run BAP assessment."
            )
            actions.append(
                "Document the refusal + the re-scope path in "
                "the customer's change-control system."
            )
            return actions

        if envelope.coverage_score < 60:
            actions.append(
                f"Failure-Envelope coverage at "
                f"{envelope.coverage_score}/100. Close at least "
                f"one Unmapped or Insufficient-Evidence "
                f"scenario before promoting to a higher tier."
            )
        if sustainability.capability_score < 60:
            actions.append(
                f"Control Sustainability at "
                f"{sustainability.capability_score}/100. "
                f"Close gaps before signing: "
                + "; ".join(sustainability.gaps)
            )
        if tier_id in ("BAP-3", "BAP-4"):
            actions.append(
                "Ship automation-bias telemetry "
                "(reviewer-modification rate, time-to-sign) - "
                "Sprint 41 deliverable, gating prerequisite "
                "for sustained operation at this tier."
            )
        if tier_id in ("BAP-2", "BAP-3", "BAP-4") \
                and not sustainability.corpus_owner_named:
            actions.append(
                "Name a standing Corpus Owner in "
                "output/corpus_versions.json (single human, "
                "not a team). Required for sustained operation."
            )
        if not actions:
            actions.append(
                "No blocking gaps identified - profile may be "
                "signed by the 5-signer RACI and the deployment "
                "may proceed at the named tier."
            )
        return actions
