"""
プレイリストRepository Protocolモジュール

プレイリスト情報のキャッシュ保存を行うRepositoryインターフェースを定義します。
"""

from typing import Protocol

from streamshuttle.usecase.dto.playlist_dto import PlaylistDto


class PlaylistRepository(Protocol):
    """
    プレイリストRepository Protocol

    プレイリスト情報をキャッシュに保存するためのインターフェースです。
    CQRS原則に従い、Command（書き込み）操作を担当します。

    実装クラスはInfrastructure層に配置されます。
    """

    async def save(self, playlist_id: str, playlist: PlaylistDto) -> None:
        """
        プレイリスト情報をキャッシュに保存します

        Args:
            playlist_id: YouTubeプレイリストID
            playlist: 保存するプレイリスト情報

        Raises:
            CacheException: キャッシュ操作に失敗した場合
        """
        ...
