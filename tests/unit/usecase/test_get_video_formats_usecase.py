"""
GetVideoFormatsUseCaseのユニットテスト

GetVideoFormatsUseCaseの各機能をテストします。
"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.query.get_video_formats_usecase import GetVideoFormatsUseCase


class TestGetVideoFormatsUseCase:
    """GetVideoFormatsUseCaseのテストクラス"""

    @pytest.fixture
    def mock_query_service(self) -> AsyncMock:
        """QueryServiceのモックを作成"""
        return AsyncMock()

    @pytest.fixture
    def usecase(self, mock_query_service: AsyncMock) -> GetVideoFormatsUseCase:
        """GetVideoFormatsUseCaseのインスタンスを作成"""
        return GetVideoFormatsUseCase(mock_query_service)

    async def test_execute_returns_formats(
        self, usecase: GetVideoFormatsUseCase, mock_query_service: AsyncMock
    ) -> None:
        """フォーマット一覧を取得できることをテスト"""
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        expected_formats = [
            VideoFormatDto(
                format_id="137",
                quality="1080p",
                codec="avc1",
                url="https://example.com/format137.mp4",
                has_audio=False,
                has_video=True,
            ),
            VideoFormatDto(
                format_id="248",
                quality="1080p",
                codec="vp9",
                url="https://example.com/format248.webm",
                has_audio=False,
                has_video=True,
            ),
            VideoFormatDto(
                format_id="136",
                quality="720p",
                codec="avc1",
                url="https://example.com/format136.mp4",
                has_audio=False,
                has_video=True,
            ),
        ]
        mock_query_service.get_available_formats.return_value = expected_formats

        # Act
        result = await usecase.execute(youtube_url)

        # Assert
        assert result == expected_formats
        mock_query_service.get_available_formats.assert_called_once_with(youtube_url)

    async def test_execute_returns_empty_list(
        self, usecase: GetVideoFormatsUseCase, mock_query_service: AsyncMock
    ) -> None:
        """フォーマットが見つからない場合、空のリストを返すことをテスト"""
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        mock_query_service.get_available_formats.return_value = []

        # Act
        result = await usecase.execute(youtube_url)

        # Assert
        assert result == []
        mock_query_service.get_available_formats.assert_called_once_with(youtube_url)

    async def test_execute_calls_query_service_correctly(
        self, usecase: GetVideoFormatsUseCase, mock_query_service: AsyncMock
    ) -> None:
        """QueryServiceが正しく呼び出されることをテスト"""
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=test_video"
        mock_query_service.get_available_formats.return_value = []

        # Act
        await usecase.execute(youtube_url)

        # Assert
        mock_query_service.get_available_formats.assert_called_once_with(youtube_url)

    async def test_execute_with_different_url_format(
        self, usecase: GetVideoFormatsUseCase, mock_query_service: AsyncMock
    ) -> None:
        """異なるURL形式でも正しく動作することをテスト"""
        # Arrange
        youtube_url = "https://youtu.be/dQw4w9WgXcQ"
        expected_formats = [
            VideoFormatDto(
                format_id="22",
                quality="720p",
                codec="avc1",
                url="https://example.com/format22.mp4",
                has_audio=False,
                has_video=True,
            ),
        ]
        mock_query_service.get_available_formats.return_value = expected_formats

        # Act
        result = await usecase.execute(youtube_url)

        # Assert
        assert result == expected_formats
        mock_query_service.get_available_formats.assert_called_once_with(youtube_url)
