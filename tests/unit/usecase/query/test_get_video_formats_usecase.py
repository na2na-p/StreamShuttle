"""GetVideoFormatsUseCaseのテストモジュール"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_formats_dto import VideoFormatsDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto
from streamshuttle.usecase.query.get_video_formats_usecase import GetVideoFormatsUseCase


@pytest.fixture
def mock_query_service():
    """VideoFormatQueryServiceのモック"""
    return AsyncMock()


@pytest.fixture
def mock_repository():
    """VideoFormatsRepositoryのモック"""
    return AsyncMock()


@pytest.fixture
def mock_cache_query_service():
    """VideoFormatsCacheQueryServiceのモック"""
    return AsyncMock()


@pytest.fixture
def usecase(mock_query_service, mock_repository, mock_cache_query_service):
    """GetVideoFormatsUseCaseのインスタンス"""
    return GetVideoFormatsUseCase(
        query_service=mock_query_service,
        repository=mock_repository,
        cache_query_service=mock_cache_query_service,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "youtube_url, video_id, cached_data",
    [
        pytest.param(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
            VideoFormatsDto(
                video_info=VideoInfoDto(
                    video_id="dQw4w9WgXcQ",
                    title="Cached Video",
                    thumbnail_url="https://example.com/thumb.jpg",
                ),
                formats=[
                    VideoFormatDto(
                        format_id="137",
                        quality="1080p",
                        codec="avc1",
                        url="https://example.com/video.mp4",
                        has_audio=False,
                        has_video=True,
                    )
                ],
            ),
            id="正常系: キャッシュヒット時にyt-dlpを呼び出さない",
        ),
    ],
)
async def test_execute_returns_cached_data_on_cache_hit(
    usecase, mock_query_service, mock_cache_query_service, youtube_url, video_id, cached_data
):
    """正常系: キャッシュヒット時にキャッシュデータを返し、yt-dlpを呼び出さない"""
    # Arrange
    mock_cache_query_service.find_by_video_id.return_value = cached_data

    # Act
    video_info, formats = await usecase.execute(youtube_url)

    # Assert
    assert video_info == cached_data.video_info
    assert formats == cached_data.formats
    mock_cache_query_service.find_by_video_id.assert_called_once_with(video_id)
    mock_query_service.get_available_formats.assert_not_called()


@pytest.mark.asyncio
async def test_execute_calls_ytdlp_and_saves_on_cache_miss(
    usecase, mock_query_service, mock_repository, mock_cache_query_service
):
    """正常系: キャッシュミス時にyt-dlpを呼び出し、結果をキャッシュに保存する"""
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=test1234567"
    video_id = "test1234567"

    mock_cache_query_service.find_by_video_id.return_value = None

    video_info = VideoInfoDto(
        video_id=video_id,
        title="Test Video",
        thumbnail_url="https://example.com/thumb.jpg",
    )
    formats = [
        VideoFormatDto(
            format_id="18",
            quality="360p",
            codec="avc1",
            url="https://example.com/video.mp4",
            has_audio=True,
            has_video=True,
        )
    ]
    mock_query_service.get_available_formats.return_value = (video_info, formats)

    # Act
    result_info, result_formats = await usecase.execute(youtube_url)

    # Assert
    assert result_info == video_info
    assert result_formats == formats
    mock_query_service.get_available_formats.assert_called_once_with(youtube_url)
    mock_repository.save.assert_called_once()

    # キャッシュ保存の引数を確認
    save_call = mock_repository.save.call_args
    assert save_call.kwargs["video_id"] == video_id
    assert save_call.kwargs["video_formats"].video_info == video_info
    assert save_call.kwargs["video_formats"].formats == formats
