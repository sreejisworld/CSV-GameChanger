"""
EVOLV Sentinel — Justification Engine
========================================
Takes an ImpactReport from the Impact Engine and generates a formal,
GxP-compliant Impact Assessment Report (IAR) using Claude.

IAR Sections
------------
1. Change Summary      — plain-English explanation of the technical change.
2. In-Scope Tests      — per-test justification for why re-execution is required.
3. Exclusion Rationale — defensible, GAMP 5-grounded explanation for why
                         adjacent modules do not require re-testing.
4. Regulatory Conclusion — formal risk acceptance statement.

Modes
-----
- LLM mode (default)   : Calls Claude claude-sonnet-4-6 to generate rich,
                         contextual GxP language.
- Dry-run mode         : Generates deterministic, template-filled text with
                         no API calls. Safe for CI/smoke tests.

Usage
-----
    from Agents.sentinel.justification_engine import JustificationEngine

    engine = JustificationEngine.from_file(
        "Agents/sentinel/traceability_sample.json"
    )
    iar = engine.generate_iar(
        impact_report=report,
        diff_text=diff,
        author="Jane Smith, CSV Lead",
        project_name="EVOLV Validation Factory v2.1",
    )
    print(engine.render_to_markdown(iar))

:requirement: EVOLV Sentinel — Justification Engine / IAR Generation
"""
from __future__ import annotations

import json
import os
import re
import textwrap
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from .impact_engine import ImpactEngine, ImpactReport, AtRiskRequirement


# ---------------------------------------------------------------------------
# GAMP 5 / CSA citation constants
# ---------------------------------------------------------------------------

_GAMP5_CHANGE_CONTROL = (
    "GAMP 5 Rev 2, Section 8 — Change Control and Configuration Management"
)
_GAMP5_TESTING = "GAMP 5 Rev 2, Section 6.5 — Testing"
_GAMP5_RISK = "GAMP 5 Rev 2, Section 5 — Risk Management"
_CFR_PART11 = "21 CFR Part 11.10(e) and 11.10(k)"
_GAMP5_UNCHANGED = (
    "GAMP 5 Rev 2, Section 8.3.3 — Impact assessment shall consider "
    "the scope of the change; unaffected functional paths do not require "
    "re-qualification."
)

# Claude model to use for LLM generation
_CLAUDE_MODEL = "claude-sonnet-4-6"

# Maximum characters of diff included in the prompt (avoid token overflow)
_MAX_DIFF_CHARS = 3_000

# ---------------------------------------------------------------------------
# Dataclasses — IAR sections
# ---------------------------------------------------------------------------


@dataclass
class ChangeSummary:
    """
    Section 1 of the IAR: plain-English change description.

    :requirement: EVOLV Sentinel — Change Summary generation
    """
    change_type: str          # "Enhancement", "Defect Fix", "Configuration", "New Feature"
    gxp_classification: str   # "GxP Direct", "GxP Indirect", "GxP None"
    overview: str             # 1–2 sentence plain-English summary
    technical_detail: str     # module names, functions, what specifically changed
    affected_modules: List[str]
    affected_functions: List[str]


@dataclass
class InScopeTest:
    """
    One entry in Section 3: a test script that must be re-executed.

    :requirement: EVOLV Sentinel — In-Scope Test justification
    """
    script_id: str
    phase: str           # IQ / OQ / PQ / UAT / Informal
    title: str
    priority: str        # Critical / High / Medium / Low
    automation_status: str
    justification: str   # Why this test is specifically required
    regulatory_basis: str


@dataclass
class ExcludedModule:
    """
    One entry in Section 4: a related module that does NOT require re-testing.

    :requirement: EVOLV Sentinel — Exclusion Rationale generation
    """
    module_id: str
    file_path: str
    description: str
    shared_requirements: List[str]   # req_ids that link this module to the change
    exclusion_rationale: str         # GxP-defensible reason for exclusion
    regulatory_basis: str


