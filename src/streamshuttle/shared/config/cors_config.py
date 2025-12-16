"""CORS設定"""

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings


class CorsConfig(BaseSettings):
    """CORS設定

    本サービスはJinja2テンプレートによるサーバーサイドレンダリング(SSR)を採用しており、
    フロントエンドとバックエンドが同一オリジンで動作するため、基本的にCORSは不要です。

    開発環境等で外部オリジンからのアクセスを許可する場合のみ、
    カンマ区切りの文字列形式で環境変数 CORS_ALLOWED_ORIGINS_RAW に設定してください。

    例: CORS_ALLOWED_ORIGINS_RAW=http://localhost:3000,http://127.0.0.1:3000

    本番環境では同一オリジンポリシーを活かし、この設定は空のままにすることを推奨します。
    """

    allowed_origins_raw: str = Field(
        default="",
        description="CORS許可オリジンリスト（カンマ区切り）。環境変数: CORS_ALLOWED_ORIGINS_RAW",
    )

    model_config = {
        "env_prefix": "CORS_",
        "frozen": True,
    }

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_origins(self) -> list[str]:
        """カンマ区切り文字列からオリジンリストを生成

        Returns:
            list[str]: パースされたオリジンのリスト
        """
        if not self.allowed_origins_raw:
            return []
        return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]
