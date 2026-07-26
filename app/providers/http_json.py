"""Generic HTTP+JSON adapter for an enterprise AI gateway."""

from __future__ import annotations

import httpx

from app.models import ProviderAnalysis, WorkflowRequest
from app.providers.base import AnalysisProvider


class HttpJsonProvider(AnalysisProvider):
    name = "http-json"

    def __init__(
        self,
        *,
        api_url: str,
        api_key: str,
        model: str | None,
        timeout_seconds: float,
    ) -> None:
        if not api_url or not api_key:
            raise ValueError("AI_API_URL and AI_API_KEY are required for http-json")
        self._api_url = api_url
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    async def analyze(
        self,
        request: WorkflowRequest,
        *,
        correlation_id: str,
    ) -> ProviderAnalysis:
        payload = {
            "model": self._model,
            "correlation_id": correlation_id,
            "response_schema": ProviderAnalysis.model_json_schema(),
            "input": request.model_dump(mode="json"),
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "X-Correlation-Id": correlation_id,
        }

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(self._api_url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()

        result = body.get("result", body)
        return ProviderAnalysis.model_validate(result)

