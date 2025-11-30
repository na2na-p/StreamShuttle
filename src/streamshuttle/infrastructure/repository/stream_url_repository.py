"""
StreamUrlRepository 実装モジュール

Domain層で定義されたStreamUrlRepositoryインターフェースの実装クラスを定義します。
"""

import logging

from streamshuttle.domain.model.stream_url import StreamUrl, VideoId
from streamshuttle.domain.repository.stream_url_repository import (
    StreamUrlRepository as StreamUrlRepositoryInterface,
)
from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.shared.exceptions import CacheError

logger = logging.getLogger(__name__)


class StreamUrlRepository(StreamUrlRepositoryInterface):
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

        Redis障害時はログを出力して処理を続行します（キャッシュ保存失敗は
        本体処理の成功に影響しません）。

        Args:
            stream_url: 保存するStreamUrl Aggregate
            use_hls: HLS形式の使用フラグ（デフォルト: False）
        """
        # use_hlsを含むキャッシュキーを生成
        key = f"{stream_url.video_id.value}:hls:{use_hls}"
        value = stream_url.resolved_url.value
        ttl = stream_url.cache_expiry.ttl_seconds()

        try:
            await self._redis_dao.set(key=key, value=value, ttl=ttl)
        except CacheError as e:
            logger.warning("Redis障害: キャッシュ保存スキップ key=%s, error=%s", key, e)

    async def delete(self, video_id: VideoId) -> None:
        """
        VideoIdに紐づくStreamUrlを削除します

        指定されたVideoIdに対応するStreamUrlをRedisから削除します。
        該当するStreamUrlが存在しない場合でもエラーとしません。

        Redis障害時はログを出力して処理を続行します（キャッシュ削除失敗は
        本体処理の成功に影響しません）。

        Args:
            video_id: 削除対象のVideoId
        """
        key = video_id.value
        try:
            await self._redis_dao.delete(key=key)
        except CacheError as e:
            logger.warning("Redis障害: キャッシュ削除スキップ key=%s, error=%s", key, e)
