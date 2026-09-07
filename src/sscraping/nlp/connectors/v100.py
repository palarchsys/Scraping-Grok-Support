"""Connecteur local V100 32 Go.

Le GPU n'est PAS dans ce process : vLLM ou llama.cpp écoute V100_BASE_URL.
Même contrat que GrokConnector — swap de backend sans retoucher le prompt.

Recommandé (install.sh --v100) :
  vllm  Qwen/Qwen2.5-14B-Instruct-AWQ  --max-model-len 4096
  14B AWQ ~8–10 Go ; reste ~20 Go pour KV cache (batch 4–8, Volta sm_70).
  Fallback llama.cpp GGUF Q4_K_M si vLLM refuse Volta.
"""

from __future__ import annotations

from sscraping.nlp.connectors.openai_compat import OpenAICompatConnector
from sscraping.settings import Settings


class V100Connector(OpenAICompatConnector):
    def __init__(self, settings: Settings) -> None:
        headers = {"Content-Type": "application/json"}
        if settings.v100_api_key and settings.v100_api_key != "not-needed":
            headers["Authorization"] = f"Bearer {settings.v100_api_key}"
        super().__init__(
            name="v100",
            base_url=settings.v100_base_url,
            model=settings.v100_model,
            headers=headers,
            timeout=180.0,
        )
