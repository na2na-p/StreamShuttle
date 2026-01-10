"""
StreamUrlCacheKey ValueObjectのテストモジュール
"""

import pytest

from streamshuttle.domain.model.cache_key.stream_url_cache_key import StreamUrlCacheKey


class TestStreamUrlCacheKey:
    """StreamUrlCacheKeyのテストクラス"""

    @pytest.mark.parametrize(
        "platform, video_id_value, hls, expected_key",
        [
            pytest.param(
                "youtube",
                "dQw4w9WgXcQ",
                False,
                "youtube:dQw4w9WgXcQ:hls:False",
                id="正常系: YouTube hls=Falseでキャッシュキーが正しく生成される",
            ),
            pytest.param(
                "youtube",
                "dQw4w9WgXcQ",
                True,
                "youtube:dQw4w9WgXcQ:hls:True",
                id="正常系: YouTube hls=Trueでキャッシュキーが正しく生成される",
            ),
            pytest.param(
                "twitch",
                "gamesdonequick",
                True,
                "twitch:gamesdonequick:hls:True",
                id="正常系: Twitchチャンネル名でキャッシュキーが正しく生成される",
            ),
            pytest.param(
                "twitch",
                "1234567890",
                True,
                "twitch:1234567890:hls:True",
                id="正常系: Twitch VOD IDでキャッシュキーが正しく生成される",
            ),
            pytest.param(
                "youtube",
                "abc_def-123",
                False,
                "youtube:abc_def-123:hls:False",
                id="正常系: 特殊文字を含むvideo_idでキャッシュキーが正しく生成される",
            ),
        ],
    )
    def test_value_property_returns_correct_cache_key(
        self, platform: str, video_id_value: str, hls: bool, expected_key: str
    ) -> None:
        """valueプロパティが正しいキャッシュキー文字列を返すことを検証"""
        cache_key = StreamUrlCacheKey(
            _platform=platform,
            _video_id_value=video_id_value,
            _hls=hls,
        )

        assert cache_key.value == expected_key

    def test_str_returns_cache_key_value(self) -> None:
        """__str__がvalueと同じ文字列を返すことを検証"""
        cache_key = StreamUrlCacheKey(
            _platform="youtube",
            _video_id_value="dQw4w9WgXcQ",
            _hls=False,
        )

        assert str(cache_key) == cache_key.value
        assert str(cache_key) == "youtube:dQw4w9WgXcQ:hls:False"

    def test_immutability(self) -> None:
        """StreamUrlCacheKeyがイミュータブルであることを検証"""
        cache_key = StreamUrlCacheKey(
            _platform="youtube",
            _video_id_value="dQw4w9WgXcQ",
            _hls=False,
        )

        with pytest.raises(AttributeError):
            cache_key._platform = "twitch"  # type: ignore

        with pytest.raises(AttributeError):
            cache_key._video_id_value = "abc_def-123"  # type: ignore

        with pytest.raises(AttributeError):
            cache_key._hls = True  # type: ignore

    def test_equality_same_values(self) -> None:
        """同じ値を持つStreamUrlCacheKeyが等しいことを検証"""
        cache_key1 = StreamUrlCacheKey(
            _platform="youtube",
            _video_id_value="dQw4w9WgXcQ",
            _hls=True,
        )
        cache_key2 = StreamUrlCacheKey(
            _platform="youtube",
            _video_id_value="dQw4w9WgXcQ",
            _hls=True,
        )

        assert cache_key1 == cache_key2

    def test_equality_different_hls(self) -> None:
        """hlsが異なる場合にStreamUrlCacheKeyが異なることを検証"""
        cache_key1 = StreamUrlCacheKey(
            _platform="youtube",
            _video_id_value="dQw4w9WgXcQ",
            _hls=True,
        )
        cache_key2 = StreamUrlCacheKey(
            _platform="youtube",
            _video_id_value="dQw4w9WgXcQ",
            _hls=False,
        )

        assert cache_key1 != cache_key2

    def test_equality_different_video_id(self) -> None:
        """video_idが異なる場合にStreamUrlCacheKeyが異なることを検証"""
        cache_key1 = StreamUrlCacheKey(
            _platform="youtube",
            _video_id_value="dQw4w9WgXcQ",
            _hls=False,
        )
        cache_key2 = StreamUrlCacheKey(
            _platform="youtube",
            _video_id_value="abc_def-123",
            _hls=False,
        )

        assert cache_key1 != cache_key2

    def test_equality_different_platform(self) -> None:
        """platformが異なる場合にStreamUrlCacheKeyが異なることを検証"""
        cache_key1 = StreamUrlCacheKey(
            _platform="youtube",
            _video_id_value="dQw4w9WgXcQ",
            _hls=True,
        )
        cache_key2 = StreamUrlCacheKey(
            _platform="twitch",
            _video_id_value="dQw4w9WgXcQ",
            _hls=True,
        )

        assert cache_key1 != cache_key2
