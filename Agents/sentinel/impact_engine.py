"""
EVOLV Sentinel — Impact Engine
================================
Parses a git diff, cross-references the Sentinel Traceability Graph, and
produces a ranked list of At-Risk requirements together with the specific
IQ/OQ/PQ/UAT test scripts that must be re-executed.

Impact Score Formula
--------------------
    Score = Criticality × Scope

    Criticality  : integer pulled from the requirement node in the graph
                   (High=3, Medium=2, Low=1).

    Scope        : float in [0.0, 1.0] derived from the diff for the
                   specific module:
                       scope = 0.6 × line_factor + 0.4 × function_factor

                   line_factor     = min(1.0, changed_lines / LINE_CAP)
                   function_factor = changed_fns / max(1, total_fns_in_module)

    Score range  : 0.0 – 3.0
    Risk bands   :
        CRITICAL  : score > 2.4
        HIGH      : score > 1.8
        MEDIUM    : score > 1.0
        LOW       : score ≤ 1.0

Usage
-----
    from Agents.sentinel.impact_engine import ImpactEngine

    engine = ImpactEngine.from_file("Agents/sentinel/traceability_sample.json")
    report = engine.analyze(diff_text)
    engine.print_report(report)

:requirement: EVOLV Sentinel — Traceability Graph Impact Analysis
"""
from __future__ import annotations

import json
import re
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Lines-changed ceiling for scope normalisation.
# A diff touching ≥ LINE_CAP lines in a single module is treated as
# full-scope (scope = 1.0 on the line-factor axis).
LINE_CAP: int = 80

# Score thresholds for human-readable risk bands.
SCORE_BANDS: List[Tuple[float, str]] = [
    (2.4, "CRITICAL"),
    (1.8, "HIGH"),
    (1.0, "MEDIUM"),
    (0.0, "LOW"),
]

# Weight split between line-count and function-coverage signals.
LINE_WEIGHT: float = 0.6
FUNCTION_WEIGHT: float = 0.4


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DiffModule:
    """
    Parsed representation of one file's changes extracted from a git diff.

    :requirement: EVOLV Sentinel — diff parsing step
    """
    file_path: str
    lines_added: int
    lines_removed: int
    modified_functions: List[str] = field(default_factory=list)

    @property
    def lines_changed(self) -> int:
        """Total lines touched (additions + deletions)."""
        return self.lines_added + self.lines_removed


@dataclass
class AtRiskRequirement:
    """
    A requirement whose implementing code was modified, along with the
    computed Impact Score and the test scripts that must be re-executed.

    :requirement: EVOLV Sentinel — impact scoring output
    """
    req_id: str
    title: str
    risk_level: str
    criticality_score: int
    gxp_category: str
    regulatory_reference: str
    scope_of_change: float
    impact_score: float
    risk_band: str
    changed_module_ids: List[str]
    changed_functions: List[str]
    test_scripts_required: List[Dict[str, str]]
    change_impact_types: List[str]


@dataclass
class ImpactReport:
    """
    Full output of a single Impact Engine run.

    :requirement: EVOLV Sentinel — structured report output
    """
    diff_hash: str
    analyzed_at: str
    graph_id: str
    modified_modules: List[DiffModule]
    at_risk_requirements: List[AtRiskRequirement]
    test_scripts_to_execute: List[Dict[str, str]]
    summary: Dict[str, int]


# ---------------------------------------------------------------------------
# Diff Parser
# ---------------------------------------------------------------------------

