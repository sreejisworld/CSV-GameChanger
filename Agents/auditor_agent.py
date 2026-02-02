"""
Auditor Agent Module.

Owns Validation Traceability Matrix (VTM) and Validation Summary
Report (VSR) generation -- the validation audit deliverables.
Wraps the stateless ``scripts.generate_vtm`` and
``scripts.draft_vsr`` functions behind audit-logged methods.

:requirement: URS-12.1 - Verify generated URS against GAMP 5 text.
"""
from pathlib import Path
from typing import Any, Dict, Optional

from Agents.integrity_manager import (
    log_audit_event as _log_integrity_event,
)
from scripts.generate_vtm import (
    generate_vtm as _generate_vtm,
)
from scripts.draft_vsr import (
    draft_vsr as _draft_vsr,
)


# Default paths (mirror the script-level defaults)
_PROJECT_ROOT = Path(__file__).parent.parent
_DEFAULT_URS_DIR = _PROJECT_ROOT / "output" / "urs"
_DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "output"
_DEFAULT_VSR_DIR = _DEFAULT_OUTPUT_DIR / "vsr"
_DEFAULT_HEALTH_REPORT = (
    _DEFAULT_OUTPUT_DIR / "Trustme_Health_Report.txt"
)
_DEFAULT_VTM_CSV = (
    _DEFAULT_OUTPUT_DIR / "Trustme_Traceability_Matrix.csv"
)


class AuditorAgentError(Exception):
    """
    Error code: CSV-013 - Auditor agent processing failed.

    :requirement: URS-12.1 - Verification deliverable generation.
    """

    error_code = "CSV-013"


class AuditorAgent:
    """
    Facade that wraps VTM and VSR generation behind
    audit-logged methods.

    :requirement: URS-12.1 - Verify generated URS against
                  GAMP 5 text.
    """

    def __init__(self) -> None:
        """
        Initialize the AuditorAgent.

        No state is needed; the wrapped scripts are stateless
        functions.

        :requirement: URS-12.1 - Verification deliverable
                      generation.
        """

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def generate_vtm(
        self,
        urs_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a Validation Traceability Matrix.

        :param urs_dir: Directory containing URS Markdown files.
        :param output_dir: Directory to write the VTM output.
        :param verbose: Whether to print progress to stdout.
        :return: VTM generation result dictionary.
        :raises AuditorAgentError: If VTM generation fails.
        :requirement: URS-12.1 - Verification deliverable
                      generation.
        """
        urs_path = urs_dir or _DEFAULT_URS_DIR
        out_path = output_dir or _DEFAULT_OUTPUT_DIR
        try:
            result = _generate_vtm(
                urs_dir=urs_path,
                output_dir=out_path,
                verbose=verbose,
            )
        except Exception as exc:
            raise AuditorAgentError(
                f"VTM generation failed: {exc}"
            ) from exc
        _log_integrity_event(
            agent_name="AuditorAgent",
            action="VTM_GENERATED",
            decision_logic=(
                f"Generated VTM from {urs_path} -> {out_path}"
            ),
        )
        return result

    def generate_vsr(
        self,
        urs_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        health_report_path: Optional[Path] = None,
        vtm_csv_path: Optional[Path] = None,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o",
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a Validation Summary Report.

        :param urs_dir: Directory containing URS Markdown files.
        :param output_dir: Directory to write the VSR output.
        :param health_report_path: Path to Trustme_Health_Report.
        :param vtm_csv_path: Path to Trustme_Traceability_Matrix.
        :param openai_api_key: OpenAI API key (env var fallback).
        :param model: LLM model name for VSR generation.
        :param verbose: Whether to print progress to stdout.
        :return: VSR generation result dictionary.
        :raises AuditorAgentError: If VSR generation fails.
        :requirement: URS-12.1 - Verification deliverable
                      generation.
        """
        urs_path = urs_dir or _DEFAULT_URS_DIR
        out_path = output_dir or _DEFAULT_VSR_DIR
        hr_path = health_report_path or _DEFAULT_HEALTH_REPORT
        vtm_path = vtm_csv_path or _DEFAULT_VTM_CSV
        try:
            result = _draft_vsr(
                urs_dir=urs_path,
                output_dir=out_path,
                health_report_path=hr_path,
                vtm_csv_path=vtm_path,
                openai_api_key=openai_api_key,
                model=model,
                verbose=verbose,
            )
        except Exception as exc:
            raise AuditorAgentError(
                f"VSR generation failed: {exc}"
            ) from exc
        _log_integrity_event(
            agent_name="AuditorAgent",
            action="VSR_GENERATED",
            decision_logic=(
                f"Generated VSR from {urs_path} -> {out_path}"
            ),
        )
        return result
