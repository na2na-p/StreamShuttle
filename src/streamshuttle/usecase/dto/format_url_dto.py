"""
フォーマットURL DTO定義モジュール

QueryServiceから返されるフォーマットURL情報を保持するData Transfer Objectを定義します。
"""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class FormatUrlDto(BaseModel):
    """
    フォーマットURL DTO

    video_idとformat_idに対応するキャッシュされたフォーマットURLとその有効期限を保持します。
    FormatUrlQueryServiceがRedisキャッシュから取得したデータをこの形式で返します。

    Attributes:
        video_id: YouTube動画ID
        format_id: フォーマットID
        resolved_url: 解決済みのフォーマットURL
        expiry_at: URLの有効期限（この時刻を過ぎるとURLは無効になる）
    """

    model_config = ConfigDict(frozen=True)

    video_id: str = Field(..., description="YouTube動画ID")
    format_id: str = Field(..., description="フォーマットID")
    resolved_url: str = Field(..., description="解決済みのフォーマットURL")
    expiry_at: datetime = Field(..., description="URLの有効期限")

    def is_valid(self) -> bool:
        """
        キャッシュが有効期限内かを判定します

        Returns:
            bool: 有効期限内の場合True、期限切れの場合False
        """
        return self.expiry_at > datetime.now(UTC)

    def is_expired(self) -> bool:
        """
        キャッシュが期限切れかを判定します

        Returns:
            bool: 期限切れの場合True、有効な場合False
        """
        return not self.is_valid()
