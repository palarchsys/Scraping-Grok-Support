# ss-craping-bot

Bot pédagogique en deux étapes : **collecte** d’articles de presse, puis **analyse** du sujet. Si le sujet n’est pas une forme d’agression, on passe. Sinon on extrait nom, prénom, nationalité, âge, pays d’origine, année / mois / jour des faits — vide si absent du texte.

La table `incidents` stocke ces champs **en clair** (ce que l’article écrit). Aucun masquage SQL. Une GUI future masquera à l’affichage ; elle n’est pas dans ce dépôt.

Dépôt public = code + installateur Ubuntu 26.04. `fixtures/` = corpus hors-ligne pour tests (pas un anonymiseur).

## Pourquoi cette stack

| Couche | Choix | Pourquoi |
|---|---|---|
| Crawl | Scrapy | robots, retry, délai, scheduler, logs DEBUG |
| HTML | parsel / XPath | listes paginées + intra-article |
| RSS | Scrapy + lxml | `kind: rss` optionnel |
| SQL | PostgreSQL + psycopg3 | identités en clair, upsert URL |
| NLP | asyncio + httpx | Grok API / V100 `/v1` |
| Logs | `logs/*.log` rotatifs | scrape / sql / nlp / scrapy |
| Contrat | pydantic v2 | JSON LLM refusé si hors schéma |
| CLI | typer | `sscraping scrape \| analyze \| run` |

Étape 2 **oui sur V100 32 Go** : 14B AWQ (vLLM) ou 14B GGUF Q4 (llama.cpp). Pas de 70B.

## Deux étapes

```
config/sources.yaml (blocs site)
        │
        ▼
   Scrapy (robots, delay, XPath pagination + article)
        │
        ▼
   articles PostgreSQL (titre, texte, url, date)
        │
        ▼
   préfiltre → Grok | V100 → incidents
```

## Inputs

| Input | Rôle |
|---|---|
| `config/sources.yaml` | **Blocs site** : `id`, `listing_url`, XPath pagination, XPath liste, XPath article |
| `config/taxonomy.yaml` | Labels d’agression + tokens préfiltre |
| `.env` | Clés, plafonds, backend |
| `fixtures/` | Hors-ligne (tests) — pas le crawl live |
| CLI | `scrape --live`, `analyze --backend grok\|v100` |

Exemple de bloc site :

```yaml
- id: francetvinfo_faits_divers
  kind: html
  listing_url: https://www.francetvinfo.fr/faits-divers/
  pagination:
    next: "//a[@rel='next']/@href"
    max_pages: 5
  listing:
    item: "//article"
    url: ".//a/@href"
    title: ".//h2"
    date: ".//time/@datetime"
  article:
    title: "//h1"
    body: "//div[contains(@class,'c-body')]"
    date: "//time/@datetime"
```

Pagination alternative : `pagination.page_url: "https://site/liste?page={page}"`.

### Étape 1 — scrape

Champs : `titre`, `texte`, `url` (unique), `date_publication`.

Défaut : fixtures locales, **zéro réseau**. Live : `sscraping scrape --live` (robots.txt, délais, plafond).

### Étape 2 — analyse

Deux connecteurs, **même** interface OpenAI `/v1/chat/completions` :

| `--backend` | Où | Matériel |
|---|---|---|
| `grok` | API xAI (`grok-4.5`) | aucune GPU |
| `v100` | `http://127.0.0.1:8000/v1` | NVIDIA V100 **32 Go** |

Préfiltre regex → LLM JSON → Pydantic → SQL. Identités stockées telles quelles. `confidence` est conservé à côté.

## Install Ubuntu 26.04

```bash
git clone https://github.com/palarchsys/ss-craping-bot.git
cd ss-craping-bot
chmod +x install.sh
./install.sh
# GPU local :
./install.sh --v100
```

Éditer `.env` : `DATABASE_URL=...` et `XAI_API_KEY=...` pour Grok.

```bash
source .venv/bin/activate
sscraping db-init
sscraping scrape                 # fixtures → PostgreSQL
sscraping scrape --live          # Scrapy, logs DEBUG dans logs/
sscraping analyze --backend grok
sscraping run --backend v100     # serveur local déjà lancé
sscraping stats
tail -f logs/sscraping.log logs/sql.log logs/scrapy.log
pytest -q
```

V100 :

```bash
./scripts/serve-v100.sh          # terminal dédié
sscraping analyze --backend v100
```

Live HTTP (opt-in) : `sscraping scrape --live`.

Autre OS (dev) : `ALLOW_OTHER_OS=1 ./install.sh`.

## Contrats agent (reprise de code, peu de tokens)

- [`AGENTS.md`](AGENTS.md) — stack, layout, règles
- [`AGENTS.scrape.md`](AGENTS.scrape.md) — étape 1
- [`AGENTS.nlp.md`](AGENTS.nlp.md) — étape 2 + V100
- [`AGENTS.install.md`](AGENTS.install.md) — Ubuntu 26.04 / GPU

## Licence

MIT. Usage démonstratif uniquement.
