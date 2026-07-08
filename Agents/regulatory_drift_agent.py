"""
regulatory_drift_agent.py — Sprint 38 Regulatory Drift Detection.

Why this module exists
======================
The Validated State Confidence Engine (Sprint 37) declared a
"citation drift" signal slot in its scoring formula. The slot was
empty. This module fills it.

When a regulatory framework version updates in EVOLV's ingested
corpus (FDA publishes new CSA guidance, EMA revises Annex 11, ICH
updates Q9), this scanner walks every UR in a project, identifies
which ones cite the now-superseded version, and surfaces them with
per-UR reasoning and proposed actions.

This is the **first cross-platform feature competitors cannot
replicate** without comparable audit-chain infrastructure. ValGenesis,
Veeva Vault QMS, and Kneat do not detect regulatory drift today. For
Indian CDMOs juggling FDA + EMA + MHRA + CDSCO simultaneously, this
is the single most expensive manual cost in a QA team's calendar.

Bounded autonomy
================
The agent reads. The agent proposes. The agent never:
- modifies any UR
- triggers revalidation
- signs any approval
- modifies the audit chain
- calls an LLM (Sprint 38 ships pure-deterministic)

The Permission Envelope is declared in
`Agents/agent_passports.py` under "RegulatoryDriftAgent".

Detection strategy (v1.0.0)
===========================
For each UR, citations come from two sources:

1. **Explicit** — UR's ``reg_versions_cited`` field (set by
   RequirementArchitect when generated; may be missing for
   manually-authored or demo URs).
2. **Text-scan fallback** — substring match of known framework
   names against the UR's statement. Catches the most common case
   (UR statements that explicitly mention "21 CFR Part 11" etc.)
   without requiring backend→frontend citation plumbing.

If the cited version is in the framework's ``previous_versions``
list AND differs from ``current_version``, the citation is flagged
as drifted. Score penalty propagates through the ValidatedStateEngine
in its citation_drift signal slot.

:requirement: URS-38.1 - Detect URs citing superseded regulatory
              versions against the ingested corpus.
:requirement: URS-38.2 - Every scan writes a Logic Archive with
              inputs, per-UR scanning steps, and outputs hash-
              linked to the audit trail.
:requirement: URS-38.3 - Agent never modifies records; never
              triggers revalidation. Bounded autonomy enforced.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from Agents.integrity_manager import log_audit_event


AGENT_NAME = "RegulatoryDriftAgent"
SCHEMA_VERSION = "1.0.0"

# Default registry location. Tests override this with a temp path.
_DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent
    / "output" / "corpus_versions.json"
)

# Known framework names for the text-scan fallback. Order matters for
# precedence: longer/more-specific names listed first so e.g.
# "21 CFR Part 11" wins over a substring match on "21 CFR".
_FRAMEWORK_PATTERNS: List[tuple] = [
    ("21 CFR Part 11",      r"\b21\s*CFR\s*Part\s*11\b"),
    ("21 CFR Part 820",     r"\b21\s*CFR\s*Part\s*820\b"),
    ("EU GMP Annex 11",     r"\b(?:EU\s*GMP\s*)?Annex\s*11\b"),
    ("GAMP 5",              r"\bGAMP\s*5\b"),
    ("FDA CSA Guidance",    r"\b(?:FDA\s*)?CSA\s*(?:Guidance)?\b"),
    ("FDA PCCP Guidance",   r"\b(?:FDA\s*)?PCCP\s*(?:Guidance)?\b"),
    ("ICH Q9",              r"\bICH\s*Q9\b"),
    ("ICH Q10",             r"\bICH\s*Q10\b"),
]


# ── Exceptions ───────────────────────────────────────────────────────

class RegulatoryDriftError(Exception):
    """Base class for RegulatoryDriftAgent errors.

    :requirement: URS-38.4 - Typed error for drift-scan failures.
    """
    error_code = "CSV-018"


class CorpusRegistryError(RegulatoryDriftError):
    """The corpus version registry could not be loaded or is malformed.

    :requirement: URS-38.5 - Validate registry shape before scanning.
    """
    error_code = "CSV-019"


# ── Result dataclasses ───────────────────────────────────────────────

@dataclass
class AffectedCitation:
    """One citation that has drifted (cited version superseded)."""
    framework:        str
    cited_version:    str
    current_version:  str
    superseded_at:    str
    detection_source: str   # "explicit" or "text-scan"


@dataclass
class URDriftRecord:
    """Per-UR drift result with proposed action."""
    ur_id:               str
    statement:           str
    affected_citations:  List[AffectedCitation] = field(default_factory=list)
    suggested_action:    str = ""


@dataclass
class DriftScanReport:
    """Aggregate scan result returned by the agent."""
    scan_id:              str
    project_name:         str
    schema_version:       str
    scanned_at:           str
    frameworks_checked:   List[str]
    ur_count:             int
    affected_ur_count:    int
    affected_urs:         List[URDriftRecord]
    headline:             str
    reasoning_chain:      List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_id":            self.scan_id,
            "project_name":       self.project_name,
            "schema_version":     self.schema_version,
            "scanned_at":         self.scanned_at,
            "frameworks_checked": self.frameworks_checked,
            "ur_count":           self.ur_count,
            "affected_ur_count":  self.affected_ur_count,
            "headline":           self.headline,
            "reasoning_chain":    self.reasoning_chain,
            "affected_urs": [
                {
                    "ur_id":            r.ur_id,
                    "statement":        r.statement,
                    "suggested_action": r.suggested_action,
                    "affected_citations": [
                        {
                            "framework":        c.framework,
                            "cited_version":    c.cited_version,
                            "current_version":  c.current_version,
                            "superseded_at":    c.superseded_at,
                            "detection_source": c.detection_source,
                        }
                        for c in r.affected_citations
                    ],
                }
                for r in self.affected_urs
            ],
        }


# ── Corpus registry helpers ──────────────────────────────────────────

def load_corpus_versions(
    registry_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load the ingested-version registry from disk.

    :param registry_path: Override path for testing. Defaults to
                          ``output/corpus_versions.json`` at project root.
    :return: Parsed registry dict.
    :raises CorpusRegistryError: File missing, unreadable, or malformed.
    :requirement: URS-38.6 - Load corpus version registry from disk.
    """
    path = registry_path or _DEFAULT_REGISTRY_PATH
    try:
        with open(path, "r", encoding="utf-8") as f:
            registry = json.load(f)
    except FileNotFoundError:
        raise CorpusRegistryError(
            f"Corpus version registry not found at {path}. "
            "Run scripts/ingest_docs.py to seed the registry."
        )
    except json.JSONDecodeError as e:
        raise CorpusRegistryError(
            f"Corpus registry is malformed: {e}"
        )

    if not isinstance(registry, dict):
        raise CorpusRegistryError(
            "Corpus registry root must be a dict."
        )
    if "frameworks" not in registry:
        raise CorpusRegistryError(
            "Corpus registry missing required 'frameworks' key."
        )
    return registry


