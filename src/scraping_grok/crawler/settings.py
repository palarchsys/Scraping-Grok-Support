"""Settings Scrapy verbeux. Surchargés par runner.py depuis scraping_grok.settings."""

BOT_NAME = "scraping_grok"
SPIDER_MODULES = ["scraping_grok.crawler.spiders"]
NEWSPIDER_MODULE = "scraping_grok.crawler.spiders"

ROBOTSTXT_OBEY = True
COOKIES_ENABLED = True
COOKIES_DEBUG = False
TELNETCONSOLE_ENABLED = False

CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 0.5
RANDOMIZE_DOWNLOAD_DELAY = False
DOWNLOAD_TIMEOUT = 20
DOWNLOAD_MAXSIZE = 2_000_000
RETRY_ENABLED = True
RETRY_TIMES = 4
RETRY_HTTP_CODES = [429, 500, 502, 503, 504]

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_DEBUG = False
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 8
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

LOG_ENABLED = True
LOG_LEVEL = "DEBUG"
LOG_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)-8s [%(name)s] %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"
LOGSTATS_INTERVAL = 10.0

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

DOWNLOADER_MIDDLEWARES = {
    "scraping_grok.crawler.middlewares.VerboseDownloadMiddleware": 543,
}

ITEM_PIPELINES = {
    "scraping_grok.crawler.pipelines.LogItemPipeline": 100,
    "scraping_grok.crawler.pipelines.PostgresPipeline": 300,
}

EXTENSIONS = {
    "scraping_grok.crawler.extensions.RunReport": 500,
    "scrapy.extensions.telnet.TelnetConsole": None,
}

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_IGNORE_HTTP_CODES = [401, 403, 404, 429, 500, 502, 503, 504]
DNS_TIMEOUT = 10
