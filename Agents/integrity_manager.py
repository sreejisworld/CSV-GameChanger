"""
Integrity Manager Module.

Provides a central, append-only CSV audit trail at output/audit_trail.csv.
Every agent action is logged with a SHA-256 reasoning hash for tamper
detection, satisfying 21 CFR Part 11 traceability requirements.

The CSV file is opened exclusively in append ('a') mode so that previous
log entries can never be overwritten by application code.

:requirement: URS-2.1 - System shall maintain 21 CFR Part 11 compliant
              audit trail.
:requirement: URS-10.1 - System shall provide a central integrity-managed
              audit trail for all agent actions.
"""
import csv
import hashlib
import json
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
AUDIT_TRAIL_PATH = PROJECT_ROOT / "output" / "audit_trail.csv"
LOGIC_ARCHIVE_DIR = PROJECT_ROOT / "output" / "logic_archives"

_ARCHIVE_SCHEMA_VERSION = "1.0.0"

CSV_COLUMNS = [
    "Timestamp",
    "User_ID",
    "Agent_Name",
    "Action_Performed",
    "Decision_Logic",
    "Reasoning_Hash",
    "Compliance_Impact",
]

# Map of agent actions to their compliance impact classification.
_IMPACT_MAP = {
    # RequirementArchitect
    "SEARCH_KNOWLEDGE_BASE": "Reference Query",
    "URS_GENERATED": "GxP Documentation",
    "URS_GENERATION_FAILED": "GxP Documentation",
    "URS_TRANSFORMED_TO_UR_FR": "GxP Documentation",
    # IngestorAgent
    "DOCUMENT_INGESTED": "Data Integrity",
    "DOCUMENT_INGESTION_FAILED": "Data Integrity",
    "BATCH_INGESTION_COMPLETED": "Data Integrity",
    "GAP_ANALYSIS_COMPLETED": "Regulatory Compliance",
    "GAP_ANALYSIS_FAILED": "Regulatory Compliance",
    # RiskStrategist
    "RISK_ASSESSMENT_COMPLETED": "Patient Safety",
    # TestGenerator
    "TEST_SCRIPT_GENERATED": "Validation Evidence",
    "TEST_SCRIPT_GENERATION_FAILED": "Validation Evidence",
    "TEST_BATCH_GENERATED": "Validation Evidence",
    # DeltaAgent CSA test from UR/FR
    "CSA_TEST_SCRIPT_GENERATED": "Validation Evidence",
    "CSA_TEST_CHARTER_GENERATED": "Validation Evidence",
    "CSA_TEST_BATCH_GENERATED": "Validation Evidence",
    # API / Webhook
    "CHANGE_REQUEST_RECEIVED": "Change Control",
    "CHANGE_REQUEST_ASSESSED": "Change Control",
    "CHANGE_REQUEST_FAILED": "Change Control",
    # Sprint 39 — AI Trustworthiness Credibility Assessment Report
    "TWR_GENERATION_RECEIVED":  "AI Trustworthiness + Regulatory Compliance",
    "TWR_GENERATION_COMPLETED": "AI Trustworthiness + Regulatory Compliance",
    "TWR_GENERATION_FAILED":    "AI Trustworthiness + Regulatory Compliance",
    # Sprint 40 — Bounded Autonomy Profile (BAP) engine
    "BAP_ASSESSMENT_RECEIVED":  "AI Trustworthiness + Bounded Autonomy",
    "BAP_ASSESSMENT_COMPLETED": "AI Trustworthiness + Bounded Autonomy",
    "BAP_ASSESSMENT_FAILED":    "AI Trustworthiness + Bounded Autonomy",
    # Sprint 41 — Test Pilot Agent
    "TEST_PILOT_RUN_RECEIVED":  "Platform Quality + Regression",
    "TEST_PILOT_RUN_COMPLETED": "Platform Quality + Regression",
    "TEST_PILOT_RUN_FAILED":    "Platform Quality + Regression",
    # SignOff / Release
    "DOCUMENT_SIGN_OFF":        "Electronic Signature",
    "TEST_RUN_SIGNED_OFF":      "Electronic Signature",
    "RELEASE_APPROVAL_SIGNED":  "Electronic Signature",
    "RELEASE_APPROVED":         "Release Authorization",
    # Sprint 18.2 — Validation Deliverables Pack
    "VALIDATION_PLAN_EXPORT_RECEIVED":         "GxP Documentation",
    "VALIDATION_PLAN_EXPORT_COMPLETED":        "GxP Documentation",
    "VALIDATION_PLAN_EXPORT_FAILED":           "GxP Documentation",
    "DESIGN_SPEC_EXPORT_RECEIVED":             "GxP Documentation",
    "DESIGN_SPEC_EXPORT_COMPLETED":            "GxP Documentation",
    "DESIGN_SPEC_EXPORT_FAILED":               "GxP Documentation",
    "VALIDATION_SUMMARY_EXPORT_RECEIVED":      "Validation Evidence",
    "VALIDATION_SUMMARY_EXPORT_COMPLETED":     "Validation Evidence",
    "VALIDATION_SUMMARY_EXPORT_FAILED":        "Validation Evidence",
    # Sprint 19 — Audit Trail Viewer / Inspection Export
    "AUDIT_EXPORT_RECEIVED":                   "Regulatory Compliance",
    "AUDIT_EXPORT_COMPLETED":                  "Regulatory Compliance",
    "AUDIT_EXPORT_FAILED":                     "Regulatory Compliance",
    # Sprint 28 — Living Traceability Matrix Export
    "TRACEABILITY_EXPORT_RECEIVED":            "Regulatory Compliance",
    "TRACEABILITY_EXPORT_COMPLETED":           "Regulatory Compliance",
    "TRACEABILITY_EXPORT_FAILED":              "Regulatory Compliance",
    # VerificationAgent
    "URS_VERIFIED": "Regulatory Compliance",
    "COMPLIANCE_EXCEPTION": "Compliance Exception",
    "URS_BATCH_VERIFIED": "Regulatory Compliance",
    # SMARTRequirementsEngine
    "SMART_REQUIREMENTS_REFINED": "GxP Documentation",
    # WebhookRegistry
    "WEBHOOK_REGISTERED":        "Integration",
    "WEBHOOK_DEREGISTERED":      "Integration",
    "WEBHOOK_FIRED":             "Integration",
    "WEBHOOK_RETRY_EXHAUSTED":   "Integration — Error",
    # KeyStore
    "API_KEY_CREATED":           "Access Control",
    "API_KEY_USED":              "Access Control",
    # JobStore (bulk processing)
    "BULK_VALIDATE_STARTED":     "Validation Evidence",
    "BULK_VALIDATE_COMPLETE":    "Validation Evidence",
    "BULK_VALIDATE_FAILED":      "Validation Evidence",
    # Sentinel API events
    "SENTINEL_SCAN_RECEIVED":    "Change Control",
    "SENTINEL_SCAN_COMPLETED":   "Change Control",
    "SENTINEL_SCAN_FAILED":      "Change Control",
    # Access control decisions
    "ACCESS_PERMITTED":          "Access Control — Security",
    "ACCESS_DENIED":             "Access Control — Denial",
    # Sprint 36 — Change Impact Assessment + CCR + Revalidation
    # AI proposes the CIA, human signs the CCR, only then does the
    # revalidation sub-run get triggered. Bounded autonomy applied to
    # change management — every advance is signed; nothing autonomous.
    "CIA_RECEIVED":              "Change Control",
    "CIA_GENERATED":             "Change Control + AI Reasoning",
    "CIA_FAILED":                "Change Control",
    "CCR_RECEIVED":              "Change Control + Regulatory Compliance",
    "CCR_APPROVED":              "Change Control + 21 CFR Part 11",
    "CCR_FAILED":                "Change Control",
    "REVALIDATION_RECEIVED":     "Validation Evidence",
    "REVALIDATION_TRIGGERED":    "Validation Evidence + Change Control",
    "REVALIDATION_CLOSED":       "Validation Evidence",
    "REVALIDATION_FAILED":       "Validation Evidence",
    # Sprint 35.7 — Agent Passport read endpoints (transparency)
    "AGENT_PASSPORTS_RECEIVED":     "System Transparency",
    "AGENT_PASSPORTS_COMPLETED":    "System Transparency",
    "AGENT_PASSPORTS_FAILED":       "System Transparency",
    "AGENT_PASSPORT_LOOKUP_RECEIVED":  "System Transparency",
    "AGENT_PASSPORT_LOOKUP_COMPLETED": "System Transparency",
    "AGENT_PASSPORT_LOOKUP_FAILED":    "System Transparency",
    # Sprint 37 — Validated State Confidence Engine
    # The "EVOLV helps you STAY validated" loop. Per-UR confidence
    # scores from deterministic signals: citation freshness, bundle
    # freshness, defect pressure, change-history density. Computed
    # on demand; results audited so an inspector can see the score
    # an inspector would have seen at any past moment.
    "STATE_ASSESSMENT_RECEIVED":   "Validation Continuity",
    "STATE_ASSESSMENT_COMPLETED":  "Validation Continuity + AI Reasoning",
    "STATE_ASSESSMENT_FAILED":     "Validation Continuity",
    # Sprint 38 — Regulatory Drift Detection (Sense Layer)
    # When a regulatory framework version updates in the ingested
    # corpus, this scan flags every UR whose cited version is now
    # superseded. AI proposes the per-UR drift; QA decides whether
    # to revalidate. The first cross-platform feature competitors
    # cannot replicate without a comparable audit-chain spine.
    "DRIFT_SCAN_RECEIVED":         "Regulatory Surveillance",
    "DRIFT_SCAN_COMPLETED":        "Regulatory Surveillance + Validation Continuity",
    "DRIFT_SCAN_FAILED":           "Regulatory Surveillance",
    "CORPUS_VERSION_BUMPED":       "Regulatory Surveillance + Configuration Change",
    # Sprint 45 — audit-trail chain verification (SEC-9 closure)
    "AUDIT_CHAIN_VERIFY_RECEIVED":  "Data Integrity",
    "AUDIT_CHAIN_VERIFY_COMPLETED": "Data Integrity",
    "AUDIT_CHAIN_VERIFY_FAILED":    "Data Integrity",
}

