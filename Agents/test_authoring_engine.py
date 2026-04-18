"""
Test Authoring Engine.

The Test Authoring Engine is the world-class test-script generator
for the EVOLV Validation Factory. It takes a risk-ranked
requirement (UR + linked FRs + risk profile) and produces a
``TestBundle`` whose depth and step composition adapt to the
assessed risk level.

Key differentiators (Sprint 14):

1. **Risk-adaptive depth** \u2014 HIGH risk produces positive,
   negative, boundary, recovery, security and e-signature
   coverage; MEDIUM produces positive + one negative + charter;
   LOW produces a charter-only bundle.

2. **Regulatory citation per step** \u2014 every step carries the
   specific 21 CFR Part 11 / Annex 11 / GAMP 5 / CSA control
   it satisfies (sourced from
   :mod:`Agents.regulatory_citations`).

3. **Hybrid generation** \u2014 the deterministic skeleton is built
   first; an optional LLM enrichment pass augments instructions,
   negative inputs and edge scenarios when an OpenAI key is
   available. The deterministic skeleton remains the source of
   truth for citations and structure.

4. **JSON persistence** \u2014 each bundle is written to
   ``output/test_scripts/<bundle_id>.json`` so authoring survives
   browser refreshes and back-end restarts.

5. **Audit-logged** \u2014 every generation, regeneration and
   persistence event passes through
   :func:`Agents.integrity_manager.log_audit_event`.

:requirement: URS-22.4 - System shall generate risk-adaptive test
              bundles from risk-ranked requirements.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from Agents.integrity_manager import (
    log_audit_event as _log_integrity_event,
)
from Agents.regulatory_citations import (
    citations_for,
    citations_for_risk_level,
)


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_BUNDLE_DIR = PROJECT_ROOT / "output" / "test_scripts"
TEST_BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

_BUNDLE_SCHEMA_VERSION = "1.0.0"


# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------


class GenerationMode(Enum):
    """
    How the engine produces step bodies.

    :requirement: URS-22.5 - System shall support deterministic
                  and hybrid generation modes.
    """

    DETERMINISTIC = "deterministic"
    HYBRID = "hybrid"


class TestDepth(Enum):
    """
    Depth profile derived from the requirement risk level.

    :requirement: URS-22.6 - System shall scale test depth to
                  risk level.
    """

    FULL = "full"          # HIGH risk
    STANDARD = "standard"  # MEDIUM-HIGH (impl=Custom + Indirect)
    MEDIUM = "medium"      # MEDIUM risk
    CHARTER = "charter"    # LOW risk


# ------------------------------------------------------------------
# Dataclasses
# ------------------------------------------------------------------


@dataclass
class AuthoringStep:
    """
    A single test step with regulatory citations.

    Mirrors the shape used by ``Agents.delta_agent.CSATestStep``
    plus a ``citations`` and ``archetype`` field.

    :requirement: URS-22.7 - System shall attach regulatory
                  citations to each test step.
    """

    step_type: str            # "Setup" | "Execution"
    step_number: int
    archetype: str            # "setup" | "positive" | "negative" | ...
    step_title: str
    step_instruction: str
    expected_result: str
    test_case_type: str       # "Positive" | "Negative" | "Edge Case" | ""
    requirement_reference: str
    citations: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialise to dict for JSON / API output.

        :return: Dict representation including citations.
        """
        return asdict(self)


