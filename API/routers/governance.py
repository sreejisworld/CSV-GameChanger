"""
Governance Router — AI Decision Queue and Human-in-the-Loop Review.

Endpoints:
  POST /governance/decision        — AI system pushes a decision for review
  GET  /governance/queue           — Pending decisions awaiting human review
  GET  /governance/decisions       — All decisions (optional ?status= filter)
  POST /governance/review/{id}     — Human approves / overrides / rejects
  GET  /governance/overrides       — Immutable human override ledger
  GET  /governance/timeline        — Audit event timeline (all actors)
  GET  /governance/stats           — Summary counts for dashboard header

:requirement: URS-27.1 - System shall maintain AI decision queue for HITL.
:requirement: URS-27.2 - System shall log all human overrides to immutable ledger.
:requirement: URS-27.3 - System shall expose audit timeline for traceability.
:requirement: URS-27.4 - System shall record reviewer name, role, and reason.
:requirement: URS-27.5 - System shall provide governance statistics for dashboard.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Governance"])


# ── Request / Response models ───────────────────────────────────────

class PushDecisionRequest(BaseModel):
    """AI system submits a new decision for human review."""
    urs_id:         str
    decision_type:  str   # URS_GENERATION | RISK_CLASSIFICATION |
    #                       TEST_SCRIPT_GENERATED | URS_VERIFICATION
    ai_output:      Dict[str, Any]
    ai_reasoning:   str
    gamp5_reference: Optional[str] = None
    confidence:     Optional[float] = None
    agent_name:     Optional[str] = None


class ReviewRequest(BaseModel):
    """Human reviewer submits their verdict."""
    action:       str          # approve | override | reject
    reviewer_name: str
    reviewer_role: str
    reason:        Optional[str] = None
    new_value:     Optional[str] = None   # Only for override


# ── In-memory stores ────────────────────────────────────────────────
_decisions: Dict[str, Dict[str, Any]] = {}
_overrides: List[Dict[str, Any]] = []


# ── Seed data — pre-populated for demo realism ─────────────────────
def _now(offset_seconds: int = 0) -> str:
    """Return ISO timestamp offset from now (negative = past)."""
    from datetime import timedelta
    ts = datetime.now(timezone.utc)
    if offset_seconds:
        ts = ts + timedelta(seconds=offset_seconds)
    return ts.isoformat()


_SEED_DECISIONS: List[Dict[str, Any]] = [
    # ── Pending decisions (awaiting human review) ──────────────────
    {
        "decision_id":   "dec-001",
        "urs_id":        "URS-7.1",
        "decision_type": "URS_GENERATION",
        "agent_name":    "RequirementArchitect",
        "ai_output": {
            "criticality":            "Medium",
            "requirement_statement":  (
                "The system shall monitor and record warehouse temperature "
                "at 15-minute intervals and trigger an alert when readings "
                "fall outside the 2°C–8°C validated range."
            ),
        },
        "ai_reasoning": (
            "Requirement contains 'temperature monitoring' and 'warehouse' "
            "keywords. Cross-referenced GAMP 5 Guide (p.42): environment "
            "monitoring classified as GxP Indirect — Medium criticality. "
            "No direct patient safety keywords detected. Confidence: 0.87."
        ),
        "gamp5_reference": (
            "Per GAMP5_Guide.pdf [GAMP5_Rev2] (p.42): 'Environmental "
            "monitoring systems support quality by providing data used in "
            "product release decisions. Criticality is typically Medium "
            "unless directly linked to patient safety outcomes.'"
        ),
        "confidence": 0.87,
        "status":     "pending",
        "created_at": _now(-1800),
        "reviewed_by":   None,
        "reviewed_at":   None,
        "override_reason": None,
        "new_value":     None,
    },
    {
        "decision_id":   "dec-002",
        "urs_id":        "URS-3.1",
        "decision_type": "RISK_CLASSIFICATION",
        "agent_name":    "RiskStrategist",
        "ai_output": {
            "risk_level":             "High",
            "risk_assessment":        "GxP Direct",
            "implementation_method":  "Configured",
            "rpn":                    18,
            "testing_strategy":       "OQ and/or UAT",
        },
        "ai_reasoning": (
            "System criticality: 'critical'. Change type: 'normal'. "
            "Severity=HIGH (critical system). Occurrence=OCCASIONAL. "
            "Detectability=MEDIUM. RPN = 3×2×3 = 18 → HIGH. "
            "Patient safety override not triggered (no sterile/batch "
            "release keywords). GxP Direct + Configured → High per matrix."
        ),
        "gamp5_reference": (
            "Per GAMP5_Guide.pdf [GAMP5_Rev2] (p.67): 'Configured "
            "software directly supporting GxP processes requires formal "
            "OQ and UAT testing. Risk Priority Number above 12 mandates "
            "rigorous scripted testing strategy.'"
        ),
        "confidence": 0.91,
        "status":     "pending",
        "created_at": _now(-900),
        "reviewed_by":   None,
        "reviewed_at":   None,
        "override_reason": None,
        "new_value":     None,
    },
    {
        "decision_id":   "dec-003",
        "urs_id":        "URS-7.1",
        "decision_type": "TEST_SCRIPT_GENERATED",
        "agent_name":    "DeltaAgent",
        "ai_output": {
            "script_id":     "TS-URS-7.1",
            "test_type":     "Formal OQ",
            "step_count":    14,
            "setup_steps":   3,
            "positive_steps": 6,
            "negative_steps": 3,
            "edge_steps":    2,
        },
        "ai_reasoning": (
            "URS-7.1 risk_level=High, implementation_method=Configured. "
            "Routing to Formal OQ (scripted positive tests per FR). "
            "Generated 3 setup steps (login, navigate, data prep), "
            "6 execution steps (positive), 3 negative, 2 edge. "
            "Quality checklist: all 5 criteria passed."
        ),
        "gamp5_reference": (
            "Per CSA_Guide.pdf [CSA_Rev1] (p.23): 'For High-risk "
            "configured software, formal Operational Qualification (OQ) "
            "with documented pass/fail criteria is required. Each "
            "functional requirement must have at least one test step.'"
        ),
        "confidence": 0.94,
        "status":     "pending",
        "created_at": _now(-300),
        "reviewed_by":   None,
        "reviewed_at":   None,
        "override_reason": None,
        "new_value":     None,
    },

    # ── Completed decisions (historical record) ────────────────────
    {
        "decision_id":   "dec-004",
        "urs_id":        "URS-2.1",
        "decision_type": "URS_GENERATION",
        "agent_name":    "RequirementArchitect",
        "ai_output": {
            "criticality":           "High",
            "requirement_statement": (
                "The system shall maintain a time-stamped, user-attributed, "
                "append-only audit trail for all electronic records in "
                "accordance with 21 CFR Part 11."
            ),
        },
        "ai_reasoning": (
            "Requirement contains 'audit trail', '21 CFR Part 11', and "
            "'electronic records' — all High criticality indicators per "
            "GAMP 5 criticality matrix. Regulatory obligation keywords "
            "detected. Confidence: 0.96."
        ),
        "gamp5_reference": (
            "Per 21CFR_Part11.pdf [21CFR11_Rev1] (p.8): 'Persons who use "
            "closed systems to create, modify, maintain, or transmit "
            "electronic records shall employ procedures and controls "
            "including audit trails.'"
        ),
        "confidence": 0.96,
        "status":      "approved",
        "created_at":  _now(-7200),
        "reviewed_by": "Dr. Sarah Chen",
        "reviewer_role": "CSV Lead",
        "reviewed_at": _now(-6800),
        "override_reason": None,
        "new_value":   None,
    },
    {
        "decision_id":   "dec-005",
        "urs_id":        "URS-5.1",
        "decision_type": "RISK_CLASSIFICATION",
        "agent_name":    "RiskStrategist",
        "ai_output": {
            "risk_level":            "Medium",
            "risk_assessment":       "GxP Indirect",
            "implementation_method": "Configured",
            "rpn":                   8,
            "testing_strategy":      "Informal",
        },
        "ai_reasoning": (
            "System: 'medium' criticality. Change type: 'standard'. "
            "Severity=MEDIUM. Occurrence=RARE. Detectability=MEDIUM. "
            "RPN = 2×1×2 = 4 → LOW. Bumped to MEDIUM: GxP Indirect "
            "+ Configured. No patient safety override triggered."
        ),
        "gamp5_reference": (
            "Per GAMP5_Guide.pdf [GAMP5_Rev2] (p.71): 'GxP Indirect "
            "configured software requires at minimum informal testing "
            "to demonstrate fitness for purpose.'"
        ),
        "confidence": 0.79,
        "status":      "overridden",
        "created_at":  _now(-10800),
        "reviewed_by": "Jane Smith",
        "reviewer_role": "QA Head",
        "reviewed_at": _now(-10200),
        "override_reason": (
            "Electronic signature workflows directly support 21 CFR Part 11 "
            "compliance obligations. Patient safety risk cannot be classified "
            "below HIGH — any signature bypass creates a regulatory finding. "
            "Escalating to High with OQ and/or UAT required."
        ),
        "new_value": "High",
    },
    {
        "decision_id":   "dec-006",
        "urs_id":        "URS-4.1",
        "decision_type": "URS_VERIFICATION",
        "agent_name":    "VerificationAgent",
        "ai_output": {
            "verdict":   "Approved",
            "checks":    3,
            "passed":    3,
            "failed":    0,
        },
        "ai_reasoning": (
            "Ran 3 verification checks: (1) Criticality Alignment — PASS "
            "(High criticality consistent with GxP Direct keywords). "
            "(2) Rationale Relevance — PASS (best score 0.89 ≥ 0.45 "
            "threshold). (3) Contradiction Scan — PASS (no contradicting "
            "phrases detected against GAMP 5 regulatory text)."
        ),
        "gamp5_reference": (
            "Per GAMP5_Guide.pdf [GAMP5_Rev2] (p.55): 'Requirements "
            "shall be verified against applicable regulatory guidance "
            "before proceeding to design and implementation phases.'"
        ),
        "confidence": 0.89,
        "status":      "approved",
        "created_at":  _now(-14400),
        "reviewed_by": "Dr. Sarah Chen",
        "reviewer_role": "CSV Lead",
        "reviewed_at": _now(-13900),
        "override_reason": None,
        "new_value":   None,
    },
]


def _seed_overrides() -> List[Dict[str, Any]]:
    """Build override ledger from seeded overridden decisions."""
    result = []
    for d in _SEED_DECISIONS:
        if d["status"] == "overridden":
            result.append({
                "override_id":     str(uuid4())[:8],
                "decision_id":     d["decision_id"],
                "urs_id":          d["urs_id"],
                "decision_type":   d["decision_type"],
                "ai_said":         _summarise_ai(d),
                "human_changed_to": d["new_value"],
                "reviewer_name":   d["reviewed_by"],
                "reviewer_role":   d.get("reviewer_role", ""),
                "reason":          d["override_reason"],
                "reviewed_at":     d["reviewed_at"],
                "audit_hash":      _hash_override(d),
            })
    return result


def _summarise_ai(d: Dict) -> str:
    """Return a short human-readable summary of what the AI decided."""
    t = d["decision_type"]
    o = d["ai_output"]
    if t == "URS_GENERATION":
        return f"Criticality = {o.get('criticality', '?')}"
    if t == "RISK_CLASSIFICATION":
        return f"Risk Level = {o.get('risk_level', '?')}"
    if t == "TEST_SCRIPT_GENERATED":
        return f"Test Type = {o.get('test_type', '?')}, Steps = {o.get('step_count', '?')}"
    if t == "URS_VERIFICATION":
        return f"Verdict = {o.get('verdict', '?')}"
    return str(o)


def _hash_override(d: Dict) -> str:
    """Compute a short tamper-evident hash for display."""
    import hashlib
    payload = (
        f"{d['decision_id']}{d['reviewed_by']}"
        f"{d['reviewed_at']}{d['new_value']}{d['override_reason']}"
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ── Initialise in-memory stores with seed data ─────────────────────
for _d in _SEED_DECISIONS:
    _decisions[_d["decision_id"]] = _d

_overrides = _seed_overrides()


# ── Endpoints ───────────────────────────────────────────────────────

@router.post(
    "/governance/decision",
    summary="AI system pushes a decision for human review",
)
def push_decision(body: PushDecisionRequest):
    """
    Called by AI agents (RequirementArchitect, RiskStrategist, etc.)
    to register a new decision requiring human review.

    :requirement: URS-27.1
    """
    decision_id = f"dec-{str(uuid4())[:8]}"
    decision = {
        "decision_id":     decision_id,
        "urs_id":          body.urs_id,
        "decision_type":   body.decision_type,
        "agent_name":      body.agent_name or "AI Agent",
        "ai_output":       body.ai_output,
        "ai_reasoning":    body.ai_reasoning,
        "gamp5_reference": body.gamp5_reference,
        "confidence":      body.confidence,
        "status":          "pending",
        "created_at":      datetime.now(timezone.utc).isoformat(),
        "reviewed_by":     None,
        "reviewer_role":   None,
        "reviewed_at":     None,
        "override_reason": None,
        "new_value":       None,
    }
    _decisions[decision_id] = decision
    return {"status": "queued", "decision_id": decision_id}


@router.get(
    "/governance/queue",
    summary="Pending decisions awaiting human review",
)
def get_queue():
    """
    Returns all decisions with status='pending', sorted newest first.

    :requirement: URS-27.1
    """
    pending = [
        d for d in _decisions.values()
        if d["status"] == "pending"
    ]
    pending.sort(key=lambda x: x["created_at"], reverse=True)
    return {"queue": pending, "count": len(pending)}


@router.get(
    "/governance/decisions",
    summary="All decisions with optional status filter",
)
def get_decisions(status: Optional[str] = None):
    """
    Returns all decisions, optionally filtered by status.
    Status values: pending | approved | overridden | rejected

    :requirement: URS-27.1
    """
    items = list(_decisions.values())
    if status:
        items = [d for d in items if d["status"] == status]
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return {"decisions": items, "count": len(items)}


@router.post(
    "/governance/review/{decision_id}",
    summary="Human reviewer approves, overrides, or rejects a decision",
)
def review_decision(decision_id: str, body: ReviewRequest):
    """
    Records a human review verdict for an AI decision.
    For 'override': requires new_value and reason.
    For 'reject':   requires reason.
    For 'approve':  reason is optional.

    :requirement: URS-27.2 - All human overrides logged to immutable ledger.
    :requirement: URS-27.4 - Records reviewer name, role, and reason.
    """
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail="Decision not found.")

    d = _decisions[decision_id]
    if d["status"] != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Decision already reviewed (status={d['status']}).",
        )

    if body.action not in ("approve", "override", "reject"):
        raise HTTPException(
            status_code=422,
            detail="action must be 'approve', 'override', or 'reject'.",
        )

    if body.action == "override" and not body.new_value:
        raise HTTPException(
            status_code=422,
            detail="new_value is required for override action.",
        )
    if body.action in ("override", "reject") and not body.reason:
        raise HTTPException(
            status_code=422,
            detail="reason is required for override and reject actions.",
        )

    now = datetime.now(timezone.utc).isoformat()
    status_map = {
        "approve":  "approved",
        "override": "overridden",
        "reject":   "rejected",
    }
    d["status"]          = status_map[body.action]
    d["reviewed_by"]     = body.reviewer_name
    d["reviewer_role"]   = body.reviewer_role
    d["reviewed_at"]     = now
    d["override_reason"] = body.reason
    d["new_value"]       = body.new_value

    # Append to immutable override ledger
    if body.action == "override":
        _overrides.append({
            "override_id":     str(uuid4())[:8],
            "decision_id":     decision_id,
            "urs_id":          d["urs_id"],
            "decision_type":   d["decision_type"],
            "ai_said":         _summarise_ai(d),
            "human_changed_to": body.new_value,
            "reviewer_name":   body.reviewer_name,
            "reviewer_role":   body.reviewer_role,
            "reason":          body.reason,
            "reviewed_at":     now,
            "audit_hash":      _hash_override(d),
        })

    return {
        "status":      "recorded",
        "decision_id": decision_id,
        "new_status":  d["status"],
        "reviewed_at": now,
    }


@router.get(
    "/governance/overrides",
    summary="Immutable human override ledger",
)
def get_overrides():
    """
    Returns the complete, append-only ledger of all human overrides.
    This is the primary audit record for inspector review.

    :requirement: URS-27.2
    """
    return {
        "overrides": list(reversed(_overrides)),
        "count":     len(_overrides),
    }


@router.get(
    "/governance/timeline",
    summary="Audit event timeline for all decisions",
)
def get_timeline(urs_id: Optional[str] = None):
    """
    Returns a chronological list of all AI and human events,
    optionally filtered to a single URS.

    :requirement: URS-27.3
    """
    events = []
    items = _decisions.values()
    if urs_id:
        items = [d for d in items if d["urs_id"] == urs_id]

    for d in items:
        # AI generation event
        events.append({
            "timestamp":   d["created_at"],
            "event_type":  "AI_DECISION",
            "actor":       d.get("agent_name", "AI Agent"),
            "actor_type":  "AI",
            "urs_id":      d["urs_id"],
            "decision_id": d["decision_id"],
            "label":       _event_label(d["decision_type"], "ai"),
            "detail":      _summarise_ai(d),
            "status":      d["status"],
        })
        # Human review event (if completed)
        if d["reviewed_at"]:
            events.append({
                "timestamp":   d["reviewed_at"],
                "event_type":  f"HUMAN_{d['status'].upper()}",
                "actor":       d["reviewed_by"],
                "actor_type":  "Human",
                "urs_id":      d["urs_id"],
                "decision_id": d["decision_id"],
                "label":       _event_label(d["decision_type"], d["status"]),
                "detail":      (
                    d["override_reason"]
                    if d["override_reason"]
                    else f"{d['status'].capitalize()} by {d['reviewed_by']}"
                ),
                "status":      d["status"],
                "reviewer_role": d.get("reviewer_role"),
                "new_value":   d.get("new_value"),
            })

    events.sort(key=lambda x: x["timestamp"])
    return {"events": events, "count": len(events)}


@router.get(
    "/governance/stats",
    summary="Summary statistics for the Governance dashboard header",
)
def get_stats():
    """
    Returns counts by status for the governance dashboard.

    :requirement: URS-27.5
    """
    counts: Dict[str, int] = {
        "pending": 0, "approved": 0, "overridden": 0, "rejected": 0,
    }
    for d in _decisions.values():
        s = d.get("status", "pending")
        if s in counts:
            counts[s] += 1

    total = len(_decisions)
    reviewed = total - counts["pending"]
    review_rate = round((reviewed / total * 100) if total else 0)

    return {
        "total":        total,
        "pending":      counts["pending"],
        "approved":     counts["approved"],
        "overridden":   counts["overridden"],
        "rejected":     counts["rejected"],
        "review_rate":  review_rate,
        "override_count": len(_overrides),
    }


# ── Helpers ─────────────────────────────────────────────────────────

def _event_label(decision_type: str, action: str) -> str:
    """Return a short human-readable event label."""
    type_map = {
        "URS_GENERATION":       "URS Generated",
        "RISK_CLASSIFICATION":  "Risk Classified",
        "TEST_SCRIPT_GENERATED": "Test Script Generated",
        "URS_VERIFICATION":     "URS Verified",
    }
    action_map = {
        "ai":         "by AI",
        "approved":   "— Human Approved",
        "overridden": "— Human Overridden",
        "rejected":   "— Human Rejected",
    }
    base  = type_map.get(decision_type, decision_type)
    suffix = action_map.get(action, "")
    return f"{base} {suffix}".strip()
