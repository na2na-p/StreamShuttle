"""
YoutubeResolver ユニットテスト

YoutubeResolverの正常系と異常系のテストを提供します。
yt-dlpをモック化してテストします。
"""

import logging
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
import yt_dlp

from streamshuttle.domain.model.hls_mode import HlsMode
from streamshuttle.infrastructure.external.youtube_resolver import YoutubeResolver
from streamshuttle.infrastructure.external.ytdlp_options_factory import YtDlpOptionsFactory
from streamshuttle.shared.exceptions import (
    HlsMasterUnavailableError,
    InvalidUrlError,
    VideoUnavailableError,
    YouTubeResolverError,
)
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

    with patch.object(resolver, "_resolve_url_sync", return_value=expected_stream_url):
        with patch.object(resolver, "_extract_ttl_from_url", return_value=3600):
            # Act
            result = await resolver.resolve_url(youtube_url=youtube_url)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == expected_stream_url
    assert result.ttl_seconds == 3600


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

    with patch.object(resolver, "_resolve_url_sync", return_value=expected_stream_url) as mock_sync:
        with patch.object(resolver, "_extract_ttl_from_url", return_value=3600):
            # Act
            result = await resolver.resolve_url(youtube_url=youtube_url, format_id=format_id)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == expected_stream_url
    assert result.ttl_seconds == 3600
    mock_sync.assert_called_once_with(youtube_url, format_id, HlsMode.DISABLED)


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

    with patch.object(resolver, "_resolve_url_sync", return_value=expected_stream_url) as mock_sync:
        with patch.object(resolver, "_extract_ttl_from_url", return_value=3600):
            # Act
            result = await resolver.resolve_url(youtube_url=youtube_url)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == expected_stream_url
    assert result.ttl_seconds == 3600
    mock_sync.assert_called_once_with(youtube_url, None, HlsMode.DISABLED)


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
    mock_info = {"url": expected_url}

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act
        result = resolver._resolve_url_sync(youtube_url=youtube_url, format_id=format_id)

    # Assert
    assert result == expected_url
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
    mock_info = {"url": expected_url}

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act
        result = resolver._resolve_url_sync(youtube_url=youtube_url)

    # Assert
    assert result == expected_url
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
    mock_info = {"url": expected_url}

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act
        result = resolver._resolve_url_sync(youtube_url=youtube_url, format_id=format_id)

    # Assert
    assert result == expected_url
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
    mock_info = {"url": expected_url}

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = mock_info

        # Act
        result = resolver._resolve_url_sync(youtube_url=youtube_url, format_id=format_id)

    # Assert
    assert result == expected_url
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


def test_extract_ttl_from_url_returns_zero_for_current_expire(resolver):
    from datetime import UTC, datetime

    current_expire = int(datetime.now(UTC).timestamp())
    url = f"https://example.com/stream.mp4?expire={current_expire}"

    assert resolver._extract_ttl_from_url(url) == 0


FORMAT_UNAVAILABLE_MESSAGE = (
    "ERROR: [youtube] CbdWElnmJIY: Requested format is not available. "
    "Use --list-formats for a list of available formats"
)
YOUTUBE_URL = "https://www.youtube.com/watch?v=CbdWElnmJIY"


@pytest.mark.parametrize(
    "format_id, hls",
    [
        pytest.param(
            None, HlsMode.DISABLED, id="正常系: format_id未指定・HLS無効でフォールバックする"
        ),
        pytest.param(
            None, HlsMode.ENABLED, id="正常系: format_id未指定・HLS有効でフォールバックする"
        ),
        pytest.param("18", HlsMode.DISABLED, id="正常系: format_id指定でもフォールバックする"),
    ],
)
def test_resolve_url_sync_retries_with_fallback_client_when_format_unavailable(
    resolver, format_id, hls
):
    """既定クライアントでフォーマットが見つからない場合、androidクライアントで1回だけ再試行する"""
    # Arrange
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.side_effect = [
            yt_dlp.utils.DownloadError(FORMAT_UNAVAILABLE_MESSAGE),
            {"url": "https://example.com/v?expire=1"},
        ]

        # Act
        result = resolver._resolve_url_sync(YOUTUBE_URL, format_id, hls)

    # Assert
    assert result == "https://example.com/v?expire=1"
    assert mock_ydl.extract_info.call_count == 2
    first_opts = mock_ydl_class.call_args_list[0].args[0]
    second_opts = mock_ydl_class.call_args_list[1].args[0]
    assert "player_client" not in first_opts["extractor_args"]["youtube"]
    assert second_opts["extractor_args"]["youtube"]["player_client"] == ["android"]
    assert first_opts["format"] == second_opts["format"]


