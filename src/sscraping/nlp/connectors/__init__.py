"""Connecteurs LLM interchangeables (même interface OpenAI /v1)."""

from sscraping.nlp.connectors.base import LlmConnector
from sscraping.nlp.connectors.grok import GrokConnector
from sscraping.nlp.connectors.openai_compat import OpenAICompatConnector
from sscraping.nlp.connectors.v100 import V100Connector

__all__ = ["LlmConnector", "OpenAICompatConnector", "GrokConnector", "V100Connector"]
