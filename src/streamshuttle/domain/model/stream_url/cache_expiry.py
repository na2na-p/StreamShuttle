"""
CacheExpiry ValueObjectモジュール

キャッシュ有効期限を表現するValueObjectを定義します。
"""

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class CacheExpiry:
    """
    キャッシュ有効期限を表現するValueObject

    ストリームURLキャッシュの有効期限を管理します。
    このValueObjectは不変であり、期限切れ判定や残り時間計算の機能を提供します。

    Attributes:
        _expiry_at: 有効期限日時（タイムゾーン情報を含む、プライベートフィールド）
    """

    _expiry_at: datetime

    @property
    def expiry_at(self) -> datetime:
        """
        有効期限日時を取得します

        Returns:
            datetime: 有効期限日時
        """
        return self._expiry_at

    def __post_init__(self) -> None:
        """
        インスタンス生成後のバリデーション

        有効期限日時がタイムゾーン情報を持つことを検証します。

        Raises:
            ValueError: タイムゾーン情報がない場合
        """
        if self._expiry_at.tzinfo is None:
            raise ValueError("有効期限日時はタイムゾーン情報を持つ必要があります")

    def is_expired(self) -> bool:
        """
        キャッシュが期限切れかを判定します

        現在時刻（UTC）と有効期限を比較し、期限切れかを判定します。

        Returns:
            bool: 期限切れの場合True、有効な場合False
        """
        now = datetime.now(UTC)
        return now >= self._expiry_at

    def ttl_seconds(self) -> int:
        """
        キャッシュの残り有効時間を秒単位で計算します

        現在時刻（UTC）から有効期限までの残り秒数を計算します。
        既に期限切れの場合は0を返します。

        Returns:
            int: 残り有効秒数（期限切れの場合は0）
        """
        now = datetime.now(UTC)
        remaining = (self._expiry_at - now).total_seconds()
        return max(0, int(remaining))
