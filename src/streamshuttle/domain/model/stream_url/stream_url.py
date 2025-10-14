"""
StreamUrl Aggregateモジュール

StreamUrl Aggregateを定義します。
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from streamshuttle.domain.model.stream_url.cache_expiry import CacheExpiry
from streamshuttle.domain.model.stream_url.resolved_url import ResolvedUrl
from streamshuttle.domain.model.stream_url.video_id import VideoId


@dataclass(frozen=True)
class StreamUrl:
    """
    StreamUrl Aggregate

    YouTubeビデオIDから解決されたストリームURLとそのキャッシュ情報を管理します。
    このAggregateは不変であり、キャッシュの有効性判定機能を提供します。

    Aggregateルートとして、VideoId、ResolvedUrl、CacheExpiryの各ValueObjectを
    集約し、一貫性のある境界を形成します。

    ID設計:
        このAggregateのIDは _video_id (VideoId型) です。
        frozen=True により、ID（_video_id）の不変性が保証されています。
        同一のビデオIDに対するストリームURLは一意に識別されます。

    Attributes:
        _video_id: YouTubeビデオID（このAggregateの識別子）
        _resolved_url: 解決済みストリームURL
        _cache_expiry: キャッシュ有効期限
    """

    _video_id: VideoId
    _resolved_url: ResolvedUrl
    _cache_expiry: CacheExpiry

    @property
    def video_id(self) -> VideoId:
        """
        YouTubeビデオIDを取得します

        Returns:
            VideoId: YouTubeビデオID
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
    def create(video_id: str, resolved_url: str, ttl_seconds: int) -> "StreamUrl":
        """
        新しいStreamUrlを生成します

        このファクトリーメソッドは、文字列パラメータからValueObjectを生成し、
        StreamUrl Aggregateを構築します。ドメインロジック（バリデーション、
        有効期限計算）をカプセル化します。

        Args:
            video_id: YouTubeビデオID（11桁の英数字）
            resolved_url: 解決済みストリームURL（HTTP/HTTPSスキーム）
            ttl_seconds: キャッシュTTL（秒）

        Returns:
            StreamUrl: 生成されたStreamUrl Aggregate

        Raises:
            InvalidVideoIdException: video_idが不正な場合（11桁でない、不正な文字等）
            InvalidUrlException: resolved_urlが不正な場合（スキーム不正、ホスト不在等）
            ValueError: ttl_secondsが0以下の場合
        """
        video_id_vo = VideoId(_value=video_id)
        resolved_url_vo = ResolvedUrl(_value=resolved_url)
        expiry_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        cache_expiry = CacheExpiry(_expiry_at=expiry_at)
        return StreamUrl(
            _video_id=video_id_vo,
            _resolved_url=resolved_url_vo,
            _cache_expiry=cache_expiry
        )
