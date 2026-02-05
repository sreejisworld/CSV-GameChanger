"""
Requirement Architect Agent Module.

Generates User Requirements Specifications (URS) using GAMP 5 regulatory
context retrieved from Pinecone vector store.

:requirement: URS-6.1 - System shall generate URS from natural language input.
"""
import os
import json
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from Agents.integrity_manager import (
    log_audit_event as _log_integrity_event,
)

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# Configuration
PINECONE_INDEX_NAME = "csv-knowledge-base"
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K_RESULTS = 5
MIN_SIMILARITY_SCORE = 0.5

_KNOWN_REG_VERSIONS: set = set()

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "enterprise_standards"

REQUIRED_TEMPLATE_FIELDS = [
    "template_id", "industry", "requirement_prefix",
    "document_title", "header_project_label", "sections",
    "criticality_keywords", "rationale_prefix", "footer"
]


@dataclass
class EnterpriseTemplate:
    """
    Enterprise template for industry-specific URS formatting.

    Defines requirement prefixes, criticality keywords, document
    headings, and other formatting options that vary by industry.

    :requirement: URS-8.1 - System shall support enterprise templates.
    """

    template_id: str
    industry: str
    requirement_prefix: str
    document_title: str
    header_project_label: str
    sections: Dict[str, str]
    criticality_keywords: Dict[str, List[str]]
    rationale_prefix: str
    footer: str