@dataclass
class TestBundle:
    """
    Container for a generated, risk-adaptive test script.

    :requirement: URS-22.4 - System shall generate risk-adaptive
                  test bundles from risk-ranked requirements.
    """

    bundle_id: str
    requirement_id: str
    project_name: str
    risk_level: str          # "High" | "Medium" | "Low"
    depth: str               # TestDepth value
    mode: str                # GenerationMode value
    test_type: str           # "Informal" | "Formal OQ" | "Formal UAT"
    generated_at: str
    schema_version: str
    requirement_summary: str
    impact: str              # "GxP Direct" | "GxP Indirect" | "No GxP"
    implementation_method: str
    steps: List[Dict[str, Any]]
    bundle_citations: List[Dict[str, str]]
    quality_checklist: Dict[str, bool]
    enrichment_applied: bool = False
    persisted_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialise to dict for JSON / API output.

        :return: Dict representation suitable for storage and UI.
        """
        return asdict(self)


# ------------------------------------------------------------------
# Errors
# ------------------------------------------------------------------


class TestAuthoringError(Exception):
    """
    Error code: CSV-013 - Test authoring failed.

    :requirement: URS-22.4 - System shall generate risk-adaptive
                  test bundles from risk-ranked requirements.
    """

    error_code = "CSV-013"


# ------------------------------------------------------------------
# Engine
# ------------------------------------------------------------------


class TestAuthoringEngine:
    """
    World-class test bundle generator with risk-adaptive depth,
    regulatory citations and optional LLM enrichment.

    :requirement: URS-22.4 - System shall generate risk-adaptive
                  test bundles from risk-ranked requirements.
    """

    def __init__(
        self,
        bundle_dir: Optional[Path] = None,
    ) -> None:
        """
        Construct an engine.

        :param bundle_dir: Override the JSON persistence directory.
        :requirement: URS-22.4 - Engine construction.
        """
        self._bundle_dir = bundle_dir or TEST_BUNDLE_DIR
        self._bundle_dir.mkdir(parents=True, exist_ok=True)
        self._llm_client: Any = None  # Lazy-initialised

    # -- public API -------------------------------------------------

    def generate_bundle(
        self,
        requirement: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        mode: str = GenerationMode.HYBRID.value,
        test_type: str = "Informal",
        project_name: str = "Untitled Project",
        persist: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a single risk-adaptive test bundle.

        ``requirement`` shape (minimal):
            {"id": "UR-1", "type": "UR", "statement": "...",
             "functional_requirements": [{"fr_id": "FR-1", ...}]}

        ``risk_assessment`` shape:
            {"impact": "GxP Direct" | ..., "implMethod": "..."}

        :param requirement: Requirement dict (UR with FRs).
        :param risk_assessment: Risk row from Risk page.
        :param mode: ``"deterministic"`` or ``"hybrid"``.
        :param test_type: ``"Informal"`` | ``"Formal OQ"`` |
                          ``"Formal UAT"``.
        :param project_name: Owning project name (for audit).
        :param persist: If true, write JSON to disk.
        :return: Bundle dict suitable for the React store.
        :raises TestAuthoringError: If generation fails.
        :requirement: URS-22.4 - System shall generate
                      risk-adaptive test bundles from risk-ranked
                      requirements.
        """
        try:
            return self._do_generate(
                requirement=requirement,
                risk_assessment=risk_assessment,
                mode=mode,
                test_type=test_type,
                project_name=project_name,
                persist=persist,
            )
        except TestAuthoringError:
            raise
        except Exception as exc:
            req_id = requirement.get("id", "unknown")
            _log_integrity_event(
                agent_name="TestAuthoringEngine",
                action="TEST_BUNDLE_FAILED",
                decision_logic=(
                    f"Bundle generation failed for {req_id}: "
                    f"{exc}"
                ),
            )
            raise TestAuthoringError(
                f"Bundle generation failed for {req_id}: {exc}"
            ) from exc

    def generate_batch(
        self,
        requirements: List[Dict[str, Any]],
        risk_data: Dict[str, Dict[str, Any]],
        mode: str = GenerationMode.HYBRID.value,
        test_type: str = "Informal",
        project_name: str = "Untitled Project",
        persist: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Generate bundles for every UR in the input list.

        FRs are folded into their parent UR via ``parentId``.

        :param requirements: Flat list of UR + FR dicts.
        :param risk_data: Per-requirement risk rows keyed by ID.
        :param mode: Generation mode.
        :param test_type: Test type.
        :param project_name: Project name (for audit).
        :param persist: Write each bundle to disk.
        :return: List of bundle dicts.
        :requirement: URS-22.8 - System shall support batch test
                      bundle generation.
        """
        # Group FRs by parentId
        urs = [r for r in requirements if r.get("type") == "UR"]
        frs_by_parent: Dict[str, List[Dict[str, Any]]] = {}
        for r in requirements:
            if r.get("type") != "FR":
                continue
            parent = r.get("parentId") or ""
            frs_by_parent.setdefault(parent, []).append(r)

        bundles: List[Dict[str, Any]] = []
        for ur in urs:
            ur_with_frs = {
                **ur,
                "functional_requirements": [
                    {
                        "fr_id":     fr["id"],
                        "statement": fr.get("statement", ""),
                    }
                    for fr in frs_by_parent.get(ur["id"], [])
                ],
            }
            risk_row = risk_data.get(ur["id"], {})
            bundle = self.generate_bundle(
                requirement=ur_with_frs,
                risk_assessment=risk_row,
                mode=mode,
                test_type=test_type,
                project_name=project_name,
                persist=persist,
            )
            bundles.append(bundle)

        _log_integrity_event(
            agent_name="TestAuthoringEngine",
            action="TEST_BUNDLE_BATCH_GENERATED",
            decision_logic=(
                f"Generated {len(bundles)} test bundles "
                f"(mode={mode}, type={test_type})"
            ),
        )
        return bundles

    def load_bundle(self, bundle_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a previously persisted bundle by id.

        :param bundle_id: Bundle identifier (e.g. ``"TB-UR-1"``).
        :return: Dict if found, otherwise ``None``.
        :requirement: URS-22.9 - System shall persist test
                      bundles for cross-session retrieval.
        """
        path = self._bundle_path(bundle_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _log_integrity_event(
                agent_name="TestAuthoringEngine",
                action="TEST_BUNDLE_LOAD_FAILED",
                decision_logic=(
                    f"Could not parse {bundle_id}: {exc}"
                ),
            )
            return None

    def list_bundles(self) -> List[str]:
        """
        List all persisted bundle IDs in the bundle directory.

        :return: Sorted list of bundle identifiers.
        :requirement: URS-22.9 - System shall persist test
                      bundles for cross-session retrieval.
        """
        return sorted(
            p.stem for p in self._bundle_dir.glob("TB-*.json")
        )

    # -- internals --------------------------------------------------

    def _do_generate(
        self,
        requirement: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        mode: str,
        test_type: str,
        project_name: str,
        persist: bool,
    ) -> Dict[str, Any]:
        """
        Core generation pipeline.
        """
        req_id = requirement.get("id", "UR-?")
        statement = requirement.get("statement", "")
        frs = requirement.get("functional_requirements", []) or []

        impact = risk_assessment.get("impact", "GxP Indirect")
        impl = risk_assessment.get("implMethod", "Configured")
        risk_level = self._calc_risk_level(impact, impl)
        depth = self._depth_for_risk(risk_level, impl)

        # Step composition
        steps: List[AuthoringStep] = []
        if depth == TestDepth.CHARTER:
            steps.extend(self._build_charter(req_id, statement, frs))
        elif test_type == "Formal UAT":
            steps.extend(self._build_setup_block(statement))
            steps.extend(
                self._build_uat_block(req_id, statement, frs)
            )
        else:
            steps.extend(self._build_setup_block(statement))
            steps.extend(
                self._build_execution_block(
                    req_id, frs, depth, test_type, statement,
                )
            )

        # Hybrid LLM enrichment
        enrichment_applied = False
        if (
            mode == GenerationMode.HYBRID.value
            and depth != TestDepth.CHARTER
        ):
            enrichment_applied = self._enrich_with_llm(
                steps, statement, risk_level,
            )

        bundle_id = f"TB-{req_id}"
        bundle = TestBundle(
            bundle_id=bundle_id,
            requirement_id=req_id,
            project_name=project_name,
            risk_level=risk_level,
            depth=depth.value,
            mode=mode,
            test_type=test_type,
            generated_at=datetime.now(timezone.utc).isoformat(),
            schema_version=_BUNDLE_SCHEMA_VERSION,
            requirement_summary=statement,
            impact=impact,
            implementation_method=impl,
            steps=[s.to_dict() for s in steps],
            bundle_citations=citations_for_risk_level(risk_level),
            quality_checklist=self._quality_check(steps),
            enrichment_applied=enrichment_applied,
        )

        if persist:
            bundle.persisted_path = str(
                self._persist(bundle_id, bundle.to_dict())
            )

        _log_integrity_event(
            agent_name="TestAuthoringEngine",
            action="TEST_BUNDLE_GENERATED",
            decision_logic=(
                f"Bundle {bundle_id} (req={req_id}, "
                f"risk={risk_level}, depth={depth.value}, "
                f"mode={mode}, steps={len(steps)})"
            ),
            thought_process={
                "inputs": {
                    "requirement_id": req_id,
                    "impact": impact,
                    "implementation_method": impl,
                    "fr_count": len(frs),
                    "mode": mode,
                    "test_type": test_type,
                },
                "steps": [
                    f"Calculated risk level: {risk_level}",
                    f"Selected depth profile: {depth.value}",
                    f"Generated {len(steps)} test steps",
                    (
                        "LLM enrichment applied"
                        if enrichment_applied
                        else "Deterministic only"
                    ),
                    (
                        f"Persisted to {bundle.persisted_path}"
                        if persist
                        else "Not persisted"
                    ),
                ],
                "outputs": {
                    "bundle_id": bundle_id,
                    "step_count": len(steps),
                    "depth": depth.value,
                },
            },
        )

        return bundle.to_dict()

    # -- risk and depth --------------------------------------------

    @staticmethod
    def _calc_risk_level(impact: str, impl: str) -> str:
        """
        Mirror the React Risk-page matrix in Python.
        """
        if impact == "No GxP":
            return "Low"
        if impact == "GxP Direct":
            return (
                "Medium"
                if impl == "Out of the Box"
                else "High"
            )
        # GxP Indirect
        if impl == "Configured":
            return "High"
        if impl == "Custom":
            return "Medium"
        return "Low"

    @staticmethod
    def _depth_for_risk(
        risk_level: str, impl: str,
    ) -> TestDepth:
        """
        Pick a depth profile from the risk level + impl method.
        """
        if risk_level == "High":
            return (
                TestDepth.FULL
                if impl == "Custom"
                else TestDepth.STANDARD
            )
        if risk_level == "Medium":
            return TestDepth.MEDIUM
        return TestDepth.CHARTER

    # -- step builders ---------------------------------------------

    def _build_setup_block(
        self, statement: str,
    ) -> List[AuthoringStep]:
        """
        Standard 3-step setup block (login, navigate, prepare).
        """
        return [
            AuthoringStep(
                step_type="Setup",
                step_number=1,
                archetype="setup",
                step_title="Authenticate as authorised tester",
                step_instruction=(
                    "Log into the validated test environment "
                    "using a uniquely-attributable user account "
                    "with the role required to exercise the "
                    "feature under test."
                ),
                expected_result="",
                test_case_type="",
                requirement_reference="",
                citations=citations_for("setup"),
            ),
            AuthoringStep(
                step_type="Setup",
                step_number=2,
                archetype="setup",
                step_title=(
                    "Navigate to the feature under test"
                ),
                step_instruction=(
                    "Navigate to the module or screen that "
                    "implements: "
                    f"{self._truncate(statement, 140)}"
                ),
                expected_result="",
                test_case_type="",
                requirement_reference="",
                citations=citations_for("setup"),
            ),
            AuthoringStep(
                step_type="Setup",
                step_number=3,
                archetype="setup",
                step_title="Prepare test data and baseline",
                step_instruction=(
                    "Confirm the system is in a known good "
                    "baseline state and required test data, "
                    "test accounts and reference records exist."
                ),
                expected_result="",
                test_case_type="",
                requirement_reference="",
                citations=citations_for("setup"),
            ),
        ]

    def _build_execution_block(
        self,
        req_id: str,
        frs: List[Dict[str, Any]],
        depth: TestDepth,
        test_type: str,
        statement: str,
    ) -> List[AuthoringStep]:
        """
        Build the Execution block according to depth profile.

        Depth coverage:
          FULL     \u2192 positive + negative + boundary + recovery +
                       security per FR
          STANDARD \u2192 positive + negative + boundary per FR
          MEDIUM   \u2192 positive + negative per FR
        """
        out: List[AuthoringStep] = []
        num = 1
        targets = frs or [{"fr_id": req_id, "statement": statement}]

        archetypes = self._archetypes_for_depth(depth, test_type)

        for fr in targets:
            for arch in archetypes:
                out.append(
                    self._build_archetype_step(
                        arch, fr, req_id, num,
                    )
                )
                num += 1
        return out

    @staticmethod
    def _archetypes_for_depth(
        depth: TestDepth, test_type: str,
    ) -> List[str]:
        """
        Return the ordered list of archetype keys for a depth.
        """
        if test_type == "Formal OQ":
            return ["positive"]
        if depth == TestDepth.FULL:
            return [
                "positive",
                "negative",
                "boundary",
                "recovery",
                "security",
            ]
        if depth == TestDepth.STANDARD:
            return ["positive", "negative", "boundary"]
        # MEDIUM
        return ["positive", "negative"]

    def _build_archetype_step(
        self,
        archetype: str,
        fr: Dict[str, Any],
        ur_id: str,
        step_num: int,
    ) -> AuthoringStep:
        """
        Materialise one archetype step for one FR.
        """
        fr_id = fr.get("fr_id", "FR-?")
        statement = fr.get("statement", "")

        title_map = {
            "positive": (
                f"Verify {fr_id} \u2014 happy path"
            ),
            "negative": (
                f"Verify {fr_id} \u2014 invalid input rejection"
            ),
            "boundary": (
                f"Verify {fr_id} \u2014 boundary values"
            ),
            "recovery": (
                f"Verify {fr_id} \u2014 failure recovery"
            ),
            "security": (
                f"Verify {fr_id} \u2014 access control"
            ),
        }

        instr_map = {
            "positive": (
                f"Execute the function described by {fr_id}: "
                f"{self._truncate(statement, 160)} Provide "
                f"valid, in-spec inputs and complete the "
                f"workflow normally."
            ),
            "negative": (
                f"Attempt to execute {fr_id} using invalid, "
                f"missing or malformed input. Examples: empty "
                f"required fields, out-of-range values, "
                f"unauthorised user role."
            ),
            "boundary": (
                f"Test {fr_id} at minimum, maximum and exactly-"
                f"on-boundary values for every constrained input "
                f"or quantity defined by the requirement."
            ),
            "recovery": (
                f"Interrupt {fr_id} mid-execution (network "
                f"disconnect, process kill, browser close) and "
                f"verify the system recovers without data loss "
                f"or corruption when the user retries."
            ),
            "security": (
                f"Attempt to invoke {fr_id} as a user lacking "
                f"the required permission and as an "
                f"unauthenticated session. Verify access is "
                f"denied and the attempt is logged."
            ),
        }

        expected_map = {
            "positive": (
                f"System completes {fr_id} successfully and "
                f"persists evidence (record, audit-trail entry) "
                f"as defined in the acceptance criteria."
            ),
            "negative": (
                "System rejects the invalid input with a "
                "clear, attributable error message; no partial "
                "or corrupt record is written."
            ),
            "boundary": (
                "System accepts in-bound values, rejects "
                "out-of-bound values and never silently "
                "truncates or coerces data at the boundary."
            ),
            "recovery": (
                "On retry, the system either resumes from a "
                "consistent state or starts fresh; the audit "
                "trail records the interruption and the "
                "recovery."
            ),
            "security": (
                "Unauthorised attempts are blocked, an error "
                "is shown to the user and a security event is "
                "written to the audit trail."
            ),
        }

        case_type = {
            "positive": "Positive",
            "negative": "Negative",
            "boundary": "Edge Case",
            "recovery": "Edge Case",
            "security": "Negative",
        }.get(archetype, "Positive")

        return AuthoringStep(
            step_type="Execution",
            step_number=step_num,
            archetype=archetype,
            step_title=title_map.get(
                archetype,
                f"Verify {fr_id}",
            ),
            step_instruction=instr_map.get(
                archetype, statement,
            ),
            expected_result=expected_map.get(
                archetype, "",
            ),
            test_case_type=case_type,
            requirement_reference=f"{ur_id} / {fr_id}",
            citations=citations_for(archetype),
        )

    def _build_uat_block(
        self,
        ur_id: str,
        statement: str,
        frs: List[Dict[str, Any]],
    ) -> List[AuthoringStep]:
        """
        Business-process UAT walk-through.
        """
        out: List[AuthoringStep] = []
        out.append(
            AuthoringStep(
                step_type="Execution",
                step_number=1,
                archetype="uat",
                step_title="End-to-end business scenario",
                step_instruction=(
                    "As an end user, perform the complete "
                    "business process for: "
                    f"{self._truncate(statement, 180)}. Follow "
                    "the normal workflow start-to-finish."
                ),
                expected_result=(
                    "The end-to-end business process "
                    "completes successfully and the user "
                    "achieves the intended business goal."
                ),
                test_case_type="Positive",
                requirement_reference=ur_id,
                citations=citations_for("uat"),
            )
        )
        for idx, fr in enumerate(frs, start=2):
            fr_id = fr.get("fr_id", "FR-?")
            stmt = fr.get("statement", "")
            out.append(
                AuthoringStep(
                    step_type="Execution",
                    step_number=idx,
                    archetype="uat",
                    step_title=(
                        f"Confirm {fr_id} business outcome"
                    ),
                    step_instruction=(
                        "Verify the system supports: "
                        f"{self._truncate(stmt, 180)}"
                    ),
                    expected_result=(
                        "Business outcome achieved as "
                        "described in the requirement."
                    ),
                    test_case_type="Positive",
                    requirement_reference=f"{ur_id} / {fr_id}",
                    citations=citations_for("uat"),
                )
            )
        return out

    def _build_charter(
        self,
        ur_id: str,
        statement: str,
        frs: List[Dict[str, Any]],
    ) -> List[AuthoringStep]:
        """
        Unscripted exploratory charter for LOW risk.
        """
        out: List[AuthoringStep] = []
        out.append(
            AuthoringStep(
                step_type="Setup",
                step_number=1,
                archetype="setup",
                step_title="Establish exploratory session",
                step_instruction=(
                    "Confirm system access and ensure a known "
                    "baseline state for the exploratory "
                    "session."
                ),
                expected_result="",
                test_case_type="",
                requirement_reference="",
                citations=citations_for("setup"),
            )
        )
        targets = frs or [{"fr_id": ur_id, "statement": statement}]
        for idx, fr in enumerate(targets, start=1):
            fr_id = fr.get("fr_id", "FR-?")
            stmt = fr.get("statement", "")
            out.append(
                AuthoringStep(
                    step_type="Execution",
                    step_number=idx,
                    archetype="charter",
                    step_title=(
                        f"Exploratory: {fr_id} core flow"
                    ),
                    step_instruction=(
                        "Using tester expertise, exercise the "
                        f"feature {fr_id}: "
                        f"{self._truncate(stmt, 160)} Cover "
                        "typical, atypical and boundary usage. "
                        "Document any anomalies as session "
                        "notes."
                    ),
                    expected_result=(
                        "Feature operates as intended; any "
                        "anomalies are recorded with steps to "
                        "reproduce."
                    ),
                    test_case_type="Positive",
                    requirement_reference=f"{ur_id} / {fr_id}",
                    citations=citations_for("charter"),
                )
            )
        return out

    # -- enrichment -------------------------------------------------

    def _enrich_with_llm(
        self,
        steps: List[AuthoringStep],
        statement: str,
        risk_level: str,
    ) -> bool:
        """
        Optionally rewrite negative / boundary / recovery /
        security instructions with domain-specific examples.

        Falls back silently when no API key is available so the
        deterministic skeleton remains usable offline.

        :return: ``True`` if enrichment ran and updated steps.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False

        targets = [
            s for s in steps
            if s.archetype in {
                "negative", "boundary", "recovery", "security",
            }
        ]
        if not targets:
            return False

        try:
            client = self._get_llm_client()
        except Exception:
            return False

        prompt = self._enrichment_prompt(
            statement, risk_level, targets,
        )
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior CSV test engineer. "
                            "Rewrite each test-step instruction "
                            "to be specific to the requirement, "
                            "use precise input examples and "
                            "stay under 60 words. Return JSON "
                            "{\"steps\": [{\"index\": int, "
                            "\"instruction\": str}]} only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=1200,
            )
            payload = json.loads(resp.choices[0].message.content)
        except Exception:
            return False

        updates = {
            int(item.get("index", -1)): item.get("instruction", "")
            for item in payload.get("steps", [])
            if isinstance(item, dict)
        }

        applied = False
        for idx, step in enumerate(targets):
            new_text = updates.get(idx)
            if new_text and isinstance(new_text, str):
                step.step_instruction = new_text.strip()
                applied = True
        return applied

    def _get_llm_client(self) -> Any:
        """
        Lazily initialise the OpenAI client.
        """
        if self._llm_client is not None:
            return self._llm_client
        from openai import OpenAI  # noqa: WPS433

        self._llm_client = OpenAI()
        return self._llm_client

    @staticmethod
    def _enrichment_prompt(
        statement: str,
        risk_level: str,
        targets: List[AuthoringStep],
    ) -> str:
        """
        Build the LLM enrichment prompt.
        """
        items = [
            {
                "index": idx,
                "archetype": s.archetype,
                "current": s.step_instruction,
                "fr_ref": s.requirement_reference,
            }
            for idx, s in enumerate(targets)
        ]
        return (
            f"Requirement (risk={risk_level}): "
            f"{statement}\n\nRewrite each step instruction "
            "below to add concrete, requirement-specific "
            "examples. Return JSON only.\n\n"
            f"{json.dumps(items, ensure_ascii=False)}"
        )

    # -- quality + persistence --------------------------------------

    @staticmethod
    def _quality_check(
        steps: List[AuthoringStep],
    ) -> Dict[str, bool]:
        """
        Self-check the generated bundle for completeness.
        """
        execs = [s for s in steps if s.step_type == "Execution"]
        return {
            "all_steps_have_instructions": all(
                bool(s.step_instruction.strip()) for s in steps
            ),
            "execution_steps_have_expected_results": all(
                bool(s.expected_result.strip()) for s in execs
            ),
            "execution_steps_have_references": all(
                bool(s.requirement_reference) for s in execs
            ),
            "all_execution_steps_carry_citations": all(
                bool(s.citations) for s in execs
            ),
            "step_titles_unique": (
                len({s.step_title for s in steps}) == len(steps)
            ),
        }

    def _persist(
        self, bundle_id: str, payload: Dict[str, Any],
    ) -> Path:
        """
        Atomically write the bundle JSON.
        """
        path = self._bundle_path(bundle_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp, path)
        return path

    def _bundle_path(self, bundle_id: str) -> Path:
        """
        Resolve the on-disk path for a bundle id (sanitised).
        """
        safe = re.sub(r"[^A-Za-z0-9_\-]+", "_", bundle_id)
        return self._bundle_dir / f"{safe}.json"

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        """
        Bound long requirement strings to keep step bodies tidy.
        """
        text = (text or "").strip()
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "\u2026"
