"""
GetPlaylistUseCase ユニットテスト

キャッシュヒット/ミス時の動作と、URLの正規化を検証します。
"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.shared.exceptions import InvalidPlaylistIdError, InvalidUrlError
from streamshuttle.usecase.dto.playlist_dto import PlaylistDto
from streamshuttle.usecase.dto.playlist_info_dto import PlaylistInfoDto
from streamshuttle.usecase.dto.playlist_item_dto import PlaylistItemDto
from streamshuttle.usecase.query.get_playlist_usecase import GetPlaylistUseCase

PLAYLIST_ID = "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
PLAYLIST_URL = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"


@pytest.fixture
def playlist_info():
    """プレイリスト情報のfixture"""
    return PlaylistInfoDto(
        playlist_id=PLAYLIST_ID,
        title="テストプレイリスト",
        uploader="テストチャンネル",
        item_count=1,
        truncated=False,
    )


@pytest.fixture
def items():
    """動画一覧のfixture"""
    return [
        PlaylistItemDto(
            video_id="dQw4w9WgXcQ",
            title="1曲目",
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            duration_seconds=120,
            thumbnail_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
        )
    ]


@pytest.fixture
def mock_query_service(playlist_info, items):
    """PlaylistQueryServiceのモック"""
    query_service = AsyncMock()
    query_service.get_playlist.return_value = (playlist_info, items)
    return query_service


@pytest.fixture
def mock_repository():
    """PlaylistRepositoryのモック"""
    return AsyncMock()


@pytest.fixture
def mock_cache_query_service():
    """PlaylistCacheQueryServiceのモック（デフォルトはキャッシュミス）"""
    cache_query_service = AsyncMock()
    cache_query_service.find_by_playlist_id.return_value = None
    return cache_query_service


@pytest.fixture
def use_case(mock_query_service, mock_repository, mock_cache_query_service):
    """GetPlaylistUseCaseのfixture"""
    return GetPlaylistUseCase(
        query_service=mock_query_service,
        repository=mock_repository,
        cache_query_service=mock_cache_query_service,
    )


async def test_execute_fetches_and_caches_on_cache_miss(
    use_case, mock_query_service, mock_repository, mock_cache_query_service, items
):
    """正常系: キャッシュミス時にyt-dlpで取得し、キャッシュに保存する"""
    # Act
    result_info, result_items = await use_case.execute(PLAYLIST_URL)

    # Assert
    mock_cache_query_service.find_by_playlist_id.assert_called_once_with(PLAYLIST_ID)
    mock_query_service.get_playlist.assert_called_once_with(PLAYLIST_URL)
    mock_repository.save.assert_called_once()
    assert mock_repository.save.call_args.kwargs["playlist_id"] == PLAYLIST_ID
    assert result_info.playlist_id == PLAYLIST_ID
    assert result_items == items


async def test_execute_returns_cached_playlist_on_cache_hit(
    use_case, mock_query_service, mock_repository, mock_cache_query_service, playlist_info, items
):
    """正常系: キャッシュヒット時はyt-dlpを呼び出さない"""
    # Arrange
    mock_cache_query_service.find_by_playlist_id.return_value = PlaylistDto(
        playlist_info=playlist_info, items=items
    )

    # Act
    result_info, result_items = await use_case.execute(PLAYLIST_URL)

    # Assert
    mock_query_service.get_playlist.assert_not_called()
    mock_repository.save.assert_not_called()
    assert result_info == playlist_info
    assert result_items == items


async def test_execute_normalizes_watch_url_before_fetching(use_case, mock_query_service):
    """正常系: listパラメータ付きwatch URLがプレイリスト取得用URLに正規化される"""
    # Arrange
    watch_url = f"https://www.youtube.com/watch?v=dQw4w9WgXcQ&list={PLAYLIST_ID}"

    # Act
    await use_case.execute(watch_url)

    # Assert
    mock_query_service.get_playlist.assert_called_once_with(PLAYLIST_URL)


async def test_execute_raises_invalid_url_error(use_case):
    """異常系: 許可されないドメインのURLでInvalidUrlErrorが送出される"""
    # Act & Assert
    with pytest.raises(InvalidUrlError):
        await use_case.execute("https://example.com/playlist?list=PLtest")


async def test_execute_raises_invalid_playlist_id_error(use_case):
    """異常系: listパラメータがないURLでInvalidPlaylistIdErrorが送出される"""
    # Act & Assert
    with pytest.raises(InvalidPlaylistIdError):
        await use_case.execute("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
