import os

import pytest

from sscraping.db.store import Store
from sscraping.scrape.base import ScrapedArticle

DSN = os.environ.get("DATABASE_URL", "postgresql://sscraping:sscraping@127.0.0.1:5432/sscraping")


async def _connect() -> Store | None:
    store = Store(DSN)
    try:
        await store.open()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"PostgreSQL indisponible: {exc}")
    return store


@pytest.mark.asyncio
async def test_upsert_idempotent() -> None:
    store = await _connect()
    assert store is not None
    try:
        art = ScrapedArticle(
            source="demo",
            url="https://example.invalid/a-pg-test",
            titre="T",
            texte="hello",
            date_publication=None,
        )
        a = await store.upsert_article(art)
        art.texte = "hello world plus long"
        b = await store.upsert_article(art)
        assert a == b
        cur = await store.db.execute("SELECT texte FROM articles WHERE id = %s", (a,))
        row = await cur.fetchone()
        assert "plus long" in row["texte"]
    finally:
        await store.close()
