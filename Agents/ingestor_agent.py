"""
Ingestor Agent Module.

Reads vendor .docx and .pdf documents from input/vendor_docs/ and converts
them into structured JSON that the RequirementArchitect can consume.
Also performs GAMP 5 gap analysis against the Pinecone knowledge base.

:requirement: URS-8.1 - System shall ingest vendor documents for processing.
:requirement: URS-9.1 - System shall perform GAMP 5 gap analysis.
"""
import os
import re
import json
import logging
from pathlib import Path
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from Agents.integrity_manager import (
    log_audit_event as _log_integrity_event,
)

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


# Configuration
VENDOR_DOCS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "input",
    "vendor_docs"
)
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output"
)
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

# GAMP 5 expected lifecycle document categories for gap analysis.
# Each entry maps a category name to its Pinecone search query and
# a set of indicator keywords used to check vendor document coverage.
GAMP5_CATEGORIES: List[Dict[str, Any]] = [
    {
        "category": "Intended Use",
        "query": "intended use statement system purpose",
        "keywords": [
            "intended use", "purpose", "scope of use",
            "system purpose", "intended application"
        ]
    },
    {
        "category": "User Requirements (URS)",
        "query": "user requirements specification functional",
        "keywords": [
            "user requirement", "urs", "functional requirement",
            "user need", "business requirement"
        ]
    },
    {
        "category": "Functional Specifications",
        "query": "functional specification design",
        "keywords": [
            "functional specification", "functional spec",
            "system function", "feature", "capability"
        ]
    },
    {
        "category": "Risk Assessment",
        "query": "risk assessment patient safety FMEA",
        "keywords": [
            "risk assessment", "risk analysis", "fmea",
            "hazard", "risk matrix", "patient safety",
            "risk priority"
        ]
    },
    {
        "category": "Design Specification",
        "query": "design specification architecture",
        "keywords": [
            "design specification", "design spec",
            "architecture", "system design", "technical design"
        ]
    },
    {
        "category": "Traceability",
        "query": "traceability matrix requirements testing",
        "keywords": [
            "traceability", "trace matrix",
            "requirements traceability", "rtm"
        ]
    },
    {
        "category": "Testing Strategy",
        "query": "testing strategy IQ OQ PQ validation",
        "keywords": [
            "testing strategy", "test plan", "iq", "oq", "pq",
            "validation protocol", "test case", "test script"
        ]
    },
    {
        "category": "Change Control",
        "query": "change control management procedure",
        "keywords": [
            "change control", "change management",
            "change request", "change procedure"
        ]
    },
    {
        "category": "Data Integrity",
        "query": "data integrity ALCOA electronic records",
        "keywords": [
            "data integrity", "alcoa", "electronic record",
            "audit trail", "21 cfr part 11", "data governance"
        ]
    },
    {
        "category": "Supplier Assessment",
        "query": "supplier assessment vendor audit qualification",
        "keywords": [
            "supplier assessment", "vendor audit",
            "supplier qualification", "vendor qualification",
            "supplier evaluation"
        ]
    },
    {
        "category": "Validation Plan",
        "query": "validation plan approach lifecycle",
        "keywords": [
            "validation plan", "validation approach",
            "validation strategy", "lifecycle",
            "validation lifecycle"
        ]
    },
    {
        "category": "Standard Operating Procedures",
        "query": "SOP standard operating procedure training",
        "keywords": [
            "sop", "standard operating procedure",
            "procedure", "work instruction", "training"
        ]
    },
]

# Audit logger
audit_logger = logging.getLogger("csv_engine.audit")


EVIDENCE_EXCERPT_LENGTH = 200


class IngestorError(Exception):
    """
    Base exception for Ingestor Agent errors.

    Error code: CSV-005 - Document ingestion failed.

    :requirement: URS-8.2 - System shall report ingestion errors.
    """

    error_code = "CSV-005"


class UnsupportedFileTypeError(IngestorError):
    """
    Raised when a file type is not supported for ingestion.

    Error code: CSV-006 - Unsupported file type.

    :requirement: URS-8.2 - System shall report ingestion errors.
    """

    error_code = "CSV-006"

    def __init__(self, file_path: str):
        ext = Path(file_path).suffix
        super().__init__(
            f"Unsupported file type '{ext}' for '{file_path}'. "
            f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        )


