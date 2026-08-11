"""
プレイリスト統合 DTO定義モジュール

プレイリスト情報と項目一覧を統合して保持するData Transfer Objectを定義します。
"""

from pydantic import BaseModel, ConfigDict

from streamshuttle.usecase.dto.playlist_info_dto import PlaylistInfoDto
from streamshuttle.usecase.dto.playlist_item_dto import PlaylistItemDto


class PlaylistDto(BaseModel):
    """
    プレイリスト統合 DTO

    プレイリスト情報と項目一覧を統合して保持します。
    キャッシュのシリアライズ/デシリアライズに使用されます。

    Attributes:
        playlist_info: プレイリスト基本情報
        items: プレイリストに含まれる動画一覧
    """

    model_config = ConfigDict(frozen=True)

    playlist_info: PlaylistInfoDto
    items: list[PlaylistItemDto]
