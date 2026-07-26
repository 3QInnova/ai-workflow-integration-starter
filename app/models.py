"""Validated contracts for the API and provider boundary."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RecommendedAction(StrEnum):
    RESPOND = "respond"
    ESCALATE = "escalate"
    CREATE_INCIDENT = "create_incident"
    ISSUE_REFUND = "issue_refund"
    CANCEL_ACCOUNT = "cancel_account"


class WorkflowRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=8_000)
    channel: str = Field(default="web", min_length=1, max_length=50)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("customer_id", "channel")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class ProviderAnalysis(BaseModel):
    category: str = Field(min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=500)
    priority: Priority
    recommended_action: RecommendedAction
    confidence: float = Field(ge=0, le=1)
    rationale: list[str] = Field(default_factory=list, max_length=10)


class WorkflowResponse(BaseModel):
    workflow_id: str
    correlation_id: str
    status: str
    analysis: ProviderAnalysis
    requires_human_approval: bool
    approval_reasons: list[str]
    redactions_applied: int


class HealthResponse(BaseModel):
    service: str
    status: str
    provider: str

