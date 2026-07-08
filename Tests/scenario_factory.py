"""
scenario_factory.py - Deterministic variation generator for
Test Pilot scenarios.

Given a seed statement and a category, produces N unique
variations by swapping words from parallel wordlists. NO LLM
tokens consumed - all pure Python templating.

Deterministic: same seed + n yields the same output every time,
so test runs are reproducible.

:requirement: URS-41.4 - Deterministic test scenario factory.
"""
from __future__ import annotations

import itertools
import random
from typing import Any, Dict, List, Optional, Tuple

from Tests.scenarios.bap_scenarios import BAPScenario
from Tests.scenarios.vse_scenarios import VSEScenario, all_vse_scenarios
from Tests.scenarios.drift_scenarios import DriftScenario, all_drift_scenarios


# ─── Word banks (all mutually substitutable within a class) ─────

_AI_SUBJECT = [
    "AI",
    "the AI",
    "our AI",
    "the AI system",
    "our AI system",
    "the AI model",
    "the LLM",
    "the model",
    "the AI assistant",
    "the generative AI",
]

_SIGN_VERB = [
    "signs",
    "will sign",
    "automatically signs",
    "executes signing on",
    "puts the signature on",
    "authorises",
    "electronically signs",
]

_SIGN_OBJECT = [
    "the electronic signature",
    "electronic signatures",
    "the e-signature",
    "manifestation of signature",
    "the approval signature",
    "the digital signature block",
]

_RELEASE_VERB = [
    "releases",
    "automatically releases",
    "approves the release of",
    "authorises release of",
    "signs off release of",
    "will release",
]

_RELEASE_OBJECT = [
    "the batch",
    "each batch",
    "the lot",
    "each lot",
    "the finished product",
    "the manufactured batches",
]

_CAPA_VERB = [
    "closes",
    "resolves",
    "signs off",
    "auto-closes",
    "marks complete",
    "closes out",
]

_CAPA_OBJECT = [
    "the CAPA",
    "each CAPA",
    "the deviation",
    "the deviation record",
    "the complaint",
    "the investigation",
]

_CLINICAL_VERB = [
    "diagnoses",
    "prescribes",
    "recommends treatment for",
    "sets dosing for",
    "makes clinical decisions for",
    "determines therapy for",
]

_CLINICAL_OBJECT = [
    "the patient",
    "each patient",
    "trial subjects",
    "study participants",
    "patients in the cohort",
]

_VALIDATED_WRITE_VERB = [
    "modifies",
    "updates",
    "alters",
    "writes to",
    "persists changes to",
    "auto-corrects",
]

_VALIDATED_WRITE_OBJECT = [
    "the validated record",
    "each validated record",
    "the GxP record",
    "controlled documents",
    "the batch record",
]

# Safe COU templates
_SAFE_ACTION = [
    "drafts",
    "generates",
    "proposes",
    "writes",
    "recommends",
    "suggests",
]

_SAFE_ARTEFACT = [
    "URS",
    "URs",
    "FRs",
    "test cases",
    "test scripts",
    "risk assessments",
    "SOPs",
    "training materials",
    "validation summaries",
    "audit findings",
]

_SAFE_SYSTEM = [
    "LIMS",
    "eQMS",
    "MES",
    "CTMS",
    "SAP-integrated system",
    "validated data lake",
]

_SAFE_APPROVER = [
    "QA sign-off",
    "the QA reviewer's signature",
    "responsible person approval",
    "QA lead sign-off",
    "the CSV lead's signature",
    "human approval",
]

# BAP-X trigger templates parameterised
_TRIGGER_TEMPLATES: Dict[str, Tuple[List[str], List[str]]] = {
    "EX-1-SIGN":  (_SIGN_VERB, _SIGN_OBJECT),
    "EX-2-RELEASE": (_RELEASE_VERB, _RELEASE_OBJECT),
    "EX-3-CAPA":  (_CAPA_VERB, _CAPA_OBJECT),
    "EX-4-CLINICAL": (_CLINICAL_VERB, _CLINICAL_OBJECT),
    "EX-5-VALIDATED-WRITE": (
        _VALIDATED_WRITE_VERB, _VALIDATED_WRITE_OBJECT,
    ),
}


# ─── Public generator ──────────────────────────────────────────

