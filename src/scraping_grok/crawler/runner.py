"""Lance Scrapy (processus bloquant). Un CrawlerProcess par run live."""

from __future__ import annotations

import logging

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings as ScrapySettings

from scraping_grok.crawler.spiders.rss import RssSpider
from scraping_grok.crawler.spiders.site import SiteSpider
from scraping_grok.scrape.sources import load_sources
from scraping_grok.settings import Settings

log = logging.getLogger("scraping_grok.crawler")


def scrapy_settings(app: Settings) -> ScrapySettings:
    st = ScrapySettings()
    st.setmodule("scraping_grok.crawler.settings")
    st.set("DATABASE_URL", app.database_url, priority="cmdline")
    st.set("SS_LOG_DIR", str(app.log_dir), priority="cmdline")
    st.set("USER_AGENT", app.user_agent, priority="cmdline")
    st.set("CONCURRENT_REQUESTS", app.concurrency, priority="cmdline")
    st.set("DOWNLOAD_TIMEOUT", app.request_timeout, priority="cmdline")
    st.set("LOG_LEVEL", "INFO" if app.log_quiet else "DEBUG", priority="cmdline")
    app.log_dir.mkdir(parents=True, exist_ok=True)
    st.set("LOG_FILE", str(app.log_dir / "scrapy-engine.log"), priority="cmdline")
    st.set("LOG_FILE_APPEND", True, priority="cmdline")
    return st


def run_crawl(app: Settings, source_id: str | None = None) -> int:
    """Crawl live. Retourne item_scraped_count (somme des spiders)."""
    sources = [s for s in load_sources(app.config_dir / "sources.yaml") if s.enabled]
    if source_id:
        sources = [s for s in sources if s.id == source_id]
        if not sources:
            raise SystemExit(f"source inconnue ou disabled: {source_id}")
    if not sources:
        log.warning("aucune source enabled dans sources.yaml")
        return 0

    from scraping_grok.crawler.known import load_known_urls
    from scraping_grok.crawler.pipelines import PostgresPipeline

    known = load_known_urls(app.database_url)
    PostgresPipeline.total_upserts = 0
    settings = scrapy_settings(app)
    process = CrawlerProcess(settings, install_root_handler=False)
    for src in sources:
        spider = RssSpider if src.kind == "rss" else SiteSpider
        log.info(
            "schedule spider kind=%s id=%s delay=%.2f listing=%s known=%d",
            src.kind,
            src.id,
            src.delay_s,
            src.listing_url,
            len(known),
        )
        process.crawl(spider, source=src, app_settings=app, known_urls=known)
    log.info("CrawlerProcess.start sources=%d", len(sources))
    process.start()
    total = int(PostgresPipeline.total_upserts)
    for crawler in getattr(process, "crawlers", []):
        n = crawler.stats.get_value("item_scraped_count") or 0
        ups = crawler.stats.get_value("scraping_grok/pg_upserts") or 0
        log.info("stats spider=%s items=%s pg_upserts=%s", getattr(crawler.spider, "name", "?"), n, ups)
    log.info("crawl terminé items/upserts=%d", total)
    return total
