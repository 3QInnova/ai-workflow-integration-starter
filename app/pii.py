"""Minimal PII redaction before content crosses the provider boundary."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class RedactionResult:
    value: Any
    count: int


_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        "[REDACTED_EMAIL]",
    ),
    (
        re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)"),
        "[REDACTED_PHONE]",
    ),
    (
        re.compile(r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)"),
        "[REDACTED_PAYMENT_NUMBER]",
    ),
)


def redact_text(value: str) -> RedactionResult:
    redacted = value
    count = 0
    for pattern, replacement in _PATTERNS:
        redacted, replacements = pattern.subn(replacement, redacted)
        count += replacements
    return RedactionResult(value=redacted, count=count)


def redact_value(value: Any) -> RedactionResult:
    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, dict):
        output: dict[str, Any] = {}
        count = 0
        for key, item in value.items():
            result = redact_value(item)
            output[key] = result.value
            count += result.count
        return RedactionResult(value=output, count=count)

    if isinstance(value, list):
        output_list: list[Any] = []
        count = 0
        for item in value:
            result = redact_value(item)
            output_list.append(result.value)
            count += result.count
        return RedactionResult(value=output_list, count=count)

    return RedactionResult(value=value, count=0)

