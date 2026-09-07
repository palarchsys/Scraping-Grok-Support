from pathlib import Path

from sscraping.scrape.base import ScrapedArticle
from sscraping.scrape.site import next_page_url, parse_article_page, parse_listing
from sscraping.scrape.sources import load_sources, Source, ListingXPath, ArticleXPath, Pagination

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
        listing=ListingXPath(
            item="//article",
            url=".//a/@href",
            title=".//h2",
            date=".//time/@datetime",
        ),
        article=ArticleXPath(title="//h1", body="//article", date="//time/@datetime"),
    )


def test_load_sites_yaml() -> None:
    path = Path(__file__).resolve().parents[1] / "config" / "sources.yaml"
    sites = load_sources(path)
    assert sites
    html_ones = [s for s in sites if s.kind == "html"]
    assert html_ones[0].listing.url
    assert html_ones[0].article.body
    assert html_ones[0].pagination.next


def test_parse_listing_and_next() -> None:
    src = _src()
    html = (FIX / "list-1.html").read_text(encoding="utf-8")
    arts = parse_listing(html, "https://example.invalid/list-1.html", src)
    assert len(arts) == 2
    assert arts[0].url.endswith("/a.html")
    assert "Agression" in arts[0].titre
    nxt = next_page_url(html, "https://example.invalid/list-1.html", src, 1)
    assert nxt == "https://example.invalid/list-2.html"


def test_parse_article_xpath() -> None:
    src = _src()
    html = (FIX / "a.html").read_text(encoding="utf-8")
    art = ScrapedArticle(source="demo", url="https://example.invalid/a.html", titre="", texte="", date_publication=None)
    parse_article_page(html, art, src)
    assert art.titre.startswith("Agression")
    assert "agressé" in art.texte
    assert art.date_publication is not None


def test_page_url_template() -> None:
    src = _src()
    src.pagination = Pagination(page_url="https://example.invalid/liste?page={page}", page_start=1, max_pages=3)
    nxt = next_page_url("<html></html>", "https://example.invalid/liste?page=1", src, 1)
    assert nxt == "https://example.invalid/liste?page=2"
