"""
CSV-GameChanger Root API Server.

Provides a health-check endpoint and a URS generation endpoint
powered by the RequirementArchitect agent.

:requirement: URS-6.1 - System shall generate URS from natural
              language input.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from Agents.requirement_architect import (
    RequirementArchitect,
    RegulatoryContextNotFoundError,
)


app = FastAPI(
    title="CSV-GameChanger",
    description="GAMP 5 / CSA Compliant EVOLV Engine",
    version="0.1.0",
)


# ------------------------------------------------------------------
# Request / Response models
# ------------------------------------------------------------------
class URSRequest(BaseModel):
    """Incoming request to generate a URS."""

    requirement: str = Field(
        ...,
        min_length=1,
        description="Natural language requirement description",
        json_schema_extra={
            "example": "I want to track warehouse temperature"
        },
    )
    min_score: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum Pinecone similarity score",
    )


class URSResponse(BaseModel):
    """Generated URS returned to the caller."""

    URS_ID: str
    Requirement_Statement: str
    Criticality: str
    Regulatory_Rationale: str
    Reg_Versions_Cited: List[str] = []


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------
@app.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Health-check endpoint.

    :return: Service status and current UTC timestamp.
    """
    return {
        "status": "healthy",
        "service": "CSV-GameChanger",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/generate-urs", response_model=URSResponse)
async def generate_urs(payload: URSRequest) -> Dict[str, Any]:
    """
    Generate a User Requirements Specification from natural language.

    Delegates to the RequirementArchitect agent, which queries the
    Pinecone knowledge base for GAMP 5 context and returns a
    structured URS with regulatory rationale.

    :param payload: URSRequest with the requirement text.
    :return: Structured URS dictionary.
    :requirement: URS-6.1 - System shall generate URS from natural
                  language input.
    """
    try:
        architect = RequirementArchitect()
        urs = architect.generate_urs(
            requirement=payload.requirement,
            min_score=payload.min_score,
        )
        return urs

    except RegulatoryContextNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"URS generation failed: {exc}",
        )
