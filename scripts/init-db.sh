#!/usr/bin/env bash
# Crée le rôle/base PostgreSQL locaux (Ubuntu) si docker-compose n'est pas utilisé.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
log() { printf '[Scraping Grok Support] %s\n' "$*"; }

if command -v docker >/dev/null 2>&1 && [[ -f "$ROOT/docker-compose.yml" ]]; then
  if docker compose version >/dev/null 2>&1; then
    log "docker compose up -d db"
    (cd "$ROOT" && docker compose up -d db)
    exit 0
  fi
fi

sudo -u postgres psql -v ON_ERROR_STOP=1 <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'scraping_grok') THEN
    CREATE ROLE scraping_grok LOGIN PASSWORD 'scraping_grok';
  END IF;
END$$;
SELECT 'CREATE DATABASE scraping_grok OWNER scraping_grok'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'scraping_grok')\gexec
GRANT ALL PRIVILEGES ON DATABASE scraping_grok TO scraping_grok;
SQL
log "PostgreSQL local : postgresql://scraping_grok:scraping_grok@127.0.0.1:5432/scraping_grok"
