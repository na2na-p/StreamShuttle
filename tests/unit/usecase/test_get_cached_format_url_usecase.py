"""
GetCachedFormatUrlUseCaseのユニットテスト

GetCachedFormatUrlUseCaseの各機能をテストします。
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from streamshuttle.usecase.dto.format_url_dto import FormatUrlDto
from streamshuttle.usecase.query.get_cached_format_url_usecase import (
    GetCachedFormatUrlUseCase,
)


class TestGetCachedFormatUrlUseCase:
    """GetCachedFormatUrlUseCaseのテストクラス"""

    @pytest.fixture
    def mock_query_service(self) -> AsyncMock:
        """FormatUrlQueryServiceのモックを作成"""
        return AsyncMock()

    @pytest.fixture
    def usecase(self, mock_query_service: AsyncMock) -> GetCachedFormatUrlUseCase:
        """GetCachedFormatUrlUseCaseのインスタンスを作成"""
        return GetCachedFormatUrlUseCase(mock_query_service)

    @pytest.mark.parametrize(
        "video_id, format_id, cached_dto, expected_result_url",
        [
            pytest.param(
                "dQw4w9WgXcQ",
                "137",
                FormatUrlDto(
                    video_id="dQw4w9WgXcQ",
                    format_id="137",
                    resolved_url="https://example.com/format137.mp4",
                    expiry_at=datetime.now(UTC) + timedelta(hours=1),
                ),
                "https://example.com/format137.mp4",
                id="正常系: キャッシュヒット時にFormatUrlDtoを返す",
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
        mock_query_service: AsyncMock,
        video_id: str,
        format_id: str,
        cached_dto: FormatUrlDto | None,
        expected_result_url: str | None,
    ) -> None:
        """キャッシュからフォーマットURLを取得できることをテスト"""
        # Arrange
        mock_query_service.find_by_video_and_format_id.return_value = cached_dto

        # Act
        result = await usecase.execute(video_id, format_id)

        # Assert
        if expected_result_url is None:
            assert result is None
        else:
            assert result is not None
            assert result.resolved_url == expected_result_url
        mock_query_service.find_by_video_and_format_id.assert_called_once_with(video_id, format_id)

    async def test_execute_calls_query_service_with_correct_params(
        self, usecase: GetCachedFormatUrlUseCase, mock_query_service: AsyncMock
    ) -> None:
        """QueryServiceが正しいパラメータで呼び出されることをテスト"""
        # Arrange
        video_id = "test_video_id"
        format_id = "test_format_id"
        mock_query_service.find_by_video_and_format_id.return_value = None

        # Act
        await usecase.execute(video_id, format_id)

        # Assert
        mock_query_service.find_by_video_and_format_id.assert_called_once_with(video_id, format_id)
