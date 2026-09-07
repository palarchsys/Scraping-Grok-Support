from pathlib import Path

from scraping_grok.crawler.probe import probe_html, wall_suspect
from scraping_grok.scrape.sources import ArticleXPath, ListingXPath, Pagination, Source

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


def test_probe_listing_and_article() -> None:
    listing = (FIX / "list-1.html").read_text(encoding="utf-8")
    article = (FIX / "a.html").read_text(encoding="utf-8")
    report = probe_html(
        _src(),
        listing,
        "https://example.invalid/list-1.html",
        article,
        "https://example.invalid/a.html",
    )
    assert report["cards"] == 2
    assert report["xpath_empty"] is False
    assert report["article"]["chars"] > 20
    assert report["playwright_suggere"] is False


def test_wall_suspect() -> None:
    assert wall_suspect("<html>didomi consent" + "x" * 100, "x" * 50)
    assert wall_suspect("<html>" + "nav " * 3000, "ok")
    assert not wall_suspect("<html><article>Un homme a été agressé à coups de poing. Texte pédagogique.</article></html>", "Un homme a été agressé à coups de poing. Texte pédagogique.")
