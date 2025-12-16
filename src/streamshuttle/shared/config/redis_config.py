"""Redis接続設定"""

from pydantic import Field
from pydantic_settings import BaseSettings


class RedisConfig(BaseSettings):
    """Redis接続設定"""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")

    model_config = {
        "env_prefix": "REDIS_",
        "frozen": True,
    }
