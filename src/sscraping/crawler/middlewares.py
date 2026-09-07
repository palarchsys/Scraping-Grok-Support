"""Middleware downloader : chaque requête / réponse / retry est loguée."""

from __future__ import annotations

import logging
import time

log = logging.getLogger("sscraping.crawler")


class VerboseDownloadMiddleware:
    def process_request(self, request, spider):
        request.meta["ss_t0"] = time.perf_counter()
        log.debug(
            "REQ spider=%s method=%s url=%s headers=%s meta_page=%s",
            spider.name,
            request.method,
            request.url,
            {k.decode() if isinstance(k, bytes) else k: v for k, v in request.headers.items()},
            request.meta.get("page"),
        )

    def process_response(self, request, response, spider):
        dt = time.perf_counter() - float(request.meta.get("ss_t0", time.perf_counter()))
        log.info(
            "RES spider=%s status=%s url=%s bytes=%d latency=%.3fs flags=%s",
            spider.name,
            response.status,
            response.url,
            len(response.body),
            dt,
            response.flags,
        )
        if response.status >= 400:
            log.warning("HTTP %s %s body[:300]=%r", response.status, response.url, response.text[:300])
        return response

    def process_exception(self, request, exception, spider):
        log.error("EXC spider=%s url=%s %s: %s", spider.name, request.url, type(exception).__name__, exception)
