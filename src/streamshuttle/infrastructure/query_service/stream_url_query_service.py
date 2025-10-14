"""
ストリームURL QueryService実装モジュール

UseCase層で定義されたStreamUrlQueryServiceインターフェースの実装クラスを定義します。
"""

from datetime import UTC, datetime, timedelta

from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.shared.config import config
from streamshuttle.usecase.dto.stream_url_dto import StreamUrlDto
from streamshuttle.usecase.query_service.stream_url_query_service import (
    StreamUrlQueryService as StreamUrlQueryServiceInterface,
)


class StreamUrlQueryService(StreamUrlQueryServiceInterface):
    """
    ストリームURL QueryService実装クラス

    StreamUrlQueryServiceインターフェースのRedis実装です。
    RedisDaoを使用してキャッシュされたストリームURL情報を取得します。

    このQueryServiceは参照系（GET）処理からのみ呼び出され、
    データの取得のみを行います。

    注意事項:
        RedisからTTL情報を正確に取得することは可能ですが、
        現在の実装ではシンプルさを優先し、expiry_atは
        現在時刻+デフォルトTTL（6時間）として推定します。

    Attributes:
        _redis_dao: Redis操作を行うDAOインスタンス
    """

    def __init__(self, redis_dao: RedisDao) -> None:
        """
        StreamUrlQueryServiceを初期化します

        Args:
            redis_dao: Redis操作を行うDAOインスタンス
        """
        self._redis_dao = redis_dao

    async def find_by_video_id(self, video_id: str) -> StreamUrlDto | None:
        """
        YouTube動画IDでストリームURL情報を取得します

        Redisキャッシュから指定された動画IDに対応するストリームURL情報を取得します。
        キャッシュに存在しない場合はNoneを返します。

        Redisキーは動画ID（video_id）、値は解決済みURL（resolved_url）です。

        Args:
            video_id: YouTube動画ID（11桁の英数字）

        Returns:
            StreamUrlDto | None:
                キャッシュが存在する場合はStreamUrlDto、存在しない場合はNone

        Raises:
            CacheException: キャッシュ操作に失敗した場合
        """
        # Redisからキャッシュを取得
        cached_url = await self._redis_dao.get(key=video_id)

        # キャッシュが存在しない場合はNoneを返す
        if cached_url is None:
            return None

        expiry_at = datetime.now(UTC) + timedelta(seconds=config.CACHE_TTL_SECONDS)

        # DTOを生成して返す
        return StreamUrlDto(
            video_id=video_id,
            resolved_url=cached_url,
            expiry_at=expiry_at,
        )