# ── Detection helpers ────────────────────────────────────────────────

def _scan_statement_for_frameworks(statement: str) -> List[str]:
    """Text-scan fallback: which framework names appear in the
    UR statement?"""
    if not statement:
        return []
    found = []
    for name, pattern in _FRAMEWORK_PATTERNS:
        if re.search(pattern, statement, re.IGNORECASE):
            found.append(name)
    return found


def _is_version_superseded(
    framework_record: Dict[str, Any],
    cited_version: str,
) -> Optional[Dict[str, Any]]:
    """If `cited_version` is in the framework's previous_versions
    list, return the matching record; otherwise None."""
    if not cited_version:
        return None
    current = framework_record.get("current_version", "")
    if cited_version == current:
        return None
    for prev in framework_record.get("previous_versions", []) or []:
        if prev.get("version") == cited_version:
            return prev
    return None


# ── The agent ────────────────────────────────────────────────────────

class RegulatoryDriftAgent:
    """Scan a project for URs citing superseded regulatory versions.

    The agent does NOT:
      - modify any UR
      - trigger revalidation
      - sign any approval
      - call an LLM (Sprint 38 ships pure-deterministic; LLM
        augmentation with semantic citation matching is Sprint 40)

    Suggested actions are proposals only; the human QA team decides
    whether to act. Bounded autonomy applied to the regulatory-
    surveillance loop.

    :requirement: URS-38.1 - Detect superseded citations across URs.
    """

    def __init__(
        self,
        registry_path: Optional[Path] = None,
    ) -> None:
        """Construct the agent. Registry path is optional; defaults
        to the canonical location. Used for test isolation."""
        self._registry_path = registry_path

    def scan(
        self,
        project_snapshot: Dict[str, Any],
        corpus_versions: Optional[Dict[str, Any]] = None,
        user_id: str = "system",
    ) -> DriftScanReport:
        """Run a drift scan over every UR in the project.

        Logs the standard ``DRIFT_SCAN_RECEIVED`` /
        ``DRIFT_SCAN_COMPLETED`` / ``DRIFT_SCAN_FAILED`` triplet plus
        a Logic Archive with inputs, per-UR scanning steps, and
        outputs for inspector re-derivation.

        :param project_snapshot: dict with ``project_name`` and
                                 ``requirements`` (list of UR/FR
                                 dicts). Requirements may carry an
                                 optional ``reg_versions_cited``
                                 list; if missing, the text-scan
                                 fallback runs against the statement.
        :param corpus_versions: Override the loaded registry (e.g.
                                for testing). If None, loads from
                                disk.
        :param user_id: User triggering the scan.
        :return: DriftScanReport.
        :raises CorpusRegistryError: Registry unloadable.
        :raises RegulatoryDriftError: Scan failed.
        :requirement: URS-38.1 - Per-UR drift detection.
        :requirement: URS-38.2 - Audit triplet + Logic Archive.
        """
        log_audit_event(
            agent_name=AGENT_NAME,
            action="DRIFT_SCAN_RECEIVED",
            user_id=user_id,
            decision_logic=(
                f"Drift scan requested for project "
                f"'{project_snapshot.get('project_name', '<unknown>')}'"
            ),
        )

        try:
            if corpus_versions is None:
                registry = load_corpus_versions(self._registry_path)
            else:
                registry = corpus_versions

            report = self._build_report(project_snapshot, registry)

            log_audit_event(
                agent_name=AGENT_NAME,
                action="DRIFT_SCAN_COMPLETED",
                user_id=user_id,
                decision_logic=(
                    f"{report.scan_id}: scanned {report.ur_count} UR(s) "
                    f"against {len(report.frameworks_checked)} framework(s); "
                    f"{report.affected_ur_count} UR(s) flagged as drifted."
                ),
                thought_process={
                    "inputs": {
                        "project_name":  report.project_name,
                        "ur_count":      report.ur_count,
                        "frameworks_checked": report.frameworks_checked,
                        "schema_version": SCHEMA_VERSION,
                    },
                    "steps":   report.reasoning_chain,
                    "outputs": {
                        "scan_id":           report.scan_id,
                        "affected_ur_count": report.affected_ur_count,
                        "affected_ur_ids": [
                            r.ur_id for r in report.affected_urs
                        ],
                    },
                },
            )
            return report

        except Exception as e:
            log_audit_event(
                agent_name=AGENT_NAME,
                action="DRIFT_SCAN_FAILED",
                user_id=user_id,
                decision_logic=(
                    f"Drift scan failed: "
                    f"{type(e).__name__}: {e}"
                ),
            )
            if isinstance(e, RegulatoryDriftError):
                raise
            raise RegulatoryDriftError(
                f"Drift scan failed: {e}"
            ) from e

    # ── private helpers ─────────────────────────────────────────────

    def _build_report(
        self,
        snap: Dict[str, Any],
        registry: Dict[str, Any],
    ) -> DriftScanReport:
        now = datetime.now(timezone.utc)
        project_name = snap.get("project_name", "")
        requirements = snap.get("requirements", []) or []
        urs = [r for r in requirements if r.get("type") == "UR"]

        frameworks = registry.get("frameworks", {}) or {}
        framework_names = sorted(frameworks.keys())

        reasoning: List[str] = [
            f"Engine v{SCHEMA_VERSION}: scanning {len(urs)} UR(s) "
            f"against {len(framework_names)} framework(s) "
            f"at {now.isoformat()}.",
        ]

        affected: List[URDriftRecord] = []

        for ur in urs:
            record = self._scan_one_ur(ur, frameworks)
            if record.affected_citations:
                affected.append(record)
                cit_summary = ", ".join(
                    f"{c.framework} ({c.cited_version}"
                    f" → {c.current_version})"
                    for c in record.affected_citations
                )
                reasoning.append(
                    f"{record.ur_id}: drift detected · {cit_summary}"
                )

        if affected:
            reasoning.append(
                f"Conclusion: {len(affected)} UR(s) cite at least one "
                f"superseded regulatory version. Recommended: "
                f"re-assess Validated State to surface revised scores."
            )
            headline = (
                f"{len(affected)} of {len(urs)} UR(s) "
                f"cite at least one superseded regulatory version."
            )
        else:
            reasoning.append(
                "Conclusion: no URs reference superseded versions. "
                "Project citations are aligned with the current "
                "ingested corpus."
            )
            headline = (
                f"All {len(urs)} UR citations align with the current "
                f"ingested corpus. No drift detected."
            )

        proj_slug = re.sub(
            r"[^A-Za-z0-9]+", "-", project_name,
        ).strip("-")[:32]
        ts_compact = now.strftime("%Y%m%dT%H%M%SZ")
        scan_id = f"DRIFT-{proj_slug}-{ts_compact}"

        return DriftScanReport(
            scan_id=scan_id,
            project_name=project_name,
            schema_version=SCHEMA_VERSION,
            scanned_at=now.isoformat(),
            frameworks_checked=framework_names,
            ur_count=len(urs),
            affected_ur_count=len(affected),
            affected_urs=affected,
            headline=headline,
            reasoning_chain=reasoning,
        )

    def _scan_one_ur(
        self,
        ur: Dict[str, Any],
        frameworks: Dict[str, Any],
    ) -> URDriftRecord:
        """Compute the drift record for a single UR."""
        ur_id     = ur.get("id", "")
        statement = ur.get("statement", "") or ""

        affected: List[AffectedCitation] = []
        seen_keys: set = set()  # dedupe (framework, cited_version) pairs

        # Strategy 1: explicit reg_versions_cited list
        # Each entry is treated as a "framework name | version"
        # pair if it contains a delimiter, otherwise the agent
        # tries to match it to a framework's previous_version list.
        for cited in ur.get("reg_versions_cited", []) or []:
            framework_name, cited_version = self._split_citation(cited)
            if not framework_name:
                continue
            fw = frameworks.get(framework_name)
            if not fw:
                continue
            prev = _is_version_superseded(fw, cited_version)
            if prev is None:
                continue
            key = (framework_name, cited_version)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            affected.append(AffectedCitation(
                framework=framework_name,
                cited_version=cited_version,
                current_version=fw.get("current_version", ""),
                superseded_at=prev.get("superseded_at", ""),
                detection_source="explicit",
            ))

        # Strategy 2: text-scan fallback against the statement.
        # If the UR mentions a framework by name AND that framework
        # has any previous_versions, we conservatively assume the UR
        # was originally drafted against the prior version. This is
        # a defensible v1.0.0 heuristic — Sprint 40 will replace it
        # with LLM/embedding semantic matching.
        mentioned = _scan_statement_for_frameworks(statement)
        for framework_name in mentioned:
            fw = frameworks.get(framework_name)
            if not fw:
                continue
            previous = fw.get("previous_versions", []) or []
            if not previous:
                continue
            # Pick the most recently superseded version as the
            # presumed "cited" version. Pharma teams rarely cite
            # the oldest possible version of a framework; the most
            # recent prior version is the conservative match.
            prev = max(
                previous,
                key=lambda p: p.get("superseded_at", ""),
            )
            cited_version = prev.get("version", "")
            key = (framework_name, cited_version)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            affected.append(AffectedCitation(
                framework=framework_name,
                cited_version=cited_version,
                current_version=fw.get("current_version", ""),
                superseded_at=prev.get("superseded_at", ""),
                detection_source="text-scan",
            ))

        suggested = self._suggested_action(ur_id, affected)

        return URDriftRecord(
            ur_id=ur_id,
            statement=statement,
            affected_citations=affected,
            suggested_action=suggested,
        )

    @staticmethod
    def _split_citation(cited: str) -> tuple:
        """Parse a citation string into (framework_name, version).

        Accepts formats:
          'GAMP 5 Rev 2 (2022)'        → ('GAMP 5', 'Rev 2 (2022)')
          '21 CFR Part 11 | 1997 original' → ('21 CFR Part 11', '1997 original')
          'GAMP5_Guide'                → ('GAMP 5', 'GAMP5_Guide')

        Returns (None, None) if no framework can be identified.
        """
        if not cited:
            return (None, None)

        # Explicit pipe-delimited form
        if "|" in cited:
            parts = cited.split("|", 1)
            return (parts[0].strip(), parts[1].strip())

        # Try matching against known framework names — longest first.
        # The remainder of the string becomes the version.
        for name, pattern in _FRAMEWORK_PATTERNS:
            m = re.search(pattern, cited, re.IGNORECASE)
            if m:
                rest = (cited[:m.start()] + cited[m.end():]).strip()
                return (name, rest if rest else cited)

        return (None, None)

    @staticmethod
    def _suggested_action(
        ur_id: str, affected: List[AffectedCitation],
    ) -> str:
        if not affected:
            return ""
        if len(affected) == 1:
            c = affected[0]
            return (
                f"Re-verify {ur_id} against {c.framework} "
                f"{c.current_version} within 60 days; "
                f"cited version ({c.cited_version}) was superseded "
                f"on {c.superseded_at[:10]}."
            )
        frameworks_list = ", ".join(
            sorted({c.framework for c in affected})
        )
        return (
            f"Re-verify {ur_id} against current {frameworks_list} "
            f"within 60 days; {len(affected)} cited version(s) "
            f"have been superseded."
        )
