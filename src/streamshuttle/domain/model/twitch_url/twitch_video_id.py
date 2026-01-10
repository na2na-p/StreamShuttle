"""
TwitchVideoId ValueObjectモジュール

TwitchビデオIDを表現するValueObjectを定義します。
"""

import re
from dataclasses import dataclass

from streamshuttle.shared.exceptions import InvalidVideoIdError


@dataclass(frozen=True)
class TwitchVideoId:
    """
    TwitchビデオIDを表現するValueObject

    TwitchビデオIDはVOD ID（数字のみ）、チャンネル名、またはクリップスラグから構成されます。
    このValueObjectは不変であり、生成時にビデオID形式の妥当性を検証します。

    Attributes:
        _value: TwitchビデオID文字列（プライベートフィールド）
    """

    _value: str

    @property
    def value(self) -> str:
        """
        ビデオIDの値を取得します

        Returns:
            str: TwitchビデオID文字列
        """
        return self._value

    def __post_init__(self) -> None:
        """
        インスタンス生成後のバリデーション

        TwitchビデオIDの形式を検証します。
        - 空でないこと
        - 英数字、ハイフン、アンダースコアのみで構成されていること

        Raises:
            InvalidVideoIdError: ビデオIDの形式が不正な場合
        """
        if not self._value:
            raise InvalidVideoIdError("ビデオIDが空です")

        # Twitch Video/Clip IDは英数字、ハイフン、アンダースコアで構成
        # VOD ID: 数字のみ（例: 1234567890）
        # チャンネル名: 英数字とアンダースコア（例: channel_name）
        # クリップスラグ: 英数字とハイフン（例: ClipSlug-abc123）
        if not re.match(r"^[a-zA-Z0-9_-]+$", self._value):
            raise InvalidVideoIdError(f"ビデオIDの形式が不正です: {self._value}")

    def __str__(self) -> str:
        """ビデオIDの文字列表現を返す"""
        return self._value
