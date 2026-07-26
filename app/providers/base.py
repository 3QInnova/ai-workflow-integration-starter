"""Provider interface used to isolate external AI dependencies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import ProviderAnalysis, WorkflowRequest


class AnalysisProvider(ABC):
    name = "abstract"

    @abstractmethod
    async def analyze(
        self,
        request: WorkflowRequest,
        *,
        correlation_id: str,
    ) -> ProviderAnalysis:
        """Return a validated analysis for already-redacted input."""

