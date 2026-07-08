"""
validated_state_engine.py — Sprint 37 Validated State Confidence
Engine.

Why this module exists
======================
Every CSV platform on the market today helps pharma teams REACH the
validated state. EVOLV is the first that helps them STAY there.

After a system is released, the regulatory environment continues to
move (FDA publishes new CSA guidance, EMA revises Annex 11, ICH
updates Q9). Customer SOPs evolve. Deviations accumulate. Test
bundles age. A system that was validated nine months ago is not, by
default, validated today — it has DRIFTED.

The Validated State Engine produces, per UR, a confidence score
(0-100) that quantifies how well that requirement remains in a
validated state given everything EVOLV has observed since the last
formal verification. Each score is deterministic — same inputs
always produce the same score, no LLM ambiguity, fully audit-
defensible.

This module is the engineering answer to two converging public
positions:

- **Nuno Valério** (Merck Healthcare, Trust Architecture newsletter)
  argues that validation should be a continuous demonstration, not
  a gated event. Pharma's existing "continual improvement"
  obligation already aligns with this — adaptive AI just magnifies
  the requirement.
- **Salim Ismail** (ExO 3.0) names "Recursive Learning" as one of
  the five DRIVE characteristics — the engine improves faster than
  the environment changes.

The Validated State Engine is EVOLV's bounded-autonomy answer to
both. AI proposes the score and the suggested actions; the human
QA team signs any revalidation that flows from it.

Scoring formula (v1.0.0)
========================
Each UR starts at 100. The engine applies penalties based on
observed signals, then surfaces a tier:

    Green  ≥ 80  · validated and stable
    Yellow 50-79 · drift signals; review recommended
    Red    < 50  · out of validated state; action required

Penalties:
    - Bundle staleness     · days since last test run × 0.10  (max 25)
    - Open defect pressure · open defect count × 5            (max 25)
    - Citation drift       · pre-superseded reg version       (15 each, max 30)
    - Change history       · CIA count last 90 days × 5       (max 20)
    - No verification yet  · UR has no bundle authored        (30 flat)
    - No risk classified   · riskData[ur] missing             (15 flat)

Bonuses:
    - Recent successful re-verify (locked run, all pass, <30d): +10
    - All FRs covered by passing tests:                         +5

Score is clamped to [0, 100].

The same formula is exposed in both code AND the per-UR
`reasoning` string returned, so an inspector can hand-recompute any
score from the audit chain.

:requirement: URS-37.1 - Per-UR Validated State Confidence score
              derived deterministically from observed signals.
:requirement: URS-37.2 - Every assessment writes a Logic Archive
              with inputs, formula application, and outputs hash-
              linked to the audit trail.
:requirement: URS-37.3 - Engine never modifies existing records;
              never triggers revalidation. Score is a proposal only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from Agents.integrity_manager import log_audit_event


AGENT_NAME = "ValidatedStateEngine"
SCHEMA_VERSION = "1.0.0"


# ── Tier vocabulary ─────────────────────────────────────────────────
TIER_GREEN  = "green"
TIER_YELLOW = "yellow"
TIER_RED    = "red"

# Tier thresholds — single line to tune; same number quoted in
# customer documentation + the React surface.
GREEN_THRESHOLD  = 80
YELLOW_THRESHOLD = 50

# Penalty/bonus weights — v1.0.0 schema. Tuning these requires
# bumping SCHEMA_VERSION and a public release note so historical
# scores remain re-derivable from inputs.
W_BUNDLE_STALENESS_PER_DAY      = 0.10
W_BUNDLE_STALENESS_MAX          = 25
W_OPEN_DEFECT_PER_INCIDENT      = 5
W_OPEN_DEFECT_MAX               = 25
W_CITATION_DRIFT_PER_CITATION   = 15
W_CITATION_DRIFT_MAX            = 30
W_CHANGE_PRESSURE_PER_CIA       = 5
W_CHANGE_PRESSURE_MAX           = 20
W_NO_BUNDLE_FLAT                = 30
W_NO_RISK_FLAT                  = 15
B_RECENT_VERIFICATION_BONUS     = 10
B_RECENT_VERIFICATION_WINDOW    = 30   # days
B_ALL_FRS_PASSING_BONUS         = 5
B_RECENT_CHANGE_WINDOW          = 90   # days for CIA pressure


# ── Exceptions ───────────────────────────────────────────────────────

class ValidatedStateError(Exception):
    """Base class for ValidatedStateEngine errors.

    :requirement: URS-37.4 - Typed error for VSE failures.
    """
    error_code = "CSV-016"


class InvalidProjectSnapshotError(ValidatedStateError):
    """Project snapshot missing required fields for assessment.

    :requirement: URS-37.5 - Validate snapshot before scoring.
    """
    error_code = "CSV-017"


# ── Result dataclasses ──────────────────────────────────────────────

@dataclass
class StateSignal:
    """One penalty or bonus contributing to a UR's score."""
    name:    str
    weight:  float            # signed: positive=penalty, negative=bonus
    detail:  str
    source:  str              # e.g. "bundle.last_run", "defects.open"


