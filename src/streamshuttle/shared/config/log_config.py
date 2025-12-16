"""ログ設定"""

from pydantic import Field
from pydantic_settings import BaseSettings


class LogConfig(BaseSettings):
    """ログ設定"""

    level: str = Field(
        default="INFO",
        description="""ログレベル（デフォルト: INFO）

        許可される値: DEBUG, INFO, WARNING, ERROR, CRITICAL
        開発環境ではDEBUG、本番環境ではINFOまたはWARNINGを推奨
        """,
    )
    format: str = Field(
        default="json",
        description="""ログ出力形式（デフォルト: json）

        許可される値:
        - json: JSON形式の構造化ログ（本番環境推奨）
        - text: 人間が読みやすいテキスト形式（開発環境推奨）
        """,
    )

    model_config = {
        "env_prefix": "LOG_",
        "frozen": True,
    }