@pytest.mark.parametrize(
    "message",
    [
        pytest.param(
            "ERROR: [youtube] xxx: Private video. Sign in if you've been granted access to "
            "this video",
            id="異常系: 非公開動画では再試行しない",
        ),
        pytest.param(
            "ERROR: Unable to download API page: <urlopen error timed out>",
            id="異常系: ネットワークエラーでは再試行しない",
        ),
    ],
)
def test_resolve_url_sync_does_not_retry_on_other_download_error(resolver, message):
    """フォーマット未検出以外のDownloadErrorでは再試行せずそのまま送出する"""
    # Arrange
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError(message)

        # Act & Assert
        with pytest.raises(yt_dlp.utils.DownloadError):
            resolver._resolve_url_sync(YOUTUBE_URL)

    assert mock_ydl.extract_info.call_count == 1


def test_resolve_url_sync_raises_when_fallback_also_fails(resolver):
    """フォールバックも失敗した場合、再試行側のエラーを元のエラーに連鎖させて送出する"""
    # Arrange
    first_error = yt_dlp.utils.DownloadError(FORMAT_UNAVAILABLE_MESSAGE)
    second_error = yt_dlp.utils.DownloadError(FORMAT_UNAVAILABLE_MESSAGE)
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.side_effect = [first_error, second_error]

        # Act & Assert
        with pytest.raises(yt_dlp.utils.DownloadError) as exc_info:
            resolver._resolve_url_sync(YOUTUBE_URL)

    assert mock_ydl.extract_info.call_count == 2
    assert exc_info.value is second_error
    assert exc_info.value.__cause__ is first_error


def test_resolve_url_sync_logs_warning_on_fallback(resolver, caplog):
    """フォールバック時にandroidクライアント名を含むWARNINGを1件だけ出力する"""
    # Arrange
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.side_effect = [
            yt_dlp.utils.DownloadError(FORMAT_UNAVAILABLE_MESSAGE),
            {"url": "https://example.com/v?expire=1"},
        ]

        # Act
        with caplog.at_level(logging.WARNING):
            resolver._resolve_url_sync(YOUTUBE_URL, "18")

    # Assert
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "android" in warnings[0].getMessage()
    assert YOUTUBE_URL in warnings[0].getMessage()
    assert "18" in warnings[0].getMessage()


async def test_resolve_url_returns_dto_after_fallback(resolver):
    """フォールバック経由でもresolve_url()がResolvedUrlResultDtoを返す"""
    # Arrange
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.side_effect = [
            yt_dlp.utils.DownloadError(FORMAT_UNAVAILABLE_MESSAGE),
            {"url": "https://example.com/v?expire=4102444800"},
        ]

        # Act
        result = await resolver.resolve_url(YOUTUBE_URL)

    # Assert
    assert isinstance(result, ResolvedUrlResultDto)
    assert result.resolved_url == "https://example.com/v?expire=4102444800"
    assert mock_ydl.extract_info.call_count == 2


def test_resolve_url_sync_returns_hls_master_manifest_url(resolver):
    manifest_url = "https://manifest.googlevideo.com/api/manifest/hls_variant/expire/4102444800"
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = {
            "url": "https://example.com/progressive.mp4",
            "requested_formats": [{"format_id": "234", "manifest_url": manifest_url}],
        }

        result = resolver._resolve_url_sync(YOUTUBE_URL, hls=HlsMode.MASTER)

    assert result == manifest_url
    options = mock_ydl_class.call_args.args[0]
    assert options["extractor_args"]["youtube"]["skip"] == ["dash"]


def test_resolve_url_sync_rejects_hls_master_when_manifest_is_absent(resolver):
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = {"url": "https://example.com/progressive.mp4"}

        with pytest.raises(HlsMasterUnavailableError):
            resolver._resolve_url_sync(YOUTUBE_URL, hls=HlsMode.MASTER)


