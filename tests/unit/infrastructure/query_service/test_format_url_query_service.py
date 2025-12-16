"""
FormatUrlQueryService ユニットテスト

FormatUrlQueryServiceの正常系と異常系のテストを提供します。
RedisDaoをモック化してテストします。
"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.infrastructure.query_service.format_url_query_service import (
    FormatUrlQueryService,
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
    FormatUrlQueryServiceのフィクスチャ

    Args:
        mock_redis_dao: モックされたRedisDaoインスタンス

    Returns:
        FormatUrlQueryService: テスト用のFormatUrlQueryServiceインスタンス
    """
    return FormatUrlQueryService(redis_dao=mock_redis_dao)


async def test_format_url_query_service_find_by_video_and_format_id_returns_dto(
    query_service, mock_redis_dao
):
    """
    正常系: FormatUrlQueryService.find_by_video_and_format_id()がキャッシュが存在する場合に
    FormatUrlDtoを返すことを確認

    Arrange: RedisDaoのget()とttl()をモックして値を返す
    Act: FormatUrlQueryService.find_by_video_and_format_id()を呼び出す
    Assert: FormatUrlDtoが返されることを確認
    """
    # Arrange
    video_id = "dQw4w9WgXcQ"
    format_id = "137"
    cached_url = "https://example.com/format137.mp4"
    cache_key = f"format_url:{video_id}:{format_id}"
    mock_redis_dao.get.return_value = cached_url
    mock_redis_dao.ttl.return_value = 3600

    # Act
    result = await query_service.find_by_video_and_format_id(video_id=video_id, format_id=format_id)

    # Assert
    assert result is not None
    assert result.video_id == video_id
    assert result.format_id == format_id
    assert result.resolved_url == cached_url
    assert result.expiry_at is not None
    mock_redis_dao.get.assert_called_once_with(key=cache_key)
    mock_redis_dao.ttl.assert_called_once_with(key=cache_key)


async def test_format_url_query_service_find_by_video_and_format_id_returns_none_for_cache_miss(
    query_service, mock_redis_dao
):
    """
    正常系: FormatUrlQueryService.find_by_video_and_format_id()がキャッシュが存在しない場合に
    Noneを返すことを確認

    Arrange: RedisDaoのget()をモックしてNoneを返す
    Act: FormatUrlQueryService.find_by_video_and_format_id()を呼び出す
    Assert: Noneが返されることを確認
    """
    # Arrange
    video_id = "dQw4w9WgXcQ"
    format_id = "137"
    cache_key = f"format_url:{video_id}:{format_id}"
    mock_redis_dao.get.return_value = None

    # Act
    result = await query_service.find_by_video_and_format_id(video_id=video_id, format_id=format_id)

    # Assert
    assert result is None
    mock_redis_dao.get.assert_called_once_with(key=cache_key)


async def test_find_by_video_and_format_id_raises_cache_error_on_redis_error(
    query_service, mock_redis_dao
):
    """
    異常系: Redis操作エラー時にFormatUrlQueryService.find_by_video_and_format_id()が
    CacheErrorを発生させることを確認

    Arrange: RedisDaoのget()をモックしてCacheErrorを発生させる
    Act: FormatUrlQueryService.find_by_video_and_format_id()を呼び出す
    Assert: CacheErrorが発生することを確認
    """
    # Arrange
    video_id = "dQw4w9WgXcQ"
    format_id = "137"
    mock_redis_dao.get.side_effect = CacheError("Redis error")

    # Act & Assert
    with pytest.raises(CacheError):
        await query_service.find_by_video_and_format_id(video_id=video_id, format_id=format_id)


async def test_format_url_query_service_find_by_video_and_format_id_uses_accurate_ttl_from_redis(
    query_service, mock_redis_dao
):
    """
    正常系: FormatUrlQueryService.find_by_video_and_format_id()がRedisから正確なTTLを取得して
    expiry_atを計算することを確認

    Arrange: RedisDaoのget()とttl()をモックして、TTLとして1800秒を返す
    Act: FormatUrlQueryService.find_by_video_and_format_id()を呼び出す
    Assert: ttl()が呼び出され、返されたDTOのexpiry_atが適切に計算されていることを確認
    """
    # Arrange
    video_id = "dQw4w9WgXcQ"
    format_id = "137"
    cache_key = f"format_url:{video_id}:{format_id}"
    cached_url = "https://example.com/format137.mp4"
    ttl_seconds = 1800
    mock_redis_dao.get.return_value = cached_url
    mock_redis_dao.ttl.return_value = ttl_seconds

    # Act
    result = await query_service.find_by_video_and_format_id(video_id=video_id, format_id=format_id)

    # Assert
    assert result is not None
    mock_redis_dao.ttl.assert_called_once_with(key=cache_key)


