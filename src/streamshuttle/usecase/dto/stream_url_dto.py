"""
ストリームURL DTO定義モジュール

QueryServiceから返されるストリームURL情報を保持するData Transfer Objectを定義します。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StreamUrlDto(BaseModel):
    """
    ストリームURL DTO

    YouTube動画IDに対応する解決済みストリームURLとその有効期限を保持します。
    QueryServiceがRedisキャッシュから取得したデータをこの形式で返します。

    Attributes:
        video_id: YouTube動画ID（11桁の英数字）
        resolved_url: 解決済みの直接ストリームURL
        expiry_at: URLの有効期限（この時刻を過ぎるとURLは無効になる）
    """

    model_config = ConfigDict(frozen=True)

    video_id: str = Field(..., description="YouTube動画ID", min_length=11, max_length=11)
    resolved_url: str = Field(..., description="解決済みの直接ストリームURL")
    expiry_at: datetime = Field(..., description="URLの有効期限")
