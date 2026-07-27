"""
resilience.py - Retry + circuit-breaker for external dependencies.

Sprint 51 ("AI Input Safety Layer", part 2). A dependency-free
resilience layer wrapping EVOLV's only two outbound dependencies -
OpenAI (embeddings) and Pinecone (vector search). Hand-rolled on
purpose: in a validated system every third-party package is one
more thing to CVE-scan and re-validate, so we keep the
deterministic core lean (matches [[project-amgen-scorecard-sprint51]]).

What it provides
----------------
* ``retry_call`` - bounded exponential backoff with jitter, only
  for *transient* failures (timeouts, 429/5xx, connection resets).
  Non-transient errors (401/403/400) are never retried.
* ``CircuitBreaker`` - per-dependency breaker: trips OPEN after N
  consecutive failures, blocks calls for a recovery window, then
  allows a single HALF_OPEN trial before closing again.
* ``resilient_call`` - the combination used at each call site.
* ``health_snapshot`` - value the breaker states feed a health/
  alerting surface ("is the OpenAI breaker open?").

Maps to the big-pharma agentic-AI standard rows "Retry
mechanisms, caching, health monitoring" and "Resilient infra
design, circuit breakers".

:requirement: URS-51.6 - Retry transient external-call failures
              with bounded exponential backoff.
:requirement: URS-51.7 - Circuit-break a failing external
              dependency to fail fast and allow recovery.
"""
from __future__ import annotations

import os
import random
import threading
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


# -----------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------

class ResilienceError(Exception):
    """Base error for the resilience layer. Error code: CSV-053."""

    error_code = "CSV-053"


class CircuitOpenError(ResilienceError):
    """
    Raised when a call is attempted through an OPEN circuit
    breaker. Error code: CSV-054.
    """

    error_code = "CSV-054"


# -----------------------------------------------------------------
# Config helpers
# -----------------------------------------------------------------

def _env_int(name: str, default: int) -> int:
    """Read a non-negative int from the environment."""
    try:
        return max(0, int(os.environ.get(name, "").strip()))
    except (ValueError, AttributeError):
        return default


def _env_float(name: str, default: float) -> float:
    """Read a non-negative float from the environment."""
    try:
        return max(0.0, float(os.environ.get(name, "").strip()))
    except (ValueError, AttributeError):
        return default


# -----------------------------------------------------------------
# Transient-failure classification
# -----------------------------------------------------------------

_TRANSIENT_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}
_NONRETRYABLE_STATUS = {400, 401, 403, 404, 422}
_TRANSIENT_HINTS = (
    "timeout", "timed out", "temporarily", "temporary",
    "rate limit", "ratelimit", "too many requests",
    "connection", "connection reset", "econnreset",
    "unavailable", "overloaded", "try again", "reset by peer",
)
_TRANSIENT_TYPE_HINTS = (
    "timeout", "connection", "temporar", "unavailable",
    "ratelimit", "apiconnection", "serviceunavailable",
)


def _status_of(exc: BaseException) -> Optional[int]:
    """Best-effort extraction of an HTTP status code from *exc*."""
    for attr in ("status_code", "status", "http_status", "code"):
        val = getattr(exc, attr, None)
        if isinstance(val, int):
            return val
    resp = getattr(exc, "response", None)
    if resp is not None:
        val = getattr(resp, "status_code", None)
        if isinstance(val, int):
            return val
    return None


def default_retryable(exc: BaseException) -> bool:
    """
    Return True when *exc* looks transient and worth retrying.

    Precedence: explicit non-retryable status wins; then transient
    status; then exception-type name; then message keywords.

    :param exc: The exception raised by the wrapped call.
    :return: True if the call should be retried.
    :requirement: URS-51.6 - Retry only transient failures.
    """
    status = _status_of(exc)
    if status in _NONRETRYABLE_STATUS:
        return False
    if status in _TRANSIENT_STATUS:
        return True
    type_name = type(exc).__name__.lower()
    if any(h in type_name for h in _TRANSIENT_TYPE_HINTS):
        return True
    message = str(exc).lower()
    return any(h in message for h in _TRANSIENT_HINTS)


# -----------------------------------------------------------------
# Retry with bounded exponential backoff
# -----------------------------------------------------------------

