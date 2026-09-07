"""URLs déjà en PostgreSQL — évite un GET article inutile."""

from __future__ import annotations

import logging

from psycopg import connect

log = logging.getLogger("scraping_grok.crawler")


def load_known_urls(dsn: str) -> set[str]:
    try:
        with connect(dsn) as conn:
            rows = conn.execute("SELECT url FROM articles")
            urls = {r[0] for r in rows.fetchall() if r and r[0]}
        log.info("known urls in PG: %d", len(urls))
        return urls
    except Exception as exc:  # noqa: BLE001
        log.warning("known urls indisponible (%s) — crawl sans skip", exc)
        return set()
