"""Dump des stats Scrapy en fin de run (fichier + log)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from scrapy import signals

log = logging.getLogger("sscraping.crawler")


class RunReport:
    def __init__(self, log_dir: str) -> None:
        self.log_dir = Path(log_dir)
        self.started = datetime.now(timezone.utc)

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler.settings.get("SS_LOG_DIR") or "logs")
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.engine_started, signal=signals.engine_started)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.item_dropped, signal=signals.item_dropped)
        return ext

    def engine_started(self):
        log.info("engine started")

    def item_scraped(self, item, response, spider):
        log.debug("signal item_scraped spider=%s url=%s", spider.name, item.get("url"))

    def item_dropped(self, item, spider, exception):
        log.warning("ITEM DROPPED spider=%s url=%s err=%s", spider.name, item.get("url"), exception)

    def spider_closed(self, spider, reason):
        stats = spider.crawler.stats.get_stats()
        serial = {str(k): _jsonable(v) for k, v in stats.items()}
        report = {
            "spider": spider.name,
            "reason": reason,
            "started": self.started.isoformat(),
            "ended": datetime.now(timezone.utc).isoformat(),
            "stats": serial,
        }
        self.log_dir.mkdir(parents=True, exist_ok=True)
        path = self.log_dir / f"last_scrape_{spider.name}.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("REPORT %s reason=%s items=%s file=%s", spider.name, reason, serial.get("item_scraped_count"), path)
        log.debug("STATS %s", serial)


def _jsonable(v):
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)
