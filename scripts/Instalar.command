#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="$(command -v python3.12 || command -v python3 || true)"
if [ -z "$PYTHON" ]; then
  echo 'Instale Python 3.12 ou superior de python.org e tente novamente.'
  read -r -p 'Enter para sair.'
  exit 1
fi
"$PYTHON" -c 'import sys; assert sys.version_info >= (3,12), "Instale Python 3.12 ou superior"'
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m playwright install chromium
chmod +x scripts/*.command
printf '\nInstalação concluída. Abra scripts/Iniciar.command.\n'
read -r -p 'Enter para sair.'
