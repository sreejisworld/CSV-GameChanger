"""
Digital Sign-Off Script for CSV-GameChanger.

Prompts the user for their name and a Meaning of Signature, computes
an MD5 hash of the latest Trustme_Health_Report.txt, and appends
a sign-off record to output/audit_trail.csv via the IntegrityManager.

The MD5 hash acts as a digital seal: if the health report is later
modified, recomputing the hash will produce a different value, proving
the document changed after approval.

Usage:
    python scripts/sign_off.py

:requirement: URS-11.1 - System shall support digital sign-off with
              tamper-evident document hashing.
"""
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Agents.integrity_manager import log_audit_event


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
HEALTH_REPORT_PATH = PROJECT_ROOT / "output" / "Trustme_Health_Report.txt"


def compute_file_md5(file_path: Path) -> str:
    """
    Compute the MD5 hex digest of a file's contents.

    Reads the file in binary mode to ensure the hash is
    consistent regardless of platform line-ending handling.

    :param file_path: Absolute path to the file to hash.
    :return: 32-character lowercase hex MD5 digest.
    :requirement: URS-11.1 - System shall hash documents for
                  tamper-evident sign-off.
    """
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def sign_off() -> None:
    """
    Interactive sign-off workflow.

    1. Verifies Trustme_Health_Report.txt exists.
    2. Prompts the user for their full name.
    3. Prompts the user for a Meaning of Signature.
    4. Computes an MD5 hash of the report.
    5. Logs the sign-off to audit_trail.csv with decision
       logic containing the hash, signer name, and meaning.

    :requirement: URS-11.1 - System shall support digital sign-off.
    """
    print()
    print("=" * 60)
    print("  EVOLV - Digital Sign-Off")
    print("=" * 60)

    # ----------------------------------------------------------
    # Step 1: Locate the health report
    # ----------------------------------------------------------
    if not HEALTH_REPORT_PATH.exists():
        print()
        print(
            f"  ERROR: Health report not found at:"
        )
        print(f"    {HEALTH_REPORT_PATH}")
        print()
        print(
            "  Run 'python scripts/generate_vtm.py' first to"
        )
        print("  generate the Trustme_Health_Report.txt.")
        print()
        sys.exit(1)

    report_mtime = datetime.fromtimestamp(
        HEALTH_REPORT_PATH.stat().st_mtime,
        tz=timezone.utc,
    ).strftime("%Y-%m-%d %H:%M:%S UTC")

    print()
    print(f"  Document: {HEALTH_REPORT_PATH.name}")
    print(f"  Last Modified: {report_mtime}")
    print()

    # ----------------------------------------------------------
    # Step 2: Collect signer identity
    # ----------------------------------------------------------
    print("-" * 60)
    signer_name = input(
        "  Enter your full name: "
    ).strip()

    if not signer_name:
        print()
        print("  ERROR: Signer name cannot be empty.")
        sys.exit(1)

    # ----------------------------------------------------------
    # Step 3: Collect Meaning of Signature
    # ----------------------------------------------------------
    print()
    print("  Meaning of Signature examples:")
    print("    - Review and Approval")
    print("    - Authored")
    print("    - Verified")
    print("    - Quality Approval")
    print()
    meaning = input(
        "  Enter Meaning of Signature: "
    ).strip()

    if not meaning:
        print()
        print("  ERROR: Meaning of Signature cannot be empty.")
        sys.exit(1)

    # ----------------------------------------------------------
    # Step 4: Compute the MD5 document seal
    # ----------------------------------------------------------
    document_hash = compute_file_md5(HEALTH_REPORT_PATH)

    # ----------------------------------------------------------
    # Step 5: Log the sign-off to the audit trail
    # ----------------------------------------------------------
    decision_logic = (
        f"Document: {HEALTH_REPORT_PATH.name}; "
        f"MD5: {document_hash}; "
        f"Signer: {signer_name}; "
        f"Meaning: {meaning}"
    )

    reasoning_hash = log_audit_event(
        agent_name="SignOff",
        action="DOCUMENT_SIGN_OFF",
        user_id=signer_name,
        decision_logic=decision_logic,
        compliance_impact="Electronic Signature",
    )

    # ----------------------------------------------------------
    # Confirmation
    # ----------------------------------------------------------
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    print()
    print("=" * 60)
    print("  SIGN-OFF RECORDED")
    print("=" * 60)
    print(f"  Timestamp:    {timestamp}")
    print(f"  Signer:       {signer_name}")
    print(f"  Meaning:      {meaning}")
    print(f"  Document:     {HEALTH_REPORT_PATH.name}")
    print(f"  Document MD5: {document_hash}")
    print(f"  Audit Hash:   {reasoning_hash}")
    print()
    print(
        "  This record has been appended to the audit trail."
    )
    print(
        "  Any future modification to the health report will"
    )
    print(
        "  produce a different MD5, proving the document"
    )
    print("  changed after this approval.")
    print()
    print(
        "  GxP Validated Output - Alpha version"
    )
    print("=" * 60)
    print()


if __name__ == "__main__":
    sign_off()
