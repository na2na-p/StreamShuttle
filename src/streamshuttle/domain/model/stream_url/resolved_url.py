"""
ResolvedUrl ValueObjectモジュール

解決済みストリームURLを表現するValueObjectを定義します。
"""

from dataclasses import dataclass
from urllib.parse import urlparse

from streamshuttle.shared.exceptions import InvalidUrlError


@dataclass(frozen=True)
class ResolvedUrl:
    """
    解決済みストリームURLを表現するValueObject

    YouTube動画から解決された実際のストリームURL（m3u8など）を表現します。
    このValueObjectは不変であり、生成時にURL形式の妥当性を検証します。

    Attributes:
        _value: ストリームURL文字列（HTTP/HTTPSスキームを持つ、プライベートフィールド）
    """

    _value: str

    @property
    def value(self) -> str:
        """
        ストリームURLの値を取得します

        Returns:
            str: ストリームURL文字列
        """
        return self._value

    def __post_init__(self) -> None:
        """
        インスタンス生成後のバリデーション

        ストリームURLの形式を検証します。
        - 空文字列でないこと
        - HTTP/HTTPSスキームを持つこと
        - 有効なURL形式であること

        Raises:
            InvalidUrlError: URLの形式が不正な場合
        """
        if not self._value:
            raise InvalidUrlError("URLが空です")

        try:
            parsed = urlparse(self._value)
        except Exception as e:
            raise InvalidUrlError(f"URLのパースに失敗しました: {self._value}") from e

        # HTTP/HTTPSスキームを持つことを検証
        if parsed.scheme not in ("http", "https"):
            raise InvalidUrlError(f"URLはHTTP/HTTPSスキームを持つ必要があります: {self._value}")

        # ネットロケーション（ホスト）が存在することを検証
        if not parsed.netloc:
            raise InvalidUrlError(f"URLにホスト名が含まれていません: {self._value}")
