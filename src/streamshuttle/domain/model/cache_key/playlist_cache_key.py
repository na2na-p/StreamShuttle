"""
PlaylistCacheKey ValueObjectモジュール

プレイリスト情報のキャッシュキーを表現するValueObjectを定義します。
"""

from dataclasses import dataclass

from streamshuttle.domain.model.youtube_playlist.youtube_playlist_id import (
    YouTubePlaylistId,
)


@dataclass(frozen=True)
class PlaylistCacheKey:
    """
    プレイリスト情報のキャッシュキーを表現するValueObject

    YouTubePlaylistIdから一意なキャッシュキーを生成します。
    このValueObjectは不変であり、キャッシュキー形式の一貫性を保証します。

    Attributes:
        _playlist_id: YouTubeプレイリストID
    """

    _playlist_id: YouTubePlaylistId

    @property
    def value(self) -> str:
        """
        キャッシュキー文字列を返す

        Returns:
            str: 「playlist:playlist_id」形式のキャッシュキー
        """
        return f"playlist:{self._playlist_id.value}"

    def __str__(self) -> str:
        """キャッシュキーの文字列表現を返す"""
        return self.value
