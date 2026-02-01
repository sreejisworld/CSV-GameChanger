"""
Test Generator Agent Module.

Generates CSA-aligned Test Scripts from structured URS requirements
produced by the RequirementArchitect. Queries the Pinecone knowledge
base for FDA CSA Guidance to justify the selected testing level.

High-criticality requirements receive detailed Scripted Tests with
step-by-step procedures. Low-criticality requirements receive
Unscripted Tests with objective-based exploratory guidance.

:requirement: URS-8.1 - System shall generate test scripts from URS
              documents.
"""
import os
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
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


# Configuration
PINECONE_INDEX_NAME = "csv-knowledge-base"
EMBEDDING_MODEL = "text-embedding-3-small"
CSA_QUERY_TOP_K = 3
CSA_MIN_SIMILARITY_SCORE = 0.4

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_CACHE_DIR = PROJECT_ROOT / "output" / "test_cache"

logger = logging.getLogger("test_generator")


class TestGeneratorError(Exception):
    """
    Base exception for Test Generator errors.

    Error code: CSV-005 - Test generation failed.
    """

    error_code = "CSV-005"


class InvalidURSInputError(TestGeneratorError):
    """
    Raised when the input URS JSON is missing required fields.

    Error code: CSV-006 - Invalid URS input.

    :requirement: URS-8.2 - System shall validate URS input before
                  generation.
    """

    error_code = "CSV-006"

    def __init__(self, missing_fields: List[str]):
        self.missing_fields = missing_fields
        super().__init__(
            f"URS input is missing required fields: "
            f"{', '.join(missing_fields)}"
        )


class CSAGuidanceNotFoundError(TestGeneratorError):
    """
    Raised when no FDA CSA guidance is found in Pinecone to
    justify the testing level.

    Error code: CSV-007 - No CSA guidance context found.

    :requirement: URS-8.7 - System shall cite FDA CSA Guidance to
                  justify the testing level.
    """

    error_code = "CSV-007"

    def __init__(self, criticality: str):
        self.criticality = criticality
        super().__init__(
            f"No FDA CSA guidance found in Pinecone to justify "
            f"'{criticality}' testing level. Ensure CSA guidance "
            f"documents are ingested into the "
            f"'{PINECONE_INDEX_NAME}' index."
        )


class ValidationType(Enum):
    """
    CSA-aligned validation type for test steps.

    Scripted testing provides full traceability for high-risk
    requirements. Unscripted testing leverages tester expertise
    for low-risk requirements.

    :requirement: URS-8.3 - System shall assign validation type
                  per CSA.
    """

    SCRIPTED = "Scripted"
    UNSCRIPTED = "Unscripted"


URS_REQUIRED_FIELDS = [
    "URS_ID",
    "Requirement_Statement",
    "Criticality",
    "Regulatory_Rationale",
]


