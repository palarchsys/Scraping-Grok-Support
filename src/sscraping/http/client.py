"""Client HTTP unique : HTTP/2, retry, timeout, UA projet.

Pourquoi httpx async : un event loop scrape N sources sans thread. HTTP/2 multiplexe
quand le serveur le parle ; sinon HTTP/1.1 keep-alive.
"""

from __future__ import annotations

import asyncio
import logging

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from sscraping.settings import Settings

log = logging.getLogger(__name__)

RETRY_STATUS = {429, 500, 502, 503, 504}


class TransientHttp(Exception):
    """Erreur qu'on a intérêt à rejouer (429 / 5xx / réseau)."""


class HttpClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            http2=True,
            follow_redirects=True,
            timeout=httpx.Timeout(settings.request_timeout),
            headers={"User-Agent": settings.user_agent, "Accept": "*/*"},
            limits=httpx.Limits(max_connections=settings.concurrency + 4, max_keepalive_connections=settings.concurrency),
        )
        self._sem = asyncio.Semaphore(settings.concurrency)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> HttpClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    @retry(
        retry=retry_if_exception_type((TransientHttp, httpx.TransportError)),
        wait=wait_exponential(multiplier=0.4, min=0.4, max=8),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    async def get_text(self, url: str) -> str:
        async with self._sem:
            try:
                resp = await self._client.get(url)
            except httpx.TransportError as exc:
                log.warning("transport %s: %s", url, exc)
                raise
            if resp.status_code in RETRY_STATUS:
                raise TransientHttp(f"{resp.status_code} {url}")
            resp.raise_for_status()
            return resp.text
