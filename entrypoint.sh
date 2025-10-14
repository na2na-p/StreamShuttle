#!/bin/bash
set -e

# LOG_FORMAT環境変数に基づいてログ設定を決定
if [ "${LOG_FORMAT:-json}" = "json" ]; then
  # JSONログ設定を使用
  exec uvicorn main:app --host 0.0.0.0 --port 8000 "$@" --log-config uvicorn_log_config.json
else
  # デフォルトのテキストログを使用
  exec uvicorn main:app --host 0.0.0.0 --port 8000 "$@"
fi
