"""
プレイリスト情報 DTO定義モジュール

QueryServiceから返されるプレイリストの基本情報を保持する
Data Transfer Objectを定義します。
"""

from pydantic import BaseModel, ConfigDict, Field


class PlaylistInfoDto(BaseModel):
    """
    プレイリスト情報 DTO

    YouTubeプレイリストの基本情報を保持します。

    Attributes:
        playlist_id: プレイリストID
        title: プレイリストタイトル
        uploader: プレイリスト作成者名（取得できない場合は空文字）
        item_count: 実際に取得できた再生可能な動画数
        truncated: 上限件数により一部の動画が切り捨てられたか
    """

    model_config = ConfigDict(frozen=True)

    playlist_id: str = Field(..., description="プレイリストID")
    title: str = Field(..., description="プレイリストタイトル")
    uploader: str = Field(..., description="プレイリスト作成者名")
    item_count: int = Field(..., description="再生可能な動画数")
    truncated: bool = Field(False, description="上限件数により切り捨てられたか")
