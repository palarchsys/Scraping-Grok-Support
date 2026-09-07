# Scraping Grok Support

Bot pédagogique en deux étapes : **collecte** d’articles de presse, puis **analyse** du sujet. Si ce n’est pas un crime, on passe. Sinon on assigne **un des 8 groupes** et on extrait nom, prénom, nationalité, âge, pays d’origine, année / mois / jour des faits — vide si absent du texte.

La table `incidents` stocke ces champs **en clair** (ce que l’article écrit). Aucun masquage SQL. Une GUI future masquera à l’affichage ; elle n’est pas dans ce dépôt.

Dépôt public = code + installateur Ubuntu 26.04. `fixtures/` = corpus hors-ligne pour tests (pas un anonymiseur).

## Pourquoi cette stack

| Couche | Choix | Pourquoi |
|---|---|---|
| Crawl | Scrapy | robots, retry, délai, scheduler, logs DEBUG |
| HTML | parsel / XPath | listes paginées + intra-article |
| RSS | Scrapy + lxml | `kind: rss` optionnel |
| SQL | PostgreSQL + psycopg3 | identités en clair, upsert URL |
| NLP | asyncio + httpx | Grok API (`grok-4.5`) |
| Logs | `logs/*.log` rotatifs | scrape / sql / nlp / scrapy |
| Contrat | pydantic v2 | JSON LLM refusé si hors schéma |
| CLI | typer | `scraping-grok scrape \| analyze \| run` |

Étape 2 : Grok uniquement. Prompt compressé (lead + phrases clés), `max_tokens=280`.

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
   préfiltre → Grok → incidents → faits (nom+prénom+date)
```

## Inputs

| Input | Rôle |
|---|---|
| `config/sources.yaml` | **Blocs site** : `id`, `listing_url`, XPath pagination, XPath liste, XPath article |
| `config/taxonomy.yaml` | 8 groupes de crime + tokens préfiltre |
| `.env` | Clés, plafonds, backend |
| `fixtures/` | Hors-ligne (tests) — pas le crawl live |
| CLI | `scrape --live`, `analyze`, `triage` |

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

Défaut : fixtures locales, **zéro réseau**. Live : `scraping-grok scrape --live` (robots.txt, délais, plafond).

### Étape 2 — analyse

Connecteur unique : API xAI `grok-4.5`. Préfiltre (1 fort / 2 faibles) → texte compressé ≤1800c → JSON court (`max_tokens=280`) → preuves locales.

`is_crime` + `type_crime` (8 groupes). Puis **triage** : un `fait` = même nom + prénom + date (normalisés). Sans les trois, pas de fusion.

Identités en clair. `confidence` conservé.

| `type_crime` | Couvre |
|---|---|
| `atteintes_vie` | homicides, assassinats, tentatives |
| `violences_personnes` | coups, séquestration, menaces de mort |
| `atteintes_sexuelles` | viol, agressions sexuelles |
| `atteintes_biens` | vol, cambriolage, incendie, extorsion |
| `stupefiants` | trafic, production, usage |
| `criminalite_economique` | escroquerie, fraude, cyberarnaque |
| `circulation_securite` | accidents graves, délit de fuite |
| `ordre_public_surete` | terrorisme, otage, armes, le reste |

## Install Ubuntu 26.04

```bash
git clone https://github.com/palarchsys/Scraping-Grok-Support.git
cd Scraping-Grok-Support
chmod +x install.sh
./install.sh
```

Éditer `.env` : `DATABASE_URL=...` et `XAI_API_KEY=...`.

```bash
source .venv/bin/activate
scraping-grok db-init
scraping-grok scrape
sscraping-grok scrape --live
scraping-grok analyze
scraping-grok probe --source francetvinfo_faits_divers
scraping-grok triage
scraping-grok stats
pytest -q
```

Live HTTP (opt-in) : `scraping-grok scrape --live` (skip URL déjà en base, y compris ignored).

Autre OS (dev) : `ALLOW_OTHER_OS=1 ./install.sh`.

## Contrats agent (reprise de code, peu de tokens)

- [`AGENTS.md`](AGENTS.md) — stack, layout, règles
- [`AGENTS.scrape.md`](AGENTS.scrape.md) — étape 1
- [`AGENTS.nlp.md`](AGENTS.nlp.md) — étape 2 Grok
- [`AGENTS.install.md`](AGENTS.install.md) — Ubuntu 26.04

## Licence

MIT. Usage démonstratif uniquement.
