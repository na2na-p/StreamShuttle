"""Redis実装のCacheRepository"""

from streamshuttle.infrastructure.dao.redis_dao import RedisDao


class RedisCacheRepository:
    """Redis実装のCacheRepository

    CacheRepositoryインターフェースのRedis実装。
    """

    def __init__(self, redis_dao: RedisDao) -> None:
        """RedisCacheRepositoryを初期化

        Args:
            redis_dao: RedisDAO
        """
        self._redis_dao = redis_dao

    async def get(self, key: str) -> str | None:
        """キャッシュから値を取得

        Args:
            key: キャッシュキー

        Returns:
            str | None: キャッシュ値。存在しない場合はNone
        """
        return await self._redis_dao.get(key)

    async def set(self, key: str, value: str, ttl: int) -> None:
        """キャッシュに値を保存

        Args:
            key: キャッシュキー
            value: 保存する値
            ttl: 有効期限（秒）
        """
        await self._redis_dao.set(key=key, value=value, ttl=ttl)
