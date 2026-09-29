"""
ResolveYoutubeUrlUseCaseのユニットテスト

ResolveYoutubeUrlUseCaseの各機能をテストします。
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from streamshuttle.domain.model.stream_url import StreamUrl
from streamshuttle.domain.model.youtube_url import YoutubeUrl
from streamshuttle.usecase.command.resolve_youtube_url_usecase import ResolveYoutubeUrlUseCase
from streamshuttle.usecase.dto.resolved_url_result_dto import ResolvedUrlResultDto


class TestResolveYoutubeUrlUseCase:
    """ResolveYoutubeUrlUseCaseのテストクラス"""

    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Repositoryのモックを作成"""
        return AsyncMock()

    @pytest.fixture
    def mock_youtube_resolver(self) -> AsyncMock:
        """YoutubeResolverのモックを作成"""
        return AsyncMock()

    @pytest.fixture
    def usecase(
        self,
        mock_repository: AsyncMock,
        mock_youtube_resolver: AsyncMock,
    ) -> ResolveYoutubeUrlUseCase:
        """ResolveYoutubeUrlUseCaseのインスタンスを作成"""
        return ResolveYoutubeUrlUseCase(mock_repository, mock_youtube_resolver)

    async def test_execute_cache_hit_valid(
        self,
        usecase: ResolveYoutubeUrlUseCase,
        mock_youtube_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """キャッシュがヒットし有効期限内の場合、キャッシュから返すことをテスト"""
        # Arrange
        youtube_url = YoutubeUrl(_value="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        video_id = "dQw4w9WgXcQ"
        cached_url = "https://example.com/cached-stream.m3u8"

        cached_stream_url = StreamUrl.create(
            video_id=video_id,
            resolved_url=cached_url,
            ttl_seconds=3600,
        )
        mock_repository.find_by_video_id.return_value = cached_stream_url

        # Act
        result = await usecase.execute(youtube_url)

        # Assert
        assert result == cached_url
        mock_repository.find_by_video_id.assert_called_once_with(video_id, False)
        mock_youtube_resolver.resolve_url.assert_not_called()
        mock_repository.save.assert_not_called()

    async def test_execute_cache_miss(
        self,
        usecase: ResolveYoutubeUrlUseCase,
        mock_youtube_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """キャッシュがない場合、YouTubeから解決して保存することをテスト"""
        # Arrange
        youtube_url_str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        youtube_url = YoutubeUrl(_value=youtube_url_str)
        video_id = "dQw4w9WgXcQ"
        resolved_url = "https://example.com/new-stream.m3u8"

        mock_repository.find_by_video_id.return_value = None
        mock_youtube_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=3600
        )

        # Act
        result = await usecase.execute(youtube_url)

        # Assert
        assert result == resolved_url
        mock_repository.find_by_video_id.assert_called_once_with(video_id, False)
        mock_youtube_resolver.resolve_url.assert_called_once_with(youtube_url_str, None, False)
        mock_repository.save.assert_called_once()

        # Repositoryに保存されたStreamUrlを検証
        saved_stream_url = mock_repository.save.call_args[0][0]
        assert saved_stream_url.video_id.value == video_id
        assert saved_stream_url.resolved_url.value == resolved_url
        # hlsパラメータも検証
        assert mock_repository.save.call_args[0][1] is False

    async def test_execute_cache_expired(
        self,
        usecase: ResolveYoutubeUrlUseCase,
        mock_youtube_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """キャッシュが期限切れの場合、YouTubeから再解決することをテスト"""
        # Arrange
        youtube_url_str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        youtube_url = YoutubeUrl(_value=youtube_url_str)
        video_id = "dQw4w9WgXcQ"
        new_resolved_url = "https://example.com/new-stream.m3u8"

        expired_stream_url = StreamUrl.create(
            video_id=video_id,
            resolved_url="https://example.com/expired-stream.m3u8",
            ttl_seconds=-3600,
        )
        mock_repository.find_by_video_id.return_value = expired_stream_url
        mock_youtube_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=new_resolved_url, ttl_seconds=3600
        )

        # Act
        result = await usecase.execute(youtube_url)

        # Assert
        assert result == new_resolved_url
        mock_repository.find_by_video_id.assert_called_once_with(video_id, False)
        mock_youtube_resolver.resolve_url.assert_called_once_with(youtube_url_str, None, False)
        mock_repository.save.assert_called_once()

    async def test_execute_saves_with_correct_ttl(
        self,
        usecase: ResolveYoutubeUrlUseCase,
        mock_youtube_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """保存時に正しいTTLが設定されることをテスト"""
        # Arrange
        youtube_url = YoutubeUrl(_value="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        resolved_url = "https://example.com/stream.m3u8"
        ttl_seconds = 7200

        mock_repository.find_by_video_id.return_value = None
        mock_youtube_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=ttl_seconds
        )

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
        mock_youtube_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """format_idが指定された場合、キャッシュを使わずYoutubeResolverで解決することをテスト"""
        # Arrange
        youtube_url_str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        youtube_url = YoutubeUrl(_value=youtube_url_str)
        format_id = "137"
        resolved_url = "https://example.com/stream.mp4"

        mock_youtube_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=3600
        )

        # Act
        result = await usecase.execute(youtube_url, format_id)

        # Assert
        assert result == resolved_url
        mock_youtube_resolver.resolve_url.assert_called_once_with(youtube_url_str, format_id, False)
        mock_repository.find_by_video_id.assert_not_called()
        mock_repository.save.assert_not_called()

    @pytest.mark.parametrize(
        "format_id, hls, has_valid_cache, expect_cache_used",
        [
            pytest.param(
                "137",
                False,
                True,
                False,
                id="正常系: format_id指定時は有効なキャッシュがあってもresolverで解決する",
            ),
            pytest.param(
                "137",
                True,
                False,
                False,
                id="正常系: format_id指定かつhls=Trueでもキャッシュを使わない",
            ),
            pytest.param(
                None,
                False,
                False,
                True,
                id="正常系: format_id未指定時は従来どおりキャッシュを読み書きする",
            ),
        ],
    )
    async def test_execute_stream_url_cache_usage_by_format_id(
        self,
        usecase: ResolveYoutubeUrlUseCase,
        mock_youtube_resolver: AsyncMock,
        mock_repository: AsyncMock,
        format_id: str | None,
        hls: bool,
        has_valid_cache: bool,
        expect_cache_used: bool,
    ) -> None:
        """format_idの有無によりストリームURLキャッシュの読み書きが切り替わることをテスト"""
        # Arrange
        youtube_url_str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        youtube_url = YoutubeUrl(_value=youtube_url_str)
        video_id = "dQw4w9WgXcQ"
        resolved_url = "https://example.com/resolved.mp4"

        if has_valid_cache:
            mock_repository.find_by_video_id.return_value = StreamUrl.create(
                video_id=video_id,
                resolved_url="https://example.com/cached-stream.m3u8",
                ttl_seconds=3600,
            )
        else:
            mock_repository.find_by_video_id.return_value = None
        mock_youtube_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=3600
        )

        # Act
        result = await usecase.execute(youtube_url, format_id, hls)

        # Assert
        assert result == resolved_url
        mock_youtube_resolver.resolve_url.assert_called_once_with(youtube_url_str, format_id, hls)
        if expect_cache_used:
            mock_repository.find_by_video_id.assert_called_once_with(video_id, hls)
            mock_repository.save.assert_called_once()
        else:
            mock_repository.find_by_video_id.assert_not_called()
            mock_repository.save.assert_not_called()
