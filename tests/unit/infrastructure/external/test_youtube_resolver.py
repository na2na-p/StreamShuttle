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
from streamshuttle.usecase.dto.resolved_url_result_dto import ResolvedUrlResultDto


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
    正常系: YoutubeResolver.resolve_url()がResolvedUrlResultDtoを返すことを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてストリームURLを返す
    Act: YoutubeResolver.resolve_url()を呼び出す
    Assert: ResolvedUrlResultDtoが返されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    expected_stream_url = "https://example.com/stream.m3u8?expire=1234567890"
    resolved_info = {"url": expected_stream_url, "video_id": "dQw4w9WgXcQ"}

    with patch.object(resolver, "_resolve_url_sync", return_value=resolved_info):
        with patch.object(resolver, "_extract_ttl_from_url", return_value=3600):
            # Act
            result = await resolver.resolve_url(youtube_url=youtube_url)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == expected_stream_url
    assert result.ttl_seconds == 3600
    assert result.video_id == "dQw4w9WgXcQ"


async def test_youtube_resolver_resolve_url_raises_invalid_url_exception_for_no_scheme(resolver):
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
    resolver,
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
        resolver, "_resolve_url_sync", side_effect=yt_dlp.utils.DownloadError("Video not found")
    ):
        # Act & Assert
        with pytest.raises(YouTubeResolverError):
            await resolver.resolve_url(youtube_url=youtube_url)


