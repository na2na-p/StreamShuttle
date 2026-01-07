"""
StreamUrlCacheKey ValueObjectのテストモジュール
"""

import pytest

from streamshuttle.domain.model.cache_key.stream_url_cache_key import StreamUrlCacheKey
from streamshuttle.domain.model.stream_url.video_id import VideoId


class TestStreamUrlCacheKey:
    """StreamUrlCacheKeyのテストクラス"""

    @pytest.mark.parametrize(
        "video_id_value, hls, expected_key",
        [
            pytest.param(
                "dQw4w9WgXcQ",
                False,
                "dQw4w9WgXcQ:hls:False",
                id="正常系: hls=Falseでキャッシュキーが正しく生成される",
            ),
            pytest.param(
                "dQw4w9WgXcQ",
                True,
                "dQw4w9WgXcQ:hls:True",
                id="正常系: hls=Trueでキャッシュキーが正しく生成される",
            ),
            pytest.param(
                "abc_def-123",
                False,
                "abc_def-123:hls:False",
                id="正常系: 特殊文字を含むvideo_idでキャッシュキーが正しく生成される",
            ),
        ],
    )
    def test_value_property_returns_correct_cache_key(
        self, video_id_value: str, hls: bool, expected_key: str
    ) -> None:
        """valueプロパティが正しいキャッシュキー文字列を返すことを検証"""
        video_id = VideoId(_value=video_id_value)
        cache_key = StreamUrlCacheKey(_video_id=video_id, _hls=hls)

        assert cache_key.value == expected_key

    def test_str_returns_cache_key_value(self) -> None:
        """__str__がvalueと同じ文字列を返すことを検証"""
        video_id = VideoId(_value="dQw4w9WgXcQ")
        cache_key = StreamUrlCacheKey(_video_id=video_id, _hls=False)

        assert str(cache_key) == cache_key.value
        assert str(cache_key) == "dQw4w9WgXcQ:hls:False"

    def test_immutability(self) -> None:
        """StreamUrlCacheKeyがイミュータブルであることを検証"""
        video_id = VideoId(_value="dQw4w9WgXcQ")
        cache_key = StreamUrlCacheKey(_video_id=video_id, _hls=False)

        with pytest.raises(AttributeError):
            cache_key._video_id = VideoId(_value="abc_def-123")  # type: ignore

        with pytest.raises(AttributeError):
            cache_key._hls = True  # type: ignore

    def test_equality_same_values(self) -> None:
        """同じ値を持つStreamUrlCacheKeyが等しいことを検証"""
        video_id1 = VideoId(_value="dQw4w9WgXcQ")
        video_id2 = VideoId(_value="dQw4w9WgXcQ")
        cache_key1 = StreamUrlCacheKey(_video_id=video_id1, _hls=True)
        cache_key2 = StreamUrlCacheKey(_video_id=video_id2, _hls=True)

        assert cache_key1 == cache_key2

    def test_equality_different_hls(self) -> None:
        """hlsが異なる場合にStreamUrlCacheKeyが異なることを検証"""
        video_id = VideoId(_value="dQw4w9WgXcQ")
        cache_key1 = StreamUrlCacheKey(_video_id=video_id, _hls=True)
        cache_key2 = StreamUrlCacheKey(_video_id=video_id, _hls=False)

        assert cache_key1 != cache_key2

    def test_equality_different_video_id(self) -> None:
        """video_idが異なる場合にStreamUrlCacheKeyが異なることを検証"""
        video_id1 = VideoId(_value="dQw4w9WgXcQ")
        video_id2 = VideoId(_value="abc_def-123")
        cache_key1 = StreamUrlCacheKey(_video_id=video_id1, _hls=False)
        cache_key2 = StreamUrlCacheKey(_video_id=video_id2, _hls=False)

        assert cache_key1 != cache_key2
