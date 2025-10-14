"""
ビデオフォーマット DTO定義モジュール

QueryServiceから返されるビデオフォーマット情報を保持するData Transfer Objectを定義します。
"""

from pydantic import BaseModel, ConfigDict, Field


class VideoFormatDto(BaseModel):
    """
    ビデオフォーマット DTO

    YouTube動画の利用可能なフォーマット情報を保持します。
    QueryServiceがyt-dlpから取得した動画フォーマット情報をこの形式で返します。

    Attributes:
        format_id: フォーマットID（yt-dlpが識別するフォーマットの一意識別子）
        quality: 動画品質の説明（例: "1080p", "720p60"）
        codec: 使用されているコーデック（例: "vp9", "avc1"）
        url: フォーマットに対応する直接ストリームURL
        has_audio: 音声が含まれているか
        has_video: 動画が含まれているか
    """

    model_config = ConfigDict(frozen=True)

    format_id: str = Field(..., description="フォーマットID")
    quality: str = Field(..., description="動画品質の説明")
    codec: str = Field(..., description="使用されているコーデック")
    url: str = Field(..., description="フォーマットに対応する直接ストリームURL")
    has_audio: bool = Field(..., description="音声が含まれているか")
    has_video: bool = Field(..., description="動画が含まれているか")
