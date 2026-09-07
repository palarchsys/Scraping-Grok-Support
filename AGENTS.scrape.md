# Étape 1 scrape — contrat court

Entrée : `config/sources.yaml`. Sortie : table `articles`.

## Flux
`sources.load → robots.allow → GET listing RSS → parse items → (optionnel) GET article HTML → normalize → store.upsert_article`

## Champs obligatoires
titre, texte, url (UNIQUE), date_publication (UTC aware). texte peut être le résumé RSS si corps HTML vide.

## Perf
- Un `HttpClient` partagé, HTTP/2, pool, timeout, retry 429/5xx expo (tenacity).
- Semaphore `settings.concurrency` (défaut 8).
- selectolax, pas BeautifulSoup.
- RSS lxml. Pas de Playwright sauf source `js: true`.

## Dates
dateparser/dateutil + timezone source (souvent Europe/Paris). Relatif (« hier ») → ancré `now`.

## Erreurs
Log + `statut=erreur`. Ne jamais planter le batch. robots.txt deny → skip source.

## Tests
Fixtures HTML/RSS dans `fixtures/`. Zéro réseau en pytest.
