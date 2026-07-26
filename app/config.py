"""Environment-backed application configuration."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    provider: str = "rules"
    api_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    timeout_seconds: float = 10.0
    minimum_confidence: float = 0.75

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            provider=os.getenv("AI_PROVIDER", "rules").strip().lower(),
            api_url=os.getenv("AI_API_URL"),
            api_key=os.getenv("AI_API_KEY"),
            model=os.getenv("AI_MODEL"),
            timeout_seconds=float(os.getenv("AI_TIMEOUT_SECONDS", "10")),
            minimum_confidence=float(os.getenv("MINIMUM_CONFIDENCE", "0.75")),
        )

