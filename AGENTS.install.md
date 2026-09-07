# Install — Ubuntu 26.04

```
./install.sh
./scripts/init-db.sh
scraping-grok db-init
```

Python ≥3.12. `DATABASE_URL=postgresql://scraping_grok:scraping_grok@127.0.0.1:5432/scraping_grok`
Alt : `docker compose up -d db`.

Ne pas committer `.env`, `data/`, `logs/`.
