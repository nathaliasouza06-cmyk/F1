#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python -c 'from f1queue.app import ROOT,PORT; import webbrowser; webbrowser.open(f"http://127.0.0.1:{PORT}/#token="+(ROOT/"panel-token").read_text().strip())'
