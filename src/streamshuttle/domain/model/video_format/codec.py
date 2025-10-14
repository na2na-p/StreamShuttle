"""
Codec ValueObjectモジュール

コーデック情報を表現するValueObjectを定義します。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Codec:
    """
    コーデック情報を表現するValueObject

    YouTube動画のコーデック（エンコード方式）情報を表現します。
    このValueObjectは不変であり、異なるコーデック（h264、vp9、aac等）を
    表現するために使用されます。

    Attributes:
        _value: コーデック文字列（例: "h264", "vp9", "aac", "opus"、プライベートフィールド）
    """

    _value: str

    @property
    def value(self) -> str:
        """
        コーデック情報の値を取得します

        Returns:
            str: コーデック文字列
        """
        return self._value

    def __post_init__(self) -> None:
        """
        インスタンス生成後のバリデーション

        コーデック情報が空でないことを検証します。

        Raises:
            ValueError: コーデック情報が空の場合
        """
        if not self._value:
            raise ValueError("コーデック情報が空です")
