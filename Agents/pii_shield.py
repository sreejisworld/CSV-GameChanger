"""
pii_shield.py - Real-time PII / PHI detection for AI inputs.

Sprint 51 ("AI Input Safety Layer"). A deterministic, dependency-
free screen that inspects free text *before* it crosses the tenant
boundary to an external model (OpenAI embeddings, the Anthropic
eval judge) or vector store (Pinecone).

Why this exists
---------------
EVOLV sends user-authored requirement text to OpenAI (for
embeddings) and Pinecone (for retrieval). In a GxP tenant that
text can accidentally contain PII/PHI - a patient name pasted into
a workshop note, an MRN in a deviation description, a contact
email. Big-pharma agentic-AI standards (e.g. Amgen's internal
"Real-time PII detection, education & consent warnings") require a
control at exactly this boundary.

Design
------
* Deterministic regex + Luhn - no LLM, no network, fully
  reproducible, and therefore validatable (matches EVOLV's
  deterministic-guardrail pattern; see [[reproducibility]]).
* Never persists raw PII. Findings carry category, sensitivity,
  and character offsets only - the matched value is masked. The
  audit trail records category *counts*, never values, so the
  trail never itself becomes a PII store.
* Configurable enforcement via ``EVOLV_PII_MODE``:
  ``off`` | ``warn`` (default) | ``redact`` | ``block``.

:requirement: URS-51.1 - Detect PII/PHI entities in free-text
              inputs before external transmission.
:requirement: URS-51.4 - Screen PII/PHI without persisting raw
              matched values to any log or artifact.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


# -----------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------

class PIIShieldError(Exception):
    """Base error for the PII shield. Error code: CSV-051."""

    error_code = "CSV-051"


class PIIBlockedError(PIIShieldError):
    """
    Raised when PII/PHI is detected and enforcement mode is
    ``block``. Error code: CSV-052.
    """

    error_code = "CSV-052"


# -----------------------------------------------------------------
# Enums
# -----------------------------------------------------------------

class Sensitivity(str, Enum):
    """Relative sensitivity of a detected entity."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


_SENS_RANK: Dict["Sensitivity", int] = {
    Sensitivity.LOW: 1,
    Sensitivity.MEDIUM: 2,
    Sensitivity.HIGH: 3,
}


class PIICategory(str, Enum):
    """Category of detected PII / PHI."""

    EMAIL = "Email"
    PHONE = "Phone"
    US_SSN = "US_SSN"
    CREDIT_CARD = "Credit_Card"
    IP_ADDRESS = "IP_Address"
    DATE_OF_BIRTH = "Date_Of_Birth"
    MRN = "Medical_Record_Number"
    PATIENT_NAME = "Patient_Name"


class ScreenMode(str, Enum):
    """
    Enforcement mode applied at the tenant boundary.

    off    - screening disabled (text passes through unchanged).
    warn   - detect + audit, but still transmit the raw text.
    redact - replace detected entities before transmission.
    block  - refuse transmission (raise ``PIIBlockedError``).
    """

    OFF = "off"
    WARN = "warn"
    REDACT = "redact"
    BLOCK = "block"


class ScreenDecision(str, Enum):
    """Outcome of a screen call."""

    ALLOW_CLEAN = "allow_clean"
    ALLOW_FLAGGED = "allow_flagged"
    REDACTED = "redacted"
    BLOCKED = "blocked"


_CATEGORY_SENSITIVITY: Dict["PIICategory", "Sensitivity"] = {
    PIICategory.EMAIL: Sensitivity.MEDIUM,
    PIICategory.PHONE: Sensitivity.MEDIUM,
    PIICategory.US_SSN: Sensitivity.HIGH,
    PIICategory.CREDIT_CARD: Sensitivity.HIGH,
    PIICategory.IP_ADDRESS: Sensitivity.LOW,
    PIICategory.DATE_OF_BIRTH: Sensitivity.HIGH,
    PIICategory.MRN: Sensitivity.HIGH,
    PIICategory.PATIENT_NAME: Sensitivity.HIGH,
}


# -----------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------

