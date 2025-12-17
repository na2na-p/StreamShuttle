"""
VideoFormatsCacheKey ValueObjectモジュール

Video Formatsのキャッシュキーを表現するValueObjectを定義します。
"""

from dataclasses import dataclass

from streamshuttle.domain.model.stream_url.video_id import VideoId


@dataclass(frozen=True)
class VideoFormatsCacheKey:
    """
    Video Formatsのキャッシュキーを表現するValueObject

    VideoIdから一意なキャッシュキーを生成します。
    このValueObjectは不変であり、キャッシュキー形式の一貫性を保証します。

    Attributes:
        _video_id: YouTube動画ID
    """

    _video_id: VideoId

    @property
    def value(self) -> str:
        """
        キャッシュキー文字列を返す

        Returns:
            str: 「video_formats:video_id」形式のキャッシュキー
        """
        return f"video_formats:{self._video_id.value}"

    def __str__(self) -> str:
        """キャッシュキーの文字列表現を返す"""
        return self.value
