"""Interface unique. Grok et V100 parlent le même dialecte OpenAI /v1/chat/completions."""

from __future__ import annotations

from typing import Any, Protocol


class LlmConnector(Protocol):
    name: str
    model: str

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        """Retourne un objet JSON (déjà parsé). Lève en cas d'échec transport."""
        ...

    async def aclose(self) -> None: ...
