"""FastAPI entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Header

from app.config import Settings
from app.models import HealthResponse, WorkflowRequest, WorkflowResponse
from app.providers.base import AnalysisProvider
from app.providers.http_json import HttpJsonProvider
from app.providers.rules import RulesProvider
from app.service import WorkflowService


logging.basicConfig(level=logging.INFO, format="%(message)s")


def build_provider(settings: Settings) -> AnalysisProvider:
    if settings.provider == "rules":
        return RulesProvider()
    if settings.provider == "http-json":
        return HttpJsonProvider(
            api_url=settings.api_url or "",
            api_key=settings.api_key or "",
            model=settings.model,
            timeout_seconds=settings.timeout_seconds,
        )
    raise ValueError(f"Unsupported AI_PROVIDER: {settings.provider}")


settings = Settings.from_environment()
provider = build_provider(settings)
workflow_service = WorkflowService(
    provider,
    minimum_confidence=settings.minimum_confidence,
)

app = FastAPI(
    title="AI Workflow Integration Starter",
    version="1.0.0",
    description="Secure, auditable AI-assisted workflow orchestration.",
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        service="ai-workflow-integration-starter",
        status="healthy",
        provider=provider.name,
    )


@app.post("/v1/workflows/analyze", response_model=WorkflowResponse)
async def analyze_workflow(
    request: WorkflowRequest,
    x_correlation_id: str | None = Header(default=None),
) -> WorkflowResponse:
    return await workflow_service.analyze(
        request,
        correlation_id=x_correlation_id,
    )

