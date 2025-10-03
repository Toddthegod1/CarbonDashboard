#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export $(grep -v '^#' .env | xargs)
exec gunicorn -w 3 -b 0.0.0.0:8000 "app:create_app()"