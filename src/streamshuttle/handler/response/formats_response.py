"""
フォーマット一覧レスポンスモデル定義モジュール

GET /formats エンドポイントのレスポンス構造を定義します。
"""

from pydantic import BaseModel, ConfigDict, Field

from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto


class FormatsResponse(BaseModel):
    """
    フォーマット一覧レスポンスモデル

    YouTube動画のフォーマット一覧と動画情報を含むレスポンスを表現します。

    Attributes:
        video_info: 動画の基本情報
        formats: 利用可能なフォーマット一覧
        csrf_token: CSRFトークン
    """

    model_config = ConfigDict(frozen=True)

    video_info: VideoInfoDto = Field(..., description="動画情報")
    formats: list[VideoFormatDto] = Field(..., description="利用可能なフォーマット一覧")
    csrf_token: str = Field(..., description="CSRFトークン")