class DocumentParseError(IngestorError):
    """
    Raised when a document cannot be parsed.

    Error code: CSV-007 - Document parsing failed.

    :requirement: URS-8.2 - System shall report ingestion errors.
    """

    error_code = "CSV-007"

    def __init__(self, file_path: str, reason: str):
        super().__init__(
            f"Failed to parse '{file_path}': {reason}"
        )


@dataclass
class DocumentSection:
    """
    A section extracted from a vendor document.

    :requirement: URS-8.3 - System shall extract structured sections.
    """

    heading: str
    content: str
    page_number: int
    section_index: int

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert section to dictionary.

        :return: Dictionary representation of the section.
        :requirement: URS-8.4 - System shall output JSON format.
        """
        return {
            "heading": self.heading,
            "content": self.content,
            "page_number": self.page_number,
            "section_index": self.section_index
        }


@dataclass
class IngestedDocument:
    """
    Structured representation of an ingested vendor document.

    This format is designed to be consumed by the RequirementArchitect
    for URS generation via its generate_urs() method.

    :requirement: URS-8.3 - System shall extract structured sections.
    """

    file_name: str
    file_type: str
    title: str
    ingested_at: str
    total_pages: int
    sections: List[DocumentSection] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ingested document to dictionary.

        :return: Dictionary representation of the document.
        :requirement: URS-8.4 - System shall output JSON format.
        """
        return {
            "file_name": self.file_name,
            "file_type": self.file_type,
            "title": self.title,
            "ingested_at": self.ingested_at,
            "total_pages": self.total_pages,
            "sections": [s.to_dict() for s in self.sections],
            "requirements": self.requirements
        }

    def to_json(self) -> str:
        """
        Convert ingested document to JSON string.

        :return: JSON string representation.
        :requirement: URS-8.4 - System shall output JSON format.
        """
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class GapFinding:
    """
    A single finding from GAMP 5 gap analysis.

    :requirement: URS-9.2 - System shall identify gaps per category.
    """

    category: str
    status: str
    vendor_evidence: str
    gamp5_reference: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert finding to dictionary.

        :return: Dictionary representation of the finding.
        :requirement: URS-9.3 - System shall output gap analysis as JSON.
        """
        return {
            "category": self.category,
            "status": self.status,
            "vendor_evidence": self.vendor_evidence,
            "gamp5_reference": self.gamp5_reference,
            "recommendation": self.recommendation
        }


@dataclass
class GapAnalysisReport:
    """
    Complete GAMP 5 gap analysis report for a vendor document.

    :requirement: URS-9.1 - System shall perform GAMP 5 gap analysis.
    """

    file_name: str
    title: str
    analyzed_at: str
    total_categories: int
    covered: int
    gaps: int
    findings: List[GapFinding] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report to dictionary.

        :return: Dictionary representation of the report.
        :requirement: URS-9.3 - System shall output gap analysis as JSON.
        """
        return {
            "file_name": self.file_name,
            "title": self.title,
            "analyzed_at": self.analyzed_at,
            "total_categories": self.total_categories,
            "covered": self.covered,
            "gaps": self.gaps,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings]
        }

    def to_json(self) -> str:
        """
        Convert report to JSON string.

        :return: JSON string representation.
        :requirement: URS-9.3 - System shall output gap analysis as JSON.
        """
        return json.dumps(self.to_dict(), indent=2)

    def save(self, output_dir: str = OUTPUT_DIR) -> Path:
        """
        Save report to output/gap_analysis_report.json.

        :param output_dir: Directory to write the report file.
        :return: Path to the saved file.
        :requirement: URS-9.4 - System shall save gap analysis report.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / "gap_analysis_report.json"
        file_path.write_text(self.to_json(), encoding="utf-8")
        return file_path


class IngestorAgent:
    """
    Reads vendor .docx and .pdf files and converts them to structured
    JSON for downstream consumption by the RequirementArchitect.

    :requirement: URS-8.1 - System shall ingest vendor documents.
    """

    def __init__(
        self,
        vendor_docs_dir: str = VENDOR_DOCS_DIR
    ):
        """
        Initialize the IngestorAgent.

        :param vendor_docs_dir: Path to the vendor documents directory.
        :requirement: URS-8.1 - System shall ingest vendor documents.
        """
        self._vendor_docs_dir = vendor_docs_dir
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """
        Validate that required packages are installed.

        :raises ImportError: If python-docx or PyPDF2 is missing.
        :requirement: URS-8.5 - System shall validate dependencies.
        """
        if DocxDocument is None:
            raise ImportError(
                "python-docx is required. "
                "Install with: pip install python-docx"
            )
        if PdfReader is None:
            raise ImportError(
                "PyPDF2 is required. "
                "Install with: pip install PyPDF2"
            )

    def _log_audit_event(
        self,
        action: str,
        details: Dict[str, Any]
    ) -> None:
        """
        Log an audit event for document ingestion.

        :param action: The audit action name.
        :param details: Additional details for the audit record.
        :requirement: URS-2.1 - System shall maintain audit trail.
        """
        audit_logger.info(
            action,
            extra={
                "user_id": "SYSTEM",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "details": details
            }
        )

    def _extract_requirements_from_text(
        self,
        text: str
    ) -> List[str]:
        """
        Extract requirement-like statements from document text.

        Looks for sentences containing keywords such as "shall",
        "must", "require", or numbered/bulleted list items that
        indicate formal requirements.

        :param text: Raw text to scan for requirements.
        :return: List of extracted requirement strings.
        :requirement: URS-8.6 - System shall extract requirements.
        """
        requirements: List[str] = []
        seen: set = set()

        # Pattern: sentences with "shall", "must", "required"
        shall_pattern = re.compile(
            r'[^.]*\b(?:shall|must|is required to|'
            r'should|needs? to)\b[^.]*\.',
            re.IGNORECASE
        )
        for match in shall_pattern.finditer(text):
            req = match.group(0).strip()
            req_normalized = req.lower()
            if req_normalized not in seen and len(req) > 20:
                seen.add(req_normalized)
                requirements.append(req)

        # Pattern: numbered items (e.g. "1.", "1.1", "a)")
        numbered_pattern = re.compile(
            r'(?:^|\n)\s*(?:\d+[\.\)]\s*\d*[\.\)]?\s*|'
            r'[a-z][\.\)]\s*)(.{20,}?)(?:\n|$)',
            re.IGNORECASE
        )
        for match in numbered_pattern.finditer(text):
            req = match.group(1).strip().rstrip('.')
            req_normalized = req.lower()
            if req_normalized not in seen and len(req) > 20:
                seen.add(req_normalized)
                requirements.append(req)

        return requirements

    def _parse_pdf(self, file_path: str) -> IngestedDocument:
        """
        Parse a PDF file into an IngestedDocument.

        :param file_path: Absolute path to the PDF file.
        :return: Structured IngestedDocument.
        :raises DocumentParseError: If the PDF cannot be read.
        :requirement: URS-8.7 - System shall parse PDF documents.
        """
        try:
            reader = PdfReader(file_path)
        except Exception as e:
            raise DocumentParseError(file_path, str(e))

        total_pages = len(reader.pages)
        all_text_parts: List[str] = []
        sections: List[DocumentSection] = []

        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            all_text_parts.append(page_text)

            if page_text.strip():
                sections.append(DocumentSection(
                    heading=f"Page {page_idx + 1}",
                    content=page_text.strip(),
                    page_number=page_idx + 1,
                    section_index=page_idx
                ))

        full_text = "\n".join(all_text_parts)
        requirements = self._extract_requirements_from_text(full_text)

        # Derive title from filename
        title = Path(file_path).stem.replace("_", " ").replace("-", " ")

        return IngestedDocument(
            file_name=Path(file_path).name,
            file_type="pdf",
            title=title,
            ingested_at=datetime.now(timezone.utc).isoformat(),
            total_pages=total_pages,
            sections=sections,
            requirements=requirements
        )

    def _parse_docx(self, file_path: str) -> IngestedDocument:
        """
        Parse a .docx file into an IngestedDocument.

        Extracts headings and their associated content as sections,
        and scans for requirement-like statements.

        :param file_path: Absolute path to the .docx file.
        :return: Structured IngestedDocument.
        :raises DocumentParseError: If the file cannot be read.
        :requirement: URS-8.8 - System shall parse DOCX documents.
        """
        try:
            doc = DocxDocument(file_path)
        except Exception as e:
            raise DocumentParseError(file_path, str(e))

        sections: List[DocumentSection] = []
        current_heading: str = "Introduction"
        current_content: List[str] = []
        section_index: int = 0

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue

            # Detect headings by style name
            style_name = (paragraph.style.name or "").lower()
            is_heading = "heading" in style_name

            if is_heading:
                # Save previous section
                if current_content:
                    sections.append(DocumentSection(
                        heading=current_heading,
                        content="\n".join(current_content),
                        page_number=1,
                        section_index=section_index
                    ))
                    section_index += 1
                    current_content = []
                current_heading = text
            else:
                current_content.append(text)

        # Save final section
        if current_content:
            sections.append(DocumentSection(
                heading=current_heading,
                content="\n".join(current_content),
                page_number=1,
                section_index=section_index
            ))

        # Extract requirements from all content
        full_text = "\n".join(
            s.content for s in sections
        )
        requirements = self._extract_requirements_from_text(full_text)

        # Try to get title from core properties
        title = Path(file_path).stem.replace("_", " ").replace("-", " ")
        try:
            if doc.core_properties.title:
                title = doc.core_properties.title
        except Exception:
            pass

        return IngestedDocument(
            file_name=Path(file_path).name,
            file_type="docx",
            title=title,
            ingested_at=datetime.now(timezone.utc).isoformat(),
            total_pages=len(sections),
            sections=sections,
            requirements=requirements
        )

    def ingest_file(self, file_path: str) -> IngestedDocument:
        """
        Ingest a single vendor document and return structured JSON.

        :param file_path: Path to the .docx or .pdf file. Can be
                         relative (resolved against vendor_docs_dir)
                         or absolute.
        :return: IngestedDocument with sections and requirements.
        :raises UnsupportedFileTypeError: If the file type is not
                                          .docx or .pdf.
        :raises DocumentParseError: If the file cannot be parsed.
        :requirement: URS-8.1 - System shall ingest vendor documents.
        """
        # Resolve relative paths against vendor_docs_dir
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(self._vendor_docs_dir) / path
        file_path = str(path)

        if not path.exists():
            raise DocumentParseError(
                file_path, "File does not exist"
            )

        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(file_path)

        self._log_audit_event(
            "DOCUMENT_INGESTION_STARTED",
            {"file": file_path, "type": ext}
        )

        if ext == ".pdf":
            result = self._parse_pdf(file_path)
        else:
            result = self._parse_docx(file_path)

        self._log_audit_event(
            "DOCUMENT_INGESTION_COMPLETED",
            {
                "file": file_path,
                "sections": len(result.sections),
                "requirements_found": len(result.requirements)
            }
        )

        decision_logic = (
            f"Parsed {result.file_name} "
            f"({ext.lstrip('.').upper()}, "
            f"{result.total_pages} pages); "
            f"extracted {len(result.sections)} sections and "
            f"{len(result.requirements)} requirement-like "
            f"statements using keyword pattern matching"
        )

        _log_integrity_event(
            agent_name="IngestorAgent",
            action="DOCUMENT_INGESTED",
            decision_logic=decision_logic,
        )

        return result

    def ingest_all(self) -> List[IngestedDocument]:
        """
        Ingest all supported documents from the vendor_docs directory.

        :return: List of IngestedDocument objects.
        :raises FileNotFoundError: If the vendor_docs directory
                                   does not exist.
        :requirement: URS-8.9 - System shall batch-ingest documents.
        """
        docs_dir = Path(self._vendor_docs_dir)
        if not docs_dir.exists():
            raise FileNotFoundError(
                f"Vendor docs directory not found: {self._vendor_docs_dir}"
            )

        results: List[IngestedDocument] = []

        for file_path in sorted(docs_dir.iterdir()):
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    doc = self.ingest_file(str(file_path))
                    results.append(doc)
                except IngestorError as e:
                    audit_logger.warning(
                        "DOCUMENT_INGESTION_FAILED",
                        extra={
                            "user_id": "SYSTEM",
                            "timestamp": datetime.now(
                                timezone.utc
                            ).isoformat(),
                            "action": "DOCUMENT_INGESTION_FAILED",
                            "details": {
                                "file": str(file_path),
                                "error": str(e)
                            }
                        }
                    )
                    _log_integrity_event(
                        agent_name="IngestorAgent",
                        action="DOCUMENT_INGESTION_FAILED",
                        decision_logic=(
                            f"Failed to ingest "
                            f"{file_path.name}: {e}"
                        ),
                    )

        succeeded = len(results)
        failed = sum(
            1 for fp in sorted(docs_dir.iterdir())
            if fp.suffix.lower() in SUPPORTED_EXTENSIONS
        ) - succeeded

        decision_logic = (
            f"Batch-ingested documents from "
            f"{self._vendor_docs_dir}; "
            f"{succeeded} succeeded, {failed} failed"
        )

        _log_integrity_event(
            agent_name="IngestorAgent",
            action="BATCH_INGESTION_COMPLETED",
            decision_logic=decision_logic,
        )

        return results

    def get_requirements_for_architect(
        self,
        file_path: str
    ) -> List[str]:
        """
        Ingest a document and return its requirements as a list of
        strings ready for RequirementArchitect.generate_urs().

        :param file_path: Path to the vendor document.
        :return: List of requirement strings.
        :requirement: URS-8.10 - System shall feed RequirementArchitect.

        Example:
            >>> from Agents.ingestor_agent import IngestorAgent
            >>> from Agents.requirement_architect import (
            ...     RequirementArchitect
            ... )
            >>> ingestor = IngestorAgent()
            >>> reqs = ingestor.get_requirements_for_architect(
            ...     "vendor_spec.docx"
            ... )
            >>> architect = RequirementArchitect()
            >>> for req in reqs:
            ...     urs = architect.generate_urs(req)
            ...     print(urs)
        """
        doc = self.ingest_file(file_path)
        return doc.requirements

    def _find_keyword_evidence(
        self,
        text: str,
        keywords: List[str]
    ) -> str:
        """
        Search text for keywords and return an excerpt as evidence.

        :param text: Full document text to search.
        :param keywords: List of indicator keywords for a category.
        :return: ~200-char excerpt around the first match, or empty.
        :requirement: URS-9.5 - System shall extract vendor evidence.
        """
        text_lower = text.lower()
        for keyword in keywords:
            pos = text_lower.find(keyword)
            if pos != -1:
                start = max(0, pos - 40)
                end = min(
                    len(text),
                    pos + len(keyword) + EVIDENCE_EXCERPT_LENGTH
                )
                excerpt = text[start:end].strip()
                # Trim to sentence boundaries where possible
                if start > 0:
                    excerpt = "..." + excerpt
                if end < len(text):
                    excerpt = excerpt + "..."
                return excerpt
        return ""

    def analyze_gaps(
        self,
        file_path: str,
        pinecone_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ) -> GapAnalysisReport:
        """
        Perform GAMP 5 gap analysis on a vendor document.

        Ingests the document, then checks its content against each
        GAMP 5 lifecycle category. For each category, queries Pinecone
        for the authoritative GAMP 5 reference and checks the vendor
        document for matching keywords. Produces a structured report
        identifying covered areas and gaps.

        :param file_path: Path to the vendor .docx or .pdf file.
        :param pinecone_api_key: Pinecone API key (defaults to env).
        :param openai_api_key: OpenAI API key (defaults to env).
        :return: GapAnalysisReport with findings and summary.
        :raises IngestorError: If the document cannot be ingested.
        :raises ImportError: If pinecone/openai packages are missing.
        :requirement: URS-9.1 - System shall perform GAMP 5 gap analysis.

        Example:
            >>> from Agents.ingestor_agent import IngestorAgent
            >>> agent = IngestorAgent()
            >>> report = agent.analyze_gaps("vendor_spec.docx")
            >>> print(report.to_json())
        """
        from Agents.requirement_architect import RequirementArchitect

        self._log_audit_event(
            "GAP_ANALYSIS_STARTED",
            {"file": file_path}
        )

        # Step 1: Ingest the vendor document
        doc = self.ingest_file(file_path)
        full_text = "\n".join(
            section.content for section in doc.sections
        )

        # Step 2: Initialize RequirementArchitect for Pinecone queries
        architect = RequirementArchitect(
            pinecone_api_key=pinecone_api_key,
            openai_api_key=openai_api_key
        )

        # Step 3: Analyze each GAMP 5 category
        findings: List[GapFinding] = []
        covered_names: List[str] = []
        gap_names: List[str] = []

        for cat in GAMP5_CATEGORIES:
            category_name: str = cat["category"]
            search_query: str = cat["query"]
            keywords: List[str] = cat["keywords"]

            # Query Pinecone for GAMP 5 reference text
            gamp5_ref = ""
            try:
                search_resp = architect.search(
                    query=search_query,
                    top_k=1,
                    min_score=0.3
                )
                if search_resp.results:
                    r = search_resp.results[0]
                    src = r.source_document or "GAMP 5"
                    pg = r.page_number or 0
                    txt = (r.text or "")[:200]
                    ver = r.reg_version or ""
                    if ver:
                        gamp5_ref = (
                            f"Per {src} [{ver}] "
                            f"(p.{pg}): {txt}..."
                        )
                    else:
                        gamp5_ref = (
                            f"Per {src} "
                            f"(p.{pg}): {txt}..."
                        )
            except Exception:
                gamp5_ref = "GAMP 5 reference unavailable"

            # Check vendor document for keyword coverage
            evidence = self._find_keyword_evidence(
                full_text, keywords
            )

            if evidence:
                findings.append(GapFinding(
                    category=category_name,
                    status="covered",
                    vendor_evidence=evidence,
                    gamp5_reference=gamp5_ref,
                    recommendation=""
                ))
                covered_names.append(category_name)
            else:
                findings.append(GapFinding(
                    category=category_name,
                    status="gap",
                    vendor_evidence="",
                    gamp5_reference=gamp5_ref,
                    recommendation=(
                        f"Vendor should provide documentation "
                        f"addressing {category_name.lower()}."
                    )
                ))
                gap_names.append(category_name)

        # Step 4: Build summary
        total = len(GAMP5_CATEGORIES)
        covered_count = len(covered_names)
        gap_count = len(gap_names)

        if covered_names and gap_names:
            summary = (
                f"Vendor document covers "
                f"{', '.join(covered_names)} "
                f"but is missing "
                f"{', '.join(gap_names)}."
            )
        elif gap_names:
            summary = (
                f"Vendor document is missing all assessed "
                f"GAMP 5 categories: {', '.join(gap_names)}."
            )
        else:
            summary = (
                "Vendor document covers all assessed "
                "GAMP 5 lifecycle categories."
            )

        report = GapAnalysisReport(
            file_name=doc.file_name,
            title=doc.title,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            total_categories=total,
            covered=covered_count,
            gaps=gap_count,
            findings=findings,
            summary=summary
        )

        # Step 5: Save report
        saved_path = report.save()

        self._log_audit_event(
            "GAP_ANALYSIS_COMPLETED",
            {
                "file": file_path,
                "total_categories": total,
                "covered": covered_count,
                "gaps": gap_count,
                "report_path": str(saved_path)
            }
        )

        # Build decision logic from gap analysis findings
        if gap_names:
            gap_detail = (
                f"Gaps: {', '.join(gap_names)}"
            )
        else:
            gap_detail = "No gaps identified"

        decision_logic = (
            f"Analyzed {doc.file_name} against "
            f"{total} GAMP 5 lifecycle categories; "
            f"{covered_count} covered, "
            f"{gap_count} gaps identified. "
            f"{gap_detail}"
        )

        _log_integrity_event(
            agent_name="IngestorAgent",
            action="GAP_ANALYSIS_COMPLETED",
            decision_logic=decision_logic,
        )

        return report
