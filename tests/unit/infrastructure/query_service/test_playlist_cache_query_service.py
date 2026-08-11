"""PlaylistCacheQueryServiceのテストモジュール"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.infrastructure.query_service.playlist_cache_query_service import (
    PlaylistCacheQueryService,
)
from streamshuttle.usecase.dto.playlist_dto import PlaylistDto

PLAYLIST_ID = "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
CACHED_JSON = (
    '{"playlist_info":{"playlist_id":"PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",'
    '"title":"テストプレイリスト","uploader":"テストチャンネル","item_count":1,'
    '"truncated":false},'
    '"items":[{"video_id":"dQw4w9WgXcQ","title":"1曲目",'
    '"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","duration_seconds":120,'
    '"thumbnail_url":"https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg"}]}'
)


@pytest.fixture
def mock_redis_dao():
    """RedisDao のモックを提供するfixture"""
    return AsyncMock()


@pytest.fixture
def query_service(mock_redis_dao):
    """PlaylistCacheQueryService のインスタンスを提供するfixture"""
    return PlaylistCacheQueryService(redis_dao=mock_redis_dao)


async def test_find_by_playlist_id_returns_dto_on_cache_hit(query_service, mock_redis_dao):
    """正常系: キャッシュヒット時にPlaylistDtoを返す"""
    # Arrange
    mock_redis_dao.get.return_value = CACHED_JSON

    # Act
    result = await query_service.find_by_playlist_id(playlist_id=PLAYLIST_ID)

    # Assert
    assert isinstance(result, PlaylistDto)
    assert result.playlist_info.playlist_id == PLAYLIST_ID
    assert len(result.items) == 1
    mock_redis_dao.get.assert_called_once_with(key=f"playlist:{PLAYLIST_ID}")


async def test_find_by_playlist_id_returns_none_on_cache_miss(query_service, mock_redis_dao):
    """正常系: キャッシュミス時にNoneを返す"""
    # Arrange
    mock_redis_dao.get.return_value = None

    # Act
    result = await query_service.find_by_playlist_id(playlist_id=PLAYLIST_ID)

    # Assert
    assert result is None


async def test_find_by_playlist_id_returns_none_on_invalid_json(query_service, mock_redis_dao):
    """正常系: JSON破損時にNoneを返す"""
    # Arrange
    mock_redis_dao.get.return_value = "invalid json"

    # Act
    result = await query_service.find_by_playlist_id(playlist_id=PLAYLIST_ID)

    # Assert
    assert result is None


async def test_find_by_playlist_id_returns_none_on_redis_error(query_service, mock_redis_dao):
    """正常系: Redisエラー時にNoneを返す"""
    # Arrange
    mock_redis_dao.get.side_effect = Exception("Redis connection failed")

    # Act
    result = await query_service.find_by_playlist_id(playlist_id=PLAYLIST_ID)

    # Assert
    assert result is None


async def test_find_by_playlist_id_returns_none_on_invalid_playlist_id(
    query_service, mock_redis_dao
):
    """正常系: 不正なプレイリストIDではRedisを参照せずNoneを返す"""
    # Act
    result = await query_service.find_by_playlist_id(playlist_id="invalid id!")

    # Assert
    assert result is None
    mock_redis_dao.get.assert_not_called()
