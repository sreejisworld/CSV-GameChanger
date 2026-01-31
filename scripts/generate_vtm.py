"""
Validation Traceability Matrix (VTM) Generator for CSV-GameChanger.

Reads URS requirements from output/urs/ Markdown files, generates
test scripts via the TestGenerator agent, and produces a single CSV
file that links each requirement to its test steps.

Output: output/Trustme_Traceability_Matrix.csv

:requirement: URS-9.1 - System shall generate a Validation
              Traceability Matrix linking requirements to tests.
"""
import csv
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Agents.test_generator import (
    TestGenerator,
    TestGeneratorError,
    InvalidURSInputError,
    CSAGuidanceNotFoundError,
)


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
URS_INPUT_DIR = PROJECT_ROOT / "output" / "urs"
VTM_OUTPUT_DIR = PROJECT_ROOT / "output"
VTM_FILENAME = "Trustme_Traceability_Matrix.csv"
HEALTH_REPORT_FILENAME = "Trustme_Health_Report.txt"

VTM_COLUMNS = [
    "URS_ID",
    "Requirement_Statement",
    "Criticality",
    "Test_ID",
    "Step_Description",
    "Expected_Result",
    "Validation_Type",
    "CSA_Justification",
    "Source_Document",
]


def parse_urs_markdown(file_path: Path) -> List[Dict[str, str]]:
    """
    Parse a URS Markdown file and extract structured requirements.

    Reads the 'Detailed Requirements' section and extracts each
    requirement block identified by ``### URS-X.Y`` headings.

    :param file_path: Path to the URS Markdown file.
    :return: List of requirement dicts with keys URS_ID,
             Requirement_Statement, Criticality, and
             Regulatory_Rationale.
    :requirement: URS-9.2 - System shall parse URS documents from
                  output/urs/ directory.
    """
    content = file_path.read_text(encoding="utf-8")

    # Split on the Detailed Requirements heading to focus parsing
    detailed_marker = "## Detailed Requirements"
    if detailed_marker in content:
        content = content.split(detailed_marker, 1)[1]

    # Split into individual requirement blocks by ### heading
    blocks = re.split(r"(?=^### URS-)", content, flags=re.MULTILINE)

    requirements: List[Dict[str, str]] = []

    for block in blocks:
        block = block.strip()
        if not block.startswith("### URS-"):
            continue

        urs_id = _extract_urs_id(block)
        if not urs_id:
            continue

        statement = _extract_field(
            block, "Requirement Statement"
        )
        criticality = _extract_field(block, "Criticality")
        rationale = _extract_field(
            block, "Regulatory Rationale"
        )

        if not statement:
            continue

        requirements.append({
            "URS_ID": urs_id,
            "Requirement_Statement": statement,
            "Criticality": criticality or "Medium",
            "Regulatory_Rationale": rationale or "",
        })

    return requirements


def _extract_urs_id(block: str) -> Optional[str]:
    """
    Extract the URS ID from a requirement block heading.

    :param block: Markdown block starting with ### URS-X.Y.
    :return: The URS ID string, or None if not found.
    """
    match = re.match(r"###\s+(URS-[\d.]+)", block)
    if match:
        return match.group(1)
    return None


def _extract_field(block: str, field_name: str) -> str:
    """
    Extract a field value from a URS requirement block.

    Handles two formats:
    - Inline: ``**Field:** value``
    - Block quote: ``**Field:**`` followed by ``> value``

    :param block: The Markdown requirement block.
    :param field_name: The field label (e.g. "Criticality").
    :return: The extracted value, stripped of Markdown syntax.
    """
    # Try inline format: **Field:** value on the same line
    inline = re.search(
        rf"\*\*{re.escape(field_name)}:\*\*\s*(.+)",
        block,
    )
    if inline:
        value = inline.group(1).strip()
        # If value is empty, look for block-quote on next lines
        if not value:
            return _extract_blockquote_after(
                block, field_name
            )
        # If value starts with >, it's a block-quote on same line
        if value.startswith(">"):
            value = value[1:].strip()
        return _clean_field_value(value)

    return ""


def _extract_blockquote_after(
    block: str, field_name: str
) -> str:
    """
    Extract a block-quote value that follows a field heading.

    :param block: The Markdown requirement block.
    :param field_name: The field label.
    :return: Concatenated block-quote lines.
    """
    pattern = (
        rf"\*\*{re.escape(field_name)}:\*\*\s*\n"
        rf"((?:>.*\n?)+)"
    )
    match = re.search(pattern, block)
    if match:
        lines = match.group(1).strip().split("\n")
        cleaned = []
        for line in lines:
            line = line.strip()
            if line.startswith(">"):
                line = line[1:].strip()
            cleaned.append(line)
        return _clean_field_value(" ".join(cleaned))
    return ""


