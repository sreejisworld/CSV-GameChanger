"""
log_dev_change.py — PostToolUse hook.

Appends an audit record to output/dev_audit_trail.csv every time Claude
edits or writes a file during development. Makes the development of a
validated system itself auditable — EVOLV eating its own cooking.

CSV columns match the main audit trail schema so records can be merged:
  timestamp, agent_name, action, user_id, file_path, decision_logic,
  compliance_impact, reasoning_hash

:requirement: URS-2.1 - System shall maintain 21 CFR Part 11 compliant audit trail.
:requirement: URS-13.1 - Archive AI reasoning alongside audit records.
"""
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEV_AUDIT    = PROJECT_ROOT / "output" / "dev_audit_trail.csv"

HEADER = [
    "timestamp", "agent_name", "action", "user_id",
    "file_path", "decision_logic", "compliance_impact", "reasoning_hash",
]


def ensure_header(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HEADER)


def compute_hash(row: dict) -> str:
    payload = json.dumps(row, sort_keys=True, default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name  = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path  = tool_input.get("file_path", "unknown")
    ts         = datetime.now(timezone.utc).isoformat()

    action_map = {"Edit": "FILE_EDITED", "Write": "FILE_WRITTEN"}
    action     = action_map.get(tool_name, "FILE_MODIFIED")

    # Summarise what changed (keep it brief for the audit log)
    old = tool_input.get("old_string", "")
    new = tool_input.get("new_string", tool_input.get("content", ""))
    summary = (
        f"Modified {len(new.splitlines())} lines"
        if new else f"Tool: {tool_name}"
    )
    if old:
        summary += f" (replaced {len(old.splitlines())} lines)"

    row = {
        "timestamp":        ts,
        "agent_name":       "ClaudeCode",
        "action":           action,
        "user_id":          os.environ.get("USERNAME", os.environ.get("USER", "developer")),
        "file_path":        file_path,
        "decision_logic":   summary,
        "compliance_impact":"Development Change",
        "reasoning_hash":   "",
    }
    row["reasoning_hash"] = compute_hash(row)

    try:
        ensure_header(DEV_AUDIT)
        with open(DEV_AUDIT, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADER)
            writer.writerow(row)
    except Exception:
        # Never block Claude — audit logging must be non-fatal in dev hooks
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
