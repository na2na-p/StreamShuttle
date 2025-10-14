"""
共通設定モジュール

環境変数からRedis接続情報を読み込み、アプリケーション全体で使用する設定を提供します。
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    アプリケーション設定クラス

    環境変数からRedis接続情報とキャッシュ設定を読み込みます。
    Pydantic BaseSettingsを使用して、型安全な設定管理を実現します。
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    REDIS_HOST: str = "localhost"
    """Redis接続ホスト名（デフォルト: localhost）"""

    REDIS_PORT: int = 6379
    """Redis接続ポート番号（デフォルト: 6379）"""

    REDIS_DB: int = 0
    """Redis使用DB番号（デフォルト: 0）"""

    CACHE_TTL_SECONDS: int = 21600
    """キャッシュ有効期限（秒）（デフォルト: 21600秒 = 6時間）"""

    ALLOWED_ORIGINS: list[str] = []
    """
    CORS許可オリジンリスト（デフォルト: 空リスト）

    本サービスはJinja2テンプレートによるサーバーサイドレンダリング（SSR）を採用しており、
    フロントエンドとバックエンドが同一オリジンで動作するため、基本的にCORSは不要です。

    開発環境等で外部オリジンからのアクセスを許可する場合のみ、
    カンマ区切りの文字列形式で環境変数 ALLOWED_ORIGINS に設定してください。

    例: ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

    本番環境では同一オリジンポリシーを活かし、この設定は空のままにすることを推奨します。
    """

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str | list[str]) -> list[str]:
        """
        カンマ区切り文字列をリストに変換

        環境変数からカンマ区切りの文字列が渡された場合、リストに分割します。
        既にリストの場合はそのまま返します。

        Args:
            v: 環境変数の値（str または list[str]）

        Returns:
            list[str]: オリジンのリスト
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    RATE_LIMIT_RESOLVE: str = "10/minute"
    """resolveエンドポイントのレート制限（デフォルト: 10リクエスト/分）"""

    RATE_LIMIT_FORMATS: str = "5/minute"
    """formatsエンドポイントのレート制限（デフォルト: 5リクエスト/分）"""

    RATE_LIMIT_DOWNLOAD: str = "5/minute"
    """downloadエンドポイントのレート制限（デフォルト: 5リクエスト/分）"""

    MAX_URL_LENGTH: int = 2000
    """
    URL最大長制限（デフォルト: 2000文字）

    Public利用を前提としたセキュリティ対策として、異常に長いURLを拒否します。
    YouTube URLは通常200文字以内ですが、クエリパラメータ等を考慮し、
    2000文字を上限として設定しています。

    この制限により以下の攻撃を防ぎます：
    - DoS攻撃（極端に長いURL処理によるリソース消費）
    - Buffer overflow攻撃
    - ログファイル肥大化攻撃
    """

    CSRF_SECRET_KEY: str
    """CSRFトークン署名用の秘密鍵（環境変数CSRF_SECRET_KEYから取得、必須）"""

    CSRF_TOKEN_EXPIRY_SECONDS: int = 600
    """CSRFトークンの有効期限（秒）（デフォルト: 600秒 = 10分）"""

    LOG_LEVEL: str = "INFO"
    """
    ログレベル（デフォルト: INFO）

    許可される値: DEBUG, INFO, WARNING, ERROR, CRITICAL
    開発環境ではDEBUG、本番環境ではINFOまたはWARNINGを推奨
    """

    LOG_FORMAT: str = "json"
    """
    ログ出力形式（デフォルト: json）

    許可される値:
    - json: JSON形式の構造化ログ（本番環境推奨）
    - text: 人間が読みやすいテキスト形式（開発環境推奨）
    """


# グローバル設定インスタンス
config = Config()
