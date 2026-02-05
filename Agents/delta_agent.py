"""
Delta Agent Module.

Owns the CSA risk-based testing strategy determination and test
script generation.  Acts as an audit-logged facade over
``risk_strategist.get_csa_testing_strategy`` and ``TestGenerator``.

Also provides deterministic CSA test script generation from UR/FR
documents via ``generate_csa_test_from_ur_fr()``.

:requirement: URS-4.1 - System shall recommend testing strategy
              per CSA.
:requirement: URS-17.1 - System shall generate CSA test scripts
              from UR/FR documents.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from Agents.integrity_manager import (
    log_audit_event as _log_integrity_event,
)
from Agents.risk_strategist import (
    RiskLevel,
    TestingStrategy,
    get_csa_testing_strategy,
)
from Agents.test_generator import TestGenerator


# ------------------------------------------------------------------
# Enums for CSA test script generation
# ------------------------------------------------------------------


class CSATestType(Enum):
    """
    Type of CSA test to generate.

    :requirement: URS-17.2 - Support informal, OQ, and UAT test
                  types.
    """

    INFORMAL = "Informal"
    FORMAL_OQ = "Formal OQ"
    FORMAL_UAT = "Formal UAT"


class StepType(Enum):
    """
    Classification of a test step as Setup or Execution.

    :requirement: URS-17.3 - Separate setup from execution steps.
    """

    SETUP = "Setup"
    EXECUTION = "Execution"


class TestCaseType(Enum):
    """
    Classification of an execution step's test-case coverage.

    :requirement: URS-17.4 - Classify steps as positive, negative,
                  or edge case.
    """

    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    EDGE_CASE = "Edge Case"


# ------------------------------------------------------------------
# Dataclass for a single test step
# ------------------------------------------------------------------


@dataclass
class CSATestStep:
    """
    A single row in the CSA test script table.

    :requirement: URS-17.5 - Produce tabular test steps with
                  step type, number, title, instruction, expected
                  result, test case type, and requirement reference.
    """

    step_type: str
    step_number: int
    step_title: str
    step_instruction: str
    expected_result: str
    test_case_type: str
    requirement_reference: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to a dict matching the Excel column structure.

        :return: Dict representation of the step.
        """
        return asdict(self)


class DeltaAgentError(Exception):
    """
    Error code: CSV-012 - Delta agent processing failed.

    :requirement: URS-4.1 - Testing strategy determination.
    """

    error_code = "CSV-012"