@dataclass(frozen=True)
class PIIFinding:
    """
    A single detected entity.

    Deliberately stores *no raw value* - only the category,
    sensitivity, character offsets, and the detector that fired.
    ``masked`` is the safe display token.

    :requirement: URS-51.4 - No raw PII is persisted.
    """

    category: PIICategory
    sensitivity: Sensitivity
    start: int
    end: int
    detector: str

    @property
    def masked(self) -> str:
        """Safe, value-free display token."""
        return f"[{self.category.value}]"

    def to_dict(self) -> Dict[str, object]:
        """Serialise without exposing the matched value."""
        return {
            "category": self.category.value,
            "sensitivity": self.sensitivity.value,
            "start": self.start,
            "end": self.end,
            "detector": self.detector,
            "masked": self.masked,
        }


@dataclass
class PIIScreenResult:
    """
    Result of a ``screen_text()`` call.

    ``text_out`` is the text that should be transmitted
    downstream - unchanged in warn/off mode, redacted in redact
    mode, and the (untouched) original in block mode where the
    caller is expected not to transmit at all.
    """

    decision: ScreenDecision
    mode: ScreenMode
    findings: List[PIIFinding]
    text_out: str
    original_length: int

    @property
    def has_pii(self) -> bool:
        """True when at least one entity was detected."""
        return bool(self.findings)

    @property
    def category_counts(self) -> Dict[str, int]:
        """Map of category -> count (value-free)."""
        counts: Dict[str, int] = {}
        for f in self.findings:
            key = f.category.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    @property
    def max_sensitivity(self) -> Optional[str]:
        """Highest sensitivity across findings, or None."""
        if not self.findings:
            return None
        top = max(
            self.findings,
            key=lambda f: _SENS_RANK[f.sensitivity],
        )
        return top.sensitivity.value

    def summary(self) -> Dict[str, object]:
        """
        Return a value-free summary safe for logs and API
        responses (counts and offsets only, never raw values).

        :requirement: URS-51.4 - Screen PII/PHI without persisting
                      raw matched values to any log or artifact.
        """
        return {
            "decision": self.decision.value,
            "mode": self.mode.value,
            "has_pii": self.has_pii,
            "finding_count": len(self.findings),
            "category_counts": self.category_counts,
            "max_sensitivity": self.max_sensitivity,
            "original_length": self.original_length,
        }


# -----------------------------------------------------------------
# Detector patterns
# -----------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)
_SSN_RE = re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b")
_IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
)
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[\s.\-]?)?\(?\d{3}\)?[\s.\-]?"
    r"\d{3}[\s.\-]?\d{4}(?!\d)"
)
_CARD_CANDIDATE_RE = re.compile(r"\b\d(?:[ \-]?\d){12,18}\b")

_DOB_RE = re.compile(
    r"(?i)\b(?:d\.?o\.?b\.?|date\s+of\s+birth)\b\s*[:#\-]?\s*"
    r"(\d{1,4}[\/\-.]\d{1,2}[\/\-.]\d{1,4}"
    r"|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})"
)
_MRN_RE = re.compile(
    r"(?i)\b(?:mrn|medical\s+record\s+(?:number|no\.?)"
    r"|patient\s+id|subject\s+id)\b\s*[:#\-]?\s*"
    r"([A-Za-z0-9\-]{4,})"
)
_PATIENT_NAME_RE = re.compile(
    r"(?i)\b(?:patient|subject)\s+name\b\s*[:#\-]?\s*"
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"
)


def _luhn_ok(digits: str) -> bool:
    """Return True when *digits* passes the Luhn checksum."""
    total = 0
    parity = len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


_RawSpan = Tuple[PIICategory, int, int, str]


def _detect_pattern(
    text: str,
    category: PIICategory,
    pattern: "re.Pattern[str]",
    detector: str,
    group: int = 0,
) -> List[_RawSpan]:
    """Collect raw spans for a single regex detector."""
    out: List[_RawSpan] = []
    for m in pattern.finditer(text):
        start = m.start(group)
        end = m.end(group)
        if start < 0 or end <= start:
            continue
        out.append((category, start, end, detector))
    return out


