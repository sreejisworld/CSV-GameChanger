"""
EVOLV Sentinel — IAR Smoke Test
=================================
Demonstrates the Justification Engine with a hypothetical 'Data Export'
change scenario. Runs entirely in dry_run mode — no API key required.

Run from project root:
    python scripts/smoke_test_iar.py

Optionally pass --llm to call Claude (requires ANTHROPIC_API_KEY):
    python scripts/smoke_test_iar.py --llm

Output files saved to: output/sentinel/
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Agents.sentinel.impact_engine import ImpactEngine
from Agents.sentinel.justification_engine import JustificationEngine

# ---------------------------------------------------------------------------
# Self-contained traceability graph for the Data Export scenario.
# This is SEPARATE from the main sentinel graph; it models a hypothetical
# utils/data_exporter.py module added to the EVOLV system.
# ---------------------------------------------------------------------------

DATA_EXPORT_GRAPH = {
    "schema_version": "1.0.0",
    "graph_id": "TG-EXPORT-2026-001",
    "generated_at": "2026-02-26T12:00:00Z",
    "generated_by": "SentinelAgent/demo",
    "requirements": [
        {
            "req_id": "URS-20.1",
            "req_type": "URS",
            "title": "Export validated data to CSV for regulatory submission",
            "statement": (
                "The system shall export URS, UR/FR, and audit trail data to "
                "CSV format with a column schema that conforms to the FDA "
                "Electronic Submission requirements."
            ),
            "risk_level": "High",
            "criticality_score": 3,
            "gxp_category": "GxP Direct",
            "regulatory_reference": (
                "21 CFR Part 11.10(b) — System documentation; "
                "FDA Electronic Submissions Guidance 2023"
            ),
            "parent_req_id": None,
            "status": "Approved",
        },
        {
            "req_id": "URS-20.2",
            "req_type": "URS",
            "title": "Include regulatory version identifiers in all exported records",
            "statement": (
                "The system shall embed the regulatory version identifier "
                "(e.g., GAMP5_Rev2) in every exported row to enable "
                "post-export traceability."
            ),
            "risk_level": "High",
            "criticality_score": 3,
            "gxp_category": "GxP Direct",
            "regulatory_reference": (
                "GAMP 5 Rev 2, Section 6.3 — Traceability; "
                "21 CFR Part 11.10(e)"
            ),
            "parent_req_id": "URS-20.1",
            "status": "Approved",
        },
        {
            "req_id": "URS-20.3",
            "req_type": "URS",
            "title": "Preserve data integrity of exported records",
            "statement": (
                "The system shall include a SHA-256 audit hash in every "
                "exported row to allow post-export tamper detection in "
                "accordance with 21 CFR Part 11."
            ),
            "risk_level": "High",
            "criticality_score": 3,
            "gxp_category": "GxP Direct",
            "regulatory_reference": "21 CFR Part 11.10(e) and 11.70",
            "parent_req_id": "URS-20.1",
            "status": "Approved",
        },
        {
            "req_id": "URS-20.4",
            "req_type": "URS",
            "title": "Validate export column completeness before file write",
            "statement": (
                "The system shall validate that all required columns are "
                "present and non-null before writing the export file, "
                "raising a DataIntegrityError on any violation."
            ),
            "risk_level": "Medium",
            "criticality_score": 2,
            "gxp_category": "GxP Indirect",
            "regulatory_reference": (
                "GAMP 5 Rev 2, Section 6.4 — Data Integrity"
            ),
            "parent_req_id": "URS-20.1",
            "status": "Approved",
        },
    ],
    "code_modules": [
        {
            "module_id": "MOD-EXPORTER",
            "file_path": "utils/data_exporter.py",
            "module_name": "utils.data_exporter",
            "description": (
                "DataExporter utility — exports URS, UR/FR, and audit trail "
                "records to regulatory-compliant CSV files. Implements the "
                "FDA Electronic Submission column schema."
            ),
            "functions": [
                {
                    "function_name": "export_dataset_to_csv",
                    "class_name": "DataExporter",
                    "line_start": 45,
                    "line_end": 130,
                    "criticality_override": "High",
                },
                {
                    "function_name": "format_export_headers",
                    "class_name": "DataExporter",
                    "line_start": 131,
                    "line_end": 175,
                    "criticality_override": "High",
                },
                {
                    "function_name": "validate_export_schema",
                    "class_name": "DataExporter",
                    "line_start": 176,
                    "line_end": 220,
                    "criticality_override": None,
                },
            ],
        },
        {
            "module_id": "MOD-INTEGRITY-EXPORT",
            "file_path": "Agents/integrity_manager.py",
            "module_name": "Agents.integrity_manager",
            "description": (
                "Integrity Manager — append-only CSV audit trail with "
                "SHA-256 tamper-evident hashing. Provides audit hashes "
                "that the DataExporter embeds in export rows."
            ),
            "functions": [
                {
                    "function_name": "log_audit_event",
                    "class_name": None,
                    "line_start": 80,
                    "line_end": 145,
                    "criticality_override": "High",
                },
                {
                    "function_name": "_compute_reasoning_hash",
                    "class_name": None,
                    "line_start": 146,
                    "line_end": 175,
                    "criticality_override": "High",
                },
            ],
        },
        {
            "module_id": "MOD-PDF-EXPORT",
            "file_path": "utils/pdf_generator.py",
            "module_name": "utils.pdf_generator",
            "description": (
                "PDF Generator — produces branded URS and Validation Report "
                "PDFs with Manifestation of Signature pages. Also embeds "
                "regulatory version identifiers in PDF headers (URS-20.2)."
            ),
            "functions": [
                {
                    "function_name": "generate_urs_pdf",
                    "class_name": None,
                    "line_start": 40,
                    "line_end": 160,
                    "criticality_override": None,
                },
                {
                    "function_name": "generate_validation_report_pdf",
                    "class_name": None,
                    "line_start": 161,
                    "line_end": 310,
                    "criticality_override": None,
                },
            ],
        },
    ],
    "test_scripts": [
        {
            "script_id": "OQ-EXPORT-001",
            "phase": "OQ",
            "title": (
                "OQ: Data Export — CSV Column Schema and FDA Submission "
                "Format Verification"
            ),
            "execution_priority": "Critical",
            "test_type": "Formal OQ",
            "automation_status": "Semi-Automated",
            "owner": "CSV Validation Lead",
            "last_executed_at": "2026-01-20T09:00:00Z",
        },
        {
            "script_id": "OQ-EXPORT-002",
            "phase": "OQ",
            "title": (
                "OQ: Data Export — Regulatory Version Column Completeness "
                "and Traceability"
            ),
            "execution_priority": "Critical",
            "test_type": "Formal OQ",
            "automation_status": "Manual",
            "owner": "Regulatory Affairs",
            "last_executed_at": "2026-01-20T11:00:00Z",
        },
        {
            "script_id": "OQ-EXPORT-003",
            "phase": "OQ",
            "title": (
                "OQ: Data Export — SHA-256 Audit Hash Embedding and "
                "Tamper Detection"
            ),
            "execution_priority": "Critical",
            "test_type": "Formal OQ",
            "automation_status": "Automated",
            "owner": "Automation Engineer",
            "last_executed_at": "2026-01-20T13:00:00Z",
        },
        {
            "script_id": "OQ-EXPORT-004",
            "phase": "OQ",
            "title": (
                "OQ: Data Export — Schema Validation Pre-Write Guard "
                "(Null / Missing Column Detection)"
            ),
            "execution_priority": "High",
            "test_type": "Formal OQ",
            "automation_status": "Automated",
            "owner": "Automation Engineer",
            "last_executed_at": "2026-01-20T14:30:00Z",
        },
        {
            "script_id": "UAT-EXPORT-001",
            "phase": "UAT",
            "title": (
                "UAT: End-to-End Data Export — URS to Regulatory CSV "
                "Submission Workflow"
            ),
            "execution_priority": "High",
            "test_type": "Formal UAT",
            "automation_status": "Manual",
            "owner": "Business Analyst / CSV Lead",
            "last_executed_at": "2026-02-01T09:00:00Z",
        },
        {
            "script_id": "OQ-AUDIT-001",
            "phase": "OQ",
            "title": (
                "OQ: Integrity Manager — Audit Trail Append-Only and "
                "SHA-256 Hash Integrity"
            ),
            "execution_priority": "Critical",
            "test_type": "Formal OQ",
            "automation_status": "Automated",
            "owner": "Automation Engineer",
            "last_executed_at": "2026-01-18T13:00:00Z",
        },
    ],
    "traceability_links": [
        {
            "link_id": "LINK-URS20.1-EXPORTER-001",
            "req_id": "URS-20.1",
            "module_id": "MOD-EXPORTER",
            "function_names": ["export_dataset_to_csv", "format_export_headers"],
            "test_script_ids": ["OQ-EXPORT-001", "UAT-EXPORT-001"],
            "change_impact_type": "Direct",
            "rationale": (
                "export_dataset_to_csv() is the primary URS-20.1 implementation "
                "— it builds and writes the regulatory CSV file. "
                "format_export_headers() defines the FDA submission column order."
            ),
            "created_at": "2026-01-05T09:00:00Z",
            "verified_by": "csv_lead_001",
        },
        {
            "link_id": "LINK-URS20.2-EXPORTER-002",
            "req_id": "URS-20.2",
            "module_id": "MOD-EXPORTER",
            "function_names": ["format_export_headers"],
            "test_script_ids": ["OQ-EXPORT-002", "UAT-EXPORT-001"],
            "change_impact_type": "Direct",
            "rationale": (
                "format_export_headers() defines the column containing the "
                "regulatory version identifier. Changing column ordering or "
                "naming directly affects URS-20.2 compliance."
            ),
            "created_at": "2026-01-05T09:05:00Z",
            "verified_by": "csv_lead_001",
        },
        {
            "link_id": "LINK-URS20.3-EXPORTER-003",
            "req_id": "URS-20.3",
            "module_id": "MOD-EXPORTER",
            "function_names": ["export_dataset_to_csv"],
            "test_script_ids": ["OQ-EXPORT-003"],
            "change_impact_type": "Direct",
            "rationale": (
                "export_dataset_to_csv() embeds the audit_hash column in "
                "every exported row. Any column reordering or renaming risks "
                "misaligning the hash with its data record."
            ),
            "created_at": "2026-01-05T09:10:00Z",
            "verified_by": "csv_lead_001",
        },
        {
            "link_id": "LINK-URS20.4-EXPORTER-004",
            "req_id": "URS-20.4",
            "module_id": "MOD-EXPORTER",
            "function_names": ["validate_export_schema"],
            "test_script_ids": ["OQ-EXPORT-004"],
            "change_impact_type": "Direct",
            "rationale": (
                "validate_export_schema() implements the pre-write guard for "
                "URS-20.4. Because the header list changed, the validation "
                "schema must be re-tested against the new column set."
            ),
            "created_at": "2026-01-05T09:15:00Z",
            "verified_by": "csv_lead_001",
        },
        {
            "link_id": "LINK-URS20.3-INTEGRITY-INDIRECT",
            "req_id": "URS-20.3",
            "module_id": "MOD-INTEGRITY-EXPORT",
            "function_names": ["_compute_reasoning_hash"],
            "test_script_ids": ["OQ-AUDIT-001"],
            "change_impact_type": "Indirect",
            "rationale": (
                "The Integrity Manager produces the SHA-256 hashes that "
                "DataExporter embeds. While the hash computation itself was "
                "not changed, the audit trail linkage to exported rows is "
                "indirectly affected by changes in export column ordering."
            ),
            "created_at": "2026-01-05T09:20:00Z",
            "verified_by": "csv_lead_001",
        },
        {
            "link_id": "LINK-URS20.2-PDF-INDIRECT",
            "req_id": "URS-20.2",
            "module_id": "MOD-PDF-EXPORT",
            "function_names": ["generate_urs_pdf"],
            "test_script_ids": [],
            "change_impact_type": "Indirect",
            "rationale": (
                "PDF generator also embeds regulatory version identifiers in "
                "PDF headers, sharing URS-20.2. The PDF code path is entirely "
                "separate from the CSV export path."
            ),
            "created_at": "2026-01-05T09:25:00Z",
            "verified_by": "csv_lead_001",
        },
    ],
}

# ---------------------------------------------------------------------------
# Hypothetical git diff: Data Export function change
#
# Scenario: A developer modified DataExporter.export_dataset_to_csv() and
# format_export_headers() to:
#   1. Add a new "audit_hash" column to every export row (URS-20.3 compliance)
#   2. Reorder columns to match the 2026 FDA Electronic Submission template
#   3. Add format_export_headers() to enforce the new column order
# ---------------------------------------------------------------------------

DATA_EXPORT_DIFF = """\
diff --git a/utils/data_exporter.py b/utils/data_exporter.py
index 3a1b2c3..d4e5f6a 100644
--- a/utils/data_exporter.py
+++ b/utils/data_exporter.py
@@ -45,30 +45,45 @@ def export_dataset_to_csv(self, records: list, output_path: str) -> Path:
-        COLUMN_ORDER = [
-            "urs_id", "requirement_statement", "criticality",
-            "regulatory_rationale", "reg_version",
-        ]
+        COLUMN_ORDER = self.format_export_headers()
         rows = []
         for rec in records:
