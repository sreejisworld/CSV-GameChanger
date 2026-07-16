"""
evals.py — Trusted Evals API for the EVOLV Dev Portal.

Exposes the Sprint 44/45 deterministic eval suite
(``Agents/eval_suite.py``) over JSON so the React Dev Portal can
run the standing checks on demand and render the scoreboard a
pharma evaluator sees in demos.

Endpoints
---------
- ``GET  /evals/agents`` — registered agents + eval counts.
- ``POST /evals/run``    — run the suite (optionally one agent),
  return the scoreboard + per-eval results.

The run endpoint is deliberately synchronous: the full suite is
deterministic and completes in a few seconds with zero LLM calls.

:requirement: URS-46.1 - Expose Trusted Evals suite via JSON API.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

router = APIRouter(tags=["Trusted Evals"])
_logger = logging.getLogger("evolv.evals")


class EvalRunRequest(BaseModel):
    """POST /evals/run request body."""
    agent: Optional[str] = Field(
        None,
        max_length=60,
        description=(
            "Run a single agent's eval set (e.g. 'DeltaAgent'). "
            "Omit to run every registered deterministic agent."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"agent": None},
                {"agent": "BAPExclusionScreen"},
            ],
        },
    }


@router.get("/evals/agents")
def list_eval_agents() -> Dict[str, Any]:
    """List registered eval agents and their standing eval counts.

    Counts come from the golden-set sizes without executing the
    agents, so this endpoint is cheap enough for page load.

    :requirement: URS-46.1 - Expose Trusted Evals suite via API.
    """
    from Agents.eval_suite import (
        CHANGE_IMPACT_GOLDEN_SET,
        DELTA_AGENT_GOLDEN_SET,
        RISK_STRATEGIST_GOLDEN_SET,
        VALIDATED_STATE_GOLDEN_SET,
    )
    counts = {
        "RiskStrategist":       len(RISK_STRATEGIST_GOLDEN_SET),
        "DeltaAgent":           len(DELTA_AGENT_GOLDEN_SET),
        "ChangeImpactAgent":    len(CHANGE_IMPACT_GOLDEN_SET),
        "ValidatedStateEngine": len(VALIDATED_STATE_GOLDEN_SET),
        "BAPExclusionScreen":   95,   # 55 static + 40 generated
        "IntegrityManager":     6,    # chain-integrity evals
    }
    return {
        "agents": [
            {"name": name, "eval_count": n}
            for name, n in counts.items()
        ],
        "total_evals": sum(counts.values()),
    }


@router.post("/evals/run")
def run_eval_suite(body: EvalRunRequest) -> Dict[str, Any]:
    """Run the deterministic Trusted Evals suite and return the
    scoreboard plus per-eval results for drill-down.

    Emits the standard RECEIVED / COMPLETED / FAILED audit
    triplet. The eval run itself appends chained audit rows (the
    CIA / VSE / IntegrityManager evals invoke real agents), so
    every Dev Portal run leaves inspectable evidence.

    :requirement: URS-46.1 - Expose Trusted Evals suite via API.
    """
    from Agents.eval_suite import AGENT_RUNNERS, run_suite
    from Agents.integrity_manager import log_audit_event

    scope = body.agent or "ALL"
    log_audit_event(
        agent_name="EvalSuite",
        action="EVAL_SUITE_RUN_RECEIVED",
        decision_logic=f"Dev Portal eval run requested: {scope}",
    )
    try:
        if body.agent and body.agent not in AGENT_RUNNERS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"[CSV-060] Unknown agent '{body.agent}'. "
                    f"Known: {sorted(AGENT_RUNNERS)}"
                ),
            )
        runs = run_suite(
            agents=[body.agent] if body.agent else None,
        )
        total = sum(r.eval_count for r in runs)
        passed = sum(
            sum(1 for x in r.results if x.passed) for r in runs
        )
        scoreboard: List[Dict[str, Any]] = [
            {
                "agent_name": r.agent_name,
                "eval_count": r.eval_count,
                "passed": sum(
                    1 for x in r.results if x.passed
                ),
                "pass_rate": r.aggregate_pass_rate,
            }
            for r in runs
        ]
        log_audit_event(
            agent_name="EvalSuite",
            action="EVAL_SUITE_RUN_COMPLETED",
            decision_logic=(
                f"{scope}: {passed}/{total} evals passed "
                f"({(passed / total * 100 if total else 0):.1f}%)"
            ),
        )
        return {
            "total_evals": total,
            "total_passed": passed,
            "all_passed": passed == total,
            "scoreboard": scoreboard,
            "runs": [r.to_dict() for r in runs],
        }
    except HTTPException:
        raise
    except Exception as exc:
        _logger.exception(
            "[CSV-060] Eval suite run failed: %s", exc,
        )
        log_audit_event(
            agent_name="EvalSuite",
            action="EVAL_SUITE_RUN_FAILED",
            decision_logic="Eval suite run raised an error.",
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "[CSV-060] Eval suite run failed. "
                "See server audit log for details."
            ),
        ) from exc