class DiffParser:
    """
    Parses a raw ``git diff`` string into a list of :class:`DiffModule`
    objects, one per changed file.

    Extracts:
    - File path (from ``diff --git a/... b/...`` header lines)
    - Line counts (``+`` / ``-`` lines in hunks, excluding ``+++`` / ``---``)
    - Modified Python function names (from hunk context headers and ``+def``
      lines inside the diff body)

    :requirement: EVOLV Sentinel — diff parsing step
    """

    # Matches: diff --git a/Agents/foo.py b/Agents/foo.py
    _FILE_HEADER = re.compile(r"^diff --git a/(.+?) b/(.+?)$")

    # Matches: @@ -10,7 +12,9 @@ def some_function(
    # The optional trailing text after @@ is the enclosing function context.
    _HUNK_HEADER = re.compile(r"^@@ .+? @@(?:\s+(.+))?$")

    # Matches Python function/method definitions in diff body lines.
    # Captures both added (+def) and removed (-def) lines, plus context
    # lines that happen to be function definitions.
    _FUNCTION_DEF = re.compile(r"^[+\- ]?\s*def\s+(\w+)\s*\(")

    def parse(self, diff_text: str) -> List[DiffModule]:
        """
        Parse a complete git diff string.

        :param diff_text: Raw output of ``git diff`` or ``git diff HEAD~1``.
        :return: List of DiffModule, one per changed file.
        :requirement: EVOLV Sentinel — diff parsing
        """
        modules: List[DiffModule] = []
        current: Optional[DiffModule] = None
        fn_set: set = set()

        for line in diff_text.splitlines():
            # --- New file boundary ---
            file_match = self._FILE_HEADER.match(line)
            if file_match:
                if current is not None:
                    current.modified_functions = sorted(fn_set)
                    modules.append(current)
                current = DiffModule(
                    file_path=file_match.group(2),
                    lines_added=0,
                    lines_removed=0,
                )
                fn_set = set()
                continue

            if current is None:
                continue

            # --- Hunk header: extract enclosing function context ---
            hunk_match = self._HUNK_HEADER.match(line)
            if hunk_match and hunk_match.group(1):
                ctx = hunk_match.group(1).strip()
                fn_ctx = self._FUNCTION_DEF.match(ctx)
                if fn_ctx:
                    fn_set.add(fn_ctx.group(1))
                continue

            # --- Skip file-level +++ / --- markers ---
            if line.startswith("+++") or line.startswith("---"):
                continue

            # --- Count added / removed lines ---
            if line.startswith("+"):
                current.lines_added += 1
                fn_def = self._FUNCTION_DEF.match(line)
                if fn_def:
                    fn_set.add(fn_def.group(1))

            elif line.startswith("-"):
                current.lines_removed += 1
                fn_def = self._FUNCTION_DEF.match(line)
                if fn_def:
                    fn_set.add(fn_def.group(1))

        # Flush last module
        if current is not None:
            current.modified_functions = sorted(fn_set)
            modules.append(current)

        return modules


# ---------------------------------------------------------------------------
# Impact Engine
# ---------------------------------------------------------------------------

