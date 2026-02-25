"""
URS Drafting Script for CSV-GameChanger.

Generates a complete User Requirements Specification (URS) document
from a project description using the RequirementArchitect agent.

:requirement: URS-7.1 - System shall generate URS documents from project input.
"""
import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Agents.requirement_architect import (
    RequirementArchitect,
    RegulatoryContextNotFoundError,
    EnterpriseTemplate,
    load_template
)


# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "urs"
DEFAULT_MIN_SCORE = 0.3  # Lower threshold for broader matches


def parse_requirements(project_description: str) -> List[str]:
    """
    Parse a project description into individual requirements.

    Supports multiple formats:
    - Line-separated requirements
    - Bullet points (-, *, •)
    - Numbered lists (1., 2., etc.)

    :param project_description: Raw project description text.
    :return: List of individual requirement strings.
    :requirement: URS-7.2 - System shall parse requirements from description.
    """
    lines = project_description.strip().split('\n')
    requirements = []

    for line in lines:
        # Clean the line
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Remove bullet points and numbering
        line = re.sub(r'^[-*•]\s*', '', line)
        line = re.sub(r'^\d+[.)]\s*', '', line)

        # Skip if line is too short (likely a header or noise)
        if len(line) < 10:
            continue

        requirements.append(line)

    return requirements


def generate_urs_table(
    requirements: List[Dict[str, Any]],
    project_name: str,
    failed_requirements: List[Dict[str, str]],
    template: Optional[EnterpriseTemplate] = None
) -> str:
    """
    Generate a Markdown URS document with table format.

    :param requirements: List of generated URS dictionaries.
    :param project_name: Name of the project.
    :param failed_requirements: List of requirements that failed to generate.
    :param template: Optional enterprise template for industry-specific
                    document formatting.
    :return: Formatted Markdown string.
    :requirement: URS-7.3 - System shall output URS as Markdown table.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Use template values or defaults
    doc_title = "User Requirements Specification (URS)"
    project_label = "Project"
    table_heading = "Requirements Table"
    header_line = "*Powered by EVOLV | A WingstarTech Inc. Product*"

    if template:
        doc_title = template.document_title
        project_label = template.header_project_label
        table_heading = template.sections.get(
            "table_heading", table_heading
        )
        header_line = f"*{template.footer}*"

    # Build the Markdown document
    md_lines = [
        f"# {doc_title}",
        f"",
        header_line,
        f"",
        f"**{project_label}:** {project_name}",
        f"**Generated:** {timestamp}",
        f"**Total Requirements:** {len(requirements)}",
        f"",
        f"---",
        f"",
        f"## {table_heading}",
        f"",
        f"| URS ID | Requirement Statement | Criticality | Regulatory Rationale |",
        f"|--------|----------------------|-------------|---------------------|",
    ]

    # Add each requirement row
    for req in requirements:
        # Escape pipe characters in text fields
        statement = req["Requirement_Statement"].replace("|", "\\|")
        rationale = req["Regulatory_Rationale"].replace("|", "\\|")

        # Truncate rationale for table readability
        if len(rationale) > 150:
            rationale = rationale[:147] + "..."

        md_lines.append(
            f"| {req['URS_ID']} | {statement} | {req['Criticality']} | {rationale} |"
        )

    # Add detailed requirements section
    detail_heading = "Detailed Requirements"
    if template:
        detail_heading = template.sections.get(
            "detail_heading", detail_heading
        )

    md_lines.extend([
        f"",
        f"---",
        f"",
        f"## {detail_heading}",
        f"",
    ])

    for req in requirements:
        md_lines.extend([
            f"### {req['URS_ID']}",
            f"",
            f"**Requirement Statement:**",
            f"> {req['Requirement_Statement']}",
            f"",
            f"**Criticality:** {req['Criticality']}",
            f"",
            f"**Regulatory Rationale:**",
            f"> {req['Regulatory_Rationale']}",
            f"",
            f"---",
            f"",
        ])

    # Add failed requirements section if any
    if failed_requirements:
        md_lines.extend([
            f"## Requirements Without Regulatory Context",
            f"",
            f"The following requirements could not be mapped to GAMP 5/CSA guidance.",
            f"Consider rephrasing or manually adding regulatory justification.",
            f"",
        ])

        for i, failed in enumerate(failed_requirements, 1):
            md_lines.extend([
                f"{i}. **Input:** {failed['input']}",
                f"   - **Reason:** {failed['reason']}",
                f"",
            ])

    # Collect all regulatory versions cited across requirements
    all_reg_versions: set = set()
    for req in requirements:
        for ver in req.get("Reg_Versions_Cited", []):
            if ver:
                all_reg_versions.add(ver)

    # Add regulatory version citation line
    if all_reg_versions:
        md_lines.extend([
            f"**Regulatory Versions Cited:** "
            f"{', '.join(sorted(all_reg_versions))}",
            f"",
        ])

    # Add footer
    footer_text = "Powered by EVOLV | A WingstarTech Inc. Product"
    if template:
        footer_text = template.footer

    md_lines.extend([
        f"---",
        f"",
        f"*{footer_text}*",
        f"*GxP Validated Output - Alpha version*",
    ])

    return "\n".join(md_lines)


def save_urs_document(
    content: str,
    project_name: str,
    output_dir: Path = OUTPUT_DIR
) -> Path:
    """
    Save the URS document to the output directory.

    :param content: Markdown content to save.
    :param project_name: Name of the project (used in filename).
    :param output_dir: Directory to save the file.
    :return: Path to the saved file.
    :requirement: URS-7.4 - System shall save URS to output/urs directory.
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[^\w\s-]', '', project_name).strip().replace(' ', '_')
    filename = f"URS_{safe_name}_{timestamp}.md"

    # Save file
    output_path = output_dir / filename
    output_path.write_text(content, encoding='utf-8')

    return output_path


