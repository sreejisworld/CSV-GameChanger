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
