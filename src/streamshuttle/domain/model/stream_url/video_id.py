"""
VideoId ValueObjectモジュール

YouTubeビデオIDを表現するValueObjectを定義します。
"""

import re
from dataclasses import dataclass

from streamshuttle.shared.exceptions import InvalidVideoIdError


@dataclass(frozen=True)
class VideoId:
    """
    YouTubeビデオIDを表現するValueObject

    YouTubeビデオIDは11文字の英数字と一部記号（-、_）から構成されます。
    このValueObjectは不変であり、生成時にビデオID形式の妥当性を検証します。

    Attributes:
        _value: YouTubeビデオID文字列（11文字、プライベートフィールド）
    """

    _value: str

    @property
    def value(self) -> str:
        """
        ビデオIDの値を取得します

        Returns:
            str: YouTubeビデオID文字列
        """
        return self._value

    def __post_init__(self) -> None:
        """
        インスタンス生成後のバリデーション

        YouTubeビデオIDの形式を検証します。
        - 11文字であること
        - 英数字、ハイフン、アンダースコアのみで構成されていること

        Raises:
            InvalidVideoIdError: ビデオIDの形式が不正な場合
        """
        if not self._value:
            raise InvalidVideoIdError("ビデオIDが空です")

        if len(self._value) != 11:
            raise InvalidVideoIdError(f"ビデオIDは11文字である必要があります: {self._value}")

        # YouTube Video IDは英数字、ハイフン、アンダースコアのみ
        if not re.match(r"^[a-zA-Z0-9_-]{11}$", self._value):
            raise InvalidVideoIdError(f"ビデオIDの形式が不正です: {self._value}")
