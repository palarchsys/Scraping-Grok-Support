"""Accès PostgreSQL async (psycopg). Identités stockées en clair."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from sscraping.db import sql as Q
from sscraping.nlp.schema import IncidentExtraction
from sscraping.scrape.base import ScrapedArticle

log = logging.getLogger("sscraping.sql")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _split_sql(blob: str) -> list[str]:
    stmts: list[str] = []
    buf: list[str] = []
    for line in blob.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            stmts.append("\n".join(buf).strip())
            buf = []
    return stmts


class Store:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._conn: AsyncConnection | None = None

    async def open(self) -> None:
        log.debug("connect %s", _redact_dsn(self._dsn))
        self._conn = await AsyncConnection.connect(self._dsn, row_factory=dict_row)
        await self.init_schema()

    async def init_schema(self) -> None:
        assert self._conn is not None
        raw = SCHEMA_PATH.read_text(encoding="utf-8")
        for stmt in _split_sql(raw):
            log.debug("DDL %s", stmt.split()[0:4])
            await self._conn.execute(stmt)
        await self._conn.commit()
        log.info("schema OK")

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None
            log.debug("connection closed")

    @property
    def db(self) -> AsyncConnection:
        assert self._conn is not None
        return self._conn

    async def upsert_article(self, art: ScrapedArticle) -> int:
        log.debug(
            "UPSERT article source=%s url=%s titre=%r chars=%d statut=%s",
            art.source,
            art.url,
            art.titre[:80],
            len(art.texte or ""),
            art.statut,
        )
        cur = await self.db.execute(
            Q.UPSERT_ARTICLE,
            (art.source, art.url, art.titre, art.texte, art.date_publication, art.statut, art.error),
        )
        row = await cur.fetchone()
        await self.db.commit()
        article_id = int(row["id"])
        log.info("article id=%s url=%s", article_id, art.url)
        return article_id

    async def pending_analysis(self, limit: int = 200) -> list[dict]:
        cur = await self.db.execute(Q.PENDING, (limit,))
        rows = await cur.fetchall()
        log.info("pending analysis=%d limit=%d", len(rows), limit)
        return list(rows)

    async def mark_analyzed(self, article_id: int, backend: str) -> None:
        log.debug("MARK analyzed id=%s backend=%s", article_id, backend)
        await self.db.execute(Q.MARK_ANALYZED, (backend, article_id))
        await self.db.commit()

    async def insert_incident(
        self,
        article_id: int,
        ext: IncidentExtraction,
        backend: str,
        raw: str,
    ) -> None:
        if not ext.is_aggression:
            log.debug("skip incident id=%s is_aggression=false", article_id)
            return
        log.info(
            "UPSERT incident article_id=%s cat=%s nom=%s prenom=%s age=%s conf=%.2f",
            article_id,
            ext.categorie,
            ext.agresseur.nom,
            ext.agresseur.prenom,
            ext.agresseur.age,
            ext.confidence,
        )
        await self.db.execute(
            Q.UPSERT_INCIDENT,
            (
                article_id,
                ext.categorie,
                ext.agresseur.nom,
                ext.agresseur.prenom,
                ext.agresseur.nationalite,
                ext.agresseur.age,
                ext.agresseur.pays_origine,
                ext.faits.annee,
                ext.faits.mois,
                ext.faits.jour,
                ext.confidence,
                json.dumps(ext.preuves, ensure_ascii=False),
                backend,
                raw,
            ),
        )
        await self.db.commit()

    async def counts(self) -> dict[str, int]:
        arts = (await (await self.db.execute("SELECT COUNT(*) AS n FROM articles")).fetchone())["n"]
        inc = (await (await self.db.execute("SELECT COUNT(*) AS n FROM incidents")).fetchone())["n"]
        pending = (
            await (
                await self.db.execute(
                    "SELECT COUNT(*) AS n FROM articles WHERE analyzed_at IS NULL AND statut='ok'"
                )
            ).fetchone()
        )["n"]
        out = {"articles": int(arts), "incidents": int(inc), "pending": int(pending)}
        log.info("counts %s", out)
        return out


def _redact_dsn(dsn: str) -> str:
    if "@" not in dsn or "://" not in dsn:
        return dsn
    head, tail = dsn.split("://", 1)
    if "@" in tail and ":" in tail.split("@", 1)[0]:
        user = tail.split(":", 1)[0]
        rest = tail.split("@", 1)[1]
        return f"{head}://{user}:***@{rest}"
    return dsn
