#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
smoke_dir="$(mktemp -d)"
trap 'rm -rf "$smoke_dir"' EXIT

cd "$repo_dir"
uv build --wheel --out-dir "$smoke_dir/dist"
uv venv --python 3.12 "$smoke_dir/venv"
uv pip install --python "$smoke_dir/venv/bin/python" "$smoke_dir"/dist/*.whl

cd "$smoke_dir"
repoman="$smoke_dir/venv/bin/repoman"
"$repoman" create -pn wheel-cli --preset cli
(
    cd wheel-cli
    uv sync
    uv run wheel-cli --help
    make lint
    grep -F "make test" AGENTS.md
    ! grep -Eq "docker-test|docker-env" Makefile
)

"$repoman" create -pn wheel-docs --preset docs-only
(
    cd wheel-docs
    make setup check-docs
    test -f site/index.html
    grep -F "make check-docs" AGENTS.md
)

bash "$repo_dir/scripts/smoke_upgrade.sh" "$repoman"
