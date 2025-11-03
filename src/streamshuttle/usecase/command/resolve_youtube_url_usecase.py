"""
YouTube URL解決UseCaseモジュール

YouTube URLをストリームURLに解決し、キャッシュに保存するUseCaseを定義します。
"""

import re
from datetime import UTC, datetime

from streamshuttle.domain.model.stream_url import StreamUrl
from streamshuttle.domain.repository.stream_url_repository import StreamUrlRepository
from streamshuttle.shared.exceptions import InvalidVideoIdError
from streamshuttle.usecase.external.youtube_resolver import YoutubeResolver
from streamshuttle.usecase.query_service.stream_url_query_service import StreamUrlQueryService


class ResolveYoutubeUrlUseCase:
    """
    YouTube URL解決UseCase

    YouTube URLをストリームURLに解決し、結果をキャッシュに保存します。
    既にキャッシュが存在し有効期限内の場合は、キャッシュから返します。

    このUseCaseは以下のフローで動作します:
    1. YouTube URLからvideo_idを抽出
    2. キャッシュに該当のvideo_idが存在し有効期限内かチェック
    3. キャッシュが有効な場合はキャッシュから返す
    4. キャッシュがない/期限切れの場合はYouTubeから解決
    5. 解決したURLをキャッシュに保存
    """

    def __init__(
        self,
        repository: StreamUrlRepository,
        query_service: StreamUrlQueryService,
        youtube_resolver: YoutubeResolver,
    ) -> None:
        """
        ResolveYoutubeUrlUseCaseを初期化します

        Args:
            repository: StreamUrl永続化用Repository
            query_service: StreamUrl参照用QueryService
            youtube_resolver: YouTube URL解決用Resolver
        """
        self._repository = repository
        self._query_service = query_service
        self._youtube_resolver = youtube_resolver

    async def execute(
        self, youtube_url: str, format_id: str | None = None, use_hls: bool = False
    ) -> str:
        """
        YouTube URLをストリームURLに解決します

        Args:
            youtube_url: YouTube動画URL
            format_id: フォーマットID（オプショナル）
            use_hls: HLS形式の使用（デフォルト: False）

        Returns:
            str: 解決済みの直接ストリームURL

        Raises:
            InvalidVideoIdError: video_idの抽出に失敗した場合
            InvalidUrlException: 無効なURLが指定された場合
            YouTubeResolverException: YouTube APIへのアクセスに失敗した場合
            CacheException: キャッシュ操作に失敗した場合
            HlsNotSupportedError: HLS形式が拒否された場合
        """
        video_id = self._extract_video_id(youtube_url)

        cached = await self._query_service.find_by_video_id(video_id, use_hls)

        if cached and cached.expiry_at > datetime.now(UTC):
            return cached.resolved_url

        resolved_url, ttl_seconds = await self._youtube_resolver.resolve_url(
            youtube_url, format_id, use_hls
        )

        stream_url = StreamUrl.create(
            video_id=video_id, resolved_url=resolved_url, ttl_seconds=ttl_seconds
        )
        await self._repository.save(stream_url, use_hls)

        return resolved_url

    def _extract_video_id(self, url: str) -> str:
        """
        YouTube URLからvideo_idを抽出します

        サポートするURL形式:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://m.youtube.com/watch?v=VIDEO_ID

        Args:
            url: YouTube動画URL

        Returns:
            str: 抽出されたvideo_id（11文字）

        Raises:
            InvalidVideoIdError: video_idの抽出に失敗した場合
        """
        # パターン1: youtube.com/watch?v=VIDEO_ID
        match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
        if match:
            return match.group(1)

        # パターン2: youtu.be/VIDEO_ID
        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
        if match:
            return match.group(1)

        # パターン3: youtube.com/embed/VIDEO_ID
        match = re.search(r"youtube\.com/embed/([a-zA-Z0-9_-]{11})", url)
        if match:
            return match.group(1)

        # 抽出失敗
        raise InvalidVideoIdError(f"URLからvideo_idを抽出できませんでした: {url}")
