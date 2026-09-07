#!/usr/bin/env bash
# Programme d'installation Ubuntu 26.04 pour ss-craping-bot.
# Usage :
#   ./install.sh           # CPU + SQLite + CLI (étape 1 + connecteur Grok)
#   ./install.sh --v100    # + serveur d'inférence local (vLLM si CUDA sm_70, sinon llama.cpp)
set -euo pipefail

WITH_V100=0
for arg in "$@"; do
  case "$arg" in
    --v100) WITH_V100=1 ;;
    -h|--help)
      sed -n '2,6p' "$0"
      exit 0
      ;;
    *)
      echo "option inconnue: $arg" >&2
      exit 2
      ;;
  esac
done

log() { printf '\033[1m[ss-craping-bot]\033[0m %s\n' "$*"; }
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
  build-essential libxml2-dev libxslt1-dev libffi-dev \
  sqlite3 ca-certificates curl git pkg-config

PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' \
  || die "Python ≥ 3.12 requis (trouvé ${PYVER})"

log "venv .venv"
python3 -m venv --upgrade-deps .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -e ".[dev]"

mkdir -p data
if [[ ! -f .env ]]; then
  cp .env.example .env
  log "créé .env (édite XAI_API_KEY pour le connecteur Grok)"
fi
chmod +x scripts/serve-v100.sh 2>/dev/null || true

if [[ "$WITH_V100" -eq 1 ]]; then
  log "profil V100 32 Go"
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    die "nvidia-smi absent. Installe le driver NVIDIA (ubuntu-drivers autoinstall) puis relance --v100"
  fi
  nvidia-smi || true
  GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1 || true)"
  VRAM="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1 || echo 0)"
  log "GPU=$GPU_NAME VRAM=${VRAM} MiB"

  pip install 'huggingface_hub[cli]'
  mkdir -p models

  set +e
  pip install vllm
  VLLM_OK=$?
  set -e
  if [[ "$VLLM_OK" -ne 0 ]]; then
    log "vLLM indisponible sur cette stack CUDA (fréquent sur Volta). Fallback llama.cpp"
    if ! command -v llama-server >/dev/null 2>&1; then
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends cmake ccache
      if [[ ! -d /opt/llama.cpp ]]; then
        sudo git clone --depth 1 https://github.com/ggml-org/llama.cpp /opt/llama.cpp
      fi
      sudo cmake -S /opt/llama.cpp -B /opt/llama.cpp/build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
      sudo cmake --build /opt/llama.cpp/build -j"$(nproc)" --target llama-server
      sudo ln -sf /opt/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server
    fi
    log "télécharge Qwen2.5-14B Instruct Q4_K_M (environ 9 Go)"
    .venv/bin/huggingface-cli download \
      Qwen/Qwen2.5-14B-Instruct-GGUF \
      qwen2.5-14b-instruct-q4_k_m.gguf \
      --local-dir "$ROOT/models"
    if grep -q '^V100_MODEL=' .env; then
      sed -i 's|^V100_MODEL=.*|V100_MODEL=qwen2.5-14b-instruct|' .env
    fi
  fi

  log "démarre le serveur : ./scripts/serve-v100.sh"
  log "puis : .venv/bin/sscraping run --backend v100"
fi

log "OK"
echo
echo "  source .venv/bin/activate"
echo "  sscraping scrape          # fixtures, zéro réseau"
echo "  sscraping analyze --backend grok"
echo "  sscraping run --backend grok"
echo "  sscraping stats"
if [[ "$WITH_V100" -eq 1 ]]; then
  echo "  ./scripts/serve-v100.sh   # terminal dédié"
  echo "  sscraping analyze --backend v100"
fi
echo
echo "Mode live (respecte robots.txt, plafond max_articles) :"
echo "  sscraping scrape --live"
