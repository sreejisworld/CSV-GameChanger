"""
Intelligence Engine — 100x Requirements Intelligence Module.

Provides an LLM-powered intelligence layer over the Requirements Module:
  - Mermaid.js workflow diagram generation from free-text workflow descriptions
  - Requirement categorisation (Functional / Security / Regulatory / etc.)
  - Test Assurance Suggestions aligned to CSA methodology
  - Positive, Negative, and Edge-case Acceptance Criteria per requirement
  - Proactive Gap Finder: highlights workflow steps with no security coverage

:requirement: URS-20.1 - System shall generate intelligence from requirements context.
"""
import os
import re
import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from Agents.integrity_manager import log_audit_event as _log

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_LLM_MODEL = "gpt-4o"

_CATEGORIES: List[str] = [
    "Functional",
    "Security",
    "Regulatory",
    "Data Integrity",
    "Integration",
    "Performance",
    "Audit/Compliance",
    "Non-functional",
]

# CSA methodology: risk level -> test assurance suggestion
_TEST_ASSURANCE_MAP: Dict[str, str] = {
    "High": (
        "Scripted OQ / UAT "
        "(GAMP 5 Cat-5 Rigorous Scripted Testing per CSA risk-based approach)"
    ),
    "Medium": (
        "Hybrid Testing "
        "(Scripted critical paths + Unscripted exploratory per CSA guidance)"
    ),
    "Low": (
        "Unscripted / Ad-hoc "
        "(Exploratory charter per CSA low-risk guidance)"
    ),
}

# High-risk keywords for deterministic fallback
_HIGH_RISK_KEYWORDS = {
    "patient", "safety", "sterile", "batch", "release",
    "audit", "validation", "gxp", "regulatory", "fda",
    "compliance", "traceability", "21 cfr", "adversarial",
    "clinical", "pharmacovigilance",
}