def _clean_field_value(value: str) -> str:
    """
    Clean a field value by normalizing whitespace.

    :param value: Raw extracted value.
    :return: Cleaned string.
    """
    # Collapse multiple whitespace / newlines into single space
    value = re.sub(r"\s+", " ", value).strip()
    return value


def discover_urs_files(
    urs_dir: Path,
) -> List[Path]:
    """
    Discover all URS Markdown files in the output directory.

    :param urs_dir: Directory to scan for .md files.
    :return: Sorted list of URS file paths.
    :requirement: URS-9.3 - System shall discover URS files
                  automatically.
    """
    if not urs_dir.exists():
        return []

    files = sorted(
        urs_dir.glob("URS_*.md"),
        key=lambda p: p.stat().st_mtime,
    )
    return files


def generate_vtm_rows(
    requirements: List[Dict[str, str]],
    source_file: str,
    generator: TestGenerator,
    verbose: bool = True,
    source_path: Optional[Path] = None,
) -> List[Dict[str, str]]:
    """
    Generate VTM rows by running each requirement through the
    TestGenerator and flattening the test steps.

    Each URS requirement produces multiple rows — one per test step
    — so the resulting CSV provides a complete link from
    requirement to individual test action.

    When source_path is provided, uses timestamp-based caching to
    skip regeneration of test scripts whose source URS file has
    not been modified since the last run.

    :param requirements: List of parsed URS requirement dicts.
    :param source_file: Filename of the source URS document.
    :param generator: An initialized TestGenerator instance.
    :param verbose: Whether to print progress messages.
    :param source_path: Full Path to the source URS file for
                        timestamp-based cache comparison.
    :return: List of flat row dicts matching VTM_COLUMNS.
    :requirement: URS-9.4 - System shall link requirements to
                  test steps in the traceability matrix.
    """
    rows: List[Dict[str, str]] = []

    for i, req in enumerate(requirements, 1):
        urs_id = req["URS_ID"]

        if verbose:
            print(
                f"  [{i}/{len(requirements)}] "
                f"Generating tests for {urs_id}..."
            )

        try:
            if source_path is not None:
                script = (
                    generator.generate_test_script_if_stale(
                        req, source_path
                    )
                )
            else:
                script = generator.generate_test_script(req)
        except CSAGuidanceNotFoundError:
            if verbose:
                print(
                    f"    [WARN] No CSA guidance found for "
                    f"{urs_id} — skipping test generation."
                )
            # Still record the requirement with no test linkage
            rows.append({
                "URS_ID": urs_id,
                "Requirement_Statement": req[
                    "Requirement_Statement"
                ],
                "Criticality": req["Criticality"],
                "Test_ID": "N/A",
                "Step_Description": (
                    "Test not generated — no CSA guidance "
                    "found in Pinecone."
                ),
                "Expected_Result": "N/A",
                "Validation_Type": "N/A",
                "CSA_Justification": "No CSA guidance found.",
                "Source_Document": source_file,
            })
            continue
        except TestGeneratorError as e:
            if verbose:
                print(f"    [ERROR] {e}")
            rows.append({
                "URS_ID": urs_id,
                "Requirement_Statement": req[
                    "Requirement_Statement"
                ],
                "Criticality": req["Criticality"],
                "Test_ID": "ERROR",
                "Step_Description": f"Error: {e}",
                "Expected_Result": "N/A",
                "Validation_Type": "N/A",
                "CSA_Justification": "N/A",
                "Source_Document": source_file,
            })
            continue

        csa_justification = script.get(
            "CSA_Justification", ""
        )

        for step in script.get("Test_Steps", []):
            rows.append({
                "URS_ID": urs_id,
                "Requirement_Statement": req[
                    "Requirement_Statement"
                ],
                "Criticality": req["Criticality"],
                "Test_ID": step["Test_ID"],
                "Step_Description": step["Step_Description"],
                "Expected_Result": step["Expected_Result"],
                "Validation_Type": step["Validation_Type"],
                "CSA_Justification": csa_justification,
                "Source_Document": source_file,
            })

        if verbose:
            step_count = len(script.get("Test_Steps", []))
            vtype = script["Test_Steps"][0][
                "Validation_Type"
            ] if script.get("Test_Steps") else "N/A"
            print(
                f"    [OK] {step_count} steps "
                f"({vtype})"
            )

    return rows


