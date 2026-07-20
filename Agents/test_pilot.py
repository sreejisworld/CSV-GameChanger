"""
test_pilot.py - Sprint 41 Test Pilot Agent.

Runs 100s of deterministic scenarios against the live EVOLV
platform via HTTP, compares actual responses to expected
values, and produces terminal + HTML pass/fail reports.

Zero LLM tokens consumed. Fully reproducible.

Bounded autonomy contract:
  - read_only from EVOLV endpoints (no writes)
  - never modifies audit chain
  - never signs approvals
  - reads its own scenario library, hits the platform, reports

Design principle: EVOLV testing EVOLV, with the same
audit-defensible discipline the rest of the platform ships with.

CLI usage:
    python -m Agents.test_pilot --category exclusion --parallel 10
    python -m Agents.test_pilot --all --out output/test_pilot_reports

:requirement: URS-41.5 - Test Pilot Agent runs scenarios.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# httpx is the async HTTP client. If not installed, we fall back
# to synchronous requests for CLI use.
try:
    import httpx   # type: ignore
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    try:
        import requests   # type: ignore
        HAS_REQUESTS = True
    except ImportError:
        HAS_REQUESTS = False

from Tests.scenarios.bap_scenarios import (   # noqa: E402
    BAPScenario,
    all_bap_scenarios,
    bap_scenarios_by_category,
    COUNTS,
)
from Tests.scenario_factory import (   # noqa: E402
    generate_batch,
)
from Agents.integrity_manager import log_audit_event   # noqa: E402


AGENT_NAME = "TestPilotAgent"
SCHEMA_VERSION = "1.0.0"


# --- Result dataclasses ----------------------------------------

@dataclass
class TestResult:
    """One scenario result."""
    scenario_id:  str
    category:     str
    endpoint:     str
    passed:       bool
    duration_ms:  float
    expected:     Dict[str, Any]
    actual:       Dict[str, Any]
    error:        Optional[str] = None
    tags:         List[str] = field(default_factory=list)


@dataclass
class TestRun:
    """Aggregate report for a full run."""
    run_id:          str
    started_at:      str
    completed_at:    str
    total_duration_s: float
    base_url:        str
    scenarios_count: int
    passed_count:    int
    failed_count:    int
    error_count:     int
    pass_rate:       float
    results:         List[TestResult]
    coverage:        Dict[str, Dict[str, int]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id":          self.run_id,
            "started_at":      self.started_at,
            "completed_at":    self.completed_at,
            "total_duration_s": self.total_duration_s,
            "base_url":        self.base_url,
            "scenarios_count": self.scenarios_count,
            "passed_count":    self.passed_count,
            "failed_count":    self.failed_count,
            "error_count":     self.error_count,
            "pass_rate":       self.pass_rate,
            "results":         [asdict(r) for r in self.results],
            "coverage":        self.coverage,
        }


# --- Response-field extraction helper --------------------------

def _extract(response_json: Any, dotted_path: str) -> Any:
    """Follow a dotted path into nested dicts/lists.

    Examples:
      "would_be_excluded"        -> response["would_be_excluded"]
      "rules_fired.0.rule_id"    -> response["rules_fired"][0]["rule_id"]
      "assurance_argument.q7_fragility_markers.0.assumption"
    """
    if response_json is None:
        return None
    parts = dotted_path.split(".")
    cur: Any = response_json
    for p in parts:
        if cur is None:
            return None
        if p.isdigit():
            idx = int(p)
            if isinstance(cur, list) and 0 <= idx < len(cur):
                cur = cur[idx]
            else:
                return None
        else:
            if isinstance(cur, dict):
                cur = cur.get(p)
            else:
                return None
    return cur


def _compare_expected(
    expected: Dict[str, Any],
    actual_response: Any,
) -> Tuple[bool, Dict[str, Any]]:
    """Check every expected field against the response.

    Returns (passed, diagnostic_dict).
    """
    diagnostic: Dict[str, Any] = {}
    all_passed = True
    for field_path, exp_value in expected.items():
        actual_value = _extract(actual_response, field_path)
        matches = actual_value == exp_value
        diagnostic[field_path] = {
            "expected": exp_value,
            "actual":   actual_value,
            "match":    matches,
        }
        if not matches:
            all_passed = False
    return all_passed, diagnostic


# --- The Test Pilot Agent --------------------------------------

class TestPilotAgent:
    """Async runner for scenario batches.

    :requirement: URS-41.5 - TestPilotAgent core class.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        parallel: int = 10,
        timeout_s: float = 15.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.parallel = parallel
        self.timeout_s = timeout_s

    # -- Public API --------------------------------------------

    async def run_async(
        self,
        scenarios: List[BAPScenario],
        user_id: str = "test-pilot",
    ) -> TestRun:
        """Run scenarios in parallel via async httpx.

        :requirement: URS-41.5 - Async execution.
        """
        if not HAS_HTTPX:
            raise RuntimeError(
                "httpx not installed. Install with: pip install httpx"
            )

        run_id = (
            f"TP-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
        )
        started_at = datetime.now(timezone.utc).isoformat()

        log_audit_event(
            agent_name=AGENT_NAME,
            action="TEST_PILOT_RUN_RECEIVED",
            user_id=user_id,
            decision_logic=(
                f"Run {run_id} - {len(scenarios)} scenario(s) "
                f"against {self.base_url}"
            ),
        )

        t0 = time.time()
        semaphore = asyncio.Semaphore(self.parallel)

        async with httpx.AsyncClient(
            timeout=self.timeout_s,
        ) as client:
            tasks = [
                self._run_one(client, semaphore, sc)
                for sc in scenarios
            ]
            results: List[TestResult] = await asyncio.gather(*tasks)

        duration = time.time() - t0
        completed_at = datetime.now(timezone.utc).isoformat()

        passed = sum(1 for r in results if r.passed and not r.error)
        errored = sum(1 for r in results if r.error)
        failed = len(results) - passed - errored
        pass_rate = (
            (passed / len(results) * 100) if results else 0.0
        )

        coverage = self._compute_coverage(results)

        run = TestRun(
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_s=round(duration, 3),
            base_url=self.base_url,
            scenarios_count=len(results),
            passed_count=passed,
            failed_count=failed,
            error_count=errored,
            pass_rate=round(pass_rate, 2),
            results=results,
            coverage=coverage,
        )

        log_audit_event(
            agent_name=AGENT_NAME,
            action="TEST_PILOT_RUN_COMPLETED",
            user_id=user_id,
            decision_logic=(
                f"Run {run_id} finished: "
                f"{passed}/{len(results)} passed "
                f"({pass_rate:.1f}%), {failed} failed, "
                f"{errored} errored"
            ),
        )
        return run

    def run_sync(
        self,
        scenarios: List[BAPScenario],
        user_id: str = "test-pilot",
    ) -> TestRun:
        """Sync wrapper around run_async - convenient for CLI.

        :requirement: URS-47.5 - Test Pilot execution and reporting.
        """
        return asyncio.run(self.run_async(scenarios, user_id))

    # -- Internals ---------------------------------------------

    async def _run_one(
        self,
        client: "httpx.AsyncClient",
        semaphore: asyncio.Semaphore,
        scenario: BAPScenario,
    ) -> TestResult:
        async with semaphore:
            t0 = time.time()
            try:
                url = self.base_url + scenario.endpoint
                # Detect method by input_body presence
                r = await client.post(url, json=scenario.input_body)
                duration_ms = (time.time() - t0) * 1000
                if r.status_code >= 400:
                    return TestResult(
                        scenario_id=scenario.scenario_id,
                        category=scenario.category,
                        endpoint=scenario.endpoint,
                        passed=False,
                        duration_ms=round(duration_ms, 2),
                        expected=scenario.expected,
                        actual={
                            "http_status": r.status_code,
                            "body":        r.text[:400],
                        },
                        error=(
                            f"HTTP {r.status_code} from {url}"
                        ),
                        tags=scenario.tags,
                    )
                body = r.json()
                passed, diag = _compare_expected(
                    scenario.expected, body,
                )
                return TestResult(
                    scenario_id=scenario.scenario_id,
                    category=scenario.category,
                    endpoint=scenario.endpoint,
                    passed=passed,
                    duration_ms=round(duration_ms, 2),
                    expected=scenario.expected,
                    actual=diag,
                    error=None,
                    tags=scenario.tags,
                )
            except (asyncio.TimeoutError, Exception) as e:
                duration_ms = (time.time() - t0) * 1000
                return TestResult(
                    scenario_id=scenario.scenario_id,
                    category=scenario.category,
                    endpoint=scenario.endpoint,
                    passed=False,
                    duration_ms=round(duration_ms, 2),
                    expected=scenario.expected,
                    actual={},
                    error=f"{type(e).__name__}: {e}",
                    tags=scenario.tags,
                )

    @staticmethod
    def _compute_coverage(
        results: List[TestResult],
    ) -> Dict[str, Dict[str, int]]:
        """Per-category and per-endpoint counts."""
        by_cat: Dict[str, Dict[str, int]] = {}
        by_endpt: Dict[str, Dict[str, int]] = {}
        for r in results:
            cat = r.category
            if cat not in by_cat:
                by_cat[cat] = {"passed": 0, "failed": 0, "errored": 0}
            if r.error:
                by_cat[cat]["errored"] += 1
            elif r.passed:
                by_cat[cat]["passed"] += 1
            else:
                by_cat[cat]["failed"] += 1

            ep = r.endpoint
            if ep not in by_endpt:
                by_endpt[ep] = {"passed": 0, "failed": 0, "errored": 0}
            if r.error:
                by_endpt[ep]["errored"] += 1
            elif r.passed:
                by_endpt[ep]["passed"] += 1
            else:
                by_endpt[ep]["failed"] += 1
        return {
            "by_category": by_cat,
            "by_endpoint": by_endpt,
        }


