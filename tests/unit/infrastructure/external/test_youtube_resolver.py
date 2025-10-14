"""
YoutubeResolver ユニットテスト

YoutubeResolverの正常系と異常系のテストを提供します。
yt-dlpをモック化してテストします。
"""

from unittest.mock import patch

import pytest
import yt_dlp

from streamshuttle.infrastructure.external.youtube_resolver import YoutubeResolver
from streamshuttle.shared.exceptions import InvalidUrlError, YouTubeResolverError


@pytest.fixture
def resolver():
    """
    YoutubeResolverのフィクスチャ

    Returns:
        YoutubeResolver: テスト用のYoutubeResolverインスタンス
    """
    return YoutubeResolver()


async def test_youtube_resolver_resolve_url_returns_stream_url(resolver):
    """
    正常系: YoutubeResolver.resolve_url()がストリームURLを返すことを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてストリームURLを返す
    Act: YoutubeResolver.resolve_url()を呼び出す
    Assert: ストリームURLが返されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    expected_stream_url = "https://example.com/stream.m3u8"

    with patch.object(resolver, '_resolve_url_sync', return_value=expected_stream_url):
        # Act
        result = await resolver.resolve_url(youtube_url=youtube_url)

    # Assert
    assert result == expected_stream_url


async def test_youtube_resolver_resolve_url_raises_invalid_url_exception_for_no_scheme(
    resolver
):
    """
    異常系: スキームなしのURLでYoutubeResolver.resolve_url()を呼び出すと
    InvalidUrlErrorが発生することを確認

    Arrange: スキームなしのURLを準備
    Act: YoutubeResolver.resolve_url()を呼び出す
    Assert: InvalidUrlErrorが発生することを確認
    """
    # Arrange
    invalid_url = "www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Act & Assert
    with pytest.raises(InvalidUrlError):
        await resolver.resolve_url(youtube_url=invalid_url)


async def test_youtube_resolver_resolve_url_raises_youtube_resolver_exception_on_download_error(
    resolver
):
    """
    異常系: yt-dlpのDownloadError時にYoutubeResolver.resolve_url()が
    YouTubeResolverErrorを発生させることを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてDownloadErrorを発生させる
    Act: YoutubeResolver.resolve_url()を呼び出す
    Assert: YouTubeResolverErrorが発生することを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=invalid"

    with patch.object(
        resolver,
        '_resolve_url_sync',
        side_effect=yt_dlp.utils.DownloadError("Video not found")
    ):
        # Act & Assert
        with pytest.raises(YouTubeResolverError):
            await resolver.resolve_url(youtube_url=youtube_url)


async def test_youtube_resolver_resolve_url_raises_youtube_resolver_exception_on_generic_error(
    resolver
):
    """
    異常系: 予期しないエラー時にYoutubeResolver.resolve_url()が
    YouTubeResolverErrorを発生させることを確認

    Arrange: yt-dlpの_resolve_url_syncをモックして予期しないエラーを発生させる
    Act: YoutubeResolver.resolve_url()を呼び出す
    Assert: YouTubeResolverErrorが発生することを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    with patch.object(
        resolver,
        '_resolve_url_sync',
        side_effect=Exception("Unexpected error")
    ):
        # Act & Assert
        with pytest.raises(YouTubeResolverError):
            await resolver.resolve_url(youtube_url=youtube_url)


def test_youtube_resolver_resolve_url_sync_raises_youtube_resolver_exception_for_no_url(
    resolver
):
    """
    異常系: yt-dlpからURLが取得できない場合にYoutubeResolverException
    が発生することを確認

    Arrange: yt-dlp.YoutubeDLをモックしてurlなしの情報を返す
    Act: _resolve_url_sync()を呼び出す
    Assert: YouTubeResolverErrorが発生することを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_info = {}  # urlキーなし

    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act & Assert
        with pytest.raises(YouTubeResolverError):
            resolver._resolve_url_sync(youtube_url=youtube_url)
