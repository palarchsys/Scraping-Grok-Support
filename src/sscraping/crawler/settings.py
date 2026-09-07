"""Settings Scrapy verbeux. Surchargés par runner.py depuis sscraping.settings."""

BOT_NAME = "sscraping"
SPIDER_MODULES = ["sscraping.crawler.spiders"]
NEWSPIDER_MODULE = "sscraping.crawler.spiders"

ROBOTSTXT_OBEY = True
COOKIES_ENABLED = True
COOKIES_DEBUG = True
TELNETCONSOLE_ENABLED = False

CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 0.5
RANDOMIZE_DOWNLOAD_DELAY = False
DOWNLOAD_TIMEOUT = 20
DOWNLOAD_MAXSIZE = 10_000_000
RETRY_ENABLED = True
RETRY_TIMES = 4
RETRY_HTTP_CODES = [429, 500, 502, 503, 504]

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_DEBUG = True
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
    "sscraping.crawler.middlewares.VerboseDownloadMiddleware": 543,
}

ITEM_PIPELINES = {
    "sscraping.crawler.pipelines.LogItemPipeline": 100,
    "sscraping.crawler.pipelines.PostgresPipeline": 300,
}

EXTENSIONS = {
    "sscraping.crawler.extensions.RunReport": 500,
    "scrapy.extensions.telnet.TelnetConsole": None,
}

HTTPCACHE_ENABLED = False
DNS_TIMEOUT = 10
