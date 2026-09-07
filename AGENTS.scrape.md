# Étape 1 scrape — contrat court

Entrée principale : `config/sources.yaml` (alias `sites:`). Sortie : table `articles`.

## Inputs
Chaque bloc site :
- `id` — nom interne
- `listing_url` — URL de la **liste** d’articles
- `kind` — `html` (défaut, XPath) ou `rss`
- `pagination.next` — XPath du lien page suivante (`@href`)
- `pagination.page_url` — gabarit optionnel `.../{page}`
- `pagination.max_pages` — plafond
- `listing.item|url|title|date` — XPath de la liste (url obligatoire)
- `article.title|body|date` — XPath intra-article
- `delay_s`, `timezone`, `enabled`

Pas de nouveau site = pas de nouveau Python. Un YAML suffit.

## Flux html
`load sites → robots → GET listing → XPath cartes → next page (max_pages) → GET article → XPath titre/corps/date → upsert`

## Flux rss
`GET flux → parse items → (optionnel) GET article + XPath`

## Champs SQL
titre, texte, url UNIQUE, date_publication UTC.

## Perf
HttpClient partagé, HTTP/2, retry, semaphore. Sources en parallèle, pages/articles en série (`delay_s`). lxml XPath. Pas de Playwright sauf `js: true` (non implémenté v1).

## Tests
`fixtures/html/` + `fixtures/sample.rss.xml`. Zéro réseau en pytest.
