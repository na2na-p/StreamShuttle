"""
Quality ValueObjectモジュール

画質情報を表現するValueObjectを定義します。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Quality:
    """
    画質情報を表現するValueObject

    YouTube動画の画質（解像度）情報を表現します。
    このValueObjectは不変であり、異なる画質レベル（1080p、720p、audio等）を
    表現するために使用されます。

    Attributes:
        _value: 画質文字列（例: "1080p", "720p", "480p", "audio"、プライベートフィールド）
    """

    _value: str

    @property
    def value(self) -> str:
        """
        画質情報の値を取得します

        Returns:
            str: 画質文字列
        """
        return self._value

    def __post_init__(self) -> None:
        """
        インスタンス生成後のバリデーション

        画質情報が空でないことを検証します。

        Raises:
            ValueError: 画質情報が空の場合
        """
        if not self._value:
            raise ValueError("画質情報が空です")
