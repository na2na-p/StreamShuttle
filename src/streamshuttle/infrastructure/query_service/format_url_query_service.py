"""
フォーマットURL QueryService実装モジュール

UseCase層で定義されたFormatUrlQueryServiceインターフェースの実装クラスを定義します。
"""

from datetime import UTC, datetime, timedelta

from streamshuttle.domain.model.cache_key.format_url_cache_key import FormatUrlCacheKey
from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.shared.config import config
from streamshuttle.usecase.dto.format_url_dto import FormatUrlDto


class FormatUrlQueryService:
    """
    フォーマットURL QueryService実装クラス

    FormatUrlQueryServiceインターフェースのRedis実装です。
    RedisDaoを使用してキャッシュされたフォーマットURL情報を取得します。

    このQueryServiceは参照系（GET）処理からのみ呼び出され、
    データの取得のみを行います。

    注意事項:
        expiry_atはRedisのTTLコマンドを使用して正確に取得します。
        TTL取得に失敗した場合はデフォルトTTL（6時間）にフォールバックします。

    Attributes:
        _redis_dao: Redis操作を行うDAOインスタンス
    """

    def __init__(self, redis_dao: RedisDao) -> None:
        """
        FormatUrlQueryServiceを初期化します

        Args:
            redis_dao: Redis操作を行うDAOインスタンス
        """
        self._redis_dao = redis_dao

    async def find_by_video_and_format_id(
        self, video_id: str, format_id: str
    ) -> FormatUrlDto | None:
        """
        video_idとformat_idでフォーマットURL情報を取得します

        Redisキャッシュから指定されたvideo_idとformat_idに対応するフォーマットURL情報を
        取得します。キャッシュに存在しない場合はNoneを返します。

        Args:
            video_id: YouTube動画ID
            format_id: フォーマットID

        Returns:
            FormatUrlDto | None:
                キャッシュが存在する場合はFormatUrlDto、存在しない場合はNone

        Raises:
            CacheException: キャッシュ操作に失敗した場合
        """
        cache_key = FormatUrlCacheKey(_video_id=video_id, _format_id=format_id)

        cached_url = await self._redis_dao.get(key=cache_key.value)

        if cached_url is None:
            return None

        ttl = await self._redis_dao.ttl(key=cache_key.value)
        if ttl is None or ttl < 0:
            ttl = config.cache.ttl_seconds

        expiry_at = datetime.now(UTC) + timedelta(seconds=ttl)

        return FormatUrlDto(
            video_id=video_id,
            format_id=format_id,
            resolved_url=cached_url,
            expiry_at=expiry_at,
        )
