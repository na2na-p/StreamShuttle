"""YoutubeUrl ValueObject ユニットテスト"""

import pytest

from streamshuttle.domain.model.youtube_url import YoutubeUrl
from streamshuttle.shared.exceptions import InvalidUrlError, InvalidVideoIdError


@pytest.mark.parametrize(
    "url",
    [
        pytest.param(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ", id="正常系: 標準的なyoutube.com URL"
        ),
        pytest.param("https://youtube.com/watch?v=dQw4w9WgXcQ", id="正常系: wwwなしyoutube.com"),
        pytest.param(
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ", id="正常系: モバイル版m.youtube.com"
        ),
        pytest.param("https://youtu.be/dQw4w9WgXcQ", id="正常系: 短縮URL youtu.be"),
        pytest.param("https://www.youtu.be/dQw4w9WgXcQ", id="正常系: wwwありyoutu.be"),
        pytest.param("https://www.youtube.com/embed/dQw4w9WgXcQ", id="正常系: 埋め込みURL /embed/"),
        pytest.param("http://www.youtube.com/watch?v=dQw4w9WgXcQ", id="正常系: httpスキーム"),
    ],
)
def test_youtube_url_valid(url: str):
    """正常系: 有効なYouTube URLでYoutubeUrlが生成される"""
    youtube_url = YoutubeUrl(_value=url)
    assert youtube_url.value == url
    assert str(youtube_url) == url


@pytest.mark.parametrize(
    "invalid_url,expected_error",
    [
        pytest.param("", InvalidUrlError, id="異常系: 空文字列"),
        pytest.param("not_a_url", InvalidUrlError, id="異常系: URLでない文字列"),
        pytest.param(
            "ftp://youtube.com/watch?v=dQw4w9WgXcQ", InvalidUrlError, id="異常系: FTPスキーム"
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
            "https://evil.com/watch?v=dQw4w9WgXcQ",
            InvalidUrlError,
            id="異常系: 不正なドメイン",
        ),
        pytest.param("https://www.google.com", InvalidUrlError, id="異常系: YouTubeでないドメイン"),
    ],
)
def test_youtube_url_invalid_url(invalid_url: str, expected_error: type):
    """異常系: 無効なURLでInvalidUrlErrorが発生"""
    with pytest.raises(expected_error):
        YoutubeUrl(_value=invalid_url)


@pytest.mark.parametrize(
    "url,expected_video_id",
    [
        pytest.param(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
            id="正常系: 標準的なURL",
        ),
        pytest.param(
            "https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ", id="正常系: wwwなし"
        ),
        pytest.param(
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ", id="正常系: モバイル版"
        ),
        pytest.param("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ", id="正常系: 短縮URL youtu.be"),
        pytest.param(
            "https://www.youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ", id="正常系: wwwありyoutu.be"
        ),
        pytest.param(
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
            id="正常系: 埋め込みURL",
        ),
        pytest.param(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s",
            "dQw4w9WgXcQ",
            id="正常系: タイムスタンプ付きURL",
        ),
        pytest.param(
            "https://youtu.be/dQw4w9WgXcQ?t=10", "dQw4w9WgXcQ", id="正常系: 短縮URL+パラメータ"
        ),
    ],
)
def test_extract_video_id_success(url: str, expected_video_id: str):
    """正常系: URLからvideo_idを正しく抽出できる"""
    youtube_url = YoutubeUrl(_value=url)
    video_id = youtube_url.extract_video_id()

    assert video_id.value == expected_video_id
    assert str(video_id) == expected_video_id


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("https://www.youtube.com/", id="異常系: video_idがないURL"),
        pytest.param("https://www.youtube.com/watch", id="異常系: /watchだがvパラメータがない"),
        pytest.param("https://www.youtube.com/channel/UCxxxxxx", id="異常系: チャンネルURL"),
        pytest.param("https://youtu.be/", id="異常系: youtu.beだがvideo_idがない"),
    ],
)
def test_extract_video_id_failure(url: str):
    """異常系: video_idを抽出できない場合にInvalidVideoIdErrorが発生"""
    youtube_url = YoutubeUrl(_value=url)

    with pytest.raises(InvalidVideoIdError) as exc_info:
        youtube_url.extract_video_id()

    assert "Could not extract video ID from URL" in str(exc_info.value)


@pytest.mark.parametrize(
    "url,expected_message",
    [
        pytest.param(
            "https://www.youtube.com/watch?v=invalid@idx",
            "ビデオIDの形式が不正です",
            id="異常系: 不正な文字を含むvideo_id（@記号、11文字）",
        ),
        pytest.param(
            "https://www.youtube.com/watch?v=short",
            "11文字である必要があります",
            id="異常系: 11文字未満のvideo_id",
        ),
        pytest.param(
            "https://www.youtube.com/watch?v=toolongvideoid",
            "11文字である必要があります",
            id="異常系: 11文字を超えるvideo_id",
        ),
    ],
)
def test_extract_video_id_invalid_format(url: str, expected_message: str):
    """異常系: 不正な形式のvideo_idでInvalidVideoIdErrorが発生"""
    youtube_url = YoutubeUrl(_value=url)

    with pytest.raises(InvalidVideoIdError) as exc_info:
        youtube_url.extract_video_id()

    assert expected_message in str(exc_info.value)


def test_youtube_url_immutability():
    """正常系: YoutubeUrlは不変である"""
    youtube_url = YoutubeUrl(_value="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    with pytest.raises(Exception):
        youtube_url._value = "https://evil.com"  # type: ignore
