"""
protect_audit_trail.py — PreToolUse hook.

Blocks any tool call that would modify EVOLV's immutable audit artifacts:
  - output/audit_trail.csv
  - output/logic_archives/

Exit codes (Claude Code convention):
  0 = allow
  2 = block (reason printed to stderr, shown to Claude as feedback)

:requirement: URS-2.1 - System shall maintain 21 CFR Part 11 compliant audit trail.
"""
import json
import sys

PROTECTED = [
    "output/audit_trail.csv",
    "output\\audit_trail.csv",
    "output/logic_archives",
    "output\\logic_archives",
]

BLOCK_MSG = (
    "BLOCKED — 21 CFR Part 11 compliance: '{path}' is an immutable audit "
    "artifact. Audit records must only be appended via "
    "Agents/integrity_manager.py:log_audit_event(). "
    "Never edit the file directly."
)


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name  = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name in ("Edit", "Write"):
        file_path = tool_input.get("file_path", "")
        for p in PROTECTED:
            if p in file_path:
                print(BLOCK_MSG.format(path=file_path), file=sys.stderr)
                sys.exit(2)

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        for p in PROTECTED:
            if p in command:
                print(
                    f"BLOCKED — 21 CFR Part 11 compliance: Bash command "
                    f"references protected audit artifact '{p}'. "
                    f"Use log_audit_event() instead.",
                    file=sys.stderr,
                )
                sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
