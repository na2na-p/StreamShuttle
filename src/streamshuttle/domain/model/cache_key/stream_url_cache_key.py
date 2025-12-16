"""
StreamUrlCacheKey ValueObjectモジュール

StreamURLのキャッシュキーを表現するValueObjectを定義します。
"""

from dataclasses import dataclass

from streamshuttle.domain.model.stream_url.video_id import VideoId


@dataclass(frozen=True)
class StreamUrlCacheKey:
    """
    StreamURLのキャッシュキーを表現するValueObject

    VideoIdとuse_hlsフラグの組み合わせから一意なキャッシュキーを生成します。
    このValueObjectは不変であり、キャッシュキー形式の一貫性を保証します。

    Attributes:
        _video_id: YouTube動画ID
        _use_hls: HLS形式使用フラグ
    """

    _video_id: VideoId
    _use_hls: bool

    @property
    def value(self) -> str:
        """
        キャッシュキー文字列を返す

        Returns:
            str: 「video_id:hls:use_hls」形式のキャッシュキー
        """
        return f"{self._video_id.value}:hls:{self._use_hls}"

    def __str__(self) -> str:
        """キャッシュキーの文字列表現を返す"""
        return self.value
