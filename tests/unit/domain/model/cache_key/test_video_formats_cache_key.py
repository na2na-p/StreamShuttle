"""
VideoFormatsCacheKey ValueObjectのテストモジュール
"""

import pytest

from streamshuttle.domain.model.cache_key.video_formats_cache_key import (
    VideoFormatsCacheKey,
)
from streamshuttle.domain.model.stream_url.youtube_video_id import YouTubeVideoId


class TestVideoFormatsCacheKey:
    """VideoFormatsCacheKeyのテストクラス"""

    @pytest.mark.parametrize(
        "video_id_value, expected_key",
        [
            pytest.param(
                "dQw4w9WgXcQ",
                "video_formats:dQw4w9WgXcQ",
                id="正常系: video_idから正しいキーが生成される",
            ),
            pytest.param(
                "abc_def-123",
                "video_formats:abc_def-123",
                id="正常系: 特殊文字を含むvideo_idから正しいキーが生成される",
            ),
        ],
    )
    def test_value_property_returns_correct_cache_key(
        self, video_id_value: str, expected_key: str
    ) -> None:
        """valueプロパティが正しいキャッシュキー文字列を返すことを検証"""
        video_id = YouTubeVideoId(_value=video_id_value)
        cache_key = VideoFormatsCacheKey(_video_id=video_id)

        assert cache_key.value == expected_key

    def test_str_returns_cache_key_value(self) -> None:
        """__str__がvalueと同じ文字列を返すことを検証"""
        video_id = YouTubeVideoId(_value="dQw4w9WgXcQ")
        cache_key = VideoFormatsCacheKey(_video_id=video_id)

        assert str(cache_key) == cache_key.value
        assert str(cache_key) == "video_formats:dQw4w9WgXcQ"

    def test_immutability(self) -> None:
        """VideoFormatsCacheKeyがイミュータブルであることを検証"""
        video_id = YouTubeVideoId(_value="dQw4w9WgXcQ")
        cache_key = VideoFormatsCacheKey(_video_id=video_id)

        with pytest.raises(AttributeError):
            cache_key._video_id = YouTubeVideoId(_value="abc_def-123")  # type: ignore

    def test_equality_same_values(self) -> None:
        """同じ値を持つVideoFormatsCacheKeyが等しいことを検証"""
        video_id1 = YouTubeVideoId(_value="dQw4w9WgXcQ")
        video_id2 = YouTubeVideoId(_value="dQw4w9WgXcQ")
        cache_key1 = VideoFormatsCacheKey(_video_id=video_id1)
        cache_key2 = VideoFormatsCacheKey(_video_id=video_id2)

        assert cache_key1 == cache_key2

    def test_equality_different_video_id(self) -> None:
        """video_idが異なる場合にVideoFormatsCacheKeyが異なることを検証"""
        video_id1 = YouTubeVideoId(_value="dQw4w9WgXcQ")
        video_id2 = YouTubeVideoId(_value="abc_def-123")
        cache_key1 = VideoFormatsCacheKey(_video_id=video_id1)
        cache_key2 = VideoFormatsCacheKey(_video_id=video_id2)

        assert cache_key1 != cache_key2
