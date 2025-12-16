"""
FormatUrlCacheKey ValueObjectモジュール

フォーマットURLのキャッシュキーを表現するValueObjectを定義します。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FormatUrlCacheKey:
    """
    フォーマットURLのキャッシュキーを表現するValueObject

    video_idとformat_idの組み合わせから一意なキャッシュキーを生成します。
    このValueObjectは不変であり、キャッシュキー形式の一貫性を保証します。

    Attributes:
        _video_id: YouTube動画ID
        _format_id: フォーマットID
    """

    _video_id: str
    _format_id: str

    @property
    def value(self) -> str:
        """
        キャッシュキー文字列を返す

        Returns:
            str: 「format_url:video_id:format_id」形式のキャッシュキー
        """
        return f"format_url:{self._video_id}:{self._format_id}"

    def __str__(self) -> str:
        """キャッシュキーの文字列表現を返す"""
        return self.value
