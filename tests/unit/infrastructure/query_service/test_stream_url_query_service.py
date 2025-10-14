"""
StreamUrlQueryService ユニットテスト

StreamUrlQueryServiceの正常系と異常系のテストを提供します。
RedisDaoをモック化してテストします。
"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.infrastructure.query_service.stream_url_query_service import (
    StreamUrlQueryService,
)
from streamshuttle.shared.exceptions import CacheError


@pytest.fixture
def mock_redis_dao():
    """
    モックされたRedisDaoのフィクスチャ

    Returns:
        AsyncMock: モックされたRedisDaoインスタンス
    """
    return AsyncMock()


@pytest.fixture
def query_service(mock_redis_dao):
    """
    StreamUrlQueryServiceのフィクスチャ

    Args:
        mock_redis_dao: モックされたRedisDaoインスタンス

    Returns:
        StreamUrlQueryService: テスト用のStreamUrlQueryServiceインスタンス
    """
    return StreamUrlQueryService(redis_dao=mock_redis_dao)


async def test_stream_url_query_service_find_by_video_id_returns_dto(
    query_service, mock_redis_dao
):
    """
    正常系: StreamUrlQueryService.find_by_video_id()がキャッシュが存在する場合に
    StreamUrlDtoを返すことを確認

    Arrange: RedisDaoのget()をモックして値を返す
    Act: StreamUrlQueryService.find_by_video_id()を呼び出す
    Assert: StreamUrlDtoが返されることを確認
    """
    # Arrange
    video_id = "dQw4w9WgXcQ"
    cached_url = "https://example.com/video.m3u8"
    mock_redis_dao.get.return_value = cached_url

    # Act
    result = await query_service.find_by_video_id(video_id=video_id)

    # Assert
    assert result is not None
    assert result.video_id == video_id
    assert result.resolved_url == cached_url
    assert result.expiry_at is not None
    mock_redis_dao.get.assert_called_once_with(key=video_id)


async def test_stream_url_query_service_find_by_video_id_returns_none_for_cache_miss(
    query_service, mock_redis_dao
):
    """
    正常系: StreamUrlQueryService.find_by_video_id()がキャッシュが存在しない場合に
    Noneを返すことを確認

    Arrange: RedisDaoのget()をモックしてNoneを返す
    Act: StreamUrlQueryService.find_by_video_id()を呼び出す
    Assert: Noneが返されることを確認
    """
    # Arrange
    video_id = "dQw4w9WgXcQ"
    mock_redis_dao.get.return_value = None

    # Act
    result = await query_service.find_by_video_id(video_id=video_id)

    # Assert
    assert result is None
    mock_redis_dao.get.assert_called_once_with(key=video_id)


async def test_stream_url_query_service_find_by_video_id_raises_cache_exception_on_redis_error(
    query_service, mock_redis_dao
):
    """
    異常系: Redis操作エラー時にStreamUrlQueryService.find_by_video_id()が
    CacheErrorを発生させることを確認

    Arrange: RedisDaoのget()をモックしてCacheErrorを発生させる
    Act: StreamUrlQueryService.find_by_video_id()を呼び出す
    Assert: CacheErrorが発生することを確認
    """
    # Arrange
    video_id = "dQw4w9WgXcQ"
    mock_redis_dao.get.side_effect = CacheError("Redis error")

    # Act & Assert
    with pytest.raises(CacheError):
        await query_service.find_by_video_id(video_id=video_id)
