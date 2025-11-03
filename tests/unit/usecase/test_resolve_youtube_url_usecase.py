"""
ResolveYoutubeUrlUseCaseのユニットテスト

ResolveYoutubeUrlUseCaseの各機能をテストします。
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from streamshuttle.shared.exceptions import InvalidVideoIdError
from streamshuttle.usecase.command.resolve_youtube_url_usecase import ResolveYoutubeUrlUseCase
from streamshuttle.usecase.dto.stream_url_dto import StreamUrlDto


class TestResolveYoutubeUrlUseCase:
    """ResolveYoutubeUrlUseCaseのテストクラス"""

    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Repositoryのモックを作成"""
        return AsyncMock()

    @pytest.fixture
    def mock_query_service(self) -> AsyncMock:
        """QueryServiceのモックを作成"""
        return AsyncMock()

    @pytest.fixture
    def mock_youtube_resolver(self) -> AsyncMock:
        """YoutubeResolverのモックを作成"""
        return AsyncMock()

    @pytest.fixture
    def usecase(
        self,
        mock_repository: AsyncMock,
        mock_query_service: AsyncMock,
        mock_youtube_resolver: AsyncMock,
    ) -> ResolveYoutubeUrlUseCase:
        """ResolveYoutubeUrlUseCaseのインスタンスを作成"""
        return ResolveYoutubeUrlUseCase(mock_repository, mock_query_service, mock_youtube_resolver)

    async def test_execute_cache_hit_valid(
        self,
        usecase: ResolveYoutubeUrlUseCase,
        mock_query_service: AsyncMock,
        mock_youtube_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """キャッシュがヒットし有効期限内の場合、キャッシュから返すことをテスト"""
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = "dQw4w9WgXcQ"
        cached_url = "https://example.com/cached-stream.m3u8"
        future_time = datetime.now(UTC) + timedelta(hours=1)

        cached_dto = StreamUrlDto(video_id=video_id, resolved_url=cached_url, expiry_at=future_time)
        mock_query_service.find_by_video_id.return_value = cached_dto

        # Act
        result = await usecase.execute(youtube_url)

        # Assert
        assert result == cached_url
        mock_query_service.find_by_video_id.assert_called_once_with(video_id, False)
        mock_youtube_resolver.resolve_url.assert_not_called()
        mock_repository.save.assert_not_called()

    async def test_execute_cache_miss(
        self,
        usecase: ResolveYoutubeUrlUseCase,
        mock_query_service: AsyncMock,
        mock_youtube_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """キャッシュがない場合、YouTubeから解決して保存することをテスト"""
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = "dQw4w9WgXcQ"
        resolved_url = "https://example.com/new-stream.m3u8"

        mock_query_service.find_by_video_id.return_value = None
        mock_youtube_resolver.resolve_url.return_value = (resolved_url, 3600)

        # Act
        result = await usecase.execute(youtube_url)

        # Assert
        assert result == resolved_url
        mock_query_service.find_by_video_id.assert_called_once_with(video_id, False)
        mock_youtube_resolver.resolve_url.assert_called_once_with(youtube_url, None, False)
        mock_repository.save.assert_called_once()

        # Repositoryに保存されたStreamUrlを検証
        saved_stream_url = mock_repository.save.call_args[0][0]
        assert saved_stream_url.video_id.value == video_id
        assert saved_stream_url.resolved_url.value == resolved_url
        # use_hlsパラメータも検証
        assert mock_repository.save.call_args[0][1] is False

    async def test_execute_cache_expired(
        self,
        usecase: ResolveYoutubeUrlUseCase,
        mock_query_service: AsyncMock,
        mock_youtube_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """キャッシュが期限切れの場合、YouTubeから再解決することをテスト"""
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = "dQw4w9WgXcQ"
        expired_url = "https://example.com/expired-stream.m3u8"
        new_resolved_url = "https://example.com/new-stream.m3u8"
        past_time = datetime.now(UTC) - timedelta(hours=1)

        expired_dto = StreamUrlDto(video_id=video_id, resolved_url=expired_url, expiry_at=past_time)
        mock_query_service.find_by_video_id.return_value = expired_dto
        mock_youtube_resolver.resolve_url.return_value = (new_resolved_url, 3600)

        # Act
        result = await usecase.execute(youtube_url)

        # Assert
        assert result == new_resolved_url
        mock_query_service.find_by_video_id.assert_called_once_with(video_id, False)
        mock_youtube_resolver.resolve_url.assert_called_once_with(youtube_url, None, False)
        mock_repository.save.assert_called_once()

    async def test_extract_video_id_standard_format(
        self, usecase: ResolveYoutubeUrlUseCase
    ) -> None:
        """標準形式のYouTube URLからvideo_idを抽出できることをテスト"""
        # Arrange
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        expected_video_id = "dQw4w9WgXcQ"

        # Act
        result = usecase._extract_video_id(url)

        # Assert
        assert result == expected_video_id

    async def test_extract_video_id_short_format(self, usecase: ResolveYoutubeUrlUseCase) -> None:
        """短縮形式のYouTube URLからvideo_idを抽出できることをテスト"""
        # Arrange
        url = "https://youtu.be/dQw4w9WgXcQ"
        expected_video_id = "dQw4w9WgXcQ"

        # Act
        result = usecase._extract_video_id(url)

        # Assert
        assert result == expected_video_id

    async def test_extract_video_id_embed_format(self, usecase: ResolveYoutubeUrlUseCase) -> None:
        """埋め込み形式のYouTube URLからvideo_idを抽出できることをテスト"""
        # Arrange
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        expected_video_id = "dQw4w9WgXcQ"

        # Act
        result = usecase._extract_video_id(url)

        # Assert
        assert result == expected_video_id

    async def test_extract_video_id_mobile_format(self, usecase: ResolveYoutubeUrlUseCase) -> None:
        """モバイル形式のYouTube URLからvideo_idを抽出できることをテスト"""
        # Arrange
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        expected_video_id = "dQw4w9WgXcQ"

        # Act
        result = usecase._extract_video_id(url)

        # Assert
        assert result == expected_video_id

    async def test_extract_video_id_with_additional_params(
        self, usecase: ResolveYoutubeUrlUseCase
    ) -> None:
        """追加パラメータ付きのURLからvideo_idを抽出できることをテスト"""
        # Arrange
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=share&t=10"
        expected_video_id = "dQw4w9WgXcQ"

        # Act
        result = usecase._extract_video_id(url)

        # Assert
        assert result == expected_video_id

    async def test_extract_video_id_invalid_url(self, usecase: ResolveYoutubeUrlUseCase) -> None:
        """無効なURLの場合、InvalidVideoIdErrorが発生することをテスト"""
        # Arrange
        url = "https://example.com/not-youtube"

        # Act & Assert
        with pytest.raises(InvalidVideoIdError) as exc_info:
            usecase._extract_video_id(url)

        assert "URLからvideo_idを抽出できませんでした" in str(exc_info.value)

    async def test_execute_saves_with_correct_ttl(
        self,
        usecase: ResolveYoutubeUrlUseCase,
        mock_query_service: AsyncMock,
        mock_youtube_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """保存時に正しいTTLが設定されることをテスト"""
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        resolved_url = "https://example.com/stream.m3u8"
        ttl_seconds = 7200

        mock_query_service.find_by_video_id.return_value = None
        mock_youtube_resolver.resolve_url.return_value = (resolved_url, ttl_seconds)

        before_execute = datetime.now(UTC)

        # Act
        await usecase.execute(youtube_url)

        after_execute = datetime.now(UTC)

        # Assert
        saved_stream_url = mock_repository.save.call_args[0][0]
        expiry_at = saved_stream_url.cache_expiry.expiry_at

        # TTLが正しい範囲内であることを確認
        expected_min = before_execute + timedelta(seconds=ttl_seconds)
        expected_max = after_execute + timedelta(seconds=ttl_seconds)

        assert expected_min <= expiry_at <= expected_max

    async def test_execute_with_format_id(
        self,
        usecase: ResolveYoutubeUrlUseCase,
        mock_query_service: AsyncMock,
        mock_youtube_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """format_idが指定された場合、YoutubeResolverに正しく渡されることをテスト"""
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        format_id = "137"
        resolved_url = "https://example.com/stream.mp4"

        mock_query_service.find_by_video_id.return_value = None
        mock_youtube_resolver.resolve_url.return_value = (resolved_url, 3600)

        # Act
        result = await usecase.execute(youtube_url, format_id)

        # Assert
        assert result == resolved_url
        mock_youtube_resolver.resolve_url.assert_called_once_with(youtube_url, format_id, False)
        mock_repository.save.assert_called_once()
