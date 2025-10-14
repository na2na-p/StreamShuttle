"""
VideoFormatQueryService ユニットテスト

VideoFormatQueryServiceの正常系と異常系のテストを提供します。
yt-dlpをモック化してテストします。
"""

from unittest.mock import patch

import pytest
import yt_dlp

from streamshuttle.infrastructure.query_service.video_format_query_service import (
    VideoFormatQueryService,
)
from streamshuttle.shared.exceptions import InvalidUrlError, YouTubeResolverError


@pytest.fixture
def query_service():
    """
    VideoFormatQueryServiceのフィクスチャ

    Returns:
        VideoFormatQueryService: テスト用のVideoFormatQueryServiceインスタンス
    """
    return VideoFormatQueryService()


async def test_video_format_query_service_get_available_formats_returns_format_list(
    query_service
):
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
                "url": "https://example.com/video1.mp4"
            },
            {
                "format_id": "248",
                "format_note": "1080p",
                "vcodec": "vp9",
                "url": "https://example.com/video2.webm"
            }
        ]
    }

    with patch.object(query_service, '_extract_info', return_value=mock_info):
        # Act
        result = await query_service.get_available_formats(youtube_url=youtube_url)

    # Assert
    assert len(result) == 2
    assert result[0].format_id == "137"
    assert result[0].quality == "1080p"
    assert result[0].codec == "h264"
    assert result[1].format_id == "248"


async def test_video_format_query_service_get_available_formats_returns_empty_list_for_no_formats(
    query_service
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

    with patch.object(query_service, '_extract_info', return_value=mock_info):
        # Act
        result = await query_service.get_available_formats(youtube_url=youtube_url)

    # Assert
    assert len(result) == 0


async def test_video_format_query_service_get_available_formats_skips_incomplete_formats(
    query_service
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
            {
                "format_id": "137",
                "url": "https://example.com/video1.mp4"
            },
            {
                # format_idなし（無効）
                "url": "https://example.com/video2.mp4"
            },
            {
                "format_id": "248",
                # urlなし（無効）
            }
        ]
    }

    with patch.object(query_service, '_extract_info', return_value=mock_info):
        # Act
        result = await query_service.get_available_formats(youtube_url=youtube_url)

    # Assert
    assert len(result) == 1
    assert result[0].format_id == "137"


async def test_video_format_query_service_get_available_formats_raises_invalid_url_exception(
    query_service
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
    query_service
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
        query_service,
        '_extract_info',
        side_effect=yt_dlp.utils.DownloadError("Video not found")
    ):
        # Act & Assert
        with pytest.raises(YouTubeResolverError):
            await query_service.get_available_formats(youtube_url=youtube_url)
