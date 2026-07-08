"""
agent_passports.py — Explicit Permission Envelopes for every
EVOLV specialist function.

Why this module exists
======================
Salim Ismail's ExO 3.0 architecture and Nuno Valério's *Trust
Architecture* both name the same requirement: every agent operating
in a regulated context must carry **machine-readable metadata**
declaring what it is allowed to do, what data it may see, and what
outputs require human signature before propagation.

This is the explicit form of EVOLV's bounded-autonomy principle.
Before this module, the bounds were enforced by code reading. Now
they are an inspectable artifact a pharma QA director can read in
under five minutes and an FDA inspector can ask for by name.

The passport pattern is borrowed from Web3 smart-contract metadata
and from Salim's *"Agent Passport"* description in the ExO 3.0
methodology. Each agent declares:

- **purpose**            — single-sentence statement of intent
- **allowed_actions**    — explicit verbs the agent may perform
- **forbidden_actions**  — explicit verbs the agent must NEVER perform
- **data_classifications_allowed**   — data classes the agent may read
- **data_classifications_forbidden** — data classes the agent must never see
- **requires_human_signoff_on**      — outputs gated on human signature
- **outputs_audited_via**            — audit-event triplet the agent writes
- **rollback_eligible**              — whether outputs can be reverted
- **llm_usage**                      — whether the agent calls an LLM, and if so
                                       the constraint envelope around it

How this is enforced
====================
Today (Sprint 35.7): the passports are declarative documentation.
Every existing agent's code path satisfies its passport because the
passports were authored from the code. Verification is by reading.

Sprint 41 will introduce a runtime `passport_check()` decorator that
gates every agent call against its passport at execution time, with
violations writing a `PASSPORT_VIOLATION` audit event.

:requirement: URS-37.1 - Explicit Permission Envelope per specialist
              function (Salim Ismail ExO 3.0 / Nuno Valério Trust
              Architecture alignment).
:requirement: URS-37.2 - Passport metadata machine-readable and
              surfaceable via API for customer / auditor inspection.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


# Schema version for the passport format itself. Bumping this signals
# a breaking change to consumers (Dev Portal panel, audit exporters,
# customer-side passport readers).
PASSPORT_SCHEMA_VERSION = "1.0.0"


# ── The passports ────────────────────────────────────────────────────
#
# One entry per specialist function. Keys are stable identifiers
# used in audit-event correlation. Adding a new agent requires adding
# its passport here in the same commit as the agent code lands.
#
# Convention: action verbs are snake_case domain verbs ("query_corpus",
# "compute_embedding", "draft_urs"). Data classifications are nouns
# that map 1:1 to data taxonomies pharma customers will recognise.

AGENT_PASSPORTS: Dict[str, Dict[str, Any]] = {

    # ── Phase 2 — Requirements ────────────────────────────────────
    "RequirementArchitect": {
        "version":            "1.0.0",
        "purpose":
            "Draft URS / UR / FR documents from natural-language "
            "requirements, grounded in retrieved regulatory context.",
        "allowed_actions": [
            "query_pinecone_corpus",
            "compute_embedding",
            "call_llm_for_drafting",
            "build_regulatory_rationale",
            "classify_criticality",
            "decompose_into_3cs",
            "split_ur_to_frs",
            "generate_acceptance_criteria",
        ],
        "forbidden_actions": [
            "write_audit_trail",          # IntegrityManager only
            "sign_approval",
            "modify_risk_classification",
            "execute_test_step",
            "lock_test_run",
            "delete_records",
            "modify_audit_chain",
        ],
        "data_classifications_allowed": [
            "regulatory_corpus",
            "customer_sop",
            "project_planData",
            "user_prompt",
            "requirement_meta",
        ],
        "data_classifications_forbidden": [
            "patient_data",
            "audit_trail_raw",
            "signature_secrets",
            "other_customers_tenant_data",
        ],
        "requires_human_signoff_on": [
            "urs_publish_to_pdf",
            "promotion_to_test_authoring",
        ],
        "outputs_audited_via":
            "log_audit_event(action='URS_GENERATED'), Logic Archive written",
        "rollback_eligible":  True,
        "llm_usage": {
            "calls_llm":               True,
            "llm_purpose":             "language generation, grounded by RAG context",
            "max_context_chunks":      5,
            "must_cite_sources":       True,
            "verification_required":   True,   # → VerificationAgent post-hoc
        },
    },

    "VerificationAgent": {
        "version":            "1.0.0",
        "purpose":
            "Independently re-check every AI-generated artifact "
            "against the regulatory corpus. Reject hallucinations "
            "and log Compliance Exceptions.",
        "allowed_actions": [
            "query_pinecone_corpus",
            "compute_embedding",
            "check_criticality_alignment",
            "check_rationale_relevance",
            "check_contradictions",
            "raise_compliance_exception",
        ],
        "forbidden_actions": [
            "draft_new_urs",
            "modify_existing_urs",
            "sign_approval",
            "modify_risk_classification",
            "execute_test_step",
        ],
        "data_classifications_allowed": [
            "regulatory_corpus",
            "urs_output_under_review",
            "project_planData",
        ],
        "data_classifications_forbidden": [
            "patient_data",
            "signature_secrets",
            "other_customers_tenant_data",
        ],
        "requires_human_signoff_on":  [],   # advisory only — never gates user
        "outputs_audited_via":
            "log_audit_event(action='URS_VERIFIED' | "
            "'COMPLIANCE_EXCEPTION')",
        "rollback_eligible":  False,         # verification is read-only
        "llm_usage": {
            "calls_llm":               False,
            "llm_purpose":             None,
        },
    },

    # ── Phase 3 — Risk ────────────────────────────────────────────
    "RiskStrategist": {
        "version":            "1.0.0",
        "purpose":
            "Compute GAMP 5 risk classification (RPN, risk level, "
            "CSA testing strategy) deterministically from impact + "
            "implementation method.",
        "allowed_actions": [
            "calculate_risk_score",
            "determine_risk_level",
            "get_csa_testing_strategy",
            "map_criticality_to_severity",
            "map_change_type_to_occurrence",
            "assess_change_request",
        ],
        "forbidden_actions": [
            "draft_urs",
            "execute_test_step",
            "sign_approval",
            "write_audit_trail",
            "call_llm",
        ],
        "data_classifications_allowed": [
            "project_planData",
            "requirement_meta",
            "risk_inputs",
        ],
        "data_classifications_forbidden": [
            "patient_data",
            "audit_trail_raw",
            "signature_secrets",
        ],
        "requires_human_signoff_on": [
            "risk_acceptance_high_risk",
        ],
        "outputs_audited_via":
            "log_audit_event(action='RISK_ASSESSMENT_COMPLETED')",
        "rollback_eligible":  True,
        "llm_usage": {
            "calls_llm":               False,
            "llm_purpose":             None,
        },
    },

    # ── Phase 4 — Design / Test Authoring ─────────────────────────
    "DeltaAgent": {
        "version":            "1.0.0",
        "purpose":
            "Generate risk-adaptive CSA test scripts and test bundles "
            "with regulatory citations per step.",
        "allowed_actions": [
            "determine_testing_strategy",
            "build_setup_steps",
            "build_execution_steps",
            "build_uat_steps",
            "build_charter_steps",
            "attach_regulatory_citations",
            "build_quality_checklist",
        ],
        "forbidden_actions": [
            "draft_urs",
            "execute_test_step",
            "sign_approval",
            "modify_risk_classification",
            "promote_bundle_to_script_without_user_action",
        ],
        "data_classifications_allowed": [
            "ur_fr_documents",
            "regulatory_corpus",
            "project_planData",
            "risk_inputs",
        ],
        "data_classifications_forbidden": [
            "patient_data",
            "audit_trail_raw",
            "signature_secrets",
            "other_customers_tenant_data",
        ],
        "requires_human_signoff_on": [
            "promotion_to_runnable_script",
            "manual_step_edits",
        ],
        "outputs_audited_via":
            "log_audit_event(action='CSA_TEST_SCRIPT_GENERATED' | "
            "'CSA_TEST_CHARTER_GENERATED')",
        "rollback_eligible":  True,
        "llm_usage": {
            "calls_llm":               True,
            "llm_purpose":             "hybrid enrichment of deterministic templates",
            "max_context_chunks":      5,
            "must_cite_sources":       True,
            "verification_required":   False,   # citations validated by code
        },
    },

    # ── Phase 7 — Monitor (Sprint 36) ─────────────────────────────
    "ChangeImpactAgent": {
        "version":            "1.0.0",      # shipped in Sprint 36 (2026-06-02)
        "purpose":
            "Given a Change Request and an active project, identify "
            "the URs / FRs / test bundles affected, compute risk "
            "delta, and propose a Change Impact Assessment for QA "
            "review.",
        "allowed_actions": [
            "query_pinecone_corpus",
            "compute_embedding",
            "match_cr_to_urs_via_similarity",
            "compute_risk_delta",
            "identify_affected_bundles",
            "identify_invalidated_approvals",
            "draft_cia_document",
        ],
        "forbidden_actions": [
            "sign_ccr",                   # human QA only
            "trigger_revalidation",       # only after signed CCR
            "modify_existing_urs",
            "modify_risk_classification",
            "execute_test_step",
            "modify_audit_chain",
        ],
        "data_classifications_allowed": [
            "cr_text",
            "project_planData",
            "ur_fr_documents",
            "risk_inputs",
            "test_bundle_metadata",
            "test_run_outcomes",
            "approval_records",
        ],
        "data_classifications_forbidden": [
            "patient_data",
            "audit_trail_raw",
            "signature_secrets",
            "other_customers_tenant_data",
        ],
        "requires_human_signoff_on": [
            "ccr_approval",
            "revalidation_trigger",
        ],
        "outputs_audited_via":
            "log_audit_event(action='CIA_GENERATED' | "
            "'CCR_APPROVED' | 'REVALIDATION_TRIGGERED')",
        "rollback_eligible":  True,
        "llm_usage": {
            "calls_llm":               True,
            "llm_purpose":             "match CR text to candidate URs; draft narrative summary",
            "max_context_chunks":      8,
            "must_cite_sources":       True,
            "verification_required":   True,
        },
    },

    # ── Sense Layer — Regulatory Surveillance (Sprint 38) ─────────
    "RegulatoryDriftAgent": {
        "version":            "1.0.0",
        "purpose":
            "Scan every UR in a project for citations of "
            "superseded regulatory versions. Surface per-UR drift "
            "records with proposed revalidation actions. The first "
            "cross-platform feature competitors cannot replicate.",
        "allowed_actions": [
            "read_corpus_version_registry",
            "read_requirements",
            "scan_statement_for_framework_names",
            "compute_citation_drift",
            "propose_revalidation_action",
        ],
        "forbidden_actions": [
            "modify_existing_urs",
            "modify_corpus_version_registry",
            "trigger_revalidation",
            "sign_approval",
            "modify_audit_chain",
            "modify_test_bundle",
            "call_llm",
        ],
        "data_classifications_allowed": [
            "regulatory_corpus_metadata",
            "ur_fr_documents",
            "project_planData",
        ],
        "data_classifications_forbidden": [
            "patient_data",
            "audit_trail_raw",
            "signature_secrets",
            "other_customers_tenant_data",
            "llm_api_keys",
        ],
        "requires_human_signoff_on": [
            "any_revalidation_action_proposed",
        ],
        "outputs_audited_via":
            "log_audit_event(action='DRIFT_SCAN_COMPLETED'), "
            "Logic Archive written",
        "rollback_eligible":  True,
        "llm_usage": {
            "calls_llm":               False,
            "llm_purpose":             None,
        },
    },

    # ── Phase 7+ — Validation Continuity (Sprint 37) ──────────────
    "ValidatedStateEngine": {
        "version":            "1.0.0",
        "purpose":
            "Score each UR's current Validated State confidence "
            "(0-100) from observed signals — bundle staleness, open "
            "defect pressure, change-history density, citation "
            "drift. Surface proposals for revalidation actions "
            "without ever triggering them.",
        "allowed_actions": [
            "read_requirements",
            "read_risk_data",
            "read_test_bundles",
            "read_test_runs",
            "read_defects",
            "read_change_records",
            "compute_state_confidence_score",
            "compute_suggested_actions",
            "compute_aggregate_state",
        ],
        "forbidden_actions": [
            "modify_existing_urs",
            "modify_risk_classification",
            "execute_test_step",
            "lock_test_run",
            "trigger_revalidation",
            "sign_approval",
            "modify_audit_chain",
            "modify_test_bundle",
            "call_llm",
        ],
        "data_classifications_allowed": [
            "project_planData",
            "ur_fr_documents",
            "risk_inputs",
            "test_bundle_metadata",
            "test_run_outcomes",
            "defect_records",
            "change_record_history",
        ],
        "data_classifications_forbidden": [
            "patient_data",
            "audit_trail_raw",
            "signature_secrets",
            "other_customers_tenant_data",
            "llm_api_keys",
        ],
        "requires_human_signoff_on": [
            "any_revalidation_action_proposed",
        ],
        "outputs_audited_via":
            "log_audit_event(action='STATE_ASSESSMENT_GENERATED'), "
            "Logic Archive written",
        "rollback_eligible":  True,
        "llm_usage": {
            "calls_llm":               False,
            "llm_purpose":             None,
        },
    },

    # ── Cross-cutting — Audit + Integrity ─────────────────────────
    "IntegrityManager": {
        "version":            "1.0.0",
        "purpose":
            "Maintain the append-only audit trail and optional "
            "Logic Archives. Tamper-evident, SHA-256 chained, "
            "21 CFR Part 11 §11.10(e) compliant.",
        "allowed_actions": [
            "append_audit_row",
            "compute_reasoning_hash",
            "write_logic_archive",
            "validate_thought_process_shape",
        ],
        "forbidden_actions": [
            "modify_existing_audit_row",     # immutability is the point
            "delete_audit_row",
            "modify_existing_logic_archive",
            "call_llm",
            "draft_urs",
            "sign_approval_as_agent",        # only humans sign
            "execute_test_step",
        ],
        "data_classifications_allowed": [
            "every_agent_decision_metadata",
            "user_action_metadata",
            "thought_process_payload",
        ],
        "data_classifications_forbidden": [
            "patient_data_raw",              # only metadata + hashes
            "signature_secrets",             # only hashes
            "llm_api_keys",
        ],
        "requires_human_signoff_on":  [],    # audit writes are atomic
        "outputs_audited_via":
            "self — all writes are the audit trail",
        "rollback_eligible":  False,         # append-only by design
        "llm_usage": {
            "calls_llm":               False,
            "llm_purpose":             None,
        },
    },
}


# ── Public API ───────────────────────────────────────────────────────

def list_agent_passports() -> Dict[str, Any]:
    """
    Return all agent passports with the schema-version envelope.

    Output shape mirrors what the GET /agents/passports endpoint
    surfaces to the Dev Portal panel, the customer-facing Trust
    Center, and any downstream auditor tooling.

    :requirement: URS-37.2 - Surfaceable via API.
    """
    return {
        "schema_version":   PASSPORT_SCHEMA_VERSION,
        "passport_count":   len(AGENT_PASSPORTS),
        "passports":        AGENT_PASSPORTS,
        "notes": (
            "Permission Envelopes are declarative as of Sprint 35.7. "
            "Sprint 41 introduces a runtime passport_check() decorator "
            "that gates every agent call against its passport at "
            "execution time."
        ),
    }


def get_agent_passport(agent_name: str) -> Optional[Dict[str, Any]]:
    """
    Look up a single agent's passport by name.

    Returns None if the agent is not registered. Callers must handle
    the None case explicitly — silent fallback is the kind of thing
    inspectors catch.

    :param agent_name: Stable identifier ("RequirementArchitect" etc.)
    :return: Passport dict or None.
    :requirement: URS-37.2 - Per-agent passport lookup.
    """
    return AGENT_PASSPORTS.get(agent_name)


def validate_passport_shape(passport: Dict[str, Any]) -> List[str]:
    """
    Sanity-check a passport against the v1.0.0 schema. Returns a list
    of error strings; an empty list means the passport is structurally
    valid.

    Not exhaustive — does not check that allowed_actions are actual
    methods on the agent class. That's a Sprint 41 lint pass.

    :requirement: URS-37.3 - Passport shape validation.
    """
    required_keys = {
        "version", "purpose",
        "allowed_actions", "forbidden_actions",
        "data_classifications_allowed",
        "data_classifications_forbidden",
        "requires_human_signoff_on",
        "outputs_audited_via",
        "rollback_eligible",
        "llm_usage",
    }
    errors: List[str] = []
    missing = required_keys - set(passport.keys())
    if missing:
        errors.append(
            f"Missing required keys: {sorted(missing)}"
        )
    if "allowed_actions" in passport and not isinstance(
        passport["allowed_actions"], list,
    ):
        errors.append("allowed_actions must be a list")
    if "forbidden_actions" in passport and not isinstance(
        passport["forbidden_actions"], list,
    ):
        errors.append("forbidden_actions must be a list")
    if "llm_usage" in passport:
        llm = passport["llm_usage"]
        if not isinstance(llm, dict):
            errors.append("llm_usage must be a dict")
        elif "calls_llm" not in llm:
            errors.append("llm_usage missing required 'calls_llm' key")
    return errors


# ── Self-check at import time (cheap insurance) ──────────────────────
#
# If any passport in the registry is malformed, the module raises at
# import time so the API server crashes loudly instead of serving
# bad data to a customer.

for _name, _passport in AGENT_PASSPORTS.items():
    _errors = validate_passport_shape(_passport)
    if _errors:
        raise ValueError(
            f"Agent passport for '{_name}' is malformed: "
            f"{'; '.join(_errors)}"
        )
