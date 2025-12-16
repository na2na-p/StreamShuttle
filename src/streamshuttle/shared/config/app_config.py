"""アプリケーション全体の設定"""

from pydantic import Field
from pydantic_settings import BaseSettings

from .cache_config import CacheConfig
from .cors_config import CorsConfig
from .log_config import LogConfig
from .rate_limit_config import RateLimitConfig
from .redis_config import RedisConfig
from .security_config import SecurityConfig


class AppConfig(BaseSettings):
    """アプリケーション全体の設定

    各設定カテゴリを集約する。
    """

    redis: RedisConfig = Field(default_factory=RedisConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    log: LogConfig = Field(default_factory=LogConfig)

    app_version: str = Field(default="1.0.0", description="アプリケーションバージョン")

    model_config = {
        "frozen": True,
    }
