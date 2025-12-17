"""VideoFormatsRepositoryのテストモジュール"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.infrastructure.repository.video_formats_repository import (
    VideoFormatsRepository,
)
from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_formats_dto import VideoFormatsDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto


@pytest.fixture
def mock_redis_dao():
    """RedisDao のモックを提供するfixture"""
    return AsyncMock()


@pytest.fixture
def repository(mock_redis_dao):
    """VideoFormatsRepository のインスタンスを提供するfixture"""
    return VideoFormatsRepository(redis_dao=mock_redis_dao)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "video_id, video_formats",
    [
        pytest.param(
            "dQw4w9WgXcQ",
            VideoFormatsDto(
                video_info=VideoInfoDto(
                    video_id="dQw4w9WgXcQ",
                    title="Test Video",
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
            id="正常系: ビデオフォーマット情報をキャッシュに保存する",
        ),
    ],
)
async def test_save_caches_video_formats(repository, mock_redis_dao, video_id, video_formats):
    """正常系: save()がビデオフォーマット情報をキャッシュに保存する"""
    # Act
    await repository.save(video_id=video_id, video_formats=video_formats)

    # Assert
    mock_redis_dao.set.assert_called_once()
    call_args = mock_redis_dao.set.call_args
    assert call_args.kwargs["key"] == f"video_formats:{video_id}"
    assert "dQw4w9WgXcQ" in call_args.kwargs["value"]  # JSON内にvideo_idが含まれる
    assert call_args.kwargs["ttl"] > 0


@pytest.mark.asyncio
async def test_save_does_not_raise_on_redis_error(repository, mock_redis_dao):
    """正常系: Redisエラー時でも例外を投げない（ベストエフォート）"""
    # Arrange
    mock_redis_dao.set.side_effect = Exception("Redis connection failed")
    video_formats = VideoFormatsDto(
        video_info=VideoInfoDto(
            video_id="test",
            title="Test",
            thumbnail_url="https://example.com/thumb.jpg",
        ),
        formats=[],
    )

    # Act & Assert (例外が投げられないことを確認)
    await repository.save(video_id="test", video_formats=video_formats)
