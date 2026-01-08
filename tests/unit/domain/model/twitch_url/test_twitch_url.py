"""TwitchUrl ValueObject ユニットテスト"""

import pytest

from streamshuttle.domain.model.twitch_url import TwitchUrl
from streamshuttle.shared.exceptions import InvalidUrlError, InvalidVideoIdError


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("https://www.twitch.tv/videos/1234567890", id="正常系: VOD URL"),
        pytest.param("https://twitch.tv/videos/1234567890", id="正常系: wwwなしVOD URL"),
        pytest.param("https://m.twitch.tv/videos/1234567890", id="正常系: モバイル版VOD URL"),
        pytest.param("https://www.twitch.tv/channelname", id="正常系: ライブストリームURL"),
        pytest.param(
            "https://www.twitch.tv/channelname/clip/ClipSlug-abc123",
            id="正常系: クリップURL",
        ),
        pytest.param(
            "https://clips.twitch.tv/ClipSlug-abc123", id="正常系: clips.twitch.tvクリップURL"
        ),
        pytest.param("http://www.twitch.tv/videos/1234567890", id="正常系: httpスキーム"),
    ],
)
def test_twitch_url_valid(url: str):
    """正常系: 有効なTwitch URLでTwitchUrlが生成される"""
    twitch_url = TwitchUrl(_value=url)
    assert twitch_url.value == url
    assert str(twitch_url) == url


@pytest.mark.parametrize(
    "invalid_url,expected_error",
    [
        pytest.param("", InvalidUrlError, id="異常系: 空文字列"),
        pytest.param("not_a_url", InvalidUrlError, id="異常系: URLでない文字列"),
        pytest.param(
            "ftp://twitch.tv/videos/1234567890", InvalidUrlError, id="異常系: FTPスキーム"
        ),
        pytest.param(
            "file:///path/to/file", InvalidUrlError, id="異常系: fileスキーム（セキュリティ対策）"
        ),
        pytest.param(
            "javascript:alert(1)",
            InvalidUrlError,
            id="異常系: javascriptスキーム（セキュリティ対策）",
        ),
        pytest.param(
            "https://evil.com/videos/1234567890",
            InvalidUrlError,
            id="異常系: 不正なドメイン",
        ),
        pytest.param("https://www.youtube.com", InvalidUrlError, id="異常系: Twitchでないドメイン"),
    ],
)
def test_twitch_url_invalid_url(invalid_url: str, expected_error: type):
    """異常系: 無効なURLでInvalidUrlErrorが発生"""
    with pytest.raises(expected_error):
        TwitchUrl(_value=invalid_url)


@pytest.mark.parametrize(
    "url,expected_video_id",
    [
        pytest.param(
            "https://www.twitch.tv/videos/1234567890",
            "1234567890",
            id="正常系: VOD URL",
        ),
        pytest.param(
            "https://twitch.tv/videos/1234567890", "1234567890", id="正常系: wwwなしVOD URL"
        ),
        pytest.param(
            "https://m.twitch.tv/videos/1234567890", "1234567890", id="正常系: モバイル版VOD URL"
        ),
        pytest.param(
            "https://www.twitch.tv/channelname", "channelname", id="正常系: ライブストリームURL"
        ),
        pytest.param(
            "https://www.twitch.tv/channelname/clip/ClipSlug-abc123",
            "ClipSlug-abc123",
            id="正常系: クリップURL",
        ),
        pytest.param(
            "https://clips.twitch.tv/ClipSlug-abc123",
            "ClipSlug-abc123",
            id="正常系: clips.twitch.tvクリップURL",
        ),
    ],
)
def test_extract_video_id_success(url: str, expected_video_id: str):
    """正常系: URLからvideo_idを正しく抽出できる"""
    twitch_url = TwitchUrl(_value=url)
    video_id = twitch_url.extract_video_id()

    assert video_id.value == expected_video_id
    assert str(video_id) == expected_video_id


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("https://www.twitch.tv/", id="異常系: video_idがないURL"),
        pytest.param("https://www.twitch.tv/directory/game/", id="異常系: ディレクトリURL"),
    ],
)
def test_extract_video_id_failure(url: str):
    """異常系: video_idを抽出できない場合にInvalidVideoIdErrorが発生"""
    twitch_url = TwitchUrl(_value=url)

    with pytest.raises(InvalidVideoIdError) as exc_info:
        twitch_url.extract_video_id()

    assert "Could not extract video ID from URL" in str(exc_info.value)


def test_twitch_url_immutability():
    """正常系: TwitchUrlは不変である"""
    twitch_url = TwitchUrl(_value="https://www.twitch.tv/videos/1234567890")

    with pytest.raises(Exception):
        twitch_url._value = "https://evil.com"  # type: ignore
