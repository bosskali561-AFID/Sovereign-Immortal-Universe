#!/usr/bin/env bash
# Local LLM (Ollama) setup — offline-first, telemetry-verified.
# Installs Ollama if missing, pulls a small GGUF model, then VERIFIES the
# runtime is actually serving before claiming success.
set -euo pipefail

MODEL="${LOCAL_LLM_MODEL:-llama3.2}"
PORT="${LOCAL_LLM_PORT:-11434}"
BASE_URL="${LOCAL_LLM_URL:-http://127.0.0.1:${PORT}}"

echo "== Local LLM setup: model=${MODEL} url=${BASE_URL} =="

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama not found — installing (requires network access)..."
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "Ollama already installed: $(ollama --version 2>/dev/null || echo 'unknown version')"
fi

# Start the server if it is not already serving.
if ! curl -fsS "${BASE_URL}/api/tags" >/dev/null 2>&1; then
  echo "Starting ollama serve..."
  nohup ollama serve > /tmp/ollama.log 2>&1 &
  sleep 3
fi

echo "Pulling model ${MODEL} (this downloads the GGUF weights)..."
ollama pull "${MODEL}"

# --- Telemetry verification: never claim a model is loaded without this ---
echo "Verifying runtime via ${BASE_URL}/api/tags ..."
TAGS="$(curl -fsS "${BASE_URL}/api/tags")"
echo "Runtime telemetry: ${TAGS}"

if echo "${TAGS}" | grep -q "\"name\":\"${MODEL}"; then
  echo "SETUP_VERIFIED: ${MODEL} is present in the runtime model list."
  echo "Next: set LOCAL_LLM_ENABLED=true and LOCAL_LLM_URL=${BASE_URL} in your .env"
else
  echo "SETUP_NOT_VERIFIED: model not found in runtime list — do not claim it is loaded." >&2
  exit 1
fi
