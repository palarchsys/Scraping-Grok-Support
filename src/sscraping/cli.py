"""CLI pédagogique : scrape / analyze / run / stats."""

from __future__ import annotations

import asyncio
import logging

import typer

from sscraping.settings import get_settings

app = typer.Typer(add_completion=False, no_args_is_help=True, help="ss-craping-bot (démo pédagogique)")


def _setup_log() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@app.command()
def scrape(live: bool = typer.Option(False, "--live", help="HTTP réel. Défaut = fixtures démo.")) -> None:
    """Étape 1 : titre, texte, url, date_publication → SQLite."""
    _setup_log()
    settings = get_settings()
    if live:
        settings.demo = False

    async def _run() -> None:
        from sscraping.db.store import Store
        from sscraping.pipeline import scrape_demo, scrape_live

        store = Store(settings.db_path)
        await store.open()
        try:
            n = await (scrape_live(store, settings) if live else scrape_demo(store, settings))
            typer.echo(f"articles upsert: {n}")
        finally:
            await store.close()

    asyncio.run(_run())


@app.command()
def analyze(
    backend: str = typer.Option("grok", "--backend", help="grok | v100"),
) -> None:
    """Étape 2 : classification + extraction via le connecteur choisi."""
    _setup_log()
    if backend not in {"grok", "v100"}:
        raise typer.BadParameter("backend = grok | v100")
    settings = get_settings()

    async def _run() -> None:
        from sscraping.db.store import Store
        from sscraping.nlp.pipeline import run_analyze
        from sscraping.pipeline import make_connector

        store = Store(settings.db_path)
        await store.open()
        connector = make_connector(backend, settings)
        try:
            n = await run_analyze(store, connector, settings)
            typer.echo(f"analysés: {n} via {backend}")
        finally:
            await connector.aclose()
            await store.close()

    asyncio.run(_run())


@app.command()
def run(
    backend: str = typer.Option("grok", "--backend"),
    live: bool = typer.Option(False, "--live"),
) -> None:
    """Étape 1 puis étape 2."""
    _setup_log()
    settings = get_settings()

    async def _run() -> None:
        from sscraping.pipeline import run_all

        counts = await run_all(settings, backend, live)
        typer.echo(counts)

    asyncio.run(_run())


@app.command()
def stats() -> None:
    """Comptages SQL."""
    settings = get_settings()

    async def _run() -> None:
        from sscraping.db.store import Store

        store = Store(settings.db_path)
        await store.open()
        try:
            typer.echo(await store.counts())
        finally:
            await store.close()

    asyncio.run(_run())


if __name__ == "__main__":
    app()