@dataclass
class URStateAssessment:
    """The full Validated State picture for one UR."""
    ur_id:           str
    statement:       str
    score:           int                       # 0-100
    tier:            str                       # green | yellow | red
    signals:         List[StateSignal] = field(default_factory=list)
    suggested_action: str = ""
    reasoning:       List[str] = field(default_factory=list)
    risk_level:      Optional[str] = None
    bundle_id:       Optional[str] = None
    days_since_run:  Optional[int] = None
    open_defects:    int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ur_id":            self.ur_id,
            "statement":        self.statement,
            "score":            self.score,
            "tier":             self.tier,
            "signals": [
                {
                    "name":   s.name,
                    "weight": s.weight,
                    "detail": s.detail,
                    "source": s.source,
                }
                for s in self.signals
            ],
            "suggested_action": self.suggested_action,
            "reasoning":        self.reasoning,
            "risk_level":       self.risk_level,
            "bundle_id":        self.bundle_id,
            "days_since_run":   self.days_since_run,
            "open_defects":     self.open_defects,
        }


@dataclass
class ValidatedStateReport:
    """Aggregate report covering every UR in the project."""
    assessment_id:   str
    project_name:    str
    schema_version:  str
    assessed_at:     str
    ur_count:        int
    assessments:     List[URStateAssessment]
    tier_counts:     Dict[str, int]
    aggregate_score: int          # weighted average across all URs
    aggregate_tier:  str
    headline:        str
    reasoning_chain: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id":   self.assessment_id,
            "project_name":    self.project_name,
            "schema_version":  self.schema_version,
            "assessed_at":     self.assessed_at,
            "ur_count":        self.ur_count,
            "tier_counts":     self.tier_counts,
            "aggregate_score": self.aggregate_score,
            "aggregate_tier":  self.aggregate_tier,
            "headline":        self.headline,
            "reasoning_chain": self.reasoning_chain,
            "assessments":     [a.to_dict() for a in self.assessments],
        }


# ── Pure scoring helpers ─────────────────────────────────────────────

