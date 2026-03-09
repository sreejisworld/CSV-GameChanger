"""
EVOLV Sentinel — Blast Radius Impact Engine.

Computes the regression "blast radius" when a requirement changes.
Semantic hashing detects meaningful (not cosmetic) change; impact
mapping crawls the traceability matrix to find all linked Test
Cases, Risks, and Regulatory Clauses; regression scoring
categorises each as Red / Yellow / Green.

:requirement: URS-24.1 - Detect semantic delta between requirement
              versions.
:requirement: URS-24.2 - Map impact via traceability matrix and
              emit tiered blast-radius JSON.
:requirement: URS-24.3 - Score regression severity as
              Red / Yellow / Green.
:requirement: URS-24.4 - Calculate time saved vs. full regression.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from Agents.integrity_manager import log_audit_event


# -----------------------------------------------------------------
# Enums
# -----------------------------------------------------------------

class ChangeCategory(str, Enum):
    """
    Semantic category of a requirement change.

    :requirement: URS-24.1
    """

    STRUCTURAL = "Structural"        # Logic / scope / threshold
    BEHAVIOURAL = "Behavioural"      # Workflow / interaction
    CLARIFICATION = "Clarification"  # Typo / minor wording
    REGULATORY = "Regulatory"        # Regulation reference


class RegressionSeverity(str, Enum):
    """
    Regression impact severity for a linked item.

    :requirement: URS-24.3
    """

    RED = "Red"        # Rerun required
    YELLOW = "Yellow"  # Review advised
    GREEN = "Green"    # No action needed


class ImpactTier(int, Enum):
    """Traceability depth tier of an impacted item."""

    TIER_1 = 1  # Directly linked Test Cases
    TIER_2 = 2  # Risks + Trace Matrix
    TIER_3 = 3  # Regulatory Clauses


# -----------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------

@dataclass
class ImpactedItem:
    """
    A single item within the blast radius.

    :requirement: URS-24.2
    """

    item_id: str
    item_type: str    # test_case | risk | regulatory_clause | trace_matrix
    title: str
    severity: RegressionSeverity
    tier: ImpactTier
    reason: str
    linked_requirement: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "item_id":            self.item_id,
            "item_type":          self.item_type,
            "title":              self.title,
            "severity":           self.severity.value,
            "tier":               self.tier.value,
            "reason":             self.reason,
            "linked_requirement": self.linked_requirement,
        }


@dataclass
class BlastRadiusReport:
    """
    Full blast-radius report for a single requirement change.

    :requirement: URS-24.2, URS-24.3, URS-24.4, URS-24.5,
                  URS-24.6, URS-24.7
    """

    change_id: str
    requirement_id: str
    original_hash: str
    new_hash: str
    change_category: ChangeCategory
    semantic_delta: str
    impacted_items: List[ImpactedItem] = field(
        default_factory=list
    )
    red_count: int = 0
    yellow_count: int = 0
    green_count: int = 0
    total_test_cases: int = 0
    optimized_test_cases: int = 0
    time_saved_hours: float = 0.0
    # 0-100 composite impact score
    impact_score: int = 0
    # D3.js-compatible network graph
    network_graph: Dict[str, Any] = field(
        default_factory=lambda: {"nodes": [], "edges": []}
    )
    # Natural-language rationalization log
    rationalization_log: str = ""
    generated_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )
    blast_radius_json: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "change_id":           self.change_id,
            "requirement_id":      self.requirement_id,
            "original_hash":       self.original_hash,
            "new_hash":            self.new_hash,
            "change_category":     self.change_category.value,
            "semantic_delta":      self.semantic_delta,
            "red_count":           self.red_count,
            "yellow_count":        self.yellow_count,
            "green_count":         self.green_count,
            "total_test_cases":    self.total_test_cases,
            "optimized_test_cases": self.optimized_test_cases,
            "time_saved_hours":    round(self.time_saved_hours, 2),
            "impact_score":        self.impact_score,
            "network_graph":       self.network_graph,
            "rationalization_log": self.rationalization_log,
            "generated_at":        self.generated_at,
            "blast_radius_json":   self.blast_radius_json,
            "impacted_items": [
                i.to_dict() for i in self.impacted_items
            ],
        }


# -----------------------------------------------------------------
# Keyword sets for deterministic change categorisation
# -----------------------------------------------------------------

_STRUCTURAL_KEYWORDS = frozenset({
    "formula", "algorithm", "calculation", "equation",
    "threshold", "limit", "maximum", "minimum", "range",
    "scope", "remove", "delete", "replace", "no longer",
    "must not", "shall not", "prohibit", "add new",
})

_BEHAVIOURAL_KEYWORDS = frozenset({
    "workflow", "process", "flow", "sequence", "step",
    "before", "after", "when", "trigger", "notify",
    "approve", "reject", "escalate", "route",
})

_REGULATORY_KEYWORDS = frozenset({
    "21 cfr", "ich", "gamp", "gdpr", "hipaa",
    "part 11", "part 211", "annex 11", "iso 13485",
    "regulation", "regulatory", "compliance",
    "fda", "ema", "mhra",
})


# -----------------------------------------------------------------
# SentinelImpactAgent
# -----------------------------------------------------------------

class SentinelImpactAgent:
    """
    Blast Radius engine for EVOLV Sentinel.

    Computes the semantic delta between old and new requirement
    text, crawls the traceability matrix for linked items, scores
    each item Red / Yellow / Green, and returns a BlastRadiusReport.

    Fully deterministic by default; LLM-enhanced delta detection
    is applied opportunistically when an Anthropic key is available.

    :requirement: URS-24.1 through URS-24.4
    """

    # Minutes per test case in a full manual regression run
    _TC_MINUTES: float = 30.0

    def __init__(self) -> None:
        self._llm_client: Optional[Any] = None
        self._llm_available = False
        self._try_load_llm()

    def _try_load_llm(self) -> None:
        """Attempt to load Anthropic client (optional)."""
        try:
            import os
            import anthropic
            key = os.environ.get("ANTHROPIC_API_KEY", "")
            if key:
                self._llm_client = anthropic.Anthropic(
                    api_key=key
                )
                self._llm_available = True
        except Exception:
            pass

    # ----------------------------------------------------------
    # Main entry point
    # ----------------------------------------------------------

    def analyze_blast_radius(
        self,
        old_requirement: str,
        new_requirement: str,
        requirement_id: str,
        traceability_matrix: Optional[Dict[str, Any]] = None,
        change_id: Optional[str] = None,
    ) -> BlastRadiusReport:
        """
        Compute the full blast-radius report for a requirement
        change.

        :param old_requirement: Original requirement text.
        :param new_requirement: Updated requirement text.
        :param requirement_id: Identifier, e.g. "URS-7.1".
        :param traceability_matrix: Optional trace matrix dict
               keyed by requirement_id.  Falls back to a demo
               set when *None* or empty.
        :param change_id: Optional external change ID (ServiceNow,
               SAP, Jira).  Auto-generated when omitted.
        :return: BlastRadiusReport.
        :requirement: URS-24.1 - URS-24.4
        """
        _change_id = change_id or (
            "CHG-"
            + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        )

        old_hash = self.compute_text_hash(old_requirement)
        new_hash = self.compute_text_hash(new_requirement)

        category, delta = self.detect_semantic_delta(
            old_requirement, new_requirement
        )

        matrix = traceability_matrix or {}
        impacted = self.map_impact(
            requirement_id=requirement_id,
            change_category=category,
            traceability_matrix=matrix,
        )

        red = sum(
            1 for i in impacted
            if i.severity == RegressionSeverity.RED
        )
        yellow = sum(
            1 for i in impacted
            if i.severity == RegressionSeverity.YELLOW
        )
        green = sum(
            1 for i in impacted
            if i.severity == RegressionSeverity.GREEN
        )

        tcs = sum(
            1 for i in impacted if i.item_type == "test_case"
        )
        red_tcs = sum(
            1 for i in impacted
            if i.item_type == "test_case"
            and i.severity == RegressionSeverity.RED
        )
        yellow_tcs = sum(
            1 for i in impacted
            if i.item_type == "test_case"
            and i.severity == RegressionSeverity.YELLOW
        )
        time_saved = self._calculate_time_saved(
            red=red_tcs,
            yellow=yellow_tcs,
            total=tcs if tcs else len(impacted),
        )

        br_json = self._build_blast_radius_json(
            requirement_id=requirement_id,
            impacted_items=impacted,
        )

        impact_score = self._compute_impact_score(
            category=category,
            impacted=impacted,
            red=red,
            yellow=yellow,
        )
        network_graph = self._generate_network_graph(
            requirement_id=requirement_id,
            impacted_items=impacted,
        )
        rationalization_log = self._generate_rationalization_log(
            requirement_id=requirement_id,
            category=category,
            delta=delta,
            impacted=impacted,
            red=red,
            yellow=yellow,
            green=green,
            total_tcs=tcs or len(impacted),
            time_saved=time_saved,
            impact_score=impact_score,
        )

        report = BlastRadiusReport(
            change_id=_change_id,
            requirement_id=requirement_id,
            original_hash=old_hash,
            new_hash=new_hash,
            change_category=category,
            semantic_delta=delta,
            impacted_items=impacted,
            red_count=red,
            yellow_count=yellow,
            green_count=green,
            total_test_cases=tcs or len(impacted),
            optimized_test_cases=red_tcs + yellow_tcs,
            time_saved_hours=time_saved,
            impact_score=impact_score,
            network_graph=network_graph,
            rationalization_log=rationalization_log,
            blast_radius_json=br_json,
        )

        log_audit_event(
            agent_name="SentinelImpactAgent",
            action="BLAST_RADIUS_CALCULATED",
            decision_logic=(
                f"Req {requirement_id}: "
                f"{category.value} change — "
                f"Red={red}, Yellow={yellow}, Green={green}, "
                f"ImpactScore={impact_score}"
            ),
            thought_process={
                "inputs": {
                    "requirement_id": requirement_id,
                    "change_category": category.value,
                    "semantic_delta": delta,
                },
                "steps": [
                    "Computed semantic hash of old/new text",
                    f"Detected {category.value} change",
                    f"Mapped {len(impacted)} impacted items",
                    "Scored items Red/Yellow/Green",
                    f"Computed impact score: {impact_score}/100",
                    "Generated network graph (nodes + edges)",
                    "Wrote rationalization log",
                ],
                "outputs": {
                    "red": red,
                    "yellow": yellow,
                    "green": green,
                    "impact_score": impact_score,
                    "time_saved_hours": round(time_saved, 2),
                },
            },
        )

        return report

    # ----------------------------------------------------------
    # Semantic hashing
    # ----------------------------------------------------------

    @staticmethod
    def compute_text_hash(text: str) -> str:
        """
        Compute a normalised SHA-256 hash of requirement text.

        Normalisation strips extra whitespace and lowercases so
        purely cosmetic formatting changes do not affect the hash.

        :param text: Input text.
        :return: Hex SHA-256 digest.
        :requirement: URS-24.1
        """
        normalised = " ".join(text.lower().split())
        return hashlib.sha256(normalised.encode()).hexdigest()

    # ----------------------------------------------------------
    # Semantic delta detection
    # ----------------------------------------------------------

    def detect_semantic_delta(
        self,
        old_text: str,
        new_text: str,
    ) -> Tuple[ChangeCategory, str]:
        """
        Categorise the change and produce a human-readable delta.

        Uses the LLM when available; falls back to deterministic
        keyword analysis otherwise.

        :param old_text: Original requirement text.
        :param new_text: Updated requirement text.
        :return: (ChangeCategory, delta_description).
        :requirement: URS-24.1
        """
        if self._llm_available and self._llm_client:
            return self._llm_detect_delta(old_text, new_text)
        return self._deterministic_detect_delta(old_text, new_text)

    def _llm_detect_delta(
        self,
        old_text: str,
        new_text: str,
    ) -> Tuple[ChangeCategory, str]:
        """LLM-powered semantic delta detection via Claude Haiku."""
        prompt = (
            "You are a GxP requirements analyst. Classify the "
            "semantic change between OLD and NEW requirement "
            "text.\n\nOLD: "
            + old_text
            + "\n\nNEW: "
            + new_text
            + "\n\nRespond with JSON only:\n"
            '{"category": "Structural|Behavioural'
            '|Clarification|Regulatory",'
            ' "delta": "<one sentence summary>"}'
        )
        try:
            resp = self._llm_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            import json
            content = resp.content[0].text.strip()
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                cat_str = data.get(
                    "category", "Clarification"
                )
                try:
                    cat = ChangeCategory(cat_str)
                except ValueError:
                    cat = ChangeCategory.CLARIFICATION
                return cat, data.get(
                    "delta", "Change detected."
                )
        except Exception:
            pass
        return self._deterministic_detect_delta(old_text, new_text)

    @staticmethod
    def _deterministic_detect_delta(
        old_text: str,
        new_text: str,
    ) -> Tuple[ChangeCategory, str]:
        """
        Keyword-based delta detection (no LLM required).

        Performs phrase-level matching against keyword sets so
        that multi-word phrases like "21 cfr part 211" are
        correctly detected.

        :requirement: URS-24.1
        """
        old_lower = old_text.lower()
        new_lower = new_text.lower()

        def _phrases_in(text: str, phrases: frozenset) -> set:
            return {p for p in phrases if p in text}

        old_reg = _phrases_in(old_lower, _REGULATORY_KEYWORDS)
        new_reg = _phrases_in(new_lower, _REGULATORY_KEYWORDS)
        added_reg = new_reg - old_reg
        removed_reg = old_reg - new_reg

        if added_reg or removed_reg:
            return (
                ChangeCategory.REGULATORY,
                "Regulatory reference changed: "
                f"added={added_reg}, removed={removed_reg}",
            )

        old_struct = _phrases_in(old_lower, _STRUCTURAL_KEYWORDS)
        new_struct = _phrases_in(new_lower, _STRUCTURAL_KEYWORDS)
        if (new_struct - old_struct) or (old_struct - new_struct):
            return (
                ChangeCategory.STRUCTURAL,
                "Structural change detected: logic, scope, "
                "or threshold modified.",
            )

        old_beh = _phrases_in(old_lower, _BEHAVIOURAL_KEYWORDS)
        new_beh = _phrases_in(new_lower, _BEHAVIOURAL_KEYWORDS)
        if (new_beh - old_beh) or (old_beh - new_beh):
            return (
                ChangeCategory.BEHAVIOURAL,
                "Behavioural change detected: workflow or "
                "process step modified.",
            )

        word_delta = abs(
            len(new_text.split()) - len(old_text.split())
        )
        if word_delta > 20:
            return (
                ChangeCategory.BEHAVIOURAL,
                "Significant text expansion detected.",
            )

        return (
            ChangeCategory.CLARIFICATION,
            "Minor clarification or typographical change.",
        )

    # ----------------------------------------------------------
    # Impact mapping
    # ----------------------------------------------------------

    def map_impact(
        self,
        requirement_id: str,
        change_category: ChangeCategory,
        traceability_matrix: Dict[str, Any],
    ) -> List[ImpactedItem]:
        """
        Find all items linked to *requirement_id* in the
        traceability matrix and score each.

        Falls back to a realistic demo set when the matrix is
        empty, ensuring the UI always has meaningful output.

        :param requirement_id: Root requirement identifier.
        :param change_category: Detected category of change.
        :param traceability_matrix: Trace matrix dict.
        :return: List of ImpactedItem.
        :requirement: URS-24.2
        """
        items: List[ImpactedItem] = []
        linked = traceability_matrix.get(requirement_id, {})
        has_real_data = bool(
            linked.get("test_cases")
            or linked.get("risks")
            or linked.get("regulatory_clauses")
        )

        if has_real_data:
            # Tier 1 — Test Cases
            for tc_id, tc_info in linked.get(
                "test_cases", {}
            ).items():
                sev = self._score_tc(tc_info, change_category)
                items.append(ImpactedItem(
                    item_id=tc_id,
                    item_type="test_case",
                    title=tc_info.get(
                        "title", f"Test Case {tc_id}"
                    ),
                    severity=sev,
                    tier=ImpactTier.TIER_1,
                    reason=self._tc_reason(
                        sev, change_category
                    ),
                    linked_requirement=requirement_id,
                ))

            # Tier 2 — Risks
            for risk_id, risk_info in linked.get(
                "risks", {}
            ).items():
                sev = self._score_risk(
                    risk_info, change_category
                )
                items.append(ImpactedItem(
                    item_id=risk_id,
                    item_type="risk",
                    title=risk_info.get(
                        "title", f"Risk {risk_id}"
                    ),
                    severity=sev,
                    tier=ImpactTier.TIER_2,
                    reason=self._risk_reason(
                        sev, change_category
                    ),
                    linked_requirement=requirement_id,
                ))

            # Tier 2 — Trace Matrix update flag
            if change_category in (
                ChangeCategory.STRUCTURAL,
                ChangeCategory.REGULATORY,
            ):
                items.append(ImpactedItem(
                    item_id="TM-001",
                    item_type="trace_matrix",
                    title=(
                        "Traceability Matrix Update Required"
                    ),
                    severity=RegressionSeverity.YELLOW,
                    tier=ImpactTier.TIER_2,
                    reason=(
                        "Structural or regulatory change "
                        "requires trace matrix review."
                    ),
                    linked_requirement=requirement_id,
                ))

            # Tier 3 — Regulatory Clauses
            for clause_id, clause_info in linked.get(
                "regulatory_clauses", {}
            ).items():
                items.append(ImpactedItem(
                    item_id=clause_id,
                    item_type="regulatory_clause",
                    title=clause_info.get(
                        "title", f"Clause {clause_id}"
                    ),
                    severity=(
                        RegressionSeverity.RED
                        if change_category
                        == ChangeCategory.REGULATORY
                        else RegressionSeverity.YELLOW
                    ),
                    tier=ImpactTier.TIER_3,
                    reason=(
                        "Regulatory reference cited in this "
                        "requirement may be affected."
                    ),
                    linked_requirement=requirement_id,
                ))
        else:
            # No real trace matrix — use demo data
            items = self._demo_impact_items(
                requirement_id, change_category
            )

        return items

    # ----------------------------------------------------------
    # Scoring helpers
    # ----------------------------------------------------------

    @staticmethod
    def _score_tc(
        tc_info: Dict[str, Any],
        category: ChangeCategory,
    ) -> RegressionSeverity:
        if category == ChangeCategory.STRUCTURAL:
            return RegressionSeverity.RED
        if category in (
            ChangeCategory.BEHAVIOURAL,
            ChangeCategory.REGULATORY,
        ):
            return RegressionSeverity.YELLOW
        return RegressionSeverity.GREEN

    @staticmethod
    def _score_risk(
        risk_info: Dict[str, Any],
        category: ChangeCategory,
    ) -> RegressionSeverity:
        risk_level = risk_info.get(
            "risk_level", "medium"
        ).lower()
        if (
            category == ChangeCategory.STRUCTURAL
            and risk_level == "high"
        ):
            return RegressionSeverity.RED
        if category in (
            ChangeCategory.STRUCTURAL,
            ChangeCategory.REGULATORY,
        ):
            return RegressionSeverity.YELLOW
        return RegressionSeverity.GREEN

    @staticmethod
    def _tc_reason(
        severity: RegressionSeverity,
        category: ChangeCategory,
    ) -> str:
        if severity == RegressionSeverity.RED:
            return (
                f"{category.value} change requires full "
                "test case re-execution."
            )
        if severity == RegressionSeverity.YELLOW:
            return (
                f"{category.value} change; review expected "
                "results before execution."
            )
        return "Cosmetic change only; test case remains valid."

    @staticmethod
    def _risk_reason(
        severity: RegressionSeverity,
        category: ChangeCategory,
    ) -> str:
        if severity == RegressionSeverity.RED:
            return (
                "High-risk item linked to a structural change;"
                " risk assessment must be re-run."
            )
        if severity == RegressionSeverity.YELLOW:
            return (
                "Risk may be affected; verify RPN remains valid."
            )
        return "Risk assessment remains unaffected."

    # ----------------------------------------------------------
    # Impact Score (0-100)
    # ----------------------------------------------------------

    @staticmethod
    def _compute_impact_score(
        category: ChangeCategory,
        impacted: List[ImpactedItem],
        red: int,
        yellow: int,
    ) -> int:
        """
        Compute a 0-100 composite impact score.

        Base score per change category reflects inherent risk;
        additional points are added per impacted item and per
        Red-severity finding.

        Scale:
          - CLARIFICATION: base 10  + 2/item  + 3/red
          - BEHAVIOURAL:   base 35  + 3/item  + 5/red
          - STRUCTURAL:    base 55  + 4/item  + 7/red
          - REGULATORY:    base 65  + 4/item  + 8/red

        :requirement: URS-24.5 - Numeric impact score 0-100.
        """
        bases = {
            ChangeCategory.CLARIFICATION: (10, 2, 3),
            ChangeCategory.BEHAVIOURAL:   (35, 3, 5),
            ChangeCategory.STRUCTURAL:    (55, 4, 7),
            ChangeCategory.REGULATORY:    (65, 4, 8),
        }
        base, per_item, per_red = bases.get(
            category, (20, 2, 4)
        )
        score = base + (len(impacted) * per_item) + (
            red * per_red
        )
        return min(100, score)

    # ----------------------------------------------------------
    # Network Graph (D3.js / Force-Graph compatible)
    # ----------------------------------------------------------

    @staticmethod
    def _generate_network_graph(
        requirement_id: str,
        impacted_items: List[ImpactedItem],
    ) -> Dict[str, Any]:
        """
        Build a D3.js force-graph JSON with colour-coded nodes
        and directed edges from the root requirement to each
        impacted item.

        Node schema::

            {
                "id":    "TC-05",
                "label": "TC-05: Verify core functional...",
                "type":  "test_case",
                "color": "#ef4444",
                "size":  16
            }

        Edge schema::

            {
                "source":   "URS-7.1",
                "target":   "TC-05",
                "severity": "Red",
                "color":    "#ef4444"
            }

        :requirement: URS-24.6 - Network graph for visualisation.
        """
        _sev_colour = {
            RegressionSeverity.RED:    "#ef4444",
            RegressionSeverity.YELLOW: "#eab308",
            RegressionSeverity.GREEN:  "#22c55e",
        }
        _type_colour = {
            "test_case":          None,   # uses severity colour
            "risk":               "#f97316",
            "regulatory_clause":  "#a855f7",
            "trace_matrix":       "#64748b",
        }
        _type_size = {
            "test_case":         16,
            "risk":              14,
            "regulatory_clause": 12,
            "trace_matrix":      12,
        }

        nodes: List[Dict[str, Any]] = [
            {
                "id":    requirement_id,
                "label": requirement_id,
                "type":  "requirement",
                "color": "#3b82f6",
                "size":  24,
            }
        ]
        edges: List[Dict[str, Any]] = []

        for item in impacted_items:
            sev_col = _sev_colour.get(
                item.severity, "#94a3b8"
            )
            node_col = (
                _type_colour.get(item.item_type) or sev_col
            )
            short_title = (
                item.title[:40] + "…"
                if len(item.title) > 40
                else item.title
            )
            nodes.append({
                "id":    item.item_id,
                "label": f"{item.item_id}: {short_title}",
                "type":  item.item_type,
                "color": node_col,
                "size":  _type_size.get(item.item_type, 14),
                "severity": item.severity.value,
                "tier": item.tier.value,
            })
            edges.append({
                "source":   requirement_id,
                "target":   item.item_id,
                "severity": item.severity.value,
                "color":    sev_col,
            })

        return {"nodes": nodes, "edges": edges}

    # ----------------------------------------------------------
    # Rationalization Log (Task 4 — Audit Trail of Change)
    # ----------------------------------------------------------

    @staticmethod
    def _generate_rationalization_log(
        requirement_id: str,
        category: ChangeCategory,
        delta: str,
        impacted: List[ImpactedItem],
        red: int,
        yellow: int,
        green: int,
        total_tcs: int,
        time_saved: float,
        impact_score: int,
    ) -> str:
        """
        Generate a natural-language Rationalization Log
        explaining every Sentinel decision.

        :requirement: URS-24.7 - Rationalization Log per scan.
        """
        lines: List[str] = []

        lines.append(
            f"EVOLV Sentinel analysed requirement "
            f"'{requirement_id}' — {delta}"
        )
        lines.append("")

        # Severity breakdown
        lines.append("Impact Summary:")
        red_items = [
            i for i in impacted
            if i.severity == RegressionSeverity.RED
        ]
        yellow_items = [
            i for i in impacted
            if i.severity == RegressionSeverity.YELLOW
        ]
        green_items = [
            i for i in impacted
            if i.severity == RegressionSeverity.GREEN
        ]

        if red_items:
            ids = ", ".join(i.item_id for i in red_items)
            lines.append(
                f"  • {red} item(s) flagged CRITICAL RERUN "
                f"[{ids}]"
            )
            for i in red_items:
                lines.append(f"      – {i.title}: {i.reason}")

        if yellow_items:
            ids = ", ".join(i.item_id for i in yellow_items)
            lines.append(
                f"  • {yellow} item(s) flagged REVIEW ADVISED "
                f"[{ids}]"
            )
            for i in yellow_items:
                lines.append(f"      – {i.title}: {i.reason}")

        if green_items:
            ids = ", ".join(i.item_id for i in green_items)
            lines.append(
                f"  • {green} item(s) rerouted to HEALTHY "
                f"[{ids}]"
            )

        lines.append("")

        # Regulatory basis
        _reg_basis = {
            ChangeCategory.STRUCTURAL: (
                "Any structural change to a GxP-regulated "
                "requirement demands complete re-verification "
                "of the linked test suite to maintain "
                "compliance with 21 CFR Part 11 §11.10 and "
                "GAMP 5 validation lifecycle principles."
            ),
            ChangeCategory.REGULATORY: (
                "A change to the regulatory reference requires "
                "re-assessment of all linked test cases and "
                "risk items to confirm the new regulation's "
                "requirements are met (21 CFR Part 11 §11.50)."
            ),
            ChangeCategory.BEHAVIOURAL: (
                "A behavioural change may affect workflow "
                "paths tested by linked test cases; review "
                "is required before re-execution per GAMP 5 "
                "Category 4/5 validation guidance."
            ),
            ChangeCategory.CLARIFICATION: (
                "The change is assessed as cosmetic / "
                "clarification only. Linked test cases remain "
                "valid per GAMP 5 risk-based testing "
                "principles; no re-execution required."
            ),
        }
        lines.append("Regulatory Basis:")
        lines.append(
            "  " + _reg_basis.get(
                category, "Standard GxP review required."
            )
        )
        lines.append("")

        # Time optimisation
        full_h = (total_tcs * 30) / 60
        opt_h = ((red + yellow) * 30) / 60
        lines.append("Time Optimisation:")
        lines.append(
            f"  Full regression: {total_tcs} test case(s) "
            f"× 30 min = {full_h:.1f}h"
        )
        lines.append(
            f"  Optimised suite: {red + yellow} item(s) "
            f"× 30 min = {opt_h:.1f}h"
        )
        if time_saved > 0:
            lines.append(
                f"  Sentinel saves an estimated "
                f"{time_saved:.1f}h vs. unguided regression."
            )
        else:
            lines.append(
                "  Full regression required — no time saving "
                "achievable for this change category."
            )
        lines.append("")

        # Confidence
        confidence = (
            "HIGH" if impact_score >= 60
            else "MEDIUM" if impact_score >= 30
            else "LOW"
        )
        lines.append(
            f"Sentinel Impact Score: {impact_score}/100 | "
            f"Confidence: {confidence}"
        )

        return "\n".join(lines)

    # ----------------------------------------------------------
    # Time-saved calculation
    # ----------------------------------------------------------

    def _calculate_time_saved(
        self,
        red: int,
        yellow: int,
        total: int,
    ) -> float:
        """
        Estimate hours saved vs. a full regression suite.

        Assumes each test case takes ``_TC_MINUTES`` minutes in a
        full manual run.  Optimised suite = red + yellow only.

        :requirement: URS-24.4
        """
        if total == 0:
            return 0.0
        full_hours = (total * self._TC_MINUTES) / 60.0
        optimised = (red + yellow) * self._TC_MINUTES / 60.0
        return max(0.0, full_hours - optimised)

    # ----------------------------------------------------------
    # Blast Radius JSON builder
    # ----------------------------------------------------------

    @staticmethod
    def _build_blast_radius_json(
        requirement_id: str,
        impacted_items: List[ImpactedItem],
    ) -> Dict[str, Any]:
        """
        Build the nested tiered blast-radius JSON.

        Output shape::

            {
                "root": "URS-7.1",
                "impact_tier_1": ["TC-05", "TC-06"],
                "impact_tier_2": ["RISK-02", "TM-001"],
                "impact_tier_3": ["REG-21CFR-211"]
            }

        :requirement: URS-24.2
        """
        return {
            "root": requirement_id,
            "impact_tier_1": [
                i.item_id for i in impacted_items
                if i.tier == ImpactTier.TIER_1
            ],
            "impact_tier_2": [
                i.item_id for i in impacted_items
                if i.tier == ImpactTier.TIER_2
            ],
            "impact_tier_3": [
                i.item_id for i in impacted_items
                if i.tier == ImpactTier.TIER_3
            ],
        }

    # ----------------------------------------------------------
    # Demo fallback
    # ----------------------------------------------------------

    @staticmethod
    def _demo_impact_items(
        requirement_id: str,
        category: ChangeCategory,
    ) -> List[ImpactedItem]:
        """
        Return a realistic demo set when no trace matrix exists.

        Used for UI demos and CI environments without a live
        traceability store.
        """
        structural = category == ChangeCategory.STRUCTURAL
        regulatory = category == ChangeCategory.REGULATORY

        return [
            ImpactedItem(
                item_id="TC-05",
                item_type="test_case",
                title="Verify core functional behaviour",
                severity=(
                    RegressionSeverity.RED
                    if structural
                    else RegressionSeverity.YELLOW
                ),
                tier=ImpactTier.TIER_1,
                reason="Directly tests the changed requirement.",
                linked_requirement=requirement_id,
            ),
            ImpactedItem(
                item_id="TC-06",
                item_type="test_case",
                title="Verify boundary conditions",
                severity=(
                    RegressionSeverity.RED
                    if structural
                    else RegressionSeverity.GREEN
                ),
                tier=ImpactTier.TIER_1,
                reason=(
                    "Boundary tests may be invalidated by "
                    "logic change."
                    if structural
                    else "Not affected by clarification."
                ),
                linked_requirement=requirement_id,
            ),
            ImpactedItem(
                item_id="TC-09",
                item_type="test_case",
                title="End-to-end UAT workflow",
                severity=RegressionSeverity.YELLOW,
                tier=ImpactTier.TIER_1,
                reason=(
                    "Downstream UAT flow references this "
                    "requirement."
                ),
                linked_requirement=requirement_id,
            ),
            ImpactedItem(
                item_id="RISK-02",
                item_type="risk",
                title="Data integrity risk",
                severity=(
                    RegressionSeverity.RED
                    if structural
                    else RegressionSeverity.GREEN
                ),
                tier=ImpactTier.TIER_2,
                reason=(
                    "Structural change may alter risk profile."
                    if structural
                    else "Risk unchanged by clarification."
                ),
                linked_requirement=requirement_id,
            ),
            ImpactedItem(
                item_id="TM-001",
                item_type="trace_matrix",
                title="Traceability Matrix Update Required",
                severity=RegressionSeverity.YELLOW,
                tier=ImpactTier.TIER_2,
                reason=(
                    "Trace matrix must reflect requirement "
                    "version change."
                ),
                linked_requirement=requirement_id,
            ),
            ImpactedItem(
                item_id="REG-21CFR-211",
                item_type="regulatory_clause",
                title="21 CFR Part 211 — Batch Records",
                severity=(
                    RegressionSeverity.RED
                    if regulatory
                    else RegressionSeverity.GREEN
                ),
                tier=ImpactTier.TIER_3,
                reason=(
                    "Regulatory reference cited in requirement."
                ),
                linked_requirement=requirement_id,
            ),
        ]
