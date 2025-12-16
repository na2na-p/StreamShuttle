"""
StreamUrlRepository 実装モジュール

Domain層で定義されたStreamUrlRepositoryインターフェースの実装クラスを定義します。
"""

from streamshuttle.domain.model.stream_url import StreamUrl, VideoId
from streamshuttle.infrastructure.dao.redis_dao import RedisDao


class StreamUrlRepository:
    """
    StreamUrlRepository 実装クラス

    StreamUrlRepositoryインターフェースのRedis実装です。
    RedisDaoを使用してStreamUrl Aggregateの永続化を行います。

    このRepositoryはコマンド（書き込み）操作のみを提供します。
    参照系の操作はQueryServiceに分離されます。

    Attributes:
        _redis_dao: Redis操作を行うDAOインスタンス
    """

    def __init__(self, redis_dao: RedisDao) -> None:
        """
        StreamUrlRepositoryを初期化します

        Args:
            redis_dao: Redis操作を行うDAOインスタンス
        """
        self._redis_dao = redis_dao

    async def save(self, stream_url: StreamUrl, use_hls: bool = False) -> None:
        """
        StreamUrlを保存します

        StreamUrl AggregateをRedisに永続化します。
        既に同じVideoIdのStreamUrlが存在する場合は上書きします。

        Redisキーは「video_id:hls:use_hls」形式で、use_hlsの値によって
        異なるキャッシュエントリとして保存されます。

        Args:
            stream_url: 保存するStreamUrl Aggregate
            use_hls: HLS形式の使用フラグ（デフォルト: False）

        Raises:
            CacheException: Redisへの保存に失敗した場合
        """
        # use_hlsを含むキャッシュキーを生成
        key = f"{stream_url.video_id.value}:hls:{use_hls}"
        value = stream_url.resolved_url.value
        ttl = stream_url.cache_expiry.ttl_seconds()

        await self._redis_dao.set(key=key, value=value, ttl=ttl)

    async def delete(self, video_id: VideoId) -> None:
        """
        VideoIdに紐づくStreamUrlを削除します

        指定されたVideoIdに対応するStreamUrlをRedisから削除します。
        該当するStreamUrlが存在しない場合でもエラーとしません。

        Args:
            video_id: 削除対象のVideoId

        Raises:
            CacheException: Redisからの削除に失敗した場合
        """
        key = video_id.value
        await self._redis_dao.delete(key=key)
