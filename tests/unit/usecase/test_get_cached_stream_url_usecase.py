"""
GetCachedStreamUrlUseCaseのユニットテスト

GetCachedStreamUrlUseCaseの各機能をテストします。
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from streamshuttle.usecase.dto.stream_url_dto import StreamUrlDto
from streamshuttle.usecase.query.get_cached_stream_url_usecase import GetCachedStreamUrlUseCase


class TestGetCachedStreamUrlUseCase:
    """GetCachedStreamUrlUseCaseのテストクラス"""

    @pytest.fixture
    def mock_query_service(self) -> AsyncMock:
        """QueryServiceのモックを作成"""
        return AsyncMock()

    @pytest.fixture
    def usecase(self, mock_query_service: AsyncMock) -> GetCachedStreamUrlUseCase:
        """GetCachedStreamUrlUseCaseのインスタンスを作成"""
        return GetCachedStreamUrlUseCase(mock_query_service)

    async def test_execute_cache_exists(
        self, usecase: GetCachedStreamUrlUseCase, mock_query_service: AsyncMock
    ) -> None:
        """キャッシュが存在する場合、StreamUrlDtoを返すことをテスト"""
        # Arrange
        video_id = "dQw4w9WgXcQ"
        resolved_url = "https://example.com/stream.m3u8"
        expiry_at = datetime.now(UTC) + timedelta(hours=1)

        expected_dto = StreamUrlDto(
            video_id=video_id, resolved_url=resolved_url, expiry_at=expiry_at
        )
        mock_query_service.find_by_video_id.return_value = expected_dto

        # Act
        result = await usecase.execute(video_id)

        # Assert
        assert result == expected_dto
        mock_query_service.find_by_video_id.assert_called_once_with(video_id)

    async def test_execute_cache_not_exists(
        self, usecase: GetCachedStreamUrlUseCase, mock_query_service: AsyncMock
    ) -> None:
        """キャッシュが存在しない場合、Noneを返すことをテスト"""
        # Arrange
        video_id = "dQw4w9WgXcQ"
        mock_query_service.find_by_video_id.return_value = None

        # Act
        result = await usecase.execute(video_id)

        # Assert
        assert result is None
        mock_query_service.find_by_video_id.assert_called_once_with(video_id)

    async def test_execute_expired_cache(
        self, usecase: GetCachedStreamUrlUseCase, mock_query_service: AsyncMock
    ) -> None:
        """期限切れのキャッシュも取得できることをテスト（期限チェックは呼び出し側で行う）"""
        # Arrange
        video_id = "dQw4w9WgXcQ"
        resolved_url = "https://example.com/expired-stream.m3u8"
        expiry_at = datetime.now(UTC) - timedelta(hours=1)

        expired_dto = StreamUrlDto(
            video_id=video_id, resolved_url=resolved_url, expiry_at=expiry_at
        )
        mock_query_service.find_by_video_id.return_value = expired_dto

        # Act
        result = await usecase.execute(video_id)

        # Assert
        assert result == expired_dto
        mock_query_service.find_by_video_id.assert_called_once_with(video_id)

    async def test_execute_calls_query_service_correctly(
        self, usecase: GetCachedStreamUrlUseCase, mock_query_service: AsyncMock
    ) -> None:
        """QueryServiceが正しく呼び出されることをテスト"""
        # Arrange
        video_id = "test_video_id"
        mock_query_service.find_by_video_id.return_value = None

        # Act
        await usecase.execute(video_id)

        # Assert
        mock_query_service.find_by_video_id.assert_called_once_with(video_id)
