"""CLI pédagogique : scrape / analyze / run / stats / triage / db-init."""

from __future__ import annotations

import asyncio
import logging

import typer

from scraping_grok.logconfig import setup_logging
from scraping_grok.settings import get_settings

app = typer.Typer(add_completion=False, no_args_is_help=True, help="Scraping Grok Support (démo pédagogique)")
log = logging.getLogger("scraping_grok")


def _boot(quiet: bool) -> None:
    settings = get_settings()
    setup_logging(settings.log_dir, quiet=quiet)
    log.info("boot quiet=%s database_url set=%s", quiet, bool(settings.database_url))


@app.command()
def scrape(
    live: bool = typer.Option(False, "--live", help="HTTP réel via Scrapy. Défaut = fixtures démo."),
    source: str | None = typer.Option(None, "--source", help="id d'un bloc sources.yaml"),
    quiet: bool = typer.Option(False, "--quiet", help="INFO au lieu de DEBUG"),
) -> None:
    """Étape 1 : titre, texte, url, date_publication → PostgreSQL."""
    _boot(quiet)
    settings = get_settings()
    settings.log_quiet = quiet
    if live:
        settings.demo = False
        from scraping_grok.pipeline import scrape_live

        n = scrape_live(settings, source_id=source)
        typer.echo(f"articles scrapy: {n}")
        return

    async def _run() -> None:
        from scraping_grok.db.store import Store
        from scraping_grok.pipeline import scrape_demo

        store = Store(settings.database_url)
        await store.open()
        try:
            n = await scrape_demo(store, settings)
            typer.echo(f"articles upsert: {n}")
        finally:
            await store.close()

    asyncio.run(_run())


@app.command()
def analyze(quiet: bool = typer.Option(False, "--quiet")) -> None:
    """Étape 2 : classification + extraction Grok + groupage des faits."""
    _boot(quiet)
    settings = get_settings()

    async def _run() -> None:
        from scraping_grok.pipeline import run_analyze_only

        counts = await run_analyze_only(settings)
        typer.echo(f"analysés via grok | {counts}")

    asyncio.run(_run())


@app.command()
def run(
    live: bool = typer.Option(False, "--live"),
    source: str | None = typer.Option(None, "--source"),
    quiet: bool = typer.Option(False, "--quiet"),
) -> None:
    """Étape 1 puis étape 2 (Grok)."""
    _boot(quiet)
    settings = get_settings()
    settings.log_quiet = quiet
    if live:
        from scraping_grok.pipeline import scrape_live

        scraped = scrape_live(settings, source_id=source)
        from scraping_grok.pipeline import run_analyze_only

        counts = asyncio.run(run_analyze_only(settings))
        counts["scraped"] = scraped
        typer.echo(counts)
        return

    async def _run() -> None:
        from scraping_grok.pipeline import run_demo_then_analyze

        typer.echo(await run_demo_then_analyze(settings))

    asyncio.run(_run())


@app.command()
def triage(quiet: bool = typer.Option(False, "--quiet")) -> None:
    """Regroupe les incidents (même nom, prénom, date des faits)."""
    _boot(quiet)
    settings = get_settings()

    async def _run() -> None:
        from scraping_grok.db.store import Store

        store = Store(settings.database_url)
        await store.open()
        try:
            n = await store.triage()
            typer.echo({"rattaches": n, **(await store.counts())})
        finally:
            await store.close()

    asyncio.run(_run())


@app.command()
def stats(quiet: bool = typer.Option(False, "--quiet")) -> None:
    """Comptages PostgreSQL."""
    _boot(quiet)
    settings = get_settings()

    async def _run() -> None:
        from scraping_grok.db.store import Store

        store = Store(settings.database_url)
        await store.open()
        try:
            typer.echo(await store.counts())
        finally:
            await store.close()

    asyncio.run(_run())


@app.command("db-init")
def db_init(quiet: bool = typer.Option(False, "--quiet")) -> None:
    """Applique schema.sql sur DATABASE_URL."""
    _boot(quiet)
    settings = get_settings()

    async def _run() -> None:
        from scraping_grok.db.store import Store

        store = Store(settings.database_url)
        await store.open()
        await store.close()
        typer.echo("schema OK")

    asyncio.run(_run())


@app.command()
def probe(
    source: str | None = typer.Option(None, "--source", help="id d'un bloc sources.yaml"),
    listing: str | None = typer.Option(None, "--listing", help="URL de liste"),
    article: str | None = typer.Option(None, "--article", help="URL d'un article"),
    save: bool = typer.Option(False, "--save", help="Sauver HTML dans fixtures/html/probe/"),
    quiet: bool = typer.Option(False, "--quiet"),
) -> None:
    """Teste les XPath d'un site (1 listing + 1 article) sans écrire en base."""
    _boot(quiet)
    settings = get_settings()
    from scraping_grok.crawler.probe import fetch, probe_html, save_snapshot
    from scraping_grok.scrape.sources import load_sources

    srcs = load_sources(settings.config_dir / "sources.yaml")
    src = next((s for s in srcs if s.id == source), None) if source else None
    if source and src is None:
        raise typer.BadParameter(f"source inconnue: {source}")
    if src is None:
        if not listing:
            raise typer.BadParameter("fournir --source ou --listing")
        from scraping_grok.scrape.sources import ArticleXPath, ListingXPath, Pagination, Source

        src = Source(
            id="adhoc",
            kind="html",
            listing_url=listing,
            enabled=True,
            timezone="Europe/Paris",
            delay_s=0.5,
            pagination=Pagination(),
            listing=ListingXPath(item="//article", url=".//a/@href", title=".//h2|.//h1"),
            article=ArticleXPath(title="//h1", body="//article"),
        )
    listing_url = listing or src.listing_url
    listing_html = fetch(listing_url, settings.user_agent)[1]
    article_html = None
    article_url = article
    report_tmp = probe_html(src, listing_html, listing_url)
    if not article_url and report_tmp["sample"]:
        article_url = report_tmp["sample"][0]["url"]
    if article_url:
        article_html = fetch(article_url, settings.user_agent)[1]
    report = probe_html(src, listing_html, listing_url, article_html, article_url)
    if save:
        report["snapshot"] = str(save_snapshot(src.id, listing_html, article_html))
    typer.echo(report)


if __name__ == "__main__":
    app()

