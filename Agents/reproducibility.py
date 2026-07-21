"""
reproducibility.py - Output-consistency proof for EVOLV.

Sprint 50 ("EVOLV Validates Itself"). Reproducibility is the
deepest requirement for AI in a validated environment: the same
input must yield the same output, every time, or the tool cannot
be validated. This harness proves it for EVOLV's deterministic
specialist functions and documents - honestly - exactly where
non-determinism is intentional.

Two categories, both stated explicitly for a validation reviewer:

  FORBIDDEN non-determinism (the harness fails if it appears):
    the risk classification, the test steps, the UR/FR content,
    the exclusion verdict, the validated-state score. A GxP
    decision that drifts run-to-run is a defect.

  INTENTIONAL non-determinism (normalised before comparison):
    wall-clock fields only - generated_at, assessed_at,
    assessment_id. These are provenance stamps, not decisions.

Each engine is run K times on a fixed input; the outputs are
normalised (volatile keys stripped recursively) and compared for
byte-identity. This is OQ evidence for EVOLV's own validation
package AND the platform's output-consistency story.

LLM-backed functions (RequirementArchitect draft, VerificationAgent
review) are deliberately OUT of scope here: their variance is
bounded by structured outputs + independent verification + a human
signature gate, not by bit-reproducibility. That control story is
documented separately; this harness covers the deterministic core
that must never drift.

CLI:
    python -m Agents.reproducibility
    python -m Agents.reproducibility --runs 20 --json

:requirement: URS-50.1 - Reproducibility proof for the
              deterministic specialist functions (output
              consistency + OQ evidence).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

# ISO-8601 timestamps may also appear EMBEDDED in reasoning
# narratives (e.g. "assessing 1 UR at 2026-07-21T18:03:53Z").
# A timestamp is provenance wherever it sits, so it is
# normalised in string values too - never the surrounding
# decision text.
_ISO_TS_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?"
    r"(?:[+-]\d{2}:\d{2}|Z)?"
)

# Wall-clock / provenance keys that are ALLOWED to vary run to
# run. Stripped recursively before comparison. Everything else
# (every decision-bearing field) must be identical.
VOLATILE_KEYS = {
    "generated_at",
    "assessed_at",
    "assessment_id",
    "ran_at",
    "timestamp",
    "verified_at",
}


def _strip_volatile(obj: Any) -> Any:
    """Recursively remove volatile provenance keys and normalise
    embedded ISO timestamps so that only decision-bearing content
    is compared."""
    if isinstance(obj, dict):
        return {
            k: _strip_volatile(v)
            for k, v in obj.items()
            if k not in VOLATILE_KEYS
        }
    if isinstance(obj, list):
        return [_strip_volatile(v) for v in obj]
    if isinstance(obj, str):
        return _ISO_TS_RE.sub("<TS>", obj)
    return obj


def _canonical(obj: Any) -> str:
    """Deterministic JSON serialization for comparison."""
    return json.dumps(
        _strip_volatile(obj), sort_keys=True, default=str,
    )


@dataclass
class ReproResult:
    """Reproducibility outcome for one engine."""
    engine: str
    runs: int
    reproducible: bool
    normalised_keys: List[str]
    detail: str
    error: str = ""


@dataclass
class ReproReport:
    """Aggregate reproducibility report."""
    ran_at: str
    results: List[ReproResult] = field(default_factory=list)

    @property
    def all_reproducible(self) -> bool:
        return all(
            r.reproducible for r in self.results
        ) and bool(self.results)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ran_at": self.ran_at,
            "all_reproducible": self.all_reproducible,
            "engine_count": len(self.results),
            "results": [
                {
                    "engine": r.engine,
                    "runs": r.runs,
                    "reproducible": r.reproducible,
                    "normalised_keys": r.normalised_keys,
                    "detail": r.detail,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


def _check(
    engine: str, fn: Callable[[], Any], runs: int,
) -> ReproResult:
    """Run fn `runs` times and assert normalised outputs match."""
    try:
        canon = [_canonical(fn()) for _ in range(runs)]
    except Exception as e:
        return ReproResult(
            engine=engine, runs=runs, reproducible=False,
            normalised_keys=sorted(VOLATILE_KEYS),
            detail="", error=f"{type(e).__name__}: {e}",
        )
    first = canon[0]
    identical = all(c == first for c in canon)
    return ReproResult(
        engine=engine,
        runs=runs,
        reproducible=identical,
        normalised_keys=sorted(VOLATILE_KEYS),
        detail=(
            f"All {runs} runs byte-identical after normalising "
            "provenance timestamps."
            if identical else
            "Decision-bearing output DIFFERED across runs - "
            "this is a determinism defect."
        ),
    )


def run_reproducibility(runs: int = 10) -> ReproReport:
    """Run the reproducibility harness across the deterministic
    specialist functions.

    :param runs: Number of repeated executions per engine.
    :return: ReproReport with per-engine results.
    :requirement: URS-50.1 - Reproducibility proof.
    """
    from Agents.risk_strategist import (
        Detectability,
        assess_change_request,
    )
    from Agents.delta_agent import DeltaAgent
    from Agents.requirement_architect import RequirementArchitect
    from Agents.bounded_autonomy_profile import EXCLUSION_RULES
    from Agents.validated_state_engine import ValidatedStateEngine
    from Agents.eval_suite import (
        _fixture_ur_fr,
        _vse_snapshot,
    )

    report = ReproReport(
        ran_at=datetime.now(timezone.utc).isoformat(),
    )

    # RiskStrategist - pure mapping function.
    report.results.append(_check(
        "RiskStrategist",
        lambda: assess_change_request(
            "high", "emergency", Detectability.MEDIUM,
        ),
        runs,
    ))

    # DeltaAgent - CSA test generation (volatile: generated_at).
    delta = DeltaAgent()
    ur_fr = _fixture_ur_fr("High", 2)
    report.results.append(_check(
        "DeltaAgent",
        lambda: delta.generate_csa_test_from_ur_fr(
            ur_fr, "Informal",
        ),
        runs,
    ))

    # RequirementArchitect.transform_urs_to_ur_fr - deterministic
    # transform, no LLM call.
    architect = RequirementArchitect.__new__(RequirementArchitect)
    urs = {
        "URS_ID": "URS-REPRO-1",
        "Requirement_Statement":
            "The system shall track warehouse temperature.",
        "Criticality": "Medium",
        "Regulatory_Rationale": "Per GAMP 5 (p.42): ...",
        "Reg_Versions_Cited": ["GAMP5_Rev2"],
    }
    report.results.append(_check(
        "RequirementArchitect.transform_urs_to_ur_fr",
        lambda: architect.transform_urs_to_ur_fr(
            urs=urs, role="User", category="General",
            risk_assessment="GxP Indirect",
            implementation_method="Configured",
        ),
        runs,
    ))

    # BAP exclusion screen - pure regex verdict.
    def _bap_screen() -> Dict[str, Any]:
        stmt = "AI drafts test scripts; QA signs each one."
        return {
            "fired": [
                r["id"] for r in EXCLUSION_RULES
                if r["pattern"].search(stmt)
            ],
        }
    report.results.append(_check(
        "BAP Exclusion Screen", _bap_screen, runs,
    ))

    # ValidatedStateEngine - scoring (volatile: assessment_id,
    # assessed_at). days-since-run is integer days, stable across
    # a fast loop.
    engine = ValidatedStateEngine()
    snap = _vse_snapshot(
        bundle=True, days_since_run=2, open_defects=0,
    )
    report.results.append(_check(
        "ValidatedStateEngine",
        lambda: engine.assess(snap, user_id="ReproHarness")
        .to_dict(),
        runs,
    ))

    return report


def summarise_report(report: ReproReport) -> str:
    """Human-readable reproducibility summary.

    :requirement: URS-50.1 - Reproducibility proof.
    """
    lines = [
        "===================================================",
        "  EVOLV Reproducibility Harness - Output Consistency",
        f"  Ran {report.ran_at}",
        "===================================================",
        f"  Overall: "
        f"{'REPRODUCIBLE' if report.all_reproducible else 'DEFECT'}",
        "",
    ]
    for r in report.results:
        flag = "OK  " if r.reproducible else "FAIL"
        lines.append(
            f"  {flag}  {r.engine} ({r.runs} runs)"
        )
        lines.append(
            f"          {r.error or r.detail}"
        )
    lines.append(
        "===================================================",
    )
    lines.append(
        "  Normalised (intentional) provenance keys: "
        + ", ".join(sorted(VOLATILE_KEYS))
    )
    return "\n".join(lines)


def _cli() -> None:
    """CLI entrypoint.

    :requirement: URS-50.1 - Reproducibility proof.
    """
    import argparse
    parser = argparse.ArgumentParser(
        prog="evolv-reproducibility",
        description=(
            "Prove EVOLV's deterministic engines are "
            "byte-reproducible."
        ),
    )
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    report = run_reproducibility(runs=args.runs)
    if args.json or args.out:
        payload = json.dumps(report.to_dict(), indent=2)
        if args.out:
            args.out.write_text(payload, encoding="utf-8")
            print(f"Wrote report to {args.out}")
        else:
            print(payload)
    else:
        print(summarise_report(report))
    raise SystemExit(0 if report.all_reproducible else 1)


if __name__ == "__main__":
    _cli()