# --- Terminal report -------------------------------------------

def _c(text: str, color: str) -> str:
    """Minimal ANSI colour wrapper. Falls back to plain text on
    Windows terminals that don't support colour."""
    codes = {
        "green":   "\033[92m",
        "red":     "\033[91m",
        "yellow":  "\033[93m",
        "blue":    "\033[94m",
        "gray":    "\033[90m",
        "bold":    "\033[1m",
        "reset":   "\033[0m",
    }
    return f"{codes.get(color, '')}{text}{codes['reset']}"


def print_terminal_report(run: TestRun) -> None:
    """Print a coloured pass/fail summary to stdout.

    :requirement: URS-41.6 - Terminal report.
    """
    print()
    print("-" * 72)
    print(_c("  TEST PILOT REPORT", "bold"))
    print("-" * 72)
    print(f"  Run ID     : {run.run_id}")
    print(f"  Base URL   : {run.base_url}")
    print(f"  Started    : {run.started_at}")
    print(f"  Duration   : {run.total_duration_s} sec")
    print(f"  Scenarios  : {run.scenarios_count}")
    print()

    pass_color = (
        "green" if run.pass_rate >= 90 else
        "yellow" if run.pass_rate >= 70 else "red"
    )
    print("  " + _c(
        f"PASS RATE: {run.pass_rate}%   ", pass_color,
    ) + _c(
        f"({run.passed_count} passed / {run.failed_count} failed"
        f" / {run.error_count} errored)", "gray",
    ))
    print()

    print(_c("  Coverage by category:", "bold"))
    for cat, counts in run.coverage.get("by_category", {}).items():
        total = counts["passed"] + counts["failed"] + counts["errored"]
        line = (
            f"    {cat:14s} "
            f"{_c(str(counts['passed']) + ' pass', 'green')}, "
            f"{_c(str(counts['failed']) + ' fail', 'red' if counts['failed'] else 'gray')}, "
            f"{_c(str(counts['errored']) + ' err', 'yellow' if counts['errored'] else 'gray')} "
            f"({total} total)"
        )
        print(line)

    # First 5 failures
    failures = [
        r for r in run.results if not r.passed and not r.error
    ]
    if failures:
        print()
        print(_c(
            f"  First {min(5, len(failures))} failure(s):", "bold",
        ))
        for r in failures[:5]:
            print(_c(f"    [X] {r.scenario_id}", "red"))
            for path, diag in r.actual.items():
                if not diag.get("match"):
                    print(_c(
                        f"        {path}: "
                        f"expected={diag['expected']!r}, "
                        f"actual={diag['actual']!r}",
                        "gray",
                    ))

    errors = [r for r in run.results if r.error]
    if errors:
        print()
        print(_c(f"  {len(errors)} error(s):", "yellow"))
        for r in errors[:5]:
            print(_c(f"    ! {r.scenario_id} - {r.error}", "yellow"))

    print()
    print("-" * 72)