# Medium-risk keywords for deterministic fallback
_MEDIUM_RISK_KEYWORDS = {
    "quality", "capa", "deviation", "change control",
    "training", "document", "temperature", "inventory",
    "calibration", "sop", "report", "export",
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------
@dataclass
class AcceptanceCriteria:
    """Positive, Negative, and Edge acceptance criteria for one requirement.

    :requirement: URS-20.5 - System shall generate acceptance criteria.
    """

    positive: List[str] = field(default_factory=list)
    negative: List[str] = field(default_factory=list)
    edge: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dict."""
        return {
            "positive": self.positive,
            "negative": self.negative,
            "edge": self.edge,
        }


@dataclass
class RequirementIntelligence:
    """Full intelligence profile for a single requirement.

    :requirement: URS-20.3 - System shall produce structured intelligence.
    """

    requirement: str
    category: str
    risk_level: str
    test_assurance: str
    acceptance_criteria: AcceptanceCriteria

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dict."""
        return {
            "requirement": self.requirement,
            "category": self.category,
            "risk_level": self.risk_level,
            "test_assurance": self.test_assurance,
            "acceptance_criteria": self.acceptance_criteria.to_dict(),
        }


@dataclass
class SecurityGap:
    """A gap between a workflow step and the security matrix.

    :requirement: URS-20.6 - System shall identify security gaps.
    """

    step: str
    gap_description: str
    severity: str  # "High" | "Medium"

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dict."""
        return {
            "step": self.step,
            "gap_description": self.gap_description,
            "severity": self.severity,
        }


@dataclass
class IntelligenceResult:
    """Full intelligence output for the Requirements Module.

    :requirement: URS-20.3 - System shall produce full intelligence package.
    """

    mermaid_diagram: str
    workflow_steps: List[str]
    requirements_intelligence: List[RequirementIntelligence]
    security_gaps: List[SecurityGap]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dict."""
        return {
            "mermaid_diagram": self.mermaid_diagram,
            "workflow_steps": self.workflow_steps,
            "requirements_intelligence": [
                r.to_dict() for r in self.requirements_intelligence
            ],
            "security_gaps": [g.to_dict() for g in self.security_gaps],
        }


# ---------------------------------------------------------------------------
# Exception Classes
# ---------------------------------------------------------------------------
class IntelligenceEngineError(Exception):
    """Base error for Intelligence Engine failures.

    Error code: CSV-020.
    """

    error_code = "CSV-020"


# ---------------------------------------------------------------------------
# Intelligence Engine
# ---------------------------------------------------------------------------
class IntelligenceEngine:
    """100x Intelligence Engine — LLM-powered requirements intelligence.

    Orchestrates four intelligence capabilities in a single call:

    1. **Mermaid.js workflow diagram** — converts free-text workflow
       description into a structured, renderable LR flowchart.
    2. **Requirement categorisation + acceptance criteria** — classifies
       each requirement into a GAMP 5-aligned category and generates
       Positive / Negative / Edge acceptance criteria (single batched
       LLM call).
    3. **Test Assurance Suggestions** — deterministic CSA-aligned
       recommendation based on computed risk level.
    4. **Proactive Gap Finder** — cross-references extracted workflow
       steps against the supplied security matrix to surface steps
       with no security coverage.

    Falls back to deterministic logic for every step when the LLM is
    unavailable (no API key or OpenAI package absent).

    :requirement: URS-20.1 - System shall generate intelligence from context.
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = _LLM_MODEL,
    ):
        """Initialise the IntelligenceEngine.

        :param openai_api_key: OpenAI API key (defaults to env var).
        :param model: Chat completion model to use.
        :requirement: URS-20.2 - System shall validate LLM dependencies.
        """
        self._api_key: Optional[str] = (
            openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        self._model: str = model
        self._llm_available: bool = bool(OpenAI and self._api_key)

    # ------------------------------------------------------------------ #
    #  Public entry-point                                                  #
    # ------------------------------------------------------------------ #
    def generate_intelligence(
        self,
        requirements: List[str],
        system_description: str = "",
        workflow_text: str = "",
        security_matrix: Optional[List[Dict[str, Any]]] = None,
    ) -> IntelligenceResult:
        """Generate a full intelligence package for a set of requirements.

        :param requirements: One or more requirement strings to analyse.
        :param system_description: High-level description of the system
            under validation (used as LLM context).
        :param workflow_text: Free-text workflow description (used to
            generate the Mermaid diagram and extract step labels for
            gap analysis).
        :param security_matrix: List of dicts with keys ``step`` and
            ``security_requirements`` (list of strings).
        :return: IntelligenceResult containing diagram, categorised
            requirements, and security gaps.
        :raises IntelligenceEngineError: If no requirements are provided.
        :requirement: URS-20.3 - System shall generate intelligence package.
        """
        if not requirements:
            raise IntelligenceEngineError(
                "At least one requirement must be provided."
            )

        security_matrix = security_matrix or []

        # 1. Mermaid diagram + workflow step extraction
        mermaid_code, workflow_steps = self._generate_mermaid_diagram(
            workflow_text=workflow_text,
            system_description=system_description,
        )

        # 2. Categorise requirements + acceptance criteria (single LLM call)
        intel_rows = self._analyse_requirements(
            requirements=requirements,
            system_description=system_description,
        )

        # 3. Test Assurance Suggestions (deterministic — no LLM needed)
        for row in intel_rows:
            row.test_assurance = _TEST_ASSURANCE_MAP.get(
                row.risk_level, _TEST_ASSURANCE_MAP["Medium"]
            )

        # 4. Proactive Gap Finder
        gaps = self._find_security_gaps(
            workflow_steps=workflow_steps,
            security_matrix=security_matrix,
        )

        result = IntelligenceResult(
            mermaid_diagram=mermaid_code,
            workflow_steps=workflow_steps,
            requirements_intelligence=intel_rows,
            security_gaps=gaps,
        )

        _log(
            agent_name="IntelligenceEngine",
            action="INTELLIGENCE_GENERATED",
            decision_logic=(
                f"Generated intelligence for {len(requirements)} "
                f"requirement(s). Workflow steps: {len(workflow_steps)}. "
                f"Security gaps found: {len(gaps)}."
            ),
        )

        return result

    # ------------------------------------------------------------------ #
    #  Capability 1: Mermaid diagram                                       #
    # ------------------------------------------------------------------ #
    def _generate_mermaid_diagram(
        self,
        workflow_text: str,
        system_description: str,
    ) -> Tuple[str, List[str]]:
        """Generate a Mermaid.js flowchart from workflow_text.

        Returns a placeholder diagram if workflow_text is empty.
        Falls back to a linear chain diagram if the LLM is unavailable.

        :param workflow_text: Free-text workflow description.
        :param system_description: Optional system context for LLM.
        :return: (mermaid_code, list_of_node_labels)
        :requirement: URS-20.4 - System shall generate Mermaid diagram.
        """
        if not workflow_text.strip():
            return self._placeholder_diagram(), []

        if not self._llm_available:
            fallback = self._linear_diagram(workflow_text)
            steps = self._extract_steps_from_text(workflow_text)
            return fallback, steps

        prompt = (
            "You are a software architect writing Mermaid.js diagrams.\n"
            "Generate a Mermaid.js flowchart (flowchart LR) for the workflow "
            "described below.\n\n"
            "Rules:\n"
            "  - Output ONLY the raw Mermaid code. No explanation.\n"
            "  - Do NOT include markdown fences (no ```mermaid or ```).\n"
            "  - First line must be exactly: flowchart LR\n"
            "  - Keep node labels concise (3-6 words max).\n"
            "  - Use short alphanumeric node IDs (A, B, C1, D2, etc.).\n"
            "  - Use --> for arrows.\n"
            "  - Use {Label} for decision diamonds (e.g. C{Valid?}).\n"
            "  - Use ([Label]) for start/end nodes.\n"
            "  - Include decision branches for approval or validation steps.\n"
            "  - Do not exceed 15 nodes.\n\n"
            f"System: {system_description or 'GxP system under validation'}\n\n"
            f"Workflow:\n{workflow_text}"
        )

        try:
            client = OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=800,
            )
            raw: str = response.choices[0].message.content.strip()
            # Strip accidental markdown fences
            raw = re.sub(r"^```(?:mermaid)?\s*", "", raw, flags=re.MULTILINE)
            raw = re.sub(r"\s*```\s*$", "", raw, flags=re.MULTILINE)
            raw = raw.strip()
            if not raw.startswith("flowchart"):
                raw = "flowchart LR\n" + raw
            steps = self._extract_steps_from_mermaid(raw)
            return raw, steps
        except Exception:
            fallback = self._linear_diagram(workflow_text)
            steps = self._extract_steps_from_text(workflow_text)
            return fallback, steps

    # ------------------------------------------------------------------ #
    #  Capability 2: Requirement analysis (category + criteria)           #
    # ------------------------------------------------------------------ #
    def _analyse_requirements(
        self,
        requirements: List[str],
        system_description: str,
    ) -> List[RequirementIntelligence]:
        """Batch-analyse requirements via a single LLM call.

        Returns category, risk level, and Positive/Negative/Edge
        acceptance criteria for each requirement.

        :param requirements: List of requirement strings.
        :param system_description: System context for the LLM.
        :return: List of RequirementIntelligence (test_assurance is empty
            and filled in by the caller).
        :requirement: URS-20.5 - System shall categorise requirements.
        """
        if not self._llm_available:
            return [
                self._fallback_intelligence(r) for r in requirements
            ]

        numbered = "\n".join(
            f"{i + 1}. {r}" for i, r in enumerate(requirements)
        )
        cats = ", ".join(_CATEGORIES)

        prompt = (
            "You are a GAMP 5 / CSA compliance expert reviewing software "
            "requirements for a validated GxP system.\n\n"
            f"System: {system_description or 'GxP system under validation'}\n\n"
            "Return a JSON object with a single key \"requirements\" whose "
            "value is an array. Each array element corresponds to one "
            "numbered requirement below and must have EXACTLY these keys:\n"
            '  "index": <1-based integer matching the requirement number>,\n'
            f'  "category": <one of: {cats}>,\n'
            '  "risk_level": <"High", "Medium", or "Low">,\n'
            '  "acceptance_criteria": {\n'
            '    "positive": [<3 Given/When/Then acceptance statements>],\n'
            '    "negative": [<2 negative/error scenario statements>],\n'
            '    "edge": [<2 boundary or edge-case statements>]\n'
            "  }\n\n"
            "Risk Level classification guidance:\n"
            "  High  — patient safety, GxP direct impact, validated process, "
            "regulatory reporting, audit trail integrity, batch release\n"
            "  Medium — quality assurance, traceability, document control, "
            "training records, CAPA, change control, temperature monitoring\n"
            "  Low   — administrative features, non-GxP convenience, "
            "internal reporting with no regulatory impact\n\n"
            "Output ONLY a valid JSON object. No explanation. No markdown.\n\n"
            f"Requirements:\n{numbered}"
        )

        try:
            client = OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content.strip()
            parsed = json.loads(raw)
            # Unwrap the outer dict to get the list
            items: List[Dict[str, Any]] = []
            if isinstance(parsed, dict):
                for v in parsed.values():
                    if isinstance(v, list):
                        items = v
                        break
            elif isinstance(parsed, list):
                items = parsed
            return self._build_intel_rows(requirements, items)
        except Exception:
            return [
                self._fallback_intelligence(r) for r in requirements
            ]

    def _build_intel_rows(
        self,
        requirements: List[str],
        parsed_items: List[Dict[str, Any]],
    ) -> List[RequirementIntelligence]:
        """Map LLM-parsed items back to RequirementIntelligence objects.

        :param requirements: Original requirement strings (ordered).
        :param parsed_items: LLM output items with index/category/etc.
        :return: One RequirementIntelligence per requirement.
        """
        by_index: Dict[int, Dict[str, Any]] = {
            item.get("index", i + 1): item
            for i, item in enumerate(parsed_items)
        }
        rows: List[RequirementIntelligence] = []
        for i, req in enumerate(requirements):
            item = by_index.get(i + 1, {})
            ac_raw = item.get("acceptance_criteria", {})
            rows.append(
                RequirementIntelligence(
                    requirement=req,
                    category=item.get("category", "Functional"),
                    risk_level=item.get("risk_level", "Medium"),
                    test_assurance="",  # filled by caller
                    acceptance_criteria=AcceptanceCriteria(
                        positive=ac_raw.get("positive", []),
                        negative=ac_raw.get("negative", []),
                        edge=ac_raw.get("edge", []),
                    ),
                )
            )
        return rows

    def _fallback_intelligence(
        self,
        requirement: str,
    ) -> RequirementIntelligence:
        """Deterministic fallback profile when LLM is unavailable.

        :param requirement: Requirement string.
        :return: RequirementIntelligence with keyword-based classification.
        """
        text_lower = requirement.lower()
        if any(kw in text_lower for kw in _HIGH_RISK_KEYWORDS):
            risk = "High"
        elif any(kw in text_lower for kw in _MEDIUM_RISK_KEYWORDS):
            risk = "Medium"
        else:
            risk = "Low"

        stmt = requirement.strip().rstrip(".")
        return RequirementIntelligence(
            requirement=requirement,
            category="Functional",
            risk_level=risk,
            test_assurance=_TEST_ASSURANCE_MAP.get(risk, ""),
            acceptance_criteria=AcceptanceCriteria(
                positive=[
                    f"Given a valid system state, when "
                    f"'{stmt}' is exercised, "
                    "then the system behaves as specified."
                ],
                negative=[
                    f"Given invalid input, when '{stmt}' is attempted, "
                    "then the system returns an appropriate error message."
                ],
                edge=[
                    f"Given a boundary condition, when '{stmt}' is tested "
                    "at its operational limit, "
                    "then the system handles it gracefully without data loss."
                ],
            ),
        )

    # ------------------------------------------------------------------ #
    #  Capability 4: Proactive Gap Finder                                 #
    # ------------------------------------------------------------------ #
    def _find_security_gaps(
        self,
        workflow_steps: List[str],
        security_matrix: List[Dict[str, Any]],
    ) -> List[SecurityGap]:
        """Identify workflow steps with no corresponding security requirement.

        Uses fuzzy substring matching to align step labels with security
        matrix entries.  A step is flagged as a gap when:
          - No matrix entry matches the step label (High severity), or
          - A matching entry exists but its requirements list is empty
            (Medium severity).

        :param workflow_steps: Node labels extracted from the Mermaid code.
        :param security_matrix: List of {step, security_requirements} dicts.
        :return: List of SecurityGap objects.
        :requirement: URS-20.6 - System shall find security gaps in workflow.
        """
        if not workflow_steps:
            return []

        # Build normalised lookup of covered steps
        covered: Dict[str, List[str]] = {}
        for entry in security_matrix:
            raw_step = str(
                entry.get("step", entry.get("Step", ""))
            ).strip()
            reqs = entry.get(
                "security_requirements",
                entry.get("SecurityRequirements", []),
            )
            if raw_step:
                covered[raw_step.lower()] = (
                    reqs if isinstance(reqs, list) else []
                )

        gaps: List[SecurityGap] = []
        for step in workflow_steps:
            step_norm = step.strip().lower()
            # Fuzzy match: covered key is substring of step or vice-versa
            matched_key: Optional[str] = next(
                (
                    k for k in covered
                    if step_norm in k or k in step_norm
                ),
                None,
            )
            if matched_key is None:
                gaps.append(
                    SecurityGap(
                        step=step,
                        gap_description=(
                            f"Workflow step '{step}' has no corresponding "
                            "entry in the security matrix."
                        ),
                        severity="High",
                    )
                )
            elif not covered[matched_key]:
                gaps.append(
                    SecurityGap(
                        step=step,
                        gap_description=(
                            f"Workflow step '{step}' is listed in the "
                            "security matrix but has no security requirements "
                            "defined."
                        ),
                        severity="Medium",
                    )
                )

        return gaps

    # ------------------------------------------------------------------ #
    #  Static helpers                                                      #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _placeholder_diagram() -> str:
        """Return a generic placeholder diagram when no workflow is given."""
        return (
            "flowchart LR\n"
            "    A([Start]) --> B[Input Data]\n"
            "    B --> C{Validate?}\n"
            "    C -- Yes --> D[Process]\n"
            "    C -- No --> E[Reject]\n"
            "    D --> F[Record Audit Trail]\n"
            "    F --> G([End])\n"
            "    style A fill:#4CAF50,color:#fff\n"
            "    style G fill:#4CAF50,color:#fff\n"
            "    style E fill:#f44336,color:#fff"
        )

    @staticmethod
    def _linear_diagram(workflow_text: str) -> str:
        """Build a simple left-to-right chain diagram from workflow_text.

        Used as a deterministic fallback when the LLM is unavailable.

        :param workflow_text: Free-text workflow description.
        :return: Mermaid flowchart LR code string.
        """
        lines = [
            ln.strip(" -\u2022*0123456789.")
            for ln in workflow_text.strip().splitlines()
            if ln.strip()
        ]
        if not lines:
            return IntelligenceEngine._placeholder_diagram()

        # Cap at 12 nodes; sanitise labels for Mermaid
        nodes: List[Tuple[str, str]] = []
        for idx, label in enumerate(lines[:12]):
            safe = re.sub(r'[^a-zA-Z0-9 ]', '', label).strip()[:40]
            nodes.append((f"N{idx}", safe or f"Step {idx + 1}"))

        code = "flowchart LR\n"
        for nid, label in nodes:
            code += f'    {nid}["{label}"]\n'
        for i in range(len(nodes) - 1):
            code += f"    {nodes[i][0]} --> {nodes[i + 1][0]}\n"
        return code

    @staticmethod
    def _extract_steps_from_text(workflow_text: str) -> List[str]:
        """Extract step labels from raw workflow_text lines.

        :param workflow_text: Free-text workflow description.
        :return: List of step label strings.
        """
        steps: List[str] = []
        for line in workflow_text.strip().splitlines():
            label = line.strip(" -\u2022*0123456789.").strip()
            if label:
                steps.append(label)
        return steps[:20]

    @staticmethod
    def _extract_steps_from_mermaid(mermaid_code: str) -> List[str]:
        """Extract human-readable node labels from Mermaid code.

        Handles the common node formats:
          - A[Label]      (rectangle)
          - B{Label}      (diamond)
          - C(Label)      (rounded)
          - D([Label])    (stadium)

        :param mermaid_code: Raw Mermaid flowchart code.
        :return: De-duplicated list of node label strings.
        """
        # Match label content inside brackets/parens/braces
        pattern = re.compile(
            r'\w+\s*'
            r'(?:\(\[|\[\(|\[|\(|\{)'   # opening bracket variants
            r'([^\]\)\}]+)'              # label content
            r'(?:\]\)|\)\]|\]|\)|\})'   # closing bracket variants
        )
        seen: set = set()
        steps: List[str] = []
        for match in pattern.finditer(mermaid_code):
            label = (
                match.group(1)
                .strip()
                .strip('"')
                .strip("'")
            )
            # Exclude style directives and empty matches
            if (
                label
                and len(label) > 1
                and label not in seen
                and not label.startswith("fill:")
            ):
                seen.add(label)
                steps.append(label)
        return steps