def interactive_input() -> tuple[str, str]:
    """
    Collect project information interactively from the user.

    :return: Tuple of (project_name, project_description).
    :requirement: URS-7.5 - System shall accept interactive user input.
    """
    print("\n" + "=" * 60)
    print("Starting EVOLV Engine...")
    print("URS Drafting Tool")
    print("=" * 60)

    # Get project name
    print("\nEnter project name:")
    project_name = input("> ").strip()

    if not project_name:
        project_name = "Unnamed Project"

    # Get project description
    print("\nEnter project requirements (one per line).")
    print("Press Enter twice when done:")
    print("-" * 40)

    lines = []
    empty_count = 0

    while True:
        line = input()
        if line == "":
            empty_count += 1
            if empty_count >= 2:
                break
            lines.append("")
        else:
            empty_count = 0
            lines.append(line)

    project_description = "\n".join(lines).strip()

    return project_name, project_description


def draft_urs(
    project_name: str,
    project_description: str,
    min_score: float = DEFAULT_MIN_SCORE,
    output_dir: Path = OUTPUT_DIR,
    verbose: bool = True,
    template: Optional[EnterpriseTemplate] = None
) -> Dict[str, Any]:
    """
    Generate a complete URS document from a project description.

    :param project_name: Name of the project.
    :param project_description: Description containing requirements.
    :param min_score: Minimum similarity score for Pinecone matches.
    :param output_dir: Directory to save the output file.
    :param verbose: Whether to print progress messages.
    :param template: Optional enterprise template for industry-specific
                    formatting and criticality keywords.
    :return: Dictionary with generation results.
    :requirement: URS-7.1 - System shall generate URS documents from project input.
    """
    if verbose:
        print(f"\nProject: {project_name}")
        print("-" * 40)

    # Parse requirements from description
    requirement_inputs = parse_requirements(project_description)

    if not requirement_inputs:
        return {
            "status": "error",
            "message": "No valid requirements found in project description"
        }

    if verbose:
        print(f"Found {len(requirement_inputs)} requirements to process\n")

    # Initialize the RequirementArchitect
    try:
        architect = RequirementArchitect(template=template)
    except ImportError as e:
        return {
            "status": "error",
            "message": f"Missing dependency: {e}"
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": f"Configuration error: {e}"
        }

    # Generate URS for each requirement
    generated_requirements = []
    failed_requirements = []

    for i, req_input in enumerate(requirement_inputs, 1):
        if verbose:
            print(f"[{i}/{len(requirement_inputs)}] Processing: {req_input[:50]}...")

        try:
            urs = architect.generate_urs(req_input, min_score=min_score)
            generated_requirements.append(urs)

            if verbose:
                print(f"           [OK] Generated {urs['URS_ID']} "
                      f"(Criticality: {urs['Criticality']})")

        except RegulatoryContextNotFoundError as e:
            failed_requirements.append({
                "input": req_input,
                "reason": "No matching GAMP 5/CSA context found"
            })

            if verbose:
                print(f"           [FAIL] No regulatory context found")

        except Exception as e:
            failed_requirements.append({
                "input": req_input,
                "reason": str(e)
            })

            if verbose:
                print(f"           [FAIL] Error: {e}")

    if verbose:
        print()

    # Check if any requirements were generated
    if not generated_requirements:
        return {
            "status": "error",
            "message": "No requirements could be generated. "
                      "Ensure GAMP 5/CSA documents are ingested into Pinecone.",
            "failed_count": len(failed_requirements),
            "failed_requirements": failed_requirements
        }

    # Generate Markdown document
    md_content = generate_urs_table(
        requirements=generated_requirements,
        project_name=project_name,
        failed_requirements=failed_requirements,
        template=template
    )

    # Save the document
    output_path = save_urs_document(
        content=md_content,
        project_name=project_name,
        output_dir=output_dir
    )

    if verbose:
        print("=" * 60)
        print("URS GENERATION COMPLETE")
        print("=" * 60)
        print(f"  Generated: {len(generated_requirements)} requirements")
        print(f"  Failed:    {len(failed_requirements)} requirements")
        print(f"  Output:    {output_path}")
        print()
        print("GxP Validated Output - Alpha version")
        print()

    # Aggregate all regulatory versions cited
    all_reg_versions: set = set()
    for req in generated_requirements:
        for ver in req.get("Reg_Versions_Cited", []):
            if ver:
                all_reg_versions.add(ver)

    return {
        "status": "success",
        "output_path": str(output_path),
        "generated_count": len(generated_requirements),
        "failed_count": len(failed_requirements),
        "requirements": generated_requirements,
        "failed_requirements": failed_requirements,
        "reg_versions_cited": sorted(all_reg_versions)
    }


