"""Deterministic local provider for demos, development, and tests."""

from __future__ import annotations

from app.models import (
    Priority,
    ProviderAnalysis,
    RecommendedAction,
    WorkflowRequest,
)
from app.providers.base import AnalysisProvider


class RulesProvider(AnalysisProvider):
    name = "rules"

    async def analyze(
        self,
        request: WorkflowRequest,
        *,
        correlation_id: str,
    ) -> ProviderAnalysis:
        del correlation_id
        message = request.message.lower()

        if any(term in message for term in ("fraud", "breach", "unauthorized")):
            return ProviderAnalysis(
                category="security",
                summary="Potential security issue requiring immediate investigation.",
                priority=Priority.URGENT,
                recommended_action=RecommendedAction.CREATE_INCIDENT,
                confidence=0.94,
                rationale=["Security-sensitive language detected."],
            )

        if "refund" in message:
            return ProviderAnalysis(
                category="billing",
                summary="Customer is requesting a billing adjustment.",
                priority=Priority.HIGH,
                recommended_action=RecommendedAction.ISSUE_REFUND,
                confidence=0.88,
                rationale=["Refund intent detected."],
            )

        if any(term in message for term in ("cancel account", "close account")):
            return ProviderAnalysis(
                category="account",
                summary="Customer is requesting account closure.",
                priority=Priority.HIGH,
                recommended_action=RecommendedAction.CANCEL_ACCOUNT,
                confidence=0.91,
                rationale=["Account-closure intent detected."],
            )

        if any(term in message for term in ("outage", "cannot log in", "not working")):
            return ProviderAnalysis(
                category="technical_support",
                summary="Customer reports a service-impacting technical issue.",
                priority=Priority.HIGH,
                recommended_action=RecommendedAction.ESCALATE,
                confidence=0.86,
                rationale=["Service-impact language detected."],
            )

        return ProviderAnalysis(
            category="general_support",
            summary="Customer request can follow the standard support workflow.",
            priority=Priority.NORMAL,
            recommended_action=RecommendedAction.RESPOND,
            confidence=0.78,
            rationale=["No high-risk intent detected."],
        )

