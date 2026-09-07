# Install — Ubuntu 26.04

Seul script d’install : `install.sh` (jamais root). Override OS : `ALLOW_OTHER_OS=1`.

```
./install.sh          # venv + Scrapy + psycopg + PostgreSQL + .env
./install.sh --v100   # + vLLM ou llama.cpp CUDA + GGUF
./scripts/init-db.sh  # docker compose db ou rôle/base locaux
sscraping db-init     # schema.sql
```

Python ≥3.12 (26.04). Paquets : libxml2, libxslt, libpq, postgresql.

Postgres : `DATABASE_URL=postgresql://sscraping:sscraping@127.0.0.1:5432/sscraping`
Alt : `docker compose up -d db`

Logs : `logs/`. GPU V100 32 Go sm_70 comme avant.

Ne pas committer `.env`, `data/`, `logs/`, `models/`.