def main():
    """
    Main entry point for the URS drafting script.

    :requirement: URS-7.1 - System shall generate URS documents from project input.
    """
    parser = argparse.ArgumentParser(
        description="Generate URS documents from project descriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python scripts/draft_urs.py

  # From file
  python scripts/draft_urs.py -f requirements.txt -n "My Project"

  # Direct input
  python scripts/draft_urs.py -n "Warehouse System" -r "Track temperature" "Monitor humidity"
        """
    )

    parser.add_argument(
        "-n", "--name",
        type=str,
        help="Project name"
    )

    parser.add_argument(
        "-f", "--file",
        type=Path,
        help="File containing project requirements (one per line)"
    )

    parser.add_argument(
        "-r", "--requirements",
        nargs="+",
        type=str,
        help="Individual requirements as arguments"
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})"
    )

    parser.add_argument(
        "--min-score",
        type=float,
        default=DEFAULT_MIN_SCORE,
        help=f"Minimum similarity score for matches (default: {DEFAULT_MIN_SCORE})"
    )

    parser.add_argument(
        "-t", "--template",
        type=str,
        help="Enterprise template name (e.g., pharma_standard, "
             "medtech_standard, lab_systems)"
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    # Determine input mode
    if args.file:
        # Read from file
        if not args.file.exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(1)

        project_description = args.file.read_text(encoding='utf-8')
        project_name = args.name or args.file.stem

    elif args.requirements:
        # From command line arguments
        project_description = "\n".join(args.requirements)
        project_name = args.name or "CLI Project"

    else:
        # Interactive mode
        project_name, project_description = interactive_input()

    # Validate we have input
    if not project_description.strip():
        print("Error: No requirements provided")
        sys.exit(1)

    # Load enterprise template if specified
    enterprise_template = None
    if args.template:
        try:
            enterprise_template = load_template(args.template)
        except ValueError as e:
            print(f"Error loading template: {e}")
            sys.exit(1)

    # Generate the URS
    result = draft_urs(
        project_name=project_name,
        project_description=project_description,
        min_score=args.min_score,
        output_dir=args.output_dir,
        verbose=not args.quiet,
        template=enterprise_template
    )

    # Exit with appropriate code
    if result["status"] == "success":
        sys.exit(0)
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
