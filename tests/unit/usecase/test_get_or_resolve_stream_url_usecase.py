"""
GetOrResolveStreamUrlUseCaseユニットテスト

キャッシュ優先でストリームURLを取得するファサードUseCaseのテストです。
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from streamshuttle.usecase.command.resolve_youtube_url_usecase import (
    ResolveYoutubeUrlUseCase,
)
from streamshuttle.usecase.dto.format_url_dto import FormatUrlDto
from streamshuttle.usecase.facade.get_or_resolve_stream_url_usecase import (
    GetOrResolveStreamUrlUseCase,
)
from streamshuttle.usecase.query.get_cached_format_url_usecase import (
    GetCachedFormatUrlUseCase,
)


def create_format_url_dto(video_id: str, format_id: str, resolved_url: str) -> FormatUrlDto:
    """テスト用のFormatUrlDtoを作成するヘルパー関数"""
    return FormatUrlDto(
        video_id=video_id,
        format_id=format_id,
        resolved_url=resolved_url,
        expiry_at=datetime.now(UTC) + timedelta(hours=1),
    )


@pytest.fixture
def mock_cached_url_use_case():
    """GetCachedFormatUrlUseCaseのモック"""
    return AsyncMock(spec=GetCachedFormatUrlUseCase)


@pytest.fixture
def mock_resolve_use_case():
    """ResolveYoutubeUrlUseCaseのモック"""
    return AsyncMock(spec=ResolveYoutubeUrlUseCase)


class TestGetOrResolveStreamUrlUseCase:
    """GetOrResolveStreamUrlUseCaseのテストクラス"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "url,format_id,cached_dto,resolved_url,expected_result,expected_cache_calls,expected_resolve_calls",
        [
            pytest.param(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "137",
                create_format_url_dto("dQw4w9WgXcQ", "137", "https://cached.example.com/video.mp4"),
                None,
                "https://cached.example.com/video.mp4",
                1,
                0,
                id="正常系: キャッシュヒット時はキャッシュから返す",
            ),
            pytest.param(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "137",
                None,
                "https://resolved.example.com/video.mp4",
                "https://resolved.example.com/video.mp4",
                1,
                1,
                id="正常系: キャッシュミス時はyt-dlpで解決する",
            ),
            pytest.param(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                None,
                None,
                "https://resolved.example.com/video.mp4",
                "https://resolved.example.com/video.mp4",
                0,
                1,
                id="正常系: format_id未指定時はキャッシュ確認をスキップしてyt-dlpで解決する",
            ),
        ],
    )
    async def test_execute(
        self,
        mock_cached_url_use_case,
        mock_resolve_use_case,
        url,
        format_id,
        cached_dto,
        resolved_url,
        expected_result,
        expected_cache_calls,
        expected_resolve_calls,
    ):
        """execute メソッドが正しく動作することを検証"""
        # Arrange
        mock_cached_url_use_case.execute.return_value = cached_dto
        mock_resolve_use_case.execute.return_value = resolved_url

        use_case = GetOrResolveStreamUrlUseCase(
            cached_url_use_case=mock_cached_url_use_case,
            resolve_use_case=mock_resolve_use_case,
        )

        # Act
        result = await use_case.execute(url, format_id)

        # Assert
        assert result == expected_result
        assert mock_cached_url_use_case.execute.call_count == expected_cache_calls
        assert mock_resolve_use_case.execute.call_count == expected_resolve_calls

    @pytest.mark.asyncio
    async def test_execute_cache_hit_with_format_id(
        self, mock_cached_url_use_case, mock_resolve_use_case
    ):
        """format_id指定時にキャッシュヒットした場合、正しいパラメータでキャッシュが呼ばれることを検証"""
        # Arrange
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        format_id = "137"
        cached_url = "https://cached.example.com/video.mp4"
        cached_dto = create_format_url_dto("dQw4w9WgXcQ", format_id, cached_url)
        mock_cached_url_use_case.execute.return_value = cached_dto

        use_case = GetOrResolveStreamUrlUseCase(
            cached_url_use_case=mock_cached_url_use_case,
            resolve_use_case=mock_resolve_use_case,
        )

        # Act
        result = await use_case.execute(url, format_id)

        # Assert
        assert result == cached_url
        mock_cached_url_use_case.execute.assert_called_once_with("dQw4w9WgXcQ", "137")
        mock_resolve_use_case.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_cache_miss_calls_resolve(
        self, mock_cached_url_use_case, mock_resolve_use_case
    ):
        """キャッシュミス時にyt-dlpで解決が呼ばれることを検証"""
        # Arrange
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        format_id = "137"
        resolved_url = "https://resolved.example.com/video.mp4"
        mock_cached_url_use_case.execute.return_value = None
        mock_resolve_use_case.execute.return_value = resolved_url

        use_case = GetOrResolveStreamUrlUseCase(
            cached_url_use_case=mock_cached_url_use_case,
            resolve_use_case=mock_resolve_use_case,
        )

        # Act
        result = await use_case.execute(url, format_id)

        # Assert
        assert result == resolved_url
        mock_cached_url_use_case.execute.assert_called_once_with("dQw4w9WgXcQ", "137")
        mock_resolve_use_case.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_without_format_id_skips_cache(
        self, mock_cached_url_use_case, mock_resolve_use_case
    ):
        """format_id未指定時はキャッシュ確認をスキップすることを検証"""
        # Arrange
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        resolved_url = "https://resolved.example.com/video.mp4"
        mock_resolve_use_case.execute.return_value = resolved_url

        use_case = GetOrResolveStreamUrlUseCase(
            cached_url_use_case=mock_cached_url_use_case,
            resolve_use_case=mock_resolve_use_case,
        )

        # Act
        result = await use_case.execute(url, None)

        # Assert
        assert result == resolved_url
        mock_cached_url_use_case.execute.assert_not_called()
        mock_resolve_use_case.execute.assert_called_once()