@pytest.mark.parametrize(
    "message",
    [
        "ERROR: [youtube] xxx: Private video. Sign in if you've been granted access to this video",
        "ERROR: [youtube] xxx: Video unavailable",
        "ERROR: [youtube] xxx: Video unavailable. This video is not available",
        "ERROR: [youtube] xxx: Video unavailable. This video is no longer available because "
        "the YouTube account associated with this video has been terminated",
        "ERROR: [youtube] xxx: This video has been removed",
        "ERROR: [youtube] xxx: The uploader has not made this video available in your country",
    ],
)
async def test_resolve_url_reports_unavailable_video_for_hls_master(resolver, message):
    download_error = yt_dlp.utils.DownloadError(message)
    with patch.object(resolver, "_resolve_url_sync", side_effect=download_error):
        with pytest.raises(VideoUnavailableError):
            await resolver.resolve_url(YOUTUBE_URL, hls=HlsMode.MASTER)


@pytest.mark.parametrize(
    "message",
    [
        "ERROR: [youtube] xxx: Video unavailable. This content isn't available, try again later",
        "ERROR: [youtube] xxx: Video unavailable. This content is rate-limited",
        "ERROR: [youtube] xxx: Video unavailable. Request was rate limited",
        "ERROR: [youtube] xxx: Video unavailable. This is temporarily unavailable",
        "ERROR: [youtube] xxx: Video unavailable. HTTP Error 429: Too Many Requests",
        "ERROR: [youtube] xxx: Video unavailable. This video has been removed; try again later",
        "ERROR: [youtube] xxx: Requested format is not available. "
        "HTTP Error 429: Too Many Requests",
        "ERROR: [youtube] xxx: Video unavailable. YouTube is requiring a captcha challenge "
        "before playback",
        "ERROR: [youtube] xxx: Video unavailable. Sign in to confirm you are not a bot",
    ],
)
async def test_resolve_url_keeps_temporary_video_unavailable_error_as_resolver_error(
    resolver, message
):
    with patch.object(
        resolver, "_resolve_url_sync", side_effect=yt_dlp.utils.DownloadError(message)
    ):
        with pytest.raises(YouTubeResolverError) as exc_info:
            await resolver.resolve_url(YOUTUBE_URL, hls=HlsMode.MASTER)

    assert type(exc_info.value) is YouTubeResolverError


@pytest.mark.parametrize("hls", [HlsMode.DISABLED, HlsMode.ENABLED])
async def test_ytdlp_report_error_does_not_expose_secret_at_any_output_boundary(
    resolver, capsys, caplog, monkeypatch, hls
):
    secret = "signature=synthetic-secret-token"

    def report_error(self, _url, download):
        self.report_error(f"synthetic yt-dlp error: {secret}")

    monkeypatch.setattr(yt_dlp.YoutubeDL, "extract_info", report_error)

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(YouTubeResolverError) as exc_info:
            await resolver.resolve_url(YOUTUBE_URL, hls=hls)

    captured = capsys.readouterr()
    assert secret not in captured.out
    assert secret not in captured.err
    assert secret not in caplog.text
    assert secret not in str(exc_info.value)
    assert "classification=other" in caplog.text
    assert "platform=youtube" in caplog.text
    assert "video_id=CbdWElnmJIY" in caplog.text


def test_resolve_url_sync_rejects_untrusted_hls_master_manifest(resolver):
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = {
            "manifest_url": "https://attacker.example/api/manifest/hls_variant/expire/4102444800"
        }

        with pytest.raises(HlsMasterUnavailableError):
            resolver._resolve_url_sync(YOUTUBE_URL, hls=HlsMode.MASTER)


def test_extract_ttl_from_url_reads_hls_manifest_path_expire(resolver):
    from datetime import UTC, datetime

    future_expire = int(datetime.now(UTC).timestamp()) + 3600
    url = f"https://manifest.googlevideo.com/api/manifest/hls_variant/expire/{future_expire}/x"

    ttl = resolver._extract_ttl_from_url(url, HlsMode.MASTER)

    assert 3590 <= ttl <= 3600


@pytest.mark.parametrize(
    ("resolve_kwargs",),
    [
        pytest.param({}, id="hlsなし"),
        pytest.param({"hls": HlsMode.ENABLED}, id="hls=true"),
    ],
)
async def test_resolve_url_keeps_legacy_default_ttl_for_path_expire(resolver, resolve_kwargs):
    path_expire = int(datetime.now(UTC).timestamp()) + 3600
    stream_url = f"https://example.com/videoplayback/expire/{path_expire}/x"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = {"url": stream_url}

        result = await resolver.resolve_url(YOUTUBE_URL, **resolve_kwargs)

    assert result.ttl_seconds == 21600


