"""
YouTube URL解決UseCaseモジュール

YouTube URLをストリームURLに解決し、キャッシュに保存するUseCaseを定義します。
"""

from streamshuttle.domain.model.stream_url import StreamUrl
from streamshuttle.domain.model.youtube_url import YoutubeUrl
from streamshuttle.domain.repository.stream_url_repository import StreamUrlRepository
from streamshuttle.usecase.external.youtube_resolver import YoutubeResolver


class ResolveYoutubeUrlUseCase:
    """
    YouTube URL解決UseCase

    YouTube URLをストリームURLに解決し、結果をキャッシュに保存します。
    既にキャッシュが存在し有効期限内の場合は、キャッシュから返します。
    format_idが指定された場合はキャッシュを読み書きせず、常にYouTubeから解決します。

    このUseCaseは以下のフローで動作します:
    1. YouTube URLからvideo_idを抽出
    2. format_idが指定されている場合はキャッシュを使わずYouTubeから解決して返す
    3. Repositoryでキャッシュに該当のvideo_idが存在し有効期限内かチェック
    4. キャッシュが有効な場合はキャッシュから返す
    5. キャッシュがない/期限切れの場合はYouTubeから解決し、キャッシュに保存
    """

    def __init__(
        self,
        repository: StreamUrlRepository,
        youtube_resolver: YoutubeResolver,
    ) -> None:
        """
        ResolveYoutubeUrlUseCaseを初期化します

        Args:
            repository: StreamUrl永続化・参照用Repository
            youtube_resolver: YouTube URL解決用Resolver
        """
        self._repository = repository
        self._youtube_resolver = youtube_resolver

    async def execute(
        self, youtube_url: YoutubeUrl, format_id: str | None = None, hls: bool = False
    ) -> str:
        """
        YouTube URLをストリームURLに解決します

        Args:
            youtube_url: YouTube動画URL（YoutubeUrl ValueObject）
            format_id: フォーマットID（オプショナル）。指定時はキャッシュを読み書きしない
            hls: HLS形式の使用（デフォルト: False）

        Returns:
            str: 解決済みの直接ストリームURL

        Raises:
            InvalidVideoIdError: video_idの抽出に失敗した場合
            InvalidUrlException: 無効なURLが指定された場合
            YouTubeResolverException: YouTube APIへのアクセスに失敗した場合
            CacheException: キャッシュ操作に失敗した場合（format_id未指定時のみ）
            HlsNotSupportedError: HLS形式が拒否された場合
        """
        video_id = youtube_url.extract_video_id()

        # ストリームURLキャッシュは「動画の再生URL」を動画ID単位で保持する。
        # フォーマット固有のURL（映像のみ等）を保存・参照すると、/resolve 等が
        # 音声なしのURLを返したり、指定フォーマットと異なるURLを返したりするため使わない。
        if format_id:
            result = await self._youtube_resolver.resolve_url(str(youtube_url), format_id, hls)
            return result.resolved_url

        cached = await self._repository.find_by_video_id(str(video_id), hls)

        if cached and not cached.is_expired():
            return cached.resolved_url.value

        result = await self._youtube_resolver.resolve_url(str(youtube_url), format_id, hls)

        stream_url = StreamUrl.create(
            video_id=str(video_id),
            resolved_url=result.resolved_url,
            ttl_seconds=result.ttl_seconds,
        )
        await self._repository.save(stream_url, hls)

        return result.resolved_url