def _detect_cards(text: str) -> List[_RawSpan]:
    """Detect Luhn-valid 13-19 digit card numbers."""
    out: List[_RawSpan] = []
    for m in _CARD_CANDIDATE_RE.finditer(text):
        digits = re.sub(r"[ \-]", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            out.append(
                (PIICategory.CREDIT_CARD, m.start(), m.end(),
                 "luhn")
            )
    return out


def _span_overlap(a: _RawSpan, b: _RawSpan) -> bool:
    """True when two raw spans overlap in the source text."""
    return a[1] < b[2] and b[1] < a[2]


def _resolve_overlaps(raw: List[_RawSpan]) -> List[_RawSpan]:
    """
    Remove overlapping spans, preferring higher sensitivity then
    longer coverage. Returns spans sorted by start offset.
    """
    def _priority(item: _RawSpan) -> Tuple[int, int]:
        cat, start, end, _ = item
        return (
            _SENS_RANK[_CATEGORY_SENSITIVITY[cat]],
            end - start,
        )

    ordered = sorted(raw, key=_priority, reverse=True)
    kept: List[_RawSpan] = []
    for item in ordered:
        if any(_span_overlap(item, k) for k in kept):
            continue
        kept.append(item)
    kept.sort(key=lambda it: it[1])
    return kept


# -----------------------------------------------------------------
# Public detection / screening API
# -----------------------------------------------------------------

def detect(text: str) -> List[PIIFinding]:
    """
    Return every PII/PHI entity detected in *text*.

    Deterministic: the same input always yields the same findings
    in the same order (offsets ascending).

    :param text: Free text to scan.
    :return: List of ``PIIFinding`` (empty when clean).
    :requirement: URS-51.1 - Detect PII/PHI entities in free-text
                  inputs before external transmission.
    """
    if not text:
        return []

    raw: List[_RawSpan] = []
    raw += _detect_pattern(text, PIICategory.EMAIL, _EMAIL_RE, "regex")
    raw += _detect_pattern(text, PIICategory.US_SSN, _SSN_RE, "regex")
    raw += _detect_pattern(
        text, PIICategory.IP_ADDRESS, _IP_RE, "regex"
    )
    raw += _detect_pattern(text, PIICategory.PHONE, _PHONE_RE, "regex")
    raw += _detect_cards(text)
    raw += _detect_pattern(
        text, PIICategory.DATE_OF_BIRTH, _DOB_RE, "labeled", group=1
    )
    raw += _detect_pattern(
        text, PIICategory.MRN, _MRN_RE, "labeled", group=1
    )
    raw += _detect_pattern(
        text, PIICategory.PATIENT_NAME, _PATIENT_NAME_RE,
        "labeled", group=1,
    )

    resolved = _resolve_overlaps(raw)
    return [
        PIIFinding(
            category=cat,
            sensitivity=_CATEGORY_SENSITIVITY[cat],
            start=start,
            end=end,
            detector=detector,
        )
        for (cat, start, end, detector) in resolved
    ]


def redact(text: str, findings: List[PIIFinding]) -> str:
    """
    Replace each finding span with a ``[REDACTED:<CATEGORY>]``
    token. Applied right-to-left so offsets stay valid.

    :param text: Original text.
    :param findings: Findings from ``detect()``.
    :return: Redacted text.
    :requirement: URS-51.2 - Redact detected entities
                  deterministically.
    """
    if not findings:
        return text
    out = text
    for f in sorted(findings, key=lambda x: x.start, reverse=True):
        token = f"[REDACTED:{f.category.value}]"
        out = out[: f.start] + token + out[f.end:]
    return out


def configured_mode() -> ScreenMode:
    """
    Return the enforcement mode from ``EVOLV_PII_MODE``.

    Defaults to ``warn`` (detect + audit, do not alter output) so
    the shield is safe to enable everywhere without changing
    behaviour until a deployment opts into ``redact`` / ``block``.

    :return: The active ``ScreenMode``.
    :requirement: URS-51.3 - Enforce a configurable screen mode
                  at the tenant boundary.
    """
    raw = os.environ.get("EVOLV_PII_MODE", "warn").strip().lower()
    try:
        return ScreenMode(raw)
    except ValueError:
        return ScreenMode.WARN


def screen_text(
    text: str,
    mode: Optional[ScreenMode] = None,
) -> PIIScreenResult:
    """
    Screen *text* and return a decision without side effects.

    Pure and audit-free - use ``screen_for_external_call()`` for
    the audited, enforcing boundary wrapper.

    :param text: Free text to screen.
    :param mode: Override the configured mode (default: env).
    :return: ``PIIScreenResult`` with decision and text_out.
    :requirement: URS-51.1 - Detect PII/PHI entities in free-text
                  inputs before external transmission.
    """
    mode = mode or configured_mode()
    original_length = len(text or "")

    if mode == ScreenMode.OFF:
        return PIIScreenResult(
            ScreenDecision.ALLOW_CLEAN, mode, [], text,
            original_length,
        )

    findings = detect(text)
    if not findings:
        return PIIScreenResult(
            ScreenDecision.ALLOW_CLEAN, mode, [], text,
            original_length,
        )

    if mode == ScreenMode.BLOCK:
        return PIIScreenResult(
            ScreenDecision.BLOCKED, mode, findings, text,
            original_length,
        )
    if mode == ScreenMode.REDACT:
        return PIIScreenResult(
            ScreenDecision.REDACTED, mode, findings,
            redact(text, findings), original_length,
        )
    return PIIScreenResult(
        ScreenDecision.ALLOW_FLAGGED, mode, findings, text,
        original_length,
    )


def screen_for_external_call(
    text: str,
    agent_name: str,
    context: str = "",
    user_id: str = "system",
    mode: Optional[ScreenMode] = None,
) -> str:
    """
    Screen text at the tenant boundary, audit any detection, and
    return the text that should actually be transmitted.

    * ``off``    - returns the text unchanged, no audit.
    * ``warn``   - returns the raw text; a FLAGGED audit event is
      written when PII is present (value-free).
    * ``redact`` - returns the redacted text; FLAGGED audit event.
    * ``block``  - raises ``PIIBlockedError`` when PII is present;
      a BLOCKED audit event is written first.

    Clean text is never logged (keeps the audit trail signal
    high). No raw PII is ever written to the audit trail.

    :param text: Text about to be sent to an external service.
    :param agent_name: Calling agent (for the audit row).
    :param context: Short label of the boundary crossed
                    (e.g. "search:embedding+pinecone").
    :param user_id: Acting user for the audit row.
    :param mode: Override the configured mode (default: env).
    :return: The text to transmit (raw or redacted).
    :raises PIIBlockedError: When mode is ``block`` and PII is
            present.
    :requirement: URS-51.5 - Integrate the shield into external-
                  facing agent calls.
    """
    result = screen_text(text, mode=mode)

    if result.mode == ScreenMode.OFF or not result.has_pii:
        return result.text_out

    _log_screen(agent_name, context, user_id, result)

    if result.decision == ScreenDecision.BLOCKED:
        raise PIIBlockedError(
            "PII/PHI detected in text bound for an external "
            f"service ({context}). Categories: "
            f"{sorted(result.category_counts)}. Transmission "
            "blocked by EVOLV_PII_MODE=block."
        )
    return result.text_out


def _log_screen(
    agent_name: str,
    context: str,
    user_id: str,
    result: PIIScreenResult,
) -> None:
    """Write a value-free PII-screen event to the audit trail."""
    # Late import avoids a module-load cycle.
    from Agents.integrity_manager import log_audit_event

    action = (
        "PII_SCREEN_BLOCKED"
        if result.decision == ScreenDecision.BLOCKED
        else "PII_SCREEN_FLAGGED"
    )
    log_audit_event(
        agent_name=agent_name,
        action=action,
        user_id=user_id,
        decision_logic=(
            f"PII/PHI screen at boundary '{context}': "
            f"{len(result.findings)} finding(s); "
            f"categories={result.category_counts}; "
            f"max_sensitivity={result.max_sensitivity}; "
            f"mode={result.mode.value}; "
            f"decision={result.decision.value}"
        ),
        thought_process={
            "inputs": {
                "context": context,
                "mode": result.mode.value,
                "text_length": result.original_length,
            },
            "steps": [
                f"Detected {cat}: {count}"
                for cat, count in sorted(
                    result.category_counts.items()
                )
            ],
            "outputs": result.summary(),
        },
    )