-            rows.append({col: rec.get(col, "") for col in COLUMN_ORDER})
+            audit_hash = self._get_audit_hash(rec.get("urs_id", ""))
+            row = {col: rec.get(col, "") for col in COLUMN_ORDER}
+            row["audit_hash"] = audit_hash
+            row["export_timestamp"] = datetime.utcnow().isoformat()
+            rows.append(row)
         df = pd.DataFrame(rows, columns=COLUMN_ORDER)
-        df.to_csv(output_path, index=False, encoding="utf-8")
+        self.validate_export_schema(df, COLUMN_ORDER)
+        df.to_csv(output_path, index=False, encoding="utf-8-sig")
         return Path(output_path)
@@ -131,8 +146,22 @@ def format_export_headers(self) -> list:
-    def format_export_headers(self) -> list:
-        return [
-            "urs_id", "requirement_statement", "criticality",
-            "regulatory_rationale", "reg_version",
-        ]
+    def format_export_headers(self) -> list:
+        \"\"\"
+        Returns column order per 2026 FDA Electronic Submission Template.
+        Columns must match Appendix B of the FDA guidance document exactly.
+        \"\"\"
+        return [
+            "urs_id",
+            "requirement_statement",
+            "criticality",
+            "reg_version",
+            "regulatory_rationale",
+            "audit_hash",
+            "export_timestamp",
+        ]
"""

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    use_llm = "--llm" in sys.argv

    output_dir = Path("output/sentinel")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("  EVOLV SENTINEL — IAR Smoke Test: Data Export Scenario")
    print(f"  Mode: {'LLM (Claude)' if use_llm else 'DRY-RUN (template)'}")
    print("=" * 72)

    # -----------------------------------------------------------------------
    # Step 1: Run the Impact Engine on the Data Export diff
    # -----------------------------------------------------------------------
    print("\n[1/3] Running Impact Engine...")
    impact_engine = ImpactEngine(DATA_EXPORT_GRAPH)
    impact_report = impact_engine.analyze(DATA_EXPORT_DIFF)
    impact_engine.print_report(impact_report)

    assert impact_report.summary["at_risk_requirements"] > 0, (
        "Expected at least one at-risk requirement"
    )
    print(f"  [OK] Impact Engine: {impact_report.summary['at_risk_requirements']} "
          f"at-risk requirements identified.\n")

    # -----------------------------------------------------------------------
    # Step 2: Run the Justification Engine
    # -----------------------------------------------------------------------
    print("[2/3] Running Justification Engine...")
    j_engine = JustificationEngine(DATA_EXPORT_GRAPH)
    iar = j_engine.generate_iar(
        impact_report=impact_report,
        diff_text=DATA_EXPORT_DIFF,
        author="Dr. Priya Nair, CSV Lead — WingstarTech Inc.",
        project_name="EVOLV Validation Factory v2.1 — Data Export Module",
        dry_run=(not use_llm),
    )
    print(f"  [OK] IAR generated: {iar.iar_id}")
    print(f"       Mode         : {iar.generation_mode.upper()}")
    print(f"       In-scope tests: {len(iar.in_scope_tests)}")
    print(f"       Excluded mods : {len(iar.excluded_modules)}")

    # -----------------------------------------------------------------------
    # Step 3: Render and save
    # -----------------------------------------------------------------------
    print("\n[3/3] Rendering IAR...")
    md = j_engine.render_to_markdown(iar)

    md_path = output_dir / f"{iar.iar_id}.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"  [OK] Markdown saved: {md_path}")

    json_path = output_dir / f"{iar.iar_id}.json"
    json_path.write_text(
        json.dumps(j_engine.to_dict(iar), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  [OK] JSON saved   : {json_path}")

    # Print the rendered Markdown to stdout
    print("\n" + "=" * 72)
    print("  IMPACT ASSESSMENT REPORT — RENDERED OUTPUT")
    print("=" * 72 + "\n")
    print(md)

    print("\n" + "=" * 72)
    print("  Smoke test PASSED.")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
