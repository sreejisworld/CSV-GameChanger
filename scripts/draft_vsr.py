"""
Validation Summary Report (VSR) Drafting Script for CSV-GameChanger.

Reads the Trustme Health Report and URS files from output/urs/,
then uses an LLM to generate a Validation Summary Report in
Markdown.  The report includes an Executive Summary, Scope,
Testing Summary, Conclusion, and Trustme-branded footer.

Output: output/VSR_<ProjectName>_<timestamp>.md

:requirement: URS-11.1 - System shall generate a Validation
              Summary Report from health report and URS data.
"""
import csv
import os
import re
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
URS_INPUT_DIR = PROJECT_ROOT / "output" / "urs"
VTM_OUTPUT_DIR = PROJECT_ROOT / "output"
HEALTH_REPORT_PATH = VTM_OUTPUT_DIR / "Trustme_Health_Report.txt"
VTM_CSV_PATH = VTM_OUTPUT_DIR / "Trustme_Traceability_Matrix.csv"
VSR_OUTPUT_DIR = VTM_OUTPUT_DIR / "vsr"
LLM_MODEL = "gpt-4o"

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("draft_vsr")


# ── Exceptions ────────────────────────────────────────────


class VSRGenerationError(Exception):
    """
    Base exception for VSR generation errors.

    Error code: CSV-008 - VSR generation failed.
    """

    error_code = "CSV-008"


class HealthReportNotFoundError(VSRGenerationError):
    """
    Raised when the Trustme Health Report is missing.

    Error code: CSV-009 - Health report not found.

    :requirement: URS-11.2 - System shall require a health
                  report before generating the VSR.
    """

    error_code = "CSV-009"

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(
            f"Health report not found at {path}. "
            f"Run scripts/generate_vtm.py first."
        )


class VTMNotFoundError(VSRGenerationError):
    """
    Raised when the Traceability Matrix CSV is missing.

    Error code: CSV-010 - Traceability matrix not found.

    :requirement: URS-11.3 - System shall require a VTM before
                  generating the VSR.
    """

    error_code = "CSV-010"

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(
            f"Traceability matrix not found at {path}. "
            f"Run scripts/generate_vtm.py first."
        )


# ── Data Collection ───────────────────────────────────────


def read_health_report(
    path: Path = HEALTH_REPORT_PATH,
) -> str:
    """
    Read the Trustme Health Report text file.

    :param path: Path to Trustme_Health_Report.txt.
    :return: Full text content of the health report.
    :raises HealthReportNotFoundError: If the file is missing.
    :requirement: URS-11.2 - System shall read the health
                  report.
    """
    if not path.exists():
        raise HealthReportNotFoundError(path)
    return path.read_text(encoding="utf-8")


def read_vtm_csv(
    path: Path = VTM_CSV_PATH,
) -> List[Dict[str, str]]:
    """
    Read the Traceability Matrix CSV and return its rows.

    Skips comment lines (lines starting with ``#``).

    :param path: Path to Trustme_Traceability_Matrix.csv.
    :return: List of row dicts keyed by CSV column headers.
    :raises VTMNotFoundError: If the file is missing.
    :requirement: URS-11.3 - System shall read the VTM for
                  testing statistics.
    """
    if not path.exists():
        raise VTMNotFoundError(path)

    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        # Filter out comment lines before handing to csv
        data_lines = [
            line for line in f if not line.startswith("#")
        ]

    reader = csv.DictReader(data_lines)
    for row in reader:
        rows.append(dict(row))

    return rows


def discover_urs_files(
    urs_dir: Path = URS_INPUT_DIR,
) -> List[Path]:
    """
    Discover URS Markdown files in the output directory.

    :param urs_dir: Directory to scan for .md files.
    :return: Sorted list of URS file paths.
    :requirement: URS-11.4 - System shall discover URS files
                  for context.
    """
    if not urs_dir.exists():
        return []
    return sorted(
        urs_dir.glob("URS_*.md"),
        key=lambda p: p.stat().st_mtime,
    )