async def test_youtube_resolver_resolve_url_raises_youtube_resolver_exception_on_generic_error(
    resolver,
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

    with patch.object(resolver, "_resolve_url_sync", side_effect=Exception("Unexpected error")):
        # Act & Assert
        with pytest.raises(YouTubeResolverError):
            await resolver.resolve_url(youtube_url=youtube_url)


def test_youtube_resolver_resolve_url_sync_raises_youtube_resolver_exception_for_no_url(resolver):
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

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act & Assert
        with pytest.raises(YouTubeResolverError):
            resolver._resolve_url_sync(youtube_url=youtube_url)


async def test_youtube_resolver_resolve_url_with_format_id(resolver):
    """
    正常系: format_idが指定された場合、YoutubeResolver.resolve_url()が
    format_idを含めてResolvedUrlResultDtoを返すことを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてストリームURLを返す
    Act: YoutubeResolver.resolve_url()にformat_idを指定して呼び出す
    Assert: ResolvedUrlResultDtoが返され、_resolve_url_syncにformat_idが渡されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    format_id = "137"
    expected_stream_url = "https://example.com/stream.mp4?expire=1234567890"
    resolved_info = {"url": expected_stream_url, "video_id": "dQw4w9WgXcQ"}

    with patch.object(resolver, "_resolve_url_sync", return_value=resolved_info) as mock_sync:
        with patch.object(resolver, "_extract_ttl_from_url", return_value=3600):
            # Act
            result = await resolver.resolve_url(youtube_url=youtube_url, format_id=format_id)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == expected_stream_url
    assert result.ttl_seconds == 3600
    mock_sync.assert_called_once_with(youtube_url, format_id, False)


async def test_youtube_resolver_resolve_url_without_format_id(resolver):
    """
    正常系: format_idが指定されない場合、YoutubeResolver.resolve_url()が
    Noneを渡してResolvedUrlResultDtoを返すことを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてストリームURLを返す
    Act: YoutubeResolver.resolve_url()をformat_id指定なしで呼び出す
    Assert: ResolvedUrlResultDtoが返され、_resolve_url_syncにNoneが渡されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    expected_stream_url = "https://example.com/stream.m3u8?expire=1234567890"
    resolved_info = {"url": expected_stream_url, "video_id": "dQw4w9WgXcQ"}

    with patch.object(resolver, "_resolve_url_sync", return_value=resolved_info) as mock_sync:
        with patch.object(resolver, "_extract_ttl_from_url", return_value=3600):
            # Act
            result = await resolver.resolve_url(youtube_url=youtube_url)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == expected_stream_url
    assert result.ttl_seconds == 3600
    mock_sync.assert_called_once_with(youtube_url, None, False)


def test_youtube_resolver_resolve_url_sync_with_format_id(resolver):
    """
    正常系: format_idが指定された場合、yt-dlpに正しいformat_specが渡されることを確認

    Arrange: yt-dlp.YoutubeDLをモックしてurl付きの情報を返す
    Act: _resolve_url_sync()にformat_idを指定して呼び出す
    Assert: yt-dlpに指定されたformat_idがそのまま渡されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    format_id = "137"
    expected_url = "https://example.com/stream.mp4"
    mock_info = {"url": expected_url, "id": "dQw4w9WgXcQ"}

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act
        result = resolver._resolve_url_sync(youtube_url=youtube_url, format_id=format_id)

    # Assert
    assert result == {"url": expected_url, "video_id": "dQw4w9WgXcQ"}
    # yt-dlpのコンストラクタに渡されたオプションを確認
    call_args = mock_ydl_class.call_args
    ydl_opts = call_args[0][0]
    assert ydl_opts["format"] == "137"


def test_youtube_resolver_resolve_url_sync_without_format_id(resolver):
    """
    正常系: format_idが指定されない場合、yt-dlpに"best"が渡されることを確認

    Arrange: yt-dlp.YoutubeDLをモックしてurl付きの情報を返す
    Act: _resolve_url_sync()をformat_id指定なしで呼び出す
    Assert: yt-dlpに"best"のフォーマット指定が渡されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    expected_url = "https://example.com/stream.m3u8"
    mock_info = {"url": expected_url, "id": "dQw4w9WgXcQ"}

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act
        result = resolver._resolve_url_sync(youtube_url=youtube_url)

    # Assert
    assert result == {"url": expected_url, "video_id": "dQw4w9WgXcQ"}
    # yt-dlpのコンストラクタに渡されたオプションを確認
    call_args = mock_ydl_class.call_args
    ydl_opts = call_args[0][0]
    assert ydl_opts["format"] == "best[protocol^=http][protocol!*=m3u8][ext=mp4]/best[ext=mp4]/best"


async def test_youtube_resolver_resolve_url_with_invalid_format_id_raises_error(resolver):
    """
    異常系: 不正なformat_idが指定された場合、YouTubeResolverErrorが発生することを確認

    Arrange: yt-dlpの_resolve_url_syncをモックしてDownloadErrorを発生させる
    Act: YoutubeResolver.resolve_url()に不正なformat_idを指定して呼び出す
    Assert: YouTubeResolverErrorが発生することを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    invalid_format_id = "999"  # 存在しないformat_id

    with patch.object(
        resolver,
        "_resolve_url_sync",
        side_effect=yt_dlp.utils.DownloadError("Requested format is not available"),
    ):
        # Act & Assert
        with pytest.raises(YouTubeResolverError):
            await resolver.resolve_url(youtube_url=youtube_url, format_id=invalid_format_id)


def test_youtube_resolver_resolve_url_sync_with_format_id_not_available(resolver):
    """
    異常系: 指定されたformat_idが利用できない場合、yt-dlpがDownloadErrorを投げることを確認

    Arrange: yt-dlp.YoutubeDLをモックしてDownloadErrorを発生させる
    Act: _resolve_url_sync()に存在しないformat_idを指定して呼び出す
    Assert: yt_dlp.utils.DownloadErrorが発生することを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    invalid_format_id = "999"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError(
            "Requested format is not available"
        )

        # Act & Assert
        with pytest.raises(yt_dlp.utils.DownloadError):
            resolver._resolve_url_sync(youtube_url=youtube_url, format_id=invalid_format_id)


def test_youtube_resolver_resolve_url_sync_with_video_only_format(resolver):
    """
    正常系: video onlyフォーマット（format_id=137など）が指定された場合、
    動画のみのストリームURLが返されることを確認

    Arrange: yt-dlp.YoutubeDLをモックしてvideo onlyのurl付き情報を返す
    Act: _resolve_url_sync()にvideo onlyのformat_idを指定して呼び出す
    Assert: 動画のみのURLが返されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    format_id = "137"
    expected_url = "https://example.com/video_only.mp4"
    mock_info = {"url": expected_url, "id": "dQw4w9WgXcQ"}

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act
        result = resolver._resolve_url_sync(youtube_url=youtube_url, format_id=format_id)

    # Assert
    assert result == {"url": expected_url, "video_id": "dQw4w9WgXcQ"}
    # yt-dlpのコンストラクタに渡されたオプションを確認
    call_args = mock_ydl_class.call_args
    ydl_opts = call_args[0][0]
    assert ydl_opts["format"] == "137"


def test_youtube_resolver_resolve_url_sync_with_audio_video_format(resolver):
    """
    正常系: audio+videoフォーマット（format_id=18など）が指定された場合、
    音声付きストリームURLが返されることを確認

    Arrange: yt-dlp.YoutubeDLをモックしてaudio+videoのurl付き情報を返す
    Act: _resolve_url_sync()にaudio+videoのformat_idを指定して呼び出す
    Assert: 音声付きURLが返されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    format_id = "18"
    expected_url = "https://example.com/audio_video.mp4"
    mock_info = {"url": expected_url, "id": "dQw4w9WgXcQ"}

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act
        result = resolver._resolve_url_sync(youtube_url=youtube_url, format_id=format_id)

    # Assert
    assert result == {"url": expected_url, "video_id": "dQw4w9WgXcQ"}
    # yt-dlpのコンストラクタに渡されたオプションを確認
    call_args = mock_ydl_class.call_args
    ydl_opts = call_args[0][0]
    assert ydl_opts["format"] == "18"


def test_extract_ttl_from_url_returns_correct_ttl(resolver):
    """
    正常系: expireパラメータからTTL秒数を正しく計算することを確認

    Arrange: 現在時刻から3600秒後のexpireを設定
    Act: _extract_ttl_from_url()を呼び出す
    Assert: TTLは約3600秒（誤差±5秒程度を許容）
    """
    from datetime import UTC, datetime

    # Arrange
    future_expire = int(datetime.now(UTC).timestamp()) + 3600
    url = f"https://example.com/stream.mp4?expire={future_expire}"

    # Act
    result = resolver._extract_ttl_from_url(url)

    # Assert
    assert 3595 <= result <= 3605


def test_extract_ttl_from_url_raises_value_error_for_missing_expire(resolver):
    """
    異常系: expireパラメータが存在しない場合にValueErrorが発生することを確認

    Arrange: expireパラメータなしのURLを準備
    Act: _extract_ttl_from_url()を呼び出す
    Assert: ValueErrorが発生し、適切なエラーメッセージが含まれることを確認
    """
    # Arrange
    url = "https://example.com/stream.mp4?other=param"

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        resolver._extract_ttl_from_url(url)

    assert "expire parameter not found" in str(exc_info.value)


def test_extract_ttl_from_url_returns_zero_for_past_expire(resolver):
    """
    境界値: expireが過去の時刻の場合に0が返されることを確認

    Arrange: 現在時刻から3600秒前（過去）のexpireを設定
    Act: _extract_ttl_from_url()を呼び出す
    Assert: TTLが0であることを確認
    """
    from datetime import UTC, datetime

    # Arrange
    past_expire = int(datetime.now(UTC).timestamp()) - 3600
    url = f"https://example.com/stream.mp4?expire={past_expire}"

    # Act
    result = resolver._extract_ttl_from_url(url)

    # Assert
    assert result == 0
