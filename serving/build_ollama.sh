#!/usr/bin/env bash
# Create the Ollama models (base + tuned) from the Q4_K_M GGUFs, using ONE shared
# no-think template that reproduces the HF enable_thinking=False training format.
# Base and tuned differ ONLY in weights -> apples-to-apples serving.
#
#   ./build_ollama.sh <gguf_dir>
#   (gguf_dir must contain base-qwen3-1.7b-Q4_K_M.gguf and tuned-qwen3-1.7b-Q4_K_M.gguf)
set -euo pipefail
GGUF_DIR="${1:?usage: ./build_ollama.sh <gguf_dir>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="$(cat "$HERE/template.txt")"

for kind in base tuned; do
  gguf="$GGUF_DIR/${kind}-qwen3-1.7b-Q4_K_M.gguf"
  [ -f "$gguf" ] || { echo "missing $gguf"; exit 1; }
  mf="$(mktemp)"
  cat > "$mf" <<EOF
FROM $gguf
TEMPLATE """$TEMPLATE"""
PARAMETER temperature 0
PARAMETER top_p 1
PARAMETER seed 42
PARAMETER num_predict 512
PARAMETER stop "<|im_end|>"
EOF
  echo "== ollama create cs-$kind =="
  ollama create "cs-$kind" -f "$mf"
  rm -f "$mf"
done
echo "done: cs-base, cs-tuned"
