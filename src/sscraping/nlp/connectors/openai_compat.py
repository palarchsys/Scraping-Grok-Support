"""Client unique OpenAI `/v1/chat/completions`. Grok et V100 ne changent que l'URL."""

from __future__ import annotations

from typing import Any

import httpx
import orjson


def _strip_fence(content: str) -> str:
    """llama.cpp / certains instruct collent ```json ... ``` autour du JSON."""
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return text


class OpenAICompatConnector:
    """Même fil de fer : temperature=0, json_object, max_tokens borné."""

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        model: str,
        headers: dict[str, str],
        timeout: float,
    ) -> None:
        self.name = name
        self.model = model
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers=headers,
            http2=False,  # serveurs locaux : HTTP/1.1 keep-alive suffit et évite ALPN
        )

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        resp = await self._client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "temperature": 0,
                "max_tokens": 700,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"] or "{}"
        return orjson.loads(_strip_fence(content))

    async def aclose(self) -> None:
        await self._client.aclose()
