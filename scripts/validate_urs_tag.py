"""
validate_urs_tag.py — PostToolUse hook.

Warns (never blocks) when Claude writes a new Python function to an Agents/
or utils/ file without a :requirement: URS-X.Y docstring tag.

This enforces the traceability rule from CLAUDE.md §2 — every function in
a validated module must link back to a User Requirement.

Exit codes:
  0 = allow (always — this hook warns but never blocks)

:requirement: URS-2.1 - System shall maintain 21 CFR Part 11 compliant audit trail.
"""
import json
import re
import sys

# Only enforce traceability in these directories
SCOPED_PATHS = [
    "Agents/",
    "agents/",
    "utils/",
    "API/",
    "api/",
    "scripts/",
]

# Matches a function definition line
_FUNC_RE = re.compile(r"^\s*def\s+\w+")

# Matches a :requirement: tag anywhere in the string
_TAG_RE = re.compile(r":requirement:\s*URS-\d+\.\d+")


def _in_scope(file_path: str) -> bool:
    return any(p in file_path for p in SCOPED_PATHS)


# Boilerplate exempt from URS tagging — mirrors the CI gate
# (scripts/compliance_check.sh). Traceability applies to
# behavior, not serialization plumbing or framework overrides.
_EXEMPT_NAMES = {
    "to_dict", "from_dict", "to_json", "to_list",
    "to_full_dict", "get_instance", "header", "footer",
}

_EXEMPT_DECORATORS = {"property", "cached_property", "overload"}


def _check_content(content: str) -> list[str]:
    """
    Return a list of function names that have NO :requirement:
    tag in their docstring.

    AST-based (same semantics as the CI compliance gate): the
    tag may appear anywhere in the docstring; properties,
    overload stubs, and serialization boilerplate are exempt.
    Falls back to no findings on syntax errors — the hook must
    never block on code that is mid-edit.
    """
    import ast

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    missing: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        name = node.name
        if name.startswith("_") or name.startswith("test_"):
            continue
        if name in _EXEMPT_NAMES:
            continue
        dec_names = {
            getattr(d, "id", "") or getattr(d, "attr", "")
            for d in node.decorator_list
        }
        if dec_names & _EXEMPT_DECORATORS:
            continue
        doc = ast.get_docstring(node) or ""
        if not _TAG_RE.search(doc):
            missing.append(name)

    return missing


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name  = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name not in ("Edit", "Write"):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not _in_scope(file_path):
        sys.exit(0)

    # For Write: check full content; for Edit: check new_string
    if tool_name == "Write":
        content = tool_input.get("content", "")
    else:
        content = tool_input.get("new_string", "")

    if not content.strip():
        sys.exit(0)

    missing = _check_content(content)
    if missing:
        print(
            f"[EVOLV traceability] {file_path}: "
            f"public function(s) {missing} may be missing "
            f"':requirement: URS-X.Y' docstring tag. "
            f"See CLAUDE.md §2 — The Traceability Rule.",
            file=sys.stderr,
        )
        # Exit 0: warn only, never block
    sys.exit(0)


if __name__ == "__main__":
    main()
