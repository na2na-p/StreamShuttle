"""
ロギング設定モジュール

アプリケーション全体のロギング設定を提供します。
JSON形式の構造化ログとテキスト形式のログを切り替え可能です。
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from streamshuttle.shared.config import config


class JSONFormatter(logging.Formatter):
    """
    JSON形式のログフォーマッター

    ログレコードをJSON形式に変換します。
    タイムスタンプはISO 8601形式（UTC）で出力されます。
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        ログレコードをJSON形式に変換します

        Args:
            record: ログレコード

        Returns:
            str: JSON形式のログメッセージ
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 例外情報がある場合は追加
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 追加のコンテキスト情報がある場合は追加
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging() -> None:
    """
    ロギング設定を初期化します

    環境変数からログレベルと出力形式を読み込み、
    ルートロガーを設定します。
    """
    # ログレベルの取得と検証
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    # フォーマッターの選択
    if config.LOG_FORMAT.lower() == "json":
        formatter = JSONFormatter()
    else:
        # テキスト形式（開発環境向け）
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # ハンドラーの設定
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 既存のハンドラーをクリア
    root_logger.handlers.clear()

    # 新しいハンドラーを追加
    root_logger.addHandler(handler)

    # uvicorn関連のすべてのロガーを設定
    # reloaderのログもキャッチするため、親ロガーに伝播させる設定とする
    uvicorn_loggers = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
    ]

    for logger_name in uvicorn_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        logger.handlers.clear()
        # ハンドラーは設定せず、ルートロガーに伝播させる
        logger.propagate = True
