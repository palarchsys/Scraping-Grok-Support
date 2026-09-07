"""Respect robots.txt — obligatoire même en démo live.

On cache par netloc pour ne pas refetch à chaque article.
"""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from scraping_grok.http.client import HttpClient

log = logging.getLogger(__name__)


class RobotsCache:
    def __init__(self, client: HttpClient, user_agent: str) -> None:
        self._client = client
        self._ua = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    async def allowed(self, url: str) -> bool:
        host = urlparse(url).netloc
        parser = self._parsers.get(host)
        if parser is None:
            robots_url = urljoin(f"{urlparse(url).scheme}://{host}", "/robots.txt")
            parser = RobotFileParser()
            try:
                text = await self._client.get_text(robots_url)
                parser.parse(text.splitlines())
            except Exception as exc:  # noqa: BLE001 — robots injoignable = on continue prudemment
                log.info("robots.txt absent/injoignable %s (%s) — on autorise avec délai", robots_url, exc)
                parser.parse(["User-agent: *", "Allow: /"])
            self._parsers[host] = parser
        return parser.can_fetch(self._ua, url)
