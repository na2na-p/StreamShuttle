"""
VideoFormatQueryService ユニットテスト

VideoFormatQueryServiceの正常系と異常系のテストを提供します。
yt-dlpをモック化してテストします。
"""

import logging
from unittest.mock import patch

import pytest
import yt_dlp

from streamshuttle.infrastructure.query_service.video_format_query_service import (
    VideoFormatQueryService,
)
from streamshuttle.shared.exceptions import InvalidUrlError, YouTubeResolverError
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto


@pytest.fixture
def query_service():
    """
    VideoFormatQueryServiceのフィクスチャ

    Returns:
        VideoFormatQueryService: テスト用のVideoFormatQueryServiceインスタンス
    """
    return VideoFormatQueryService()


async def test_video_format_query_service_get_available_formats_returns_format_list(query_service):
    """
    正常系: VideoFormatQueryService.get_available_formats()がフォーマット一覧を
    返すことを確認

    Arrange: yt-dlpの_extract_infoをモックして動画情報を返す
    Act: VideoFormatQueryService.get_available_formats()を呼び出す
    Assert: VideoFormatDtoのリストが返されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_info = {
        "formats": [
            {
                "format_id": "137",
                "format_note": "1080p",
                "vcodec": "h264",
                "url": "https://example.com/video1.mp4",
            },
            {
                "format_id": "248",
                "format_note": "1080p",
                "vcodec": "vp9",
                "url": "https://example.com/video2.webm",
            },
        ]
    }

    with patch.object(query_service, "_extract_info", return_value=mock_info):
        # Act
        video_info, formats = await query_service.get_available_formats(youtube_url=youtube_url)

    # Assert
    assert isinstance(video_info, VideoInfoDto)
    assert len(formats) == 2
    assert formats[0].format_id == "137"
    assert formats[0].quality == "1080p"
    assert formats[0].codec == "h264"
    assert formats[1].format_id == "248"


async def test_video_format_query_service_get_available_formats_returns_empty_list_for_no_formats(
    query_service,
):
    """
    正常系: VideoFormatQueryService.get_available_formats()がフォーマット情報が
    存在しない場合に空のリストを返すことを確認

    Arrange: yt-dlpの_extract_infoをモックしてformatsなしの情報を返す
    Act: VideoFormatQueryService.get_available_formats()を呼び出す
    Assert: 空のリストが返されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_info = {}  # formatsキーなし

    with patch.object(query_service, "_extract_info", return_value=mock_info):
        # Act
        video_info, formats = await query_service.get_available_formats(youtube_url=youtube_url)

    # Assert
    assert isinstance(video_info, VideoInfoDto)
    assert len(formats) == 0


async def test_video_format_query_service_get_available_formats_skips_incomplete_formats(
    query_service,
):
    """
    正常系: VideoFormatQueryService.get_available_formats()が必須フィールドがない
    フォーマットをスキップすることを確認

    Arrange: yt-dlpの_extract_infoをモックして不完全なフォーマット情報を返す
    Act: VideoFormatQueryService.get_available_formats()を呼び出す
    Assert: 有効なフォーマットのみが返されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_info = {
        "formats": [
            {"format_id": "137", "url": "https://example.com/video1.mp4"},
            {
                # format_idなし（無効）
                "url": "https://example.com/video2.mp4"
            },
            {
                "format_id": "248",
                # urlなし（無効）
            },
        ]
    }

    with patch.object(query_service, "_extract_info", return_value=mock_info):
        # Act
        video_info, formats = await query_service.get_available_formats(youtube_url=youtube_url)

    # Assert
    assert isinstance(video_info, VideoInfoDto)
    assert len(formats) == 1
    assert formats[0].format_id == "137"


async def test_video_format_query_service_get_available_formats_raises_invalid_url_exception(
    query_service,
):
    """
    異常系: 無効なURLでVideoFormatQueryService.get_available_formats()を呼び出すと
    InvalidUrlErrorが発生することを確認

    Arrange: スキームなしのURLを準備
    Act: VideoFormatQueryService.get_available_formats()を呼び出す
    Assert: InvalidUrlErrorが発生することを確認
    """
    # Arrange
    invalid_url = "not_a_url"

    # Act & Assert
    with pytest.raises(InvalidUrlError):
        await query_service.get_available_formats(youtube_url=invalid_url)


async def test_video_format_query_service_get_available_formats_raises_youtube_resolver_exception_on_download_error(  # noqa: E501
    query_service,
):
    """
    異常系: yt-dlpのDownloadError時にVideoFormatQueryService.get_available_formats()が
    YouTubeResolverErrorを発生させることを確認

    Arrange: yt-dlpの_extract_infoをモックしてDownloadErrorを発生させる
    Act: VideoFormatQueryService.get_available_formats()を呼び出す
    Assert: YouTubeResolverErrorが発生することを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=invalid"

    with patch.object(
        query_service, "_extract_info", side_effect=yt_dlp.utils.DownloadError("Video not found")
    ):
        # Act & Assert
        with pytest.raises(YouTubeResolverError):
            await query_service.get_available_formats(youtube_url=youtube_url)


