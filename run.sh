#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "请先安装 Docker 与 Docker Compose。" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "构建镜像..."
docker compose build

echo "启动容器..."
docker compose up -d

echo "已启动，默认通过 http://localhost:3000 访问。"