def load_template(template_name: str) -> EnterpriseTemplate:
    """
    Load an enterprise template from the templates directory.

    Resolves template_name to a JSON file under
    templates/enterprise_standards/{template_name}.json, reads it,
    validates required fields, and returns an EnterpriseTemplate.

    :param template_name: Name of the template (without .json extension).
    :return: Loaded EnterpriseTemplate instance.
    :raises ValueError: If template file is not found or is invalid.
    :requirement: URS-8.1 - System shall support enterprise templates.
    """
    template_path = TEMPLATES_DIR / f"{template_name}.json"

    if not template_path.exists():
        available = [
            p.stem for p in TEMPLATES_DIR.glob("*.json")
        ] if TEMPLATES_DIR.exists() else []
        raise ValueError(
            f"Template '{template_name}' not found at {template_path}. "
            f"Available templates: {available}"
        )

    with open(template_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate required fields
    missing = [
        field for field in REQUIRED_TEMPLATE_FIELDS
        if field not in data
    ]
    if missing:
        raise ValueError(
            f"Template '{template_name}' is missing required fields: "
            f"{missing}"
        )

    return EnterpriseTemplate(
        template_id=data["template_id"],
        industry=data["industry"],
        requirement_prefix=data["requirement_prefix"],
        document_title=data["document_title"],
        header_project_label=data["header_project_label"],
        sections=data["sections"],
        criticality_keywords=data["criticality_keywords"],
        rationale_prefix=data["rationale_prefix"],
        footer=data["footer"]
    )


class RegulatoryContextNotFoundError(Exception):
    """
    Raised when no matching GAMP 5/CSA context is found in Pinecone.

    Error code: CSV-004 - No regulatory context found.

    :requirement: URS-6.13 - System shall require regulatory context for URS.
    """

    error_code = "CSV-004"

    def __init__(self, query: str):
        self.query = query
        super().__init__(
            f"No matching GAMP 5/CSA regulatory context found for: '{query}'. "
            f"Ensure documents are ingested into the '{PINECONE_INDEX_NAME}' index."
        )


class Criticality(Enum):
    """
    Criticality classification for user requirements.

    :requirement: URS-6.2 - System shall classify requirements as High/Med/Low.
    """

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RiskAssessmentCategory(Enum):
    """
    GAMP 5 risk assessment category for UR/FR transformation.

    :requirement: URS-16.1 - System shall classify UR risk assessment.
    """

    GXP_DIRECT = "GxP Direct"
    GXP_INDIRECT = "GxP Indirect"
    GXP_NONE = "GxP None"


class ImplementationMethod(Enum):
    """
    Implementation method for UR/FR transformation.

    :requirement: URS-16.1 - System shall classify UR implementation method.
    """

    OUT_OF_THE_BOX = "Out of the Box"
    CONFIGURED = "Configured"
    CUSTOM = "Custom"


class URFRRiskLevel(Enum):
    """
    Risk level derived from risk-assessment x implementation-method matrix.

    Distinct from ``Criticality`` and ``risk_strategist.RiskLevel``.

    :requirement: URS-16.2 - System shall determine UR/FR risk level.
    """

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class URFRTestStrategy(Enum):
    """
    Test strategy derived from risk-level x implementation-method matrix.

    :requirement: URS-16.3 - System shall determine UR/FR test strategy.
    """

    OQ_UAT = "OQ and/or UAT"
    INFORMAL = "Informal"
    SUPPLIER_PROVIDED = "Supplier Provided"


# ── UR/FR risk & test-strategy matrices ──────────────────────────

_RISK_MATRIX: Dict[
    tuple, URFRRiskLevel
] = {
    (RiskAssessmentCategory.GXP_DIRECT, ImplementationMethod.CUSTOM):
        URFRRiskLevel.HIGH,
    (RiskAssessmentCategory.GXP_DIRECT, ImplementationMethod.CONFIGURED):
        URFRRiskLevel.HIGH,
    (RiskAssessmentCategory.GXP_DIRECT, ImplementationMethod.OUT_OF_THE_BOX):
        URFRRiskLevel.MEDIUM,
    (RiskAssessmentCategory.GXP_INDIRECT, ImplementationMethod.CUSTOM):
        URFRRiskLevel.MEDIUM,
    (RiskAssessmentCategory.GXP_INDIRECT, ImplementationMethod.CONFIGURED):
        URFRRiskLevel.HIGH,
    (RiskAssessmentCategory.GXP_INDIRECT, ImplementationMethod.OUT_OF_THE_BOX):
        URFRRiskLevel.LOW,
    (RiskAssessmentCategory.GXP_NONE, ImplementationMethod.CUSTOM):
        URFRRiskLevel.LOW,
    (RiskAssessmentCategory.GXP_NONE, ImplementationMethod.CONFIGURED):
        URFRRiskLevel.LOW,
    (RiskAssessmentCategory.GXP_NONE, ImplementationMethod.OUT_OF_THE_BOX):
        URFRRiskLevel.LOW,
}

_TEST_STRATEGY_MATRIX: Dict[
    tuple, URFRTestStrategy
] = {
    (URFRRiskLevel.HIGH, ImplementationMethod.OUT_OF_THE_BOX):
        URFRTestStrategy.OQ_UAT,
    (URFRRiskLevel.HIGH, ImplementationMethod.CONFIGURED):
        URFRTestStrategy.OQ_UAT,
    (URFRRiskLevel.HIGH, ImplementationMethod.CUSTOM):
        URFRTestStrategy.OQ_UAT,
    (URFRRiskLevel.MEDIUM, ImplementationMethod.OUT_OF_THE_BOX):
        URFRTestStrategy.SUPPLIER_PROVIDED,
    (URFRRiskLevel.MEDIUM, ImplementationMethod.CONFIGURED):
        URFRTestStrategy.INFORMAL,
    (URFRRiskLevel.MEDIUM, ImplementationMethod.CUSTOM):
        URFRTestStrategy.INFORMAL,
    (URFRRiskLevel.LOW, ImplementationMethod.OUT_OF_THE_BOX):
        URFRTestStrategy.SUPPLIER_PROVIDED,
    (URFRRiskLevel.LOW, ImplementationMethod.CONFIGURED):
        URFRTestStrategy.INFORMAL,
    (URFRRiskLevel.LOW, ImplementationMethod.CUSTOM):
        URFRTestStrategy.INFORMAL,
}

URFR_CATEGORIES: List[str] = [
    "General",
    "Reporting",
    "Integration",
    "Security",
    "Non-functional",
]

_RISK_NOTE: str = (
    "Final Risk Profiling will be decided with stakeholders "
    "as part of the Risk Assessment process."
)


@dataclass
class URSDocument:
    """
    User Requirements Specification document structure.

    :requirement: URS-6.3 - System shall output structured URS documents.
    """

    urs_id: str
    requirement_statement: str
    criticality: str
    regulatory_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert URS document to dictionary.

        :return: Dictionary representation of the URS.
        :requirement: URS-6.4 - System shall provide JSON output format.
        """
        return {
            "URS_ID": self.urs_id,
            "Requirement_Statement": self.requirement_statement,
            "Criticality": self.criticality,
            "Regulatory_Rationale": self.regulatory_rationale
        }

    def to_json(self) -> str:
        """
        Convert URS document to JSON string.

        :return: JSON string representation of the URS.
        :requirement: URS-6.4 - System shall provide JSON output format.
        """
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class SearchResult:
    """
    Represents a search result from the Pinecone knowledge base.

    :requirement: URS-6.14 - System shall return structured search results.
    """

    chunk_id: str
    text: str
    source_document: str
    page_number: int
    similarity_score: float
    reg_version: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert search result to dictionary.

        :return: Dictionary representation of the search result.
        """
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source_document": self.source_document,
            "page_number": self.page_number,
            "similarity_score": self.similarity_score,
            "reg_version": self.reg_version
        }


