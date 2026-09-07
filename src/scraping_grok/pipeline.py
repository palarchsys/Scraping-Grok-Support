"""Orchestrateurs étape 1 (live Scrapy + démo fixtures) et run complet."""

from __future__ import annotations

import json
import logging

from scraping_grok.db.store import Store
from scraping_grok.nlp.connectors.grok import GrokConnector
from scraping_grok.nlp.pipeline import run_analyze
from scraping_grok.scrape.base import ScrapedArticle
from scraping_grok.scrape.normalize import parse_date
from scraping_grok.settings import Settings

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
    from scraping_grok.crawler.runner import run_crawl

    log.info("scrape live source_id=%s", source_id)
    return run_crawl(settings, source_id=source_id)


def make_connector(settings: Settings) -> GrokConnector:
    return GrokConnector(settings)


async def run_analyze_only(settings: Settings) -> dict[str, int]:
    store = Store(settings.database_url)
    await store.open()
    connector = make_connector(settings)
    try:
        analyzed = await run_analyze(store, connector, settings)
        counts = await store.counts()
        counts.update({"analyzed": analyzed, **getattr(connector, "usage", {})})
        return counts
    finally:
        await connector.aclose()
        await store.close()


async def run_demo_then_analyze(settings: Settings) -> dict[str, int]:
    store = Store(settings.database_url)
    await store.open()
    try:
        scraped = await scrape_demo(store, settings)
        connector = make_connector(settings)
        try:
            analyzed = await run_analyze(store, connector, settings)
        finally:
            usage = getattr(connector, "usage", {})
            await connector.aclose()
        counts = await store.counts()
        counts.update({"scraped": scraped, "analyzed": analyzed, **usage})
        return counts
    finally:
        await store.close()
