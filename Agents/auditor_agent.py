"""
Auditor Agent Module.

Owns Validation Traceability Matrix (VTM) and Validation Summary
Report (VSR) generation -- the validation audit deliverables.
Wraps the stateless ``scripts.generate_vtm`` and
``scripts.draft_vsr`` functions behind audit-logged methods.

:requirement: URS-12.1 - Verify generated URS against GAMP 5 text.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    # ----------------------------------------------------------
    # Requirements Traceability Matrix
    # ----------------------------------------------------------

    def generate_rtm(
        self,
        ur_fr: Dict[str, Any],
        test_script: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a Requirements Traceability Matrix (RTM).

        Maps every Functional Requirement ID from the
        RequirementArchitect to every matching Test Step
        from the DeltaAgent test script.

        :param ur_fr: UR/FR document from
            ``RequirementArchitect.transform_urs_to_ur_fr()``.
        :param test_script: Test script from
            ``DeltaAgent.generate_csa_test_from_ur_fr()``.
        :return: RTM dict with rows and coverage metrics.
        :raises AuditorAgentError: If RTM generation fails.
        :requirement: URS-18.1 - Generate RTM from UR/FR
                      and test script.
        """
        try:
            return self._do_generate_rtm(
                ur_fr, test_script,
            )
        except AuditorAgentError:
            raise
        except Exception as exc:
            urs_id = ur_fr.get("urs_id", "unknown")
            raise AuditorAgentError(
                f"RTM generation failed for "
                f"{urs_id}: {exc}"
            ) from exc

    def _do_generate_rtm(
        self,
        ur_fr: Dict[str, Any],
        test_script: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Internal RTM generation logic.

        :param ur_fr: UR/FR document dictionary.
        :param test_script: Test script dictionary.
        :return: RTM dictionary.
        """
        urs_id = ur_fr.get("urs_id", "unknown")
        ur = ur_fr.get("user_requirement", {})
        ur_id = ur.get("ur_id", "UR-?")
        frs = ur_fr.get(
            "functional_requirements", [],
        )

        script_id = test_script.get(
            "script_id", "unknown",
        )
        steps = test_script.get("steps", [])

        # Build lookup: fr_id -> matching exec steps
        fr_map: Dict[str, List[Dict]] = {}
        for step in steps:
            ref = step.get(
                "requirement_reference", "",
            )
            if not ref:
                continue
            for fr in frs:
                fr_id = fr.get("fr_id", "")
                if fr_id and fr_id in ref:
                    fr_map.setdefault(
                        fr_id, [],
                    ).append(step)

        rows: List[Dict[str, Any]] = []
        covered = 0

        for fr in frs:
            fr_id = fr.get("fr_id", "")
            matching = fr_map.get(fr_id, [])

            if matching:
                covered += 1
                status = "Covered"
                step_refs = ", ".join(
                    f"{s['step_number']} "
                    f"({s.get('test_case_type', '-')})"
                    for s in matching
                )
                case_types = sorted({
                    s.get("test_case_type", "")
                    for s in matching
                    if s.get("test_case_type")
                })
            else:
                status = "Gap"
                step_refs = "-"
                case_types = []

            rows.append({
                "urs_id": urs_id,
                "ur_id": ur_id,
                "fr_id": fr_id,
                "requirement_statement": fr.get(
                    "statement", "",
                ),
                "test_script_id": script_id,
                "test_steps": step_refs,
                "test_case_types": case_types,
                "coverage_status": status,
            })

        total = len(frs)
        pct = (
            (covered / total * 100) if total else 0.0
        )

        result: Dict[str, Any] = {
            "rtm_id": f"RTM-{urs_id}",
            "generated_at": datetime.now(
                timezone.utc,
            ).isoformat(),
            "urs_id": urs_id,
            "ur_id": ur_id,
            "test_script_id": script_id,
            "risk_level": ur.get(
                "risk_level", "-",
            ),
            "test_strategy": ur.get(
                "test_strategy", "-",
            ),
            "total_requirements": total,
            "covered_requirements": covered,
            "gap_requirements": total - covered,
            "coverage_percentage": round(pct, 1),
            "rows": rows,
        }

        _log_integrity_event(
            agent_name="AuditorAgent",
            action="RTM_GENERATED",
            decision_logic=(
                f"Generated {result['rtm_id']}: "
                f"{covered}/{total} FRs covered "
                f"({pct:.0f}%)"
            ),
            thought_process={
                "inputs": {
                    "urs_id": urs_id,
                    "script_id": script_id,
                    "fr_count": total,
                },
                "steps": [
                    "Extracted FRs from UR/FR document",
                    "Matched test steps by "
                    "requirement_reference",
                    f"Found {covered} covered, "
                    f"{total - covered} gaps",
                ],
                "outputs": {
                    "rtm_id": result["rtm_id"],
                    "coverage_pct": pct,
                },
            },
        )

        return result
