"""
PlaylistQueryService ユニットテスト

PlaylistQueryServiceの正常系と異常系のテストを提供します。
yt-dlpをモック化してテストします。
"""

from unittest.mock import patch

import pytest
import yt_dlp

from streamshuttle.infrastructure.query_service.playlist_query_service import (
    PlaylistQueryService,
)
from streamshuttle.shared.exceptions import (
    InvalidUrlError,
    PlaylistNotFoundError,
    YouTubeResolverError,
)

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"


@pytest.fixture
def query_service():
    """
    PlaylistQueryServiceのフィクスチャ

    Returns:
        PlaylistQueryService: 取得上限3件のテスト用インスタンス
    """
    return PlaylistQueryService(max_items=3)


def build_entry(video_id: str, title: str = "テスト動画", duration: float | None = 120.0) -> dict:
    """
    yt-dlpのフラット抽出エントリーを模したdictを生成します

    Args:
        video_id: 動画ID
        title: 動画タイトル
        duration: 動画の長さ（秒）

    Returns:
        dict: エントリー辞書
    """
    return {"id": video_id, "title": title, "duration": duration}


async def test_playlist_query_service_returns_playlist_items(query_service):
    """
    正常系: プレイリスト情報と動画一覧が返されることを確認

    Arrange: yt-dlpの_extract_infoをモックしてプレイリスト情報を返す
    Act: get_playlist()を呼び出す
    Assert: プレイリスト情報と動画一覧が返される
    """
    # Arrange
    mock_info = {
        "id": "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
        "title": "テストプレイリスト",
        "uploader": "テストチャンネル",
        "entries": [build_entry("dQw4w9WgXcQ", "1曲目"), build_entry("9bZkp7q19f0", "2曲目")],
    }

    # Act
    with patch.object(query_service, "_extract_info", return_value=mock_info):
        playlist_info, items = await query_service.get_playlist(PLAYLIST_URL)

    # Assert
    assert playlist_info.playlist_id == "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
    assert playlist_info.title == "テストプレイリスト"
    assert playlist_info.uploader == "テストチャンネル"
    assert playlist_info.item_count == 2
    assert playlist_info.truncated is False
    assert len(items) == 2
    assert items[0].video_id == "dQw4w9WgXcQ"
    assert items[0].title == "1曲目"
    assert items[0].url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert items[0].duration_seconds == 120
    assert items[0].thumbnail_url == "https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg"


async def test_playlist_query_service_excludes_unplayable_entries(query_service):
    """
    正常系: 再生できないエントリーが一覧から除外されることを確認

    Arrange: 非公開・削除済み・None・ID欠落のエントリーを含む情報を返す
    Act: get_playlist()を呼び出す
    Assert: 再生可能な動画のみが返される
    """
    # Arrange
    mock_info = {
        "id": "PLtest",
        "title": "テストプレイリスト",
        "entries": [
            build_entry("dQw4w9WgXcQ", "再生できる動画"),
            build_entry("9bZkp7q19f0", "[Private video]"),
            build_entry("kJQP7kiw5Fk", "[Deleted video]"),
            None,
            {"title": "IDがないエントリー"},
        ],
    }

    # Act
    with patch.object(query_service, "_extract_info", return_value=mock_info):
        playlist_info, items = await query_service.get_playlist(PLAYLIST_URL)

    # Assert
    assert len(items) == 1
    assert items[0].video_id == "dQw4w9WgXcQ"
    assert playlist_info.item_count == 1


async def test_playlist_query_service_truncates_when_over_max_items(query_service):
    """
    正常系: 上限を超えるプレイリストが切り捨てられることを確認

    Arrange: 上限（3件）を超える4件のエントリーを返す
    Act: get_playlist()を呼び出す
    Assert: 3件に切り詰められ、truncatedがTrueになる
    """
    # Arrange
    mock_info = {
        "id": "PLtest",
        "title": "長いプレイリスト",
        "entries": [build_entry(f"video{index:06d}") for index in range(4)],
    }

    # Act
    with patch.object(query_service, "_extract_info", return_value=mock_info):
        playlist_info, items = await query_service.get_playlist(PLAYLIST_URL)

    # Assert
    assert len(items) == 3
    assert playlist_info.item_count == 3
    assert playlist_info.truncated is True