async def test_video_format_query_service_filters_out_hls_formats(query_service):
    """
    正常系: VideoFormatQueryService.get_available_formats()がHLSフォーマット
    (m3u8系プロトコル)を除外することを確認

    Arrange: yt-dlpの_extract_infoをモックしてHLSと通常フォーマットを返す
    Act: VideoFormatQueryService.get_available_formats()を呼び出す
    Assert: HLSフォーマットが除外され、通常フォーマットのみが返されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_info = {
        "formats": [
            {
                "format_id": "91",
                "format_note": "144p",
                "vcodec": "h264",
                "acodec": "aac",
                "url": "https://example.com/video1.m3u8",
                "protocol": "m3u8",
            },
            {
                "format_id": "92",
                "format_note": "240p",
                "vcodec": "h264",
                "acodec": "aac",
                "url": "https://example.com/video2.m3u8",
                "protocol": "m3u8_native",
            },
            {
                "format_id": "93",
                "format_note": "360p",
                "vcodec": "h264",
                "acodec": "aac",
                "url": "https://example.com/video3.m3u8",
                "protocol": "m3u8_native+http",
            },
            {
                "format_id": "137",
                "format_note": "1080p",
                "vcodec": "h264",
                "acodec": "none",
                "url": "https://example.com/video4.mp4",
                "protocol": "https",
            },
        ]
    }

    with patch.object(query_service, "_extract_info", return_value=mock_info):
        # Act
        video_info, formats = await query_service.get_available_formats(youtube_url=youtube_url)

    # Assert
    assert isinstance(video_info, VideoInfoDto)
    assert len(formats) == 1
    assert formats[0].format_id == "137"
    assert formats[0].quality == "1080p"
    assert formats[0].codec == "h264"


async def test_video_format_query_service_sets_has_audio_and_has_video_flags(query_service):
    """
    正常系: VideoFormatQueryService.get_available_formats()がacodec/vcodecに基づいて
    has_audio/has_videoフラグを正しく設定することを確認

    Arrange: yt-dlpの_extract_infoをモックして様々なacodec/vcodecパターンを返す
    Act: VideoFormatQueryService.get_available_formats()を呼び出す
    Assert: 各フォーマットのhas_audio/has_videoが正しく設定されることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_info = {
        "formats": [
            {
                "format_id": "22",
                "format_note": "720p",
                "vcodec": "h264",
                "acodec": "aac",
                "url": "https://example.com/video1.mp4",
                "protocol": "https",
            },
            {
                "format_id": "137",
                "format_note": "1080p",
                "vcodec": "h264",
                "acodec": "none",
                "url": "https://example.com/video2.mp4",
                "protocol": "https",
            },
            {
                "format_id": "140",
                "format_note": "128k",
                "vcodec": "none",
                "acodec": "aac",
                "url": "https://example.com/audio1.m4a",
                "protocol": "https",
            },
            {
                "format_id": "999",
                "format_note": "test",
                "vcodec": "none",
                "acodec": "none",
                "url": "https://example.com/test.bin",
                "protocol": "https",
            },
        ]
    }

    with patch.object(query_service, "_extract_info", return_value=mock_info):
        # Act
        video_info, formats = await query_service.get_available_formats(youtube_url=youtube_url)

    # Assert
    assert isinstance(video_info, VideoInfoDto)
    assert len(formats) == 4

    assert formats[0].format_id == "22"
    assert formats[0].has_audio is True
    assert formats[0].has_video is True

    assert formats[1].format_id == "137"
    assert formats[1].has_audio is False
    assert formats[1].has_video is True

    assert formats[2].format_id == "140"
    assert formats[2].has_audio is True
    assert formats[2].has_video is False

    assert formats[3].format_id == "999"
    assert formats[3].has_audio is False
    assert formats[3].has_video is False


