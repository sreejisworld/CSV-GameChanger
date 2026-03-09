"""
Enterprise Audit Logging Decorator.

Provides the ``@audit_log`` decorator for 21 CFR Part 11 compliant
function-level audit trails.  Every decorated call captures:
    • Timestamp       — UTC ISO-8601
    • User_ID         — extracted from kwargs or ``user_id`` param
    • Action          — derived from the function name or overridden
    • Old_Value       — first positional arg or ``old_value`` kwarg
    • New_Value       — second positional arg or ``new_value`` kwarg
    • AI_Rationale    — ``ai_rationale`` kwarg or return-value
                        inspection
    • Outcome         — SUCCESS / FAILURE + exception details

All records are appended to the immutable
``output/audit_trail.csv`` via the IntegrityManager, ensuring no
entry can ever be overwritten.

Usage::

    from utils.audit_decorator import audit_log

    @audit_log(action="REQUIREMENT_APPROVED")
    def approve_requirement(
        req_id: str,
        new_value: str,
        *,
        user_id: str = "SYSTEM",
        ai_rationale: str = "",
    ) -> dict:
        ...

    @audit_log  # action defaults to the function name
    def edit_test_case(old_value: dict, new_value: dict, **kw):
        ...

:requirement: URS-27.1 - System shall provide a decorator that
              captures Timestamp, User_ID, Action, Old_Value,
              New_Value, and AI_Rationale for every decorated call.
:requirement: URS-27.2 - The decorator log must be immutable and
              append-only (21 CFR Part 11 §11.10(e)).
:requirement: URS-27.3 - Decorator must log failures without
              suppressing the original exception.
"""
from __future__ import annotations

import functools
import traceback
from typing import Any, Callable, Optional, TypeVar, Union, overload

from Agents.integrity_manager import log_audit_event

F = TypeVar("F", bound=Callable[..., Any])


# -----------------------------------------------------------------
# Internal helpers
# -----------------------------------------------------------------

def _extract(
    args: tuple,
    kwargs: dict,
    param_name: str,
    positional_index: int,
    default: Any = None,
) -> Any:
    """
    Extract a value from kwargs by name or from args by index.

    :param args: Positional arguments tuple.
    :param kwargs: Keyword arguments dict.
    :param param_name: Preferred keyword name.
    :param positional_index: Fallback positional index.
    :param default: Value when neither source has the key.
    :return: Extracted value or *default*.
    """
    if param_name in kwargs:
        return kwargs[param_name]
    if positional_index < len(args):
        return args[positional_index]
    return default


def _safe_repr(value: Any, max_len: int = 400) -> str:
    """
    Return a safe string representation of *value*.

    Truncates at *max_len* characters to keep audit rows readable.

    :param value: Any Python object.
    :param max_len: Maximum character length.
    :return: Truncated string representation.
    """
    try:
        text = repr(value)
    except Exception:
        text = "<unrepresentable>"
    if len(text) > max_len:
        text = text[:max_len] + "…"
    return text


def _build_decision_logic(
    action: str,
    user_id: str,
    old_value: Any,
    new_value: Any,
    ai_rationale: str,
    outcome: str,
    error_detail: str = "",
) -> str:
    """
    Assemble a human-readable decision_logic string for the CSV row.

    :return: Formatted multi-field string.
    :requirement: URS-27.1
    """
    parts = [
        f"Action={action}",
        f"User={user_id}",
        f"Old={_safe_repr(old_value, 120)}",
        f"New={_safe_repr(new_value, 120)}",
        f"Outcome={outcome}",
    ]
    if ai_rationale:
        parts.append(f"AI_Rationale={ai_rationale[:200]}")
    if error_detail:
        parts.append(f"Error={error_detail[:200]}")
    return " | ".join(parts)


# -----------------------------------------------------------------
# @audit_log decorator
# -----------------------------------------------------------------

@overload
def audit_log(func: F) -> F: ...


@overload
def audit_log(
    *,
    action: Optional[str] = None,
    agent_name: str = "AuditDecorator",
    user_id_param: str = "user_id",
    old_value_param: str = "old_value",
    new_value_param: str = "new_value",
    ai_rationale_param: str = "ai_rationale",
    compliance_impact: Optional[str] = None,
) -> Callable[[F], F]: ...