def retry_call(
    fn: Callable[[], Any],
    *,
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: float = 8.0,
    retryable: Optional[Callable[[BaseException], bool]] = None,
    sleep: Callable[[float], None] = time.sleep,
    jitter: bool = True,
    provider: str = "",
) -> Any:
    """
    Call *fn* with bounded exponential-backoff retries.

    Retries only when *retryable* returns True. Re-raises the last
    exception when attempts are exhausted or the error is not
    transient. On exhaustion of a transient error a
    ``DEPENDENCY_RETRY_EXHAUSTED`` audit event is written.

    :param fn: Zero-arg callable performing the external call.
    :param max_attempts: Total attempts (default env / 3).
    :param base_delay: First backoff in seconds (default env / 0.5).
    :param max_delay: Upper bound on any single backoff.
    :param retryable: Predicate deciding if an error is transient.
    :param sleep: Sleep function (injectable for tests).
    :param jitter: Add up to ``base_delay`` random jitter.
    :param provider: Label for audit/logging (e.g. "openai").
    :return: The return value of *fn*.
    :requirement: URS-51.6 - Retry transient external-call
                  failures with bounded exponential backoff.
    """
    attempts = max_attempts or _env_int("EVOLV_RETRY_MAX_ATTEMPTS", 3)
    attempts = max(1, attempts)
    delay0 = (
        base_delay if base_delay is not None
        else _env_float("EVOLV_RETRY_BASE_DELAY", 0.5)
    )
    is_retryable = retryable or default_retryable

    last: Optional[BaseException] = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - re-raised below
            last = exc
            if attempt >= attempts or not is_retryable(exc):
                if attempt >= attempts and is_retryable(exc):
                    _log_retry_exhausted(provider, attempt, exc)
                raise
            delay = min(max_delay, delay0 * (2 ** (attempt - 1)))
            if jitter and delay0 > 0:
                delay += random.uniform(0, delay0)
            sleep(delay)
    if last is not None:
        raise last
    raise ResilienceError("retry_call exhausted with no result")


# -----------------------------------------------------------------
# Circuit breaker
# -----------------------------------------------------------------

class CircuitState(str, Enum):
    """State of a circuit breaker."""

    CLOSED = "closed"        # normal operation
    OPEN = "open"            # failing fast, calls blocked
    HALF_OPEN = "half_open"  # one trial call permitted


class CircuitBreaker:
    """
    A per-dependency circuit breaker.

    Trips OPEN after ``failure_threshold`` consecutive failures.
    While OPEN, ``before_call()`` raises ``CircuitOpenError`` until
    ``recovery_timeout`` seconds have elapsed, after which a single
    HALF_OPEN trial is allowed. A successful trial closes the
    breaker; a failed trial re-opens it.

    Thread-safe. The clock is injectable for deterministic tests.

    :requirement: URS-51.7 - Circuit-break a failing external
                  dependency to fail fast and allow recovery.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.name = name
        self.failure_threshold = max(1, failure_threshold)
        self.recovery_timeout = max(0.0, recovery_timeout)
        self.half_open_max_calls = max(1, half_open_max_calls)
        self._clock = clock
        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at = 0.0
        self._half_open_calls = 0
        self._last_error = ""
        self._trip_count = 0

    def before_call(self) -> None:
        """
        Gate a call. Raise ``CircuitOpenError`` if the breaker is
        OPEN (and not yet recoverable) or a HALF_OPEN trial is
        already in flight.

        :requirement: URS-51.7 - Fail fast while OPEN.
        """
        with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = self._clock() - self._opened_at
                if elapsed >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._log(
                        "CIRCUIT_BREAKER_HALF_OPEN",
                        "recovery window elapsed; trial permitted",
                    )
                else:
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is OPEN "
                        f"({self._trip_count} trip(s)); retry in "
                        f"~{self.recovery_timeout - elapsed:.0f}s."
                    )
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' HALF_OPEN trial "
                        "already in progress."
                    )
                self._half_open_calls += 1

    def on_success(self) -> None:
        """
        Record a success; close the breaker if it was tripping.

        :requirement: URS-51.7 - Recover a circuit-broken
                      dependency.
        """
        with self._lock:
            if self._state in (
                CircuitState.HALF_OPEN, CircuitState.OPEN,
            ):
                self._log(
                    "CIRCUIT_BREAKER_CLOSED",
                    "dependency recovered; breaker closed",
                )
            self._state = CircuitState.CLOSED
            self._failures = 0
            self._half_open_calls = 0
            self._last_error = ""

    def on_failure(self, exc: BaseException) -> None:
        """
        Record a failure; open the breaker at the threshold.

        :requirement: URS-51.7 - Trip the breaker on repeated
                      dependency failure.
        """
        with self._lock:
            self._last_error = (
                f"{type(exc).__name__}: {exc}"
            )[:200]
            if self._state == CircuitState.HALF_OPEN:
                self._open_locked()
                return
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._open_locked()

    def _open_locked(self) -> None:
        """Transition to OPEN. Caller must hold ``_lock``."""
        self._state = CircuitState.OPEN
        self._opened_at = self._clock()
        self._trip_count += 1
        self._half_open_calls = 0
        self._log(
            "CIRCUIT_BREAKER_OPENED",
            f"{self._failures} consecutive failure(s); "
            f"blocking calls for {self.recovery_timeout:.0f}s",
        )

    def snapshot(self) -> Dict[str, Any]:
        """
        Return a value-free state snapshot for health surfaces.

        :requirement: URS-51.9 - Dependency health snapshot from
                      circuit-breaker state.
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "consecutive_failures": self._failures,
                "trip_count": self._trip_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_s": self.recovery_timeout,
                "last_error": self._last_error,
            }

    def _log(self, action: str, detail: str) -> None:
        """Write a breaker-transition audit event (best-effort)."""
        try:
            from Agents.integrity_manager import log_audit_event
            log_audit_event(
                agent_name="Resilience",
                action=action,
                decision_logic=f"[{self.name}] {detail}",
            )
        except Exception:
            # Audit logging must never break the resilience control
            # path; a transition that cannot be logged is still
            # applied.
            pass


