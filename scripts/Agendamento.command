#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python scripts/install_agent.py
read -r -p 'Enter para sair.'