@dataclass
class ImpactAssessmentReport:
    """
    Complete Impact Assessment Report.

    :requirement: EVOLV Sentinel — IAR output document
    """
    iar_id: str
    generated_at: str
    graph_id: str
    project_name: str
    author: str
    diff_hash: str
    generation_mode: str             # "llm" or "dry_run"

    # Section 1
    change_summary: ChangeSummary
    # Section 2 — at-risk requirements table (from ImpactReport)
    at_risk_requirements: List[AtRiskRequirement]
    # Section 3
    in_scope_tests: List[InScopeTest]
    # Section 4
    excluded_modules: List[ExcludedModule]
    # Section 5
    regulatory_conclusion: str
    risk_acceptance_statement: str


# ---------------------------------------------------------------------------
# System prompt for Claude
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = textwrap.dedent("""\
    You are a Senior GxP Validation Engineer and Regulatory Affairs Specialist
    at a pharmaceutical software company. You produce formal Impact Assessment
    Reports (IARs) for changes to validated computer systems governed by
    GAMP 5 Rev 2 and 21 CFR Part 11.

    Your language must be:
    - Precise, unambiguous, and regulatory inspection-ready.
    - Grounded strictly in the technical evidence provided — never speculative.
    - Written in formal document style using phrases such as:
        "The modification does not alter functional path logic..."
        "No requalification is warranted under GAMP 5 Section 8.3.3..."
        "Re-execution of this script is required to confirm functional
         equivalence per GAMP 5 Section 6.5..."
    - Free of marketing language, hedging, and filler words.

    Respond ONLY with a valid JSON object that exactly matches the schema
    described in the user message. No preamble, no explanation outside the JSON.
""")


# ---------------------------------------------------------------------------
# Justification Engine
# ---------------------------------------------------------------------------

