"""
StreamUrlRepository ユニットテスト

StreamUrlRepositoryの正常系と異常系のテストを提供します。
RedisDaoをモック化してテストします。
"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.domain.model.stream_url.stream_url import StreamUrl
from streamshuttle.domain.model.stream_url.video_id import VideoId
from streamshuttle.infrastructure.repository.stream_url_repository import StreamUrlRepository
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
def repository(mock_redis_dao):
    """
    StreamUrlRepositoryのフィクスチャ

    Args:
        mock_redis_dao: モックされたRedisDaoインスタンス

    Returns:
        StreamUrlRepository: テスト用のStreamUrlRepositoryインスタンス
    """
    return StreamUrlRepository(redis_dao=mock_redis_dao)


async def test_stream_url_repository_save_calls_redis_dao_set(repository, mock_redis_dao):
    """
    正常系: StreamUrlRepository.save()がRedisDaoのset()を呼び出すことを確認

    Arrange: StreamUrlを準備
    Act: StreamUrlRepository.save()を呼び出す
    Assert: RedisDaoのset()が正しいパラメータで呼び出されたことを確認
    """
    # Arrange
    stream_url = StreamUrl.create(
        video_id="dQw4w9WgXcQ", resolved_url="https://example.com/video.m3u8", ttl_seconds=3600
    )

    # Act
    await repository.save(stream_url=stream_url)

    # Assert
    mock_redis_dao.set.assert_called_once()
    call_args = mock_redis_dao.set.call_args
    # hls=Falseがデフォルトなので、キャッシュキーに含まれる
    assert call_args.kwargs["key"] == "dQw4w9WgXcQ:hls:False"
    assert call_args.kwargs["value"] == "https://example.com/video.m3u8"
    assert call_args.kwargs["ttl"] > 0


async def test_stream_url_repository_save_raises_cache_exception_on_redis_error(
    repository, mock_redis_dao
):
    """
    異常系: Redis操作エラー時にStreamUrlRepository.save()がCacheErrorを
    発生させることを確認

    Arrange: RedisDaoのset()をモックしてCacheErrorを発生させる
    Act: StreamUrlRepository.save()を呼び出す
    Assert: CacheErrorが発生することを確認
    """
    # Arrange
    stream_url = StreamUrl.create(
        video_id="dQw4w9WgXcQ", resolved_url="https://example.com/video.m3u8", ttl_seconds=3600
    )
    mock_redis_dao.set.side_effect = CacheError("Redis error")

    # Act & Assert
    with pytest.raises(CacheError):
        await repository.save(stream_url=stream_url)


async def test_stream_url_repository_delete_calls_redis_dao_delete(repository, mock_redis_dao):
    """
    正常系: StreamUrlRepository.delete()がRedisDaoのdelete()を呼び出すことを確認

    Arrange: VideoIdを準備
    Act: StreamUrlRepository.delete()を呼び出す
    Assert: RedisDaoのdelete()が正しいキーで呼び出されたことを確認
    """
    # Arrange
    video_id = VideoId(_value="dQw4w9WgXcQ")

    # Act
    await repository.delete(video_id=video_id)

    # Assert
    mock_redis_dao.delete.assert_called_once_with(key="dQw4w9WgXcQ:hls:False")


async def test_stream_url_repository_delete_with_hls_true(repository, mock_redis_dao):
    """
    正常系: StreamUrlRepository.delete()がhls=Trueで正しいキャッシュキーを使用することを確認

    Arrange: VideoIdを準備
    Act: StreamUrlRepository.delete()をhls=Trueで呼び出す
    Assert: RedisDaoのdelete()がHLS用キャッシュキーで呼び出されたことを確認
    """
    # Arrange
    video_id = VideoId(_value="dQw4w9WgXcQ")

    # Act
    await repository.delete(video_id=video_id, hls=True)

    # Assert
    mock_redis_dao.delete.assert_called_once_with(key="dQw4w9WgXcQ:hls:True")


async def test_stream_url_repository_delete_raises_cache_exception_on_redis_error(
    repository, mock_redis_dao
):
    """
    異常系: Redis操作エラー時にStreamUrlRepository.delete()がCacheErrorを
    発生させることを確認

    Arrange: RedisDaoのdelete()をモックしてCacheErrorを発生させる
    Act: StreamUrlRepository.delete()を呼び出す
    Assert: CacheErrorが発生することを確認
    """
    # Arrange
    video_id = VideoId(_value="dQw4w9WgXcQ")
    mock_redis_dao.delete.side_effect = CacheError("Redis error")

    # Act & Assert
    with pytest.raises(CacheError):
        await repository.delete(video_id=video_id)
