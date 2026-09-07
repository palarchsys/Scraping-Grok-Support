"""Spider générique : un bloc YAML = un crawl (liste paginée → articles)."""

from __future__ import annotations

import logging

import scrapy

from sscraping.crawler.extract import next_page_url, parse_article, parse_listing
from sscraping.crawler.items import ArticleItem
from sscraping.scrape.sources import Source
from sscraping.settings import Settings

log = logging.getLogger("sscraping.crawler")


class SiteSpider(scrapy.Spider):
    name = "site"

    def __init__(self, source: Source, app_settings: Settings, **kwargs):
        super().__init__(name=f"site-{source.id}", **kwargs)
        self.source = source
        self.app_settings = app_settings
        self.seen_article_urls: set[str] = set()
        self.scheduled = 0
        self.pages = 0
        self.download_delay = source.delay_s

    def start_requests(self):
        src = self.source
        url = src.listing_url
        if src.pagination.page_url and "{page}" in src.pagination.page_url and not src.pagination.next:
            url = src.pagination.page_url.format(page=src.pagination.page_start)
        log.info(
            "START spider=%s kind=%s listing=%s delay=%.2fs max_pages=%s max_articles=%s",
            self.name,
            src.kind,
            url,
            src.delay_s,
            src.pagination.max_pages,
            self.app_settings.max_articles,
        )
        yield scrapy.Request(
            url,
            callback=self.parse_listing,
            errback=self.errback,
            meta={"page": 1, "source_id": src.id},
            dont_filter=False,
        )

    def parse_listing(self, response: scrapy.http.Response):
        page = int(response.meta.get("page", 1))
        self.pages += 1
        log.info(
            "LISTING spider=%s page=%d status=%s url=%s bytes=%d encoding=%s",
            self.name,
            page,
            response.status,
            response.url,
            len(response.body),
            response.encoding,
        )
        teasers = parse_listing(response.text, response.url, self.source)
        for art in teasers:
            if art.url in self.seen_article_urls:
                continue
            if self.scheduled >= self.app_settings.max_articles:
                log.info("plafond max_articles=%s — stop scheduling", self.app_settings.max_articles)
                break
            self.seen_article_urls.add(art.url)
            self.scheduled += 1
            log.debug("SCHEDULE article #%d %s", self.scheduled, art.url)
            yield scrapy.Request(
                art.url,
                callback=self.parse_article,
                errback=self.errback,
                cb_kwargs={"teaser": art},
                meta={"source_id": self.source.id},
            )

        if self.scheduled >= self.app_settings.max_articles:
            return
        if page >= self.source.pagination.max_pages:
            log.info("plafond max_pages=%s", self.source.pagination.max_pages)
            return
        nxt = next_page_url(response.text, response.url, self.source, page)
        if not nxt:
            log.info("pas de page suivante après %s", response.url)
            return
        log.info("FOLLOW next page=%d %s", page + 1, nxt)
        yield scrapy.Request(
            nxt,
            callback=self.parse_listing,
            errback=self.errback,
            meta={"page": page + 1, "source_id": self.source.id},
        )

    def parse_article(self, response: scrapy.http.Response, teaser):
        log.info(
            "ARTICLE spider=%s status=%s url=%s bytes=%d",
            self.name,
            response.status,
            response.url,
            len(response.body),
        )
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
        yield ArticleItem(
            source=self.source.id,
            url=failure.request.url,
            titre=failure.request.url,
            texte="",
            date_publication=None,
            statut="erreur",
            error=str(failure.value)[:500],
        )

    def closed(self, reason: str) -> None:
        log.info(
            "CLOSED spider=%s reason=%s pages=%d scheduled=%d",
            self.name,
            reason,
            self.pages,
            self.scheduled,
        )
        if self.scheduled == 0:
            log.warning("spider=%s zéro article — vérifier XPath / robots / listing_url", self.name)
