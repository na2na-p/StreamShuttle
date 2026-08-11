"""
プレイリスト項目 DTO定義モジュール

QueryServiceから返されるプレイリスト内の動画1件分の情報を保持する
Data Transfer Objectを定義します。
"""

from pydantic import BaseModel, ConfigDict, Field


class PlaylistItemDto(BaseModel):
    """
    プレイリスト項目 DTO

    プレイリストに含まれる動画1件の基本情報を保持します。
    プレイリスト取得はフラット抽出（各動画の詳細取得を行わない）のため、
    ストリームURLは含まれません。再生時に別途解決されます。

    Attributes:
        video_id: YouTube動画ID
        title: 動画タイトル
        url: 動画の視聴URL（https://www.youtube.com/watch?v=xxxxx形式）
        duration_seconds: 動画の長さ（秒）。取得できない場合はNone
        thumbnail_url: サムネイルURL
    """

    model_config = ConfigDict(frozen=True)

    video_id: str = Field(..., description="YouTube動画ID")
    title: str = Field(..., description="動画タイトル")
    url: str = Field(..., description="動画の視聴URL")
    duration_seconds: int | None = Field(None, description="動画の長さ（秒）")
    thumbnail_url: str = Field(..., description="サムネイルURL")
