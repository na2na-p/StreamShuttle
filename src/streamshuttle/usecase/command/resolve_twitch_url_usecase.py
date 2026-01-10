"""
Twitch URL解決UseCaseモジュール

Twitch URLをストリームURLに解決し、キャッシュに保存するUseCaseを定義します。
"""

from streamshuttle.domain.model.stream_url import StreamUrl
from streamshuttle.domain.model.twitch_url import TwitchUrl
from streamshuttle.domain.repository.stream_url_repository import StreamUrlRepository
from streamshuttle.usecase.external.twitch_resolver import TwitchResolver


class ResolveTwitchUrlUseCase:
    """
    Twitch URL解決UseCase

    Twitch URLをストリームURLに解決し、結果をキャッシュに保存します。
    既にキャッシュが存在し有効期限内の場合は、キャッシュから返します。

    このUseCaseは以下のフローで動作します:
    1. Twitch URLからvideo_idを抽出
    2. Repositoryでキャッシュに該当のvideo_idが存在し有効期限内かチェック
    3. キャッシュが有効な場合はキャッシュから返す
    4. キャッシュがない/期限切れの場合はTwitchから解決
    5. 解決したURLをキャッシュに保存
    """

    def __init__(
        self,
        repository: StreamUrlRepository,
        twitch_resolver: TwitchResolver,
    ) -> None:
        """
        ResolveTwitchUrlUseCaseを初期化します

        Args:
            repository: StreamUrl永続化・参照用Repository
            twitch_resolver: Twitch URL解決用Resolver
        """
        self._repository = repository
        self._twitch_resolver = twitch_resolver

    async def execute(self, twitch_url: TwitchUrl, format_id: str | None = None) -> str:
        """
        Twitch URLをストリームURLに解決します

        Args:
            twitch_url: Twitch動画URL（TwitchUrl ValueObject）
            format_id: フォーマットID（オプショナル）

        Returns:
            str: 解決済みの直接ストリームURL

        Raises:
            InvalidVideoIdError: video_idの抽出に失敗した場合
            InvalidUrlError: 無効なURLが指定された場合
            TwitchResolverError: Twitch APIへのアクセスに失敗した場合
            CacheError: キャッシュ操作に失敗した場合
        """
        video_id = twitch_url.extract_video_id()

        # TwitchはHLS形式のみなので、hls=Trueとしてキャッシュを検索
        cached = await self._repository.find_by_video_id(str(video_id), hls=True)

        if cached and not cached.is_expired():
            return cached.resolved_url.value

        result = await self._twitch_resolver.resolve_url(str(twitch_url), format_id)

        stream_url = StreamUrl.create(
            video_id=str(video_id),
            resolved_url=result.resolved_url,
            ttl_seconds=result.ttl_seconds,
        )
        await self._repository.save(stream_url, hls=True)

        return result.resolved_url
