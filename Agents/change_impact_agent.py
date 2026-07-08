"""
change_impact_agent.py — Sprint 36 Change Impact Assessment.

Given a Change Request (CR text + active project snapshot), the
ChangeImpactAgent identifies which URs / FRs / test bundles the
change affects, computes the risk delta, and proposes a structured
Change Impact Assessment (CIA) document for QA review.

The principle: **AI proposes, human signs, then revalidation runs.**

- The agent never triggers revalidation directly.
- The agent never modifies existing URs or risk classifications.
- The CIA is a *draft* until a human signs the Change Control Record
  (CCR). Only after the CCR is signed does the revalidation sub-run
  spawn on Verify.

This is bounded autonomy applied to the change-management loop —
exactly the architecture Nuno Valério described in *The Trust
Architecture* and Salim Ismail described in ExO 3.0's "Decide" layer
inside the Permission Envelope.

The agent's Permission Envelope is declared in
`Agents/agent_passports.py` under the key "ChangeImpactAgent".

:requirement: URS-36.1 - Generate AI-drafted Change Impact Assessment
              from a CR + active project, identifying affected URs /
              FRs / test bundles and computing risk delta.
:requirement: URS-36.2 - Every CIA generation writes a Logic Archive
              with inputs, reasoning steps, and outputs hash-linked
              to the audit trail.
:requirement: URS-36.3 - The agent never modifies existing URs or
              risk classifications. The CIA is a proposal only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from Agents.integrity_manager import log_audit_event


# Module-level constant for the agent name — used in audit events and
# Logic Archive cross-references.
AGENT_NAME = "ChangeImpactAgent"


# Risk-delta vocabulary. A change can push a UR's effective risk up,
# down, or leave it unchanged. Used in the CIA summary.
RISK_DELTA_INCREASE = "increase"
RISK_DELTA_DECREASE = "decrease"
RISK_DELTA_UNCHANGED = "unchanged"


# ── Exceptions ───────────────────────────────────────────────────────

class ChangeImpactError(Exception):
    """Base class for ChangeImpactAgent errors.

    :requirement: URS-36.4 - Typed error for CIA generation failures.
    """
    error_code = "CSV-014"


class InvalidProjectSnapshotError(ChangeImpactError):
    """The active project snapshot is missing required fields.

    :requirement: URS-36.5 - Validate project snapshot before
                  attempting CIA generation.
    """
    error_code = "CSV-015"


# ── Result dataclasses ───────────────────────────────────────────────

@dataclass
class AffectedRequirement:
    """One UR or FR identified as affected by the change."""
    requirement_id:  str
    type:            str            # "UR" or "FR"
    statement:       str
    parent_id:       Optional[str]
    reason:          str            # why the agent flagged this
    risk_before:     Optional[str]
    risk_after:      Optional[str]
    risk_delta:      str            # "increase" | "decrease" | "unchanged"


@dataclass
class AffectedBundle:
    """One test bundle whose validity is challenged by the change."""
    bundle_id:           str
    requirement_id:      str
    requirement_summary: str
    reason:              str
    needs_revalidation:  bool


@dataclass
class InvalidatedApproval:
    """One signed approval that the change invalidates."""
    approver_name:  str
    role:           str
    signed_at:      str
    reason:         str


@dataclass
class ChangeImpactAssessment:
    """The full CIA artefact. Serialisable to JSON for API + PDF."""
    cia_id:               str
    cr_id:                str
    cr_text:              str
    project_name:         str
    summary:              str
    affected_urs:         List[AffectedRequirement] = field(default_factory=list)
    affected_frs:         List[AffectedRequirement] = field(default_factory=list)
    affected_bundles:     List[AffectedBundle]      = field(default_factory=list)
    invalidated_approvals:List[InvalidatedApproval] = field(default_factory=list)
    risk_delta_summary:   Dict[str, int]            = field(default_factory=dict)
    recommendation:       str = "revalidate"
    reasoning_chain:      List[str] = field(default_factory=list)
    reg_versions_cited:   List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a JSON-friendly dict for the API response."""
        return {
            "cia_id":         self.cia_id,
            "cr_id":          self.cr_id,
            "cr_text":        self.cr_text,
            "project_name":   self.project_name,
            "summary":        self.summary,
            "affected_urs":   [_asdict(r) for r in self.affected_urs],
            "affected_frs":   [_asdict(r) for r in self.affected_frs],
            "affected_bundles": [
                _asdict(b) for b in self.affected_bundles
            ],
            "invalidated_approvals": [
                _asdict(a) for a in self.invalidated_approvals
            ],
            "risk_delta_summary": self.risk_delta_summary,
            "recommendation":     self.recommendation,
            "reasoning_chain":    self.reasoning_chain,
            "reg_versions_cited": self.reg_versions_cited,
        }


