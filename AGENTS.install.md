# Install — Ubuntu 26.04

```
./install.sh
./scripts/init-db.sh
sscraping db-init
```

Python ≥3.12. `DATABASE_URL=postgresql://sscraping:sscraping@127.0.0.1:5432/sscraping`
Alt : `docker compose up -d db`. Pas de profil GPU.

Ne pas committer `.env`, `data/`, `logs/`.
