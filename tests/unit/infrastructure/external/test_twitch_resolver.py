"""
TwitchResolver ユニットテスト

TwitchResolverの正常系と異常系のテストを提供します。
yt-dlpをモック化してテストします。
"""

from unittest.mock import patch

import pytest
import yt_dlp

from streamshuttle.infrastructure.external.twitch_resolver import TwitchResolver
from streamshuttle.shared.exceptions import InvalidUrlError, TwitchResolverError
from streamshuttle.usecase.dto.resolved_url_result_dto import ResolvedUrlResultDto


@pytest.fixture
def resolver():
    """
    TwitchResolverのフィクスチャ

    Returns:
        TwitchResolver: テスト用のTwitchResolverインスタンス
    """
    return TwitchResolver()


async def test_twitch_resolver_resolve_url_returns_stream_url(resolver):
    """
    正常系: TwitchResolver.resolve_url()がResolvedUrlResultDtoを返すことを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてストリームURLを返す
    Act: TwitchResolver.resolve_url()を呼び出す
    Assert: ResolvedUrlResultDtoが返されることを確認
    """
    # Arrange
    twitch_url = "https://www.twitch.tv/videos/1234567890"
    expected_stream_url = "https://example.com/stream.m3u8"

    with patch.object(resolver, "_resolve_url_sync", return_value=expected_stream_url):
        # Act
        result = await resolver.resolve_url(twitch_url=twitch_url)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == expected_stream_url
    # TwitchはデフォルトTTLを使用
    assert result.ttl_seconds > 0


async def test_twitch_resolver_resolve_url_raises_invalid_url_exception_for_no_scheme(resolver):
    """
    異常系: スキームなしのURLでTwitchResolver.resolve_url()を呼び出すと
    InvalidUrlErrorが発生することを確認

    Arrange: スキームなしのURLを準備
    Act: TwitchResolver.resolve_url()を呼び出す
    Assert: InvalidUrlErrorが発生することを確認
    """
    # Arrange
    invalid_url = "www.twitch.tv/videos/1234567890"

    # Act & Assert
    with pytest.raises(InvalidUrlError):
        await resolver.resolve_url(twitch_url=invalid_url)


async def test_twitch_resolver_resolve_url_raises_twitch_resolver_exception_on_download_error(
    resolver,
):
    """
    異常系: yt-dlpのDownloadError時にTwitchResolver.resolve_url()が
    TwitchResolverErrorを発生させることを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてDownloadErrorを発生させる
    Act: TwitchResolver.resolve_url()を呼び出す
    Assert: TwitchResolverErrorが発生することを確認
    """
    # Arrange
    twitch_url = "https://www.twitch.tv/videos/invalid"

    with patch.object(
        resolver, "_resolve_url_sync", side_effect=yt_dlp.utils.DownloadError("Video not found")
    ):
        # Act & Assert
        with pytest.raises(TwitchResolverError):
            await resolver.resolve_url(twitch_url=twitch_url)


async def test_twitch_resolver_resolve_url_raises_twitch_resolver_exception_on_generic_error(
    resolver,
):
    """
    異常系: 予期しないエラー時にTwitchResolver.resolve_url()が
    TwitchResolverErrorを発生させることを確認

    Arrange: yt-dlpの_resolve_url_syncをモックして予期しないエラーを発生させる
    Act: TwitchResolver.resolve_url()を呼び出す
    Assert: TwitchResolverErrorが発生することを確認
    """
    # Arrange
    twitch_url = "https://www.twitch.tv/videos/1234567890"

    with patch.object(resolver, "_resolve_url_sync", side_effect=Exception("Unexpected error")):
        # Act & Assert
        with pytest.raises(TwitchResolverError):
            await resolver.resolve_url(twitch_url=twitch_url)


def test_twitch_resolver_resolve_url_sync_raises_twitch_resolver_exception_for_no_url(resolver):
    """
    異常系: yt-dlpからURLが取得できない場合にTwitchResolverError
    が発生することを確認

    Arrange: yt-dlp.YoutubeDLをモックしてurlなしの情報を返す
    Act: _resolve_url_sync()を呼び出す
    Assert: TwitchResolverErrorが発生することを確認
    """
    # Arrange
    twitch_url = "https://www.twitch.tv/videos/1234567890"
    mock_info = {}  # urlキーなし

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act & Assert
        with pytest.raises(TwitchResolverError):
            resolver._resolve_url_sync(twitch_url=twitch_url)


