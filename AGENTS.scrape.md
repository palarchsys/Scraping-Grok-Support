# Étape 1 scrape — Scrapy + PostgreSQL

Entrée : `config/sources.yaml`. Sortie : table `articles`.
Live : spider générique (`crawler/spiders/site.py` ou `rss.py`). Demo : fixtures → Store.

## Inputs (bloc YAML)
`id`, `listing_url`, `kind` (html|rss), `pagination.next` XPath, `pagination.page_url`, `max_pages`, `listing.item|url|title|date`, `article.title|body|date`, `delay_s`.

## Flux html
`CrawlerProcess → robots.txt → GET listing → parsel XPath cartes → follow next (max_pages) → GET article → XPath → ArticleItem → PostgresPipeline UPSERT`

## Logs
DEBUG : REQ/RES (status, bytes, latency), XPath matches (0 = WARNING + snippet HTML), pagination, chaque UPSERT id, stats spider_closed → `logs/last_scrape_*.json`. Fichiers : `logs/scrapy.log`, `logs/sql.log`, `logs/scrapy-engine.log`.

## Perf
`CONCURRENT_REQUESTS_PER_DOMAIN=1`, `download_delay` = `delay_s` du bloc, AutoThrottle debug, retry 429/5xx. Sources = plusieurs spiders dans le même process.

## Tests
`fixtures/html/` zéro réseau (extract.py). Store PG skip si `DATABASE_URL` injoignable.