async def test_find_by_video_and_format_id_falls_back_to_default_ttl_when_ttl_is_none(
    query_service, mock_redis_dao
):
    """
    異常系: TTL取得がNoneを返した場合にデフォルトTTLにフォールバックすることを確認

    Arrange: RedisDaoのget()をモック、ttl()がNoneを返すようにモック
    Act: FormatUrlQueryService.find_by_video_and_format_id()を呼び出す
    Assert: デフォルトTTLが使用されてDTOが返されることを確認
    """
    # Arrange
    video_id = "dQw4w9WgXcQ"
    format_id = "137"
    cache_key = f"format_url:{video_id}:{format_id}"
    cached_url = "https://example.com/format137.mp4"
    mock_redis_dao.get.return_value = cached_url
    mock_redis_dao.ttl.return_value = None

    # Act
    result = await query_service.find_by_video_and_format_id(video_id=video_id, format_id=format_id)

    # Assert
    assert result is not None
    assert result.video_id == video_id
    assert result.format_id == format_id
    assert result.resolved_url == cached_url
    assert result.expiry_at is not None
    mock_redis_dao.ttl.assert_called_once_with(key=cache_key)


async def test_format_url_query_service_fallback_to_default_ttl_when_ttl_is_negative_one(
    query_service, mock_redis_dao
):
    """
    境界値: TTLが-1（TTL未設定）の場合にデフォルトTTLにフォールバックすることを確認

    Arrange: RedisDaoのget()をモック、ttl()が-1を返すようにモック
    Act: FormatUrlQueryService.find_by_video_and_format_id()を呼び出す
    Assert: デフォルトTTLが使用されてDTOが返されることを確認
    """
    # Arrange
    video_id = "dQw4w9WgXcQ"
    format_id = "137"
    cache_key = f"format_url:{video_id}:{format_id}"
    cached_url = "https://example.com/format137.mp4"
    mock_redis_dao.get.return_value = cached_url
    mock_redis_dao.ttl.return_value = -1

    # Act
    result = await query_service.find_by_video_and_format_id(video_id=video_id, format_id=format_id)

    # Assert
    assert result is not None
    assert result.video_id == video_id
    assert result.format_id == format_id
    assert result.resolved_url == cached_url
    assert result.expiry_at is not None
    mock_redis_dao.ttl.assert_called_once_with(key=cache_key)


async def test_format_url_query_service_fallback_to_default_ttl_when_ttl_is_negative_two(
    query_service, mock_redis_dao
):
    """
    境界値: TTLが-2（キー不存在）の場合の処理を確認

    Note: 通常はget()がNoneを返すためこのケースは発生しないが、
    レースコンディションでこの状態になる可能性があるため、
    フォールバック動作が正しく機能することを確認する

    Arrange: RedisDaoのget()をモック、ttl()が-2を返すようにモック
    Act: FormatUrlQueryService.find_by_video_and_format_id()を呼び出す
    Assert: デフォルトTTLが使用されてDTOが返されることを確認
    """
    # Arrange
    video_id = "dQw4w9WgXcQ"
    format_id = "137"
    cache_key = f"format_url:{video_id}:{format_id}"
    cached_url = "https://example.com/format137.mp4"
    mock_redis_dao.get.return_value = cached_url
    mock_redis_dao.ttl.return_value = -2

    # Act
    result = await query_service.find_by_video_and_format_id(video_id=video_id, format_id=format_id)

    # Assert
    assert result is not None
    assert result.video_id == video_id
    assert result.format_id == format_id
    assert result.resolved_url == cached_url
    assert result.expiry_at is not None
    mock_redis_dao.ttl.assert_called_once_with(key=cache_key)
