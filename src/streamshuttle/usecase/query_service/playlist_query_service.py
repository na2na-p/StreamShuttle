"""
プレイリストQueryService Protocolモジュール

YouTubeプレイリストの情報を取得するQueryServiceインターフェースを定義します。
"""

from typing import Protocol

from streamshuttle.usecase.dto.playlist_info_dto import PlaylistInfoDto
from streamshuttle.usecase.dto.playlist_item_dto import PlaylistItemDto


class PlaylistQueryService(Protocol):
    """
    プレイリストQueryService Protocol

    YouTubeプレイリストURLから、プレイリスト情報と含まれる動画一覧を取得するための
    インターフェースです。CQRS原則に従い、Query（読み取り）操作を担当します。

    実装クラスはInfrastructure層に配置されます。
    """

    async def get_playlist(
        self, playlist_url: str
    ) -> tuple[PlaylistInfoDto, list[PlaylistItemDto]]:
        """
        プレイリストURLからプレイリスト情報と動画一覧を取得します

        Args:
            playlist_url: YouTubeプレイリストURL

        Returns:
            tuple[PlaylistInfoDto, list[PlaylistItemDto]]: プレイリスト情報と動画一覧

        Raises:
            InvalidUrlError: 無効なURLが指定された場合
            PlaylistNotFoundError: プレイリストが存在しない、非公開、
                または再生可能な動画を含まない場合
            YouTubeResolverError: YouTubeへのアクセスに失敗した場合
        """
        ...
