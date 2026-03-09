"""
TenantDictionary Middleware — API-Level Process Mimicry.

Intercepts every JSON API response and replaces internal EVOLV
label values with the active tenant's nomenclature overrides,
achieving ServiceNow-style "Process Mimicry" without touching
the database schema.

Example: outgoing JSON contains "Requirement" wherever the
tenant's ConfigService maps "requirement" → "User Need", the
middleware rewrites it to "User Need" transparently.

:requirement: URS-25.1 - System shall intercept API responses
              and apply tenant nomenclature overrides.
:requirement: URS-25.2 - Internal database keys must remain
              unchanged; only display labels are transformed.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse


class TenantDictionaryMiddleware(BaseHTTPMiddleware):
    """
    FastAPI / Starlette middleware that applies the active
    TenantConfig label map to every outgoing JSON response.

    Registered once on the FastAPI app; reads the ConfigService
    singleton on each request so label changes take effect
    immediately without a restart.

    Only JSON responses (Content-Type: application/json) are
    processed; all other responses are passed through unchanged.

    :requirement: URS-25.1 - API-level nomenclature interception.
    :requirement: URS-25.2 - Schema keys are never modified.
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Intercept the response, apply label substitution, return.

        :param request: Incoming HTTP request.
        :param call_next: Next middleware / route handler.
        :return: Potentially rewritten HTTP response.
        :requirement: URS-25.1
        """
        response: Response = await call_next(request)

        content_type = response.headers.get(
            "content-type", ""
        )
        if "application/json" not in content_type:
            return response

        # Read the full response body
        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk

        # Attempt label substitution
        try:
            body_bytes = self._substitute_labels(body_bytes)
        except Exception:
            # Never break the API — pass through on any error
            pass

        return Response(
            content=body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type="application/json",
        )

    @staticmethod
    def _substitute_labels(body: bytes) -> bytes:
        """
        Walk a JSON payload and substitute display labels.

        Only string *values* are rewritten — keys are left intact
        to preserve schema integrity.

        :param body: Raw JSON bytes.
        :return: Rewritten JSON bytes.
        :requirement: URS-25.2
        """
        try:
            from Agents.metadata_mapper import ConfigService
        except ImportError:
            return body

        svc = ConfigService.get_instance()
        labels = svc.mapper.get_all_labels()

        # Skip if no overrides are active
        from Agents.metadata_mapper import _DEFAULT_LABELS
        if labels == _DEFAULT_LABELS:
            return body

        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return body

        rewritten = _walk_and_replace(data, labels)

        return json.dumps(rewritten, ensure_ascii=False).encode(
            "utf-8"
        )


# -----------------------------------------------------------------
# Recursive JSON walker
# -----------------------------------------------------------------

def _walk_and_replace(
    node: Any,
    label_map: Dict[str, str],
) -> Any:
    """
    Recursively walk a parsed JSON structure and rewrite string
    values whose text matches a default EVOLV label.

    Dicts, lists, and scalars are all handled; only str values
    are candidates for substitution.

    :param node: Parsed JSON node (dict, list, str, int, …).
    :param label_map: Internal-key → display-label map.
    :return: Rewritten node of the same type.
    """
    if isinstance(node, dict):
        return {
            k: _walk_and_replace(v, label_map)
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [_walk_and_replace(i, label_map) for i in node]
    if isinstance(node, str):
        return _substitute_string(node, label_map)
    return node


def _substitute_string(
    text: str,
    label_map: Dict[str, str],
) -> str:
    """
    Replace default EVOLV labels in a string with tenant labels.

    Uses whole-word regex replacement (case-insensitive) for
    each overridden label so partial matches are avoided.

    :param text: Source string value from the JSON payload.
    :param label_map: Active label map from ConfigService.
    :return: Rewritten string.
    """
    from Agents.metadata_mapper import _DEFAULT_LABELS
    result = text
    for key, display in label_map.items():
        default = _DEFAULT_LABELS.get(key, "")
        if default and default.lower() != display.lower():
            result = re.sub(
                r"\b" + re.escape(default) + r"\b",
                display,
                result,
                flags=re.IGNORECASE,
            )
    return result
