#!/usr/bin/env bash
set -euo pipefail
uninstaller_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$uninstaller_dir/deploy/uninstall.py" "$@"