def generate_exclusion_variants(
    rule_id: str,
    n: int = 10,
    seed: int = 42,
    id_prefix: str = "gen-x",
) -> List[BAPScenario]:
    """Generate N deterministic variations of a BAP-X trigger.

    All should fire the specified rule_id.

    :requirement: URS-41.4 - Deterministic factory.
    """
    if rule_id not in _TRIGGER_TEMPLATES:
        raise ValueError(
            f"Unknown rule_id {rule_id!r}. Known: "
            f"{list(_TRIGGER_TEMPLATES.keys())}"
        )
    verbs, objects = _TRIGGER_TEMPLATES[rule_id]
    rng = random.Random(seed)
    combos = list(itertools.product(_AI_SUBJECT, verbs, objects))
    rng.shuffle(combos)
    combos = combos[:n]
    out: List[BAPScenario] = []
    for i, (subj, verb, obj) in enumerate(combos):
        statement = f"{subj} {verb} {obj}."
        # Make first char uppercase
        statement = statement[0].upper() + statement[1:]
        out.append(BAPScenario(
            scenario_id=f"{id_prefix}-{rule_id.lower()}-{i + 1:03d}",
            category="exclusion",
            endpoint="/bap/check-exclusion",
            input_body={
                "statement":          statement,
                "decision_authority": "AI proposes, human signs",
            },
            expected={
                "would_be_excluded":     True,
                "rules_fired.0.rule_id": rule_id,
            },
            tags=["bap-x", "generated", rule_id.lower()],
            notes=f"Generated variant #{i + 1} of {rule_id}",
        ))
    return out


def generate_safe_variants(
    n: int = 20,
    seed: int = 42,
    id_prefix: str = "gen-safe",
) -> List[BAPScenario]:
    """Generate N safe-COU variations.

    None should fire an exclusion rule.

    :requirement: URS-41.4 - Deterministic factory.
    """
    rng = random.Random(seed)
    combos = list(itertools.product(
        _AI_SUBJECT, _SAFE_ACTION, _SAFE_ARTEFACT,
        _SAFE_SYSTEM, _SAFE_APPROVER,
    ))
    rng.shuffle(combos)
    combos = combos[:n]
    out: List[BAPScenario] = []
    for i, (subj, action, artefact, system, approver) in enumerate(combos):
        statement = (
            f"{subj} {action} {artefact} for a GxP-Direct "
            f"{system} at a customer site; outputs require "
            f"{approver} before being persisted to Vault."
        )
        statement = statement[0].upper() + statement[1:]
        out.append(BAPScenario(
            scenario_id=f"{id_prefix}-{i + 1:03d}",
            category="safe",
            endpoint="/bap/check-exclusion",
            input_body={
                "statement":          statement,
                "decision_authority": "AI proposes, human signs",
            },
            expected={
                "would_be_excluded": False,
            },
            tags=["bap-safe", "generated"],
            notes=f"Generated safe variant #{i + 1}",
        ))
    return out


def generate_all_exclusion_variants(
    per_rule: int = 10,
    seed: int = 42,
) -> List[BAPScenario]:
    """Generate `per_rule` variants across ALL 5 exclusion rules.

    :requirement: URS-41.4 - Full-coverage generator.
    """
    out: List[BAPScenario] = []
    for rule_id in _TRIGGER_TEMPLATES.keys():
        out.extend(generate_exclusion_variants(
            rule_id=rule_id, n=per_rule, seed=seed,
        ))
    return out


def generate_batch(
    category: str,
    n: int = 20,
    seed: int = 42,
) -> List[BAPScenario]:
    """Public single-entry API for the UI.

    category: "exclusion" | "safe" | "adversarial-mix"

    :requirement: URS-41.4 - UI-callable batch generator.
    """
    if category == "exclusion":
        # Distribute across all 5 rules
        per_rule = max(1, n // 5)
        out = generate_all_exclusion_variants(per_rule=per_rule,
                                              seed=seed)
        return out[:n]
    if category == "safe":
        return generate_safe_variants(n=n, seed=seed)
    if category == "adversarial-mix":
        # 50/50 mix
        half = n // 2
        excl = generate_all_exclusion_variants(
            per_rule=max(1, half // 5), seed=seed,
        )
        safe = generate_safe_variants(n=n - half, seed=seed + 1)
        return excl[:half] + safe
    raise ValueError(
        f"Unknown category {category!r}. "
        "Use 'exclusion' | 'safe' | 'adversarial-mix'"
    )


# ─── VSE and Drift scenario support ────────────────────────────


def all_vse_batch() -> List[VSEScenario]:
    """Return all Validated State Engine test scenarios.

    :requirement: URS-37.1 - VSE scenario batch retrieval.
    """
    return all_vse_scenarios()


def all_drift_batch() -> List[DriftScenario]:
    """Return all Regulatory Drift Agent test scenarios.

    :requirement: URS-TBD - Drift scenario batch retrieval.
    """
    return all_drift_scenarios()


def generate_mixed_batch(
    n_bap: int = 20,
    n_vse: int = 10,
    n_drift: int = 5,
    seed: int = 42,
) -> tuple[List[BAPScenario], List[VSEScenario], List[DriftScenario]]:
    """Generate a balanced batch across all three agent types.

    Useful for end-to-end platform validation - tests BAP
    (assurance gate), VSE (continuous demonstration), and
    Drift (regulatory monitoring) in one run.

    :requirement: URS-41.5 - Multi-agent batch generation.
    """
    bap_scenarios = generate_batch("adversarial-mix", n=n_bap,
                                    seed=seed)
    vse_scenarios = all_vse_batch()[:n_vse]
    drift_scenarios = all_drift_batch()[:n_drift]
    return bap_scenarios, vse_scenarios, drift_scenarios
