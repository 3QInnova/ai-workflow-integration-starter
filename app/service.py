"""Workflow orchestration, safety policy, and audit trail."""

from __future__ import annotations

from uuid import uuid4

from app.audit import emit_audit_event
from app.models import RecommendedAction, WorkflowRequest, WorkflowResponse
from app.pii import redact_value
from app.providers.base import AnalysisProvider


_SENSITIVE_ACTIONS = {
    RecommendedAction.ISSUE_REFUND,
    RecommendedAction.CANCEL_ACCOUNT,
}


class WorkflowService:
    def __init__(
        self,
        provider: AnalysisProvider,
        *,
        minimum_confidence: float = 0.75,
    ) -> None:
        self._provider = provider
        self._minimum_confidence = minimum_confidence

    async def analyze(
        self,
        request: WorkflowRequest,
        *,
        correlation_id: str | None = None,
    ) -> WorkflowResponse:
        workflow_id = str(uuid4())
        effective_correlation_id = correlation_id or str(uuid4())

        redacted = redact_value(request.model_dump(mode="json"))
        safe_request = WorkflowRequest.model_validate(redacted.value)

        emit_audit_event(
            "workflow.started",
            workflow_id=workflow_id,
            correlation_id=effective_correlation_id,
            provider=self._provider.name,
            redactions_applied=redacted.count,
        )

        analysis = await self._provider.analyze(
            safe_request,
            correlation_id=effective_correlation_id,
        )

        approval_reasons: list[str] = []
        if analysis.recommended_action in _SENSITIVE_ACTIONS:
            approval_reasons.append("The recommended action changes customer state or funds.")
        if analysis.confidence < self._minimum_confidence:
            approval_reasons.append(
                f"Confidence is below the {self._minimum_confidence:.2f} policy threshold."
            )

        requires_approval = bool(approval_reasons)
        status = "pending_approval" if requires_approval else "completed"

        emit_audit_event(
            "workflow.analyzed",
            workflow_id=workflow_id,
            correlation_id=effective_correlation_id,
            provider=self._provider.name,
            category=analysis.category,
            action=analysis.recommended_action,
            confidence=analysis.confidence,
            requires_human_approval=requires_approval,
        )

        return WorkflowResponse(
            workflow_id=workflow_id,
            correlation_id=effective_correlation_id,
            status=status,
            analysis=analysis,
            requires_human_approval=requires_approval,
            approval_reasons=approval_reasons,
            redactions_applied=redacted.count,
        )