DEFAULT_IMPACT = "Operational"

# Module-level lock for thread-safe writes.
_write_lock = threading.Lock()

# ── Hash chaining (Sprint 45 — closes security finding SEC-9) ────
# Every row's Reasoning_Hash now incorporates the previous row's
# hash, upgrading the trail from per-row tamper evidence to a
# linked chain: silently deleting, reordering, or editing any
# chained row breaks every hash after it. Rows written before
# this upgrade ("legacy rows") verify against the original
# per-row formula; the verifier reports both segments.
#
# Known limitation (documented, not hidden): truncating the TAIL
# of the chain is not detectable from the file alone. Anchor the
# chain head externally (e.g. record verify_audit_chain().head_hash
# in a periodic QA log) to close that gap operationally.

CHAIN_GENESIS_HASH = "0" * 64

# Last-written hash per audit file, so we don't re-read the file
# on every append. Guarded by _write_lock.
_last_hash_cache: Dict[str, str] = {}


def _compute_reasoning_hash(
    timestamp: str,
    user_id: str,
    agent_name: str,
    action: str,
    decision_logic: str,
    compliance_impact: str,
) -> str:
    """
    Compute a SHA-256 hash over the audit record fields.

    The hash provides tamper-evident integrity — any modification to a
    logged row will cause a mismatch when the hash is recomputed from
    the stored field values.

    :param timestamp: ISO-8601 timestamp of the event.
    :param user_id: Identifier of the acting user or SYSTEM.
    :param agent_name: Name of the agent performing the action.
    :param action: The action performed.
    :param decision_logic: Human-readable summary of the agent's
                           decision reasoning.
    :param compliance_impact: Classified compliance impact.
    :return: Hex-encoded SHA-256 digest.
    :requirement: URS-10.2 - System shall hash audit records for
                  tamper detection.
    """
    payload = "|".join([
        timestamp,
        user_id,
        agent_name,
        action,
        decision_logic,
        compliance_impact,
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _compute_chained_hash(
    prev_hash: str,
    timestamp: str,
    user_id: str,
    agent_name: str,
    action: str,
    decision_logic: str,
    compliance_impact: str,
) -> str:
    """
    Compute a chained SHA-256 hash over the previous row's hash
    plus this row's fields.

    Any modification to an earlier chained row changes its hash,
    which invalidates this hash and every one after it — the
    property that makes the trail a verifiable chain rather than
    a collection of individually-hashed rows.

    :param prev_hash: Reasoning_Hash of the previous row, or
                      ``CHAIN_GENESIS_HASH`` for the first row.
    :param timestamp: ISO-8601 timestamp of the event.
    :param user_id: Identifier of the acting user or SYSTEM.
    :param agent_name: Name of the agent performing the action.
    :param action: The action performed.
    :param decision_logic: Human-readable reasoning summary.
    :param compliance_impact: Classified compliance impact.
    :return: Hex-encoded SHA-256 digest.
    :requirement: URS-45.1 - Audit rows shall be hash-chained.
    """
    payload = "|".join([
        prev_hash,
        timestamp,
        user_id,
        agent_name,
        action,
        decision_logic,
        compliance_impact,
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_last_row_hash(path: Path) -> str:
    """
    Return the Reasoning_Hash of the last data row in *path*,
    or ``CHAIN_GENESIS_HASH`` when the file is missing/empty.

    :param path: Path to the audit trail CSV file.
    :return: Hex hash string to chain the next row onto.
    :requirement: URS-45.1 - Audit rows shall be hash-chained.
    """
    if (not path.exists()) or path.stat().st_size == 0:
        return CHAIN_GENESIS_HASH
    hash_idx = CSV_COLUMNS.index("Reasoning_Hash")
    last_hash = CHAIN_GENESIS_HASH
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row == CSV_COLUMNS:
                continue
            if len(row) > hash_idx:
                last_hash = row[hash_idx]
    return last_hash


def _get_prev_hash(path: Path) -> str:
    """
    Cached lookup of the previous row's hash for *path*.

    Must be called while holding ``_write_lock`` so the cache
    stays coherent with concurrent appends in this process.

    :param path: Path to the audit trail CSV file.
    :return: Hash to chain the next row onto.
    :requirement: URS-45.1 - Audit rows shall be hash-chained.
    """
    key = str(path.resolve())
    if key not in _last_hash_cache:
        _last_hash_cache[key] = _read_last_row_hash(path)
    return _last_hash_cache[key]


def _validate_thought_process(
    thought_process: Dict[str, Any],
) -> None:
    """
    Validate that a thought-process dict has the required shape.

    The dict must contain ``"inputs"`` (dict), ``"steps"`` (list),
    and ``"outputs"`` (dict).

    :param thought_process: The thought-process payload to validate.
    :raises ValueError: If any required key is missing or has the
                        wrong type.
    :requirement: URS-13.1 - System shall archive AI reasoning
                  alongside audit records.
    """
    required_keys = {"inputs", "steps", "outputs"}
    missing = required_keys - thought_process.keys()
    if missing:
        raise ValueError(
            f"thought_process missing required keys: "
            f"{', '.join(sorted(missing))}"
        )

    if not isinstance(thought_process["steps"], list):
        raise ValueError(
            "thought_process['steps'] must be a list"
        )


def _write_logic_archive(
    timestamp: str,
    agent_name: str,
    action: str,
    user_id: str,
    compliance_impact: str,
    decision_logic: str,
    audit_trail_hash: str,
    thought_process: Dict[str, Any],
) -> Path:
    """
    Write a hidden, self-describing JSON logic-archive file.

    The archive cross-references the CSV audit trail row via
    *audit_trail_hash* and includes its own tamper-evident
    SHA-256 integrity hash.

    :param timestamp: ISO-8601 timestamp of the audit event.
    :param agent_name: Name of the agent.
    :param action: The action performed.
    :param user_id: Identifier of the acting user.
    :param compliance_impact: Classified compliance impact.
    :param decision_logic: Human-readable reasoning summary.
    :param audit_trail_hash: SHA-256 hash from the CSV row.
    :param thought_process: Dict with ``inputs``, ``steps``,
                            ``outputs`` keys.
    :return: Path to the written archive file.
    :requirement: URS-13.1 - System shall archive AI reasoning
                  alongside audit records.
    """
    LOGIC_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    archive = {
        "$schema_version": _ARCHIVE_SCHEMA_VERSION,
        "archive_type": "logic_archive",
        "audit_trail_hash": audit_trail_hash,
        "timestamp": timestamp,
        "agent_name": agent_name,
        "action": action,
        "user_id": user_id,
        "compliance_impact": compliance_impact,
        "decision_logic_summary": decision_logic,
        "inputs": thought_process["inputs"],
        "steps": thought_process["steps"],
        "outputs": thought_process["outputs"],
    }

    # Tamper-evident hash over all fields except integrity.
    content_bytes = json.dumps(
        archive, sort_keys=True, ensure_ascii=False,
    ).encode("utf-8")
    archive_hash = hashlib.sha256(content_bytes).hexdigest()

    archive["integrity"] = {
        "archive_hash": archive_hash,
        "algorithm": "sha256",
    }

    # Filename: .{ACTION}_{YYYYMMDDTHHMMSSZ}_{hash[:8]}.json
    ts_compact = timestamp.replace(":", "").replace("-", "")
    filename = (
        f".{action}_{ts_compact}_{audit_trail_hash[:8]}.json"
    )
    archive_path = LOGIC_ARCHIVE_DIR / filename

    with open(archive_path, mode="w", encoding="utf-8") as f:
        json.dump(archive, f, indent=2, ensure_ascii=False)

    return archive_path


def _ensure_csv_header(path: Path) -> None:
    """
    Write the CSV header row if the file does not yet exist or is empty.

    Uses append mode so an existing file is never truncated.

    :param path: Path to the audit trail CSV file.
    :requirement: URS-10.1 - System shall provide a central audit trail.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    write_header = (not path.exists()) or (path.stat().st_size == 0)

    if write_header:
        with open(path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)


def log_audit_event(
    agent_name: str,
    action: str,
    user_id: str = "SYSTEM",
    decision_logic: str = "",
    compliance_impact: Optional[str] = None,
    audit_path: Path = AUDIT_TRAIL_PATH,
    thought_process: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Append a single audit record to the central CSV audit trail.

    The file is opened in append ('a') mode exclusively, ensuring
    that no previous entries can ever be overwritten by this code.

    When *thought_process* is provided, a hidden JSON logic-archive
    file is written to ``output/logic_archives/`` containing the
    full AI reasoning (inputs, intermediate steps, outputs),
    cross-referenced to this CSV row via the reasoning hash.

    :param agent_name: Name of the agent (e.g. "RequirementArchitect").
    :param action: Action performed (e.g. "URS_GENERATED").
    :param user_id: Identifier of the acting user (default "SYSTEM").
    :param decision_logic: Human-readable summary of the agent's
                           decision reasoning for this action
                           (e.g. "Determined TC-URS-7.1 is Unscripted
                           because Criticality is Low based on CSA
                           Guidance Section 4").
    :param compliance_impact: Override for the compliance impact
                              classification. When None, the impact is
                              looked up from the built-in action map.
    :param audit_path: Path to the CSV file (defaults to
                       output/audit_trail.csv).
    :param thought_process: Optional dict with keys ``"inputs"``,
                            ``"steps"`` (list), and ``"outputs"``
                            describing the full AI reasoning chain.
                            When provided, a logic-archive JSON file
                            is written alongside the CSV row.
    :return: The SHA-256 reasoning hash written to the record.
    :requirement: URS-2.1 - System shall maintain 21 CFR Part 11
                  compliant audit trail.
    :requirement: URS-10.1 - System shall provide a central
                  integrity-managed audit trail for all agent actions.
    :requirement: URS-13.1 - System shall archive AI reasoning
                  alongside audit records.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if compliance_impact is None:
        compliance_impact = _IMPACT_MAP.get(action, DEFAULT_IMPACT)

    with _write_lock:
        _ensure_csv_header(audit_path)

        # Chain this row onto the previous row's hash (Sprint 45,
        # SEC-9). Computed inside the lock so the prev-hash read
        # and the append are atomic per process.
        prev_hash = _get_prev_hash(audit_path)
        reasoning_hash = _compute_chained_hash(
            prev_hash, timestamp, user_id, agent_name, action,
            decision_logic, compliance_impact,
        )

        row = [
            timestamp,
            user_id,
            agent_name,
            action,
            decision_logic,
            reasoning_hash,
            compliance_impact,
        ]

        with open(
            audit_path, mode="a", newline="", encoding="utf-8"
        ) as f:
            writer = csv.writer(f)
            writer.writerow(row)

        _last_hash_cache[str(audit_path.resolve())] = reasoning_hash

        if thought_process is not None:
            _validate_thought_process(thought_process)
            _write_logic_archive(
                timestamp, agent_name, action, user_id,
                compliance_impact, decision_logic,
                reasoning_hash, thought_process,
            )

    return reasoning_hash


# ── Chain verification (Sprint 45 — SEC-9) ───────────────────────

@dataclass
class ChainRowIssue:
    """One problem row found during chain verification."""
    row_number:  int          # 1-based, excluding the header
    action:      str
    timestamp:   str
    reason:      str


@dataclass
class ChainVerificationReport:
    """Outcome of walking the full audit trail chain."""
    audit_path:    str
    total_rows:    int
    chained_ok:    int
    legacy_ok:     int
    issues:        List[ChainRowIssue] = field(default_factory=list)
    head_hash:     str = CHAIN_GENESIS_HASH
    verified_at:   str = ""

    @property
    def intact(self) -> bool:
        return len(self.issues) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_path":  self.audit_path,
            "verified_at": self.verified_at,
            "intact":      self.intact,
            "total_rows":  self.total_rows,
            "chained_ok":  self.chained_ok,
            "legacy_ok":   self.legacy_ok,
            "head_hash":   self.head_hash,
            "issues": [
                {
                    "row_number": i.row_number,
                    "action":     i.action,
                    "timestamp":  i.timestamp,
                    "reason":     i.reason,
                }
                for i in self.issues
            ],
        }


def verify_audit_chain(
    audit_path: Path = AUDIT_TRAIL_PATH,
) -> ChainVerificationReport:
    """
    Walk the audit trail and verify every row's hash.

    Each row must satisfy one of two formulas:

    - **Chained** (rows written from Sprint 45 onward):
      ``sha256(prev_hash | fields)`` — links the row to its
      predecessor, so any edit/delete/reorder upstream breaks it.
    - **Legacy** (rows written before the upgrade):
      ``sha256(fields)`` — per-row tamper evidence only.

    A legacy-format row appearing AFTER a chained row is flagged:
    that pattern is what a downgrade/tamper attempt looks like.

    Record ``head_hash`` externally (QA log, ticket) to detect
    tail truncation, which no file-internal scheme can catch.

    :param audit_path: CSV to verify (defaults to the central
                       audit trail).
    :return: ChainVerificationReport with per-row issues.
    :requirement: URS-45.2 - Full-chain verification an inspector
                  can run on demand.
    """
    report = ChainVerificationReport(
        audit_path=str(audit_path),
        total_rows=0,
        chained_ok=0,
        legacy_ok=0,
        verified_at=datetime.now(timezone.utc).isoformat(),
    )
    if (not audit_path.exists()) or audit_path.stat().st_size == 0:
        return report

    hash_idx = CSV_COLUMNS.index("Reasoning_Hash")
    prev_hash = CHAIN_GENESIS_HASH
    seen_chained = False

    with open(audit_path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row == CSV_COLUMNS:
                continue
            report.total_rows += 1
            if len(row) != len(CSV_COLUMNS):
                report.issues.append(ChainRowIssue(
                    row_number=report.total_rows,
                    action=row[3] if len(row) > 3 else "?",
                    timestamp=row[0] if row else "?",
                    reason=(
                        f"Malformed row: {len(row)} columns, "
                        f"expected {len(CSV_COLUMNS)}."
                    ),
                ))
                prev_hash = (
                    row[hash_idx] if len(row) > hash_idx
                    else prev_hash
                )
                continue

            (timestamp, user_id, agent_name, action,
             decision_logic, row_hash,
             compliance_impact) = row

            chained_expected = _compute_chained_hash(
                prev_hash, timestamp, user_id, agent_name,
                action, decision_logic, compliance_impact,
            )
            legacy_expected = _compute_reasoning_hash(
                timestamp, user_id, agent_name, action,
                decision_logic, compliance_impact,
            )

            if row_hash == chained_expected:
                report.chained_ok += 1
                seen_chained = True
            elif row_hash == legacy_expected:
                report.legacy_ok += 1
                if seen_chained:
                    report.issues.append(ChainRowIssue(
                        row_number=report.total_rows,
                        action=action,
                        timestamp=timestamp,
                        reason=(
                            "Legacy-format hash after chained "
                            "rows — possible downgrade/tamper."
                        ),
                    ))
            else:
                report.issues.append(ChainRowIssue(
                    row_number=report.total_rows,
                    action=action,
                    timestamp=timestamp,
                    reason=(
                        "Hash matches neither chained nor "
                        "legacy formula — row content or order "
                        "has been altered."
                    ),
                ))

            prev_hash = row_hash

    report.head_hash = prev_hash
    return report
