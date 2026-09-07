#!/usr/bin/env bash
# Programme d'installation Ubuntu 26.04 pour Scraping Grok Support.
# Usage : ./install.sh
set -euo pipefail

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      sed -n '2,4p' "$0"
      exit 0
      ;;
    *)
      echo "option inconnue: $arg" >&2
      exit 2
      ;;
  esac
done

log() { printf '\033[1m[Scraping Grok Support]\033[0m %s\n' "$*"; }
die() { printf 'erreur: %s\n' "$*" >&2; exit 1; }

if [[ -f /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
else
  die "/etc/os-release introuvable"
fi

if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "26.04" ]]; then
  if [[ "${ALLOW_OTHER_OS:-0}" != "1" ]]; then
    die "Ubuntu 26.04 requis (détecté: ${PRETTY_NAME:-inconnu}). OVERRIDE: ALLOW_OTHER_OS=1 $0"
  fi
  log "ALLOW_OTHER_OS=1 — on continue sur ${PRETTY_NAME:-?}"
fi

if [[ "$(id -u)" -eq 0 ]]; then
  die "ne pas lancer en root ; le script appellera sudo pour apt"
fi

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

log "paquets APT"
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  python3 python3-venv python3-pip python3-dev python3-full \
  build-essential libxml2-dev libxslt1-dev libffi-dev libpq-dev \
  postgresql postgresql-contrib \
  ca-certificates curl git pkg-config

PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' \
  || die "Python ≥ 3.12 requis (trouvé ${PYVER})"

log "venv .venv"
python3 -m venv --upgrade-deps .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -e ".[dev]"

mkdir -p data logs
chmod +x scripts/init-db.sh 2>/dev/null || true
if [[ ! -f .env ]]; then
  cp .env.example .env
  log "créé .env (édite XAI_API_KEY pour Grok)"
fi

log "PostgreSQL"
set +e
./scripts/init-db.sh
PG_OK=$?
set -e
if [[ "$PG_OK" -ne 0 ]]; then
  log "init-db a échoué — lance plus tard : ./scripts/init-db.sh && scraping-grok db-init"
else
  set +e
  scraping-grok db-init
  set -e
fi

log "OK"
echo
echo "  source .venv/bin/activate"
echo "  scraping-grok db-init"
echo "  scraping-grok scrape"
echo "  scraping-grok scrape --live"
echo "  scraping-grok analyze"
echo "  scraping-grok triage"
echo "  scraping-grok stats"
echo "  tail -f logs/scraping-grok.log logs/sql.log logs/nlp.log"
