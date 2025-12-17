"""VideoFormatsCacheQueryServiceのテストモジュール"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.infrastructure.query_service.video_formats_cache_query_service import (
    VideoFormatsCacheQueryService,
)
from streamshuttle.usecase.dto.video_formats_dto import VideoFormatsDto


@pytest.fixture
def mock_redis_dao():
    """RedisDao のモックを提供するfixture"""
    return AsyncMock()


@pytest.fixture
def query_service(mock_redis_dao):
    """VideoFormatsCacheQueryService のインスタンスを提供するfixture"""
    return VideoFormatsCacheQueryService(redis_dao=mock_redis_dao)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "video_id, cached_json",
    [
        pytest.param(
            "dQw4w9WgXcQ",
            '{"video_info":{"video_id":"dQw4w9WgXcQ","title":"Test Video","thumbnail_url":"https://example.com/thumb.jpg"},"formats":[{"format_id":"137","quality":"1080p","codec":"avc1","url":"https://example.com/video.mp4","has_audio":false,"has_video":true}]}',
            id="正常系: キャッシュヒット時にVideoFormatsDtoを返す",
        ),
    ],
)
async def test_find_by_video_id_returns_dto_on_cache_hit(
    query_service, mock_redis_dao, video_id, cached_json
):
    """正常系: キャッシュヒット時にVideoFormatsDtoを返す"""
    # Arrange
    mock_redis_dao.get.return_value = cached_json

    # Act
    result = await query_service.find_by_video_id(video_id=video_id)

    # Assert
    assert result is not None
    assert isinstance(result, VideoFormatsDto)
    assert result.video_info.video_id == video_id
    mock_redis_dao.get.assert_called_once_with(key=f"video_formats:{video_id}")


@pytest.mark.asyncio
async def test_find_by_video_id_returns_none_on_cache_miss(query_service, mock_redis_dao):
    """正常系: キャッシュミス時にNoneを返す"""
    # Arrange
    mock_redis_dao.get.return_value = None

    # Act
    result = await query_service.find_by_video_id(video_id="test")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_find_by_video_id_returns_none_on_invalid_json(query_service, mock_redis_dao):
    """正常系: JSON破損時にNoneを返す"""
    # Arrange
    mock_redis_dao.get.return_value = "invalid json"

    # Act
    result = await query_service.find_by_video_id(video_id="test")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_find_by_video_id_returns_none_on_redis_error(query_service, mock_redis_dao):
    """正常系: Redisエラー時にNoneを返す"""
    # Arrange
    mock_redis_dao.get.side_effect = Exception("Redis connection failed")

    # Act
    result = await query_service.find_by_video_id(video_id="test")

    # Assert
    assert result is None
