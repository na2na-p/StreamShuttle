"""
ビデオフォーマットキャッシュQueryService実装モジュール

VideoFormatsCacheQueryService Protocolの実装クラスを定義します。
"""

from pydantic import ValidationError

from streamshuttle.domain.model.cache_key.video_formats_cache_key import VideoFormatsCacheKey
from streamshuttle.domain.model.stream_url.video_id import VideoId
from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.usecase.dto.video_formats_dto import VideoFormatsDto


class VideoFormatsCacheQueryService:
    """
    ビデオフォーマットキャッシュQueryService実装クラス

    VideoFormatsCacheQueryService Protocolの実装です。
    RedisDaoを使用してキャッシュからビデオフォーマット情報を取得します。

    このQueryServiceはQuery（読み取り）処理からのみ呼び出され、
    データの取得のみを行います。

    エラーハンドリング:
        キャッシュ取得に失敗した場合やJSON破損時はNoneを返します。
        これにより、キャッシュミスとして扱われ、通常のyt-dlp処理にフォールバックします。
    """

    def __init__(self, redis_dao: RedisDao) -> None:
        """
        VideoFormatsCacheQueryServiceを初期化します

        Args:
            redis_dao: Redis操作を行うDAOインスタンス
        """
        self._redis_dao = redis_dao

    async def find_by_video_id(self, video_id: str) -> VideoFormatsDto | None:
        """
        動画IDでビデオフォーマット情報を取得します

        Redisキャッシュから指定された動画IDに対応するビデオフォーマット情報を取得します。
        キャッシュに存在しない場合やJSON破損時はNoneを返します。

        Args:
            video_id: YouTube動画ID

        Returns:
            VideoFormatsDto | None: キャッシュが存在する場合はVideoFormatsDto、
                                    存在しない場合やエラー時はNone

        Note:
            キャッシュ取得に失敗した場合やJSON破損時は例外を投げず、Noneを返します。
            これにより、キャッシュミスとして扱われ、通常のyt-dlp処理にフォールバックします。
        """
        try:
            cache_key = VideoFormatsCacheKey(_video_id=VideoId(_value=video_id))
            cached_json = await self._redis_dao.get(key=cache_key.value)

            if cached_json is None:
                return None

            video_formats = VideoFormatsDto.model_validate_json(cached_json)
            return video_formats

        except ValidationError:
            return None
        except Exception:
            return None
