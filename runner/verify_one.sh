#!/usr/bin/env bash
set -u
if [ "$#" -ne 3 ]; then
  echo "usage: $0 <file.lean> <fixture_id> <out_dir>" >&2
  exit 10
fi
script_dir="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$script_dir/verify_one.py" "$@"