@dataclass
class SearchResponse:
    """
    Response object containing search results from Pinecone query.

    :requirement: URS-6.14 - System shall return structured search results.
    """

    query: str
    results: List[SearchResult] = field(default_factory=list)
    total_results: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert search response to dictionary.

        :return: Dictionary representation of the search response.
        """
        return {
            "query": self.query,
            "total_results": self.total_results,
            "results": [r.to_dict() for r in self.results]
        }

    def to_json(self) -> str:
        """
        Convert search response to JSON string.

        :return: JSON string representation of the search response.
        """
        return json.dumps(self.to_dict(), indent=2)


class RequirementArchitect:
    """
    Generates User Requirements Specifications using GAMP 5 context from Pinecone.

    This agent takes natural language requirement descriptions and produces
    structured URS documents with regulatory rationale based on retrieved
    GAMP 5 guidance.

    :requirement: URS-6.1 - System shall generate URS from natural language input.
    """

    def __init__(
        self,
        pinecone_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        index_name: str = PINECONE_INDEX_NAME,
        template: Optional[EnterpriseTemplate] = None
    ):
        """
        Initialize the RequirementArchitect with API clients.

        :param pinecone_api_key: Pinecone API key (defaults to env var).
        :param openai_api_key: OpenAI API key (defaults to env var).
        :param index_name: Name of the Pinecone index to query.
        :param template: Optional enterprise template for industry-specific
                        formatting and criticality keywords.
        :requirement: URS-6.5 - System shall connect to Pinecone knowledge base.
        """
        self._pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        self._openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self._index_name = index_name
        self._urs_counter = 0
        self._template = template

        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """
        Validate that required dependencies are available.

        :raises ImportError: If pinecone or openai packages are not installed.
        :requirement: URS-6.6 - System shall validate environment before processing.
        """
        if Pinecone is None:
            raise ImportError(
                "pinecone-client is required. Install with: pip install pinecone"
            )
        if OpenAI is None:
            raise ImportError(
                "openai is required. Install with: pip install openai"
            )

    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for input text using OpenAI.

        :param text: The text to embed.
        :return: Embedding vector as list of floats.
        :requirement: URS-6.7 - System shall embed user input for similarity search.
        """
        if not self._openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for embeddings")

        client = OpenAI(api_key=self._openai_api_key)
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    def _query_pinecone(
        self,
        embedding: List[float],
        top_k: int = TOP_K_RESULTS,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone index for similar GAMP 5 sections.

        :param embedding: The query embedding vector.
        :param top_k: Number of results to return.
        :param min_score: Minimum similarity score threshold.
        :return: List of matching documents with metadata.
        :requirement: URS-6.8 - System shall retrieve relevant GAMP 5 sections.
        """
        if not self._pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is required for vector search")

        pc = Pinecone(api_key=self._pinecone_api_key)
        index = pc.Index(self._index_name)

        results = index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True
        )

        matches = []
        for match in results.matches:
            if match.score >= min_score:
                matches.append({
                    "chunk_id": match.id,
                    "text": match.metadata.get("text", ""),
                    "source_document": match.metadata.get(
                        "source_document", ""
                    ),
                    "page_number": match.metadata.get(
                        "page_number", 0
                    ),
                    "score": match.score,
                    "reg_version": match.metadata.get(
                        "reg_version", ""
                    ),
                })

        return matches

    def search(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
        min_score: float = MIN_SIMILARITY_SCORE
    ) -> SearchResponse:
        """
        Search the Pinecone knowledge base for relevant GAMP 5/CSA content.

        Embeds the query string and performs a semantic similarity search
        against the ingested regulatory documents in the csv-knowledge-base
        Pinecone index.

        :param query: Natural language query to search for
                     (e.g., "temperature monitoring requirements").
        :param top_k: Maximum number of results to return (default: 5).
        :param min_score: Minimum similarity score threshold (default: 0.5).
        :return: SearchResponse containing matching chunks with metadata.
        :raises ValueError: If query is empty or API keys are missing.
        :requirement: URS-6.15 - System shall search knowledge base for context.

        Example:
            >>> architect = RequirementArchitect()
            >>> results = architect.search("warehouse temperature monitoring")
            >>> for result in results.results:
            ...     print(f"{result.source_document}: {result.text[:100]}...")
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        # Generate embedding for the query
        embedding = self._get_embedding(query)

        # Query Pinecone
        matches = self._query_pinecone(embedding, top_k=top_k, min_score=min_score)

        # Convert to SearchResult objects
        results = [
            SearchResult(
                chunk_id=m["chunk_id"],
                text=m["text"],
                source_document=m["source_document"],
                page_number=m["page_number"],
                similarity_score=m["score"],
                reg_version=m.get("reg_version", ""),
            )
            for m in matches
        ]

        response = SearchResponse(
            query=query,
            results=results,
            total_results=len(results)
        )

        # Detect new regulatory versions
        global _KNOWN_REG_VERSIONS
        new_versions = {
            r.reg_version
            for r in results
            if r.reg_version
        } - _KNOWN_REG_VERSIONS
        if new_versions:
            for ver in sorted(new_versions):
                print(
                    f"[RequirementArchitect] New regulatory "
                    f"version detected: {ver}. Do you wish "
                    f"to re-evaluate existing logic? (y/n)"
                )
                _log_integrity_event(
                    agent_name="RequirementArchitect",
                    action="REG_VERSION_CHANGE_DETECTED",
                    decision_logic=(
                        f"New regulatory version {ver} "
                        f"detected in search results"
                    ),
                )
            _KNOWN_REG_VERSIONS |= new_versions

        _log_integrity_event(
            agent_name="RequirementArchitect",
            action="SEARCH_KNOWLEDGE_BASE",
        )

        return response

    def _determine_criticality(
        self,
        requirement: str,
        search_results: List[SearchResult]
    ) -> Criticality:
        """
        Determine requirement criticality based on content analysis.

        High criticality indicators:
        - Patient safety impact
        - Data integrity concerns
        - Regulatory compliance requirements
        - GxP critical systems

        Medium criticality indicators:
        - Operational efficiency
        - Quality system support
        - Audit trail requirements

        Low criticality indicators:
        - Administrative functions
        - Non-GxP systems
        - Convenience features

        :param requirement: The original requirement text.
        :param search_results: Retrieved GAMP 5 search results.
        :return: Criticality classification.
        :requirement: URS-6.9 - System shall assess requirement criticality.
        """
        requirement_lower = requirement.lower()

        # Use template keywords if available, otherwise defaults
        if self._template:
            high_keywords = self._template.criticality_keywords.get(
                "high", []
            )
            medium_keywords = self._template.criticality_keywords.get(
                "medium", []
            )
        else:
            # High criticality keywords
            high_keywords = [
                "patient", "safety", "critical", "gxp", "compliance",
                "validation", "sterile", "batch", "release", "adverse",
                "pharmacovigilance", "clinical", "regulatory",
                "fda", "ema"
            ]

            # Medium criticality keywords
            medium_keywords = [
                "quality", "audit", "traceability", "calibration",
                "deviation", "capa", "change control", "training",
                "document", "sop", "warehouse", "inventory",
                "temperature"
            ]

        # Check for high criticality
        for keyword in high_keywords:
            if keyword in requirement_lower:
                return Criticality.HIGH

        # Check context for regulatory references
        context_text = " ".join([r.text.lower() for r in search_results if r.text])
        for keyword in high_keywords:
            if keyword in context_text:
                return Criticality.HIGH

        # Check for medium criticality
        for keyword in medium_keywords:
            if keyword in requirement_lower:
                return Criticality.MEDIUM

        return Criticality.LOW

    def _generate_urs_id(self) -> str:
        """
        Generate a unique URS identifier.

        :return: URS ID in format URS-X.Y.
        :requirement: URS-6.10 - System shall assign unique URS identifiers.
        """
        self._urs_counter += 1
        # Format: URS-[major].[minor] - using 7 as major for new requirements
        return f"URS-7.{self._urs_counter}"

    def _build_regulatory_rationale(
        self,
        search_results: List[SearchResult]
    ) -> str:
        """
        Build regulatory rationale from retrieved GAMP 5 context.

        :param search_results: List of SearchResult objects from Pinecone.
        :return: Formatted regulatory rationale string.
        :raises RegulatoryContextNotFoundError: If no results provided.
        :requirement: URS-6.11 - System shall provide regulatory justification.
        """
        if not search_results:
            raise RegulatoryContextNotFoundError("unknown requirement")

        rationale_parts = []
        seen_sources = set()

        prefix = "Per"
        if self._template:
            prefix = self._template.rationale_prefix

        for result in search_results[:3]:  # Use top 3 matches
            source = result.source_document or "Unknown"
            page = result.page_number or 0
            text = result.text[:200] if result.text else ""
            ver = result.reg_version or ""

            source_key = f"{source}:p{page}"
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                if ver:
                    rationale_parts.append(
                        f"{prefix} {source} [{ver}] "
                        f"(p.{page}): {text}..."
                    )
                else:
                    rationale_parts.append(
                        f"{prefix} {source} "
                        f"(p.{page}): {text}..."
                    )

        return " | ".join(rationale_parts)

    def _format_requirement_statement(self, requirement: str) -> str:
        """
        Format user input into formal requirement statement.

        Transforms casual input into structured "The system shall..." format.

        :param requirement: Raw user requirement input.
        :return: Formatted requirement statement.
        :requirement: URS-6.12 - System shall format requirements per standards.
        """
        requirement = requirement.strip()

        req_prefix = "The system shall"
        if self._template:
            req_prefix = self._template.requirement_prefix

        # Already formatted with current prefix
        if requirement.lower().startswith(req_prefix.lower()):
            return requirement

        # Remove common prefixes
        prefixes_to_remove = [
            "i want to", "i need to", "we need to", "we want to",
            "it should", "should be able to", "need to", "want to"
        ]

        lower_req = requirement.lower()
        for prefix in prefixes_to_remove:
            if lower_req.startswith(prefix):
                requirement = requirement[len(prefix):].strip()
                break

        # Ensure proper capitalization for the action
        if requirement:
            requirement = requirement[0].lower() + requirement[1:]

        return f"{req_prefix} {requirement}."

    def generate_urs(
        self,
        requirement: str,
        min_score: float = MIN_SIMILARITY_SCORE
    ) -> Dict[str, Any]:
        """
        Generate a User Requirements Specification from natural language input.

        This function takes a natural language requirement description,
        queries the Pinecone index for relevant GAMP 5 guidance, and
        produces a structured URS document with regulatory rationale.

        Every generated URS is guaranteed to have at least one matching
        chunk from the ingested GAMP 5/CSA documents as regulatory context.

        :param requirement: Natural language requirement description
                          (e.g., "I want to track warehouse temp").
        :param min_score: Minimum similarity score for matching chunks
                         (default: 0.5).
        :return: Dictionary containing URS_ID, Requirement_Statement,
                Criticality, and Regulatory_Rationale.
        :raises ValueError: If requirement is empty or API keys are missing.
        :raises RegulatoryContextNotFoundError: If no matching GAMP 5/CSA
                context is found in the knowledge base.
        :requirement: URS-6.1 - System shall generate URS from natural language input.

        Example:
            >>> architect = RequirementArchitect()
            >>> urs = architect.generate_urs("I want to track warehouse temp")
            >>> print(urs)
            {
                "URS_ID": "URS-7.1",
                "Requirement_Statement": "The system shall track warehouse temp.",
                "Criticality": "Medium",
                "Regulatory_Rationale": "Per GAMP 5 Guide (p.42): ..."
            }
        """
        if not requirement or not requirement.strip():
            raise ValueError("Requirement cannot be empty")

        # Step 1: Search Pinecone for relevant GAMP 5/CSA sections
        search_response = self.search(
            query=requirement,
            top_k=TOP_K_RESULTS,
            min_score=min_score
        )

        # Step 2: Ensure at least one matching chunk is found
        if not search_response.results:
            _log_integrity_event(
                agent_name="RequirementArchitect",
                action="URS_GENERATION_FAILED",
            )
            raise RegulatoryContextNotFoundError(requirement)

        # Step 3: Determine criticality based on content
        criticality = self._determine_criticality(
            requirement,
            search_response.results
        )

        # Step 4: Generate URS ID
        urs_id = self._generate_urs_id()

        # Step 5: Format requirement statement
        statement = self._format_requirement_statement(requirement)

        # Step 6: Build regulatory rationale from search results
        rationale = self._build_regulatory_rationale(search_response.results)

        # Collect unique regulatory versions cited
        reg_versions_cited = sorted({
            r.reg_version
            for r in search_response.results
            if r.reg_version
        })

        # Create URS document
        urs = URSDocument(
            urs_id=urs_id,
            requirement_statement=statement,
            criticality=criticality.value,
            regulatory_rationale=rationale
        )

        _log_integrity_event(
            agent_name="RequirementArchitect",
            action="URS_GENERATED",
        )

        result = urs.to_dict()
        result["Reg_Versions_Cited"] = reg_versions_cited
        return result

    # ── UR/FR transformation helpers ─────────────────────────────

    @staticmethod
    def _determine_ur_fr_risk_level(
        ra: RiskAssessmentCategory,
        im: ImplementationMethod,
    ) -> URFRRiskLevel:
        """
        Look up risk level from the risk-assessment x implementation matrix.

        :param ra: Risk assessment category.
        :param im: Implementation method.
        :return: Derived risk level.
        :requirement: URS-16.2 - System shall determine UR/FR risk level.
        """
        return _RISK_MATRIX[(ra, im)]

    @staticmethod
    def _determine_ur_fr_test_strategy(
        risk_level: URFRRiskLevel,
        im: ImplementationMethod,
    ) -> URFRTestStrategy:
        """
        Look up test strategy from the risk-level x implementation matrix.

        :param risk_level: The derived risk level.
        :param im: Implementation method.
        :return: Recommended test strategy.
        :requirement: URS-16.3 - System shall determine UR/FR test strategy.
        """
        return _TEST_STRATEGY_MATRIX[(risk_level, im)]

    @staticmethod
    def _split_requirement_to_frs(
        statement: str,
    ) -> List[str]:
        """
        Split a compound requirement statement into FR clauses.

        Splits on common conjunctions (``and``, ``as well as``,
        semicolons) while preserving each clause as a complete
        sentence.  Single-clause statements return a one-element
        list.

        :param statement: The requirement statement to split.
        :return: List of individual FR clause strings.
        :requirement: URS-16.4 - System shall decompose URS into FRs.
        """
        import re

        # Normalise whitespace
        text = " ".join(statement.split())

        # Split on semicolons first
        parts: List[str] = []
        for segment in text.split(";"):
            segment = segment.strip()
            if not segment:
                continue
            # Split on " and " / " as well as " only when they
            # separate independent clauses (preceded by a comma or
            # appearing after "shall").
            sub_parts = re.split(
                r",\s*and\s+|,\s*as well as\s+|\band\b\s+shall\s+",
                segment,
            )
            for sp in sub_parts:
                sp = sp.strip(" .,")
                if sp:
                    parts.append(sp)

        # Fallback: if nothing was split, return the original
        if not parts:
            parts = [text.strip(" .")]

        return parts

    @staticmethod
    def _generate_acceptance_criteria(
        fr_statement: str,
        criticality: str,
    ) -> List[str]:
        """
        Produce Given/When/Then acceptance criteria for a single FR.

        Uses deterministic templates based on criticality to ensure
        consistent output without LLM calls.

        :param fr_statement: The functional requirement statement.
        :param criticality: URS criticality (High, Medium, Low).
        :return: List of acceptance-criteria strings.
        :requirement: URS-16.5 - System shall generate acceptance criteria.
        """
        criteria = [
            (
                f"Given the system is operational, "
                f"when {fr_statement.rstrip('.')}, "
                f"then the expected outcome is achieved "
                f"and an audit trail entry is recorded."
            ),
        ]
        if criticality in ("High", "Medium"):
            criteria.append(
                f"Given an invalid input, "
                f"when {fr_statement.rstrip('.')} is attempted, "
                f"then the system rejects the action "
                f"and logs the failure."
            )
        return criteria

    def transform_urs_to_ur_fr(
        self,
        urs: Dict[str, Any],
        role: str = "User",
        category: str = "General",
        risk_assessment: str = "GxP Indirect",
        implementation_method: str = "Configured",
    ) -> Dict[str, Any]:
        """
        Transform an approved URS dict into a structured UR/FR document.

        This is a fully deterministic, rule-based transformation.
        No LLM or Pinecone calls are made; all regulatory context
        is inherited from the source URS.

        :param urs: URS dictionary (must contain URS_ID,
                    Requirement_Statement, Criticality,
                    Regulatory_Rationale).
        :param role: The user role for the UR statement
                     (default "User").
        :param category: UR/FR category from URFR_CATEGORIES
                         (default "General").
        :param risk_assessment: Risk assessment category string
                                (default "GxP Indirect").
        :param implementation_method: Implementation method string
                                      (default "Configured").
        :return: Structured UR/FR JSON-serialisable dictionary.
        :raises ValueError: If URS is missing required keys or
                            category / risk_assessment /
                            implementation_method are invalid.
        :requirement: URS-16.6 - System shall transform URS to UR/FR.
        :requirement: URS-16.7 - System shall log UR/FR transformation.
        """
        # ── validate inputs ──────────────────────────────────────
        required_keys = {
            "URS_ID", "Requirement_Statement",
            "Criticality", "Regulatory_Rationale",
        }
        missing = required_keys - urs.keys()
        if missing:
            raise ValueError(
                f"URS dict missing required keys: "
                f"{', '.join(sorted(missing))}"
            )

        if category not in URFR_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. "
                f"Must be one of {URFR_CATEGORIES}"
            )

        # Resolve enums from string values
        ra_map = {e.value: e for e in RiskAssessmentCategory}
        im_map = {e.value: e for e in ImplementationMethod}

        if risk_assessment not in ra_map:
            raise ValueError(
                f"Invalid risk_assessment '{risk_assessment}'. "
                f"Must be one of {list(ra_map.keys())}"
            )
        if implementation_method not in im_map:
            raise ValueError(
                f"Invalid implementation_method "
                f"'{implementation_method}'. "
                f"Must be one of {list(im_map.keys())}"
            )

        ra_enum = ra_map[risk_assessment]
        im_enum = im_map[implementation_method]

        # ── derive risk & test strategy ──────────────────────────
        risk_level = self._determine_ur_fr_risk_level(ra_enum, im_enum)
        test_strategy = self._determine_ur_fr_test_strategy(
            risk_level, im_enum,
        )

        # ── build UR statement ───────────────────────────────────
        statement = urs["Requirement_Statement"]
        # Strip "The system shall " prefix for embedding in UR
        core = statement
        for prefix in (
            "The system shall ", "the system shall ",
        ):
            if core.startswith(prefix):
                core = core[len(prefix):]
                break
        ur_statement = (
            f"As a {role}, there will be "
            f"{core.rstrip('.')} so that the requirement "
            f"is fulfilled."
        )

        # ── split into FRs ───────────────────────────────────────
        fr_clauses = self._split_requirement_to_frs(statement)
        criticality = urs["Criticality"]
        functional_requirements: List[Dict[str, Any]] = []
        for idx, clause in enumerate(fr_clauses, start=1):
            fr_id = f"FR-{idx}"
            acceptance = self._generate_acceptance_criteria(
                clause, criticality,
            )
            functional_requirements.append({
                "fr_id": fr_id,
                "parent_ur_id": "UR-1",
                "statement": clause,
                "acceptance_criteria": acceptance,
            })

        # ── assemble output ──────────────────────────────────────
        reg_versions = urs.get("Reg_Versions_Cited", [])
        result: Dict[str, Any] = {
            "urs_id": urs["URS_ID"],
            "requirement_summary": statement,
            "category": category,
            "user_requirement": {
                "ur_id": "UR-1",
                "statement": ur_statement,
                "risk_assessment": risk_assessment,
                "implementation_method": implementation_method,
                "risk_level": risk_level.value,
                "test_strategy": test_strategy.value,
                "risk_note": _RISK_NOTE,
            },
            "functional_requirements": functional_requirements,
            "assumptions_and_dependencies": [
                "System access and permissions are managed "
                "per site SOP.",
            ],
            "compliance_notes": [
                "Cross-reference SOP-436231 for change-control "
                "procedures.",
                "All testing evidence must be retained per "
                "21 CFR Part 11.",
            ],
            "implementation_notes": [
                f"Implementation method: {implementation_method}.",
                f"Risk assessment category: {risk_assessment}.",
            ],
            "reg_versions_cited": reg_versions,
        }

        # ── audit trail ──────────────────────────────────────────
        _log_integrity_event(
            agent_name="RequirementArchitect",
            action="URS_TRANSFORMED_TO_UR_FR",
            decision_logic=(
                f"Transformed {urs['URS_ID']} to UR/FR. "
                f"RA={risk_assessment}, IM={implementation_method}, "
                f"Risk={risk_level.value}, "
                f"Test={test_strategy.value}."
            ),
            thought_process={
                "inputs": {
                    "urs_id": urs["URS_ID"],
                    "criticality": criticality,
                    "role": role,
                    "category": category,
                    "risk_assessment": risk_assessment,
                    "implementation_method": implementation_method,
                },
                "steps": [
                    "Validated URS contains required keys",
                    "Resolved risk-assessment and implementation "
                    "enums",
                    f"Looked up risk level: {risk_level.value}",
                    f"Looked up test strategy: "
                    f"{test_strategy.value}",
                    f"Split requirement into "
                    f"{len(fr_clauses)} FR(s)",
                    "Generated acceptance criteria per FR",
                    "Assembled UR/FR output document",
                ],
                "outputs": {
                    "ur_id": "UR-1",
                    "fr_count": len(functional_requirements),
                    "risk_level": risk_level.value,
                    "test_strategy": test_strategy.value,
                },
            },
        )

        return result
