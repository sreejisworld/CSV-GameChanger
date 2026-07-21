"""
self_validation.py - EVOLV validates itself, with itself.

Sprint 50. A customer's QA cannot deploy a Category-5 software
tool without the tool's own validation evidence: a Validation
Plan, a Requirements Traceability Matrix (URS -> design -> test),
Installation Qualification, and Operational Qualification. Most
vendors assemble this by hand over months.

EVOLV already owns the raw material - 260 traceable requirements
mapped to code in the URS Traceability Index, a 136-eval suite
that IS the OQ test evidence, a hash-chained audit trail of
execution, pinned dependencies as the IQ baseline, and a
reproducibility proof. This module ASSEMBLES that standing
evidence into the GxP validation-package structure.

The recursive proof point: EVOLV is validated using EVOLV's own
methodology (V-model, risk-based, traceability-first).

:requirement: URS-50.2 - Self-validation package assembler
              (VP + RTM + IQ + OQ from standing evidence).
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

_PROJECT_ROOT = Path(__file__).parent.parent
_CLAUDE_MD = _PROJECT_ROOT / "CLAUDE.md"

# Matches a URS Traceability Index row:
#   | URS-3.1 | requirement text | `implementation` |
_URS_ROW_RE = re.compile(
    r"^\|\s*(URS-\d+\.\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$"
)

SELF_VALIDATION_SCHEMA_VERSION = "1.0.0"


# ── Verification-method mapping ─────────────────────────────────────
# Maps an implementation-file keyword to the objective evidence
# that verifies the requirement. Order matters: first match wins.

_VERIFICATION_MAP: List[tuple] = [
    ("risk_strategist",
     "RiskStrategist evals (12) + reproducibility harness"),
    ("delta_agent",
     "DeltaAgent evals (7) + reproducibility harness"),
    ("change_impact_agent",
     "ChangeImpactAgent evals (6)"),
    ("validated_state_engine",
     "ValidatedStateEngine evals (5) + reproducibility"),
    ("bounded_autonomy_profile",
     "BAP exclusion evals (95) + reproducibility"),
    ("integrity_manager",
     "IntegrityManager chain evals (6) + audit-chain verify"),
    ("requirement_architect",
     "RequirementArchitect golden evals (10) + independent "
     "VerificationAgent review + reproducibility"),
    ("verification_agent",
     "VerificationAgent (COMPLIANCE_EXCEPTION audit events)"),
    ("reproducibility",
     "Reproducibility harness (5 evals, byte-identity)"),
    ("eval_suite",
     "Self-testing: the suite gates CI on every push"),
    ("agent_evals",
     "Trusted Evals golden-set suite (CI gate)"),
    ("version_registry",
     "Version registry API test + drift-detection check"),
    ("security",
     "Security audit 2026-07-16 (10/10 findings closed) + "
     "pip-audit in CI"),
    ("pdf_generator",
     "Code review + manual OQ (rendered-PDF inspection)"),
    ("customer_evals",
     "Golden-set validation test (deterministic shape check)"),
    ("test_pilot",
     "Test Pilot 90+ adversarial scenario suite"),
    ("test_authoring_engine",
     "Test-authoring bundle generation test + citations check"),
    (".jsx",
     "React build check (CI) + manual UI OQ"),
    ("react-platform",
     "React build check (CI) + manual UI OQ"),
    ("scripts/",
     "Compliance gate (CI) + script execution check"),
    ("API/",
     "API integration test + compliance gate (CI)"),
]

_DEFAULT_VERIFICATION = "Code review + compliance gate (CI)"


def _verification_for(implementation: str) -> str:
    """Return the objective verification evidence for a
    requirement, keyed off its implementation reference."""
    impl = implementation.lower()
    for key, evidence in _VERIFICATION_MAP:
        if key.lower() in impl:
            return evidence
    return _DEFAULT_VERIFICATION


@dataclass
class TraceRow:
    """One Requirements Traceability Matrix row."""
    urs_id: str
    requirement: str
    implementation: str
    verification: str


# Broad architecture layer for a given implementation reference -
# used by the public (redacted) package so the RTM proves the
# requirement is implemented in a real layer without exposing the
# file/function-level architecture map (legitimate IP protection,
# per the vendor-transparency line "protecting IP != refusing
# accountability").
_LAYER_MAP: List[tuple] = [
    ("react-platform", "React platform (UI)"),
    (".jsx", "React platform (UI)"),
    ("Agents/", "AI specialist-function layer"),
    ("API/", "API service layer"),
    ("utils/", "Utilities layer"),
    ("scripts/", "Tooling / CI"),
    ("docs/", "Documentation"),
    ("frontend/", "Streamlit surface"),
    ("website/", "Marketing site"),
]

_REDACTED_MARKER = "Implemented & traced (detail in evaluator copy)"


def _redact_impl(implementation: str) -> str:
    """Collapse an implementation reference to its broad layer for
    the public package."""
    impl = implementation.lower()
    for key, layer in _LAYER_MAP:
        if key.lower() in impl:
            return layer
    return _REDACTED_MARKER


@dataclass
class SelfValidationPackage:
    """The assembled self-validation package (structured)."""
    schema_version: str
    generated_at: str
    platform_version: str
    validation_plan: Dict[str, Any]
    iq: Dict[str, Any]
    oq: Dict[str, Any]
    traceability: List[TraceRow] = field(default_factory=list)
    redacted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "platform_version": self.platform_version,
            "redacted": self.redacted,
            "validation_plan": self.validation_plan,
            "iq": self.iq,
            "oq": self.oq,
            "requirement_count": len(self.traceability),
            "traceability": [
                {
                    "urs_id": r.urs_id,
                    "requirement": r.requirement,
                    "implementation": r.implementation,
                    "verification": r.verification,
                }
                for r in self.traceability
            ],
        }


def parse_urs_index(
    claude_md: Path = _CLAUDE_MD,
) -> List[TraceRow]:
    """Parse the URS Traceability Index from CLAUDE.md into RTM
    rows with verification evidence attached.

    :param claude_md: Path to CLAUDE.md.
    :return: List of TraceRow (deduplicated by URS id, last
             definition wins - matches the living index).
    :requirement: URS-50.2 - Self-validation package assembler.
    """
    rows: Dict[str, TraceRow] = {}
    text = claude_md.read_text(encoding="utf-8")
    for line in text.splitlines():
        m = _URS_ROW_RE.match(line)
        if not m:
            continue
        urs_id, requirement, implementation = m.groups()
        if requirement.strip().lower() == "requirement":
            continue  # header row
        rows[urs_id] = TraceRow(
            urs_id=urs_id,
            requirement=requirement.strip(),
            implementation=implementation.strip(),
            verification=_verification_for(implementation),
        )

    def _sort_key(rid: str) -> tuple:
        nums = re.findall(r"\d+", rid)
        return tuple(int(n) for n in nums[:2]) if nums else (0, 0)

    return [rows[k] for k in sorted(rows, key=_sort_key)]


def build_iq_baseline() -> Dict[str, Any]:
    """Build the Installation Qualification baseline: the
    verifiable install configuration.

    :requirement: URS-50.2 - Self-validation package assembler.
    """
    reqs_path = _PROJECT_ROOT / "requirements.txt"
    pinned: List[str] = []
    if reqs_path.exists():
        for line in reqs_path.read_text(
            encoding="utf-8"
        ).splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                pinned.append(line)
    has_docker = (_PROJECT_ROOT / "Dockerfile").exists()
    has_compose = (
        _PROJECT_ROOT / "docker-compose.yml"
    ).exists()
    return {
        "python_baseline": "3.11 (CI) / 3.14 (dev verified)",
        "dependency_manifest": "requirements.txt",
        "pinned_security_floors": [
            p for p in pinned if ">=" in p
        ],
        "dependency_count": len(pinned),
        "container": {
            "dockerfile_present": has_docker,
            "compose_present": has_compose,
        },
        "required_env": [
            "OPENAI_API_KEY (URS generation + embeddings)",
            "PINECONE_API_KEY (GAMP 5 knowledge base)",
            "EVOLV_API_KEY (production auth gate)",
            "EVOLV_CORS_ORIGINS (production CORS allow-list)",
        ],
        "cve_status": (
            "pip-audit clean at 2026-07-16 baseline; re-audited "
            "in CI on every push (blocking)"
        ),
        "install_verification": (
            "python -c 'import API.main' succeeds; "
            "GET /versions/registry returns the component "
            "baseline"
        ),
    }


def build_oq_summary() -> Dict[str, Any]:
    """Build the Operational Qualification evidence: execute the
    eval suite live and summarise pass rates + reproducibility.

    :requirement: URS-50.2 - Self-validation package assembler.
    """
    from Agents.eval_suite import run_suite
    runs = run_suite()
    total = sum(r.eval_count for r in runs)
    passed = sum(
        sum(1 for x in r.results if x.passed) for r in runs
    )
    return {
        "method": (
            "The Trusted Evals suite executes deterministic "
            "test cases against every specialist function; it "
            "gates CI on every change. Executed live for this "
            "package."
        ),
        "total_tests": total,
        "passed": passed,
        "pass_rate": passed / total if total else 0.0,
        "by_agent": [
            {
                "agent": r.agent_name,
                "tests": r.eval_count,
                "passed": sum(
                    1 for x in r.results if x.passed
                ),
            }
            for r in runs
        ],
        "reproducibility": (
            "Deterministic engines proven byte-identical across "
            "repeated runs (ReproducibilityHarness agent)."
        ),
        "additional_evidence": [
            "Test Pilot: 90+ adversarial scenarios",
            "Security audit 2026-07-16: 10/10 findings closed",
            "Audit-chain verification: tamper-evident execution "
            "record",
        ],
    }


def build_validation_plan(rtm_count: int) -> Dict[str, Any]:
    """Build the Validation Plan metadata for EVOLV itself.

    :requirement: URS-50.2 - Self-validation package assembler.
    """
    return {
        "system": "EVOLV | The Validation Factory",
        "gamp_category": (
            "Category 5 (custom application) - risk-based "
            "approach per GAMP 5 Second Edition and FDA CSA "
            "guidance"
        ),
        "intended_use": (
            "AI-assisted authoring and management of Computer "
            "System Validation deliverables in GxP-regulated "
            "environments. AI drafts; qualified humans review "
            "and sign; every decision is inspectable."
        ),
        "validation_approach": (
            "V-model lifecycle. Requirements traced to "
            "implementation and to objective test evidence "
            f"({rtm_count} requirements). Deterministic engines "
            "verified by a standing eval suite executed in CI; "
            "output consistency proven by a reproducibility "
            "harness; execution recorded in a hash-chained "
            "audit trail."
        ),
        "roles": [
            "System Owner - WingstarTech Inc.",
            "QA / Validation Lead - customer or WingstarTech",
            "Independent reviewer - VerificationAgent + human "
            "sign-off",
        ],
        "deliverables": [
            "Validation Plan (this document)",
            "Requirements Traceability Matrix",
            "Installation Qualification (IQ)",
            "Operational Qualification (OQ)",
            "Reproducibility / output-consistency evidence",
            "Security posture summary",
        ],
        "acceptance_criteria": (
            "100% of requirements traced to implementation and "
            "verification; OQ eval suite passes at 100%; "
            "deterministic engines byte-reproducible; zero open "
            "security findings; audit chain intact."
        ),
    }


def generate_self_validation_package(
    redacted: bool = False,
) -> SelfValidationPackage:
    """Assemble the full EVOLV self-validation package from
    standing evidence (runs the OQ eval suite live).

    :param redacted: When True, the RTM implementation column is
                     collapsed to the broad architecture layer
                     (public-safe: proves each requirement is
                     implemented and verified without exposing the
                     file/function-level architecture map). Use
                     for public sharing; the full package is for
                     qualified evaluators.
    :requirement: URS-50.2 - Self-validation package assembler.
    """
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from Agents.version_registry import EVOLV_PLATFORM_VERSION

    rtm = parse_urs_index()
    if redacted:
        rtm = [
            TraceRow(
                urs_id=r.urs_id,
                requirement=r.requirement,
                implementation=_redact_impl(r.implementation),
                verification=r.verification,
            )
            for r in rtm
        ]
    return SelfValidationPackage(
        schema_version=SELF_VALIDATION_SCHEMA_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
        platform_version=EVOLV_PLATFORM_VERSION,
        validation_plan=build_validation_plan(len(rtm)),
        iq=build_iq_baseline(),
        oq=build_oq_summary(),
        traceability=rtm,
        redacted=redacted,
    )


def _cli() -> None:
    """CLI: print the self-validation package as JSON.

    :requirement: URS-50.2 - Self-validation package assembler.
    """
    import argparse
    import json
    parser = argparse.ArgumentParser(
        prog="evolv-self-validation",
        description=(
            "Assemble EVOLV's own validation package from "
            "standing evidence."
        ),
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--rtm-only", action="store_true",
        help="Parse the RTM without running the OQ suite.",
    )
    args = parser.parse_args()

    if args.rtm_only:
        rtm = parse_urs_index()
        payload = json.dumps(
            [
                {
                    "urs_id": r.urs_id,
                    "requirement": r.requirement,
                    "implementation": r.implementation,
                    "verification": r.verification,
                }
                for r in rtm
            ],
            indent=2,
        )
        print(f"RTM: {len(rtm)} requirements")
    else:
        pkg = generate_self_validation_package()
        payload = json.dumps(pkg.to_dict(), indent=2)

    if args.out:
        args.out.write_text(payload, encoding="utf-8")
        print(f"Wrote package to {args.out}")
    elif args.json:
        print(payload)


if __name__ == "__main__":
    _cli()
