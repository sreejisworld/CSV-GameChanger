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


def _check_content(content: str) -> list[str]:
    """
    Return a list of function names that have NO :requirement: tag.

    Simple heuristic: scan line by line; when we see `def foo(`,
    look ahead up to 10 lines for a docstring containing :requirement:.
    """
    lines = content.splitlines()
    missing: list[str] = []

    for i, line in enumerate(lines):
        if not _FUNC_RE.match(line):
            continue

        # Extract function name
        m = re.search(r"def\s+(\w+)", line)
        func_name = m.group(1) if m else "?"

        # Skip private helpers and test functions
        if func_name.startswith("_") or func_name.startswith("test_"):
            continue

        # Look ahead for :requirement: tag within next 10 lines
        window = "\n".join(lines[i : i + 10])
        if not _TAG_RE.search(window):
            missing.append(func_name)

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
