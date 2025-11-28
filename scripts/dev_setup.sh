
#!/usr/bin/env bash
set -euo pipefail

# cd to repo root
cd "$(dirname "$0")/.."

echo ">>> Creating venv (.venv)"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate || source .venv/Scripts/activate

echo ">>> Installing Python deps"
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

echo ">>> Checking Node & npm versions (need node>=18, npm>=9)"
node --version || { echo "Node is missing. Install from https://nodejs.org/"; exit 1; }
npm --version || { echo "npm is missing. Install Node LTS"; exit 1; }
npx --version || { echo "npx is missing. Install Node LTS"; exit 1; }

echo ">>> Verifying waa CLI"
waa --help || { echo "waa CLI not available after install"; exit 1; }

echo ">>> Kick off a smoke test (expected to fail initially)"
python tests/test_fs_mock_agent.py || true

echo ">>> All set. Next steps: open docs/PLAN_A3.md and start Part 1."
