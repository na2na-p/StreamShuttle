"""
プレイリストキャッシュQueryService Protocolモジュール

キャッシュからプレイリスト情報を取得するQueryServiceインターフェースを定義します。
"""

from typing import Protocol

from streamshuttle.usecase.dto.playlist_dto import PlaylistDto


class PlaylistCacheQueryService(Protocol):
    """
    プレイリストキャッシュQueryService Protocol

    キャッシュからプレイリスト情報を取得するためのインターフェースです。
    CQRS原則に従い、Query（読み取り）操作を担当します。

    実装クラスはInfrastructure層に配置されます。
    """

    async def find_by_playlist_id(self, playlist_id: str) -> PlaylistDto | None:
        """
        プレイリストIDでプレイリスト情報を取得します

        Args:
            playlist_id: YouTubeプレイリストID

        Returns:
            PlaylistDto | None: キャッシュが存在する場合はPlaylistDto、存在しない場合はNone

        Note:
            キャッシュ取得に失敗した場合やJSON破損時は例外を投げず、Noneを返します。
            これにより、キャッシュミスとして扱われ、通常のyt-dlp処理にフォールバックします。
        """
        ...
