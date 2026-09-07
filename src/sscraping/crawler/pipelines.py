"""Pipelines Scrapy : log item + upsert PostgreSQL (psycopg sync)."""

from __future__ import annotations

import logging

from psycopg import connect
from psycopg.rows import dict_row

from sscraping.db import sql as Q
from sscraping.db.store import _redact_dsn, _split_sql, SCHEMA_PATH

log = logging.getLogger("sscraping.sql")
clog = logging.getLogger("sscraping.crawler")


class LogItemPipeline:
    def process_item(self, item, spider):
        clog.debug(
            "ITEM spider=%s url=%s titre=%r chars=%d statut=%s",
            spider.name,
            item.get("url"),
            (item.get("titre") or "")[:80],
            len(item.get("texte") or ""),
            item.get("statut"),
        )
        return item


class PostgresPipeline:
    total_upserts = 0

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._conn = None
        self.upserts = 0

    @classmethod
    def from_crawler(cls, crawler):
        dsn = crawler.settings.get("DATABASE_URL")
        if not dsn:
            raise ValueError("DATABASE_URL manquant dans les settings Scrapy")
        return cls(dsn)

    def open_spider(self, spider):
        log.info("pipeline PG open dsn=%s spider=%s", _redact_dsn(self.dsn), spider.name)
        self._conn = connect(self.dsn, row_factory=dict_row, autocommit=False)
        for stmt in _split_sql(SCHEMA_PATH.read_text(encoding="utf-8")):
            self._conn.execute(stmt)
        self._conn.commit()

    def close_spider(self, spider):
        log.info("pipeline PG close spider=%s upserts=%d", spider.name, self.upserts)
        if self._conn:
            self._conn.close()
            self._conn = None

    def process_item(self, item, spider):
        assert self._conn is not None
        log.debug("SQL UPSERT url=%s", item.get("url"))
        cur = self._conn.execute(
            Q.UPSERT_ARTICLE,
            (
                item.get("source"),
                item.get("url"),
                item.get("titre") or "",
                item.get("texte") or "",
                item.get("date_publication"),
                item.get("statut") or "ok",
                item.get("error"),
            ),
        )
        row = cur.fetchone()
        self._conn.commit()
        self.upserts += 1
        PostgresPipeline.total_upserts += 1
        article_id = int(row["id"]) if row else None
        log.info("SQL OK id=%s url=%s upserts=%d", article_id, item.get("url"), self.upserts)
        spider.crawler.stats.inc_value("sscraping/pg_upserts")
        return item
