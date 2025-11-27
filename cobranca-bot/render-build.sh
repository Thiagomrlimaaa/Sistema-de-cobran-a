#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Atualizando apt..."
apt-get update

echo "🌐 Instalando Chromium..."
DEBIAN_FRONTEND=noninteractive apt-get install -y chromium

echo "✅ Chromium instalado em /usr/bin/chromium"