@dataclass
class TestStep:
    """
    A single step within a test script.

    :requirement: URS-8.4 - Each test step shall include ID,
                  description, expected result, and validation type.
    """

    test_id: str
    step_description: str
    expected_result: str
    validation_type: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert test step to dictionary.

        :return: Dictionary representation of the test step.
        """
        return {
            "Test_ID": self.test_id,
            "Step_Description": self.step_description,
            "Expected_Result": self.expected_result,
            "Validation_Type": self.validation_type,
        }


@dataclass
class TestScript:
    """
    Complete test script generated from a URS requirement.

    :requirement: URS-8.1 - System shall generate test scripts
                  from URS.
    """

    urs_id: str
    requirement_statement: str
    criticality: str
    csa_justification: str = ""
    generated_at: str = ""
    steps: List[TestStep] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Set generated_at timestamp if not provided."""
        if not self.generated_at:
            self.generated_at = (
                datetime.now(timezone.utc).isoformat()
            )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert test script to dictionary.

        :return: Dictionary representation of the test script.
        :requirement: URS-8.5 - System shall provide JSON output.
        """
        return {
            "URS_ID": self.urs_id,
            "Requirement_Statement": self.requirement_statement,
            "Criticality": self.criticality,
            "CSA_Justification": self.csa_justification,
            "Generated_At": self.generated_at,
            "Test_Steps": [s.to_dict() for s in self.steps],
        }

    def to_json(self) -> str:
        """
        Convert test script to JSON string.

        :return: JSON string representation of the test script.
        :requirement: URS-8.5 - System shall provide JSON output.
        """
        return json.dumps(self.to_dict(), indent=2)


class TestGenerator:
    """
    Generates CSA-aligned test scripts from URS requirements.

    Takes structured URS output from the RequirementArchitect and
    produces test scripts whose structure depends on criticality:

    - **High**: Detailed Scripted Test with step-by-step procedures,
      preconditions, discrete actions, and exact expected results.
    - **Medium**: Scripted Test with focused verification steps.
    - **Low**: Unscripted Test with objective-based exploratory
      guidance leveraging tester expertise.

    Queries the Pinecone knowledge base for FDA CSA Guidance to
    cite the regulatory justification for the chosen testing level.

    :requirement: URS-8.1 - System shall generate test scripts
                  from URS.
    """

    def __init__(
        self,
        pinecone_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        index_name: str = PINECONE_INDEX_NAME,
        cache_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize the TestGenerator with optional API clients.

        :param pinecone_api_key: Pinecone API key (defaults to
                                 PINECONE_API_KEY env var).
        :param openai_api_key: OpenAI API key (defaults to
                               OPENAI_API_KEY env var).
        :param index_name: Name of the Pinecone index to query.
        :param cache_dir: Directory for cached test scripts.
                          Defaults to output/test_cache/.
        :requirement: URS-8.1 - System shall generate test scripts.
        """
        self._pinecone_api_key = (
            pinecone_api_key or os.getenv("PINECONE_API_KEY")
        )
        self._openai_api_key = (
            openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        self._index_name = index_name
        self._test_counter: int = 0
        self._cache_dir = cache_dir or DEFAULT_CACHE_DIR

        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """
        Validate that required dependencies are available.

        :raises ImportError: If pinecone or openai packages are
                             not installed.
        :requirement: URS-8.8 - System shall validate environment
                      before processing.
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
        Generate embedding vector for input text using OpenAI.

        :param text: The text to embed.
        :return: Embedding vector as list of floats.
        :requirement: URS-8.9 - System shall embed queries for
                      CSA guidance retrieval.
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
        top_k: int = CSA_QUERY_TOP_K,
        min_score: float = CSA_MIN_SIMILARITY_SCORE,
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone index for relevant FDA CSA guidance.

        :param embedding: The query embedding vector.
        :param top_k: Number of results to return.
        :param min_score: Minimum similarity score threshold.
        :return: List of matching documents with metadata.
        :requirement: URS-8.10 - System shall retrieve FDA CSA
                      guidance from Pinecone.
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
                })

        return matches

    def _fetch_csa_justification(
        self, criticality: str, statement: str
    ) -> str:
        """
        Query Pinecone for FDA CSA Guidance that justifies the
        testing level for the given criticality.

        Builds a targeted query combining the criticality level,
        the requirement statement, and CSA testing terminology to
        retrieve the most relevant guidance passages.

        :param criticality: The criticality level (High/Medium/Low).
        :param statement: The requirement statement for context.
        :return: Formatted CSA justification string with citations.
        :raises CSAGuidanceNotFoundError: If no matching CSA
                guidance is found in Pinecone.
        :requirement: URS-8.7 - System shall cite FDA CSA Guidance
                      to justify the testing level.
        """
        crit_lower = criticality.lower()

        if crit_lower == "high":
            query = (
                "FDA CSA guidance scripted testing high risk "
                "critical thinking patient safety "
                "rigorous documentation traceability "
                f"{statement}"
            )
        elif crit_lower == "medium":
            query = (
                "FDA CSA guidance hybrid testing medium risk "
                "scripted unscripted combination "
                f"{statement}"
            )
        else:
            query = (
                "FDA CSA guidance unscripted testing low risk "
                "tester expertise exploratory objective-based "
                f"{statement}"
            )

        embedding = self._get_embedding(query)
        matches = self._query_pinecone(embedding)

        if not matches:
            raise CSAGuidanceNotFoundError(criticality)

        justification_parts = []
        seen_sources = set()

        for match in matches[:3]:
            source = match["source_document"] or "Unknown"
            page = match["page_number"] or 0
            text = match["text"][:200] if match["text"] else ""

            source_key = f"{source}:p{page}"
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                justification_parts.append(
                    f"Per {source} (p.{page}): {text}..."
                )

        return " | ".join(justification_parts)

    def _validate_urs_input(
        self, urs: Dict[str, Any]
    ) -> None:
        """
        Validate that the URS dictionary contains required fields.

        :param urs: URS dictionary from RequirementArchitect.
        :raises InvalidURSInputError: If required fields missing.
        :requirement: URS-8.2 - System shall validate URS input.
        """
        missing = [
            f for f in URS_REQUIRED_FIELDS if f not in urs
        ]
        if missing:
            raise InvalidURSInputError(missing)

    def _determine_validation_type(
        self, criticality: str
    ) -> ValidationType:
        """
        Determine validation type based on requirement criticality.

        Per FDA CSA Guidance:
        - High criticality -> Scripted (full traceability required)
        - Medium criticality -> Scripted (hybrid approach)
        - Low criticality -> Unscripted (leverage tester expertise)

        :param criticality: Criticality string from URS.
        :return: ValidationType enum value.
        :requirement: URS-8.3 - System shall assign validation type.
        """
        criticality_lower = criticality.lower()
        if criticality_lower in ("high", "medium"):
            return ValidationType.SCRIPTED
        return ValidationType.UNSCRIPTED

    def _generate_test_id(
        self, urs_id: str, step: int
    ) -> str:
        """
        Generate a unique test step identifier.

        :param urs_id: The parent URS ID.
        :param step: The step number within this test script.
        :return: Test ID in format TC-<URS_ID>-<step>.
        :requirement: URS-8.4 - Each test step shall include ID.
        """
        return f"TC-{urs_id}-{step}"

    def generate_test_script(
        self, urs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a test script from a URS requirement dictionary.

        Produces a test script whose structure depends on the
        Criticality field of the input URS:

        - **High**: Detailed Scripted Test with preconditions,
          discrete numbered actions, exact pass/fail criteria,
          boundary testing, error handling verification, and
          audit trail confirmation.
        - **Medium**: Scripted Test with focused verification
          steps covering function, boundaries, and traceability.
        - **Low**: Unscripted Test with objective-based steps
          defining the test objective, exploratory scope, and
          acceptance criteria for tester-driven exploration.

        Queries Pinecone for FDA CSA Guidance to justify why the
        selected testing level is appropriate.

        :param urs: URS dictionary with keys URS_ID,
                    Requirement_Statement, Criticality, and
                    Regulatory_Rationale.
        :return: Dictionary containing the full test script.
        :raises InvalidURSInputError: If URS is missing fields.
        :raises CSAGuidanceNotFoundError: If no FDA CSA guidance
                is found in Pinecone.
        :requirement: URS-8.1 - System shall generate test scripts.

        Example:
            >>> gen = TestGenerator()
            >>> urs = {
            ...     "URS_ID": "URS-7.1",
            ...     "Requirement_Statement": "The system shall "
            ...         "track warehouse temperature.",
            ...     "Criticality": "High",
            ...     "Regulatory_Rationale": "Per GAMP 5 ..."
            ... }
            >>> script = gen.generate_test_script(urs)
            >>> print(script["CSA_Justification"])
            Per FDA_CSA_Guidance.pdf (p.12): ...
        """
        self._validate_urs_input(urs)

        urs_id = urs["URS_ID"]
        statement = urs["Requirement_Statement"]
        criticality = urs["Criticality"]
        rationale = urs["Regulatory_Rationale"]

        validation_type = self._determine_validation_type(
            criticality
        )

        csa_justification = self._fetch_csa_justification(
            criticality, statement
        )

        crit_lower = criticality.lower()
        if crit_lower == "high":
            steps = self._build_scripted_steps(
                urs_id, statement, rationale, validation_type
            )
            step_strategy = "Rigorous Scripted (6 steps)"
        elif crit_lower == "low":
            steps = self._build_unscripted_steps(
                urs_id, statement, rationale, validation_type
            )
            step_strategy = "Objective-Based Unscripted (3 steps)"
        else:
            steps = self._build_medium_steps(
                urs_id, statement, rationale, validation_type
            )
            step_strategy = "Focused Scripted (4 steps)"

        script = TestScript(
            urs_id=urs_id,
            requirement_statement=statement,
            criticality=criticality,
            csa_justification=csa_justification,
            steps=steps,
        )

        # Build decision logic summary from actual reasoning
        first_test_id = steps[0].test_id if steps else "N/A"

        # Extract first CSA source citation for the summary
        csa_ref_short = csa_justification.split("|")[0].strip()
        if len(csa_ref_short) > 120:
            csa_ref_short = csa_ref_short[:117] + "..."

        decision_logic = (
            f"Determined {first_test_id} is "
            f"{validation_type.value} because Criticality "
            f"is {criticality} ({crit_lower.capitalize()}); "
            f"selected {step_strategy}; "
            f"CSA justification: {csa_ref_short}"
        )

        _log_integrity_event(
            agent_name="TestGenerator",
            action="TEST_SCRIPT_GENERATED",
            decision_logic=decision_logic,
        )

        return script.to_dict()

    def _get_cache_path(self, urs_id: str) -> Path:
        """
        Return the cache file path for a given URS ID.

        :param urs_id: The URS identifier (e.g. "URS-7.1").
        :return: Path to the cached JSON test script.
        """
        safe_name = urs_id.replace(".", "_").replace(
            " ", "_"
        )
        return self._cache_dir / f"{safe_name}.json"

    def _load_cached_script(
        self, urs_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load a cached test script from disk.

        :param urs_id: The URS identifier.
        :return: Cached test script dict, or None if not found.
        """
        cache_path = self._get_cache_path(urs_id)
        if not cache_path.exists():
            return None
        try:
            return json.loads(
                cache_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            return None

    def _save_cached_script(
        self,
        urs_id: str,
        script: Dict[str, Any],
        source_mtime: float,
    ) -> None:
        """
        Save a test script to the cache with the source file's
        last-modified timestamp.

        :param urs_id: The URS identifier.
        :param script: The generated test script dict.
        :param source_mtime: The source URS file's mtime.
        """
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        cached = {
            "source_mtime": source_mtime,
            "script": script,
        }

        cache_path = self._get_cache_path(urs_id)
        cache_path.write_text(
            json.dumps(cached, indent=2),
            encoding="utf-8",
        )

    def generate_test_script_if_stale(
        self,
        urs: Dict[str, Any],
        source_file: Path,
    ) -> Dict[str, Any]:
        """
        Generate a test script only if the source URS file has
        been modified since the last cached generation.

        Compares the last-modified timestamp of the source URS
        Markdown file against the timestamp stored in the cached
        test script JSON. If the requirement file is newer than
        the cached script, the test is regenerated and the cache
        is updated. If the cache is still fresh, the cached
        script is returned without calling the API.

        :param urs: URS dictionary with keys URS_ID,
                    Requirement_Statement, Criticality, and
                    Regulatory_Rationale.
        :param source_file: Path to the source URS Markdown file.
        :return: Dictionary containing the test script (cached
                 or freshly generated).
        :raises InvalidURSInputError: If URS is missing fields.
        :raises CSAGuidanceNotFoundError: If no FDA CSA guidance
                is found in Pinecone.
        :requirement: URS-8.14 - System shall skip test
                      regeneration when the source requirement
                      has not changed.
        """
        self._validate_urs_input(urs)
        urs_id = urs["URS_ID"]

        source_mtime = source_file.stat().st_mtime

        cached = self._load_cached_script(urs_id)
        if cached is not None:
            cached_mtime = cached.get("source_mtime", 0.0)
            if source_mtime <= cached_mtime:
                logger.info(
                    "%s: Requirement unchanged — skipping "
                    "regeneration (cached).",
                    urs_id,
                )
                return cached["script"]

        logger.info(
            "%s: Requirement is newer — regenerating "
            "test script.",
            urs_id,
        )
        script = self.generate_test_script(urs)

        self._save_cached_script(urs_id, script, source_mtime)

        return script

    def _build_scripted_steps(
        self,
        urs_id: str,
        statement: str,
        rationale: str,
        validation_type: ValidationType,
    ) -> List[TestStep]:
        """
        Build detailed Scripted Test steps for High criticality.

        Generates a comprehensive step-by-step procedure with:
        1. Precondition verification
        2. Primary function execution and verification
        3. Input validation and boundary testing
        4. Error handling and recovery verification
        5. Data integrity and persistence confirmation
        6. Audit trail and regulatory traceability check

        :param urs_id: The URS identifier.
        :param statement: The requirement statement.
        :param rationale: The regulatory rationale.
        :param validation_type: Will be Scripted.
        :return: List of TestStep objects.
        :requirement: URS-8.11 - High criticality requirements
                      shall receive detailed scripted test steps.
        """
        vtype = validation_type.value

        steps = [
            TestStep(
                test_id=self._generate_test_id(urs_id, 1),
                step_description=(
                    "PRECONDITION: Confirm the system is in a "
                    "known, validated state. Verify all "
                    "prerequisite configurations, user "
                    "permissions, and dependent services are "
                    "active and operating within specification."
                ),
                expected_result=(
                    "System is accessible, all prerequisite "
                    "conditions are met, and the environment "
                    "matches the validated baseline."
                ),
                validation_type=vtype,
            ),
            TestStep(
                test_id=self._generate_test_id(urs_id, 2),
                step_description=(
                    f"EXECUTE: Perform the primary action "
                    f"described by the requirement. "
                    f"Action: {statement} "
                    f"Use representative production data or "
                    f"approved test data that exercises the "
                    f"full functional scope."
                ),
                expected_result=(
                    f"The system completes the action "
                    f"successfully. Observed behavior matches "
                    f"the requirement: {statement} "
                    f"No errors, warnings, or unexpected "
                    f"deviations occur."
                ),
                validation_type=vtype,
            ),
            TestStep(
                test_id=self._generate_test_id(urs_id, 3),
                step_description=(
                    "BOUNDARY TEST: Submit minimum, maximum, "
                    "and out-of-range values for all inputs "
                    "related to this requirement. Include "
                    "null, empty, and special-character inputs "
                    "where applicable."
                ),
                expected_result=(
                    "System accepts all valid boundary values "
                    "and produces correct results. System "
                    "rejects out-of-range and invalid inputs "
                    "with clear, user-facing error messages. "
                    "No data corruption occurs."
                ),
                validation_type=vtype,
            ),
            TestStep(
                test_id=self._generate_test_id(urs_id, 4),
                step_description=(
                    "ERROR HANDLING: Simulate failure "
                    "conditions (e.g., network timeout, "
                    "invalid credentials, service "
                    "unavailability) during the operation "
                    "described by this requirement."
                ),
                expected_result=(
                    "System handles each failure gracefully "
                    "with appropriate error codes, does not "
                    "expose sensitive information, and "
                    "recovers to a consistent state without "
                    "data loss."
                ),
                validation_type=vtype,
            ),
            TestStep(
                test_id=self._generate_test_id(urs_id, 5),
                step_description=(
                    "DATA INTEGRITY: After executing the "
                    "primary action, verify that all data "
                    "created or modified is persisted "
                    "correctly. Confirm values in the "
                    "database or output match expected results "
                    "and no unintended side effects occurred."
                ),
                expected_result=(
                    "Stored data is accurate and complete. "
                    "No orphaned records, no truncation, and "
                    "all related entities are consistent."
                ),
                validation_type=vtype,
            ),
            TestStep(
                test_id=self._generate_test_id(urs_id, 6),
                step_description=(
                    "AUDIT TRAIL: Confirm that every action "
                    "performed in this test is recorded in the "
                    "21 CFR Part 11 compliant audit log with "
                    "user_id, timestamp, and action. "
                    f"Regulatory rationale: {rationale}"
                ),
                expected_result=(
                    "Audit log contains a complete, "
                    "chronological, tamper-evident record of "
                    "all operations. Each entry includes "
                    "user_id, timestamp, and action. Evidence "
                    "is traceable to the regulatory rationale."
                ),
                validation_type=vtype,
            ),
        ]

        return steps

    def _build_unscripted_steps(
        self,
        urs_id: str,
        statement: str,
        rationale: str,
        validation_type: ValidationType,
    ) -> List[TestStep]:
        """
        Build objective-based Unscripted Test steps for Low
        criticality.

        Generates exploratory test guidance with:
        1. Test objective defining what to verify
        2. Exploratory scope defining areas to exercise
        3. Acceptance criteria defining pass/fail conditions

        Per FDA CSA Guidance, unscripted testing leverages the
        tester's domain expertise and critical thinking to verify
        low-risk functionality without rigid step-by-step scripts.

        :param urs_id: The URS identifier.
        :param statement: The requirement statement.
        :param rationale: The regulatory rationale.
        :param validation_type: Will be Unscripted.
        :return: List of TestStep objects.
        :requirement: URS-8.12 - Low criticality requirements
                      shall receive objective-based unscripted
                      test steps.
        """
        vtype = validation_type.value

        steps = [
            TestStep(
                test_id=self._generate_test_id(urs_id, 1),
                step_description=(
                    f"OBJECTIVE: Verify that the system "
                    f"satisfies the following requirement "
                    f"through exploratory testing: "
                    f"{statement} "
                    f"The tester should use domain expertise "
                    f"and critical thinking to exercise the "
                    f"feature in realistic usage scenarios."
                ),
                expected_result=(
                    f"The system behaves as expected for "
                    f"the requirement: {statement} "
                    f"The tester confirms the feature works "
                    f"correctly under normal usage conditions."
                ),
                validation_type=vtype,
            ),
            TestStep(
                test_id=self._generate_test_id(urs_id, 2),
                step_description=(
                    "EXPLORATORY SCOPE: Exercise the feature "
                    "across its typical usage patterns. "
                    "Explore related workflows, common user "
                    "paths, and reasonable edge cases based "
                    "on tester judgment. Document any "
                    "observations, anomalies, or usability "
                    "concerns encountered during exploration."
                ),
                expected_result=(
                    "Feature operates correctly across "
                    "explored scenarios. No critical defects "
                    "or unexpected behaviors are observed. "
                    "Tester documents findings with enough "
                    "detail to reproduce any issues found."
                ),
                validation_type=vtype,
            ),
            TestStep(
                test_id=self._generate_test_id(urs_id, 3),
                step_description=(
                    f"ACCEPTANCE CRITERIA: Confirm overall "
                    f"fitness-for-use of the feature. "
                    f"Regulatory context: {rationale}"
                ),
                expected_result=(
                    "Tester attests that the feature meets "
                    "its intended purpose and no issues "
                    "were found that would impact quality "
                    "or compliance. Testing summary is "
                    "recorded for audit reference."
                ),
                validation_type=vtype,
            ),
        ]

        return steps

    def _build_medium_steps(
        self,
        urs_id: str,
        statement: str,
        rationale: str,
        validation_type: ValidationType,
    ) -> List[TestStep]:
        """
        Build Scripted Test steps for Medium criticality.

        Generates a focused verification procedure with:
        1. Functional verification of the requirement
        2. Boundary and negative-case validation
        3. Data integrity confirmation
        4. Regulatory traceability check

        :param urs_id: The URS identifier.
        :param statement: The requirement statement.
        :param rationale: The regulatory rationale.
        :param validation_type: Will be Scripted.
        :return: List of TestStep objects.
        :requirement: URS-8.13 - Medium criticality requirements
                      shall receive focused scripted test steps.
        """
        vtype = validation_type.value

        steps = [
            TestStep(
                test_id=self._generate_test_id(urs_id, 1),
                step_description=(
                    f"VERIFY FUNCTION: Execute the action "
                    f"described by the requirement: "
                    f"{statement} "
                    f"Use standard test data that covers the "
                    f"primary functional scope."
                ),
                expected_result=(
                    f"System behavior matches the "
                    f"requirement: {statement} "
                    f"Operation completes without errors."
                ),
                validation_type=vtype,
            ),
            TestStep(
                test_id=self._generate_test_id(urs_id, 2),
                step_description=(
                    "BOUNDARY VALIDATION: Test boundary "
                    "values and common invalid inputs for "
                    "this requirement. Verify error messages "
                    "are clear and no data loss occurs."
                ),
                expected_result=(
                    "System handles boundary and invalid "
                    "inputs correctly with appropriate "
                    "error messages. No data corruption."
                ),
                validation_type=vtype,
            ),
            TestStep(
                test_id=self._generate_test_id(urs_id, 3),
                step_description=(
                    "DATA INTEGRITY: Confirm that data "
                    "created or modified by this operation "
                    "is persisted accurately and completely."
                ),
                expected_result=(
                    "Stored data matches expected values. "
                    "No unintended modifications to related "
                    "records."
                ),
                validation_type=vtype,
            ),
            TestStep(
                test_id=self._generate_test_id(urs_id, 4),
                step_description=(
                    f"TRACEABILITY: Verify the operation is "
                    f"recorded in the audit trail. "
                    f"Regulatory rationale: {rationale}"
                ),
                expected_result=(
                    "Audit log entry exists with user_id, "
                    "timestamp, and action. Evidence is "
                    "traceable to the regulatory rationale."
                ),
                validation_type=vtype,
            ),
        ]

        return steps

    def generate_batch(
        self, urs_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate test scripts for a batch of URS requirements.

        :param urs_list: List of URS dictionaries.
        :return: List of test script dictionaries.
        :raises InvalidURSInputError: If any URS is invalid.
        :raises CSAGuidanceNotFoundError: If CSA guidance is not
                found for any requirement.
        :requirement: URS-8.6 - System shall support batch
                      generation.
        """
        results = [
            self.generate_test_script(urs) for urs in urs_list
        ]

        # Summarise the batch composition for the audit trail
        crit_counts: Dict[str, int] = {}
        for r in results:
            crit = r.get("Criticality", "Unknown")
            crit_counts[crit] = crit_counts.get(crit, 0) + 1
        breakdown = ", ".join(
            f"{cnt} {lvl}" for lvl, cnt in crit_counts.items()
        )
        decision_logic = (
            f"Batch-generated {len(results)} test scripts "
            f"from {len(urs_list)} URS inputs; "
            f"criticality breakdown: {breakdown}"
        )

        _log_integrity_event(
            agent_name="TestGenerator",
            action="TEST_BATCH_GENERATED",
            decision_logic=decision_logic,
        )

        return results