def _asdict(obj: Any) -> Dict[str, Any]:
    """Trivial dataclass-to-dict helper. Avoids the import."""
    return {k: getattr(obj, k) for k in obj.__dataclass_fields__}


# ── Keyword matching helpers ─────────────────────────────────────────
#
# Sprint 36 ships the agent with a deterministic keyword-overlap
# matcher between the CR text and each UR statement. Sprint 40 will
# add a real LLM/embedding match against the corpus — for now,
# determinism keeps the demo predictable and the audit story clean.

# Stop-words excluded from CR / UR keyword overlap. Tuned for the
# pharma vocabulary — high-information words like "signature",
# "audit", "release" stay; filler like "the", "and", "system" go.
_STOPWORDS: Set[str] = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "for",
    "on", "with", "at", "by", "from", "as", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "shall", "should", "may", "might", "must",
    "can", "could", "this", "that", "these", "those", "we", "you",
    "i", "they", "he", "she", "it", "our", "your", "their",
    "system", "systems", "user", "users",
}


def _tokenize(text: str) -> Set[str]:
    """Lower-case word tokens with stop-words and short fragments
    filtered out. Used for keyword-overlap matching between a CR and
    each UR statement."""
    if not text:
        return set()
    words = re.findall(r"\b[a-zA-Z][a-zA-Z\-]+\b", text.lower())
    return {
        w for w in words
        if w not in _STOPWORDS and len(w) > 2
    }


def _overlap_score(cr_tokens: Set[str], ur_tokens: Set[str]) -> float:
    """Jaccard-style overlap between CR token set and UR token set.
    Returns a float in [0, 1]. Higher means more shared vocabulary."""
    if not cr_tokens or not ur_tokens:
        return 0.0
    intersection = cr_tokens & ur_tokens
    union = cr_tokens | ur_tokens
    return len(intersection) / len(union) if union else 0.0


def _overlap_keywords(
    cr_tokens: Set[str], ur_tokens: Set[str],
) -> List[str]:
    """The shared tokens (intersection), sorted alphabetically. Used
    in the CIA's reasoning chain for explainability."""
    return sorted(cr_tokens & ur_tokens)


# Magic numbers — extracted as constants so the impact threshold is
# a single line to tune. Sprint 40 will replace this with an LLM
# similarity threshold over embeddings.
_AFFECTED_THRESHOLD = 0.05  # min Jaccard overlap to flag a UR as affected
_HIGH_OVERLAP_THRESHOLD = 0.15   # noteworthy in reasoning chain


# ── The agent ────────────────────────────────────────────────────────

