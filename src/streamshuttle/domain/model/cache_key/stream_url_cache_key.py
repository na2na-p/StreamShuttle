"""
StreamUrlCacheKey ValueObjectモジュール

StreamURLのキャッシュキーを表現するValueObjectを定義します。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StreamUrlCacheKey:
    """
    StreamURLのキャッシュキーを表現するValueObject

    プラットフォーム、ビデオID値、hlsフラグの組み合わせから一意なキャッシュキーを生成します。
    このValueObjectは不変であり、キャッシュキー形式の一貫性を保証します。

    Attributes:
        _platform: プラットフォーム識別子（"youtube" | "twitch"）
        _video_id_value: ビデオID値（文字列）
        _hls: HLS形式使用フラグ
    """

    _platform: str
    _video_id_value: str
    _hls: bool

    @property
    def value(self) -> str:
        """
        キャッシュキー文字列を返す

        Returns:
            str: 「{platform}:{video_id}:hls:{hls}」形式のキャッシュキー
        """
        return f"{self._platform}:{self._video_id_value}:hls:{self._hls}"

    def __str__(self) -> str:
        """キャッシュキーの文字列表現を返す"""
        return self.value
