
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
source .venv/bin/activate || source .venv/Scripts/activate

echo ">>> Running FS tool tests"
python tests/test_fs_mock_agent.py || true

echo ">>> Running server mock agent tests"
python tests/test_server_mock_agent.py || true

echo ">>> Running TODO tool tests"
python tests/test_todo_mock_agent.py || true

echo ">>> Running testing-tools tests"
python tests/test_testing_tools.py || true

echo ">>> Done."
