#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

mkdir -p data/tmp/reports data/mailserver/start

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to run this project." >&2
  exit 1
fi

echo "Building and starting the MailCheck Python stack..."
docker compose up --build
