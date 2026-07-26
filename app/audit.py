"""Structured audit events that intentionally exclude request content."""

from __future__ import annotations

import json
import logging
from typing import Any


logger = logging.getLogger("ai_workflow.audit")


def emit_audit_event(event: str, **details: Any) -> None:
    payload = {"event": event, **details}
    logger.info(json.dumps(payload, sort_keys=True, separators=(",", ":")))

