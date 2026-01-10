"""
ストリームURL QueryService実装モジュール

UseCase層で定義されたStreamUrlQueryServiceインターフェースの実装クラスを定義します。
"""

from datetime import UTC, datetime, timedelta

from streamshuttle.domain.model.cache_key.stream_url_cache_key import StreamUrlCacheKey
from streamshuttle.domain.model.stream_url.youtube_video_id import YouTubeVideoId
from streamshuttle.domain.model.twitch_url.twitch_video_id import TwitchVideoId
from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.shared.config import config
from streamshuttle.usecase.dto.stream_url_dto import StreamUrlDto


class StreamUrlQueryService:
    """
    ストリームURL QueryService実装クラス

    StreamUrlQueryServiceインターフェースのRedis実装です。
    RedisDaoを使用してキャッシュされたストリームURL情報を取得します。

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
        StreamUrlQueryServiceを初期化します

        Args:
            redis_dao: Redis操作を行うDAOインスタンス
        """
        self._redis_dao = redis_dao

    async def find_by_video_id(
        self, video_id: str, hls: bool = False, platform: str = "youtube"
    ) -> StreamUrlDto | None:
        """
        動画IDでストリームURL情報を取得します

        Redisキャッシュから指定された動画IDに対応するストリームURL情報を取得します。
        キャッシュに存在しない場合はNoneを返します。

        Redisキーは「{platform}:{video_id}:hls:{hls}」形式で、
        プラットフォームとhlsの値によって異なるキャッシュエントリを参照します。

        Args:
            video_id: 動画ID（YouTubeは11桁、Twitchは可変長）
            hls: HLS形式の使用フラグ（デフォルト: False）
            platform: プラットフォーム識別子（デフォルト: "youtube"）

        Returns:
            StreamUrlDto | None:
                キャッシュが存在する場合はStreamUrlDto、存在しない場合はNone

        Raises:
            InvalidVideoIdError: ビデオIDの形式が不正な場合
            CacheException: キャッシュ操作に失敗した場合
        """
        # プラットフォームに応じたValue Objectで検証
        if platform == "youtube":
            YouTubeVideoId(_value=video_id)
        else:
            TwitchVideoId(_value=video_id)

        cache_key = StreamUrlCacheKey(
            _platform=platform,
            _video_id_value=video_id,
            _hls=hls,
        )

        cached_url = await self._redis_dao.get(key=cache_key.value)

        if cached_url is None:
            return None

        ttl = await self._redis_dao.ttl(key=cache_key.value)
        if ttl is None or ttl < 0:
            ttl = config.cache.ttl_seconds

        expiry_at = datetime.now(UTC) + timedelta(seconds=ttl)

        return StreamUrlDto(
            video_id=video_id,
            resolved_url=cached_url,
            expiry_at=expiry_at,
        )
