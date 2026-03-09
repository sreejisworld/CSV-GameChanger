"""
Attribute-Based Access Control (ABAC) Policy Engine.

Implements Dynamic Access Control (DAC) in the Veeva style:
access decisions are made based on *attributes* of the user and
the resource — not simply on role membership.

Key "Wow" Rule:
    If ``user.training_status is False``, the ``Approve`` action
    is unconditionally revoked regardless of any other attribute
    or role.

:requirement: URS-26.1 - System shall enforce attribute-based
              access control for all protected actions.
:requirement: URS-26.2 - Training status must block Approve action
              regardless of user role.
:requirement: URS-26.3 - Lifecycle state must gate write actions
              on GxP resources.
:requirement: URS-26.4 - Site context must restrict cross-site
              access to GxP-critical resources.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from Agents.integrity_manager import log_audit_event


# -----------------------------------------------------------------
# Enums
# -----------------------------------------------------------------

class LifecycleState(str, Enum):
    """
    Document lifecycle state — controls mutability.

    :requirement: URS-26.3
    """

    DRAFT = "Draft"
    REVIEW = "Review"
    LOCKED = "Locked"      # 21 CFR Part 11 — no edits allowed


class SiteContext(str, Enum):
    """
    Regulated site type for resource classification.

    :requirement: URS-26.4
    """

    GMP = "GMP"
    GCP = "GCP"
    GLP = "GLP"
    ISO13485 = "ISO13485"


class GxPCriticality(str, Enum):
    """
    GxP impact level of a resource.

    :requirement: URS-26.1
    """

    DIRECT = "GxP Direct"
    INDIRECT = "GxP Indirect"
    NONE = "GxP None"


class PolicyVerdict(str, Enum):
    """Access-control decision."""

    PERMIT = "Permit"
    DENY = "Deny"


# -----------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------

@dataclass
class UserContext:
    """
    Attributes of the requesting user.

    :requirement: URS-26.1 - Attribute-based access control.
    :requirement: URS-26.2 - training_status gates Approve.
    """

    user_id: str
    role: str                     # e.g. "Admin", "Reviewer", "Author"
    department: str               # e.g. "QA", "IT", "Regulatory"
    site_id: str                  # e.g. "SITE-001", "US-PHAR-01"
    training_status: bool         # False → Approve always denied
    # Optional extra attributes for future extensibility
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "user_id":         self.user_id,
            "role":            self.role,
            "department":      self.department,
            "site_id":         self.site_id,
            "training_status": self.training_status,
            "attributes":      self.attributes,
        }


@dataclass
class ResourceContext:
    """
    Attributes of the target resource.

    :requirement: URS-26.1 - Attribute-based access control.
    :requirement: URS-26.3 - Lifecycle state gates writes.
    :requirement: URS-26.4 - Site context restricts cross-site.
    """

    resource_id: str
    resource_type: str              # e.g. "requirement", "test_case"
    gxp_criticality: GxPCriticality
    lifecycle_state: LifecycleState
    site_context: SiteContext
    owner_site_id: str              # Site that owns this resource
    # Optional extra attributes
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "resource_id":       self.resource_id,
            "resource_type":     self.resource_type,
            "gxp_criticality":   self.gxp_criticality.value,
            "lifecycle_state":   self.lifecycle_state.value,
            "site_context":      self.site_context.value,
            "owner_site_id":     self.owner_site_id,
            "attributes":        self.attributes,
        }


@dataclass
class PolicyDecision:
    """
    Result of a ``PolicyEngine.permit()`` call.

    :requirement: URS-26.1 - Access decisions are fully auditable.
    """

    verdict: PolicyVerdict
    action: str
    user_id: str
    resource_id: str
    # All rules evaluated, in order
    rules_evaluated: List[str] = field(default_factory=list)
    # First rule that produced a Deny (empty string if Permit)
    denied_by: str = ""
    rationale: str = ""
    evaluated_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    @property
    def is_permitted(self) -> bool:
        """Return True when the verdict is Permit."""
        return self.verdict == PolicyVerdict.PERMIT

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "verdict":          self.verdict.value,
            "action":           self.action,
            "user_id":          self.user_id,
            "resource_id":      self.resource_id,
            "rules_evaluated":  self.rules_evaluated,
            "denied_by":        self.denied_by,
            "rationale":        self.rationale,
            "evaluated_at":     self.evaluated_at,
        }


# -----------------------------------------------------------------
# Role → allowed actions whitelist
# -----------------------------------------------------------------

#: Maps role names (case-insensitive) to the set of actions the
#: role is permitted to *request* — the policy engine still applies
#: attribute overrides on top of this list.
_ROLE_ACTIONS: Dict[str, frozenset] = {
    "admin": frozenset({
        "read", "create", "edit", "delete",
        "approve", "reject", "lock", "unlock",
        "export", "audit_view",
    }),
    "reviewer": frozenset({
        "read", "approve", "reject", "comment", "export",
    }),
    "author": frozenset({
        "read", "create", "edit", "comment", "export",
    }),
    "viewer": frozenset({
        "read", "export",
    }),
    "qa_officer": frozenset({
        "read", "approve", "reject", "lock",
        "comment", "export", "audit_view",
    }),
    "system": frozenset({
        "read", "create", "edit", "delete",
        "approve", "lock", "export", "audit_view",
    }),
}

#: Default (minimal) permissions for unrecognised roles.
_DEFAULT_ROLE_ACTIONS: frozenset = frozenset({"read"})


def _role_actions(role: str) -> frozenset:
    return _ROLE_ACTIONS.get(role.lower(), _DEFAULT_ROLE_ACTIONS)


# -----------------------------------------------------------------
# PolicyEngine
# -----------------------------------------------------------------

class PolicyEngine:
    """
    Attribute-Based Access Control engine for EVOLV.

    Evaluates ``permit(user, action, resource)`` by running a
    prioritised chain of policy rules.  The first rule that
    produces a ``Deny`` short-circuits evaluation (deny-by-default
    unless all rules pass).

    Policy Rule Chain (evaluated in order):
        1. Training Status Gate  — URS-26.2 "Wow" Rule
        2. Role Capability Check — URS-26.1
        3. Lifecycle State Gate  — URS-26.3
        4. Cross-Site Restriction — URS-26.4
        5. GxP Criticality Gate  — URS-26.1

    Each decision is logged to the immutable audit trail.

    :requirement: URS-26.1 - Attribute-based access control.
    :requirement: URS-26.2 - Training status blocks Approve.
    :requirement: URS-26.3 - Lifecycle state gates writes.
    :requirement: URS-26.4 - Site context restricts cross-site.
    """

    # Actions that mutate a GxP document
    _WRITE_ACTIONS: frozenset = frozenset({
        "create", "edit", "delete", "approve",
        "reject", "lock", "unlock",
    })

    # Actions that change lifecycle state irreversibly
    _LOCK_ACTIONS: frozenset = frozenset({"edit", "delete"})

    def permit(
        self,
        user: UserContext,
        action: str,
        resource: ResourceContext,
        audit: bool = True,
    ) -> PolicyDecision:
        """
        Evaluate whether *user* may perform *action* on *resource*.

        Runs the rule chain and returns a ``PolicyDecision``.  When
        *audit* is ``True`` (default), the decision is written to
        the immutable audit trail.

        :param user: Attributes of the requesting user.
        :param action: Action name (e.g. "approve", "edit").
        :param resource: Attributes of the target resource.
        :param audit: Write decision to audit trail (default True).
        :return: PolicyDecision with verdict and rationale.
        :requirement: URS-26.1 - Attribute-based access control.
        """
        action_lower = action.lower()
        rules_evaluated: List[str] = []

        verdict, denied_by, rationale = self._run_rules(
            user=user,
            action=action_lower,
            resource=resource,
            rules_evaluated=rules_evaluated,
        )

        decision = PolicyDecision(
            verdict=verdict,
            action=action,
            user_id=user.user_id,
            resource_id=resource.resource_id,
            rules_evaluated=rules_evaluated,
            denied_by=denied_by,
            rationale=rationale,
        )

        if audit:
            self._log_decision(user, action, resource, decision)

        return decision

    # ----------------------------------------------------------
    # Rule chain
    # ----------------------------------------------------------

    def _run_rules(
        self,
        user: UserContext,
        action: str,
        resource: ResourceContext,
        rules_evaluated: List[str],
    ) -> Tuple[PolicyVerdict, str, str]:
        """
        Evaluate each rule in priority order.

        :return: (verdict, denied_by_rule, rationale)
        :requirement: URS-26.1 through URS-26.4
        """
        rules = [
            self._rule_training_status,
            self._rule_role_capability,
            self._rule_lifecycle_state,
            self._rule_cross_site,
            self._rule_gxp_criticality,
        ]

        for rule_fn in rules:
            rule_name = rule_fn.__name__.replace("_rule_", "")
            rules_evaluated.append(rule_name)
            deny_reason = rule_fn(user, action, resource)
            if deny_reason:
                return (
                    PolicyVerdict.DENY,
                    rule_name,
                    deny_reason,
                )

        rationale = (
            f"All {len(rules_evaluated)} policy rules passed. "
            f"User '{user.user_id}' ({user.role}) "
            f"is permitted to '{action}' "
            f"resource '{resource.resource_id}'."
        )
        return PolicyVerdict.PERMIT, "", rationale

    # ----------------------------------------------------------
    # Rule 1 — Training Status Gate (URS-26.2 "Wow" Rule)
    # ----------------------------------------------------------

    @staticmethod
    def _rule_training_status(
        user: UserContext,
        action: str,
        resource: ResourceContext,
    ) -> str:
        """
        Unconditionally deny Approve when training is incomplete.

        This is the "Wow" Rule: training_status == False revokes
        the Approve action regardless of role or any other
        attribute.

        :requirement: URS-26.2
        """
        if action == "approve" and not user.training_status:
            return (
                "TRAINING_INCOMPLETE: User "
                f"'{user.user_id}' has not completed required "
                "training. The 'Approve' action is dynamically "
                "revoked until training status is confirmed. "
                "(21 CFR Part 11 §11.10(i) — personnel training "
                "records must be current.)"
            )
        return ""

    # ----------------------------------------------------------
    # Rule 2 — Role Capability Check (URS-26.1)
    # ----------------------------------------------------------

    @staticmethod
    def _rule_role_capability(
        user: UserContext,
        action: str,
        resource: ResourceContext,
    ) -> str:
        """
        Check the user's role has the requested action in its
        permitted set.

        :requirement: URS-26.1
        """
        allowed = _role_actions(user.role)
        if action not in allowed:
            return (
                f"ROLE_DENIED: Role '{user.role}' is not "
                f"authorised to perform '{action}'. "
                f"Permitted actions: {sorted(allowed)}."
            )
        return ""

    # ----------------------------------------------------------
    # Rule 3 — Lifecycle State Gate (URS-26.3)
    # ----------------------------------------------------------

    @staticmethod
    def _rule_lifecycle_state(
        user: UserContext,
        action: str,
        resource: ResourceContext,
    ) -> str:
        """
        Block mutating actions on Locked documents.

        Once a GxP document is Locked (electronically signed),
        no edits or deletions are permitted to preserve the
        21 CFR Part 11 compliant record.

        :requirement: URS-26.3
        """
        if (
            resource.lifecycle_state == LifecycleState.LOCKED
            and action in PolicyEngine._LOCK_ACTIONS
        ):
            return (
                f"LOCKED_DOCUMENT: Resource "
                f"'{resource.resource_id}' is in "
                f"'{LifecycleState.LOCKED.value}' state. "
                f"Action '{action}' is prohibited. "
                "(21 CFR Part 11 §11.10(e) — audit trail must "
                "not be modifiable.)"
            )
        if (
            resource.lifecycle_state == LifecycleState.REVIEW
            and action in ("delete",)
        ):
            return (
                f"REVIEW_LOCK: Resource "
                f"'{resource.resource_id}' is under review. "
                "Deletion is not permitted until review is "
                "complete."
            )
        return ""

    # ----------------------------------------------------------
    # Rule 4 — Cross-Site Restriction (URS-26.4)
    # ----------------------------------------------------------

    @staticmethod
    def _rule_cross_site(
        user: UserContext,
        action: str,
        resource: ResourceContext,
    ) -> str:
        """
        Restrict write access to resources owned by a different
        site unless the user is in the QA or System role.

        :requirement: URS-26.4
        """
        cross_site = (
            user.site_id != resource.owner_site_id
        )
        write_action = action in PolicyEngine._WRITE_ACTIONS
        privileged_role = user.role.lower() in (
            "admin", "qa_officer", "system"
        )

        if cross_site and write_action and not privileged_role:
            return (
                f"CROSS_SITE_DENIED: User site "
                f"'{user.site_id}' does not match resource "
                f"owner site '{resource.owner_site_id}'. "
                f"Action '{action}' on cross-site GxP resources "
                "requires QA Officer or Admin privileges."
            )
        return ""

    # ----------------------------------------------------------
    # Rule 5 — GxP Criticality Gate (URS-26.1)
    # ----------------------------------------------------------

    @staticmethod
    def _rule_gxp_criticality(
        user: UserContext,
        action: str,
        resource: ResourceContext,
    ) -> str:
        """
        Require elevated role for write actions on GxP Direct
        resources.

        GxP Direct resources (batch records, validated systems)
        may only be modified by Author or above roles.

        :requirement: URS-26.1
        """
        if (
            resource.gxp_criticality == GxPCriticality.DIRECT
            and action in PolicyEngine._WRITE_ACTIONS
            and user.role.lower() == "viewer"
        ):
            return (
                f"GXP_DIRECT_RESTRICTED: Resource "
                f"'{resource.resource_id}' is classified as "
                f"'{GxPCriticality.DIRECT.value}'. "
                f"Action '{action}' requires at least Author "
                "role. Viewer role is insufficient for GxP "
                "Direct resources."
            )
        return ""

    # ----------------------------------------------------------
    # Audit logging
    # ----------------------------------------------------------

    @staticmethod
    def _log_decision(
        user: UserContext,
        action: str,
        resource: ResourceContext,
        decision: PolicyDecision,
    ) -> None:
        """
        Write the access-control decision to the audit trail.

        :requirement: URS-26.1 - Audit trail for access decisions.
        """
        log_audit_event(
            agent_name="PolicyEngine",
            action=(
                "ACCESS_PERMITTED"
                if decision.is_permitted
                else "ACCESS_DENIED"
            ),
            user_id=user.user_id,
            decision_logic=(
                f"Action={action} | "
                f"Resource={resource.resource_id} "
                f"({resource.resource_type}) | "
                f"Verdict={decision.verdict.value} | "
                f"Rule={decision.denied_by or 'all_passed'}"
            ),
            compliance_impact=(
                "Access Control — Security"
                if decision.is_permitted
                else "Access Control — Denial"
            ),
            thought_process={
                "inputs": {
                    "user": user.to_dict(),
                    "action": action,
                    "resource": resource.to_dict(),
                },
                "steps": [
                    f"Evaluated rule: {r}"
                    for r in decision.rules_evaluated
                ],
                "outputs": decision.to_dict(),
            },
        )

    # ----------------------------------------------------------
    # Convenience — batch permit check
    # ----------------------------------------------------------

    def permit_batch(
        self,
        user: UserContext,
        actions: List[str],
        resource: ResourceContext,
    ) -> Dict[str, PolicyDecision]:
        """
        Evaluate multiple actions for the same user/resource pair.

        :param user: User attributes.
        :param actions: List of action names to evaluate.
        :param resource: Resource attributes.
        :return: Dict mapping action → PolicyDecision.
        :requirement: URS-26.1
        """
        return {
            action: self.permit(user, action, resource)
            for action in actions
        }

    def allowed_actions(
        self,
        user: UserContext,
        resource: ResourceContext,
        candidate_actions: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Return the subset of *candidate_actions* permitted for
        *user* on *resource*.

        When *candidate_actions* is None, all known actions from
        the role whitelist are tested.

        :param user: User attributes.
        :param resource: Resource attributes.
        :param candidate_actions: Actions to test (default: all).
        :return: List of permitted action names.
        :requirement: URS-26.1
        """
        if candidate_actions is None:
            candidate_actions = list(
                _role_actions(user.role)
            )
        return [
            action
            for action in candidate_actions
            if self.permit(
                user, action, resource, audit=False
            ).is_permitted
        ]