async def test_playlist_query_service_handles_missing_duration(query_service):
    """
    正常系: 長さが取得できない動画でもDTOが生成されることを確認

    Arrange: durationがないエントリーを返す
    Act: get_playlist()を呼び出す
    Assert: duration_secondsがNoneになる
    """
    # Arrange
    mock_info = {
        "id": "PLtest",
        "title": "テストプレイリスト",
        "entries": [build_entry("dQw4w9WgXcQ", "ライブ配信", duration=None)],
    }

    # Act
    with patch.object(query_service, "_extract_info", return_value=mock_info):
        _, items = await query_service.get_playlist(PLAYLIST_URL)

    # Assert
    assert items[0].duration_seconds is None


@pytest.mark.parametrize(
    "mock_info",
    [
        pytest.param(None, id="異常系: 情報が取得できない"),
        pytest.param({"id": "PLtest", "entries": []}, id="異常系: 動画が0件"),
    ],
)
async def test_playlist_query_service_raises_when_playlist_is_empty(query_service, mock_info):
    """
    異常系: プレイリストが空の場合にPlaylistNotFoundErrorが送出されることを確認

    Arrange: 空のプレイリスト情報を返す
    Act: get_playlist()を呼び出す
    Assert: PlaylistNotFoundErrorが送出される
    """
    # Act & Assert
    with patch.object(query_service, "_extract_info", return_value=mock_info):
        with pytest.raises(PlaylistNotFoundError):
            await query_service.get_playlist(PLAYLIST_URL)


async def test_playlist_query_service_raises_when_no_playable_entries(query_service):
    """
    異常系: 再生可能な動画が1件もない場合にPlaylistNotFoundErrorが送出されることを確認

    Arrange: 非公開動画のみを含むプレイリスト情報を返す
    Act: get_playlist()を呼び出す
    Assert: PlaylistNotFoundErrorが送出される
    """
    # Arrange
    mock_info = {
        "id": "PLtest",
        "title": "非公開のみ",
        "entries": [build_entry("dQw4w9WgXcQ", "[Private video]")],
    }

    # Act & Assert
    with patch.object(query_service, "_extract_info", return_value=mock_info):
        with pytest.raises(PlaylistNotFoundError):
            await query_service.get_playlist(PLAYLIST_URL)


async def test_playlist_query_service_raises_invalid_url_error(query_service):
    """
    異常系: 無効なURLでInvalidUrlErrorが送出されることを確認

    Arrange: 許可されないドメインのURLを準備
    Act: get_playlist()を呼び出す
    Assert: InvalidUrlErrorが送出される
    """
    # Act & Assert
    with pytest.raises(InvalidUrlError):
        await query_service.get_playlist("https://example.com/playlist?list=PLtest")


async def test_playlist_query_service_raises_resolver_error_on_download_error(query_service):
    """
    異常系: 通信障害等のDownloadErrorがYouTubeResolverErrorに変換されることを確認

    Arrange: _extract_infoが通信エラーのDownloadErrorを送出するようにモック
    Act: get_playlist()を呼び出す
    Assert: YouTubeResolverErrorが送出される
    """
    # Act & Assert
    with patch.object(
        query_service,
        "_extract_info",
        side_effect=yt_dlp.utils.DownloadError("Unable to download API page: timed out"),
    ):
        with pytest.raises(YouTubeResolverError):
            await query_service.get_playlist(PLAYLIST_URL)


@pytest.mark.parametrize(
    "error_message",
    [
        pytest.param("The playlist does not exist.", id="異常系: 存在しないプレイリスト"),
        pytest.param("This playlist is private", id="異常系: 非公開プレイリスト"),
        pytest.param("Playlist not found", id="異常系: プレイリスト未検出"),
    ],
)
async def test_playlist_query_service_raises_not_found_on_unavailable_playlist(
    query_service, error_message
):
    """
    異常系: プレイリスト自体が利用できない場合にPlaylistNotFoundErrorが送出されることを確認

    通信障害（502相当）と、存在しない・非公開のプレイリスト（404相当）を
    区別できることを検証します。

    Arrange: _extract_infoが不存在・非公開を示すDownloadErrorを送出するようにモック
    Act: get_playlist()を呼び出す
    Assert: PlaylistNotFoundErrorが送出される
    """
    # Act & Assert
    with patch.object(
        query_service,
        "_extract_info",
        side_effect=yt_dlp.utils.DownloadError(error_message),
    ):
        with pytest.raises(PlaylistNotFoundError):
            await query_service.get_playlist(PLAYLIST_URL)
