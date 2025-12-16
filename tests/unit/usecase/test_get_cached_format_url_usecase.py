"""
GetCachedFormatUrlUseCaseのユニットテスト

GetCachedFormatUrlUseCaseの各機能をテストします。
"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.usecase.query.get_cached_format_url_usecase import (
    GetCachedFormatUrlUseCase,
)


class TestGetCachedFormatUrlUseCase:
    """GetCachedFormatUrlUseCaseのテストクラス"""

    @pytest.fixture
    def mock_cache_repository(self) -> AsyncMock:
        """CacheRepositoryのモックを作成"""
        return AsyncMock()

    @pytest.fixture
    def usecase(self, mock_cache_repository: AsyncMock) -> GetCachedFormatUrlUseCase:
        """GetCachedFormatUrlUseCaseのインスタンスを作成"""
        return GetCachedFormatUrlUseCase(mock_cache_repository)

    @pytest.mark.parametrize(
        "video_id, format_id, cached_value, expected_result",
        [
            pytest.param(
                "dQw4w9WgXcQ",
                "137",
                "https://example.com/format137.mp4",
                "https://example.com/format137.mp4",
                id="正常系: キャッシュヒット時にURLを返す",
            ),
            pytest.param(
                "dQw4w9WgXcQ",
                "248",
                None,
                None,
                id="正常系: キャッシュミス時にNoneを返す",
            ),
        ],
    )
    async def test_execute(
        self,
        usecase: GetCachedFormatUrlUseCase,
        mock_cache_repository: AsyncMock,
        video_id: str,
        format_id: str,
        cached_value: str | None,
        expected_result: str | None,
    ) -> None:
        """キャッシュからフォーマットURLを取得できることをテスト"""
        # Arrange
        mock_cache_repository.get.return_value = cached_value

        # Act
        result = await usecase.execute(video_id, format_id)

        # Assert
        assert result == expected_result
        mock_cache_repository.get.assert_called_once_with(f"format_url:{video_id}:{format_id}")

    async def test_execute_constructs_correct_cache_key(
        self, usecase: GetCachedFormatUrlUseCase, mock_cache_repository: AsyncMock
    ) -> None:
        """キャッシュキーが正しく構築されることをテスト"""
        # Arrange
        video_id = "test_video_id"
        format_id = "test_format_id"
        mock_cache_repository.get.return_value = None

        # Act
        await usecase.execute(video_id, format_id)

        # Assert
        mock_cache_repository.get.assert_called_once_with("format_url:test_video_id:test_format_id")