async def test_video_format_query_service_does_not_filter_http_formats(query_service):
    """
    正常系: VideoFormatQueryService.get_available_formats()がHTTP/HTTPS/空のプロトコルを
    除外しないことを確認

    Arrange: yt-dlpの_extract_infoをモックして様々なHTTPプロトコルを返す
    Act: VideoFormatQueryService.get_available_formats()を呼び出す
    Assert: すべてのHTTP系フォーマットが結果に含まれることを確認
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_info = {
        "formats": [
            {
                "format_id": "137",
                "format_note": "1080p",
                "vcodec": "h264",
                "acodec": "none",
                "url": "https://example.com/video1.mp4",
                "protocol": "https",
            },
            {
                "format_id": "248",
                "format_note": "1080p",
                "vcodec": "vp9",
                "acodec": "none",
                "url": "http://example.com/video2.webm",
                "protocol": "http",
            },
            {
                "format_id": "140",
                "format_note": "128k",
                "vcodec": "none",
                "acodec": "aac",
                "url": "https://example.com/audio1.m4a",
                "protocol": "",
            },
        ]
    }

    with patch.object(query_service, "_extract_info", return_value=mock_info):
        # Act
        video_info, formats = await query_service.get_available_formats(youtube_url=youtube_url)

    # Assert
    assert isinstance(video_info, VideoInfoDto)
    assert len(formats) == 3
    assert formats[0].format_id == "137"
    assert formats[0].codec == "h264"
    assert formats[1].format_id == "248"
    assert formats[1].codec == "vp9"
    assert formats[2].format_id == "140"
    assert formats[2].codec == "unknown"


def _fmt(format_id, acodec, vcodec, protocol="https"):
    return {
        "format_id": format_id,
        "format_note": "note",
        "acodec": acodec,
        "vcodec": vcodec,
        "protocol": protocol,
        "url": f"https://example.com/{format_id}",
    }


FALLBACK_URL = "https://www.youtube.com/watch?v=CbdWElnmJIY"


def _first_result_without_combined():
    return {
        "id": "CbdWElnmJIY",
        "title": "T",
        "thumbnail": "https://example.com/t.jpg",
        "formats": [_fmt("137", "none", "avc1"), _fmt("140", "mp4a", "none")],
    }


async def test_get_available_formats_merges_combined_formats_from_fallback_client(
    query_service,
):
    """結合済みフォーマットが無い場合、androidクライアントの結合済みフォーマットだけを末尾に追加する"""
    # Arrange
    second = {
        "title": "Other",
        "formats": [_fmt("sb0", "none", "avc1"), _fmt("18", "mp4a", "avc1")],
    }

    with patch.object(
        query_service, "_extract_info", side_effect=[_first_result_without_combined(), second]
    ) as mock_extract:
        # Act
        video_info, formats = await query_service.get_available_formats(FALLBACK_URL)

    # Assert
    assert [f.format_id for f in formats] == ["137", "140", "18"]
    assert formats[-1].has_audio is True
    assert formats[-1].has_video is True
    assert video_info.title == "T"
    assert mock_extract.call_count == 2
    assert mock_extract.call_args_list[1].args == (FALLBACK_URL, ("android",))


async def test_get_available_formats_does_not_fallback_when_combined_exists(query_service):
    """結合済みフォーマットが既にある場合はフォールバックしない"""
    # Arrange
    first = {"formats": [_fmt("18", "mp4a", "avc1"), _fmt("137", "none", "avc1")]}

    with patch.object(query_service, "_extract_info", return_value=first) as mock_extract:
        # Act
        _, formats = await query_service.get_available_formats(FALLBACK_URL)

    # Assert
    assert mock_extract.call_count == 1
    assert [f.format_id for f in formats] == ["18", "137"]


async def test_get_available_formats_excludes_hls_from_fallback(query_service):
    """フォールバック結果のHLS(m3u8)フォーマットは追加しない"""
    # Arrange
    second = {"formats": [_fmt("91", "mp4a", "avc1", protocol="m3u8_native"), _fmt("18", "a", "v")]}

    with patch.object(
        query_service, "_extract_info", side_effect=[_first_result_without_combined(), second]
    ):
        # Act
        _, formats = await query_service.get_available_formats(FALLBACK_URL)

    # Assert
    assert [f.format_id for f in formats] == ["137", "140", "18"]


async def test_get_available_formats_skips_duplicate_format_id_from_fallback(query_service):
    """フォールバック結果のformat_idが既存と重複する場合は追加しない"""
    # Arrange
    second = {"formats": [_fmt("137", "mp4a", "avc1"), _fmt("18", "mp4a", "avc1")]}

    with patch.object(
        query_service, "_extract_info", side_effect=[_first_result_without_combined(), second]
    ):
        # Act
        _, formats = await query_service.get_available_formats(FALLBACK_URL)

    # Assert
    assert [f.format_id for f in formats] == ["137", "140", "18"]
    assert formats[0].has_audio is False


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(
            yt_dlp.utils.DownloadError("Requested format is not available"),
            id="異常系: フォールバックがDownloadErrorでも元の一覧を返す",
        ),
        pytest.param(RuntimeError("boom"), id="異常系: フォールバックが一般例外でも元の一覧を返す"),
    ],
)
async def test_get_available_formats_returns_original_when_fallback_fails(
    query_service, error, caplog
):
    """フォールバックが失敗しても例外を出さず、元の一覧を返しWARNINGを記録する"""
    # Arrange
    with patch.object(
        query_service, "_extract_info", side_effect=[_first_result_without_combined(), error]
    ):
        # Act
        with caplog.at_level(logging.INFO):
            _, formats = await query_service.get_available_formats(FALLBACK_URL)

    # Assert
    assert [f.format_id for f in formats] == ["137", "140"]
    levels = [r.levelno for r in caplog.records]
    assert levels.count(logging.WARNING) == 1
    assert levels.count(logging.INFO) == 1