def audit_log(
    func: Optional[F] = None,
    *,
    action: Optional[str] = None,
    agent_name: str = "AuditDecorator",
    user_id_param: str = "user_id",
    old_value_param: str = "old_value",
    new_value_param: str = "new_value",
    ai_rationale_param: str = "ai_rationale",
    compliance_impact: Optional[str] = None,
) -> Union[F, Callable[[F], F]]:
    """
    Decorator that captures a 21 CFR Part 11 compliant audit record
    for every call to the decorated function.

    Can be used bare or with keyword arguments::

        @audit_log
        def my_func(old_value, new_value, *, user_id="SYSTEM"): ...

        @audit_log(action="REQUIREMENT_LOCKED", agent_name="LockAgent")
        def lock_req(old_value, new_value, *, user_id="SYSTEM"): ...

    Fields captured per call:
        - **Timestamp** — UTC ISO-8601 (auto-set by IntegrityManager)
        - **User_ID** — value of the *user_id* kwarg (or "SYSTEM")
        - **Action** — ``action`` parameter or function name (upper)
        - **Old_Value** — first positional arg or ``old_value`` kwarg
        - **New_Value** — second positional arg or ``new_value`` kwarg
        - **AI_Rationale** — ``ai_rationale`` kwarg (optional)
        - **Outcome** — SUCCESS or FAILURE + exception class

    On failure the original exception is **re-raised** after logging
    so callers are not silently swallowed.

    :param func: The decorated function (bare usage).
    :param action: Override the audit action name.
    :param agent_name: Agent name written to audit trail.
    :param user_id_param: Name of the user_id keyword argument.
    :param old_value_param: Name of the old_value keyword argument.
    :param new_value_param: Name of the new_value keyword argument.
    :param ai_rationale_param: Name of the ai_rationale kwarg.
    :param compliance_impact: Override compliance classification.
    :return: Decorated function or decorator factory.
    :requirement: URS-27.1 - Capture all six audit fields.
    :requirement: URS-27.2 - Immutable append-only log.
    :requirement: URS-27.3 - Log failures without suppression.
    """
    def _decorator(fn: F) -> F:
        _action = (action or fn.__name__).upper()

        @functools.wraps(fn)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            # --- extract call-site values ---
            user_id: str = str(
                kwargs.get(user_id_param, "SYSTEM")
            )
            old_value: Any = _extract(
                args, kwargs, old_value_param, 0
            )
            new_value: Any = _extract(
                args, kwargs, new_value_param, 1
            )
            ai_rationale: str = str(
                kwargs.get(ai_rationale_param, "")
            )

            try:
                result = fn(*args, **kwargs)

                # Use return value as new_value when not supplied
                effective_new = (
                    result
                    if new_value is None
                    else new_value
                )
                # Extract ai_rationale from result dict if present
                if (
                    not ai_rationale
                    and isinstance(result, dict)
                ):
                    ai_rationale = str(
                        result.get("ai_rationale", "")
                        or result.get("rationale", "")
                    )

                log_audit_event(
                    agent_name=agent_name,
                    action=_action,
                    user_id=user_id,
                    decision_logic=_build_decision_logic(
                        action=_action,
                        user_id=user_id,
                        old_value=old_value,
                        new_value=effective_new,
                        ai_rationale=ai_rationale,
                        outcome="SUCCESS",
                    ),
                    compliance_impact=compliance_impact,
                    thought_process={
                        "inputs": {
                            "old_value": _safe_repr(
                                old_value
                            ),
                            "new_value": _safe_repr(
                                new_value
                            ),
                            "user_id": user_id,
                            "ai_rationale": ai_rationale,
                        },
                        "steps": [
                            f"Called {fn.__qualname__}",
                            "Captured old_value and new_value",
                            "Function executed successfully",
                        ],
                        "outputs": {
                            "result": _safe_repr(result),
                            "outcome": "SUCCESS",
                        },
                    },
                )

                return result

            except Exception as exc:
                error_detail = (
                    f"{type(exc).__name__}: {exc}"
                )
                tb_lines = traceback.format_exc().splitlines()
                # Last 3 lines of traceback for brevity
                tb_summary = " | ".join(tb_lines[-3:])

                log_audit_event(
                    agent_name=agent_name,
                    action=_action + "_FAILED",
                    user_id=user_id,
                    decision_logic=_build_decision_logic(
                        action=_action,
                        user_id=user_id,
                        old_value=old_value,
                        new_value=new_value,
                        ai_rationale=ai_rationale,
                        outcome="FAILURE",
                        error_detail=error_detail,
                    ),
                    compliance_impact=(
                        compliance_impact
                        or "Operational — Error"
                    ),
                    thought_process={
                        "inputs": {
                            "old_value": _safe_repr(
                                old_value
                            ),
                            "new_value": _safe_repr(
                                new_value
                            ),
                            "user_id": user_id,
                            "ai_rationale": ai_rationale,
                        },
                        "steps": [
                            f"Called {fn.__qualname__}",
                            "Exception raised during execution",
                            f"Exception: {error_detail}",
                        ],
                        "outputs": {
                            "outcome": "FAILURE",
                            "error": error_detail,
                            "traceback_summary": tb_summary,
                        },
                    },
                )

                # Re-raise — never suppress exceptions silently
                raise

        return _wrapper  # type: ignore[return-value]

    # Support both @audit_log and @audit_log(...)
    if func is not None:
        return _decorator(func)
    return _decorator
