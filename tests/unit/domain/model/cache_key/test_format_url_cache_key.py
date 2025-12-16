"""
FormatUrlCacheKey ValueObjectのテストモジュール
"""

import pytest

from streamshuttle.domain.model.cache_key.format_url_cache_key import FormatUrlCacheKey


class TestFormatUrlCacheKey:
    """FormatUrlCacheKeyのテストクラス"""

    @pytest.mark.parametrize(
        "video_id, format_id, expected_key",
        [
            pytest.param(
                "dQw4w9WgXcQ",
                "22",
                "format_url:dQw4w9WgXcQ:22",
                id="正常系: 数値format_idでキャッシュキーが正しく生成される",
            ),
            pytest.param(
                "dQw4w9WgXcQ",
                "best",
                "format_url:dQw4w9WgXcQ:best",
                id="正常系: 文字列format_idでキャッシュキーが正しく生成される",
            ),
            pytest.param(
                "abc_def-123",
                "1080p",
                "format_url:abc_def-123:1080p",
                id="正常系: 特殊文字を含むvideo_idでキャッシュキーが正しく生成される",
            ),
        ],
    )
    def test_value_property_returns_correct_cache_key(
        self, video_id: str, format_id: str, expected_key: str
    ) -> None:
        """valueプロパティが正しいキャッシュキー文字列を返すことを検証"""
        cache_key = FormatUrlCacheKey(_video_id=video_id, _format_id=format_id)

        assert cache_key.value == expected_key

    def test_str_returns_cache_key_value(self) -> None:
        """__str__がvalueと同じ文字列を返すことを検証"""
        cache_key = FormatUrlCacheKey(_video_id="dQw4w9WgXcQ", _format_id="22")

        assert str(cache_key) == cache_key.value
        assert str(cache_key) == "format_url:dQw4w9WgXcQ:22"

    def test_immutability(self) -> None:
        """FormatUrlCacheKeyがイミュータブルであることを検証"""
        cache_key = FormatUrlCacheKey(_video_id="dQw4w9WgXcQ", _format_id="22")

        with pytest.raises(AttributeError):
            cache_key._video_id = "abc_def-123"  # type: ignore

        with pytest.raises(AttributeError):
            cache_key._format_id = "1080p"  # type: ignore

    def test_equality_same_values(self) -> None:
        """同じ値を持つFormatUrlCacheKeyが等しいことを検証"""
        cache_key1 = FormatUrlCacheKey(_video_id="dQw4w9WgXcQ", _format_id="22")
        cache_key2 = FormatUrlCacheKey(_video_id="dQw4w9WgXcQ", _format_id="22")

        assert cache_key1 == cache_key2

    def test_equality_different_format_id(self) -> None:
        """format_idが異なる場合にFormatUrlCacheKeyが異なることを検証"""
        cache_key1 = FormatUrlCacheKey(_video_id="dQw4w9WgXcQ", _format_id="22")
        cache_key2 = FormatUrlCacheKey(_video_id="dQw4w9WgXcQ", _format_id="1080p")

        assert cache_key1 != cache_key2

    def test_equality_different_video_id(self) -> None:
        """video_idが異なる場合にFormatUrlCacheKeyが異なることを検証"""
        cache_key1 = FormatUrlCacheKey(_video_id="dQw4w9WgXcQ", _format_id="22")
        cache_key2 = FormatUrlCacheKey(_video_id="abc_def-123", _format_id="22")

        assert cache_key1 != cache_key2