async def test_twitch_resolver_resolve_url_with_format_id(resolver):
    """
    正常系: format_idが指定された場合、TwitchResolver.resolve_url()が
    format_idを含めてResolvedUrlResultDtoを返すことを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてストリームURLを返す
    Act: TwitchResolver.resolve_url()にformat_idを指定して呼び出す
    Assert: ResolvedUrlResultDtoが返され、_resolve_url_syncにformat_idが渡されることを確認
    """
    # Arrange
    twitch_url = "https://www.twitch.tv/videos/1234567890"
    format_id = "1080p60"
    expected_stream_url = "https://example.com/stream.m3u8"

    with patch.object(resolver, "_resolve_url_sync", return_value=expected_stream_url) as mock_sync:
        # Act
        result = await resolver.resolve_url(twitch_url=twitch_url, format_id=format_id)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == expected_stream_url
    mock_sync.assert_called_once_with(twitch_url, format_id)


async def test_twitch_resolver_resolve_url_without_format_id(resolver):
    """
    正常系: format_idが指定されない場合、TwitchResolver.resolve_url()が
    Noneを渡してResolvedUrlResultDtoを返すことを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてストリームURLを返す
    Act: TwitchResolver.resolve_url()をformat_id指定なしで呼び出す
    Assert: ResolvedUrlResultDtoが返され、_resolve_url_syncにNoneが渡されることを確認
    """
    # Arrange
    twitch_url = "https://www.twitch.tv/videos/1234567890"
    expected_stream_url = "https://example.com/stream.m3u8"

    with patch.object(resolver, "_resolve_url_sync", return_value=expected_stream_url) as mock_sync:
        # Act
        result = await resolver.resolve_url(twitch_url=twitch_url)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == expected_stream_url
    mock_sync.assert_called_once_with(twitch_url, None)


def test_twitch_resolver_resolve_url_sync_with_format_id(resolver):
    """
    正常系: format_idが指定された場合、yt-dlpに正しいformat_specが渡されることを確認

    Arrange: yt-dlp.YoutubeDLをモックしてurl付きの情報を返す
    Act: _resolve_url_sync()にformat_idを指定して呼び出す
    Assert: yt-dlpに指定されたformat_idがそのまま渡されることを確認
    """
    # Arrange
    twitch_url = "https://www.twitch.tv/videos/1234567890"
    format_id = "1080p60"
    expected_url = "https://example.com/stream.m3u8"
    mock_info = {"url": expected_url}

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act
        result = resolver._resolve_url_sync(twitch_url=twitch_url, format_id=format_id)

    # Assert
    assert result == expected_url
    # yt-dlpのコンストラクタに渡されたオプションを確認
    call_args = mock_ydl_class.call_args
    ydl_opts = call_args[0][0]
    assert ydl_opts["format"] == "1080p60"


def test_twitch_resolver_resolve_url_sync_without_format_id(resolver):
    """
    正常系: format_idが指定されない場合、yt-dlpに"best"が渡されることを確認

    Arrange: yt-dlp.YoutubeDLをモックしてurl付きの情報を返す
    Act: _resolve_url_sync()をformat_id指定なしで呼び出す
    Assert: yt-dlpに"best"のフォーマット指定が渡されることを確認
    """
    # Arrange
    twitch_url = "https://www.twitch.tv/videos/1234567890"
    expected_url = "https://example.com/stream.m3u8"
    mock_info = {"url": expected_url}

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act
        result = resolver._resolve_url_sync(twitch_url=twitch_url)

    # Assert
    assert result == expected_url
    # yt-dlpのコンストラクタに渡されたオプションを確認
    call_args = mock_ydl_class.call_args
    ydl_opts = call_args[0][0]
    assert ydl_opts["format"] == "best"


async def test_twitch_resolver_resolve_url_live_stream(resolver):
    """
    正常系: ライブストリームURLでTwitchResolver.resolve_url()が
    ResolvedUrlResultDtoを返すことを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてストリームURLを返す
    Act: TwitchResolver.resolve_url()にライブストリームURLを渡して呼び出す
    Assert: ResolvedUrlResultDtoが返されることを確認
    """
    # Arrange
    twitch_url = "https://www.twitch.tv/channelname"
    expected_stream_url = "https://example.com/live.m3u8"

    with patch.object(resolver, "_resolve_url_sync", return_value=expected_stream_url):
        # Act
        result = await resolver.resolve_url(twitch_url=twitch_url)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == expected_stream_url


async def test_twitch_resolver_resolve_url_clip(resolver):
    """
    正常系: クリップURLでTwitchResolver.resolve_url()が
    ResolvedUrlResultDtoを返すことを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてストリームURLを返す
    Act: TwitchResolver.resolve_url()にクリップURLを渡して呼び出す
    Assert: ResolvedUrlResultDtoが返されることを確認
    """
    # Arrange
    twitch_url = "https://clips.twitch.tv/ClipSlug-abc123"
    expected_stream_url = "https://example.com/clip.mp4"

    with patch.object(resolver, "_resolve_url_sync", return_value=expected_stream_url):
        # Act
        result = await resolver.resolve_url(twitch_url=twitch_url)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == expected_stream_url
