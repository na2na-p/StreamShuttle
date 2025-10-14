"""
RedisDao ユニットテスト

RedisDaoの正常系と異常系のテストを提供します。
fakeredisを使用してRedis接続をモックします。
"""

import pytest
from fakeredis import FakeAsyncRedis
from redis.asyncio import RedisError

from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.shared.exceptions import CacheError


@pytest.fixture
async def fake_redis():
    """
    fakeredisを使用したRedisモックのフィクスチャ

    Returns:
        FakeAsyncRedis: テスト用の非同期Redisモックインスタンス
    """
    return FakeAsyncRedis(decode_responses=True)


@pytest.fixture
async def redis_dao(fake_redis):
    """
    RedisDaoのフィクスチャ

    内部のRedisクライアントをfakeredisに差し替えたRedisDaoインスタンスを提供します。

    Args:
        fake_redis: fakeredisインスタンス

    Returns:
        RedisDao: テスト用のRedisDaoインスタンス
    """
    dao = RedisDao(host="localhost", port=6379, db=0)
    dao._redis = fake_redis
    return dao


async def test_redis_dao_set_stores_value_with_ttl(redis_dao, fake_redis):
    """
    正常系: RedisDao.set()がTTL付きで値を保存できることを確認

    Arrange: キー、値、TTLを準備
    Act: RedisDao.set()を呼び出す
    Assert: fakeredisに値が保存されていることを確認
    """
    # Arrange
    key = "test_key"
    value = "test_value"
    ttl = 3600

    # Act
    await redis_dao.set(key=key, value=value, ttl=ttl)

    # Assert
    stored_value = await fake_redis.get(key)
    assert stored_value == value
    assert await fake_redis.ttl(key) > 0


async def test_redis_dao_get_returns_value_for_existing_key(redis_dao, fake_redis):
    """
    正常系: RedisDao.get()が存在するキーの値を取得できることを確認

    Arrange: fakeredisに値を設定
    Act: RedisDao.get()を呼び出す
    Assert: 正しい値が返されることを確認
    """
    # Arrange
    key = "test_key"
    value = "test_value"
    await fake_redis.set(key, value)

    # Act
    result = await redis_dao.get(key=key)

    # Assert
    assert result == value


async def test_redis_dao_get_returns_none_for_nonexistent_key(redis_dao):
    """
    正常系: RedisDao.get()が存在しないキーに対してNoneを返すことを確認

    Arrange: 存在しないキーを準備
    Act: RedisDao.get()を呼び出す
    Assert: Noneが返されることを確認
    """
    # Arrange
    key = "nonexistent_key"

    # Act
    result = await redis_dao.get(key=key)

    # Assert
    assert result is None


async def test_redis_dao_delete_removes_key(redis_dao, fake_redis):
    """
    正常系: RedisDao.delete()がキーを削除できることを確認

    Arrange: fakeredisに値を設定
    Act: RedisDao.delete()を呼び出す
    Assert: fakeredisから値が削除されていることを確認
    """
    # Arrange
    key = "test_key"
    value = "test_value"
    await fake_redis.set(key, value)

    # Act
    await redis_dao.delete(key=key)

    # Assert
    assert await fake_redis.get(key) is None


async def test_redis_dao_delete_does_not_raise_for_nonexistent_key(redis_dao):
    """
    正常系: RedisDao.delete()が存在しないキーに対してエラーを発生させないことを確認

    Arrange: 存在しないキーを準備
    Act: RedisDao.delete()を呼び出す
    Assert: エラーが発生しないことを確認
    """
    # Arrange
    key = "nonexistent_key"

    # Act & Assert
    await redis_dao.delete(key=key)  # エラーが発生しないことを確認


async def test_redis_dao_exists_returns_true_for_existing_key(redis_dao, fake_redis):
    """
    正常系: RedisDao.exists()が存在するキーに対してTrueを返すことを確認

    Arrange: fakeredisに値を設定
    Act: RedisDao.exists()を呼び出す
    Assert: Trueが返されることを確認
    """
    # Arrange
    key = "test_key"
    value = "test_value"
    await fake_redis.set(key, value)

    # Act
    result = await redis_dao.exists(key=key)

    # Assert
    assert result is True


async def test_redis_dao_exists_returns_false_for_nonexistent_key(redis_dao):
    """
    正常系: RedisDao.exists()が存在しないキーに対してFalseを返すことを確認

    Arrange: 存在しないキーを準備
    Act: RedisDao.exists()を呼び出す
    Assert: Falseが返されることを確認
    """
    # Arrange
    key = "nonexistent_key"

    # Act
    result = await redis_dao.exists(key=key)

    # Assert
    assert result is False


async def test_redis_dao_set_raises_cache_exception_on_redis_error(redis_dao, mocker):
    """
    異常系: Redis操作エラー時にRedisDao.set()がCacheErrorを発生させることを確認

    Arrange: Redisクライアントのsetexメソッドをモックしてエラーを発生させる
    Act: RedisDao.set()を呼び出す
    Assert: CacheErrorが発生することを確認
    """
    # Arrange
    mocker.patch.object(redis_dao._redis, "setex", side_effect=RedisError("Redis connection error"))

    # Act & Assert
    with pytest.raises(CacheError) as exc_info:
        await redis_dao.set(key="test_key", value="test_value", ttl=3600)

    assert "Redisへの保存に失敗しました" in str(exc_info.value)


async def test_redis_dao_get_raises_cache_exception_on_redis_error(redis_dao, mocker):
    """
    異常系: Redis操作エラー時にRedisDao.get()がCacheErrorを発生させることを確認

    Arrange: Redisクライアントのgetメソッドをモックしてエラーを発生させる
    Act: RedisDao.get()を呼び出す
    Assert: CacheErrorが発生することを確認
    """
    # Arrange
    mocker.patch.object(redis_dao._redis, "get", side_effect=RedisError("Redis connection error"))

    # Act & Assert
    with pytest.raises(CacheError) as exc_info:
        await redis_dao.get(key="test_key")

    assert "Redisからの取得に失敗しました" in str(exc_info.value)


async def test_redis_dao_delete_raises_cache_exception_on_redis_error(redis_dao, mocker):
    """
    異常系: Redis操作エラー時にRedisDao.delete()がCacheErrorを発生させることを確認

    Arrange: Redisクライアントのdeleteメソッドをモックしてエラーを発生させる
    Act: RedisDao.delete()を呼び出す
    Assert: CacheErrorが発生することを確認
    """
    # Arrange
    mocker.patch.object(
        redis_dao._redis, "delete", side_effect=RedisError("Redis connection error")
    )

    # Act & Assert
    with pytest.raises(CacheError) as exc_info:
        await redis_dao.delete(key="test_key")

    assert "Redisからの削除に失敗しました" in str(exc_info.value)


async def test_redis_dao_exists_raises_cache_exception_on_redis_error(redis_dao, mocker):
    """
    異常系: Redis操作エラー時にRedisDao.exists()がCacheErrorを発生させることを確認

    Arrange: Redisクライアントのexistsメソッドをモックしてエラーを発生させる
    Act: RedisDao.exists()を呼び出す
    Assert: CacheErrorが発生することを確認
    """
    # Arrange
    mocker.patch.object(
        redis_dao._redis, "exists", side_effect=RedisError("Redis connection error")
    )

    # Act & Assert
    with pytest.raises(CacheError) as exc_info:
        await redis_dao.exists(key="test_key")

    assert "Redisの存在確認に失敗しました" in str(exc_info.value)
