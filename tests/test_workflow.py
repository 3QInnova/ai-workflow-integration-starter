from __future__ import annotations

import unittest

from app.models import (
    Priority,
    ProviderAnalysis,
    RecommendedAction,
    WorkflowRequest,
)
from app.pii import redact_value
from app.providers.base import AnalysisProvider
from app.providers.rules import RulesProvider
from app.service import WorkflowService


class StubProvider(AnalysisProvider):
    name = "stub"

    def __init__(self, analysis: ProviderAnalysis) -> None:
        self.analysis = analysis
        self.last_request: WorkflowRequest | None = None

    async def analyze(
        self,
        request: WorkflowRequest,
        *,
        correlation_id: str,
    ) -> ProviderAnalysis:
        del correlation_id
        self.last_request = request
        return self.analysis


class RedactionTests(unittest.TestCase):
    def test_redacts_nested_pii(self) -> None:
        result = redact_value(
            {
                "message": "Contact me at person@example.com or 303-555-0199.",
                "metadata": {"payment": "4111 1111 1111 1111"},
            }
        )

        self.assertEqual(result.count, 3)
        self.assertNotIn("person@example.com", str(result.value))
        self.assertNotIn("303-555-0199", str(result.value))
        self.assertNotIn("4111 1111 1111 1111", str(result.value))


class WorkflowServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_standard_request_completes_without_approval(self) -> None:
        service = WorkflowService(RulesProvider())
        response = await service.analyze(
            WorkflowRequest(
                customer_id="customer-123",
                message="How can I update my notification preferences?",
            ),
            correlation_id="corr-123",
        )

        self.assertEqual(response.status, "completed")
        self.assertFalse(response.requires_human_approval)
        self.assertEqual(response.correlation_id, "corr-123")

    async def test_sensitive_action_requires_human_approval(self) -> None:
        service = WorkflowService(RulesProvider())
        response = await service.analyze(
            WorkflowRequest(
                customer_id="customer-123",
                message="Please issue a refund to my card.",
            )
        )

        self.assertEqual(response.status, "pending_approval")
        self.assertTrue(response.requires_human_approval)
        self.assertEqual(
            response.analysis.recommended_action,
            RecommendedAction.ISSUE_REFUND,
        )

    async def test_provider_receives_redacted_content(self) -> None:
        provider = StubProvider(
            ProviderAnalysis(
                category="general_support",
                summary="Standard request.",
                priority=Priority.NORMAL,
                recommended_action=RecommendedAction.RESPOND,
                confidence=0.9,
            )
        )
        service = WorkflowService(provider)

        response = await service.analyze(
            WorkflowRequest(
                customer_id="customer-123",
                message="Email person@example.com or call 303-555-0199.",
            )
        )

        self.assertEqual(response.redactions_applied, 2)
        self.assertIsNotNone(provider.last_request)
        assert provider.last_request is not None
        self.assertIn("[REDACTED_EMAIL]", provider.last_request.message)
        self.assertIn("[REDACTED_PHONE]", provider.last_request.message)

    async def test_low_confidence_requires_human_approval(self) -> None:
        provider = StubProvider(
            ProviderAnalysis(
                category="unknown",
                summary="Uncertain classification.",
                priority=Priority.NORMAL,
                recommended_action=RecommendedAction.RESPOND,
                confidence=0.52,
            )
        )
        service = WorkflowService(provider, minimum_confidence=0.75)

        response = await service.analyze(
            WorkflowRequest(customer_id="customer-123", message="Please help.")
        )

        self.assertTrue(response.requires_human_approval)
        self.assertTrue(
            any("Confidence" in reason for reason in response.approval_reasons)
        )


if __name__ == "__main__":
    unittest.main()

