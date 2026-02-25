"""
Agent Controller Module.

Centralized interface between API endpoints and all CSV-GameChanger
agents. Every controller method logs an ``API_REQUEST`` audit event
via the IntegrityManager before delegating to the underlying agent,
ensuring a uniform audit trail for all API-initiated operations.

:requirement: URS-2.1 - System shall maintain 21 CFR Part 11
              compliant audit trail.
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from Agents.integrity_manager import log_audit_event
from Agents.risk_strategist import assess_change_request
from Agents.requirement_architect import RequirementArchitect
from Agents.verification_agent import VerificationAgent
from Agents.delta_agent import DeltaAgent
from Agents.auditor_agent import AuditorAgent
from Agents.ingestor_agent import IngestorAgent


class AgentController:
    """
    Centralized controller that wraps every agent behind an
    audit-logged facade.

    Each public method:
    1. Logs an ``API_REQUEST`` event via ``log_audit_event()``.
    2. Delegates to the underlying agent.
    3. Returns the agent's result unchanged.

    :requirement: URS-2.1 - System shall maintain 21 CFR Part 11
                  compliant audit trail.
    """

    def __init__(self) -> None:
        """
        Initialize the AgentController.

        Agent instances are created lazily on first use so that
        missing API keys or optional dependencies do not block
        controller construction.

        :requirement: URS-2.1 - Audit trail for all agent actions.
        """
        self._requirement_architect: Optional[
            RequirementArchitect
        ] = None
        self._verification_agent: Optional[
            VerificationAgent
        ] = None
        self._delta_agent: Optional[DeltaAgent] = None
        self._auditor_agent: Optional[AuditorAgent] = None
        self._ingestor_agent: Optional[IngestorAgent] = None

    # ----------------------------------------------------------
    # Lazy agent accessors
    # ----------------------------------------------------------

    def _get_requirement_architect(self) -> RequirementArchitect:
        """
        Return the cached RequirementArchitect, creating it on
        first access.

        :return: RequirementArchitect instance.
        """
        if self._requirement_architect is None:
            self._requirement_architect = RequirementArchitect()
        return self._requirement_architect

    def _get_verification_agent(self) -> VerificationAgent:
        """
        Return the cached VerificationAgent, creating it on
        first access.

        :return: VerificationAgent instance.
        """
        if self._verification_agent is None:
            self._verification_agent = VerificationAgent()
        return self._verification_agent

    def _get_delta_agent(self) -> DeltaAgent:
        """
        Return the cached DeltaAgent, creating it on first
        access.

        :return: DeltaAgent instance.
        """
        if self._delta_agent is None:
            self._delta_agent = DeltaAgent()
        return self._delta_agent

    def _get_auditor_agent(self) -> AuditorAgent:
        """
        Return the cached AuditorAgent, creating it on first
        access.

        :return: AuditorAgent instance.
        """
        if self._auditor_agent is None:
            self._auditor_agent = AuditorAgent()
        return self._auditor_agent

    def _get_ingestor_agent(self) -> IngestorAgent:
        """
        Return the cached IngestorAgent, creating it on first
        access.

        :return: IngestorAgent instance.
        """
        if self._ingestor_agent is None:
            self._ingestor_agent = IngestorAgent()
        return self._ingestor_agent

    # ----------------------------------------------------------
    # Audit helper
    # ----------------------------------------------------------

    def _log_request(
        self, endpoint: str, detail: str
    ) -> None:
        """
        Log an ``API_REQUEST`` audit event.

        :param endpoint: Logical endpoint name (method being called).
        :param detail: Short summary of the input (truncated to 80
                       characters for readability).
        :requirement: URS-2.1 - Audit trail for all agent actions.
        """
        log_audit_event(
            agent_name="AgentController",
            action="API_REQUEST",
            decision_logic=(
                f"Endpoint: {endpoint} | "
                f"Input: {detail[:80]}"
            ),
        )

    # ----------------------------------------------------------
    # RequirementArchitect wrappers
    # ----------------------------------------------------------

    def generate_urs(
        self,
        requirement: str,
        min_score: float = 0.35,
        expert_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a URS document from a natural-language requirement.

        :param requirement: Plain-English requirement statement.
        :param min_score: Minimum Pinecone similarity score.
        :param expert_mode: When *True*, skip external document
                            lookup and use deterministic logic.
        :return: Structured URS dictionary.
        :requirement: URS-6.1 - Generate URS from natural language.
        """
        self._log_request("generate_urs", requirement)
        architect = self._get_requirement_architect()
        return architect.generate_urs(
            requirement=requirement,
            min_score=min_score,
            expert_mode=expert_mode,
        )

    def search_knowledge_base(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.35,
    ) -> Dict[str, Any]:
        """
        Search the GAMP 5 / CSA Pinecone knowledge base.

        :param query: Free-text search query.
        :param top_k: Maximum results to return.
        :param min_score: Minimum similarity score.
        :return: SearchResponse as a dictionary.
        :requirement: URS-6.15 - Search knowledge base for context.
        """
        self._log_request("search_knowledge_base", query)
        architect = self._get_requirement_architect()
        response = architect.search(
            query=query,
            top_k=top_k,
            min_score=min_score,
        )
        return {
            "query": response.query,
            "total_results": response.total_results,
            "results": [
                {
                    "chunk_id": r.chunk_id,
                    "text": r.text,
                    "source_document": r.source_document,
                    "page_number": r.page_number,
                    "similarity_score": r.similarity_score,
                    "reg_version": r.reg_version,
                }
                for r in response.results
            ],
        }

    # ----------------------------------------------------------
    # VerificationAgent wrappers
    # ----------------------------------------------------------

    def verify_urs(
        self,
        urs: Dict[str, Any],
        min_score: float = 0.35,
    ) -> Dict[str, Any]:
        """
        Verify a single URS against GAMP 5 regulatory text.

        :param urs: Structured URS dictionary.
        :param min_score: Minimum Pinecone similarity score.
        :return: VerificationResult as a dictionary.
        :requirement: URS-12.1 - Verify generated URS against
                      GAMP 5 text.
        """
        urs_id = urs.get("URS_ID", "unknown")
        self._log_request("verify_urs", f"URS_ID={urs_id}")
        agent = self._get_verification_agent()
        result = agent.verify_urs(urs=urs, min_score=min_score)
        return {
            "URS_ID": result.urs_id,
            "Verdict": result.verdict.value,
            "Findings": [
                {
                    "check_name": f.check_name,
                    "status": f.status.value,
                    "detail": f.detail,
                    "gamp5_reference": f.gamp5_reference,
                }
                for f in result.findings
            ],
        }

    def verify_urs_batch(
        self,
        urs_list: List[Dict[str, Any]],
        min_score: float = 0.35,
    ) -> List[Dict[str, Any]]:
        """
        Verify a batch of URS documents.

        :param urs_list: List of URS dictionaries.
        :param min_score: Minimum Pinecone similarity score.
        :return: List of VerificationResult dictionaries.
        :requirement: URS-12.13 - Support batch verification.
        """
        self._log_request(
            "verify_urs_batch",
            f"{len(urs_list)} URS documents",
        )
        agent = self._get_verification_agent()
        results = agent.verify_batch(
            urs_list=urs_list, min_score=min_score
        )
        return [
            {
                "URS_ID": r.urs_id,
                "Verdict": r.verdict.value,
                "Findings": [
                    {
                        "check_name": f.check_name,
                        "status": f.status.value,
                        "detail": f.detail,
                        "gamp5_reference": f.gamp5_reference,
                    }
                    for f in r.findings
                ],
            }
            for r in results
        ]

    # ----------------------------------------------------------
    # RiskStrategist wrapper
    # ----------------------------------------------------------

    def assess_risk(
        self,
        system_criticality: str,
        change_type: str,
    ) -> Dict[str, Any]:
        """
        Assess risk for a change request using GAMP 5 methodology.

        :param system_criticality: ServiceNow criticality field.
        :param change_type: ServiceNow change type field.
        :return: Risk assessment dictionary.
        :requirement: URS-4.7 - Assess risk for all change requests.
        """
        self._log_request(
            "assess_risk",
            f"criticality={system_criticality}, "
            f"type={change_type}",
        )
        return assess_change_request(
            system_criticality=system_criticality,
            change_type=change_type,
        )

    # ----------------------------------------------------------
    # DeltaAgent wrappers
    # ----------------------------------------------------------

    def determine_testing_strategy(
        self, risk_level: str
    ) -> str:
        """
        Determine the CSA testing strategy for a risk level.

        :param risk_level: Risk level string (Low, Medium, High).
        :return: Testing strategy string.
        :requirement: URS-4.4 - Recommend CSA testing strategy.
        """
        from Agents.risk_strategist import RiskLevel
        self._log_request(
            "determine_testing_strategy",
            f"risk_level={risk_level}",
        )
        level = RiskLevel(risk_level)
        agent = self._get_delta_agent()
        strategy = agent.determine_testing_strategy(level)
        return strategy.value

    def generate_test_script(
        self, urs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a CSA-aligned test script from a URS requirement.

        :param urs: Structured URS dictionary.
        :return: Test script dictionary.
        :requirement: URS-8.1 - Generate test scripts from URS.
        """
        urs_id = urs.get("URS_ID", "unknown")
        self._log_request(
            "generate_test_script", f"URS_ID={urs_id}"
        )
        agent = self._get_delta_agent()
        return agent.generate_test_script(urs)

    def generate_test_batch(
        self, urs_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate test scripts for a batch of URS requirements.

        :param urs_list: List of URS dictionaries.
        :return: List of test script dictionaries.
        :requirement: URS-8.6 - Support batch generation.
        """
        self._log_request(
            "generate_test_batch",
            f"{len(urs_list)} URS documents",
        )
        agent = self._get_delta_agent()
        return agent.generate_test_batch(urs_list)

    # ----------------------------------------------------------
    # IngestorAgent wrappers
    # ----------------------------------------------------------

    def ingest_vendor_document(
        self, file_path: str
    ) -> Dict[str, Any]:
        """
        Ingest a vendor document and return structured JSON.

        :param file_path: Path to the .docx or .pdf file.
        :return: IngestedDocument as a dictionary.
        :requirement: URS-8.1 - Ingest vendor documents.
        """
        self._log_request(
            "ingest_vendor_document", file_path
        )
        ingestor = self._get_ingestor_agent()
        result = ingestor.ingest_file(file_path)
        return result.to_dict()

    def analyze_vendor_gaps(
        self, file_path: str
    ) -> Dict[str, Any]:
        """
        Perform GAMP 5 gap analysis on a vendor document.

        :param file_path: Path to the .docx or .pdf file.
        :return: GapAnalysisReport as a dictionary.
        :requirement: URS-9.1 - Perform GAMP 5 gap analysis.
        """
        self._log_request("analyze_vendor_gaps", file_path)
        ingestor = self._get_ingestor_agent()
        report = ingestor.analyze_gaps(file_path)
        return report.to_dict()

    # ----------------------------------------------------------
    # AuditorAgent wrappers
    # ----------------------------------------------------------

    def generate_vtm(
        self,
        urs_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a Validation Traceability Matrix.

        :param urs_dir: Directory containing URS Markdown files.
        :param output_dir: Directory to write the VTM output.
        :param verbose: Whether to print progress to stdout.
        :return: VTM generation result dictionary.
        :requirement: URS-12.1 - Verification deliverable
                      generation.
        """
        from pathlib import Path as _Path
        self._log_request(
            "generate_vtm",
            f"urs_dir={urs_dir}",
        )
        agent = self._get_auditor_agent()
        return agent.generate_vtm(
            urs_dir=_Path(urs_dir) if urs_dir else None,
            output_dir=_Path(output_dir) if output_dir else None,
            verbose=verbose,
        )

    def generate_vsr(
        self,
        urs_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        health_report_path: Optional[str] = None,
        vtm_csv_path: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o",
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a Validation Summary Report.

        :param urs_dir: Directory containing URS Markdown files.
        :param output_dir: Directory to write the VSR output.
        :param health_report_path: Path to Trustme_Health_Report.
        :param vtm_csv_path: Path to Trustme_Traceability_Matrix.
        :param openai_api_key: OpenAI API key (env var fallback).
        :param model: LLM model name for VSR generation.
        :param verbose: Whether to print progress to stdout.
        :return: VSR generation result dictionary.
        :requirement: URS-12.1 - Verification deliverable
                      generation.
        """
        from pathlib import Path as _Path
        self._log_request(
            "generate_vsr",
            f"urs_dir={urs_dir}",
        )
        agent = self._get_auditor_agent()
        return agent.generate_vsr(
            urs_dir=_Path(urs_dir) if urs_dir else None,
            output_dir=(
                _Path(output_dir) if output_dir else None
            ),
            health_report_path=(
                _Path(health_report_path)
                if health_report_path else None
            ),
            vtm_csv_path=(
                _Path(vtm_csv_path)
                if vtm_csv_path else None
            ),
            openai_api_key=openai_api_key,
            model=model,
            verbose=verbose,
        )

    # ----------------------------------------------------------
    # IntegrityManager pass-through
    # ----------------------------------------------------------

    def log_event(
        self,
        agent_name: str,
        action: str,
        user_id: str = "SYSTEM",
        decision_logic: str = "",
        compliance_impact: Optional[str] = None,
        thought_process: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an audit event directly via the IntegrityManager.

        This is a pass-through for callers that need to log custom
        events without going through a specific agent wrapper.

        :param agent_name: Name of the originating agent.
        :param action: Action performed.
        :param user_id: Identifier of the acting user.
        :param decision_logic: Human-readable reasoning summary.
        :param compliance_impact: Override compliance classification.
        :param thought_process: Optional AI reasoning chain.
        :return: SHA-256 reasoning hash of the logged record.
        :requirement: URS-2.1 - Audit trail for all agent actions.
        """
        return log_audit_event(
            agent_name=agent_name,
            action=action,
            user_id=user_id,
            decision_logic=decision_logic,
            compliance_impact=compliance_impact,
            thought_process=thought_process,
        )
