"""セキュリティ設定"""

from pydantic import Field
from pydantic_settings import BaseSettings


class SecurityConfig(BaseSettings):
    """セキュリティ設定

    Public利用を前提としたセキュリティ対策設定を提供します。
    """

    max_url_length: int = Field(
        default=2000,
        description="""URL最大長制限（デフォルト: 2000文字）

        Public利用を前提としたセキュリティ対策として、異常に長いURLを拒否します。
        YouTube URLは通常200文字以内ですが、クエリパラメータ等を考慮し、
        2000文字を上限として設定しています。

        この制限により以下の攻撃を防ぎます：
        - DoS攻撃（極端に長いURL処理によるリソース消費）
        - Buffer overflow攻撃
        - ログファイル肥大化攻撃
        """,
    )
    csrf_secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="CSRFトークン署名用の秘密鍵（環境変数から取得）",
    )
    csrf_token_expiry_seconds: int = Field(
        default=600, description="CSRFトークンの有効期限（秒）（デフォルト: 600秒 = 10分）"
    )

    model_config = {
        "env_prefix": "SECURITY_",
        "frozen": True,
    }
