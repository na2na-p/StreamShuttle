"""
プレイリスト取得UseCaseモジュール

YouTubeプレイリストの動画一覧を取得するUseCaseを定義します。
"""

from streamshuttle.domain.model.youtube_playlist import YoutubePlaylistUrl
from streamshuttle.usecase.dto.playlist_dto import PlaylistDto
from streamshuttle.usecase.dto.playlist_info_dto import PlaylistInfoDto
from streamshuttle.usecase.dto.playlist_item_dto import PlaylistItemDto
from streamshuttle.usecase.query_service.playlist_cache_query_service import (
    PlaylistCacheQueryService,
)
from streamshuttle.usecase.query_service.playlist_query_service import PlaylistQueryService
from streamshuttle.usecase.repository.playlist_repository import PlaylistRepository


class GetPlaylistUseCase:
    """
    プレイリスト取得UseCase

    YouTubeプレイリストURLから再生可能な動画一覧を取得します。
    Redisキャッシュを活用し、2回目以降のリクエストを高速化します。
    CQRS原則に準拠した参照専用のUseCaseです。
    """

    def __init__(
        self,
        query_service: PlaylistQueryService,
        repository: PlaylistRepository,
        cache_query_service: PlaylistCacheQueryService,
    ) -> None:
        """
        GetPlaylistUseCaseを初期化します

        Args:
            query_service: プレイリスト参照用QueryService（yt-dlp呼び出し）
            repository: プレイリストキャッシュ保存用Repository
            cache_query_service: プレイリストキャッシュ取得用QueryService
        """
        self._query_service = query_service
        self._repository = repository
        self._cache_query_service = cache_query_service

    async def execute(self, playlist_url: str) -> tuple[PlaylistInfoDto, list[PlaylistItemDto]]:
        """
        プレイリストURLから動画一覧とプレイリスト情報を取得します

        1回目のリクエスト: yt-dlpで情報取得 → Redisにキャッシュ → 返却
        2回目以降: Redisキャッシュから取得 → 返却

        Args:
            playlist_url: YouTubeプレイリストURL（listパラメータを含むURL）

        Returns:
            tuple[PlaylistInfoDto, list[PlaylistItemDto]]: プレイリスト情報と動画一覧

        Raises:
            InvalidUrlError: 無効なURLが指定された場合
            InvalidPlaylistIdError: プレイリストIDが抽出できない、または不正な場合
            PlaylistNotFoundError: プレイリストが存在しない、非公開、
                または再生可能な動画を含まない場合
            YouTubeResolverError: YouTubeへのアクセスに失敗した場合
        """
        # 1. URLを検証し、プレイリストIDを抽出
        validated_url = YoutubePlaylistUrl(_value=playlist_url)
        playlist_id = validated_url.extract_playlist_id().value

        # 2. キャッシュチェック
        cached_playlist = await self._cache_query_service.find_by_playlist_id(playlist_id)
        if cached_playlist is not None:
            return cached_playlist.playlist_info, cached_playlist.items

        # 3. キャッシュミス: yt-dlpで取得
        # watch URLにlistパラメータが付いている場合でもプレイリスト全体を取得するため、
        # 正規化済みURL（/playlist?list=...）を使用する
        playlist_info, items = await self._query_service.get_playlist(
            validated_url.to_canonical_url()
        )

        # 4. キャッシュに保存
        playlist_dto = PlaylistDto(playlist_info=playlist_info, items=items)
        await self._repository.save(playlist_id=playlist_id, playlist=playlist_dto)

        # 5. 結果を返す
        return playlist_info, items
