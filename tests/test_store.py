from pathlib import Path

import pytest

from sscraping.db.store import Store
from sscraping.scrape.base import ScrapedArticle


@pytest.mark.asyncio
async def test_upsert_idempotent(tmp_path: Path) -> None:
    store = Store(tmp_path / "t.db")
    await store.open()
    art = ScrapedArticle(
        source="demo",
        url="https://example.invalid/a",
        titre="T",
        texte="hello",
        date_publication=None,
    )
    a = await store.upsert_article(art)
    art.texte = "hello world plus long"
    b = await store.upsert_article(art)
    assert a == b
    row = await (await store.db.execute("SELECT texte FROM articles WHERE id=?", (a,))).fetchone()
    assert "plus long" in row["texte"]
    await store.close()
