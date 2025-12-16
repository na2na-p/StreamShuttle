"""
GetVideoFormatsUseCaseのユニットテスト

GetVideoFormatsUseCaseの各機能をテストします。
"""

from unittest.mock import AsyncMock

import pytest

from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto
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
        self,
        usecase: GetVideoFormatsUseCase,
        mock_query_service: AsyncMock,
    ) -> None:
        """フォーマット一覧を取得することをテスト（CQRS準拠: 参照のみ）"""
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        expected_video_info = VideoInfoDto(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            thumbnail_url="https://example.com/thumb.jpg",
        )
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
        mock_query_service.get_available_formats.return_value = (
            expected_video_info,
            expected_formats,
        )

        # Act
        video_info, formats = await usecase.execute(youtube_url)

        # Assert
        assert video_info == expected_video_info
        assert formats == expected_formats
        mock_query_service.get_available_formats.assert_called_once_with(youtube_url)

    async def test_execute_returns_empty_list(
        self,
        usecase: GetVideoFormatsUseCase,
        mock_query_service: AsyncMock,
    ) -> None:
        """
        フォーマットが見つからない場合、空のリストを返すことをテスト（CQRS準拠: 参照のみ）
        """
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        expected_video_info = VideoInfoDto(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            thumbnail_url="https://example.com/thumb.jpg",
        )
        mock_query_service.get_available_formats.return_value = (expected_video_info, [])

        # Act
        video_info, formats = await usecase.execute(youtube_url)

        # Assert
        assert video_info == expected_video_info
        assert formats == []
        mock_query_service.get_available_formats.assert_called_once_with(youtube_url)

    async def test_execute_calls_query_service_correctly(
        self,
        usecase: GetVideoFormatsUseCase,
        mock_query_service: AsyncMock,
    ) -> None:
        """QueryServiceが正しく呼び出されることをテスト"""
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=test_video"
        expected_video_info = VideoInfoDto(
            video_id="test_video", title="Test Video", thumbnail_url="https://example.com/thumb.jpg"
        )
        mock_query_service.get_available_formats.return_value = (expected_video_info, [])

        # Act
        await usecase.execute(youtube_url)

        # Assert
        mock_query_service.get_available_formats.assert_called_once_with(youtube_url)

    async def test_execute_with_different_url_format(
        self,
        usecase: GetVideoFormatsUseCase,
        mock_query_service: AsyncMock,
    ) -> None:
        """異なるURL形式でも正しく動作することをテスト（CQRS準拠: 参照のみ）"""
        # Arrange
        youtube_url = "https://youtu.be/dQw4w9WgXcQ"
        expected_video_info = VideoInfoDto(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            thumbnail_url="https://example.com/thumb.jpg",
        )
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
        mock_query_service.get_available_formats.return_value = (
            expected_video_info,
            expected_formats,
        )

        # Act
        video_info, formats = await usecase.execute(youtube_url)

        # Assert
        assert video_info == expected_video_info
        assert formats == expected_formats
        mock_query_service.get_available_formats.assert_called_once_with(youtube_url)