class DeltaAgent:
    """
    Facade that unifies testing-strategy determination and test
    script generation behind audit-logged methods.

    :requirement: URS-4.1 - System shall recommend testing strategy
                  per CSA.
    """

    def __init__(self) -> None:
        """
        Initialize the DeltaAgent.

        The ``TestGenerator`` is created lazily on first use so
        that missing API keys do not block construction.

        :requirement: URS-4.1 - Testing strategy determination.
        """
        self._test_generator: Optional[TestGenerator] = None

    # ----------------------------------------------------------
    # Lazy accessor
    # ----------------------------------------------------------

    def _get_test_generator(self) -> TestGenerator:
        """
        Return the cached TestGenerator, creating it on first
        access.

        :return: TestGenerator instance.
        """
        if self._test_generator is None:
            self._test_generator = TestGenerator()
        return self._test_generator

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def determine_testing_strategy(
        self, risk_level: RiskLevel
    ) -> TestingStrategy:
        """
        Determine the CSA testing strategy for a given risk level.

        :param risk_level: Assessed GAMP 5 risk level.
        :return: Recommended TestingStrategy.
        :requirement: URS-4.4 - System shall recommend CSA testing
                      strategy.
        """
        strategy = get_csa_testing_strategy(risk_level)
        _log_integrity_event(
            agent_name="DeltaAgent",
            action="TESTING_STRATEGY_DETERMINED",
            decision_logic=(
                f"Risk={risk_level.value} -> "
                f"Strategy={strategy.value}"
            ),
        )
        return strategy

    def generate_test_script(
        self, urs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a CSA-aligned test script from a URS requirement.

        :param urs: Structured URS dictionary.
        :return: Test script dictionary.
        :raises DeltaAgentError: If test generation fails.
        :requirement: URS-8.1 - Generate test scripts from URS.
        """
        urs_id = urs.get("URS_ID", "unknown")
        try:
            generator = self._get_test_generator()
            result = generator.generate_test_script(urs)
        except Exception as exc:
            raise DeltaAgentError(
                f"Test script generation failed for "
                f"{urs_id}: {exc}"
            ) from exc
        _log_integrity_event(
            agent_name="DeltaAgent",
            action="TEST_SCRIPT_GENERATED",
            decision_logic=f"Generated test script for {urs_id}",
        )
        return result

    def generate_test_batch(
        self, urs_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate test scripts for a batch of URS requirements.

        :param urs_list: List of URS dictionaries.
        :return: List of test script dictionaries.
        :raises DeltaAgentError: If batch generation fails.
        :requirement: URS-8.6 - Support batch generation.
        """
        try:
            generator = self._get_test_generator()
            results = generator.generate_batch(urs_list)
        except Exception as exc:
            raise DeltaAgentError(
                f"Batch test generation failed for "
                f"{len(urs_list)} URS documents: {exc}"
            ) from exc
        _log_integrity_event(
            agent_name="DeltaAgent",
            action="TEST_BATCH_GENERATED",
            decision_logic=(
                f"Generated {len(results)} test scripts "
                f"from {len(urs_list)} URS documents"
            ),
        )
        return results

    # ----------------------------------------------------------
    # CSA test script generation from UR/FR
    # ----------------------------------------------------------

    @staticmethod
    def _build_setup_steps(
        ur_fr: Dict[str, Any],
    ) -> List[CSATestStep]:
        """
        Generate common Setup steps for scripted tests.

        :param ur_fr: UR/FR document dictionary.
        :return: List of setup CSATestStep instances.
        :requirement: URS-17.3 - Separate setup from execution
                      steps.
        """
        return [
            CSATestStep(
                step_type=StepType.SETUP.value,
                step_number=1,
                step_title="Login as System Owner",
                step_instruction=(
                    "Log into the application using system "
                    "owner credentials."
                ),
                expected_result="",
                test_case_type="",
                requirement_reference="",
            ),
            CSATestStep(
                step_type=StepType.SETUP.value,
                step_number=2,
                step_title="Navigate to feature under test",
                step_instruction=(
                    "Navigate to the module or screen "
                    "related to the requirement: "
                    f"{ur_fr.get('requirement_summary', '')}."
                ),
                expected_result="",
                test_case_type="",
                requirement_reference="",
            ),
            CSATestStep(
                step_type=StepType.SETUP.value,
                step_number=3,
                step_title="Prepare test data",
                step_instruction=(
                    "Ensure test data is available and the "
                    "system is in a known baseline state."
                ),
                expected_result="",
                test_case_type="",
                requirement_reference="",
            ),
        ]

    @staticmethod
    def _build_positive_steps(
        fr: Dict[str, Any],
        ur_id: str,
        step_start: int,
    ) -> List[CSATestStep]:
        """
        Generate positive execution steps for one FR.

        :param fr: Functional requirement dictionary.
        :param ur_id: Parent user requirement ID.
        :param step_start: Starting step number.
        :return: List of positive CSATestStep instances.
        :requirement: URS-17.4 - Classify steps as positive,
                      negative, or edge case.
        """
        fr_id = fr.get("fr_id", "FR-?")
        statement = fr.get("statement", "")
        criteria = fr.get("acceptance_criteria", [])
        expected = (
            criteria[0]
            if criteria
            else f"System performs: {statement}"
        )
        return [
            CSATestStep(
                step_type=StepType.EXECUTION.value,
                step_number=step_start,
                step_title=(
                    f"Verify {fr_id} - {TestCaseType.POSITIVE.value}"
                ),
                step_instruction=(
                    f"Execute the function described by {fr_id}: "
                    f"{statement} Provide valid input and confirm "
                    f"the expected outcome."
                ),
                expected_result=expected,
                test_case_type=TestCaseType.POSITIVE.value,
                requirement_reference=f"{ur_id} / {fr_id}",
            ),
        ]

    @staticmethod
    def _build_negative_steps(
        fr: Dict[str, Any],
        ur_id: str,
        step_start: int,
    ) -> List[CSATestStep]:
        """
        Generate negative execution steps for one FR.

        :param fr: Functional requirement dictionary.
        :param ur_id: Parent user requirement ID.
        :param step_start: Starting step number.
        :return: List of negative CSATestStep instances.
        :requirement: URS-17.4 - Classify steps as positive,
                      negative, or edge case.
        """
        fr_id = fr.get("fr_id", "FR-?")
        statement = fr.get("statement", "")
        return [
            CSATestStep(
                step_type=StepType.EXECUTION.value,
                step_number=step_start,
                step_title=(
                    f"Verify {fr_id} - {TestCaseType.NEGATIVE.value}"
                ),
                step_instruction=(
                    f"Attempt to execute {fr_id}: {statement} "
                    f"using invalid or missing input data."
                ),
                expected_result=(
                    "System rejects the invalid input and "
                    "displays an appropriate error message "
                    "without data corruption."
                ),
                test_case_type=TestCaseType.NEGATIVE.value,
                requirement_reference=f"{ur_id} / {fr_id}",
            ),
        ]

    @staticmethod
    def _build_edge_case_steps(
        fr: Dict[str, Any],
        ur_id: str,
        step_start: int,
    ) -> List[CSATestStep]:
        """
        Generate edge-case execution steps for one FR.

        :param fr: Functional requirement dictionary.
        :param ur_id: Parent user requirement ID.
        :param step_start: Starting step number.
        :return: List of edge-case CSATestStep instances.
        :requirement: URS-17.4 - Classify steps as positive,
                      negative, or edge case.
        """
        fr_id = fr.get("fr_id", "FR-?")
        statement = fr.get("statement", "")
        return [
            CSATestStep(
                step_type=StepType.EXECUTION.value,
                step_number=step_start,
                step_title=(
                    f"Verify {fr_id} - "
                    f"{TestCaseType.EDGE_CASE.value}"
                ),
                step_instruction=(
                    f"Test boundary and limit conditions for "
                    f"{fr_id}: {statement} Use maximum, minimum, "
                    f"and boundary values."
                ),
                expected_result=(
                    "System handles boundary conditions "
                    "gracefully without error or data loss."
                ),
                test_case_type=TestCaseType.EDGE_CASE.value,
                requirement_reference=f"{ur_id} / {fr_id}",
            ),
        ]

    @staticmethod
    def _build_uat_steps(
        ur_fr: Dict[str, Any],
        step_start: int,
    ) -> List[CSATestStep]:
        """
        Generate UAT business-process execution steps.

        Steps simulate real user business-process flow across
        all FRs.  Plain language, business-driven, no
        field-level detail.

        :param ur_fr: UR/FR document dictionary.
        :param step_start: Starting step number.
        :return: List of UAT CSATestStep instances.
        :requirement: URS-17.6 - Generate UAT business-process
                      test steps.
        """
        ur = ur_fr.get("user_requirement", {})
        ur_id = ur.get("ur_id", "UR-?")
        frs = ur_fr.get("functional_requirements", [])
        summary = ur_fr.get("requirement_summary", "")

        steps: List[CSATestStep] = []
        num = step_start

        # Scenario description as first execution step
        steps.append(
            CSATestStep(
                step_type=StepType.EXECUTION.value,
                step_number=num,
                step_title="Business scenario overview",
                step_instruction=(
                    f"As an end user, perform the complete "
                    f"business process for: {summary}. "
                    f"Follow the normal workflow from start "
                    f"to finish."
                ),
                expected_result=(
                    "The end-to-end business process "
                    "completes successfully and the user "
                    "achieves the intended goal."
                ),
                test_case_type=TestCaseType.POSITIVE.value,
                requirement_reference=ur_id,
            ),
        )
        num += 1

        for fr in frs:
            fr_id = fr.get("fr_id", "FR-?")
            statement = fr.get("statement", "")
            criteria = fr.get("acceptance_criteria", [])
            expected = (
                criteria[0]
                if criteria
                else (
                    "Business outcome achieved as "
                    "described in the requirement."
                )
            )
            steps.append(
                CSATestStep(
                    step_type=StepType.EXECUTION.value,
                    step_number=num,
                    step_title=(
                        f"Confirm {fr_id} business outcome"
                    ),
                    step_instruction=(
                        f"Verify that the system supports: "
                        f"{statement}"
                    ),
                    expected_result=expected,
                    test_case_type=TestCaseType.POSITIVE.value,
                    requirement_reference=(
                        f"{ur_id} / {fr_id}"
                    ),
                ),
            )
            num += 1

        return steps

    @staticmethod
    def _build_charter_steps(
        ur_fr: Dict[str, Any],
    ) -> List[CSATestStep]:
        """
        Generate unscripted exploratory charter steps in
        tabular format for Medium/Low risk.

        :param ur_fr: UR/FR document dictionary.
        :return: List of charter CSATestStep instances.
        :requirement: URS-17.7 - Generate unscripted test
                      charters for medium/low risk.
        """
        ur = ur_fr.get("user_requirement", {})
        ur_id = ur.get("ur_id", "UR-?")
        frs = ur_fr.get("functional_requirements", [])
        summary = ur_fr.get("requirement_summary", "")

        steps: List[CSATestStep] = []

        # Setup step
        steps.append(
            CSATestStep(
                step_type=StepType.SETUP.value,
                step_number=1,
                step_title="Establish test environment",
                step_instruction=(
                    "Confirm system access and ensure the "
                    "application is in a known baseline "
                    "state for exploratory testing."
                ),
                expected_result="",
                test_case_type="",
                requirement_reference="",
            ),
        )

        exec_num = 1
        for fr in frs:
            fr_id = fr.get("fr_id", "FR-?")
            statement = fr.get("statement", "")
            criteria = fr.get("acceptance_criteria", [])
            expected = (
                criteria[0]
                if criteria
                else (
                    "Feature operates as intended per "
                    "the requirement specification."
                )
            )
            steps.append(
                CSATestStep(
                    step_type=StepType.EXECUTION.value,
                    step_number=exec_num,
                    step_title=(
                        f"Exploratory: Verify {fr_id} "
                        f"core functionality"
                    ),
                    step_instruction=(
                        f"Using tester expertise, exercise "
                        f"the feature described by {fr_id}: "
                        f"{statement} Explore typical, "
                        f"atypical, and boundary usage "
                        f"patterns."
                    ),
                    expected_result=expected,
                    test_case_type=TestCaseType.POSITIVE.value,
                    requirement_reference=(
                        f"{ur_id} / {fr_id}"
                    ),
                ),
            )
            exec_num += 1

        # If no FRs, add a general exploratory step
        if not frs:
            steps.append(
                CSATestStep(
                    step_type=StepType.EXECUTION.value,
                    step_number=1,
                    step_title=(
                        "Exploratory: Verify core "
                        "functionality"
                    ),
                    step_instruction=(
                        f"Using tester expertise, exercise "
                        f"the feature: {summary}. Explore "
                        f"typical, atypical, and boundary "
                        f"usage patterns."
                    ),
                    expected_result=(
                        "Feature operates as intended per "
                        "the requirement specification."
                    ),
                    test_case_type=TestCaseType.POSITIVE.value,
                    requirement_reference=ur_id,
                ),
            )

        return steps

    @staticmethod
    def _build_quality_checklist(
        steps: List[CSATestStep],
    ) -> Dict[str, bool]:
        """
        Produce a quality self-check dict for the generated
        test script.

        :param steps: The generated test steps.
        :return: Quality checklist dict.
        :requirement: URS-17.8 - Self-check generated scripts
                      for quality.
        """
        exec_steps = [
            s for s in steps
            if s.step_type == StepType.EXECUTION.value
        ]
        return {
            "steps_clear_and_sequential": all(
                s.step_instruction for s in steps
            ),
            "expected_results_observable": all(
                s.expected_result for s in exec_steps
            ),
            "execution_steps_have_references": all(
                s.requirement_reference for s in exec_steps
            ),
            "test_types_assigned": all(
                s.test_case_type for s in exec_steps
            ),
            "no_redundant_steps": (
                len(steps)
                == len({s.step_title for s in steps})
            ),
        }

    def generate_csa_test_from_ur_fr(
        self,
        ur_fr: Dict[str, Any],
        test_type: str = "Informal",
    ) -> Dict[str, Any]:
        """
        Generate a CSA-aligned test script from a UR/FR document.

        High risk produces a full scripted test (setup + execution
        steps).  Medium/Low risk produces an unscripted test
        charter in the same tabular format.

        :param ur_fr: UR/FR document from
                      ``RequirementArchitect.transform_urs_to_ur_fr()``.
        :param test_type: One of ``"Informal"``,
                          ``"Formal OQ"``, ``"Formal UAT"``.
        :return: Test script dictionary.
        :raises DeltaAgentError: If generation fails.
        :requirement: URS-17.1 - Generate CSA test scripts from
                      UR/FR documents.
        """
        try:
            return self._do_generate_csa_test(
                ur_fr, test_type
            )
        except DeltaAgentError:
            raise
        except Exception as exc:
            urs_id = ur_fr.get("urs_id", "unknown")
            raise DeltaAgentError(
                f"CSA test generation failed for "
                f"{urs_id}: {exc}"
            ) from exc

    def _do_generate_csa_test(
        self,
        ur_fr: Dict[str, Any],
        test_type: str,
    ) -> Dict[str, Any]:
        """
        Internal implementation of CSA test generation.

        :param ur_fr: UR/FR document dictionary.
        :param test_type: Test type string.
        :return: Test script dictionary.
        """
        ur = ur_fr.get("user_requirement", {})
        risk_level = ur.get("risk_level", "Low")
        test_strategy = ur.get("test_strategy", "Informal")
        urs_id = ur_fr.get("urs_id", "unknown")
        ur_id = ur.get("ur_id", "UR-?")
        frs = ur_fr.get("functional_requirements", [])

        is_high = risk_level == "High"

        if is_high:
            steps = self._build_setup_steps(ur_fr)
            exec_num = 1

            for fr in frs:
                if test_type == CSATestType.FORMAL_UAT.value:
                    # UAT handled separately below
                    pass
                elif test_type == CSATestType.FORMAL_OQ.value:
                    pos = self._build_positive_steps(
                        fr, ur_id, exec_num,
                    )
                    steps.extend(pos)
                    exec_num += len(pos)
                else:
                    # Informal: positive + negative + edge
                    pos = self._build_positive_steps(
                        fr, ur_id, exec_num,
                    )
                    steps.extend(pos)
                    exec_num += len(pos)

                    neg = self._build_negative_steps(
                        fr, ur_id, exec_num,
                    )
                    steps.extend(neg)
                    exec_num += len(neg)

                    edge = self._build_edge_case_steps(
                        fr, ur_id, exec_num,
                    )
                    steps.extend(edge)
                    exec_num += len(edge)

            if test_type == CSATestType.FORMAL_UAT.value:
                uat = self._build_uat_steps(ur_fr, 1)
                # Replace execution steps with UAT steps
                steps = [
                    s for s in steps
                    if s.step_type == StepType.SETUP.value
                ] + uat

            script_id = f"TS-{urs_id}"
            action = "CSA_TEST_SCRIPT_GENERATED"
        else:
            steps = self._build_charter_steps(ur_fr)
            script_id = f"TC-{urs_id}"
            action = "CSA_TEST_CHARTER_GENERATED"

        checklist = self._build_quality_checklist(steps)

        result: Dict[str, Any] = {
            "script_id": script_id,
            "urs_id": urs_id,
            "ur_id": ur_id,
            "test_type": test_type,
            "risk_level": risk_level,
            "test_strategy": test_strategy,
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "steps": [s.to_dict() for s in steps],
            "quality_checklist": checklist,
        }

        _log_integrity_event(
            agent_name="DeltaAgent",
            action=action,
            decision_logic=(
                f"Generated {script_id} "
                f"(risk={risk_level}, type={test_type}) "
                f"with {len(steps)} steps"
            ),
            thought_process={
                "inputs": {
                    "urs_id": urs_id,
                    "ur_id": ur_id,
                    "risk_level": risk_level,
                    "test_type": test_type,
                },
                "steps": [
                    f"Risk level is {risk_level}",
                    (
                        "Generated scripted test steps"
                        if is_high
                        else "Generated charter steps"
                    ),
                    f"Produced {len(steps)} total steps",
                    "Quality checklist computed",
                ],
                "outputs": {
                    "script_id": script_id,
                    "step_count": len(steps),
                    "quality_checklist": checklist,
                },
            },
        )

        return result

    def generate_csa_test_batch(
        self,
        ur_fr_list: List[Dict[str, Any]],
        test_type: str = "Informal",
    ) -> List[Dict[str, Any]]:
        """
        Generate CSA test scripts for a batch of UR/FR documents.

        :param ur_fr_list: List of UR/FR document dicts.
        :param test_type: One of ``"Informal"``,
                          ``"Formal OQ"``, ``"Formal UAT"``.
        :return: List of test script dictionaries.
        :raises DeltaAgentError: If batch generation fails.
        :requirement: URS-17.8 - Support batch CSA test
                      generation.
        """
        results: List[Dict[str, Any]] = []
        for ur_fr in ur_fr_list:
            results.append(
                self.generate_csa_test_from_ur_fr(
                    ur_fr, test_type,
                )
            )

        _log_integrity_event(
            agent_name="DeltaAgent",
            action="CSA_TEST_BATCH_GENERATED",
            decision_logic=(
                f"Generated {len(results)} CSA test scripts "
                f"from {len(ur_fr_list)} UR/FR documents "
                f"(type={test_type})"
            ),
        )

        return results
