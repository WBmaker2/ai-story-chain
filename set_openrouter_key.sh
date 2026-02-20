#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$ROOT_DIR/.env"

print -n "OpenRouter API Key 입력(화면에 표시되지 않음): "
read -s OPENROUTER_API_KEY
print

if [[ -z "$OPENROUTER_API_KEY" ]]; then
  echo "API Key가 비어 있습니다."
  exit 1
fi

print -n "이미지 모델(기본: google/gemini-2.0-flash-exp:free): "
read OPENROUTER_IMAGE_MODEL
if [[ -z "$OPENROUTER_IMAGE_MODEL" ]]; then
  OPENROUTER_IMAGE_MODEL="google/gemini-2.0-flash-exp:free"
fi

cat > "$ENV_FILE" <<ENV
OPENROUTER_API_KEY=$OPENROUTER_API_KEY
OPENROUTER_IMAGE_MODEL=$OPENROUTER_IMAGE_MODEL
ENV

chmod 600 "$ENV_FILE"
echo ".env 저장 완료: $ENV_FILE"
echo "권한: $(stat -f '%Sp' "$ENV_FILE")"