def read_urs_summaries(
    urs_files: List[Path],
) -> List[Dict[str, str]]:
    """
    Extract a lightweight summary from each URS file.

    Pulls the project name, total requirements count, and the
    requirements table from the header section.

    :param urs_files: List of URS Markdown file paths.
    :return: List of summary dicts with project, total, and
             table keys.
    :requirement: URS-11.4 - System shall read URS files for
                  VSR context.
    """
    summaries: List[Dict[str, str]] = []

    for urs_file in urs_files:
        content = urs_file.read_text(encoding="utf-8")

        # Extract project name
        project_match = re.search(
            r"\*\*Project:\*\*\s*(.+)", content
        )
        project = (
            project_match.group(1).strip()
            if project_match
            else urs_file.stem
        )

        # Extract total requirements
        total_match = re.search(
            r"\*\*Total Requirements:\*\*\s*(\d+)", content
        )
        total = (
            total_match.group(1) if total_match else "N/A"
        )

        # Extract the requirements table
        table_lines: List[str] = []
        in_table = False
        for line in content.split("\n"):
            if line.startswith("| URS ID"):
                in_table = True
            if in_table:
                if line.startswith("|"):
                    table_lines.append(line)
                else:
                    break

        summaries.append({
            "file": urs_file.name,
            "project": project,
            "total": total,
            "table": "\n".join(table_lines),
        })

    return summaries


