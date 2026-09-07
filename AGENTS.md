# ss-craping-bot — contrat agent (lire en entier, ne pas élargir)

Pédagogique, démo locale. Rien n’est publié depuis git.
PostgreSQL stocke les identités **en clair**. NULL si absent du texte. Pas de masquage SQL.

## Objectif
1. scrape (Scrapy) → `articles`
2. nlp (Grok) → si ≠ crime : skip ; sinon `type_crime` (8 groupes) + auteur + date des faits
3. triage → `faits` : même nom+prénom+date (normalisés) = un seul fait, N articles

## Stack
Python ≥3.12 · Scrapy · PostgreSQL/psycopg3 · Grok `api.x.ai` (`grok-4.5`) · pydantic v2 · typer
Pas de V100 / pas de LLM local.

Logs DEBUG : `logs/{sscraping,scrapy,sql,nlp}.log`. `--quiet` = INFO.

## Layout
```
install.sh  docker-compose.yml  scripts/init-db.sh
config/sources.yaml  config/taxonomy.yaml
src/sscraping/
  cli.py pipeline.py settings.py logconfig.py
  db/{schema.sql,sql.py,store.py}
  crawler/{..., known.py, spiders/site.py, spiders/rss.py}
  nlp/{pipeline,compress,filter,preuves,group,schema}.py
  nlp/connectors/{openai_compat,grok}.py
```

## Règles
- URL unique. Skip GET si URL déjà en PG.
- LLM : préfiltre fort/faible → `compress_for_llm` (≤1800c) → prompt statique (cache préfixe) → `max_tokens=280` → preuves locales.
- Un article → 0..1 incident. Groupage seulement si nom, prénom, année, mois, jour tous présents.
- Ne jamais inventer un champ. Ne jamais anonymiser en SQL.

## Commandes
`./install.sh` · `sscraping db-init` · `sscraping scrape --live` · `sscraping analyze` · `sscraping triage` · `pytest -q`

Prompt NLP → `nlp/pipeline.py` SYSTEM_PROMPT uniquement (rester identique d’un appel à l’autre).
