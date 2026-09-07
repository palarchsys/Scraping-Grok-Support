"""Client OpenAI `/v1/chat/completions` (Grok / api.x.ai). Prompt systeme identique = cache préfixe."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
import orjson

log = logging.getLogger("sscraping.nlp")


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
        self._base_url = base_url.rstrip("/")
        safe_headers = {k: ("***" if k.lower() == "authorization" else v) for k, v in headers.items()}
        log.info("connector init name=%s model=%s base=%s headers=%s timeout=%s", name, model, self._base_url, safe_headers, timeout)
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers=headers,
            http2=False,
        )

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        log.debug(
            "LLM POST name=%s model=%s system_chars=%d user_chars=%d user_head=%r",
            self.name,
            self.model,
            len(system),
            len(user),
            user[:240],
        )
        t0 = time.perf_counter()
        try:
            resp = await self._client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "temperature": 0,
                    "max_tokens": 280,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
            )
        except Exception:
            log.exception("LLM transport name=%s url=%s/chat/completions", self.name, self._base_url)
            raise
        dt = time.perf_counter() - t0
        log.info("LLM HTTP name=%s status=%s latency=%.3fs bytes=%d", self.name, resp.status_code, dt, len(resp.content))
        if resp.status_code >= 400:
            log.error("LLM error body=%s", resp.text[:800])
        resp.raise_for_status()
        payload = resp.json()
        usage = payload.get("usage") or {}
        log.debug("LLM usage=%s", usage)
        content = (payload.get("choices") or [{}])[0].get("message", {}).get("content") or "{}"
        log.debug("LLM content_head=%r", content[:400])
        return orjson.loads(_strip_fence(content))

    async def aclose(self) -> None:
        log.debug("connector close name=%s", self.name)
        await self._client.aclose()