def compute_testing_stats(
    vtm_rows: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Compute testing statistics from the VTM rows.

    Counts unique test IDs by Validation_Type and tallies
    requirements by criticality.

    :param vtm_rows: Rows from the traceability matrix CSV.
    :return: Dictionary with scripted/unscripted counts, totals,
             and criticality breakdown.
    :requirement: URS-11.5 - System shall compute scripted vs
                  unscripted test counts.
    """
    # Unique requirements
    reqs: Dict[str, Dict[str, str]] = {}
    for row in vtm_rows:
        urs_id = row.get("URS_ID", "")
        if urs_id and urs_id not in reqs:
            reqs[urs_id] = {
                "criticality": row.get("Criticality", ""),
                "validation_type": row.get(
                    "Validation_Type", ""
                ),
            }

    total_reqs = len(reqs)

    # Criticality breakdown
    high = sum(
        1 for r in reqs.values()
        if r["criticality"].lower() == "high"
    )
    medium = sum(
        1 for r in reqs.values()
        if r["criticality"].lower() == "medium"
    )
    low = sum(
        1 for r in reqs.values()
        if r["criticality"].lower() == "low"
    )

    # Unique test steps by validation type
    scripted_tests: set[str] = set()
    unscripted_tests: set[str] = set()
    error_tests: set[str] = set()

    for row in vtm_rows:
        test_id = row.get("Test_ID", "")
        vtype = row.get("Validation_Type", "").lower()

        if test_id in ("N/A", "ERROR", ""):
            if test_id in ("N/A", "ERROR"):
                error_tests.add(
                    row.get("URS_ID", "") + test_id
                )
            continue

        if vtype == "scripted":
            scripted_tests.add(test_id)
        elif vtype == "unscripted":
            unscripted_tests.add(test_id)

    # Traced vs untraced
    traced_ids: set[str] = set()
    for row in vtm_rows:
        if row.get("Test_ID", "") not in ("N/A", "ERROR", ""):
            traced_ids.add(row.get("URS_ID", ""))

    traced = len(traced_ids)
    traced_pct = (traced / total_reqs * 100) if total_reqs else 0.0

    return {
        "total_requirements": total_reqs,
        "high_risk": high,
        "medium_risk": medium,
        "low_risk": low,
        "scripted_test_count": len(scripted_tests),
        "unscripted_test_count": len(unscripted_tests),
        "total_test_steps": (
            len(scripted_tests) + len(unscripted_tests)
        ),
        "traced": traced,
        "traced_pct": traced_pct,
        "errors": len(error_tests),
    }


# ── LLM Generation ───────────────────────────────────────


def build_llm_prompt(
    health_report: str,
    urs_summaries: List[Dict[str, str]],
    stats: Dict[str, Any],
) -> str:
    """
    Build the system and user prompt for the LLM.

    Assembles the health report text, URS summaries, and
    computed testing statistics into a structured prompt that
    instructs the LLM to produce a Validation Summary Report.

    :param health_report: Raw text of the health report.
    :param urs_summaries: Summarised URS data per file.
    :param stats: Testing statistics from compute_testing_stats.
    :return: The user prompt string.
    :requirement: URS-11.6 - System shall provide context to the
                  LLM for VSR generation.
    """
    # Combine URS summaries into a block
    urs_block_parts: List[str] = []
    for s in urs_summaries:
        urs_block_parts.append(
            f"File: {s['file']}\n"
            f"Project: {s['project']}\n"
            f"Total Requirements: {s['total']}\n"
            f"Requirements Table:\n{s['table']}"
        )
    urs_block = "\n\n".join(urs_block_parts)

    pass_fail = "PASS" if stats["traced_pct"] >= 100 else "FAIL"

    prompt = f"""\
You are a GxP regulatory compliance writer working for \
EVOLV by WingstarTech Inc.  Generate a **Validation Summary Report (VSR)** \
in Markdown from the data below.

The report MUST contain EXACTLY these sections in order:

## 1 - Executive Summary
A high-level pass/fail statement.  Based on the data the \
overall result is **{pass_fail}**.
Summarise the total requirements, traceability coverage, and \
the pass/fail verdict in two to three sentences.

## 2 - Scope
State which regulatory frameworks were checked.  The system \
uses **ISPE GAMP 5** for risk-based validation and \
**FDA Computer Software Assurance (CSA)** for testing \
strategy selection.  Mention both explicitly.

## 3 - Testing Summary
Report how many tests were generated and break them down:
- Scripted Tests (High/Medium Risk): {stats['scripted_test_count']}
- Unscripted Tests (Low Risk): {stats['unscripted_test_count']}
- Total Test Steps: {stats['total_test_steps']}
- Requirements with no test linkage: {stats['errors']}

Include a note explaining that High-Risk requirements \
received rigorous scripted testing per CSA, while Low-Risk \
requirements received objective-based unscripted testing \
that leverages tester expertise.

## 4 - Conclusion
State whether the system is considered **Fit for Intended \
Use** based on the traceability coverage \
({stats['traced_pct']:.0f}% traced).  If coverage is 100%, \
declare the system validated.  If not, note the gaps and \
recommend remediation.

## 5 - Footer
End the report with exactly this line:

> Signed by EVOLV Regulatory Engine

---

### Data Inputs

**Health Report:**
```
{health_report}
```

**URS Summaries:**
{urs_block}

**Statistics:**
- Total Requirements: {stats['total_requirements']}
- High-Risk: {stats['high_risk']}
- Medium-Risk: {stats['medium_risk']}
- Low-Risk: {stats['low_risk']}
- Scripted Test Steps: {stats['scripted_test_count']}
- Unscripted Test Steps: {stats['unscripted_test_count']}
- Traced: {stats['traced']}/{stats['total_requirements']} \
({stats['traced_pct']:.1f}%)

---

Rules:
- Output ONLY the Markdown report, no preamble or postamble.
- Start the document with a level-1 heading: \
"# Validation Summary Report (VSR)"
- Immediately below the heading write: \
"*Powered by EVOLV | A WingstarTech Inc. Product*"
- Use professional, audit-ready language.
- Do not invent data; use only the numbers provided.
- Keep the report concise (under 600 words).
"""

    return prompt


SYSTEM_PROMPT = (
    "You are a GxP regulatory compliance technical writer. "
    "You produce concise, audit-ready validation documents "
    "in Markdown.  You never fabricate data; you only use "
    "the numbers and context provided."
)


def call_llm(
    prompt: str,
    openai_api_key: Optional[str] = None,
    model: str = LLM_MODEL,
) -> str:
    """
    Call the OpenAI Chat Completions API to generate the VSR.

    :param prompt: The user prompt containing all VSR context.
    :param openai_api_key: OpenAI API key (defaults to env var).
    :param model: The model to use for generation.
    :return: The generated Markdown text.
    :raises VSRGenerationError: If the API call fails.
    :requirement: URS-11.7 - System shall use an LLM to draft
                  the Validation Summary Report.
    """
    if OpenAI is None:
        raise ImportError(
            "openai is required. "
            "Install with: pip install openai"
        )

    api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is required for VSR generation"
        )

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
    except Exception as e:
        raise VSRGenerationError(
            f"LLM API call failed: {e}"
        ) from e

    content = response.choices[0].message.content
    if not content:
        raise VSRGenerationError(
            "LLM returned an empty response."
        )

    return content.strip()


# ── Output ────────────────────────────────────────────────


def save_vsr_document(
    content: str,
    project_name: str,
    output_dir: Path = VSR_OUTPUT_DIR,
) -> Path:
    """
    Save the VSR Markdown document to disk.

    :param content: The generated Markdown content.
    :param project_name: Project name used in the filename.
    :param output_dir: Directory to write the file.
    :return: Path to the saved file.
    :requirement: URS-11.8 - System shall save the VSR to the
                  output directory.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(
        r"[^\w\s-]", "", project_name
    ).strip().replace(" ", "_")
    filename = f"VSR_{safe_name}_{timestamp}.md"

    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")

    return output_path


# ── Main Entry Point ──────────────────────────────────────


def draft_vsr(
    urs_dir: Path = URS_INPUT_DIR,
    output_dir: Path = VSR_OUTPUT_DIR,
    health_report_path: Path = HEALTH_REPORT_PATH,
    vtm_csv_path: Path = VTM_CSV_PATH,
    openai_api_key: Optional[str] = None,
    model: str = LLM_MODEL,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Generate a Validation Summary Report from existing outputs.

    Reads the Trustme Health Report, the VTM CSV, and URS
    Markdown files, then calls the LLM to produce a VSR.

    :param urs_dir: Directory containing URS Markdown files.
    :param output_dir: Directory to write the VSR output.
    :param health_report_path: Path to Trustme_Health_Report.txt.
    :param vtm_csv_path: Path to Trustme_Traceability_Matrix.csv.
    :param openai_api_key: OpenAI API key (defaults to env var).
    :param model: LLM model name for generation.
    :param verbose: Whether to print progress messages.
    :return: Dictionary with generation results.
    :requirement: URS-11.1 - System shall generate a Validation
                  Summary Report.
    """
    if verbose:
        print("\n" + "=" * 60)
        print(
            "EVOLV - Regulatory Compliance Engine"
        )
        print("Validation Summary Report Generator")
        print("=" * 60)

    # ── Step 1: Read Health Report ────────────────────────
    if verbose:
        print("\n[1/5] Reading Health Report...")

    health_report = read_health_report(health_report_path)

    if verbose:
        print("      [OK] Health report loaded.")

    # ── Step 2: Read VTM CSV ─────────────────────────────
    if verbose:
        print("[2/5] Reading Traceability Matrix...")

    vtm_rows = read_vtm_csv(vtm_csv_path)

    if verbose:
        print(
            f"      [OK] {len(vtm_rows)} VTM rows loaded."
        )

    # ── Step 3: Discover and read URS files ──────────────
    if verbose:
        print("[3/5] Discovering URS files...")

    urs_files = discover_urs_files(urs_dir)

    if not urs_files:
        msg = (
            f"No URS files found in {urs_dir}. "
            f"Run scripts/draft_urs.py first."
        )
        if verbose:
            print(f"      [ERROR] {msg}")
        return {"status": "error", "message": msg}

    urs_summaries = read_urs_summaries(urs_files)

    if verbose:
        print(
            f"      [OK] {len(urs_files)} URS file(s) loaded."
        )

    # ── Step 4: Compute stats and call LLM ───────────────
    if verbose:
        print("[4/5] Generating VSR via LLM...")

    stats = compute_testing_stats(vtm_rows)
    prompt = build_llm_prompt(
        health_report, urs_summaries, stats
    )

    vsr_content = call_llm(
        prompt,
        openai_api_key=openai_api_key,
        model=model,
    )

    if verbose:
        print("      [OK] VSR content generated.")

    # ── Step 5: Save ─────────────────────────────────────
    if verbose:
        print("[5/5] Saving VSR document...")

    # Derive project name from first URS summary
    project_name = urs_summaries[0]["project"]

    output_path = save_vsr_document(
        content=vsr_content,
        project_name=project_name,
        output_dir=output_dir,
    )

    if verbose:
        print(f"      [OK] Saved to {output_path}")
        print()
        print("=" * 60)
        print("VSR GENERATION COMPLETE")
        print("=" * 60)
        print(
            f"  Requirements:     "
            f"{stats['total_requirements']}"
        )
        print(
            f"  Scripted tests:   "
            f"{stats['scripted_test_count']}"
        )
        print(
            f"  Unscripted tests: "
            f"{stats['unscripted_test_count']}"
        )
        print(
            f"  Traced:           "
            f"{stats['traced_pct']:.0f}%"
        )
        print(f"  Output:           {output_path}")
        print()
        print("GxP Validated Output - Alpha version")
        print()

    return {
        "status": "success",
        "output_path": str(output_path),
        "total_requirements": stats["total_requirements"],
        "scripted_tests": stats["scripted_test_count"],
        "unscripted_tests": stats["unscripted_test_count"],
        "traced_pct": stats["traced_pct"],
    }


# ── CLI ───────────────────────────────────────────────────


def main() -> None:
    """
    CLI entry point for the VSR drafting script.

    :requirement: URS-11.1 - System shall generate a Validation
                  Summary Report.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate a Validation Summary Report (VSR) "
            "from Trustme Health Report and URS files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: uses output/ for all inputs and writes VSR
  python scripts/draft_vsr.py

  # Custom URS directory
  python scripts/draft_vsr.py -u path/to/urs_files

  # Custom output directory
  python scripts/draft_vsr.py -o path/to/output

  # Specify LLM model
  python scripts/draft_vsr.py --model gpt-4o-mini

  # Quiet mode
  python scripts/draft_vsr.py -q
        """,
    )

    parser.add_argument(
        "-u", "--urs-dir",
        type=Path,
        default=URS_INPUT_DIR,
        help=(
            "Directory containing URS Markdown files "
            f"(default: {URS_INPUT_DIR})"
        ),
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=VSR_OUTPUT_DIR,
        help=(
            "Directory to write the VSR "
            f"(default: {VSR_OUTPUT_DIR})"
        ),
    )

    parser.add_argument(
        "--health-report",
        type=Path,
        default=HEALTH_REPORT_PATH,
        help=(
            "Path to Trustme_Health_Report.txt "
            f"(default: {HEALTH_REPORT_PATH})"
        ),
    )

    parser.add_argument(
        "--vtm",
        type=Path,
        default=VTM_CSV_PATH,
        help=(
            "Path to Trustme_Traceability_Matrix.csv "
            f"(default: {VTM_CSV_PATH})"
        ),
    )

    parser.add_argument(
        "--model",
        type=str,
        default=LLM_MODEL,
        help=f"LLM model name (default: {LLM_MODEL})",
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output",
    )

    args = parser.parse_args()

    try:
        result = draft_vsr(
            urs_dir=args.urs_dir,
            output_dir=args.output_dir,
            health_report_path=args.health_report,
            vtm_csv_path=args.vtm,
            model=args.model,
            verbose=not args.quiet,
        )
    except (
        HealthReportNotFoundError,
        VTMNotFoundError,
    ) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except VSRGenerationError as e:
        print(f"Error: {e}")
        sys.exit(1)

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
