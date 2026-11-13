@echo off
echo === Installing dev-squad ===
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
echo Done. Run: python -m dev_squad --help