def write_vtm_csv(
    rows: List[Dict[str, str]],
    output_path: Path,
) -> Path:
    """
    Write the traceability matrix rows to a CSV file.

    :param rows: List of flat row dicts matching VTM_COLUMNS.
    :param output_path: Full path for the output CSV file.
    :return: Path to the written CSV file.
    :requirement: URS-9.5 - System shall output the traceability
                  matrix as a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        # Header branding row
        f.write(
            "# Generated by Trustme AI"
            " - Regulatory Compliance Engine"
            f" | {timestamp}\n"
        )

        writer = csv.DictWriter(
            f, fieldnames=VTM_COLUMNS, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)

        # Footer branding row
        f.write(
            "# GxP Validated Output - Alpha version\n"
        )

    return output_path


def write_health_report(
    rows: List[Dict[str, str]],
    output_path: Path,
) -> Path:
    """
    Write a Trustme Health Report summarizing the VTM results.

    Aggregates VTM rows by unique URS_ID to produce:
    - Total number of requirements
    - Breakdown by criticality (High / Medium / Low counts
      and percentages)
    - Compliance status showing what percentage of
      requirements are fully traced to test steps

    A requirement is considered "traced" when at least one of
    its VTM rows has a valid Test_ID (not "N/A" or "ERROR").

    :param rows: List of flat row dicts from VTM generation.
    :param output_path: Full path for the output text file.
    :return: Path to the written health report.
    :requirement: URS-9.6 - System shall output a health report
                  summarizing traceability coverage.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    # Aggregate by unique URS_ID
    reqs: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        urs_id = row["URS_ID"]
        if urs_id not in reqs:
            reqs[urs_id] = {
                "criticality": row["Criticality"],
                "traced": False,
            }
        if row["Test_ID"] not in ("N/A", "ERROR"):
            reqs[urs_id]["traced"] = True

    total = len(reqs)

    # Criticality counts
    high_count = sum(
        1 for r in reqs.values()
        if r["criticality"].lower() == "high"
    )
    medium_count = sum(
        1 for r in reqs.values()
        if r["criticality"].lower() == "medium"
    )
    low_count = sum(
        1 for r in reqs.values()
        if r["criticality"].lower() == "low"
    )

    # Percentages (guard against zero division)
    high_pct = (high_count / total * 100) if total else 0.0
    medium_pct = (
        (medium_count / total * 100) if total else 0.0
    )
    low_pct = (low_count / total * 100) if total else 0.0

    # Compliance status
    traced_count = sum(
        1 for r in reqs.values() if r["traced"]
    )
    traced_pct = (
        (traced_count / total * 100) if total else 0.0
    )
    compliance_status = f"{traced_pct:.0f}% Traced"

    # Build report
    divider = "=" * 60
    section = "-" * 60

    lines = [
        divider,
        "  Trustme AI - Regulatory Compliance Engine",
        "  Health Report",
        divider,
        f"  Generated: {timestamp}",
        "",
        section,
        "  REQUIREMENTS SUMMARY",
        section,
        f"  Total Requirements:  {total}",
        "",
        f"  High-Risk:           {high_count:>4}  "
        f"({high_pct:.1f}%)",
        f"  Medium-Risk:         {medium_count:>4}  "
        f"({medium_pct:.1f}%)",
        f"  Low-Risk:            {low_count:>4}  "
        f"({low_pct:.1f}%)",
        "",
        section,
        "  COMPLIANCE STATUS",
        section,
        f"  Traced Requirements: {traced_count} / {total}",
        f"  Compliance Status:   {compliance_status}",
        "",
    ]

    # List any untraced requirements
    untraced = [
        uid for uid, r in reqs.items() if not r["traced"]
    ]
    if untraced:
        lines.append(
            "  UNTRACED REQUIREMENTS (action required):"
        )
        for uid in sorted(untraced):
            lines.append(f"    - {uid}")
        lines.append("")

    lines.append(divider)
    lines.append("  GxP Validated Output - Alpha version")
    lines.append(divider)
    lines.append("")

    output_path.write_text(
        "\n".join(lines), encoding="utf-8"
    )

    return output_path


