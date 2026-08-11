"""
YoutubePlaylistUrl ValueObject ユニットテスト

プレイリストURLのバリデーションとプレイリストID抽出を検証します。
"""

import pytest

from streamshuttle.domain.model.youtube_playlist import YoutubePlaylistUrl
from streamshuttle.shared.exceptions import InvalidPlaylistIdError, InvalidUrlError

PLAYLIST_ID = "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"


@pytest.mark.parametrize(
    "url",
    [
        pytest.param(
            f"https://www.youtube.com/playlist?list={PLAYLIST_ID}",
            id="正常系: playlist URL",
        ),
        pytest.param(
            f"https://www.youtube.com/watch?v=dQw4w9WgXcQ&list={PLAYLIST_ID}",
            id="正常系: watch URL（listパラメータ付き）",
        ),
        pytest.param(
            f"https://youtu.be/dQw4w9WgXcQ?list={PLAYLIST_ID}",
            id="正常系: 短縮URL（listパラメータ付き）",
        ),
        pytest.param(
            f"https://m.youtube.com/playlist?list={PLAYLIST_ID}",
            id="正常系: モバイルURL",
        ),
    ],
)
def test_youtube_playlist_url_extracts_playlist_id(url):
    """
    正常系: 各種URL形式からプレイリストIDが抽出できることを確認

    Arrange: listパラメータを含むURLを準備
    Act: extract_playlist_id()を呼び出す
    Assert: プレイリストIDが抽出される
    """
    # Act
    playlist_id = YoutubePlaylistUrl(_value=url).extract_playlist_id()

    # Assert
    assert playlist_id.value == PLAYLIST_ID


def test_youtube_playlist_url_to_canonical_url_normalizes_watch_url():
    """
    正常系: watch URLがプレイリスト取得用URLに正規化されることを確認

    Arrange: listパラメータ付きのwatch URLを準備
    Act: to_canonical_url()を呼び出す
    Assert: /playlist?list=形式のURLが返される
    """
    # Arrange
    url = f"https://www.youtube.com/watch?v=dQw4w9WgXcQ&list={PLAYLIST_ID}"

    # Act
    canonical_url = YoutubePlaylistUrl(_value=url).to_canonical_url()

    # Assert
    assert canonical_url == f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"


@pytest.mark.parametrize(
    "url",
    [
        pytest.param(
            f"ftp://www.youtube.com/playlist?list={PLAYLIST_ID}",
            id="異常系: 許可されないスキーム",
        ),
        pytest.param(
            f"https://example.com/playlist?list={PLAYLIST_ID}",
            id="異常系: 許可されないドメイン",
        ),
        pytest.param(
            f"https://evil-youtube.com/playlist?list={PLAYLIST_ID}",
            id="異常系: 類似ドメイン",
        ),
    ],
)
def test_youtube_playlist_url_rejects_invalid_url(url):
    """
    異常系: 不正なURLが拒否されることを確認

    Arrange: スキームまたはドメインが不正なURLを準備
    Act: YoutubePlaylistUrlを生成
    Assert: InvalidUrlErrorが送出される
    """
    # Act & Assert
    with pytest.raises(InvalidUrlError):
        YoutubePlaylistUrl(_value=url)


def test_youtube_playlist_url_rejects_url_without_list_parameter():
    """
    異常系: listパラメータを含まないURLが拒否されることを確認

    Arrange: listパラメータのないwatch URLを準備
    Act: extract_playlist_id()を呼び出す
    Assert: InvalidPlaylistIdErrorが送出される
    """
    # Arrange
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Act & Assert
    with pytest.raises(InvalidPlaylistIdError):
        YoutubePlaylistUrl(_value=url).extract_playlist_id()


def test_youtube_playlist_url_rejects_private_playlist_url():
    """
    異常系: 非公開プレイリストのURLが拒否されることを確認

    Arrange: list=WL（後で見る）のURLを準備
    Act: extract_playlist_id()を呼び出す
    Assert: InvalidPlaylistIdErrorが送出される
    """
    # Arrange
    url = "https://www.youtube.com/playlist?list=WL"

    # Act & Assert
    with pytest.raises(InvalidPlaylistIdError):
        YoutubePlaylistUrl(_value=url).extract_playlist_id()
