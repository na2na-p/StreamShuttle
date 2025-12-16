"""設定モジュール"""

from .app_config import AppConfig
from .cache_config import CacheConfig
from .cors_config import CorsConfig
from .log_config import LogConfig
from .rate_limit_config import RateLimitConfig
from .redis_config import RedisConfig
from .security_config import SecurityConfig

# グローバルインスタンス（後のチケットで削除予定）
config = AppConfig()

__all__ = [
    "AppConfig",
    "RedisConfig",
    "CacheConfig",
    "CorsConfig",
    "RateLimitConfig",
    "SecurityConfig",
    "LogConfig",
    "config",
]
