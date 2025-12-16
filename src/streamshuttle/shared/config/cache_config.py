"""キャッシュTTL設定"""

from pydantic import Field
from pydantic_settings import BaseSettings


class CacheConfig(BaseSettings):
    """キャッシュTTL設定"""

    ttl_seconds: int = Field(default=21600, description="Cache TTL in seconds (default: 6 hours)")

    model_config = {
        "env_prefix": "CACHE_",
        "frozen": True,
    }
