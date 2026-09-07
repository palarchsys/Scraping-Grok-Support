"""Orchestrateurs étape 1 (live Scrapy + démo fixtures) et run complet."""

from __future__ import annotations

import json
import logging

from sscraping.db.store import Store
from sscraping.nlp.connectors.grok import GrokConnector
from sscraping.nlp.connectors.v100 import V100Connector
from sscraping.nlp.pipeline import run_analyze
from sscraping.scrape.base import ScrapedArticle
from sscraping.scrape.normalize import parse_date
from sscraping.settings import Settings

log = logging.getLogger(__name__)


async def scrape_demo(store: Store, settings: Settings) -> int:
    """Charge fixtures/articles.json — zéro réseau. C'est le mode par défaut."""
    path = settings.fixtures_dir / "articles.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    log.info("demo fixtures=%s n=%d", path, len(items))
    n = 0
    for item in items:
        art = ScrapedArticle(
            source=item["source"],
            url=item["url"],
            titre=item["titre"],
            texte=item["texte"],
            date_publication=parse_date(item.get("date_publication"), "Europe/Paris"),
        )
        await store.upsert_article(art)
        n += 1
    log.info("demo upsert=%d", n)
    return n


def scrape_live(settings: Settings, source_id: str | None = None) -> int:
    """Crawl Scrapy bloquant (HTTP réel, robots, XPath, PostgreSQL)."""
    from sscraping.crawler.runner import run_crawl

    log.info("scrape live source_id=%s", source_id)
    return run_crawl(settings, source_id=source_id)


def make_connector(backend: str, settings: Settings):
    if backend == "grok":
        return GrokConnector(settings)
    if backend == "v100":
        return V100Connector(settings)
    raise ValueError("backend doit être grok ou v100")


async def run_analyze_only(settings: Settings, backend: str) -> dict[str, int]:
    store = Store(settings.database_url)
    await store.open()
    connector = make_connector(backend, settings)
    try:
        analyzed = await run_analyze(store, connector, settings)
        counts = await store.counts()
        counts.update({"analyzed": analyzed})
        return counts
    finally:
        await connector.aclose()
        await store.close()


async def run_demo_then_analyze(settings: Settings, backend: str) -> dict[str, int]:
    store = Store(settings.database_url)
    await store.open()
    try:
        scraped = await scrape_demo(store, settings)
        connector = make_connector(backend, settings)
        try:
            analyzed = await run_analyze(store, connector, settings)
        finally:
            await connector.aclose()
        counts = await store.counts()
        counts.update({"scraped": scraped, "analyzed": analyzed})
        return counts
    finally:
        await store.close()