class ChangeImpactAgent:
    """Agent that drafts a Change Impact Assessment for QA review.

    The agent does NOT:
      - sign the CCR (only humans sign)
      - trigger revalidation (only a signed CCR can do that)
      - modify existing URs or risk classifications
      - write to the audit trail directly (uses log_audit_event)

    Sprint 36 ships with a deterministic matcher; Sprint 40 adds an
    LLM/embedding match against the regulatory corpus.

    :requirement: URS-36.1 - Generate AI-drafted CIA from CR + project.
    """

    def __init__(self) -> None:
        """Construct the agent. No external dependencies in Sprint 36
        (deterministic matcher only). Sprint 40 will inject the
        Pinecone / OpenAI clients via the same constructor."""
        pass

    def assess(
        self,
        cr_id: str,
        cr_text: str,
        project_snapshot: Dict[str, Any],
        user_id: str = "system",
    ) -> ChangeImpactAssessment:
        """Generate the Change Impact Assessment.

        Logs the standard CIA_RECEIVED / CIA_GENERATED / CIA_FAILED
        triplet to the audit trail. Writes a Logic Archive with full
        inputs / steps / outputs for inspector re-derivation.

        :param cr_id: ServiceNow Change Request ID (e.g. "CR-2026-0421").
        :param cr_text: Free-text description of the proposed change.
        :param project_snapshot: Dict with keys:
                                 ``project_name``,
                                 ``requirements`` (list of UR/FR
                                 dicts with ``id``, ``type``,
                                 ``statement``, ``parentId``),
                                 ``risk_data`` (dict keyed by UR id),
                                 ``test_bundles`` (dict keyed by
                                 UR id),
                                 ``approvals`` (list of signed
                                 approval dicts).
        :param user_id: User triggering the assessment.
        :return: ChangeImpactAssessment dataclass.
        :raises InvalidProjectSnapshotError: If snapshot is missing
                required fields.
        :raises ChangeImpactError: If CIA generation fails.
        :requirement: URS-36.1 - Generate AI-drafted CIA.
        """
        log_audit_event(
            agent_name=AGENT_NAME,
            action="CIA_RECEIVED",
            user_id=user_id,
            decision_logic=(
                f"CIA request received for CR {cr_id} against project "
                f"'{project_snapshot.get('project_name', '<unknown>')}'"
            ),
        )

        try:
            self._validate_snapshot(project_snapshot)

            cia = self._build_cia(cr_id, cr_text, project_snapshot)

            # Audit + Logic Archive cross-reference. The
            # thought_process payload gives an inspector everything
            # they need to re-derive the CIA from inputs.
            log_audit_event(
                agent_name=AGENT_NAME,
                action="CIA_GENERATED",
                user_id=user_id,
                decision_logic=(
                    f"CIA {cia.cia_id} generated for CR {cr_id}: "
                    f"{len(cia.affected_urs)} UR(s), "
                    f"{len(cia.affected_frs)} FR(s), "
                    f"{len(cia.affected_bundles)} bundle(s) affected; "
                    f"recommendation={cia.recommendation}"
                ),
                thought_process={
                    "inputs": {
                        "cr_id":        cr_id,
                        "cr_text":      cr_text,
                        "project_name": project_snapshot.get(
                            "project_name",
                        ),
                        "ur_fr_count":  len(
                            project_snapshot.get("requirements", []),
                        ),
                    },
                    "steps":   cia.reasoning_chain,
                    "outputs": {
                        "cia_id":            cia.cia_id,
                        "affected_ur_ids":   [
                            r.requirement_id for r in cia.affected_urs
                        ],
                        "affected_fr_ids":   [
                            r.requirement_id for r in cia.affected_frs
                        ],
                        "affected_bundles":  [
                            b.bundle_id for b in cia.affected_bundles
                        ],
                        "risk_delta_summary": cia.risk_delta_summary,
                        "recommendation":     cia.recommendation,
                    },
                },
            )
            return cia

        except Exception as e:
            log_audit_event(
                agent_name=AGENT_NAME,
                action="CIA_FAILED",
                user_id=user_id,
                decision_logic=(
                    f"CIA generation failed for CR {cr_id}: "
                    f"{type(e).__name__}: {e}"
                ),
            )
            if isinstance(e, ChangeImpactError):
                raise
            raise ChangeImpactError(
                f"CIA generation failed: {e}"
            ) from e

    # ── private helpers ─────────────────────────────────────────────

    def _validate_snapshot(
        self, snapshot: Dict[str, Any],
    ) -> None:
        """Sanity-check the snapshot has the keys we need."""
        if not isinstance(snapshot, dict):
            raise InvalidProjectSnapshotError(
                "Project snapshot must be a dict."
            )
        if not snapshot.get("project_name"):
            raise InvalidProjectSnapshotError(
                "Project snapshot missing 'project_name'."
            )
        if "requirements" not in snapshot:
            raise InvalidProjectSnapshotError(
                "Project snapshot missing 'requirements' list."
            )

    def _build_cia(
        self,
        cr_id: str,
        cr_text: str,
        snapshot: Dict[str, Any],
    ) -> ChangeImpactAssessment:
        """Core CIA construction logic. Deterministic in Sprint 36."""
        requirements = snapshot.get("requirements", []) or []
        risk_data    = snapshot.get("risk_data", {})    or {}
        test_bundles = snapshot.get("test_bundles", {}) or {}
        approvals    = snapshot.get("approvals", [])    or []
        project_name = snapshot.get("project_name", "")

        cr_tokens = _tokenize(cr_text)

        reasoning_chain: List[str] = []
        reasoning_chain.append(
            f"Tokenized CR text into {len(cr_tokens)} content-words "
            f"after stop-word filtering."
        )

        affected_urs: List[AffectedRequirement] = []
        affected_frs: List[AffectedRequirement] = []
        affected_ur_ids: Set[str] = set()

        # Walk URs first — FRs are matched by parent inclusion.
        urs = [r for r in requirements if r.get("type") == "UR"]
        frs = [r for r in requirements if r.get("type") == "FR"]

        for ur in urs:
            ur_id        = ur.get("id", "")
            ur_statement = ur.get("statement", "") or ""
            ur_tokens    = _tokenize(ur_statement)
            score        = _overlap_score(cr_tokens, ur_tokens)

            if score < _AFFECTED_THRESHOLD:
                continue

            shared = _overlap_keywords(cr_tokens, ur_tokens)
            shared_summary = ", ".join(shared[:6]) or "(no shared keywords)"

            risk_before = self._risk_label(risk_data.get(ur_id))
            # Sprint 36 ships with a conservative no-delta default —
            # the AI flags potential affect, the human decides risk
            # implication during CCR review. Sprint 40 will add
            # explicit risk-delta inference.
            risk_after  = risk_before
            risk_delta  = RISK_DELTA_UNCHANGED

            affected_urs.append(AffectedRequirement(
                requirement_id=ur_id,
                type="UR",
                statement=ur_statement,
                parent_id=None,
                reason=(
                    f"Vocabulary overlap with CR text "
                    f"(score {score:.2f}); shared keywords: "
                    f"{shared_summary}."
                ),
                risk_before=risk_before,
                risk_after=risk_after,
                risk_delta=risk_delta,
            ))
            affected_ur_ids.add(ur_id)

            if score >= _HIGH_OVERLAP_THRESHOLD:
                reasoning_chain.append(
                    f"{ur_id} flagged as HIGHLY affected "
                    f"(overlap {score:.2f}, keywords: {shared_summary})."
                )
            else:
                reasoning_chain.append(
                    f"{ur_id} flagged as affected "
                    f"(overlap {score:.2f})."
                )

        # FRs inherit from parent UR affecting status.
        for fr in frs:
            fr_id     = fr.get("id", "")
            parent_id = fr.get("parentId")
            if parent_id and parent_id in affected_ur_ids:
                affected_frs.append(AffectedRequirement(
                    requirement_id=fr_id,
                    type="FR",
                    statement=fr.get("statement", "") or "",
                    parent_id=parent_id,
                    reason=(
                        f"Inherits from parent {parent_id} which "
                        f"was flagged as affected."
                    ),
                    risk_before=None,
                    risk_after=None,
                    risk_delta=RISK_DELTA_UNCHANGED,
                ))

        # Bundles: any UR with an affected status and a test bundle
        # needs revalidation. The CIA names them; the CCR sign-off
        # authorises the rerun.
        affected_bundles: List[AffectedBundle] = []
        for ur_id in sorted(affected_ur_ids):
            bundle = test_bundles.get(ur_id)
            if not bundle:
                continue
            affected_bundles.append(AffectedBundle(
                bundle_id=bundle.get("bundle_id", f"TB-{ur_id}"),
                requirement_id=ur_id,
                requirement_summary=(
                    bundle.get("requirement_summary", "")
                ),
                reason=(
                    f"Parent UR {ur_id} flagged as affected; "
                    f"bundle requires revalidation against the "
                    f"changed requirement state."
                ),
                needs_revalidation=True,
            ))

        # Approvals are invalidated if ANY affected UR has been
        # released. Conservative — pharma prefers re-attest over
        # silent acceptance of prior signatures.
        invalidated_approvals: List[InvalidatedApproval] = []
        if affected_ur_ids:
            for appr in approvals:
                invalidated_approvals.append(InvalidatedApproval(
                    approver_name=appr.get("name")
                                  or appr.get("signerName", ""),
                    role=appr.get("role", ""),
                    signed_at=appr.get("signedAt")
                              or appr.get("signed_at", ""),
                    reason=(
                        f"{len(affected_ur_ids)} UR(s) affected by "
                        f"this change; prior approval must be "
                        f"re-attested per change-control SOP."
                    ),
                ))

        # Aggregate risk-delta counts for the summary line.
        delta_summary = {
            RISK_DELTA_INCREASE:  0,
            RISK_DELTA_DECREASE:  0,
            RISK_DELTA_UNCHANGED: len(affected_urs),
        }

        # Recommendation logic. If no URs flagged, no revalidation
        # needed. If any flagged, revalidation is the default; the
        # CCR-signing human can override during sign-off.
        if not affected_urs:
            recommendation = "no_revalidation_needed"
            reasoning_chain.append(
                "No URs flagged as affected by this CR; "
                "recommendation: no revalidation needed."
            )
        else:
            recommendation = "revalidate"
            reasoning_chain.append(
                f"Recommendation: revalidate "
                f"{len(affected_bundles)} bundle(s) covering "
                f"{len(affected_urs)} UR(s); QA to sign CCR before "
                f"any revalidation runs."
            )

        # Summary line — what a human reads first.
        if affected_urs:
            summary = (
                f"This change is assessed as affecting "
                f"{len(affected_urs)} UR(s) "
                f"({len(affected_frs)} downstream FR(s)) and "
                f"{len(affected_bundles)} test bundle(s). "
                f"{len(invalidated_approvals)} prior approval(s) "
                f"require re-attestation. Recommended action: "
                f"revalidate the affected slice after CCR sign-off."
            )
        else:
            summary = (
                "This change does not appear to affect any "
                "validated requirement based on vocabulary "
                "overlap. Recommended action: QA review to confirm "
                "no further action needed."
            )

        cia_id = f"CIA-{cr_id}"

        return ChangeImpactAssessment(
            cia_id=cia_id,
            cr_id=cr_id,
            cr_text=cr_text,
            project_name=project_name,
            summary=summary,
            affected_urs=affected_urs,
            affected_frs=affected_frs,
            affected_bundles=affected_bundles,
            invalidated_approvals=invalidated_approvals,
            risk_delta_summary=delta_summary,
            recommendation=recommendation,
            reasoning_chain=reasoning_chain,
            reg_versions_cited=[],   # Sprint 40 — LLM-backed citations
        )

    @staticmethod
    def _risk_label(risk_row: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract a friendly risk label from a riskData row."""
        if not risk_row:
            return None
        level = (risk_row.get("riskLevel") or "").strip()
        if not level:
            return None
        # Normalise — riskData stores HIGH/MEDIUM/LOW; display
        # surfaces want Title Case.
        return level.capitalize()


def sign_ccr(
    cia_id: str,
    cr_id: str,
    signer_name: str,
    role: str,
    meaning: str,
    decision: str,
    user_id: str = "system",
) -> Dict[str, Any]:
    """Record a signed Change Control Record for a generated CIA.

    The CCR is the human-signed gate that authorises (or rejects)
    revalidation. The agent's CIA is a *proposal*; the CCR is the
    *decision*. Bounded autonomy in action.

    Logs the CCR_RECEIVED / CCR_APPROVED / CCR_FAILED audit triplet
    per the EVOLV API rules. Writes a Logic Archive with the full
    signature record for inspector re-derivation.

    :param cia_id: The CIA being signed against.
    :param cr_id:  The parent CR id.
    :param signer_name: Full name of the QA signer.
    :param role:        Signer's role (e.g. "QA Director").
    :param meaning:     21 CFR Part 11 §11.50 signature meaning.
    :param decision:    One of:
                        ``approve_revalidation``,
                        ``approve_no_revalidation``,
                        ``reject``.
    :param user_id:     User triggering the signature.
    :return: Signed CCR dict suitable for the API response and store
             persistence.
    :raises ChangeImpactError: If decision is invalid.
    :requirement: URS-36.6 - Record signed Change Control Record.
    """
    log_audit_event(
        agent_name=AGENT_NAME,
        action="CCR_RECEIVED",
        user_id=user_id,
        decision_logic=(
            f"CCR sign-off request received for CIA {cia_id} "
            f"(CR {cr_id}) by '{signer_name}' / {role}; "
            f"decision={decision}"
        ),
    )

    try:
        valid_decisions = {
            "approve_revalidation",
            "approve_no_revalidation",
            "reject",
        }
        if decision not in valid_decisions:
            raise ChangeImpactError(
                f"Invalid CCR decision '{decision}'. "
                f"Must be one of: {sorted(valid_decisions)}."
            )
        if not signer_name or not signer_name.strip():
            raise ChangeImpactError(
                "CCR signature requires a signer_name."
            )

        from datetime import datetime, timezone
        signed_at = datetime.now(timezone.utc).isoformat()
        ccr_id = f"CCR-{cr_id}"

        ccr_record = {
            "ccr_id":      ccr_id,
            "cia_id":      cia_id,
            "cr_id":       cr_id,
            "signer_name": signer_name.strip(),
            "role":        role,
            "meaning":     meaning,
            "decision":    decision,
            "signed_at":   signed_at,
        }

        log_audit_event(
            agent_name=AGENT_NAME,
            action="CCR_APPROVED",
            user_id=user_id,
            decision_logic=(
                f"CCR {ccr_id} signed by '{signer_name}' ({role}); "
                f"decision={decision}; meaning='{meaning}'"
            ),
            thought_process={
                "inputs":  {
                    "cia_id":      cia_id,
                    "cr_id":       cr_id,
                    "signer_name": signer_name,
                    "role":        role,
                    "decision":    decision,
                },
                "steps":   [
                    "Validated decision is in approved vocabulary.",
                    "Validated signer_name is non-empty.",
                    "Generated signed_at ISO-8601 timestamp.",
                    "Composed CCR record dict for persistence.",
                ],
                "outputs": ccr_record,
            },
        )
        return ccr_record

    except Exception as e:
        log_audit_event(
            agent_name=AGENT_NAME,
            action="CCR_FAILED",
            user_id=user_id,
            decision_logic=(
                f"CCR sign-off failed for CIA {cia_id}: "
                f"{type(e).__name__}: {e}"
            ),
        )
        if isinstance(e, ChangeImpactError):
            raise
        raise ChangeImpactError(
            f"CCR sign-off failed: {e}"
        ) from e
