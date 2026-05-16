#!/bin/sh
set -e

echo "Installing merlin..."

if command -v uv >/dev/null 2>&1; then
    uv tool install merlin-dbt
elif command -v pipx >/dev/null 2>&1; then
    pipx install merlin-dbt
elif command -v pip >/dev/null 2>&1; then
    pip install merlin-dbt
elif command -v pip3 >/dev/null 2>&1; then
    pip3 install merlin-dbt
else
    echo "Error: No Python package manager found (uv, pipx, pip, or pip3)."
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo ""
echo "merlin installed. Run 'merlin --help' to get started."
echo "Example: merlin +my_model+"