# --- HTML report -----------------------------------------------

def render_html_report(run: TestRun) -> str:
    """Render the run as a self-contained HTML dashboard.

    :requirement: URS-41.7 - HTML scorecard report.
    """
    esc = lambda s: (str(s) if s is not None else "").replace(
        "&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    pass_color = (
        "#22c55e" if run.pass_rate >= 90 else
        "#eab308" if run.pass_rate >= 70 else "#ef4444"
    )

    rows_html = []
    for r in run.results:
        status_icon = "[OK]" if r.passed and not r.error else (
            "!" if r.error else "[X]"
        )
        status_class = (
            "row-pass" if r.passed and not r.error
            else "row-error" if r.error else "row-fail"
        )
        # Diagnostic column
        diag_html = ""
        if r.error:
            diag_html = (
                f"<code>{esc(r.error[:200])}</code>"
            )
        elif not r.passed:
            fails = []
            for p, d in (r.actual or {}).items():
                if not d.get("match"):
                    fails.append(
                        f"<div><code>{esc(p)}</code>: "
                        f"expected <b>{esc(d.get('expected'))}</b>, "
                        f"got <b>{esc(d.get('actual'))}</b></div>"
                    )
            diag_html = "".join(fails)
        tags_html = " ".join(
            f"<span class='tag'>{esc(t)}</span>" for t in r.tags[:4]
        )
        rows_html.append(
            f"<tr class='{status_class}'>"
            f"<td class='status'>{status_icon}</td>"
            f"<td class='sid'><code>{esc(r.scenario_id)}</code></td>"
            f"<td>{esc(r.category)}</td>"
            f"<td><code>{esc(r.endpoint)}</code></td>"
            f"<td>{r.duration_ms:.0f} ms</td>"
            f"<td>{diag_html}</td>"
            f"<td>{tags_html}</td>"
            f"</tr>"
        )

    coverage_html = ""
    for cat, c in run.coverage.get("by_category", {}).items():
        tot = c["passed"] + c["failed"] + c["errored"]
        rate = (c["passed"] / tot * 100) if tot else 0
        coverage_html += (
            f"<div class='cov-row'>"
            f"<div class='cov-label'>{esc(cat)}</div>"
            f"<div class='cov-bar'>"
            f"<div class='cov-fill' style='width:{rate:.1f}%'>"
            f"</div></div>"
            f"<div class='cov-count'>"
            f"{c['passed']} / {tot}</div></div>"
        )

    html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>Test Pilot Report - {esc(run.run_id)}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font: 14px/1.5 -apple-system, "Segoe UI", Arial, sans-serif;
    color: #2A2825; background: #FAFAF7; margin: 0; padding: 24px;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{ font-size: 28px; margin: 0 0 6px; letter-spacing: -0.5px; }}
  .subtitle {{ color: #6B6862; font-size: 13px; margin-bottom: 24px; }}
  .kpi-row {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 16px; margin-bottom: 24px;
  }}
  .kpi {{
    background: white; border: 1px solid #EAE7E1;
    border-radius: 10px; padding: 18px 20px;
  }}
  .kpi-label {{
    font-size: 10px; letter-spacing: 1.2px; color: #6B6862;
    text-transform: uppercase; font-weight: 700;
    margin-bottom: 6px;
  }}
  .kpi-value {{ font-size: 28px; font-weight: 800; letter-spacing: -0.8px; }}
  .kpi.big-pass .kpi-value {{ color: {pass_color}; }}
  .section {{
    background: white; border: 1px solid #EAE7E1;
    border-radius: 10px; padding: 20px; margin-bottom: 20px;
  }}
  h2 {{
    font-size: 15px; margin: 0 0 14px; font-weight: 800;
    letter-spacing: -0.2px;
  }}
  .cov-row {{
    display: grid; grid-template-columns: 130px 1fr 100px;
    align-items: center; gap: 12px; padding: 8px 0;
    border-bottom: 1px solid #F0EDE7;
  }}
  .cov-row:last-child {{ border-bottom: 0; }}
  .cov-label {{ font-weight: 700; font-size: 13px; text-transform: capitalize; }}
  .cov-bar {{
    background: #F0EDE7; height: 10px; border-radius: 5px;
    overflow: hidden;
  }}
  .cov-fill {{
    background: linear-gradient(90deg, #007FFF, #32CD32);
    height: 100%; transition: width 0.3s;
  }}
  .cov-count {{ text-align: right; font-family: monospace; font-size: 12px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th {{
    text-align: left; padding: 10px 8px; background: #2A2825;
    color: white; font-weight: 700; font-size: 10px;
    letter-spacing: 0.8px; text-transform: uppercase;
  }}
  td {{
    padding: 8px; border-bottom: 1px solid #F0EDE7;
    vertical-align: top;
  }}
  tr.row-pass {{ background: #F0FDF4; }}
  tr.row-fail {{ background: #FEF2F2; }}
  tr.row-error {{ background: #FFFBEB; }}
  td.status {{ font-size: 18px; font-weight: 800; text-align: center; width: 30px; }}
  tr.row-pass td.status {{ color: #16A34A; }}
  tr.row-fail td.status {{ color: #DC2626; }}
  tr.row-error td.status {{ color: #D97706; }}
  code {{
    background: #F0EDE7; padding: 1px 5px; border-radius: 3px;
    font-size: 11px;
  }}
  .tag {{
    display: inline-block; font-size: 9px; padding: 2px 6px;
    background: #EAE7E1; border-radius: 3px; margin-right: 2px;
    letter-spacing: 0.5px; text-transform: uppercase; font-weight: 700;
    color: #6B6862;
  }}
  .sid {{ font-family: monospace; }}
</style></head>
<body>
<div class="container">
  <h1>Test Pilot Report</h1>
  <div class="subtitle">
    Run <code>{esc(run.run_id)}</code> ·
    against <code>{esc(run.base_url)}</code> ·
    started {esc(run.started_at)}
  </div>

  <div class="kpi-row">
    <div class="kpi big-pass">
      <div class="kpi-label">Pass rate</div>
      <div class="kpi-value">{run.pass_rate}%</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Scenarios</div>
      <div class="kpi-value">{run.scenarios_count}</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Duration</div>
      <div class="kpi-value">{run.total_duration_s}s</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Failures / Errors</div>
      <div class="kpi-value" style="color:#DC2626">
        {run.failed_count} / {run.error_count}
      </div>
    </div>
  </div>

  <div class="section">
    <h2>Coverage by category</h2>
    {coverage_html}
  </div>

  <div class="section">
    <h2>Every scenario ({run.scenarios_count})</h2>
    <table>
      <thead>
        <tr>
          <th></th><th>Scenario</th><th>Category</th>
          <th>Endpoint</th><th>Time</th>
          <th>Result / Diagnostic</th><th>Tags</th>
        </tr>
      </thead>
      <tbody>
        {"".join(rows_html)}
      </tbody>
    </table>
  </div>
</div>
</body></html>"""
    return html


def save_html_report(
    run: TestRun,
    out_dir: str = "output/test_pilot_reports",
) -> Path:
    """Write the HTML report to disk. Returns the path.

    :requirement: URS-47.5 - Test Pilot execution and reporting.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    fname = f"{run.run_id}.html"
    path = Path(out_dir) / fname
    path.write_text(render_html_report(run), encoding="utf-8")
    return path


def save_json_report(
    run: TestRun,
    out_dir: str = "output/test_pilot_reports",
) -> Path:
    """Write the JSON report to disk. Returns the path.

    :requirement: URS-47.5 - Test Pilot execution and reporting.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    fname = f"{run.run_id}.json"
    path = Path(out_dir) / fname
    path.write_text(
        json.dumps(run.to_dict(), indent=2, default=str),
        encoding="utf-8",
    )
    return path


# --- CLI -------------------------------------------------------

def _cli() -> None:
    """Command-line entry point.

    Usage:
        python -m Agents.test_pilot --category exclusion
        python -m Agents.test_pilot --all --parallel 20
        python -m Agents.test_pilot --generated exclusion --count 100
    """
    parser = argparse.ArgumentParser(
        description="EVOLV Test Pilot Agent - "
                    "runs deterministic scenarios",
    )
    parser.add_argument(
        "--category",
        choices=["exclusion", "safe", "tier", "adversarial"],
        help="Run pre-built scenarios in this category",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run all pre-built scenarios",
    )
    parser.add_argument(
        "--generated",
        choices=["exclusion", "safe", "adversarial-mix"],
        help="Generate N variants and run them",
    )
    parser.add_argument(
        "--count", type=int, default=20,
        help="Number of generated scenarios (for --generated)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Seed for deterministic generation",
    )
    parser.add_argument(
        "--parallel", type=int, default=10,
        help="Max parallel requests",
    )
    parser.add_argument(
        "--base-url", default="http://localhost:8000",
        help="EVOLV API base URL",
    )
    parser.add_argument(
        "--out", default="output/test_pilot_reports",
        help="Directory for HTML + JSON reports",
    )
    parser.add_argument(
        "--user-id", default="test-pilot",
        help="User ID for audit trail",
    )
    args = parser.parse_args()

    if not (args.category or args.all or args.generated):
        parser.error(
            "Provide one of --category, --all, or --generated"
        )

    if args.all:
        scenarios = all_bap_scenarios()
    elif args.category:
        scenarios = bap_scenarios_by_category(args.category)
    else:
        scenarios = generate_batch(
            args.generated, n=args.count, seed=args.seed,
        )

    print(_c(
        f"Running {len(scenarios)} scenario(s) against "
        f"{args.base_url} (parallel={args.parallel})...",
        "blue",
    ))

    agent = TestPilotAgent(
        base_url=args.base_url,
        parallel=args.parallel,
    )
    run = agent.run_sync(scenarios, user_id=args.user_id)
    print_terminal_report(run)
    html_path = save_html_report(run, out_dir=args.out)
    json_path = save_json_report(run, out_dir=args.out)
    print(_c(f"  HTML report: {html_path}", "blue"))
    print(_c(f"  JSON report: {json_path}", "blue"))
    print()
    # Exit non-zero if any failed (CI-friendly)
    if run.failed_count > 0 or run.error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    _cli()
