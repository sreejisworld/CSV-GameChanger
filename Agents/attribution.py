"""
attribution.py - Enforce unique-user attribution on human-decision
audit events.

Sprint 52 ("Fool-proof by design", part 1). Closes the FDA 21 CFR
211.68(b) "shared login / no attribution" finding at the source: a
GMP-relevant *human decision* (an electronic signature, an approval,
an attestation) must be recorded against a real, unique person -
never a generic or shared identity like "SYSTEM", "admin", or a
role name.

The problem this prevents
-------------------------
EVOLV's API captures the actor as
``user_id = request.headers.get("X-User-ID", "SYSTEM")``. A missing
header silently degrades to the generic "SYSTEM" identity. For
automated agent plumbing that is correct; for a human sign-off it is
exactly the un-attributable record FDA cites in warning letters. This
module is the deterministic guard that tells the two apart and refuses
(or flags) the un-attributable case.

Design (mirrors ``pii_shield`` so it is safe to enable everywhere)
------------------------------------------------------------------
* Only **attributable actions** (sign-offs / approvals / attestations)
  are guarded - never ``*_RECEIVED`` / ``*_FAILED`` plumbing events, so
  the guard can never recurse through an error path.
* Mode is set by ``EVOLV_ATTRIBUTION_MODE`` = off | warn | enforce
  (default **warn** - behaviour-neutral: it logs, it does not block).
* ``enforce`` raises ``AttributionError`` *before* the row is written,
  so an un-attributable signature can never enter the audit trail.

:requirement: URS-52.1 - Enforce unique-user attribution on
              human-decision audit events.
:requirement: URS-52.2 - Deterministic shared/generic identity
              denylist.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Tuple


logger = logging.getLogger("evolv.attribution")


class AttributionError(Exception):
    """
    Error code: CSV-055 - A human-decision audit event was recorded
    against a shared / generic / missing identity.
    """

    error_code = "CSV-055"


# -----------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------

_MODE_ENV = "EVOLV_ATTRIBUTION_MODE"
_VALID_MODES = ("off", "warn", "enforce")


def configured_mode() -> str:
    """
    Return the active attribution mode from the environment.

    :return: One of "off", "warn", "enforce" (default "warn").
    :requirement: URS-52.4 - Configurable attribution mode.
    """
    mode = os.getenv(_MODE_ENV, "warn").strip().lower()
    return mode if mode in _VALID_MODES else "warn"


# -----------------------------------------------------------------
# Shared / generic identity denylist
# -----------------------------------------------------------------

#: Non-unique identifiers that cannot attribute an action to a real
#: person. Compared case-insensitively after trimming. A legitimate
#: identity is a specific human (a username or email), never a role,
#: a group, or the automation sentinel.
_SHARED_IDS = frozenset({
    "", "system", "admin", "administrator", "user", "users",
    "shared", "share", "test", "tester", "guest", "anonymous",
    "anon", "none", "null", "n/a", "na", "unknown", "default",
    "root", "operator", "qa", "reviewer", "approver", "signer",
})


def is_shared_identity(user_id: str) -> bool:
    """
    Return True when *user_id* is missing, generic, or a shared/role
    identity that cannot attribute an action to a specific person.

    :param user_id: The acting identity recorded on the event.
    :return: True if the identity is not a unique person.
    :requirement: URS-52.2 - Deterministic shared/generic identity
                  denylist.
    """
    return (user_id or "").strip().lower() in _SHARED_IDS


# -----------------------------------------------------------------
# Attributable-action classification
# -----------------------------------------------------------------

#: Suffixes that mark a committed human decision.
_ATTRIBUTABLE_SUFFIXES = ("_SIGNED", "_APPROVED", "_ATTESTED")

#: Explicit human-decision actions that do not match a suffix.
_ATTRIBUTABLE_ACTIONS = frozenset({
    "CCR_APPROVED", "CCR_SIGNED", "QA_REVIEW_SIGNED",
    "MANIFESTATION_SIGNED", "URS_APPROVED", "RELEASE_APPROVED",
    "ELECTRONIC_SIGNATURE",
})

#: Plumbing suffixes that are never a human decision - guarded first
#: so an error/receipt path can never trip (or recurse through) the
#: guard.
_NON_ATTRIBUTABLE_SUFFIXES = (
    "_FAILED", "_RECEIVED", "_STARTED", "_REQUESTED",
)


def is_attributable_action(action: str) -> bool:
    """
    Return True when *action* represents a human decision that must be
    attributable to a specific person (a signature / approval /
    attestation), as opposed to system or plumbing events.

    :param action: The audit action constant (e.g. "CCR_APPROVED").
    :return: True if the action requires unique-user attribution.
    :requirement: URS-52.3 - Classify human-decision (attributable)
                  actions versus system actions.
    """
    a = (action or "").strip().upper()
    if a.endswith(_NON_ATTRIBUTABLE_SUFFIXES):
        return False
    if a in _ATTRIBUTABLE_ACTIONS:
        return True
    return a.endswith(_ATTRIBUTABLE_SUFFIXES)


# -----------------------------------------------------------------
# Screening + guard
# -----------------------------------------------------------------

@dataclass
class AttributionResult:
    """Outcome of screening one (user_id, action) pair."""

    user_id: str
    action: str
    attributable: bool
    shared_identity: bool
    mode: str
    violation: bool
    message: str


def screen_attribution(user_id: str, action: str) -> AttributionResult:
    """
    Classify a (user_id, action) pair without side effects.

    A *violation* is an attributable action recorded against a shared
    identity while the mode is not "off".

    :param user_id: The acting identity.
    :param action: The audit action constant.
    :return: A populated :class:`AttributionResult`.
    :requirement: URS-52.1 - Enforce unique-user attribution on
                  human-decision audit events.
    """
    mode = configured_mode()
    attributable = is_attributable_action(action)
    shared = is_shared_identity(user_id)
    violation = attributable and shared and mode != "off"
    if violation:
        message = (
            f"Human-decision action '{action}' recorded against "
            f"shared/generic identity '{user_id or '(empty)'}' - "
            "a unique person is required (21 CFR 211.68(b))."
        )
    else:
        message = ""
    return AttributionResult(
        user_id=user_id,
        action=action,
        attributable=attributable,
        shared_identity=shared,
        mode=mode,
        violation=violation,
        message=message,
    )


def guard_attribution(user_id: str, action: str) -> AttributionResult:
    """
    Screen a (user_id, action) pair and act on the mode.

    - ``enforce`` → raise :class:`AttributionError` on a violation,
      before any audit row is written.
    - ``warn``    → log the violation and return (row still written).
    - ``off``     → never a violation.

    Called from :func:`Agents.integrity_manager.log_audit_event` so
    every write path across the platform is covered in one place.

    :param user_id: The acting identity.
    :param action: The audit action constant.
    :return: The :class:`AttributionResult` (when not raising).
    :raises AttributionError: In enforce mode on a violation.
    :requirement: URS-52.4 - Configurable attribution mode integrated
                  into the audit write path.
    """
    result = screen_attribution(user_id, action)
    if not result.violation:
        return result
    if result.mode == "enforce":
        raise AttributionError(f"[CSV-055] {result.message}")
    logger.warning("[CSV-055] %s", result.message)
    return result


def classify(user_id: str, action: str) -> Tuple[bool, bool]:
    """
    Convenience: return ``(attributable, shared_identity)``.

    :param user_id: The acting identity.
    :param action: The audit action constant.
    :return: Tuple of (is attributable, is shared identity).
    :requirement: URS-52.3 - Classify human-decision actions.
    """
    return is_attributable_action(action), is_shared_identity(user_id)
