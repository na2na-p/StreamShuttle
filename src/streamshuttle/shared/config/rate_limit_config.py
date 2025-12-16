"""レート制限設定"""

from pydantic import Field
from pydantic_settings import BaseSettings


class RateLimitConfig(BaseSettings):
    """レート制限設定"""

    resolve: str = Field(
        default="10/minute",
        description="resolveエンドポイントのレート制限（デフォルト: 10リクエスト/分）",
    )
    formats: str = Field(
        default="5/minute",
        description="formatsエンドポイントのレート制限（デフォルト: 5リクエスト/分）",
    )
    download: str = Field(
        default="5/minute",
        description="downloadエンドポイントのレート制限（デフォルト: 5リクエスト/分）",
    )

    model_config = {
        "env_prefix": "RATE_LIMIT_",
        "frozen": True,
    }