class JustificationEngine:
    """
    Generates a formal Impact Assessment Report (IAR) from an ImpactReport.

    Wraps the Claude API to produce GxP-compliant change justification,
    in-scope test rationale, and module exclusion rationale.

    :requirement: EVOLV Sentinel — Justification Engine orchestration
    """

    def __init__(
        self,
        graph: Dict,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Initialise the Justification Engine.

        :param graph:   Parsed traceability graph dict.
        :param api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
        """
        self._graph = graph
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._module_index: Dict[str, Dict] = {
            m["module_id"]: m for m in graph.get("code_modules", [])
        }
        self._req_index: Dict[str, Dict] = {
            r["req_id"]: r for r in graph.get("requirements", [])
        }
        self._script_index: Dict[str, Dict] = {
            s["script_id"]: s for s in graph.get("test_scripts", [])
        }
        self._links: List[Dict] = graph.get("traceability_links", [])

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        api_key: Optional[str] = None,
    ) -> "JustificationEngine":
        """
        Load a traceability graph from a JSON file on disk.

        :param path:    Path to populated traceability graph JSON.
        :param api_key: Anthropic API key (optional).
        :return: Configured JustificationEngine.
        :requirement: EVOLV Sentinel — graph loading
        """
        with open(path, "r", encoding="utf-8") as fh:
            graph = json.load(fh)
        return cls(graph, api_key=api_key)

    @classmethod
    def from_json(
        cls,
        json_str: str,
        api_key: Optional[str] = None,
    ) -> "JustificationEngine":
        """Load from a raw JSON string."""
        return cls(json.loads(json_str), api_key=api_key)

    # ------------------------------------------------------------------
    # Excluded module identification
    # ------------------------------------------------------------------

    def _identify_excluded_modules(
        self, impact_report: ImpactReport
    ) -> List[Dict[str, Any]]:
        """
        Find modules that are related to the change (via shared requirements)
        but were NOT themselves modified in the diff.

        A module is "related" if it appears in a traceability_link that
        references the same requirement as a changed module.

        :param impact_report: Output of ImpactEngine.analyze().
        :return: List of dicts with module metadata and shared requirement IDs.
        :requirement: EVOLV Sentinel — exclusion candidate identification
        """
        # File paths that were actually modified
        changed_paths = {
            m.file_path for m in impact_report.modified_modules
        }
        # Module IDs directly impacted
        impacted_module_ids = {
            r_id
            for req in impact_report.at_risk_requirements
            for r_id in req.changed_module_ids
        }
        # Requirement IDs implicated by the change
        implicated_req_ids = {
            r.req_id for r in impact_report.at_risk_requirements
        }

        excluded: List[Dict[str, Any]] = []
        seen_module_ids: set = set()

        for link in self._links:
            mod_id = link["module_id"]
            req_id = link["req_id"]

            if mod_id in impacted_module_ids:
                continue  # This module is IN scope — skip

            if req_id not in implicated_req_ids:
                continue  # No shared requirement with the change — skip

            if mod_id in seen_module_ids:
                # Already added — just append the shared req
                for entry in excluded:
                    if entry["module_id"] == mod_id:
                        if req_id not in entry["shared_requirements"]:
                            entry["shared_requirements"].append(req_id)
                continue

            graph_module = self._module_index.get(mod_id)
            if graph_module is None:
                continue

            # Only include if not changed
            if graph_module["file_path"] in changed_paths:
                continue

            seen_module_ids.add(mod_id)
            excluded.append({
                "module_id": mod_id,
                "file_path": graph_module["file_path"],
                "description": graph_module.get("description", ""),
                "shared_requirements": [req_id],
                "change_impact_type": link.get("change_impact_type", "Indirect"),
            })

        return excluded

    # ------------------------------------------------------------------
    # Claude API call
    # ------------------------------------------------------------------

    def _call_claude(
        self,
        impact_report: ImpactReport,
        diff_text: str,
        excluded_raw: List[Dict],
    ) -> Dict:
        """
        Call Claude to generate IAR narrative sections.

        :param impact_report: Scored impact analysis.
        :param diff_text:     Raw git diff (truncated if necessary).
        :param excluded_raw:  Pre-identified excluded modules.
        :return: Parsed JSON dict with all narrative sections.
        :requirement: EVOLV Sentinel — LLM-powered IAR generation
        """
        try:
            import anthropic  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "anthropic package not installed. "
                "Run: pip install anthropic"
            ) from exc

        if not self._api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. "
                "Pass api_key= or set the environment variable."
            )

        # Truncate diff to avoid token overflow
        diff_snippet = diff_text[:_MAX_DIFF_CHARS]
        if len(diff_text) > _MAX_DIFF_CHARS:
            diff_snippet += (
                f"\n... [diff truncated — "
                f"{len(diff_text) - _MAX_DIFF_CHARS} chars omitted]"
            )

        # Build structured context
        changed_modules_ctx = []
        for m in impact_report.modified_modules:
            changed_modules_ctx.append({
                "file_path": m.file_path,
                "lines_added": m.lines_added,
                "lines_removed": m.lines_removed,
                "modified_functions": m.modified_functions,
            })

        at_risk_ctx = [
            {
                "req_id": r.req_id,
                "title": r.title,
                "risk_level": r.risk_level,
                "gxp_category": r.gxp_category,
                "criticality_score": r.criticality_score,
                "scope_of_change": r.scope_of_change,
                "impact_score": r.impact_score,
                "risk_band": r.risk_band,
                "changed_functions": r.changed_functions,
                "regulatory_reference": r.regulatory_reference,
                "change_impact_types": r.change_impact_types,
            }
            for r in impact_report.at_risk_requirements
        ]

        all_scripts = {
            s["script_id"]: s
            for req in impact_report.at_risk_requirements
            for s in req.test_scripts_required
        }

        # Build the prompt
        user_prompt = f"""
Generate an Impact Assessment Report (IAR) for the following validated system
change. Base your assessment strictly on the data provided.

═══════════════════════════════════════════════════════════
GIT DIFF SNIPPET
═══════════════════════════════════════════════════════════
{diff_snippet}

═══════════════════════════════════════════════════════════
CHANGED MODULES
═══════════════════════════════════════════════════════════
{json.dumps(changed_modules_ctx, indent=2)}

═══════════════════════════════════════════════════════════
AT-RISK REQUIREMENTS
═══════════════════════════════════════════════════════════
{json.dumps(at_risk_ctx, indent=2)}

═══════════════════════════════════════════════════════════
TEST SCRIPTS REQUIRING RE-EXECUTION
═══════════════════════════════════════════════════════════
{json.dumps(list(all_scripts.values()), indent=2)}

═══════════════════════════════════════════════════════════
RELATED MODULES NOT MODIFIED (exclusion candidates)
═══════════════════════════════════════════════════════════
{json.dumps(excluded_raw, indent=2)}

═══════════════════════════════════════════════════════════
REQUIRED OUTPUT SCHEMA
═══════════════════════════════════════════════════════════
Return exactly this JSON structure. All string values must be formal
GxP document language suitable for FDA/EMA regulatory inspection.

{{
  "change_type": "<Enhancement|Defect Fix|Configuration Change|New Feature>",
  "gxp_classification": "<GxP Direct|GxP Indirect|GxP None>",
  "overview": "<1-2 sentence plain-English summary of what changed>",
  "technical_detail": "<Precise description: which modules, which functions, what was altered at the code level>",
  "in_scope_tests": [
    {{
      "script_id": "<exact script_id from data above>",
      "justification": "<2-3 sentence formal justification for why this specific test must be re-executed>",
      "regulatory_basis": "<GAMP 5 / 21 CFR Part 11 citation>"
    }}
  ],
  "excluded_modules": [
    {{
      "module_id": "<exact module_id from data above>",
      "exclusion_rationale": "<2-3 sentence GxP-defensible explanation. Must reference specific unchanged logic. Must NOT say 'probably' or 'likely'.>",
      "regulatory_basis": "<GAMP 5 / 21 CFR Part 11 citation for the exclusion principle>"
    }}
  ],
  "regulatory_conclusion": "<2-3 sentence formal risk acceptance statement. Must reference GAMP 5 risk-based approach. Must state whether the change is GxP direct.>",
  "risk_acceptance_statement": "<1 sentence formal declaration that the change has been assessed and the residual risk is acceptable pending re-execution of in-scope tests.>"
}}
"""

        client = anthropic.Anthropic(api_key=self._api_key)
        message = client.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)

    # ------------------------------------------------------------------
    # Dry-run (template-based, no LLM)
    # ------------------------------------------------------------------

    def _dry_run_response(
        self,
        impact_report: ImpactReport,
        excluded_raw: List[Dict],
    ) -> Dict:
        """
        Generate a template-based IAR response without calling Claude.

        Produces deterministic, GxP-compliant boilerplate text populated
        with data from the ImpactReport. Suitable for CI, smoke tests,
        and environments without API key access.

        :param impact_report: Scored impact analysis.
        :param excluded_raw:  Pre-identified excluded modules.
        :return: Dict matching the Claude response schema.
        :requirement: EVOLV Sentinel — offline IAR template mode
        """
        changed_files = [m.file_path for m in impact_report.modified_modules]
        changed_fns_flat = sorted({
            fn
            for r in impact_report.at_risk_requirements
            for fn in r.changed_functions
        })
        top_req = (
            impact_report.at_risk_requirements[0]
            if impact_report.at_risk_requirements
            else None
        )

        gxp_class = "GxP None"
        for r in impact_report.at_risk_requirements:
            if r.gxp_category == "GxP Direct":
                gxp_class = "GxP Direct"
                break
            if r.gxp_category == "GxP Indirect":
                gxp_class = "GxP Indirect"

        fn_list = ", ".join(changed_fns_flat) or "one or more functions"
        file_list = ", ".join(changed_files)

        overview = (
            f"This change modifies {fn_list} within {file_list}. "
            f"The modification affects {len(impact_report.at_risk_requirements)} "
            f"validated requirement(s) with a maximum impact score of "
            f"{max((r.impact_score for r in impact_report.at_risk_requirements), default=0):.2f}."
        )
        technical_detail = (
            f"The following source files were modified: {file_list}. "
            f"Functions affected: {fn_list}. "
            f"Net lines changed: "
            f"+{sum(m.lines_added for m in impact_report.modified_modules)} "
            f"/ -{sum(m.lines_removed for m in impact_report.modified_modules)}. "
            f"The change was assessed at the function level against the "
            f"EVOLV Sentinel Traceability Graph (Graph ID: "
            f"{impact_report.graph_id})."
        )

        # Collect unique scripts across all at-risk requirements
        seen_scripts: set = set()
        in_scope_tests = []
        for req in impact_report.at_risk_requirements:
            for s in req.test_scripts_required:
                sid = s["script_id"]
                if sid in seen_scripts:
                    continue
                seen_scripts.add(sid)
                in_scope_tests.append({
                    "script_id": sid,
                    "justification": (
                        f"{s['title']} must be re-executed because the "
                        f"modification to {fn_list} directly affects the "
                        f"functional behaviour validated by this script. "
                        f"Per GAMP 5 Section 6.5, any change to a validated "
                        f"function requires re-execution of associated "
                        f"{s['phase']} test scripts to confirm functional "
                        f"equivalence and maintain the validated state."
                    ),
                    "regulatory_basis": _GAMP5_TESTING,
                })

        excluded_modules = []
        for mod in excluded_raw:
            shared = ", ".join(mod["shared_requirements"])
            excluded_modules.append({
                "module_id": mod["module_id"],
                "exclusion_rationale": (
                    f"Module {mod['module_id']} ({mod['file_path']}) was "
                    f"not modified in this change. Although it shares "
                    f"requirement(s) {shared} with the changed modules, "
                    f"its internal functional path logic, algorithm, and "
                    f"data structures remain identical to the previously "
                    f"validated version. Per GAMP 5 Section 8.3.3, "
                    f"requalification is not required for unmodified modules "
                    f"where the change does not affect their functional scope."
                ),
                "regulatory_basis": _GAMP5_UNCHANGED,
            })

        req_ref = top_req.regulatory_reference if top_req else _GAMP5_RISK
        conclusion = (
            f"This change has been assessed as {gxp_class} under GAMP 5 "
            f"risk classification. The Impact Engine identified "
            f"{len(impact_report.at_risk_requirements)} at-risk requirement(s) "
            f"and {len(seen_scripts)} test script(s) requiring re-execution. "
            f"Modules with no functional code changes have been formally "
            f"excluded from re-testing in accordance with the GAMP 5 "
            f"risk-based approach to change control. "
            f"Regulatory basis: {req_ref}."
        )
        risk_stmt = (
            f"The residual risk associated with this change is assessed as "
            f"acceptable upon successful re-execution of all in-scope test "
            f"scripts identified in Section 3 of this report."
        )

        return {
            "change_type": "Enhancement",
            "gxp_classification": gxp_class,
            "overview": overview,
            "technical_detail": technical_detail,
            "in_scope_tests": in_scope_tests,
            "excluded_modules": excluded_modules,
            "regulatory_conclusion": conclusion,
            "risk_acceptance_statement": risk_stmt,
        }

    # ------------------------------------------------------------------
    # IAR assembly
    # ------------------------------------------------------------------

    def _assemble_iar(
        self,
        llm_response: Dict,
        impact_report: ImpactReport,
        excluded_raw: List[Dict],
        project_name: str,
        author: str,
        generation_mode: str,
    ) -> ImpactAssessmentReport:
        """
        Assemble a fully structured ImpactAssessmentReport from the
        LLM (or dry-run) response dict and the ImpactReport.

        :requirement: EVOLV Sentinel — IAR assembly
        """
        iar_id = (
            f"IAR-"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d')}-"
            f"{impact_report.diff_hash[:8].upper()}"
        )

        # Change Summary
        change_summary = ChangeSummary(
            change_type=llm_response.get("change_type", "Enhancement"),
            gxp_classification=llm_response.get(
                "gxp_classification", "GxP Direct"
            ),
            overview=llm_response.get("overview", ""),
            technical_detail=llm_response.get("technical_detail", ""),
            affected_modules=[
                m.file_path for m in impact_report.modified_modules
            ],
            affected_functions=sorted({
                fn
                for r in impact_report.at_risk_requirements
                for fn in r.changed_functions
            }),
        )

        # Build script lookup for phase/priority/automation
        script_lookup: Dict[str, Dict] = {}
        for req in impact_report.at_risk_requirements:
            for s in req.test_scripts_required:
                script_lookup[s["script_id"]] = s

        # In-scope tests
        seen_scripts: set = set()
        in_scope_tests: List[InScopeTest] = []
        for entry in llm_response.get("in_scope_tests", []):
            sid = entry.get("script_id", "")
            if sid in seen_scripts:
                continue
            seen_scripts.add(sid)
            s_meta = script_lookup.get(sid, {})
            in_scope_tests.append(InScopeTest(
                script_id=sid,
                phase=s_meta.get("phase", ""),
                title=s_meta.get("title", sid),
                priority=s_meta.get("execution_priority", ""),
                automation_status=s_meta.get("automation_status", "Manual"),
                justification=entry.get("justification", ""),
                regulatory_basis=entry.get("regulatory_basis", _GAMP5_TESTING),
            ))

        # Excluded modules
        excluded_meta: Dict[str, Dict] = {
            e["module_id"]: e for e in excluded_raw
        }
        excluded_modules: List[ExcludedModule] = []
        for entry in llm_response.get("excluded_modules", []):
            mid = entry.get("module_id", "")
            meta = excluded_meta.get(mid, {})
            graph_mod = self._module_index.get(mid, {})
            excluded_modules.append(ExcludedModule(
                module_id=mid,
                file_path=meta.get(
                    "file_path", graph_mod.get("file_path", "")
                ),
                description=graph_mod.get("description", ""),
                shared_requirements=meta.get("shared_requirements", []),
                exclusion_rationale=entry.get("exclusion_rationale", ""),
                regulatory_basis=entry.get(
                    "regulatory_basis", _GAMP5_UNCHANGED
                ),
            ))

        return ImpactAssessmentReport(
            iar_id=iar_id,
            generated_at=impact_report.analyzed_at,
            graph_id=impact_report.graph_id,
            project_name=project_name,
            author=author,
            diff_hash=impact_report.diff_hash,
            generation_mode=generation_mode,
            change_summary=change_summary,
            at_risk_requirements=impact_report.at_risk_requirements,
            in_scope_tests=in_scope_tests,
            excluded_modules=excluded_modules,
            regulatory_conclusion=llm_response.get(
                "regulatory_conclusion", ""
            ),
            risk_acceptance_statement=llm_response.get(
                "risk_acceptance_statement", ""
            ),
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_iar(
        self,
        impact_report: ImpactReport,
        diff_text: str,
        author: str = "EVOLV Sentinel",
        project_name: str = "EVOLV Validation Factory",
        dry_run: bool = False,
    ) -> ImpactAssessmentReport:
        """
        Generate a formal Impact Assessment Report for the given ImpactReport.

        :param impact_report: Output of ImpactEngine.analyze().
        :param diff_text:     Raw git diff string.
        :param author:        Name/role of the report preparer.
        :param project_name:  Project name for the IAR header.
        :param dry_run:       If True, skip Claude and use template mode.
        :return: Structured ImpactAssessmentReport.
        :requirement: EVOLV Sentinel — IAR generation entry point
        """
        if not impact_report.at_risk_requirements:
            raise ValueError(
                "ImpactReport contains no at-risk requirements. "
                "Run ImpactEngine.analyze() first."
            )

        excluded_raw = self._identify_excluded_modules(impact_report)

        if dry_run or not self._api_key:
            mode = "dry_run"
            llm_response = self._dry_run_response(impact_report, excluded_raw)
        else:
            mode = "llm"
            llm_response = self._call_claude(
                impact_report, diff_text, excluded_raw
            )

        return self._assemble_iar(
            llm_response=llm_response,
            impact_report=impact_report,
            excluded_raw=excluded_raw,
            project_name=project_name,
            author=author,
            generation_mode=mode,
        )

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    @staticmethod
    def render_to_markdown(iar: ImpactAssessmentReport) -> str:
        """
        Render an ImpactAssessmentReport to a formal Markdown document.

        :param iar: Populated ImpactAssessmentReport.
        :return:    Markdown string suitable for saving as .md or rendering
                    in Streamlit.
        :requirement: EVOLV Sentinel — IAR Markdown rendering
        """
        cs = iar.change_summary
        lines = [
            "# IMPACT ASSESSMENT REPORT",
            "",
            "---",
            "",
            "## Document Control",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| **IAR ID** | `{iar.iar_id}` |",
            f"| **Project** | {iar.project_name} |",
            f"| **Traceability Graph** | `{iar.graph_id}` |",
            f"| **Reference Diff Hash** | `{iar.diff_hash}` |",
            f"| **Date Generated** | {iar.generated_at[:10]} |",
            f"| **Time (UTC)** | {iar.generated_at[11:19]} |",
            f"| **Prepared By** | {iar.author} |",
            f"| **Generation Mode** | {iar.generation_mode.upper()} |",
            f"| **Document Status** | DRAFT — Pending QA Review |",
            "",
            "---",
            "",
            "## 1. Change Summary",
            "",
            f"| Attribute | Value |",
            f"|-----------|-------|",
            f"| **Change Type** | {cs.change_type} |",
            f"| **GxP Classification** | {cs.gxp_classification} |",
            f"| **Files Modified** | {len(cs.affected_modules)} |",
            f"| **Functions Affected** | {len(cs.affected_functions)} |",
            "",
            "### 1.1 Overview",
            "",
            cs.overview,
            "",
            "### 1.2 Technical Detail",
            "",
            cs.technical_detail,
            "",
            "### 1.3 Modified Files",
            "",
        ]
        for fp in cs.affected_modules:
            lines.append(f"- `{fp}`")

        if cs.affected_functions:
            lines += [
                "",
                "### 1.4 Modified Functions",
                "",
            ]
            for fn in cs.affected_functions:
                lines.append(f"- `{fn}()`")

        lines += [
            "",
            "---",
            "",
            "## 2. Risk Impact Assessment",
            "",
            "Impact Score = **Requirement Criticality** x **Scope of Change**  ",
            "Scope is calculated as: `0.6 x line_factor + 0.4 x function_factor`",
            "",
            "| # | Requirement ID | Title | Risk Level | GxP | Criticality | Scope | **Impact Score** | Band |",
            "|---|---------------|-------|------------|-----|-------------|-------|-----------------|------|",
        ]
        for i, r in enumerate(iar.at_risk_requirements, 1):
            lines.append(
                f"| {i} | `{r.req_id}` | {r.title[:45]} | {r.risk_level} "
                f"| {r.gxp_category} | {r.criticality_score} "
                f"| {r.scope_of_change:.4f} | **{r.impact_score:.4f}** "
                f"| **{r.risk_band}** |"
            )

        lines += [
            "",
            "---",
            "",
            "## 3. In-Scope Tests — Required Re-Execution",
            "",
            "_The following test scripts must be re-executed before the change_",
            "_may be considered in a validated state._",
            "",
        ]
        for i, t in enumerate(iar.in_scope_tests, 1):
            lines += [
                f"### 3.{i} `{t.script_id}` — {t.title}",
                "",
                f"| Field | Value |",
                f"|-------|-------|",
                f"| **Phase** | {t.phase} |",
                f"| **Execution Priority** | {t.priority} |",
                f"| **Automation Status** | {t.automation_status} |",
                "",
                f"**Justification:**",
                "",
                f"> {t.justification}",
                "",
                f"**Regulatory Basis:** _{t.regulatory_basis}_",
                "",
            ]

        lines += [
            "---",
            "",
            "## 4. Exclusion Rationale",
            "",
            "_The following modules are related to the changed code via shared_",
            "_requirements but do NOT require re-testing. A formal GxP-defensible_",
            "_rationale is provided for each exclusion._",
            "",
        ]

        if not iar.excluded_modules:
            lines += [
                "> **No exclusions applicable.** All related modules were either",
                "> directly modified or have no traceability link to the changed",
                "> requirements.",
                "",
            ]
        else:
            for i, ex in enumerate(iar.excluded_modules, 1):
                shared_str = ", ".join(f"`{r}`" for r in ex.shared_requirements)
                lines += [
                    f"### 4.{i} `{ex.module_id}` — `{ex.file_path}`",
                    "",
                    f"**Description:** {ex.description}",
                    "",
                    f"**Shared Requirements:** {shared_str}",
                    "",
                    f"**Exclusion Rationale:**",
                    "",
                    f"> {ex.exclusion_rationale}",
                    "",
                    f"**Regulatory Basis:** _{ex.regulatory_basis}_",
                    "",
                ]

        lines += [
            "---",
            "",
            "## 5. Regulatory Conclusion",
            "",
            iar.regulatory_conclusion,
            "",
            f"> **Risk Acceptance Statement:** {iar.risk_acceptance_statement}",
            "",
            "---",
            "",
            "## 6. Sign-Off",
            "",
            "_This document must be reviewed and approved by the CSV Lead and_",
            "_Quality Assurance before the change may be deployed to the_",
            "_validated environment._",
            "",
            "| Role | Name | Signature | Date |",
            "|------|------|-----------|------|",
            "| Prepared By (CSV Engineer) | | | |",
            "| Reviewed By (QA) | | | |",
            "| Approved By (System Owner) | | | |",
            "",
            "---",
            "",
            "_Generated by EVOLV Sentinel — Justification Engine_  ",
            f"_Powered by EVOLV | A WingstarTech Inc. Product_  ",
            f"_IAR ID: {iar.iar_id}_  ",
            f"_Diff Hash: {iar.diff_hash}_",
        ]

        return "\n".join(lines)

    def to_dict(self, iar: ImpactAssessmentReport) -> Dict:
        """
        Serialise an ImpactAssessmentReport to a JSON-ready dict.

        :param iar: Populated ImpactAssessmentReport.
        :return: Dict suitable for JSON export or audit logging.
        :requirement: EVOLV Sentinel — IAR serialisation
        """
        cs = iar.change_summary

        def _req(r: AtRiskRequirement) -> Dict:
            return {
                "req_id": r.req_id,
                "title": r.title,
                "risk_level": r.risk_level,
                "gxp_category": r.gxp_category,
                "criticality_score": r.criticality_score,
                "scope_of_change": r.scope_of_change,
                "impact_score": r.impact_score,
                "risk_band": r.risk_band,
                "changed_module_ids": r.changed_module_ids,
                "changed_functions": r.changed_functions,
                "test_scripts_required": r.test_scripts_required,
            }

        return {
            "iar_id": iar.iar_id,
            "generated_at": iar.generated_at,
            "graph_id": iar.graph_id,
            "project_name": iar.project_name,
            "author": iar.author,
            "diff_hash": iar.diff_hash,
            "generation_mode": iar.generation_mode,
            "change_summary": {
                "change_type": cs.change_type,
                "gxp_classification": cs.gxp_classification,
                "overview": cs.overview,
                "technical_detail": cs.technical_detail,
                "affected_modules": cs.affected_modules,
                "affected_functions": cs.affected_functions,
            },
            "at_risk_requirements": [_req(r) for r in iar.at_risk_requirements],
            "in_scope_tests": [
                {
                    "script_id": t.script_id,
                    "phase": t.phase,
                    "title": t.title,
                    "priority": t.priority,
                    "automation_status": t.automation_status,
                    "justification": t.justification,
                    "regulatory_basis": t.regulatory_basis,
                }
                for t in iar.in_scope_tests
            ],
            "excluded_modules": [
                {
                    "module_id": ex.module_id,
                    "file_path": ex.file_path,
                    "description": ex.description,
                    "shared_requirements": ex.shared_requirements,
                    "exclusion_rationale": ex.exclusion_rationale,
                    "regulatory_basis": ex.regulatory_basis,
                }
                for ex in iar.excluded_modules
            ],
            "regulatory_conclusion": iar.regulatory_conclusion,
            "risk_acceptance_statement": iar.risk_acceptance_statement,
        }
