#!/bin/bash
set -e
echo "=== Installing dev-squad ==="
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
echo "Done. Run: python -m dev_squad --help"
