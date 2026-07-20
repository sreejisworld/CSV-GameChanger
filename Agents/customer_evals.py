"""
customer_evals.py - Bring-Your-Own-Golden-Set harness.

Sprint 49. Answers vendor-governance question #3:

    "Can we run independent performance testing against our
     own data?"

A customer writes a golden set of THEIR requirement statements
with THEIR expectations (keywords, framework citations,
criticality, acceptance-criteria minimums), loads it here, and
runs it through the same eval machinery EVOLV uses on itself
(``Agents/agent_evals.py``). The output is the same EvalRun
format the Trusted Evals suite produces - directly comparable
to the vendor's own numbers, generated on the customer's side
without EVOLV involvement.

Golden-set file format (JSON list):

    [{"id": "CUST-001", "name": "sample_receipt",
      "input": "The system shall log sample receipt ...",
      "expected": {
          "must_contain_keywords": ["sample", "receipt"],
          "must_cite_frameworks": ["21 CFR Part 11"],
          "expected_criticality": "High",
          "acceptance_criteria_min": 1}}]

CLI:
    python -m Agents.customer_evals --file my_golden_set.json
    python -m Agents.customer_evals --file set.json --json

:requirement: URS-49.1 - Customer-supplied golden-set eval
              harness (independent performance testing).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from Agents.agent_evals import (
    EvalRun,
    run_evals,
    summarise_eval_run,
)


class CustomerGoldenSetError(Exception):
    """Error code: CSV-061 - Invalid customer golden set."""

    error_code = "CSV-061"


_REQUIRED_KEYS = {"id", "name", "input", "expected"}


def validate_golden_set(
    entries: List[Dict[str, Any]],
) -> List[str]:
    """Validate a customer golden set's shape.

    Deterministic and dependency-free so a customer can lint
    their file before scheduling a full run.

    :param entries: Parsed golden-set list.
    :return: List of human-readable problems (empty = valid).
    :requirement: URS-49.1 - Customer golden-set harness.
    """
    problems: List[str] = []
    if not isinstance(entries, list) or not entries:
        return ["Golden set must be a non-empty JSON list."]
    seen_ids: set = set()
    for i, e in enumerate(entries):
        where = f"entry {i + 1}"
        if not isinstance(e, dict):
            problems.append(f"{where}: not an object.")
            continue
        missing = _REQUIRED_KEYS - e.keys()
        if missing:
            problems.append(
                f"{where}: missing keys "
                f"{sorted(missing)}."
            )
            continue
        if e["id"] in seen_ids:
            problems.append(
                f"{where}: duplicate id '{e['id']}'."
            )
        seen_ids.add(e["id"])
        if not str(e["input"]).strip():
            problems.append(f"{where}: empty input.")
        exp = e["expected"]
        if not isinstance(exp, dict):
            problems.append(
                f"{where}: 'expected' must be an object."
            )
            continue
        crit = exp.get("expected_criticality")
        if crit not in (None, "High", "Medium", "Low"):
            problems.append(
                f"{where}: expected_criticality must be "
                "High | Medium | Low | null."
            )
    return problems


def load_golden_set(path: Path) -> List[Dict[str, Any]]:
    """Load and validate a customer golden-set JSON file.

    :param path: Path to the JSON file.
    :return: Validated golden-set list.
    :raises CustomerGoldenSetError: On parse/shape problems.
    :requirement: URS-49.1 - Customer golden-set harness.
    """
    try:
        entries = json.loads(
            Path(path).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CustomerGoldenSetError(
            f"[CSV-061] Cannot read golden set: {exc}"
        ) from exc
    problems = validate_golden_set(entries)
    if problems:
        raise CustomerGoldenSetError(
            "[CSV-061] Invalid golden set:\n  "
            + "\n  ".join(problems)
        )
    return entries


def run_customer_evals(
    golden_set: List[Dict[str, Any]],
) -> EvalRun:
    """Run a customer golden set through the standard eval
    engine (RequirementArchitect path - requires the corpus
    and embedding credentials of the deployment it runs in).

    :param golden_set: Validated golden-set list.
    :return: EvalRun in the standard Trusted Evals format.
    :requirement: URS-49.1 - Customer golden-set harness.
    """
    return run_evals(
        agent_name="RequirementArchitect",
        golden_set=golden_set,
    )


def _cli() -> None:
    """CLI entrypoint for customer-side independent testing.

    :requirement: URS-49.1 - Customer golden-set harness.
    """
    import argparse
    parser = argparse.ArgumentParser(
        prog="evolv-customer-evals",
        description=(
            "Run YOUR golden set through EVOLV's eval engine."
        ),
    )
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true",
                        help="Lint the file; no agent calls.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    entries = load_golden_set(args.file)
    if args.validate_only:
        print(
            f"Golden set OK: {len(entries)} entries, "
            "shape valid."
        )
        return
    run = run_customer_evals(entries)
    if args.json or args.out:
        payload = json.dumps(run.to_dict(), indent=2)
        if args.out:
            args.out.write_text(payload, encoding="utf-8")
            print(f"Wrote report to {args.out}")
        else:
            print(payload)
    else:
        print(summarise_eval_run(run))


if __name__ == "__main__":
    _cli()
