"""Connecteur API Grok (xAI). OpenAI-compatible, base https://api.x.ai/v1."""

from __future__ import annotations

from scraping_grok.nlp.connectors.openai_compat import OpenAICompatConnector
from scraping_grok.settings import Settings


class GrokConnector(OpenAICompatConnector):
    def __init__(self, settings: Settings) -> None:
        if not settings.xai_api_key:
            raise RuntimeError("XAI_API_KEY manquant dans .env")
        super().__init__(
            name="grok",
            base_url=settings.grok_base_url,
            model=settings.grok_model,
            headers={
                "Authorization": f"Bearer {settings.xai_api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
