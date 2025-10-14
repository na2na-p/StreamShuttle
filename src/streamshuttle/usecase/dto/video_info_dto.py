"""
動画情報 DTO定義モジュール

QueryServiceから返される動画情報を保持するData Transfer Objectを定義します。
"""

from pydantic import BaseModel, ConfigDict, Field


class VideoInfoDto(BaseModel):
    """
    動画情報 DTO

    YouTube動画の基本情報を保持します。
    QueryServiceがyt-dlpから取得した動画情報をこの形式で返します。

    Attributes:
        video_id: 動画ID（YouTubeの11文字のID）
        title: 動画タイトル
        thumbnail_url: サムネイルURL
    """

    model_config = ConfigDict(frozen=True)

    video_id: str = Field(..., description="動画ID")
    title: str = Field(..., description="動画タイトル")
    thumbnail_url: str = Field(..., description="サムネイルURL")
