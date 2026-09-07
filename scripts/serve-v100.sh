#!/usr/bin/env bash
# Serveur OpenAI-compatible pour le connecteur --backend v100 (port 8000).
# Prérequis : ./install.sh --v100   (driver NVIDIA + vLLM ou llama-server)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
MODEL="${V100_MODEL:-Qwen/Qwen2.5-14B-Instruct-AWQ}"

if python3 -c "import vllm" 2>/dev/null; then
  exec python3 -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.90 \
    --max-num-seqs 8 \
    --port 8000 \
    --host 127.0.0.1
fi

if command -v llama-server >/dev/null 2>&1; then
  GGUF="${V100_GGUF:-$ROOT/models/qwen2.5-14b-instruct-q4_k_m.gguf}"
  [[ -f "$GGUF" ]] || { echo "manque $GGUF — relance ./install.sh --v100" >&2; exit 1; }
  exec llama-server -m "$GGUF" --port 8000 --host 127.0.0.1 -c 4096 -ngl 99 --jinja
fi

echo "ni vllm ni llama-server. Relance: ./install.sh --v100" >&2
exit 1
