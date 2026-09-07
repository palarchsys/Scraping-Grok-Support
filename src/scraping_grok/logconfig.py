"""Logs verbeux : console + fichiers rotatifs (scraping_grok / scrapy / sql / nlp)."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

FMT = "%(asctime)s.%(msecs)03d %(levelname)-8s [%(name)s] %(filename)s:%(lineno)d %(funcName)s — %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_dir: Path, *, quiet: bool = False, level: str = "DEBUG") -> None:
    """À appeler une fois au boot CLI. quiet=INFO, sinon DEBUG partout sauf twisted."""
    log_dir.mkdir(parents=True, exist_ok=True)
    root_level = logging.INFO if quiet else getattr(logging, level.upper(), logging.DEBUG)

    def _file(name: str) -> RotatingFileHandler:
        h = RotatingFileHandler(
            log_dir / name,
            maxBytes=5_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        h.setFormatter(logging.Formatter(FMT, DATEFMT))
        h.setLevel(logging.DEBUG)
        return h

    console = logging.StreamHandler()
    console.setLevel(root_level)
    console.setFormatter(logging.Formatter(FMT, DATEFMT))

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)
    root.addHandler(console)
    root.addHandler(_file("scraping_grok.log"))

    sql_h = _file("sql.log")
    sql = logging.getLogger("scraping_grok.sql")
    sql.addHandler(sql_h)
    sql.setLevel(logging.DEBUG)
    sql.propagate = True

    nlp_h = _file("nlp.log")
    nlp = logging.getLogger("scraping_grok.nlp")
    nlp.addHandler(nlp_h)
    nlp.setLevel(logging.DEBUG)
    nlp.propagate = True

    scrapy_h = _file("scrapy.log")
    for name in ("scrapy", "scraping_grok.crawler"):
        lg = logging.getLogger(name)
        lg.addHandler(scrapy_h)
        lg.setLevel(logging.DEBUG)
        lg.propagate = True

    logging.getLogger("twisted").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.DEBUG if not quiet else logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.INFO)
    logging.getLogger(__name__).debug("logging prêt dir=%s level=%s", log_dir, logging.getLevelName(root_level))
