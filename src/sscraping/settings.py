"""Chargement unique de la config runtime (.env + variables)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Tous les knobs perf / connecteurs. Un seul objet, injecté partout."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        extra="ignore",
    )

    demo: bool = True
    database_url: str = "postgresql://sscraping:sscraping@127.0.0.1:5432/sscraping"
    log_dir: Path = ROOT / "logs"
    log_quiet: bool = False
    concurrency: int = 8
    nlp_concurrency: int = 4
    request_timeout: float = 20.0
    user_agent: str = "ss-craping-bot/1.0 (pedagogical)"
    confidence_threshold: float = 0.7
    config_dir: Path = ROOT / "config"
    fixtures_dir: Path = ROOT / "fixtures"

    xai_api_key: str = ""
    grok_model: str = "grok-4.5"
    grok_base_url: str = "https://api.x.ai/v1"

    v100_base_url: str = "http://127.0.0.1:8000/v1"
    v100_model: str = "Qwen/Qwen2.5-14B-Instruct-AWQ"
    v100_api_key: str = "not-needed"

    max_articles: int = Field(default=50, description="Plafond pédagogique par run live.")


def get_settings() -> Settings:
    return Settings()
