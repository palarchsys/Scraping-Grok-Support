"""CLI pédagogique : scrape / analyze / run / stats / db-init."""

from __future__ import annotations

import asyncio
import logging

import typer

from sscraping.logconfig import setup_logging
from sscraping.settings import get_settings

app = typer.Typer(add_completion=False, no_args_is_help=True, help="ss-craping-bot (démo pédagogique)")
log = logging.getLogger("sscraping")


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
        from sscraping.pipeline import scrape_live

        n = scrape_live(settings, source_id=source)
        typer.echo(f"articles scrapy: {n}")
        return

    async def _run() -> None:
        from sscraping.db.store import Store
        from sscraping.pipeline import scrape_demo

        store = Store(settings.database_url)
        await store.open()
        try:
            n = await scrape_demo(store, settings)
            typer.echo(f"articles upsert: {n}")
        finally:
            await store.close()

    asyncio.run(_run())


@app.command()
def analyze(
    backend: str = typer.Option("grok", "--backend", help="grok | v100"),
    quiet: bool = typer.Option(False, "--quiet"),
) -> None:
    """Étape 2 : classification + extraction via le connecteur choisi."""
    _boot(quiet)
    if backend not in {"grok", "v100"}:
        raise typer.BadParameter("backend = grok | v100")
    settings = get_settings()

    async def _run() -> None:
        from sscraping.pipeline import run_analyze_only

        counts = await run_analyze_only(settings, backend)
        typer.echo(f"analysés: {counts.get('analyzed')} via {backend} | {counts}")

    asyncio.run(_run())


@app.command()
def run(
    backend: str = typer.Option("grok", "--backend"),
    live: bool = typer.Option(False, "--live"),
    source: str | None = typer.Option(None, "--source"),
    quiet: bool = typer.Option(False, "--quiet"),
) -> None:
    """Étape 1 puis étape 2. Live = Scrapy d'abord (reactor), puis asyncio NLP."""
    _boot(quiet)
    settings = get_settings()
    settings.log_quiet = quiet
    scraped = 0
    if live:
        from sscraping.pipeline import scrape_live

        scraped = scrape_live(settings, source_id=source)
        from sscraping.pipeline import run_analyze_only

        counts = asyncio.run(run_analyze_only(settings, backend))
        counts["scraped"] = scraped
        typer.echo(counts)
        return

    async def _run() -> None:
        from sscraping.pipeline import run_demo_then_analyze

        typer.echo(await run_demo_then_analyze(settings, backend))

    asyncio.run(_run())


@app.command()
def stats(quiet: bool = typer.Option(False, "--quiet")) -> None:
    """Comptages PostgreSQL."""
    _boot(quiet)
    settings = get_settings()

    async def _run() -> None:
        from sscraping.db.store import Store

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
        from sscraping.db.store import Store

        store = Store(settings.database_url)
        await store.open()
        await store.close()
        typer.echo("schema OK")

    asyncio.run(_run())


if __name__ == "__main__":
    app()
