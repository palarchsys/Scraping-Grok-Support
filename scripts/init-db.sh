#!/usr/bin/env bash
# Crée le rôle/base PostgreSQL locaux (Ubuntu) si docker-compose n'est pas utilisé.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
log() { printf '[ss-craping-bot] %s\n' "$*"; }

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
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sscraping') THEN
    CREATE ROLE sscraping LOGIN PASSWORD 'sscraping';
  END IF;
END$$;
SELECT 'CREATE DATABASE sscraping OWNER sscraping'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sscraping')\gexec
GRANT ALL PRIVILEGES ON DATABASE sscraping TO sscraping;
SQL
log "PostgreSQL local : postgresql://sscraping:sscraping@127.0.0.1:5432/sscraping"
