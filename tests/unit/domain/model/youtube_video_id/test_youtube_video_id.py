"""YoutubeVideoId ValueObject ユニットテスト"""

import pytest

from streamshuttle.domain.model.youtube_video_id import YoutubeVideoId
from streamshuttle.shared.exceptions import InvalidVideoIdError


@pytest.mark.parametrize(
    "video_id_str",
    [
        pytest.param("dQw4w9WgXcQ", id="正常系: 標準的な11文字のvideo_id"),
        pytest.param("0123456789_", id="正常系: 数字とアンダースコア"),
        pytest.param("abcdefghij-", id="正常系: 英字とハイフン"),
        pytest.param("A-Z_0-9_abc", id="正常系: 大文字小文字数字記号混合"),
    ],
)
def test_youtube_video_id_valid(video_id_str: str):
    """正常系: 有効なvideo_idでYoutubeVideoIdが生成される"""
    video_id = YoutubeVideoId(_value=video_id_str)
    assert video_id.value == video_id_str
    assert str(video_id) == video_id_str


@pytest.mark.parametrize(
    "invalid_video_id_str",
    [
        pytest.param("", id="異常系: 空文字列"),
        pytest.param("short", id="異常系: 11文字未満"),
        pytest.param("toolongvideoid", id="異常系: 11文字超過"),
        pytest.param("invalid@char", id="異常系: 不正な文字（@記号）"),
        pytest.param("invalid char", id="異常系: 不正な文字（スペース）"),
        pytest.param("invalid.char", id="異常系: 不正な文字（ドット）"),
        pytest.param("12345678901", id="境界値: 11文字だが全て数字（許可される）"),
        pytest.param("あいうえおかきくけこさ", id="異常系: 日本語文字"),
    ],
)
def test_youtube_video_id_invalid(invalid_video_id_str: str):
    """異常系: 無効なvideo_idでInvalidVideoIdErrorが発生"""
    # 境界値ケース: 11文字の数字は有効
    if invalid_video_id_str == "12345678901":
        video_id = YoutubeVideoId(_value=invalid_video_id_str)
        assert video_id.value == invalid_video_id_str
        return

    with pytest.raises(InvalidVideoIdError) as exc_info:
        YoutubeVideoId(_value=invalid_video_id_str)

    assert "Invalid video ID format" in str(exc_info.value)


def test_youtube_video_id_immutability():
    """正常系: YoutubeVideoIdは不変である"""
    video_id = YoutubeVideoId(_value="dQw4w9WgXcQ")

    with pytest.raises(Exception):
        video_id._value = "new_value"  # type: ignore
