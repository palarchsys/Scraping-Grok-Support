"""Orchestrateurs étape 1 (live + démo) et run complet."""

from __future__ import annotations

import asyncio
import json
import logging

from sscraping.db.store import Store
from sscraping.http.client import HttpClient
from sscraping.http.robots import RobotsCache
from sscraping.nlp.connectors.grok import GrokConnector
from sscraping.nlp.connectors.v100 import V100Connector
from sscraping.nlp.pipeline import run_analyze
from sscraping.scrape.base import ScrapedArticle
from sscraping.scrape.html import extract_article
from sscraping.scrape.normalize import parse_date
from sscraping.scrape.rss import parse_feed
from sscraping.scrape.sources import Source, load_sources
from sscraping.settings import Settings

log = logging.getLogger(__name__)


async def scrape_demo(store: Store, settings: Settings) -> int:
    """Charge fixtures/articles.json — zéro réseau. C'est le mode par défaut."""
    path = settings.fixtures_dir / "articles.json"
    items = json.loads(path.read_text(encoding="utf-8"))
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
    return n


async def _scrape_source(
    src: Source,
    http: HttpClient,
    robots: RobotsCache,
    store: Store,
    settings: Settings,
) -> int:
    if not await robots.allowed(src.listing):
        log.warning("robots deny listing %s", src.listing)
        return 0
    try:
        xml = await http.get_text(src.listing)
        articles = parse_feed(xml, src.id, src.timezone)[: settings.max_articles]
    except Exception as exc:  # noqa: BLE001
        log.exception("listing %s: %s", src.id, exc)
        return 0

    n = 0
    for art in articles:
        if not await robots.allowed(art.url):
            continue
        await asyncio.sleep(src.delay_s)
        if src.article_selectors:
            try:
                html = await http.get_text(art.url)
                title, body = extract_article(html, src.article_selectors)
                if title:
                    art.titre = title
                if body:
                    art.texte = body
            except Exception as exc:  # noqa: BLE001
                log.info("corps HTML raté %s: %s — on garde le résumé RSS", art.url, exc)
        await store.upsert_article(art)
        n += 1
    return n


async def scrape_live(store: Store, settings: Settings) -> int:
    """Sources en parallèle, items d'une source en série (politesse delay_s)."""
    sources = [s for s in load_sources(settings.config_dir / "sources.yaml") if s.enabled]
    async with HttpClient(settings) as http:
        robots = RobotsCache(http, settings.user_agent)
        counts = await asyncio.gather(
            *(_scrape_source(src, http, robots, store, settings) for src in sources)
        )
    return int(sum(counts))


def make_connector(backend: str, settings: Settings):
    if backend == "grok":
        return GrokConnector(settings)
    if backend == "v100":
        return V100Connector(settings)
    raise ValueError("backend doit être grok ou v100")


async def run_all(settings: Settings, backend: str, live: bool) -> dict[str, int]:
    store = Store(settings.db_path)
    await store.open()
    try:
        scraped = await (scrape_live(store, settings) if live else scrape_demo(store, settings))
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
