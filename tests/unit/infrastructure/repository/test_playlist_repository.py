"""PlaylistRepositoryのテストモジュール"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.infrastructure.repository.playlist_repository import PlaylistRepository
from streamshuttle.usecase.dto.playlist_dto import PlaylistDto
from streamshuttle.usecase.dto.playlist_info_dto import PlaylistInfoDto
from streamshuttle.usecase.dto.playlist_item_dto import PlaylistItemDto

PLAYLIST_ID = "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"


@pytest.fixture
def mock_redis_dao():
    """RedisDao のモックを提供するfixture"""
    return AsyncMock()


@pytest.fixture
def repository(mock_redis_dao):
    """PlaylistRepository のインスタンスを提供するfixture"""
    return PlaylistRepository(redis_dao=mock_redis_dao)


@pytest.fixture
def playlist():
    """保存対象のPlaylistDtoを提供するfixture"""
    return PlaylistDto(
        playlist_info=PlaylistInfoDto(
            playlist_id=PLAYLIST_ID,
            title="テストプレイリスト",
            uploader="テストチャンネル",
            item_count=1,
            truncated=False,
        ),
        items=[
            PlaylistItemDto(
                video_id="dQw4w9WgXcQ",
                title="1曲目",
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                duration_seconds=120,
                thumbnail_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
            )
        ],
    )


async def test_save_caches_playlist(repository, mock_redis_dao, playlist):
    """正常系: save()がプレイリスト情報をキャッシュに保存する"""
    # Act
    await repository.save(playlist_id=PLAYLIST_ID, playlist=playlist)

    # Assert
    mock_redis_dao.set.assert_called_once()
    call_args = mock_redis_dao.set.call_args
    assert call_args.kwargs["key"] == f"playlist:{PLAYLIST_ID}"
    assert "dQw4w9WgXcQ" in call_args.kwargs["value"]
    assert call_args.kwargs["ttl"] > 0


async def test_save_does_not_raise_on_redis_error(repository, mock_redis_dao, playlist):
    """正常系: Redisエラー時でも例外を投げない（ベストエフォート）"""
    # Arrange
    mock_redis_dao.set.side_effect = Exception("Redis connection failed")

    # Act & Assert（例外が投げられないことを確認）
    await repository.save(playlist_id=PLAYLIST_ID, playlist=playlist)


async def test_save_does_not_raise_on_invalid_playlist_id(repository, mock_redis_dao, playlist):
    """正常系: 不正なプレイリストIDでも例外を投げず、保存を行わない"""
    # Act & Assert（例外が投げられないことを確認）
    await repository.save(playlist_id="invalid id!", playlist=playlist)

    # Assert
    mock_redis_dao.set.assert_not_called()