async def test_resolve_url_uses_path_expire_for_hls_master(resolver):
    path_expire = int(datetime.now(UTC).timestamp()) + 3600
    manifest_url = (
        f"https://manifest.googlevideo.com/api/manifest/hls_variant/expire/{path_expire}/x"
    )

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = {"manifest_url": manifest_url}

        result = await resolver.resolve_url(YOUTUBE_URL, hls=HlsMode.MASTER)

    assert 3590 <= result.ttl_seconds <= 3600


async def test_resolve_url_does_not_assign_default_ttl_to_hls_master_without_expire(resolver):
    manifest_url = "https://manifest.googlevideo.com/api/manifest/hls_variant/playlist.m3u8"
    with patch.object(resolver, "_resolve_url_sync", return_value=manifest_url):
        result = await resolver.resolve_url(YOUTUBE_URL, hls=HlsMode.MASTER)

    assert result.ttl_seconds == 0


HLS_MASTER_MANIFEST_URL = (
    "https://manifest.googlevideo.com/api/manifest/hls_variant/expire/4102444800/playlist.m3u8"
)


def _hls_formats_with_separate_streams() -> list[dict]:
    return [
        {
            "format_id": "video",
            "url": "https://example.test/video.m3u8",
            "manifest_url": HLS_MASTER_MANIFEST_URL,
            "ext": "mp4",
            "protocol": "m3u8_native",
            "vcodec": "avc1.64001f",
            "acodec": "none",
            "width": 1280,
            "height": 720,
            "tbr": 1000,
        },
        {
            "format_id": "audio",
            "url": "https://example.test/audio.m3u8",
            "manifest_url": HLS_MASTER_MANIFEST_URL,
            "ext": "m4a",
            "protocol": "m3u8_native",
            "vcodec": "none",
            "acodec": "mp4a.40.2",
            "abr": 128,
            "tbr": 128,
        },
    ]


def _hls_formats_with_combined_stream() -> list[dict]:
    return [
        {
            "format_id": "18",
            "url": "https://example.test/combined.mp4",
            "manifest_url": HLS_MASTER_MANIFEST_URL,
            "ext": "mp4",
            "protocol": "https",
            "vcodec": "avc1.42001E",
            "acodec": "mp4a.40.2",
            "width": 640,
            "height": 360,
            "tbr": 500,
        }
    ]


def _select_formats_with_ytdlp(format_spec: str, formats: list[dict]) -> dict:
    info = {
        "id": "testvideo",
        "title": "test video",
        "extractor": "youtube",
        "extractor_key": "Youtube",
        "webpage_url": "https://www.youtube.com/watch?v=testvideo",
        "formats": formats,
    }
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "format": format_spec}) as ydl:
        return ydl.process_ie_result(info, download=False)


@pytest.mark.parametrize(
    "formats",
    [
        pytest.param(_hls_formats_with_separate_streams(), id="映像のみと音声のみのHLS形式"),
        pytest.param(_hls_formats_with_combined_stream(), id="結合済み形式のみ"),
    ],
)
def test_hls_master_format_selects_streams_and_preserves_master_manifest(resolver, formats):
    """hls=masterはyt-dlpの実際の選択を通してマニフェストを取得できる。"""
    format_spec = YtDlpOptionsFactory.select_url_resolution_format(
        format_id="18", hls=HlsMode.MASTER
    )

    selected_info = _select_formats_with_ytdlp(format_spec, formats)

    assert resolver._extract_hls_manifest_url(selected_info) == HLS_MASTER_MANIFEST_URL


def test_resolve_url_sync_does_not_fallback_after_master_manifest_is_selected(resolver):
    """既定クライアントがhls=masterを解決できればandroidへ再試行しない。"""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = {"manifest_url": HLS_MASTER_MANIFEST_URL}

        result = resolver._resolve_url_sync(YOUTUBE_URL, format_id="18", hls=HlsMode.MASTER)

    assert result == HLS_MASTER_MANIFEST_URL
    assert mock_ydl.extract_info.call_count == 1
    assert mock_ydl_class.call_args.args[0]["format"] == (
        YtDlpOptionsFactory.select_url_resolution_format("18", HlsMode.MASTER)
    )
