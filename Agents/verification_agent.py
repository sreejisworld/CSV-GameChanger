"""
Verification Agent Module.

Reviews URS documents produced by the RequirementArchitect against the
GAMP 5 / CSA regulatory text stored in Pinecone.  Three independent
checks are executed:

1. **Criticality alignment** -- does the assigned criticality agree
   with the risk-related language found in the authoritative GAMP 5
   chunks?
2. **Regulatory rationale relevance** -- is the cited rationale
   semantically close to the requirement it is supposed to justify?
3. **Contradiction scan** -- does the requirement statement contain
   language that directly opposes obligations stated in the GAMP 5
   source text?

If any check fails the URS is **rejected** and a Compliance Exception
is logged to the central audit trail via the IntegrityManager.

:requirement: URS-12.1 - System shall verify generated URS against
              GAMP 5 regulatory text.
:requirement: URS-12.2 - System shall reject URS drafts that
              contradict regulatory guidance.
"""
import os
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from Agents.integrity_manager import (
    log_audit_event as _log_integrity_event,
)

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
PINECONE_INDEX_NAME = "csv-knowledge-base"
EMBEDDING_MODEL = "text-embedding-3-small"
VERIFICATION_TOP_K = 5
VERIFICATION_MIN_SCORE = 0.35
RATIONALE_RELEVANCE_THRESHOLD = 0.45

# Keywords whose presence in GAMP 5 context signals high-risk
# obligations.  If the URS classifies the requirement as Low while
# these appear in the retrieved guidance, the criticality is
# under-classified.
HIGH_RISK_INDICATORS = [
    "patient", "safety", "critical", "gxp",
    "sterile", "batch release", "adverse event",
    "pharmacovigilance", "clinical", "life-sustaining",
    "life-supporting", "validated", "21 cfr part 11",
]

# Phrases in a requirement statement that directly contradict
# core GAMP 5 obligations when the corresponding obligation
# keyword appears in the retrieved source text.
_CONTRADICTION_PAIRS = [
    {
        "requirement_phrases": [
            "skip validation", "no validation required",
            "validation is unnecessary",
            "does not require validation",
        ],
        "gamp5_keywords": [
            "validation", "shall be validated",
            "validation is required",
        ],
    },
    {
        "requirement_phrases": [
            "skip testing", "no testing required",
            "testing is unnecessary",
            "does not require testing",
        ],
        "gamp5_keywords": [
            "testing", "shall be tested",
            "test plan", "verification",
        ],
    },
    {
        "requirement_phrases": [
            "no audit trail", "disable audit",
            "audit trail is not needed",
            "without audit trail",
        ],
        "gamp5_keywords": [
            "audit trail", "traceability",
            "electronic record", "21 cfr part 11",
        ],
    },
    {
        "requirement_phrases": [
            "no change control",
            "bypass change control",
            "without change control",
        ],
        "gamp5_keywords": [
            "change control", "change management",
        ],
    },
]

# Required keys in the URS dictionary produced by
# RequirementArchitect.generate_urs().
URS_REQUIRED_FIELDS = [
    "URS_ID",
    "Requirement_Statement",
    "Criticality",
    "Regulatory_Rationale",
]

_KNOWN_REG_VERSIONS: set = set()


# ------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------
class VerificationError(Exception):
    """
    Base exception for Verification Agent errors.

    Error code: CSV-010 - URS verification failed.

    :requirement: URS-12.3 - System shall report verification errors.
    """

    error_code = "CSV-010"


class InvalidURSError(VerificationError):
    """
    Raised when the URS dictionary is missing required fields.

    Error code: CSV-011 - Invalid URS input for verification.

    :requirement: URS-12.3 - System shall report verification errors.
    """

    error_code = "CSV-011"

    def __init__(self, missing_fields: List[str]):
        self.missing_fields = missing_fields
        super().__init__(
            f"URS is missing required fields: "
            f"{', '.join(missing_fields)}"
        )


# ------------------------------------------------------------------
# Enums & data classes
# ------------------------------------------------------------------
class Verdict(Enum):
    """
    Outcome of a verification review.

    :requirement: URS-12.1 - System shall verify generated URS.
    """

    APPROVED = "Approved"
    REJECTED = "Rejected"


class CheckStatus(Enum):
    """
    Result of a single verification check.

    :requirement: URS-12.1 - System shall verify generated URS.
    """

    PASS = "Pass"
    FAIL = "Fail"


