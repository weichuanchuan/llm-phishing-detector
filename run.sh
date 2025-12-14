#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[ERROR] Missing required command: $cmd" >&2
    exit 1
  fi
}

require_command docker

if ! docker compose version >/dev/null 2>&1; then
  echo "[ERROR] Docker Compose V2 is required (docker compose)." >&2
  exit 1
fi

if [ ! -f .env ]; then
  echo "[ERROR] .env file not found. Please create it before deployment." >&2
  exit 1
fi

set -a
source .env
set +a

if [ -z "${MAIL_SERVER_FS:-}" ]; then
  echo "[ERROR] MAIL_SERVER_FS is not set in .env." >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/data"
mkdir -p "$MAIL_SERVER_FS"

if ! docker network inspect traefik_web >/dev/null 2>&1; then
  echo "[INFO] Creating traefik_web network..."
  docker network create traefik_web
fi

echo "[INFO] Building and starting MailCheck containers..."
docker compose up -d --build

echo "[SUCCESS] MailCheck is running. View logs with: docker compose logs -f"
