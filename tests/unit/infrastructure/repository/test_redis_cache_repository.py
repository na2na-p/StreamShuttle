"""RedisCacheRepositoryのユニットテスト"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.infrastructure.repository.redis_cache_repository import RedisCacheRepository


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "key, expected_value",
    [
        pytest.param("test_key", "test_value", id="正常系: 値が存在する場合"),
        pytest.param("missing_key", None, id="正常系: 値が存在しない場合はNoneを返す"),
    ],
)
async def test_get(key: str, expected_value: str | None):
    """get()メソッドのテスト"""
    # Arrange
    mock_redis_dao = AsyncMock()
    mock_redis_dao.get.return_value = expected_value
    repository = RedisCacheRepository(mock_redis_dao)

    # Act
    result = await repository.get(key)

    # Assert
    assert result == expected_value
    mock_redis_dao.get.assert_called_once_with(key)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "key, value, ttl",
    [
        pytest.param("test_key", "test_value", 3600, id="正常系: TTL付きで値を保存"),
        pytest.param("another_key", "another_value", 7200, id="正常系: 異なるTTLで保存"),
    ],
)
async def test_set(key: str, value: str, ttl: int):
    """set()メソッドのテスト"""
    # Arrange
    mock_redis_dao = AsyncMock()
    mock_redis_dao.set.return_value = None
    repository = RedisCacheRepository(mock_redis_dao)

    # Act
    await repository.set(key, value, ttl)

    # Assert
    mock_redis_dao.set.assert_called_once_with(key=key, value=value, ttl=ttl)
