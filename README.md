# ss-craping-bot

Bot pédagogique en deux étapes : **collecte** d’articles de presse, puis **analyse** du sujet. Si le sujet n’est pas une forme d’agression, on passe. Sinon on extrait nom, prénom, nationalité, âge, pays d’origine, année / mois / jour des faits — vide si absent du texte.

La table `incidents` stocke ces champs **en clair** (ce que l’article écrit). Aucun masquage SQL. Une GUI future masquera à l’affichage ; elle n’est pas dans ce dépôt.

Dépôt public = code + installateur Ubuntu 26.04. `fixtures/` = corpus hors-ligne pour tests (pas un anonymiseur).

## Pourquoi cette stack

| Couche | Choix | Pourquoi |
|---|---|---|
| Runtime | Python ≥ 3.12, asyncio | I/O bound (HTTP + LLM) |
| HTTP | httpx HTTP/2 + tenacity | pool, retry 429/5xx |
| HTML | selectolax | CSS rapide, pas BeautifulSoup |
| RSS | lxml | XML déterministe |
| SQL | SQLite WAL + aiosqlite | un process, upserts/s suffisants |
| Contrat | pydantic v2 | JSON LLM refusé si hors schéma |
| CLI | typer | `sscraping scrape \| analyze \| run` |

Étape 2 **oui sur V100 32 Go** : 14B AWQ (vLLM) ou 14B GGUF Q4 (llama.cpp). Pas de 70B.

## Deux étapes

```
sources.yaml ──► RSS (+ HTML optionnel) ──► articles (SQLite)
                                              │
                         préfiltre tokens ────┤ miss → skip
                                              ▼ hit
                         Grok API  ou  V100 /v1 ──► JSON ──► incidents
```

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

Éditer `.env` : `XAI_API_KEY=...` pour Grok.

```bash
source .venv/bin/activate
sscraping scrape                 # fixtures
sscraping analyze --backend grok
sscraping run --backend v100     # serveur local déjà lancé
sscraping stats
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
