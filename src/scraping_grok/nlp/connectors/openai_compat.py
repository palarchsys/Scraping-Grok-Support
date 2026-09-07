"""Client OpenAI `/v1/chat/completions` (Grok / api.x.ai). Prompt systeme identique = cache préfixe."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
import orjson

log = logging.getLogger("scraping_grok.nlp")


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
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.calls = 0
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
                    "max_tokens": 400,
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
        self.calls += 1
        self.prompt_tokens += int(usage.get("prompt_tokens") or 0)
        self.completion_tokens += int(usage.get("completion_tokens") or 0)
        log.info(
            "LLM usage prompt=%s completion=%s total_prompt=%s total_completion=%s calls=%s",
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
            self.prompt_tokens,
            self.completion_tokens,
            self.calls,
        )
        content = (payload.get("choices") or [{}])[0].get("message", {}).get("content") or "{}"
        log.debug("LLM content_head=%r", content[:400])
        return orjson.loads(_strip_fence(content))

    async def aclose(self) -> None:
        log.debug("connector close name=%s", self.name)
        await self._client.aclose()

    @property
    def usage(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "calls": self.calls,
        }
