from pathlib import Path

import scrapy
from scrapy.http import HtmlResponse

from sscraping.crawler.spiders.site import SiteSpider
from sscraping.scrape.sources import ArticleXPath, ListingXPath, Pagination, Source
from sscraping.settings import Settings

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "html"


def _src() -> Source:
    return Source(
        id="demo",
        kind="html",
        listing_url="https://example.invalid/list-1.html",
        enabled=True,
        timezone="Europe/Paris",
        delay_s=0,
        pagination=Pagination(next="//a[@rel='next']/@href", max_pages=5),
        listing=ListingXPath(item="//article", url=".//a/@href", title=".//h2", date=".//time/@datetime"),
        article=ArticleXPath(title="//h1", body="//article", date="//time/@datetime"),
    )


def test_spider_listing_yields_article_and_next() -> None:
    spider = SiteSpider(source=_src(), app_settings=Settings(max_articles=50))
    url = "https://example.invalid/list-1.html"
    body = (FIX / "list-1.html").read_bytes()
    request = scrapy.Request(url, meta={"page": 1})
    resp = HtmlResponse(url=url, body=body, encoding="utf-8", request=request)
    reqs = list(spider.parse_listing(resp))
    urls = [r.url for r in reqs]
    assert any(u.endswith("/a.html") for u in urls)
    assert any(u.endswith("/b.html") for u in urls)
    assert any(u.endswith("/list-2.html") for u in urls)