# -----------------------------------------------------------------
# Named breaker registry + combined wrapper
# -----------------------------------------------------------------

_breakers: Dict[str, CircuitBreaker] = {}
_breakers_lock = threading.Lock()


def get_breaker(name: str) -> CircuitBreaker:
    """
    Return the process-wide circuit breaker for *name*, creating it
    from the env-configured thresholds on first use.

    :param name: Dependency label (e.g. "openai", "pinecone").
    :return: The shared ``CircuitBreaker`` for that dependency.
    :requirement: URS-51.7 - Per-dependency circuit breaker.
    """
    with _breakers_lock:
        breaker = _breakers.get(name)
        if breaker is None:
            breaker = CircuitBreaker(
                name,
                failure_threshold=_env_int(
                    "EVOLV_CB_FAILURE_THRESHOLD", 5,
                ),
                recovery_timeout=_env_float(
                    "EVOLV_CB_RECOVERY_TIMEOUT", 30.0,
                ),
            )
            _breakers[name] = breaker
        return breaker


def resilient_call(
    fn: Callable[..., Any],
    *args: Any,
    breaker: Optional[CircuitBreaker] = None,
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: float = 8.0,
    retryable: Optional[Callable[[BaseException], bool]] = None,
    sleep: Callable[[float], None] = time.sleep,
    **kwargs: Any,
) -> Any:
    """
    Call ``fn(*args, **kwargs)`` through an optional circuit
    breaker with bounded exponential-backoff retries.

    The breaker gates entry (fail fast when OPEN); retries handle
    transient blips; the breaker is updated with the final
    outcome. This is the wrapper used at each external call site.

    :param fn: The external callable (e.g. ``client.embeddings
               .create``).
    :param breaker: Circuit breaker to gate/record the call.
    :param max_attempts: Retry attempts (default env / 3).
    :param base_delay: First backoff seconds (default env / 0.5).
    :param max_delay: Upper bound on any single backoff.
    :param retryable: Transient-error predicate.
    :param sleep: Sleep function (injectable for tests).
    :return: The return value of *fn*.
    :requirement: URS-51.8 - Wrap external OpenAI/Pinecone calls
                  with retry + circuit breaker.
    """
    if breaker is not None:
        breaker.before_call()
    provider = breaker.name if breaker is not None else ""
    try:
        result = retry_call(
            lambda: fn(*args, **kwargs),
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            retryable=retryable,
            sleep=sleep,
            provider=provider,
        )
    except Exception as exc:
        if breaker is not None:
            breaker.on_failure(exc)
        raise
    if breaker is not None:
        breaker.on_success()
    return result


def health_snapshot() -> Dict[str, Any]:
    """
    Return the current health of every known dependency, derived
    from circuit-breaker state (no live API calls, no cost).

    ``healthy`` is False when any breaker is OPEN - the signal a
    monitoring/alerting surface consumes.

    :return: Dict with per-breaker snapshots and an overall flag.
    :requirement: URS-51.9 - Dependency health snapshot from
                  circuit-breaker state.
    """
    with _breakers_lock:
        snaps: List[Dict[str, Any]] = [
            b.snapshot() for b in _breakers.values()
        ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "breakers": snaps,
        "healthy": all(s["state"] != "open" for s in snaps),
    }


def _log_retry_exhausted(
    provider: str,
    attempts: int,
    exc: BaseException,
) -> None:
    """Write a ``DEPENDENCY_RETRY_EXHAUSTED`` audit event."""
    try:
        from Agents.integrity_manager import log_audit_event
        log_audit_event(
            agent_name="Resilience",
            action="DEPENDENCY_RETRY_EXHAUSTED",
            decision_logic=(
                f"[{provider or 'external'}] gave up after "
                f"{attempts} attempt(s); last error "
                f"{type(exc).__name__}: {exc}"[:200]
            ),
        )
    except Exception:
        # Never let audit-logging failure mask the original error.
        pass
