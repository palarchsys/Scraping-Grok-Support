"""Spider RSS : flux XML puis GET article (XPath intra-article si défini)."""

from __future__ import annotations

import logging

import scrapy

from scraping_grok.crawler.extract import parse_article
from scraping_grok.crawler.items import ArticleItem
from scraping_grok.scrape.rss import parse_feed
from scraping_grok.scrape.sources import Source
from scraping_grok.settings import Settings

log = logging.getLogger("scraping_grok.crawler")


class RssSpider(scrapy.Spider):
    name = "rss"

    def __init__(self, source: Source, app_settings: Settings, known_urls: set[str] | None = None, **kwargs):
        super().__init__(name=f"rss-{source.id}", **kwargs)
        self.source = source
        self.app_settings = app_settings
        self.scheduled = 0
        self.download_delay = source.delay_s
        self.known_urls: set[str] = set(known_urls or [])
        self.skipped_known = 0

    def start_requests(self):
        log.info("START rss spider=%s feed=%s", self.name, self.source.listing_url)
        yield scrapy.Request(
            self.source.listing_url,
            callback=self.parse_feed,
            errback=self.errback,
            meta={"source_id": self.source.id},
        )

    def parse_feed(self, response: scrapy.http.Response):
        log.info("FEED status=%s url=%s bytes=%d", response.status, response.url, len(response.body))
        items = parse_feed(response.text, self.source.id, self.source.timezone)
        log.info("FEED entries=%d", len(items))
        for art in items:
            if art.url in self.known_urls:
                self.skipped_known += 1
                log.info("SKIP already in PG %s", art.url)
                continue
            if self.scheduled >= self.app_settings.max_articles:
                log.info("plafond max_articles=%s", self.app_settings.max_articles)
                break
            self.scheduled += 1
            if self.source.article.title or self.source.article.body:
                log.debug("SCHEDULE rss article %s", art.url)
                yield scrapy.Request(
                    art.url,
                    callback=self.parse_article,
                    errback=self.errback,
                    cb_kwargs={"teaser": art},
                )
            else:
                log.debug("YIELD rss résumé %s", art.url)
                yield ArticleItem(
                    source=art.source,
                    url=art.url,
                    titre=art.titre,
                    texte=art.texte,
                    date_publication=art.date_publication,
                    statut=art.statut,
                    error=art.error,
                )

    def parse_article(self, response: scrapy.http.Response, teaser):
        art = parse_article(response.text, teaser, self.source)
        yield ArticleItem(
            source=art.source,
            url=art.url,
            titre=art.titre,
            texte=art.texte,
            date_publication=art.date_publication,
            statut=art.statut,
            error=art.error,
        )

    def errback(self, failure):
        log.error("REQUEST FAIL spider=%s url=%s err=%s", self.name, failure.request.url, failure.value)

    def closed(self, reason: str) -> None:
        log.info("CLOSED spider=%s reason=%s scheduled=%d skipped_known=%d", self.name, reason, self.scheduled, self.skipped_known)
