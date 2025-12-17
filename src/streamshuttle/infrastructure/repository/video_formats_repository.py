"""
ビデオフォーマットRepository実装モジュール

VideoFormatsRepository Protocolの実装クラスを定義します。
"""

from streamshuttle.domain.model.cache_key.video_formats_cache_key import (
    VideoFormatsCacheKey,
)
from streamshuttle.domain.model.stream_url.video_id import VideoId
from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.shared.config import config
from streamshuttle.usecase.dto.video_formats_dto import VideoFormatsDto


class VideoFormatsRepository:
    """
    ビデオフォーマットRepository実装クラス

    VideoFormatsRepository Protocolの実装です。
    RedisDaoを使用してビデオフォーマット情報をキャッシュに保存します。

    このRepositoryはCommand（書き込み）処理からのみ呼び出され、
    データの保存のみを行います。

    エラーハンドリング:
        キャッシュ保存に失敗してもシステム全体のエラーにはせず、
        ログ出力のみ行います（ベストエフォート）。
    """

    def __init__(self, redis_dao: RedisDao) -> None:
        """
        VideoFormatsRepositoryを初期化します

        Args:
            redis_dao: Redis操作を行うDAOインスタンス
        """
        self._redis_dao = redis_dao

    async def save(self, video_id: str, video_formats: VideoFormatsDto) -> None:
        """
        ビデオフォーマット情報をキャッシュに保存します

        VideoFormatsDtoをJSON形式でシリアライズし、Redisにキャッシュします。
        TTLはconfig.cache.ttl_secondsで設定された値を使用します。

        Args:
            video_id: YouTube動画ID
            video_formats: 保存するビデオフォーマット情報

        Note:
            キャッシュ保存に失敗した場合でも例外を投げず、ログを出力するのみです。
            これにより、キャッシュ障害がサービス全体に影響しないようにします。
        """
        try:
            cache_key = VideoFormatsCacheKey(_video_id=VideoId(_value=video_id))
            json_data = video_formats.model_dump_json()

            await self._redis_dao.set(
                key=cache_key.value,
                value=json_data,
                ttl=config.cache.ttl_seconds,
            )
        except Exception:
            pass
