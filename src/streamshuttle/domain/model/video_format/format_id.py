"""
FormatId ValueObjectモジュール

フォーマットIDを表現するValueObjectを定義します。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FormatId:
    """
    フォーマットIDを表現するValueObject

    YouTube動画のストリーム形式を識別するフォーマットIDを表現します。
    このValueObjectは不変であり、異なるフォーマット（画質、コーデック等）を
    一意に識別するために使用されます。

    Attributes:
        _value: フォーマットID文字列（例: "137", "248", "140"、プライベートフィールド）
    """

    _value: str

    @property
    def value(self) -> str:
        """
        フォーマットIDの値を取得します

        Returns:
            str: フォーマットID文字列
        """
        return self._value

    def __post_init__(self) -> None:
        """
        インスタンス生成後のバリデーション

        フォーマットIDが空でないことを検証します。

        Raises:
            ValueError: フォーマットIDが空の場合
        """
        if not self._value:
            raise ValueError("フォーマットIDが空です")
