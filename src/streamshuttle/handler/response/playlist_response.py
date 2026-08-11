"""
プレイリストレスポンスモデル定義モジュール

GET /playlist エンドポイントのレスポンス構造を定義します。
"""

from pydantic import BaseModel, ConfigDict, Field

from streamshuttle.usecase.dto.playlist_info_dto import PlaylistInfoDto
from streamshuttle.usecase.dto.playlist_item_dto import PlaylistItemDto


class PlaylistResponse(BaseModel):
    """
    プレイリストレスポンスモデル

    YouTubeプレイリストの基本情報と再生可能な動画一覧を含むレスポンスを表現します。

    Attributes:
        playlist_info: プレイリストの基本情報
        items: 再生可能な動画一覧
    """

    model_config = ConfigDict(frozen=True)

    playlist_info: PlaylistInfoDto = Field(..., description="プレイリスト情報")
    items: list[PlaylistItemDto] = Field(..., description="再生可能な動画一覧")
