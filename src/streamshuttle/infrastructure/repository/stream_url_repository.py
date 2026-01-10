"""
StreamUrlRepository 実装モジュール

Domain層で定義されたStreamUrlRepositoryインターフェースの実装クラスを定義します。
"""

from streamshuttle.domain.model.cache_key.stream_url_cache_key import StreamUrlCacheKey
from streamshuttle.domain.model.stream_url import StreamUrl, YouTubeVideoId
from streamshuttle.domain.model.twitch_url import TwitchVideoId
from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.shared.config import config


class StreamUrlRepository:
    """
    StreamUrlRepository 実装クラス

    StreamUrlRepositoryインターフェースのRedis実装です。
    RedisDaoを使用してStreamUrl Aggregateの永続化を行います。

    CQRS原則に基づき、更新系UseCaseからAggregate単位でのキャッシュ取得が可能です。
    参照系UseCase向けのDTO取得はQueryServiceで行います。

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

    async def save(
        self, stream_url: StreamUrl, hls: bool = False, platform: str = "youtube"
    ) -> None:
        """
        StreamUrlを保存します

        StreamUrl AggregateをRedisに永続化します。
        既に同じVideoIdのStreamUrlが存在する場合は上書きします。

        Redisキーは「{platform}:{video_id}:hls:{hls}」形式で、
        プラットフォームとhlsの値によって異なるキャッシュエントリとして保存されます。

        Args:
            stream_url: 保存するStreamUrl Aggregate
            hls: HLS形式の使用フラグ（デフォルト: False）
            platform: プラットフォーム識別子（デフォルト: "youtube"）

        Raises:
            CacheException: Redisへの保存に失敗した場合
        """
        cache_key = StreamUrlCacheKey(
            _platform=platform,
            _video_id_value=stream_url.video_id.value,
            _hls=hls,
        )
        value = stream_url.resolved_url.value
        ttl = stream_url.cache_expiry.ttl_seconds()

        await self._redis_dao.set(key=cache_key.value, value=value, ttl=ttl)

    async def delete(
        self,
        video_id: YouTubeVideoId | TwitchVideoId,
        hls: bool = False,
        platform: str = "youtube",
    ) -> None:
        """
        VideoIdに紐づくStreamUrlを削除します

        指定されたVideoIdに対応するStreamUrlをRedisから削除します。
        該当するStreamUrlが存在しない場合でもエラーとしません。

        Args:
            video_id: 削除対象のVideoId（YouTubeVideoIdまたはTwitchVideoId）
            hls: HLS形式の使用フラグ（デフォルト: False）
            platform: プラットフォーム識別子（デフォルト: "youtube"）

        Raises:
            CacheException: Redisからの削除に失敗した場合
        """
        cache_key = StreamUrlCacheKey(
            _platform=platform,
            _video_id_value=video_id.value,
            _hls=hls,
        )
        await self._redis_dao.delete(key=cache_key.value)

    async def find_by_video_id(
        self, video_id: str, hls: bool = False, platform: str = "youtube"
    ) -> StreamUrl | None:
        """
        VideoIdに紐づくStreamUrlを取得します

        指定されたVideoIdに対応するStreamUrl Aggregateをデータストアから取得します。
        該当するStreamUrlが存在しない場合はNoneを返します。

        Redisキーは「{platform}:{video_id}:hls:{hls}」形式で、
        プラットフォームとhlsの値によって異なるキャッシュエントリを参照します。

        Args:
            video_id: 動画ID（YouTubeは11桁、Twitchは可変長）
            hls: HLS形式の使用フラグ（デフォルト: False）
            platform: プラットフォーム識別子（デフォルト: "youtube"）

        Returns:
            StreamUrl | None:
                キャッシュが存在する場合はStreamUrl Aggregate、存在しない場合はNone

        Raises:
            InvalidVideoIdError: ビデオIDの形式が不正な場合
            CacheException: Redisからの取得に失敗した場合
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

        return StreamUrl.create(
            video_id=video_id,
            resolved_url=cached_url,
            ttl_seconds=ttl,
            platform=platform,
        )