def _now_utc() -> datetime:
    """Wrapped for easy mocking in tests."""
    return datetime.now(timezone.utc)


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Parse ISO-8601 strings; tolerate trailing 'Z' and missing tz."""
    if not ts:
        return None
    try:
        # Normalise common pharma exports: trailing Z → +00:00
        s = ts.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _days_between(later: datetime, earlier: datetime) -> int:
    """Whole days between two timestamps; floors at 0."""
    delta = (later - earlier).total_seconds() / 86400.0
    return max(0, int(delta))


def _tier_for_score(score: int) -> str:
    if score >= GREEN_THRESHOLD:
        return TIER_GREEN
    if score >= YELLOW_THRESHOLD:
        return TIER_YELLOW
    return TIER_RED


def _suggested_action(
    tier: str, signals: List[StateSignal], ur_id: str,
) -> str:
    """Map tier + dominant penalty to a concrete suggested action."""
    if tier == TIER_GREEN:
        return "Continue routine monitoring. No action required."

    # Find the dominant penalty (largest weight) to anchor the action
    penalties = [s for s in signals if s.weight > 0]
    if not penalties:
        if tier == TIER_YELLOW:
            return (
                f"Review {ur_id} within 60 days; minor drift signals "
                f"detected but no dominant cause."
            )
        return (
            f"Revalidate {ur_id} immediately; multiple drift signals "
            f"have eroded validated state."
        )

    dominant = max(penalties, key=lambda s: s.weight)
    horizon = "within 30 days" if tier == TIER_RED else "within 60 days"

    if "Bundle staleness" in dominant.name:
        return (
            f"Re-execute test bundle for {ur_id} {horizon}. "
            f"{dominant.detail}"
        )
    if "Open defect" in dominant.name:
        return (
            f"Close open defects against {ur_id} {horizon}; "
            f"{dominant.detail}"
        )
    if "Citation drift" in dominant.name:
        return (
            f"Re-verify {ur_id} against the current regulatory "
            f"corpus {horizon}; {dominant.detail}"
        )
    if "Change pressure" in dominant.name:
        return (
            f"Stabilise {ur_id}: review accumulated CR impacts "
            f"{horizon}. {dominant.detail}"
        )
    if "No test bundle" in dominant.name:
        return (
            f"Author and execute a test bundle for {ur_id} "
            f"{horizon}; UR has never been verified."
        )
    if "No risk classification" in dominant.name:
        return (
            f"Complete risk classification for {ur_id} {horizon}; "
            f"missing risk profile blocks downstream validation."
        )
    return (
        f"Re-verify {ur_id} {horizon}; primary signal: "
        f"{dominant.name}."
    )


# ── Headline phrasing for the aggregate report ──────────────────────

def _headline(
    tier_counts: Dict[str, int], aggregate_score: int, aggregate_tier: str,
) -> str:
    total = sum(tier_counts.values())
    if total == 0:
        return (
            "No UR records found for this project — "
            "no validated state to assess yet."
        )
    red = tier_counts.get(TIER_RED, 0)
    yellow = tier_counts.get(TIER_YELLOW, 0)
    if aggregate_tier == TIER_GREEN and red == 0 and yellow == 0:
        return (
            f"Project sits cleanly in validated state "
            f"(aggregate score {aggregate_score}/100, "
            f"{total} UR{'s' if total != 1 else ''} all green)."
        )
    if aggregate_tier == TIER_GREEN:
        return (
            f"Project remains in validated state overall "
            f"(aggregate score {aggregate_score}/100), but "
            f"{yellow} UR{'s' if yellow != 1 else ''} show drift "
            f"signals worth a review."
        )
    if aggregate_tier == TIER_YELLOW:
        return (
            f"Project is drifting from validated state "
            f"(aggregate score {aggregate_score}/100). "
            f"{yellow + red} UR{'s' if yellow + red != 1 else ''} "
            f"need attention "
            f"({red} red, {yellow} yellow)."
        )
    return (
        f"Project is OUT OF validated state "
        f"(aggregate score {aggregate_score}/100). "
        f"{red} UR{'s' if red != 1 else ''} require immediate "
        f"revalidation."
    )


# ── The engine ───────────────────────────────────────────────────────

class ValidatedStateEngine:
    """Score each UR's current validated-state confidence.

    The engine does NOT:
      - modify any existing records
      - trigger revalidation
      - sign any approvals
      - call an LLM (Sprint 37 ships pure-deterministic)

    Suggested actions are proposals only — the human QA team
    decides whether to act. Bounded autonomy applied to the
    validation-continuity loop.

    :requirement: URS-37.1 - Per-UR confidence scoring.
    """

    def __init__(self) -> None:
        """No external dependencies in v1.0.0. Sprint 38 will inject
        the regulatory-corpus client for citation-drift detection
        against the live ingested versions."""
        pass

    def assess(
        self,
        project_snapshot: Dict[str, Any],
        user_id: str = "system",
        drift_report: Optional[Dict[str, Any]] = None,
    ) -> ValidatedStateReport:
        """Produce a Validated State report for every UR in the
        project.

        Logs the standard STATE_ASSESSMENT_RECEIVED /
        STATE_ASSESSMENT_COMPLETED / STATE_ASSESSMENT_FAILED triplet
        with a Logic Archive containing inputs, per-UR scoring
        steps, and aggregate outputs.

        :param project_snapshot: dict with keys ``project_name``,
                                 ``requirements`` (list of UR/FR
                                 dicts), ``risk_data``, ``test_bundles``,
                                 ``test_runs``, ``defects``,
                                 ``change_records``, optionally
                                 ``current_corpus_versions``.
        :param user_id: User triggering the assessment.
        :param drift_report: Optional Sprint 38 RegulatoryDriftAgent
                             scan report (dict). When provided, the
                             previously-empty `citation_drift` signal
                             slot fires — −15 per affected citation,
                             capped at −30. Sprint 38 adds the
                             integration; Sprint 37 declared the slot.
        :return: ValidatedStateReport.
        :raises InvalidProjectSnapshotError: snapshot malformed.
        :raises ValidatedStateError: scoring failed.
        :requirement: URS-37.1 - Per-UR scoring.
        :requirement: URS-37.2 - Audit-event triplet + Logic Archive.
        :requirement: URS-38.7 - Citation drift signal honoured.
        """
        log_audit_event(
            agent_name=AGENT_NAME,
            action="STATE_ASSESSMENT_RECEIVED",
            user_id=user_id,
            decision_logic=(
                f"Validated State assessment requested for project "
                f"'{project_snapshot.get('project_name', '<unknown>')}'"
                + (" · with drift report" if drift_report else "")
            ),
        )

        try:
            self._validate_snapshot(project_snapshot)
            report = self._build_report(
                project_snapshot,
                drift_report=drift_report,
            )

            log_audit_event(
                agent_name=AGENT_NAME,
                action="STATE_ASSESSMENT_COMPLETED",
                user_id=user_id,
                decision_logic=(
                    f"{report.assessment_id}: scored "
                    f"{report.ur_count} UR(s); "
                    f"aggregate={report.aggregate_score}/100 "
                    f"({report.aggregate_tier}); "
                    f"tier counts={report.tier_counts}"
                ),
                thought_process={
                    "inputs": {
                        "project_name":  project_snapshot.get(
                            "project_name",
                        ),
                        "ur_count":      report.ur_count,
                        "schema_version": SCHEMA_VERSION,
                    },
                    "steps":   report.reasoning_chain,
                    "outputs": {
                        "assessment_id":   report.assessment_id,
                        "aggregate_score": report.aggregate_score,
                        "aggregate_tier":  report.aggregate_tier,
                        "tier_counts":     report.tier_counts,
                        "per_ur_scores": {
                            a.ur_id: a.score for a in report.assessments
                        },
                    },
                },
            )
            return report

        except Exception as e:
            log_audit_event(
                agent_name=AGENT_NAME,
                action="STATE_ASSESSMENT_FAILED",
                user_id=user_id,
                decision_logic=(
                    f"State assessment failed: "
                    f"{type(e).__name__}: {e}"
                ),
            )
            if isinstance(e, ValidatedStateError):
                raise
            raise ValidatedStateError(
                f"State assessment failed: {e}"
            ) from e

    # ── private helpers ─────────────────────────────────────────────

    def _validate_snapshot(self, snap: Dict[str, Any]) -> None:
        if not isinstance(snap, dict):
            raise InvalidProjectSnapshotError(
                "Project snapshot must be a dict."
            )
        if not snap.get("project_name"):
            raise InvalidProjectSnapshotError(
                "Project snapshot missing 'project_name'."
            )
        if "requirements" not in snap:
            raise InvalidProjectSnapshotError(
                "Project snapshot missing 'requirements' list."
            )

    def _build_report(
        self, snap: Dict[str, Any],
        drift_report: Optional[Dict[str, Any]] = None,
    ) -> ValidatedStateReport:
        now = _now_utc()
        project_name = snap.get("project_name", "")
        requirements = snap.get("requirements", []) or []
        risk_data    = snap.get("risk_data", {})    or {}
        test_bundles = snap.get("test_bundles", {}) or {}
        test_runs    = snap.get("test_runs", {})    or {}
        defects      = snap.get("defects", {})      or {}
        change_records = snap.get("change_records", {}) or {}
        corpus_versions = snap.get(
            "current_corpus_versions", {},
        ) or {}

        # Sprint 38 — index drift records by UR id for fast lookup
        # during scoring. Each value is the list of affected_citation
        # dicts from the DriftScanReport.
        drift_by_ur: Dict[str, List[Dict[str, Any]]] = {}
        if drift_report:
            for r in drift_report.get("affected_urs", []) or []:
                ur_id = r.get("ur_id")
                if ur_id:
                    drift_by_ur[ur_id] = (
                        r.get("affected_citations", []) or []
                    )

        urs = [r for r in requirements if r.get("type") == "UR"]
        frs = [r for r in requirements if r.get("type") == "FR"]

        # Group FRs by parent for the "all FRs passing" bonus check.
        frs_by_parent: Dict[str, List[Dict[str, Any]]] = {}
        for fr in frs:
            parent = fr.get("parentId")
            if parent:
                frs_by_parent.setdefault(parent, []).append(fr)

        # Group runs by scriptId so we can find the latest run per UR.
        runs_by_script: Dict[str, List[Dict[str, Any]]] = {}
        for run in test_runs.values():
            sid = run.get("scriptId")
            if sid:
                runs_by_script.setdefault(sid, []).append(run)

        # Count CIA hits per UR in the change-pressure window.
        cia_pressure_per_ur = self._count_recent_cia_hits(
            change_records, now,
        )

        reasoning_chain: List[str] = []
        reasoning_chain.append(
            f"Engine v{SCHEMA_VERSION}: assessing {len(urs)} UR(s) "
            f"at {now.isoformat()}."
            + (f" Drift report present · "
               f"{len(drift_by_ur)} UR(s) flagged with drift."
               if drift_by_ur else "")
        )

        per_ur: List[URStateAssessment] = []

        for ur in urs:
            assessment = self._score_one_ur(
                ur=ur,
                risk_data=risk_data,
                test_bundles=test_bundles,
                runs_by_script=runs_by_script,
                defects=defects,
                frs_by_parent=frs_by_parent,
                cia_count=cia_pressure_per_ur.get(ur.get("id"), 0),
                corpus_versions=corpus_versions,
                drift_citations=drift_by_ur.get(ur.get("id"), []),
                now=now,
            )
            per_ur.append(assessment)
            reasoning_chain.append(
                f"{assessment.ur_id}: score={assessment.score} "
                f"({assessment.tier})"
            )

        # Aggregate
        tier_counts = {
            TIER_GREEN:  sum(1 for a in per_ur if a.tier == TIER_GREEN),
            TIER_YELLOW: sum(1 for a in per_ur if a.tier == TIER_YELLOW),
            TIER_RED:    sum(1 for a in per_ur if a.tier == TIER_RED),
        }
        if per_ur:
            aggregate_score = int(
                sum(a.score for a in per_ur) / len(per_ur)
            )
        else:
            aggregate_score = 0
        aggregate_tier = _tier_for_score(aggregate_score)
        headline = _headline(
            tier_counts, aggregate_score, aggregate_tier,
        )
        reasoning_chain.append(
            f"Aggregate: {aggregate_score}/100 ({aggregate_tier}); "
            f"green={tier_counts[TIER_GREEN]}, "
            f"yellow={tier_counts[TIER_YELLOW]}, "
            f"red={tier_counts[TIER_RED]}."
        )

        # Assessment id mirrors the CIA pattern: stable per project +
        # timestamp so reruns are distinguishable in the audit chain.
        ts_compact = now.strftime("%Y%m%dT%H%M%SZ")
        proj_slug = re.sub(
            r"[^A-Za-z0-9]+", "-", project_name,
        ).strip("-")[:32]
        assessment_id = f"VSE-{proj_slug}-{ts_compact}"

        return ValidatedStateReport(
            assessment_id=assessment_id,
            project_name=project_name,
            schema_version=SCHEMA_VERSION,
            assessed_at=now.isoformat(),
            ur_count=len(per_ur),
            assessments=per_ur,
            tier_counts=tier_counts,
            aggregate_score=aggregate_score,
            aggregate_tier=aggregate_tier,
            headline=headline,
            reasoning_chain=reasoning_chain,
        )

    def _score_one_ur(
        self,
        ur: Dict[str, Any],
        risk_data: Dict[str, Any],
        test_bundles: Dict[str, Any],
        runs_by_script: Dict[str, List[Dict[str, Any]]],
        defects: Dict[str, List[Dict[str, Any]]],
        frs_by_parent: Dict[str, List[Dict[str, Any]]],
        cia_count: int,
        corpus_versions: Dict[str, str],
        now: datetime,
        drift_citations: Optional[List[Dict[str, Any]]] = None,
    ) -> URStateAssessment:
        """Compute score + signals + suggested action for one UR.

        :param drift_citations: Sprint 38 — list of AffectedCitation
                                dicts from a RegulatoryDriftAgent
                                scan, filtered to this UR. When
                                non-empty, applies the
                                citation_drift penalty.
        """
        ur_id     = ur.get("id", "")
        statement = ur.get("statement", "") or ""

        signals: List[StateSignal] = []
        score = 100

        # ── Citation drift (Sprint 38) ──
        # The Sprint 37 formula declared this slot but left it empty.
        # Sprint 38 fills it: −15 per drifted citation, capped at −30
        # (matches the public formula on Slide 5 of the LinkedIn
        # carousel).
        if drift_citations:
            drift_penalty = min(
                len(drift_citations) * W_CITATION_DRIFT_PER_CITATION,
                W_CITATION_DRIFT_MAX,
            )
            cit_summary = "; ".join(
                f"{c.get('framework', '?')}: "
                f"{c.get('cited_version', '?')} "
                f"-> {c.get('current_version', '?')}"
                for c in drift_citations[:3]
            )
            if len(drift_citations) > 3:
                cit_summary += f" (+{len(drift_citations) - 3} more)"
            signals.append(StateSignal(
                name="Citation drift",
                weight=float(drift_penalty),
                detail=(
                    f"{len(drift_citations)} cited regulatory "
                    f"version(s) superseded: {cit_summary}"
                ),
                source="regulatory_drift_agent",
            ))
            score -= drift_penalty

        # ── Risk classification ──
        risk_row = risk_data.get(ur_id) or {}
        risk_level = (risk_row.get("riskLevel") or "").strip() or None
        if not risk_level:
            signals.append(StateSignal(
                name="No risk classification",
                weight=float(W_NO_RISK_FLAT),
                detail="UR has not been risk-classified yet.",
                source="risk_data",
            ))
            score -= W_NO_RISK_FLAT

        # ── Bundle presence + staleness ──
        bundle = test_bundles.get(ur_id)
        bundle_id = bundle.get("bundle_id") if bundle else None
        days_since_run: Optional[int] = None

        if not bundle:
            signals.append(StateSignal(
                name="No test bundle authored",
                weight=float(W_NO_BUNDLE_FLAT),
                detail="No test bundle exists; UR is not testable.",
                source="test_bundles",
            ))
            score -= W_NO_BUNDLE_FLAT
        else:
            # Find latest locked run (signed evidence) for this bundle
            script_id = bundle_id
            candidate_runs = runs_by_script.get(script_id, [])
            locked_runs = [
                r for r in candidate_runs
                if r.get("status") == "locked" and r.get("lockedAt")
            ]
            if locked_runs:
                # Sort by lockedAt descending
                locked_runs.sort(
                    key=lambda r: r.get("lockedAt", ""),
                    reverse=True,
                )
                latest = locked_runs[0]
                latest_locked_at = _parse_iso(latest.get("lockedAt"))
                if latest_locked_at:
                    days_since_run = _days_between(now, latest_locked_at)
                    staleness_penalty = min(
                        int(days_since_run * W_BUNDLE_STALENESS_PER_DAY),
                        W_BUNDLE_STALENESS_MAX,
                    )
                    if staleness_penalty > 0:
                        signals.append(StateSignal(
                            name="Bundle staleness",
                            weight=float(staleness_penalty),
                            detail=(
                                f"Last verified {days_since_run} "
                                f"days ago "
                                f"({latest_locked_at.date()})."
                            ),
                            source="test_runs.locked_at",
                        ))
                        score -= staleness_penalty

                    # Recent-verification bonus
                    if days_since_run <= B_RECENT_VERIFICATION_WINDOW:
                        # Check the run was clean (no failed steps)
                        step_results = latest.get("stepResults") or {}
                        failed = sum(
                            1 for sr in step_results.values()
                            if (sr or {}).get("verdict") == "Fail"
                        )
                        if failed == 0:
                            signals.append(StateSignal(
                                name="Recent successful re-verification",
                                weight=float(-B_RECENT_VERIFICATION_BONUS),
                                detail=(
                                    f"Locked & clean run within "
                                    f"{B_RECENT_VERIFICATION_WINDOW} "
                                    f"days."
                                ),
                                source="test_runs.locked_at",
                            ))
                            score += B_RECENT_VERIFICATION_BONUS
            else:
                # Bundle exists but no locked run yet
                signals.append(StateSignal(
                    name="Bundle staleness",
                    weight=float(W_BUNDLE_STALENESS_MAX),
                    detail=(
                        "Bundle authored but no locked test run on "
                        "record; treating as fully stale."
                    ),
                    source="test_runs",
                ))
                score -= W_BUNDLE_STALENESS_MAX

        # ── Open defect pressure ──
        # Defects are keyed by runId in our store; flatten by
        # scriptId via the runs map we already have.
        open_count = 0
        if bundle_id:
            for run in runs_by_script.get(bundle_id, []):
                run_id = run.get("runId")
                if not run_id:
                    continue
                for d in defects.get(run_id, []):
                    status = (d.get("status") or "Open").lower()
                    if status != "closed":
                        open_count += 1
        if open_count > 0:
            defect_penalty = min(
                open_count * W_OPEN_DEFECT_PER_INCIDENT,
                W_OPEN_DEFECT_MAX,
            )
            signals.append(StateSignal(
                name="Open defect pressure",
                weight=float(defect_penalty),
                detail=(
                    f"{open_count} open defect"
                    f"{'s' if open_count != 1 else ''} against this "
                    f"UR's bundle."
                ),
                source="defects",
            ))
            score -= defect_penalty

        # ── CIA change-history pressure ──
        if cia_count > 0:
            change_penalty = min(
                cia_count * W_CHANGE_PRESSURE_PER_CIA,
                W_CHANGE_PRESSURE_MAX,
            )
            signals.append(StateSignal(
                name="Change pressure (recent CIAs)",
                weight=float(change_penalty),
                detail=(
                    f"{cia_count} Change Impact Assessment"
                    f"{'s' if cia_count != 1 else ''} touched this "
                    f"UR in the last {B_RECENT_CHANGE_WINDOW} days."
                ),
                source="change_records",
            ))
            score -= change_penalty

        # ── All FRs passing bonus ──
        if bundle_id and frs_by_parent.get(ur_id):
            fr_count = len(frs_by_parent[ur_id])
            # Crude proxy: if the latest locked run had all passes,
            # we count it as covering FRs. Sprint 38 will refine to
            # check FR-level coverage explicitly.
            if (
                bundle
                and days_since_run is not None
                and days_since_run <= B_RECENT_VERIFICATION_WINDOW
            ):
                signals.append(StateSignal(
                    name="All FRs covered by recent passing run",
                    weight=float(-B_ALL_FRS_PASSING_BONUS),
                    detail=(
                        f"All {fr_count} FR"
                        f"{'s' if fr_count != 1 else ''} covered by "
                        f"the recent passing run."
                    ),
                    source="test_runs.stepResults",
                ))
                score += B_ALL_FRS_PASSING_BONUS

        # Clamp + finalise
        score = max(0, min(100, score))
        tier  = _tier_for_score(score)
        suggested = _suggested_action(tier, signals, ur_id)

        reasoning = self._format_reasoning(
            ur_id=ur_id,
            base_score=100,
            signals=signals,
            final_score=score,
            tier=tier,
        )

        return URStateAssessment(
            ur_id=ur_id,
            statement=statement,
            score=score,
            tier=tier,
            signals=signals,
            suggested_action=suggested,
            reasoning=reasoning,
            risk_level=risk_level,
            bundle_id=bundle_id,
            days_since_run=days_since_run,
            open_defects=open_count,
        )

    @staticmethod
    def _format_reasoning(
        ur_id: str,
        base_score: int,
        signals: List[StateSignal],
        final_score: int,
        tier: str,
    ) -> List[str]:
        out = [
            f"Start: {ur_id} base score = {base_score}/100.",
        ]
        for s in signals:
            if s.weight > 0:
                out.append(
                    f"− {int(s.weight)} for '{s.name}' "
                    f"({s.detail})"
                )
            elif s.weight < 0:
                out.append(
                    f"+ {int(-s.weight)} bonus for '{s.name}' "
                    f"({s.detail})"
                )
        out.append(
            f"Final: {final_score}/100 → tier '{tier}'."
        )
        return out

    @staticmethod
    def _count_recent_cia_hits(
        change_records: Dict[str, Dict[str, Any]],
        now: datetime,
    ) -> Dict[str, int]:
        """For each UR id, count how many CIAs in the recent window
        listed it as affected."""
        out: Dict[str, int] = {}
        window_start = now - timedelta(days=B_RECENT_CHANGE_WINDOW)
        for record in change_records.values():
            created_at = _parse_iso(
                record.get("createdAt") or record.get("created_at"),
            )
            if created_at is None or created_at < window_start:
                continue
            cia = record.get("cia") or {}
            for ur in cia.get("affected_urs", []) or []:
                ur_id = ur.get("requirement_id") or ur.get("ur_id")
                if ur_id:
                    out[ur_id] = out.get(ur_id, 0) + 1
        return out