def generate_vtm(
    urs_dir: Path = URS_INPUT_DIR,
    output_dir: Path = VTM_OUTPUT_DIR,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Main entry point: discover URS files, generate test scripts,
    and produce the Validation Traceability Matrix CSV.

    :param urs_dir: Directory containing URS Markdown files.
    :param output_dir: Directory to write the CSV output.
    :param verbose: Whether to print progress messages.
    :return: Dictionary with generation results.
    :requirement: URS-9.1 - System shall generate a Validation
                  Traceability Matrix.
    """
    if verbose:
        print("\n" + "=" * 60)
        print("Generated by Trustme AI"
              " - Regulatory Compliance Engine")
        print("Validation Traceability Matrix Generator")
        print("=" * 60)

    # Discover URS files
    urs_files = discover_urs_files(urs_dir)

    if not urs_files:
        msg = (
            f"No URS files found in {urs_dir}. "
            f"Run scripts/draft_urs.py first."
        )
        if verbose:
            print(f"\nError: {msg}")
        return {"status": "error", "message": msg}

    if verbose:
        print(f"\nFound {len(urs_files)} URS file(s):\n")
        for f in urs_files:
            print(f"  - {f.name}")

    # Initialize TestGenerator
    try:
        generator = TestGenerator()
    except ImportError as e:
        msg = f"Missing dependency: {e}"
        if verbose:
            print(f"\nError: {msg}")
        return {"status": "error", "message": msg}

    # Process each URS file
    all_rows: List[Dict[str, str]] = []
    total_reqs = 0
    total_errors = 0

    for urs_file in urs_files:
        if verbose:
            print(f"\nProcessing: {urs_file.name}")
            print("-" * 50)

        requirements = parse_urs_markdown(urs_file)

        if not requirements:
            if verbose:
                print(
                    "  [WARN] No requirements found in file."
                )
            continue

        if verbose:
            print(
                f"  Parsed {len(requirements)} requirement(s)"
            )

        total_reqs += len(requirements)

        rows = generate_vtm_rows(
            requirements=requirements,
            source_file=urs_file.name,
            generator=generator,
            verbose=verbose,
            source_path=urs_file,
        )

        error_rows = [
            r for r in rows
            if r["Test_ID"] in ("N/A", "ERROR")
        ]
        total_errors += len(error_rows)

        all_rows.extend(rows)

    if not all_rows:
        msg = "No traceability rows generated."
        if verbose:
            print(f"\nError: {msg}")
        return {"status": "error", "message": msg}

    # Write CSV
    output_path = output_dir / VTM_FILENAME
    write_vtm_csv(all_rows, output_path)

    # Write Health Report
    health_path = output_dir / HEALTH_REPORT_FILENAME
    write_health_report(all_rows, health_path)

    if verbose:
        print("\n" + "=" * 60)
        print("VTM GENERATION COMPLETE")
        print("=" * 60)
        print(f"  Requirements processed: {total_reqs}")
        print(f"  Traceability rows:      {len(all_rows)}")
        print(f"  Errors / warnings:      {total_errors}")
        print(f"  VTM output:             {output_path}")
        print(f"  Health report:          {health_path}")
        print()
        print("GxP Validated Output - Alpha version")
        print()

    return {
        "status": "success",
        "output_path": str(output_path),
        "health_report_path": str(health_path),
        "requirements_processed": total_reqs,
        "traceability_rows": len(all_rows),
        "errors": total_errors,
    }


def main() -> None:
    """
    CLI entry point for the VTM generator.

    :requirement: URS-9.1 - System shall generate a Validation
                  Traceability Matrix.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate a Validation Traceability Matrix (VTM) "
            "linking URS requirements to test scripts."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: read from output/urs/, write to output/
  python scripts/generate_vtm.py

  # Custom URS directory
  python scripts/generate_vtm.py -u path/to/urs_files

  # Custom output directory
  python scripts/generate_vtm.py -o path/to/output

  # Quiet mode
  python scripts/generate_vtm.py -q
        """,
    )

    parser.add_argument(
        "-u", "--urs-dir",
        type=Path,
        default=URS_INPUT_DIR,
        help=(
            f"Directory containing URS Markdown files "
            f"(default: {URS_INPUT_DIR})"
        ),
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=VTM_OUTPUT_DIR,
        help=(
            f"Directory to write the VTM CSV "
            f"(default: {VTM_OUTPUT_DIR})"
        ),
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output",
    )

    args = parser.parse_args()

    result = generate_vtm(
        urs_dir=args.urs_dir,
        output_dir=args.output_dir,
        verbose=not args.quiet,
    )

    if result["status"] == "success":
        sys.exit(0)
    else:
        if not args.quiet:
            print(
                f"Error: {result.get('message', 'Unknown')}"
            )
        sys.exit(1)


if __name__ == "__main__":
    main()
