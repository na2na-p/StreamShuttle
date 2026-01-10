"""
StreamUrl Aggregateモジュール

StreamUrl Aggregateを定義します。
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from streamshuttle.domain.model.stream_url.cache_expiry import CacheExpiry
from streamshuttle.domain.model.stream_url.resolved_url import ResolvedUrl
from streamshuttle.domain.model.stream_url.youtube_video_id import YouTubeVideoId
from streamshuttle.domain.model.twitch_url.twitch_video_id import TwitchVideoId


@dataclass(frozen=True)
class StreamUrl:
    """
    StreamUrl Aggregate

    ビデオIDから解決されたストリームURLとそのキャッシュ情報を管理します。
    YouTube、Twitch等のプラットフォームに対応します。
    このAggregateは不変であり、キャッシュの有効性判定機能を提供します。

    Aggregateルートとして、VideoId、ResolvedUrl、CacheExpiryの各ValueObjectを
    集約し、一貫性のある境界を形成します。

    ID設計:
        このAggregateのIDは _video_id (YouTubeVideoId | TwitchVideoId型) です。
        frozen=True により、ID（_video_id）の不変性が保証されています。
        同一のビデオIDに対するストリームURLは一意に識別されます。

    Attributes:
        _video_id: ビデオID（このAggregateの識別子）
        _resolved_url: 解決済みストリームURL
        _cache_expiry: キャッシュ有効期限
    """

    _video_id: YouTubeVideoId | TwitchVideoId
    _resolved_url: ResolvedUrl
    _cache_expiry: CacheExpiry

    @property
    def video_id(self) -> YouTubeVideoId | TwitchVideoId:
        """
        ビデオIDを取得します

        Returns:
            YouTubeVideoId | TwitchVideoId: ビデオID
        """
        return self._video_id

    @property
    def resolved_url(self) -> ResolvedUrl:
        """
        解決済みストリームURLを取得します

        Returns:
            ResolvedUrl: 解決済みストリームURL
        """
        return self._resolved_url

    @property
    def cache_expiry(self) -> CacheExpiry:
        """
        キャッシュ有効期限を取得します

        Returns:
            CacheExpiry: キャッシュ有効期限
        """
        return self._cache_expiry

    def is_expired(self) -> bool:
        """
        ストリームURLのキャッシュが期限切れかを判定します

        内部のCacheExpiryオブジェクトを使用して期限切れ判定を行います。

        Returns:
            bool: 期限切れの場合True、有効な場合False
        """
        return self._cache_expiry.is_expired()

    @staticmethod
    def create(
        video_id: str,
        resolved_url: str,
        ttl_seconds: int,
        platform: str = "youtube",
    ) -> "StreamUrl":
        """
        新しいStreamUrlを生成します

        このファクトリーメソッドは、文字列パラメータからValueObjectを生成し、
        StreamUrl Aggregateを構築します。ドメインロジック（バリデーション、
        有効期限計算）をカプセル化します。

        Args:
            video_id: ビデオID（YouTubeは11桁、Twitchは可変長）
            resolved_url: 解決済みストリームURL（HTTP/HTTPSスキーム）
            ttl_seconds: キャッシュTTL（秒）
            platform: プラットフォーム識別子（デフォルト: "youtube"）

        Returns:
            StreamUrl: 生成されたStreamUrl Aggregate

        Raises:
            InvalidVideoIdException: video_idが不正な場合
            InvalidUrlException: resolved_urlが不正な場合（スキーム不正、ホスト不在等）
            ValueError: ttl_secondsが0以下の場合
        """
        if platform == "youtube":
            video_id_vo: YouTubeVideoId | TwitchVideoId = YouTubeVideoId(_value=video_id)
        else:
            video_id_vo = TwitchVideoId(_value=video_id)

        resolved_url_vo = ResolvedUrl(_value=resolved_url)
        expiry_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        cache_expiry = CacheExpiry(_expiry_at=expiry_at)
        return StreamUrl(
            _video_id=video_id_vo, _resolved_url=resolved_url_vo, _cache_expiry=cache_expiry
        )
