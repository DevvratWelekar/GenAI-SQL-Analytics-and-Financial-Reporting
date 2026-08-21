#!/bin/sh
set -eu

ollama serve >/tmp/ollama.log 2>&1 &
ollama_pid=$!
trap 'kill "$ollama_pid" 2>/dev/null || true' EXIT

until ollama list >/dev/null 2>&1; do
  sleep 1
done

ollama pull "${OLLAMA_MODEL:-qwen2.5:1.5b}"

exec streamlit run src/app.py \
  --server.address 0.0.0.0 \
  --server.port "${PORT:-8501}" \
  --server.headless true
