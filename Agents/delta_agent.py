"""
Delta Agent Module.

Owns the CSA risk-based testing strategy determination and test
script generation.  Acts as an audit-logged facade over
``risk_strategist.get_csa_testing_strategy`` and ``TestGenerator``.

:requirement: URS-4.1 - System shall recommend testing strategy
              per CSA.
"""
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
