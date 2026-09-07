# Install — Ubuntu 26.04

Seul script d’install : `install.sh` (jamais root). Override OS : `ALLOW_OTHER_OS=1`.

```
./install.sh          # venv + deps CPU + .env
./install.sh --v100   # + vLLM ou llama.cpp CUDA + GGUF
```

Python ≥3.12 (26.04). Paquets : libxml2, libxslt, sqlite3, build-essential.

GPU : Tesla V100 32 Go, sm_70. vLLM peut refuser Volta → fallback llama.cpp Q4_K_M ~9 Go.
Serveur : `scripts/serve-v100.sh` bind 127.0.0.1:8000.

Ne pas committer `.env`, `data/`, `models/`.
