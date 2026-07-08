"""
agent_evals.py — Trusted Evals for EVOLV specialist functions.

Why this module exists
======================
Salim Ismail's ExO 3.0 "Govern/Assure" architecture names four
pillars that keep an agentic engine trustable at speed. The first
pillar is **Trusted Evals**:

  > "Every agent runs continuously against a known test set.
  >  Drift flags alerts before customers see it."

Without a standing eval set, prompt iteration is unstable. A
well-meaning change to a RequirementArchitect prompt can silently
degrade output quality for weeks before anyone notices. With one,
every prompt change runs the gauntlet first.

This module is the **skeleton** form — Sprint 35.7 ships:
- A golden test set (10 input → expected-pattern pairs for
  RequirementArchitect)
- A `run_evals()` function with a deterministic similarity check
- A `summarise_eval_run()` reporter

Sprint 44 will extend this with:
- Continuous nightly runs against every registered agent
- Drift dashboard surfaced in Dev Portal
- Alert thresholds + Compliance Exception escalation
- LLM-as-judge for semantic similarity (where deterministic checks
  miss nuance)

For now, the skeleton is enough to demo the principle and run
manually before any agent prompt change ships.

:requirement: URS-38.1 - Standing eval set for every specialist
              function with deterministic pass/fail scoring.
:requirement: URS-38.2 - Run evals on demand from the command line
              or from a Dev Portal action.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


# ── Schema version for the eval format ──────────────────────────────
EVAL_SCHEMA_VERSION = "1.0.0"


# ── Golden test set for RequirementArchitect ────────────────────────
#
# Each entry is an input requirement statement plus a set of
# expected-pattern markers we look for in the output. Markers are:
#
#   - must_contain_keywords:   substrings that MUST appear in the URS
#                              statement (case-insensitive)
#   - must_cite_frameworks:    regulatory frameworks the rationale
#                              MUST reference
#   - expected_criticality:    None | "High" | "Medium" | "Low"
#   - acceptance_criteria_min: minimum number of acceptance criteria
#
# This is deliberately deterministic. LLM-as-judge for semantic
# similarity comes in Sprint 44. For now, exact-match patterns catch
# 80% of regressions for 0% LLM cost.

REQUIREMENT_ARCHITECT_GOLDEN_SET: List[Dict[str, Any]] = [
    {
        "id":    "RA-EVAL-001",
        "name":  "warehouse_temperature",
        "input": (
            "We need to monitor warehouse temperature continuously "
            "and alert on out-of-range conditions per 21 CFR Part 11."
        ),
        "expected": {
            "must_contain_keywords": [
                "temperature", "monitor",
            ],
            "must_cite_frameworks": [
                "21 CFR Part 11",
            ],
            "expected_criticality":    "High",
            "acceptance_criteria_min": 1,
        },
    },
    {
        "id":    "RA-EVAL-002",
        "name":  "esignature_disposal",
        "input": (
            "The system must enforce electronic signatures on every "
            "sample disposal event."
        ),
        "expected": {
            "must_contain_keywords": [
                "signature", "disposal",
            ],
            "must_cite_frameworks": [
                "21 CFR Part 11",
            ],
            "expected_criticality":    "High",
            "acceptance_criteria_min": 1,
        },
    },
    {
        "id":    "RA-EVAL-003",
        "name":  "audit_trail",
        "input": (
            "Maintain a complete audit trail of every change to a "
            "GxP record."
        ),
        "expected": {
            "must_contain_keywords": [
                "audit", "trail",
            ],
            "must_cite_frameworks": [
                "21 CFR Part 11",
            ],
            "expected_criticality":    "High",
            "acceptance_criteria_min": 1,
        },
    },
    {
        "id":    "RA-EVAL-004",
        "name":  "rbac_roles",
        "input": (
            "Provide role-based access control with named roles for "
            "lab tech, supervisor, QA reviewer."
        ),
        "expected": {
            "must_contain_keywords": [
                "role", "access",
            ],
            "must_cite_frameworks": [],
            "expected_criticality":    "Medium",
            "acceptance_criteria_min": 1,
        },
    },
    {
        "id":    "RA-EVAL-005",
        "name":  "sap_integration",
        "input": (
            "Synchronise material master data with SAP S/4HANA "
            "every 15 minutes."
        ),
        "expected": {
            "must_contain_keywords": [
                "SAP", "synchronise",
            ],
            "must_cite_frameworks": [],
            "expected_criticality":    "Medium",
            "acceptance_criteria_min": 1,
        },
    },
    {
        "id":    "RA-EVAL-006",
        "name":  "batch_release",
        "input": (
            "Enforce qualified e-signature on batch release decisions "
            "for sterile injectables."
        ),
        "expected": {
            "must_contain_keywords": [
                "batch", "release",
            ],
            "must_cite_frameworks": [
                "21 CFR Part 11",
            ],
            "expected_criticality":    "High",
            "acceptance_criteria_min": 1,
        },
    },
    {
        "id":    "RA-EVAL-007",
        "name":  "deviation_capa",
        "input": (
            "Track deviation events through to CAPA closure with "
            "approval gates at investigation and effectiveness check."
        ),
        "expected": {
            "must_contain_keywords": [
                "deviation", "CAPA",
            ],
            "must_cite_frameworks": [],
            "expected_criticality":    "High",
            "acceptance_criteria_min": 1,
        },
    },
    {
        "id":    "RA-EVAL-008",
        "name":  "reporting_dashboard",
        "input": (
            "Executive dashboard showing daily throughput and "
            "pending approvals for site directors."
        ),
        "expected": {
            "must_contain_keywords": [
                "dashboard", "throughput",
            ],
            "must_cite_frameworks": [],
            "expected_criticality":    "Low",
            "acceptance_criteria_min": 1,
        },
    },
    {
        "id":    "RA-EVAL-009",
        "name":  "instrument_capture",
        "input": (
            "Receive instrument data via HL7 interface and store with "
            "instrument-of-origin attribution."
        ),
        "expected": {
            "must_contain_keywords": [
                "HL7", "instrument",
            ],
            "must_cite_frameworks": [],
            "expected_criticality":    "Medium",
            "acceptance_criteria_min": 1,
        },
    },
    {
        "id":    "RA-EVAL-010",
        "name":  "chain_of_custody",
        "input": (
            "Capture full chain-of-custody per sample with immutable "
            "handler transition records."
        ),
        "expected": {
            "must_contain_keywords": [
                "custody", "sample",
            ],
            "must_cite_frameworks": [],
            "expected_criticality":    "High",
            "acceptance_criteria_min": 1,
        },
    },
]


# ── Result dataclasses ──────────────────────────────────────────────

@dataclass
class EvalCheck:
    """One named check inside a single eval."""
    name:     str
    passed:   bool
    detail:   str


@dataclass
class EvalResult:
    """Outcome of running a single eval entry."""
    eval_id:        str
    eval_name:      str
    input_text:     str
    output_summary: Optional[str]
    checks:         List[EvalCheck] = field(default_factory=list)
    score:          float = 0.0
    passed:         bool = False
    error:          Optional[str] = None

    @property
    def total_checks(self) -> int:
        return len(self.checks)

    @property
    def passed_checks(self) -> int:
        return sum(1 for c in self.checks if c.passed)


@dataclass
class EvalRun:
    """Aggregate of every eval in a run."""
    agent_name:        str
    schema_version:    str
    ran_at:            str
    eval_count:        int
    results:           List[EvalResult]
    aggregate_pass_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version":      self.schema_version,
            "agent_name":          self.agent_name,
            "ran_at":              self.ran_at,
            "eval_count":          self.eval_count,
            "aggregate_pass_rate": self.aggregate_pass_rate,
            "results": [
                {
                    "eval_id":        r.eval_id,
                    "eval_name":      r.eval_name,
                    "input_text":     r.input_text,
                    "output_summary": r.output_summary,
                    "score":          r.score,
                    "passed":         r.passed,
                    "error":          r.error,
                    "checks":         [
                        {
                            "name":   c.name,
                            "passed": c.passed,
                            "detail": c.detail,
                        }
                        for c in r.checks
                    ],
                    "passed_checks":  r.passed_checks,
                    "total_checks":   r.total_checks,
                }
                for r in self.results
            ],
        }


# ── Deterministic check helpers ─────────────────────────────────────

def _check_keywords(
    text: str, keywords: List[str],
) -> EvalCheck:
    """Lower-case substring search for each keyword."""
    if not keywords:
        return EvalCheck(
            name="keywords",
            passed=True,
            detail="No keywords required.",
        )
    text_lower = (text or "").lower()
    missing = [
        k for k in keywords
        if k.lower() not in text_lower
    ]
    return EvalCheck(
        name="keywords",
        passed=(len(missing) == 0),
        detail=(
            f"All {len(keywords)} required keywords present."
            if not missing
            else f"Missing keywords: {missing}"
        ),
    )


def _check_frameworks(
    rationale: str, frameworks: List[str],
) -> EvalCheck:
    """Each framework string must appear in the rationale text."""
    if not frameworks:
        return EvalCheck(
            name="frameworks",
            passed=True,
            detail="No frameworks required for citation.",
        )
    rationale_text = (rationale or "")
    missing = [
        f for f in frameworks
        if f not in rationale_text
    ]
    return EvalCheck(
        name="frameworks",
        passed=(len(missing) == 0),
        detail=(
            f"All {len(frameworks)} required frameworks cited."
            if not missing
            else f"Missing framework citations: {missing}"
        ),
    )


def _check_criticality(
    actual: Optional[str], expected: Optional[str],
) -> EvalCheck:
    """Exact match (case-sensitive) — criticality is a controlled vocab."""
    if expected is None:
        return EvalCheck(
            name="criticality",
            passed=True,
            detail="No criticality expectation set.",
        )
    return EvalCheck(
        name="criticality",
        passed=(actual == expected),
        detail=f"Expected '{expected}', got '{actual}'.",
    )


def _check_acceptance_criteria_count(
    actual_count: int, minimum: int,
) -> EvalCheck:
    """Count must be >= minimum."""
    return EvalCheck(
        name="acceptance_criteria",
        passed=(actual_count >= minimum),
        detail=(
            f"Found {actual_count} acceptance criteria "
            f"(minimum required: {minimum})."
        ),
    )


# ── Run engine ──────────────────────────────────────────────────────

def run_evals(
    agent_name: str = "RequirementArchitect",
    golden_set: Optional[List[Dict[str, Any]]] = None,
    architect_factory: Optional[Callable[[], Any]] = None,
) -> EvalRun:
    """
    Run the standing eval set against the named agent. Returns an
    EvalRun aggregate with per-eval results and a pass-rate summary.

    The `architect_factory` parameter lets callers inject a mock for
    unit testing without spinning up Pinecone + OpenAI. In production
    use, leave it as None and the function constructs a live
    RequirementArchitect.

    Failure modes are captured (not raised) so a single broken eval
    doesn't take down the whole run.

    :param agent_name: Which agent to eval. Today only
                       "RequirementArchitect" is supported; Sprint 44
                       extends to VerificationAgent + DeltaAgent.
    :param golden_set: Override the default golden set (for testing).
    :param architect_factory: Inject a callable returning an architect
                              instance (for testing).
    :return: EvalRun aggregate.
    :requirement: URS-38.2 - Run evals on demand.
    """
    if agent_name != "RequirementArchitect":
        # Sprint 44 will widen this. For now, fail loudly so
        # callers can't silently get empty results.
        raise NotImplementedError(
            f"Eval support for agent '{agent_name}' lands in "
            "Sprint 44. RequirementArchitect is the only "
            "supported agent in the Sprint 35.7 skeleton."
        )

    if golden_set is None:
        golden_set = REQUIREMENT_ARCHITECT_GOLDEN_SET

    # Late import — keeps this module loadable in environments
    # without Pinecone / OpenAI deps (unit tests, doc builds).
    if architect_factory is None:
        from Agents.requirement_architect import RequirementArchitect
        architect_factory = RequirementArchitect

    results: List[EvalResult] = []
    architect = None

    for entry in golden_set:
        result = EvalResult(
            eval_id=entry["id"],
            eval_name=entry["name"],
            input_text=entry["input"],
            output_summary=None,
        )
        try:
            if architect is None:
                architect = architect_factory()

            # Generate URS — defensive call. If this raises, capture
            # error and continue to next eval.
            urs = architect.generate_urs(entry["input"])

            statement   = urs.get("Requirement_Statement", "")
            rationale   = urs.get("Regulatory_Rationale", "")
            criticality = urs.get("Criticality")
            acceptance  = urs.get("Acceptance_Criteria", []) or []

            result.output_summary = (
                statement[:160] + "…"
                if len(statement) > 160 else statement
            )

            # Run checks against expectations
            exp = entry["expected"]
            result.checks.append(_check_keywords(
                statement, exp.get("must_contain_keywords", []),
            ))
            result.checks.append(_check_frameworks(
                rationale, exp.get("must_cite_frameworks", []),
            ))
            result.checks.append(_check_criticality(
                criticality, exp.get("expected_criticality"),
            ))
            result.checks.append(_check_acceptance_criteria_count(
                len(acceptance),
                exp.get("acceptance_criteria_min", 0),
            ))

            passed = sum(1 for c in result.checks if c.passed)
            total = len(result.checks)
            result.score  = passed / total if total else 0.0
            result.passed = (passed == total)

        except Exception as e:
            result.error  = f"{type(e).__name__}: {e}"
            result.passed = False
            result.score  = 0.0

        results.append(result)

    pass_count = sum(1 for r in results if r.passed)
    agg_rate = pass_count / len(results) if results else 0.0

    return EvalRun(
        agent_name=agent_name,
        schema_version=EVAL_SCHEMA_VERSION,
        ran_at=datetime.now(timezone.utc).isoformat(),
        eval_count=len(results),
        results=results,
        aggregate_pass_rate=agg_rate,
    )


def summarise_eval_run(run: EvalRun) -> str:
    """
    Format an EvalRun as a human-readable summary block suitable for
    CLI output and Logic Archive narratives.

    :requirement: URS-38.3 - Human-readable eval run summary.
    """
    lines = [
        "════════════════════════════════════════════════════════",
        f"  EVOLV Trusted Evals — {run.agent_name}",
        f"  Schema v{run.schema_version} · Ran {run.ran_at}",
        "════════════════════════════════════════════════════════",
        "",
        f"  Aggregate pass rate: "
        f"{run.aggregate_pass_rate * 100:.1f}% "
        f"({sum(1 for r in run.results if r.passed)}/{run.eval_count})",
        "",
        "  Per-eval results:",
        "",
    ]
    for r in run.results:
        flag = "✓ PASS" if r.passed else "✗ FAIL"
        if r.error:
            lines.append(
                f"   {flag}  {r.eval_id}  "
                f"({r.eval_name}) — ERROR: {r.error}"
            )
        else:
            lines.append(
                f"   {flag}  {r.eval_id}  "
                f"({r.eval_name})  "
                f"{r.passed_checks}/{r.total_checks} checks"
            )
            for c in r.checks:
                marker = "✓" if c.passed else "✗"
                lines.append(f"          {marker} {c.name}: {c.detail}")
        lines.append("")
    lines.append(
        "════════════════════════════════════════════════════════",
    )
    return "\n".join(lines)


# ── CLI entrypoint (manual run before prompt changes ship) ──────────

def _cli() -> None:
    """
    Run the standing eval set and print a summary. Intended for
    manual invocation before any RequirementArchitect prompt change
    is committed.

    Usage:
        python -m Agents.agent_evals
        python -m Agents.agent_evals --json   (machine-readable)
    """
    import argparse
    parser = argparse.ArgumentParser(
        prog="evolv-evals",
        description="Run EVOLV Trusted Evals against a specialist function.",
    )
    parser.add_argument(
        "--agent",
        default="RequirementArchitect",
        help="Agent name to eval (default: RequirementArchitect).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON instead of summary text.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Optional path to write JSON report. Use with --json.",
    )
    args = parser.parse_args()

    run = run_evals(agent_name=args.agent)

    if args.json:
        payload = json.dumps(run.to_dict(), indent=2)
        if args.out:
            Path(args.out).write_text(payload, encoding="utf-8")
            print(f"Wrote eval run report to {args.out}")
        else:
            print(payload)
    else:
        print(summarise_eval_run(run))


if __name__ == "__main__":
    _cli()