class ImpactEngine:
    """
    Cross-references parsed diff modules against the Sentinel Traceability
    Graph to produce a scored, ranked list of at-risk requirements and the
    test scripts that must be re-executed.

    :requirement: EVOLV Sentinel — impact scoring engine
    """

    def __init__(self, graph: Dict) -> None:
        """
        Initialise from an already-parsed traceability graph dict.

        :param graph: Parsed JSON object conforming to traceability_schema.json.
        """
        self._graph = graph
        self._req_index: Dict[str, Dict] = {
            r["req_id"]: r for r in graph.get("requirements", [])
        }
        self._module_index: Dict[str, Dict] = {
            m["module_id"]: m for m in graph.get("code_modules", [])
        }
        self._script_index: Dict[str, Dict] = {
            s["script_id"]: s for s in graph.get("test_scripts", [])
        }
        self._links: List[Dict] = graph.get("traceability_links", [])
        self._parser = DiffParser()

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: str | Path) -> "ImpactEngine":
        """
        Load a traceability graph from a JSON file on disk.

        :param path: Path to the populated traceability graph JSON.
        :return: Configured ImpactEngine instance.
        :requirement: EVOLV Sentinel — graph loading
        """
        with open(path, "r", encoding="utf-8") as fh:
            graph = json.load(fh)
        return cls(graph)

    @classmethod
    def from_json(cls, json_str: str) -> "ImpactEngine":
        """
        Load a traceability graph from a raw JSON string.

        :param json_str: Serialised traceability graph.
        :return: Configured ImpactEngine instance.
        """
        return cls(json.loads(json_str))

    # ------------------------------------------------------------------
    # Scope calculation
    # ------------------------------------------------------------------

    def _compute_scope(
        self,
        diff_module: DiffModule,
        graph_module: Dict,
    ) -> float:
        """
        Calculate Scope of Change ∈ [0.0, 1.0] for a single modified module.

        Formula:
            scope = LINE_WEIGHT × line_factor + FUNCTION_WEIGHT × function_factor

            line_factor     = min(1.0, lines_changed / LINE_CAP)
            function_factor = |modified_fns ∩ tracked_fns| / max(1, |tracked_fns|)

        :param diff_module:   Parsed diff data for the file.
        :param graph_module:  Matching code_module node from the graph.
        :return: Scope float in [0.0, 1.0].
        :requirement: EVOLV Sentinel — scope calculation
        """
        # Line factor — normalised to LINE_CAP ceiling
        line_factor = min(1.0, diff_module.lines_changed / LINE_CAP)

        # Function factor — intersection of diff-detected fns with tracked fns
        tracked_fns = {f["function_name"] for f in graph_module.get("functions", [])}
        changed_fns = set(diff_module.modified_functions)
        if tracked_fns:
            overlap = changed_fns & tracked_fns
            fn_factor = len(overlap) / len(tracked_fns)
        else:
            # No tracked functions listed — treat whole module as implicated
            fn_factor = 1.0

        scope = (LINE_WEIGHT * line_factor) + (FUNCTION_WEIGHT * fn_factor)
        return round(min(1.0, scope), 4)

    # ------------------------------------------------------------------
    # Risk band
    # ------------------------------------------------------------------

    @staticmethod
    def _score_to_band(score: float) -> str:
        """
        Map a numeric Impact Score to a human-readable risk band.

        :param score: Impact Score in [0.0, 3.0].
        :return: One of CRITICAL / HIGH / MEDIUM / LOW.
        :requirement: EVOLV Sentinel — risk band classification
        """
        for threshold, band in SCORE_BANDS:
            if score > threshold:
                return band
        return "LOW"

    # ------------------------------------------------------------------
    # Core analysis
    # ------------------------------------------------------------------

    def analyze(self, diff_text: str) -> ImpactReport:
        """
        Run the full impact analysis pipeline on a git diff.

        Steps:
        1. Parse the diff into DiffModule objects.
        2. Match each DiffModule to graph code_modules by file_path.
        3. For each matching module, resolve traceability_links.
        4. For each linked requirement, compute Scope and Impact Score.
        5. Deduplicate requirements (keeping highest score if linked from
           multiple changed modules).
        6. Collect all unique test scripts from impacted links.
        7. Sort requirements by Impact Score descending.

        :param diff_text: Raw git diff string.
        :return: Fully populated ImpactReport.
        :requirement: EVOLV Sentinel — end-to-end impact pipeline
        """
        diff_hash = hashlib.sha256(diff_text.encode()).hexdigest()[:16]
        diff_modules = self._parser.parse(diff_text)

        # Map file_path → DiffModule for fast lookup
        diff_by_path: Dict[str, DiffModule] = {
            m.file_path: m for m in diff_modules
        }

        # Accumulate: req_id → best AtRiskRequirement (highest score wins)
        req_map: Dict[str, AtRiskRequirement] = {}

        # Accumulate all test scripts that need re-execution
        scripts_needed: Dict[str, Dict[str, str]] = {}

        for link in self._links:
            module_id = link["module_id"]
            req_id = link["req_id"]

            graph_module = self._module_index.get(module_id)
            if graph_module is None:
                continue

            diff_mod = diff_by_path.get(graph_module["file_path"])
            if diff_mod is None:
                # This module was not changed — skip
                continue

            req = self._req_index.get(req_id)
            if req is None:
                continue

            # Resolve which tracked functions actually changed
            tracked_fns = {
                f["function_name"] for f in graph_module.get("functions", [])
            }
            changed_and_tracked = [
                fn for fn in diff_mod.modified_functions
                if fn in tracked_fns
            ] or diff_mod.modified_functions  # fall back if no fn names parsed

            # Effective criticality — honour per-function override when a
            # specifically high-risk function was changed
            criticality = req["criticality_score"]
            for fn in graph_module.get("functions", []):
                if (
                    fn["function_name"] in set(diff_mod.modified_functions)
                    and fn.get("criticality_override")
                ):
                    override_map = {"High": 3, "Medium": 2, "Low": 1}
                    override_val = override_map.get(
                        fn["criticality_override"], criticality
                    )
                    criticality = max(criticality, override_val)

            scope = self._compute_scope(diff_mod, graph_module)
            score = round(criticality * scope, 4)
            band = self._score_to_band(score)

            # Collect test scripts for this link
            link_scripts = []
            for sid in link.get("test_script_ids", []):
                script = self._script_index.get(sid)
                if script:
                    link_scripts.append({
                        "script_id": sid,
                        "phase": script.get("phase", ""),
                        "title": script.get("title", ""),
                        "execution_priority": script.get(
                            "execution_priority", ""
                        ),
                        "automation_status": script.get(
                            "automation_status", "Manual"
                        ),
                    })
                    scripts_needed[sid] = link_scripts[-1]

            # Merge into req_map: keep the highest score per requirement
            if req_id not in req_map or score > req_map[req_id].impact_score:
                req_map[req_id] = AtRiskRequirement(
                    req_id=req_id,
                    title=req.get("title", ""),
                    risk_level=req.get("risk_level", ""),
                    criticality_score=criticality,
                    gxp_category=req.get("gxp_category", ""),
                    regulatory_reference=req.get("regulatory_reference", ""),
                    scope_of_change=scope,
                    impact_score=score,
                    risk_band=band,
                    changed_module_ids=[module_id],
                    changed_functions=changed_and_tracked,
                    test_scripts_required=link_scripts,
                    change_impact_types=[link.get("change_impact_type", "")],
                )
            else:
                # Merge additional module / function / script info
                existing = req_map[req_id]
                if module_id not in existing.changed_module_ids:
                    existing.changed_module_ids.append(module_id)
                for fn in changed_and_tracked:
                    if fn not in existing.changed_functions:
                        existing.changed_functions.append(fn)
                for s in link_scripts:
                    if not any(
                        x["script_id"] == s["script_id"]
                        for x in existing.test_scripts_required
                    ):
                        existing.test_scripts_required.append(s)
                impact_type = link.get("change_impact_type", "")
                if impact_type not in existing.change_impact_types:
                    existing.change_impact_types.append(impact_type)

        # Sort requirements: highest impact score first, then alpha by req_id
        at_risk = sorted(
            req_map.values(),
            key=lambda r: (-r.impact_score, r.req_id),
        )

        # Sort test scripts by execution priority (Critical first)
        priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        all_scripts = sorted(
            scripts_needed.values(),
            key=lambda s: priority_order.get(s.get("execution_priority", "Low"), 3),
        )

        # Build summary counts
        band_counts: Dict[str, int] = {
            "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0
        }
        for r in at_risk:
            band_counts[r.risk_band] += 1

        return ImpactReport(
            diff_hash=diff_hash,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            graph_id=self._graph.get("graph_id", ""),
            modified_modules=diff_modules,
            at_risk_requirements=at_risk,
            test_scripts_to_execute=all_scripts,
            summary={
                "total_files_changed": len(diff_modules),
                "at_risk_requirements": len(at_risk),
                "test_scripts_required": len(all_scripts),
                **band_counts,
            },
        )

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def print_report(report: ImpactReport) -> None:
        """
        Print a human-readable impact report to stdout.

        :param report: ImpactReport produced by :meth:`analyze`.
        :requirement: EVOLV Sentinel — report output
        """
        sep = "=" * 72
        thin = "-" * 72

        print(f"\n{sep}")
        print(f"  EVOLV SENTINEL — IMPACT ANALYSIS REPORT")
        print(f"  Graph   : {report.graph_id}")
        print(f"  Diff    : {report.diff_hash}")
        print(f"  Run at  : {report.analyzed_at}")
        print(sep)

        s = report.summary
        print(
            f"\n  Files changed          : {s['total_files_changed']}"
            f"\n  At-risk requirements   : {s['at_risk_requirements']}"
            f"\n  Test scripts required  : {s['test_scripts_required']}"
            f"\n  Risk breakdown         : CRITICAL={s['CRITICAL']}  "
            f"HIGH={s['HIGH']}  MEDIUM={s['MEDIUM']}  LOW={s['LOW']}"
        )

        print(f"\n{thin}")
        print("  MODIFIED FILES")
        print(thin)
        for mod in report.modified_modules:
            fns = ", ".join(mod.modified_functions) or "(no fn names parsed)"
            print(
                f"  {mod.file_path}"
                f"\n    +{mod.lines_added} / -{mod.lines_removed} lines"
                f"  |  Functions: {fns}"
            )

        print(f"\n{sep}")
        print("  AT-RISK REQUIREMENTS  (sorted by Impact Score desc)")
        print(sep)
        for i, r in enumerate(report.at_risk_requirements, 1):
            print(
                f"\n  [{i}] {r.req_id} — {r.title}"
                f"\n      Risk Level      : {r.risk_level}"
                f"\n      GxP Category    : {r.gxp_category}"
                f"\n      Criticality     : {r.criticality_score}  "
                f"Scope: {r.scope_of_change:.4f}"
                f"\n      Impact Score    : {r.impact_score:.4f}  "
                f"->  {r.risk_band}"
                f"\n      Impact Type     : {', '.join(r.change_impact_types)}"
                f"\n      Changed Modules : {', '.join(r.changed_module_ids)}"
                f"\n      Changed Fns     : "
                f"{', '.join(r.changed_functions) or '(whole module)'}"
                f"\n      Regulatory Ref  : {r.regulatory_reference}"
            )
            print(f"      Test Scripts Required:")
            for s in r.test_scripts_required:
                print(
                    f"        • [{s['execution_priority']:8s}] "
                    f"{s['script_id']} — {s['title'][:52]}"
                )

        print(f"\n{sep}")
        print("  CONSOLIDATED TEST EXECUTION PLAN")
        print(sep)
        for s in report.test_scripts_to_execute:
            print(
                f"  [{s['execution_priority']:8s}] "
                f"{s['script_id']:25s} "
                f"({s['phase']:8s} / {s['automation_status']:15s})  "
                f"{s['title'][:40]}"
            )
        print(f"\n{sep}\n")

    def to_dict(self, report: ImpactReport) -> Dict:
        """
        Serialise an ImpactReport to a plain dict (JSON-serialisable).

        :param report: ImpactReport to serialise.
        :return: Dict suitable for JSON export or audit logging.
        :requirement: EVOLV Sentinel — report serialisation
        """
        def _mod(m: DiffModule) -> Dict:
            return {
                "file_path": m.file_path,
                "lines_added": m.lines_added,
                "lines_removed": m.lines_removed,
                "lines_changed": m.lines_changed,
                "modified_functions": m.modified_functions,
            }

        def _req(r: AtRiskRequirement) -> Dict:
            return {
                "req_id": r.req_id,
                "title": r.title,
                "risk_level": r.risk_level,
                "criticality_score": r.criticality_score,
                "gxp_category": r.gxp_category,
                "regulatory_reference": r.regulatory_reference,
                "scope_of_change": r.scope_of_change,
                "impact_score": r.impact_score,
                "risk_band": r.risk_band,
                "changed_module_ids": r.changed_module_ids,
                "changed_functions": r.changed_functions,
                "test_scripts_required": r.test_scripts_required,
                "change_impact_types": r.change_impact_types,
            }

        return {
            "diff_hash": report.diff_hash,
            "analyzed_at": report.analyzed_at,
            "graph_id": report.graph_id,
            "summary": report.summary,
            "modified_modules": [_mod(m) for m in report.modified_modules],
            "at_risk_requirements": [_req(r) for r in report.at_risk_requirements],
            "test_scripts_to_execute": report.test_scripts_to_execute,
        }