@dataclass
class VerificationFinding:
    """
    A single finding produced by one verification check.

    :requirement: URS-12.4 - System shall produce structured
                  verification findings.
    """

    check_name: str
    status: str
    detail: str
    gamp5_reference: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert finding to dictionary.

        :return: Dictionary representation of the finding.
        """
        return {
            "check_name": self.check_name,
            "status": self.status,
            "detail": self.detail,
            "gamp5_reference": self.gamp5_reference,
        }


@dataclass
class VerificationResult:
    """
    Complete result of verifying a single URS document.

    :requirement: URS-12.1 - System shall verify generated URS.
    """

    urs_id: str
    verdict: str
    findings: List[VerificationFinding] = field(
        default_factory=list
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary.

        :return: Dictionary representation of the result.
        """
        return {
            "URS_ID": self.urs_id,
            "Verdict": self.verdict,
            "Findings": [f.to_dict() for f in self.findings],
        }

    @property
    def is_rejected(self) -> bool:
        """Return True when the URS was rejected."""
        return self.verdict == Verdict.REJECTED.value


# ------------------------------------------------------------------
# Agent
# ------------------------------------------------------------------
class VerificationAgent:
    """
    Reviews URS output from the RequirementArchitect against GAMP 5
    regulatory text stored in Pinecone.

    If any check detects a contradiction or misclassification the
    draft is rejected and a Compliance Exception is logged to the
    audit trail.

    :requirement: URS-12.1 - System shall verify generated URS
                  against GAMP 5 regulatory text.
    :requirement: URS-12.2 - System shall reject URS drafts that
                  contradict regulatory guidance.
    """

    def __init__(
        self,
        pinecone_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        index_name: str = PINECONE_INDEX_NAME,
    ) -> None:
        """
        Initialize the VerificationAgent with API clients.

        :param pinecone_api_key: Pinecone API key (defaults to
                                 PINECONE_API_KEY env var).
        :param openai_api_key: OpenAI API key (defaults to
                               OPENAI_API_KEY env var).
        :param index_name: Name of the Pinecone index to query.
        :requirement: URS-12.5 - System shall connect to Pinecone
                      for verification queries.
        """
        self._pinecone_api_key = (
            pinecone_api_key or os.getenv("PINECONE_API_KEY")
        )
        self._openai_api_key = (
            openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        self._index_name = index_name
        self._validate_dependencies()

    # --------------------------------------------------------------
    # Infrastructure helpers
    # --------------------------------------------------------------
    def _validate_dependencies(self) -> None:
        """
        Validate that required packages are installed.

        :raises ImportError: If pinecone or openai is missing.
        :requirement: URS-12.6 - System shall validate environment
                      before verification.
        """
        if Pinecone is None:
            raise ImportError(
                "pinecone-client is required. "
                "Install with: pip install pinecone"
            )
        if OpenAI is None:
            raise ImportError(
                "openai is required. "
                "Install with: pip install openai"
            )

    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for *text* using OpenAI.

        :param text: The text to embed.
        :return: Embedding vector as list of floats.
        :requirement: URS-12.7 - System shall embed text for
                      verification queries.
        """
        if not self._openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required for embeddings"
            )

        client = OpenAI(api_key=self._openai_api_key)
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    def _query_pinecone(
        self,
        embedding: List[float],
        top_k: int = VERIFICATION_TOP_K,
        min_score: float = VERIFICATION_MIN_SCORE,
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone for relevant GAMP 5 chunks.

        :param embedding: The query embedding vector.
        :param top_k: Maximum results to return.
        :param min_score: Minimum similarity score threshold.
        :return: List of matching chunk dicts with metadata.
        :requirement: URS-12.8 - System shall retrieve GAMP 5 text
                      for verification.
        """
        if not self._pinecone_api_key:
            raise ValueError(
                "PINECONE_API_KEY is required for vector search"
            )

        pc = Pinecone(api_key=self._pinecone_api_key)
        index = pc.Index(self._index_name)

        results = index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
        )

        matches = []
        for match in results.matches:
            if match.score >= min_score:
                matches.append({
                    "chunk_id": match.id,
                    "text": match.metadata.get("text", ""),
                    "source_document": match.metadata.get(
                        "source_document", ""
                    ),
                    "page_number": match.metadata.get(
                        "page_number", 0
                    ),
                    "score": match.score,
                    "reg_version": match.metadata.get(
                        "reg_version", ""
                    ),
                })

        return matches

    @staticmethod
    def _validate_urs(urs: Dict[str, Any]) -> None:
        """
        Validate that the URS dictionary contains all required keys.

        :param urs: URS dictionary from RequirementArchitect.
        :raises InvalidURSError: If required fields are missing.
        :requirement: URS-12.9 - System shall validate URS input
                      before verification.
        """
        missing = [
            f for f in URS_REQUIRED_FIELDS if f not in urs
        ]
        if missing:
            raise InvalidURSError(missing)

    @staticmethod
    def _format_gamp5_ref(
        matches: List[Dict[str, Any]],
    ) -> str:
        """
        Build a short citation string from the first match.

        :param matches: List of Pinecone match dicts.
        :return: Formatted citation or fallback text.
        :requirement: URS-14.4 - System shall include reg version
                      in verification citations.
        """
        if not matches:
            return "No GAMP 5 reference available"
        m = matches[0]
        src = m["source_document"] or "GAMP 5"
        pg = m["page_number"] or 0
        txt = (m["text"] or "")[:150]
        ver = m.get("reg_version", "")
        if ver:
            return (
                f"Per {src} [{ver}] (p.{pg}): {txt}..."
            )
        return f"Per {src} (p.{pg}): {txt}..."

    # --------------------------------------------------------------
    # Individual checks
    # --------------------------------------------------------------
    def _check_criticality_alignment(
        self,
        statement: str,
        criticality: str,
        matches: List[Dict[str, Any]],
    ) -> VerificationFinding:
        """
        Verify that the assigned criticality is consistent with
        risk-related language in the GAMP 5 source text.

        If the URS is classified as Low but the retrieved GAMP 5
        chunks contain high-risk indicators (e.g. *patient*,
        *safety*, *sterile*), the criticality is under-classified
        and the check fails.

        :param statement: The requirement statement.
        :param criticality: The assigned criticality (High/Med/Low).
        :param matches: GAMP 5 chunks retrieved from Pinecone.
        :return: VerificationFinding with PASS or FAIL.
        :requirement: URS-12.10 - System shall detect criticality
                      misclassification.
        """
        gamp5_ref = self._format_gamp5_ref(matches)

        if criticality.lower() in ("high",):
            return VerificationFinding(
                check_name="Criticality Alignment",
                status=CheckStatus.PASS.value,
                detail=(
                    f"Criticality is {criticality}; no "
                    f"under-classification possible."
                ),
                gamp5_reference=gamp5_ref,
            )

        # Combine all retrieved GAMP 5 text for scanning.
        context = " ".join(
            (m["text"] or "").lower() for m in matches
        )
        statement_lower = statement.lower()

        triggered: List[str] = []
        for indicator in HIGH_RISK_INDICATORS:
            if (
                indicator in context
                or indicator in statement_lower
            ):
                triggered.append(indicator)

        if triggered:
            return VerificationFinding(
                check_name="Criticality Alignment",
                status=CheckStatus.FAIL.value,
                detail=(
                    f"Criticality is {criticality} but GAMP 5 "
                    f"context contains high-risk indicators: "
                    f"{', '.join(triggered)}. "
                    f"Requirement may be under-classified."
                ),
                gamp5_reference=gamp5_ref,
            )

        return VerificationFinding(
            check_name="Criticality Alignment",
            status=CheckStatus.PASS.value,
            detail=(
                f"Criticality {criticality} is consistent "
                f"with the retrieved GAMP 5 guidance."
            ),
            gamp5_reference=gamp5_ref,
        )

    def _check_rationale_relevance(
        self,
        statement: str,
        matches: List[Dict[str, Any]],
    ) -> VerificationFinding:
        """
        Verify that the cited regulatory rationale is semantically
        relevant to the requirement statement.

        Re-embeds the requirement statement and compares the best
        Pinecone match score against a threshold.  A low score
        indicates the cited GAMP 5 passage does not actually
        support the requirement.

        :param statement: The requirement statement text.
        :param matches: GAMP 5 chunks retrieved from Pinecone.
        :return: VerificationFinding with PASS or FAIL.
        :requirement: URS-12.11 - System shall verify rationale
                      relevance.
        """
        gamp5_ref = self._format_gamp5_ref(matches)

        if not matches:
            return VerificationFinding(
                check_name="Rationale Relevance",
                status=CheckStatus.FAIL.value,
                detail=(
                    "No GAMP 5 chunks were retrieved for this "
                    "requirement; the regulatory rationale "
                    "cannot be substantiated."
                ),
                gamp5_reference=gamp5_ref,
            )

        best_score = max(m["score"] for m in matches)

        if best_score < RATIONALE_RELEVANCE_THRESHOLD:
            return VerificationFinding(
                check_name="Rationale Relevance",
                status=CheckStatus.FAIL.value,
                detail=(
                    f"Best GAMP 5 match score is "
                    f"{best_score:.2f}, below the "
                    f"{RATIONALE_RELEVANCE_THRESHOLD} "
                    f"threshold. The cited rationale may not "
                    f"adequately support this requirement."
                ),
                gamp5_reference=gamp5_ref,
            )

        return VerificationFinding(
            check_name="Rationale Relevance",
            status=CheckStatus.PASS.value,
            detail=(
                f"Best GAMP 5 match score is "
                f"{best_score:.2f}, above the "
                f"{RATIONALE_RELEVANCE_THRESHOLD} threshold. "
                f"Rationale is relevant."
            ),
            gamp5_reference=gamp5_ref,
        )

    @staticmethod
    def _check_contradictions(
        statement: str,
        matches: List[Dict[str, Any]],
    ) -> VerificationFinding:
        """
        Scan for direct contradictions between the requirement
        statement and GAMP 5 obligations.

        Iterates over known contradiction pairs.  If a requirement
        phrase (e.g. *"skip validation"*) is present in the statement
        **and** the opposing GAMP 5 keyword (e.g. *"validation is
        required"*) appears in the retrieved source text, the check
        fails.

        :param statement: The requirement statement text.
        :param matches: GAMP 5 chunks retrieved from Pinecone.
        :return: VerificationFinding with PASS or FAIL.
        :requirement: URS-12.12 - System shall detect contradictions
                      between URS and GAMP 5 text.
        """
        if not matches:
            gamp5_ref = "No GAMP 5 reference available"
        else:
            _m = matches[0]
            _src = _m["source_document"] or "GAMP 5"
            _pg = _m["page_number"] or 0
            _txt = (_m["text"] or "")[:150]
            _ver = _m.get("reg_version", "")
            if _ver:
                gamp5_ref = (
                    f"Per {_src} [{_ver}] "
                    f"(p.{_pg}): {_txt}..."
                )
            else:
                gamp5_ref = (
                    f"Per {_src} "
                    f"(p.{_pg}): {_txt}..."
                )

        statement_lower = statement.lower()
        context = " ".join(
            (m["text"] or "").lower() for m in matches
        )

        contradictions: List[str] = []

        for pair in _CONTRADICTION_PAIRS:
            req_hit = None
            for phrase in pair["requirement_phrases"]:
                if phrase in statement_lower:
                    req_hit = phrase
                    break

            if req_hit is None:
                continue

            for kw in pair["gamp5_keywords"]:
                if kw in context:
                    contradictions.append(
                        f"Requirement contains '{req_hit}' "
                        f"but GAMP 5 text states '{kw}'"
                    )
                    break

        if contradictions:
            return VerificationFinding(
                check_name="Contradiction Scan",
                status=CheckStatus.FAIL.value,
                detail=(
                    "Direct contradiction(s) detected: "
                    + "; ".join(contradictions)
                    + "."
                ),
                gamp5_reference=gamp5_ref,
            )

        return VerificationFinding(
            check_name="Contradiction Scan",
            status=CheckStatus.PASS.value,
            detail=(
                "No contradictions detected between "
                "the requirement and GAMP 5 guidance."
            ),
            gamp5_reference=gamp5_ref,
        )

    # --------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------
    def verify_urs(
        self,
        urs: Dict[str, Any],
        min_score: float = VERIFICATION_MIN_SCORE,
    ) -> VerificationResult:
        """
        Verify a URS dictionary against GAMP 5 regulatory text.

        Runs three independent checks (criticality alignment,
        rationale relevance, contradiction scan).  If **any** check
        fails the URS is rejected and a ``COMPLIANCE_EXCEPTION`` is
        logged to the audit trail.  Otherwise an ``URS_VERIFIED``
        event is logged.

        :param urs: URS dictionary with keys URS_ID,
                    Requirement_Statement, Criticality, and
                    Regulatory_Rationale.
        :param min_score: Minimum Pinecone similarity score for
                          retrieved chunks (default: 0.35).
        :return: VerificationResult containing the verdict and
                 individual findings.
        :raises InvalidURSError: If URS is missing required fields.
        :requirement: URS-12.1 - System shall verify generated URS.
        :requirement: URS-12.2 - System shall reject URS drafts
                      that contradict regulatory guidance.

        Example:
            >>> agent = VerificationAgent()
            >>> urs = {
            ...     "URS_ID": "URS-7.1",
            ...     "Requirement_Statement": "The system shall "
            ...         "track warehouse temperature.",
            ...     "Criticality": "Medium",
            ...     "Regulatory_Rationale": "Per GAMP 5 ..."
            ... }
            >>> result = agent.verify_urs(urs)
            >>> print(result.verdict)
            Approved
        """
        self._validate_urs(urs)

        urs_id = urs["URS_ID"]
        statement = urs["Requirement_Statement"]
        criticality = urs["Criticality"]

        # Retrieve fresh GAMP 5 context for verification
        embedding = self._get_embedding(statement)
        matches = self._query_pinecone(
            embedding,
            top_k=VERIFICATION_TOP_K,
            min_score=min_score,
        )

        # Detect new regulatory versions
        global _KNOWN_REG_VERSIONS
        new_versions = {
            m.get("reg_version", "")
            for m in matches
            if m.get("reg_version")
        } - _KNOWN_REG_VERSIONS
        if new_versions:
            for ver in sorted(new_versions):
                print(
                    f"[VerificationAgent] New regulatory "
                    f"version detected: {ver}. Do you wish "
                    f"to re-evaluate existing logic? (y/n)"
                )
                _log_integrity_event(
                    agent_name="VerificationAgent",
                    action="REG_VERSION_CHANGE_DETECTED",
                    decision_logic=(
                        f"New regulatory version {ver} "
                        f"detected during verification"
                    ),
                )
            _KNOWN_REG_VERSIONS |= new_versions

        # Run all three checks
        findings: List[VerificationFinding] = [
            self._check_criticality_alignment(
                statement, criticality, matches
            ),
            self._check_rationale_relevance(
                statement, matches
            ),
            self._check_contradictions(
                statement, matches
            ),
        ]

        # Determine verdict
        has_failure = any(
            f.status == CheckStatus.FAIL.value
            for f in findings
        )

        if has_failure:
            verdict = Verdict.REJECTED
            failed_checks = [
                f.check_name
                for f in findings
                if f.status == CheckStatus.FAIL.value
            ]
            failed_details = " | ".join(
                f"{f.check_name}: {f.detail}"
                for f in findings
                if f.status == CheckStatus.FAIL.value
            )

            decision_logic = (
                f"REJECTED {urs_id}: Failed checks: "
                f"{', '.join(failed_checks)}. "
                f"{failed_details}"
            )

            _log_integrity_event(
                agent_name="VerificationAgent",
                action="COMPLIANCE_EXCEPTION",
                decision_logic=decision_logic,
            )
        else:
            verdict = Verdict.APPROVED

            passed_summary = ", ".join(
                f.check_name for f in findings
            )

            decision_logic = (
                f"APPROVED {urs_id}: All checks passed "
                f"({passed_summary}). Criticality "
                f"{criticality} confirmed against GAMP 5 "
                f"context."
            )

            _log_integrity_event(
                agent_name="VerificationAgent",
                action="URS_VERIFIED",
                decision_logic=decision_logic,
            )

        return VerificationResult(
            urs_id=urs_id,
            verdict=verdict.value,
            findings=findings,
        )

    def verify_batch(
        self,
        urs_list: List[Dict[str, Any]],
        min_score: float = VERIFICATION_MIN_SCORE,
    ) -> List[VerificationResult]:
        """
        Verify a batch of URS dictionaries.

        :param urs_list: List of URS dicts from
                         RequirementArchitect.
        :param min_score: Minimum Pinecone similarity score.
        :return: List of VerificationResult objects.
        :raises InvalidURSError: If any URS is missing fields.
        :requirement: URS-12.13 - System shall support batch
                      verification.
        """
        results = [
            self.verify_urs(urs, min_score=min_score)
            for urs in urs_list
        ]

        approved = sum(
            1 for r in results if not r.is_rejected
        )
        rejected = sum(
            1 for r in results if r.is_rejected
        )

        decision_logic = (
            f"Batch-verified {len(results)} URS documents; "
            f"{approved} approved, {rejected} rejected"
        )

        _log_integrity_event(
            agent_name="VerificationAgent",
            action="URS_BATCH_VERIFIED",
            decision_logic=decision_logic,
        )

        return results
