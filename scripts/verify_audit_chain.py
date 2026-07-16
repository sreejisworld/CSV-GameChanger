"""
verify_audit_chain.py — Walk the EVOLV audit trail and verify
the SHA-256 hash chain (Sprint 45, closes security finding SEC-9).

An inspector (or a nightly job) runs this against the central
audit trail. Every row must verify as either a chained row
(hash covers the previous row's hash + this row's fields) or a
legacy row (per-row hash, written before the chain upgrade).
Any edited, reordered, or deleted-in-the-middle row breaks the
chain and is reported with its row number.

Usage:
    python scripts/verify_audit_chain.py
    python scripts/verify_audit_chain.py --path output/audit_trail.csv
    python scripts/verify_audit_chain.py --json

Exit codes:
    0 — chain intact
    1 — issues found (tampering / malformed rows)

Record the printed head hash externally (QA log) so tail
truncation — undetectable from the file alone — is caught by
comparing heads across verification runs.

:requirement: URS-45.2 - Full-chain verification an inspector
              can run on demand.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from Agents.integrity_manager import (  # noqa: E402
    AUDIT_TRAIL_PATH,
    verify_audit_chain,
)


def main() -> int:
    """Run chain verification and print a report.

    :return: Process exit code (0 intact, 1 issues).
    :requirement: URS-45.2 - Chain verification CLI.
    """
    parser = argparse.ArgumentParser(
        prog="verify-audit-chain",
        description=(
            "Verify the SHA-256 hash chain of the EVOLV audit "
            "trail."
        ),
    )
    parser.add_argument(
        "--path", type=Path, default=AUDIT_TRAIL_PATH,
        help="Audit CSV to verify (default: central trail).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Machine-readable JSON output.",
    )
    args = parser.parse_args()

    report = verify_audit_chain(args.path)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.intact else 1

    status = "INTACT" if report.intact else "ISSUES FOUND"
    print("EVOLV Audit Trail Chain Verification")
    print(f"  File:       {report.audit_path}")
    print(f"  Verified:   {report.verified_at}")
    print(f"  Status:     {status}")
    print(
        f"  Rows:       {report.total_rows} total · "
        f"{report.chained_ok} chained · "
        f"{report.legacy_ok} legacy (pre-chain)"
    )
    print(f"  Head hash:  {report.head_hash}")
    print(
        "  Note: record the head hash externally; tail "
        "truncation is only detectable by comparing heads "
        "across runs."
    )
    if report.issues:
        print(f"\n  {len(report.issues)} issue(s):")
        for issue in report.issues:
            print(
                f"   row {issue.row_number:>5}  "
                f"[{issue.timestamp}] {issue.action}: "
                f"{issue.reason}"
            )
    return 0 if report.intact else 1


if __name__ == "__main__":
    sys.exit(main())
