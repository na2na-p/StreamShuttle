"""
ResolveTwitchUrlUseCaseのユニットテスト

ResolveTwitchUrlUseCaseの各機能をテストします。
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from streamshuttle.domain.model.stream_url import StreamUrl
from streamshuttle.domain.model.twitch_url import TwitchUrl
from streamshuttle.usecase.command.resolve_twitch_url_usecase import ResolveTwitchUrlUseCase
from streamshuttle.usecase.dto.resolved_url_result_dto import ResolvedUrlResultDto


class TestResolveTwitchUrlUseCase:
    """ResolveTwitchUrlUseCaseのテストクラス"""

    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Repositoryのモックを作成"""
        return AsyncMock()

    @pytest.fixture
    def mock_twitch_resolver(self) -> AsyncMock:
        """TwitchResolverのモックを作成"""
        return AsyncMock()

    @pytest.fixture
    def usecase(
        self,
        mock_repository: AsyncMock,
        mock_twitch_resolver: AsyncMock,
    ) -> ResolveTwitchUrlUseCase:
        """ResolveTwitchUrlUseCaseのインスタンスを作成"""
        return ResolveTwitchUrlUseCase(mock_repository, mock_twitch_resolver)

    @pytest.mark.asyncio
    async def test_execute_cache_hit_valid(
        self,
        usecase: ResolveTwitchUrlUseCase,
        mock_twitch_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """正常系: キャッシュがヒットし有効期限内の場合、キャッシュから返すことをテスト"""
        # Arrange
        # 可変長のTwitchチャンネル名を使用（11文字以外も可）
        twitch_url = TwitchUrl(_value="https://www.twitch.tv/gamesdonequick")
        video_id = "gamesdonequick"  # 14文字
        cached_url = "https://example.com/cached-stream.m3u8"

        cached_stream_url = StreamUrl.create(
            video_id=video_id,
            resolved_url=cached_url,
            ttl_seconds=3600,
            platform="twitch",
        )
        mock_repository.find_by_video_id.return_value = cached_stream_url

        # Act
        result = await usecase.execute(twitch_url)

        # Assert
        assert result == cached_url
        mock_repository.find_by_video_id.assert_called_once_with(
            video_id, hls=True, platform="twitch"
        )
        mock_twitch_resolver.resolve_url.assert_not_called()
        mock_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_cache_miss(
        self,
        usecase: ResolveTwitchUrlUseCase,
        mock_twitch_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """正常系: キャッシュがない場合、Twitchから解決して保存することをテスト"""
        # Arrange
        twitch_url_str = "https://www.twitch.tv/gamesdonequick"
        twitch_url = TwitchUrl(_value=twitch_url_str)
        video_id = "gamesdonequick"  # 14文字
        resolved_url = "https://example.com/new-stream.m3u8"

        mock_repository.find_by_video_id.return_value = None
        mock_twitch_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=3600
        )

        # Act
        result = await usecase.execute(twitch_url)

        # Assert
        assert result == resolved_url
        mock_repository.find_by_video_id.assert_called_once_with(
            video_id, hls=True, platform="twitch"
        )
        mock_twitch_resolver.resolve_url.assert_called_once_with(twitch_url_str, None)
        mock_repository.save.assert_called_once()

        # Repositoryに保存されたStreamUrlを検証
        saved_stream_url = mock_repository.save.call_args[0][0]
        assert saved_stream_url.video_id.value == video_id
        assert saved_stream_url.resolved_url.value == resolved_url
        # TwitchはHLS形式のみなのでhls=Trueで保存、platform="twitch"で保存
        _, save_kwargs = mock_repository.save.call_args
        assert save_kwargs.get("hls") is True
        assert save_kwargs.get("platform") == "twitch"

    @pytest.mark.asyncio
    async def test_execute_cache_expired(
        self,
        usecase: ResolveTwitchUrlUseCase,
        mock_twitch_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """正常系: キャッシュが期限切れの場合、Twitchから再解決することをテスト"""
        # Arrange
        twitch_url_str = "https://www.twitch.tv/gamesdonequick"
        twitch_url = TwitchUrl(_value=twitch_url_str)
        video_id = "gamesdonequick"  # 14文字
        new_resolved_url = "https://example.com/new-stream.m3u8"

        expired_stream_url = StreamUrl.create(
            video_id=video_id,
            resolved_url="https://example.com/expired-stream.m3u8",
            ttl_seconds=-3600,
            platform="twitch",
        )
        mock_repository.find_by_video_id.return_value = expired_stream_url
        mock_twitch_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=new_resolved_url, ttl_seconds=3600
        )

        # Act
        result = await usecase.execute(twitch_url)

        # Assert
        assert result == new_resolved_url
        mock_repository.find_by_video_id.assert_called_once_with(
            video_id, hls=True, platform="twitch"
        )
        mock_twitch_resolver.resolve_url.assert_called_once_with(twitch_url_str, None)
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_saves_with_correct_ttl(
        self,
        usecase: ResolveTwitchUrlUseCase,
        mock_twitch_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """正常系: 保存時に正しいTTLが設定されることをテスト"""
        # Arrange
        twitch_url = TwitchUrl(_value="https://www.twitch.tv/gamesdonequick")
        resolved_url = "https://example.com/stream.m3u8"
        ttl_seconds = 7200

        mock_repository.find_by_video_id.return_value = None
        mock_twitch_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=ttl_seconds
        )

        before_execute = datetime.now(UTC)

        # Act
        await usecase.execute(twitch_url)

        after_execute = datetime.now(UTC)

        # Assert
        saved_stream_url = mock_repository.save.call_args[0][0]
        expiry_at = saved_stream_url.cache_expiry.expiry_at

        # TTLが正しい範囲内であることを確認
        expected_min = before_execute + timedelta(seconds=ttl_seconds)
        expected_max = after_execute + timedelta(seconds=ttl_seconds)

        assert expected_min <= expiry_at <= expected_max

    @pytest.mark.asyncio
    async def test_execute_with_format_id(
        self,
        usecase: ResolveTwitchUrlUseCase,
        mock_twitch_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """正常系: format_idが指定された場合、TwitchResolverに正しく渡されることをテスト"""
        # Arrange
        twitch_url_str = "https://www.twitch.tv/gamesdonequick"
        twitch_url = TwitchUrl(_value=twitch_url_str)
        format_id = "best"
        resolved_url = "https://example.com/stream.m3u8"

        mock_repository.find_by_video_id.return_value = None
        mock_twitch_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=3600
        )

        # Act
        result = await usecase.execute(twitch_url, format_id)

        # Assert
        assert result == resolved_url
        mock_twitch_resolver.resolve_url.assert_called_once_with(twitch_url_str, format_id)
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_always_uses_hls_for_cache(
        self,
        usecase: ResolveTwitchUrlUseCase,
        mock_twitch_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """正常系: TwitchはHLS形式のみなので、キャッシュ操作で常にhls=Trueを使用することをテスト"""
        # Arrange
        twitch_url = TwitchUrl(_value="https://www.twitch.tv/gamesdonequick")
        resolved_url = "https://example.com/stream.m3u8"

        mock_repository.find_by_video_id.return_value = None
        mock_twitch_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=3600
        )

        # Act
        await usecase.execute(twitch_url)

        # Assert
        # find_by_video_idはhls=True, platform="twitch"で呼ばれる
        mock_repository.find_by_video_id.assert_called_once()
        _, kwargs = mock_repository.find_by_video_id.call_args
        assert kwargs.get("hls") is True
        assert kwargs.get("platform") == "twitch"

        # saveもhls=True, platform="twitch"で呼ばれる
        mock_repository.save.assert_called_once()
        _, save_kwargs = mock_repository.save.call_args
        assert save_kwargs.get("hls") is True
        assert save_kwargs.get("platform") == "twitch"

    @pytest.mark.asyncio
    async def test_execute_with_vod_url(
        self,
        mock_repository: AsyncMock,
        mock_twitch_resolver: AsyncMock,
    ) -> None:
        """正常系: VOD URLからビデオIDが正しく抽出されることをテスト"""
        # Arrange
        # VOD ID: 可変長の数字
        usecase = ResolveTwitchUrlUseCase(mock_repository, mock_twitch_resolver)
        twitch_url_str = "https://www.twitch.tv/videos/1234567890123"
        twitch_url = TwitchUrl(_value=twitch_url_str)
        video_id = "1234567890123"  # 13桁の数字
        resolved_url = "https://example.com/stream.m3u8"

        mock_repository.find_by_video_id.return_value = None
        mock_twitch_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=3600
        )

        # Act
        result = await usecase.execute(twitch_url)

        # Assert
        assert result == resolved_url
        mock_repository.find_by_video_id.assert_called_once_with(
            video_id, hls=True, platform="twitch"
        )
        saved_stream_url = mock_repository.save.call_args[0][0]
        assert saved_stream_url.video_id.value == video_id

    @pytest.mark.asyncio
    async def test_execute_with_clip_url(
        self,
        mock_repository: AsyncMock,
        mock_twitch_resolver: AsyncMock,
    ) -> None:
        """正常系: クリップURLからスラグが正しく抽出されることをテスト"""
        # Arrange
        # クリップスラグ: 可変長
        usecase = ResolveTwitchUrlUseCase(mock_repository, mock_twitch_resolver)
        twitch_url_str = "https://clips.twitch.tv/AwesomeClipSlugHere"
        twitch_url = TwitchUrl(_value=twitch_url_str)
        video_id = "AwesomeClipSlugHere"  # 19文字
        resolved_url = "https://example.com/stream.m3u8"

        mock_repository.find_by_video_id.return_value = None
        mock_twitch_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=3600
        )

        # Act
        result = await usecase.execute(twitch_url)

        # Assert
        assert result == resolved_url
        mock_repository.find_by_video_id.assert_called_once_with(
            video_id, hls=True, platform="twitch"
        )
        saved_stream_url = mock_repository.save.call_args[0][0]
        assert saved_stream_url.video_id.value == video_id

    @pytest.mark.asyncio
    async def test_execute_returns_cached_url_without_resolving(
        self,
        usecase: ResolveTwitchUrlUseCase,
        mock_twitch_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """正常系: 有効なキャッシュがある場合、resolverを呼び出さないことをテスト"""
        # Arrange
        twitch_url = TwitchUrl(_value="https://www.twitch.tv/gamesdonequick")
        cached_url = "https://example.com/cached.m3u8"

        mock_cached = MagicMock()
        mock_cached.is_expired.return_value = False
        mock_cached.resolved_url.value = cached_url
        mock_repository.find_by_video_id.return_value = mock_cached

        # Act
        result = await usecase.execute(twitch_url)

        # Assert
        assert result == cached_url
        mock_twitch_resolver.resolve_url.assert_not_called()
        mock_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_short_channel_name(
        self,
        usecase: ResolveTwitchUrlUseCase,
        mock_twitch_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """正常系: 短いチャンネル名（4文字）で正しく動作することをテスト"""
        # Arrange
        twitch_url_str = "https://www.twitch.tv/riot"
        twitch_url = TwitchUrl(_value=twitch_url_str)
        video_id = "riot"  # 4文字
        resolved_url = "https://example.com/stream.m3u8"

        mock_repository.find_by_video_id.return_value = None
        mock_twitch_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=3600
        )

        # Act
        result = await usecase.execute(twitch_url)

        # Assert
        assert result == resolved_url
        mock_repository.find_by_video_id.assert_called_once_with(
            video_id, hls=True, platform="twitch"
        )

    @pytest.mark.asyncio
    async def test_execute_with_long_channel_name(
        self,
        usecase: ResolveTwitchUrlUseCase,
        mock_twitch_resolver: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """正常系: 長いチャンネル名（25文字）で正しく動作することをテスト"""
        # Arrange
        twitch_url_str = "https://www.twitch.tv/averylongchannelnameeee"
        twitch_url = TwitchUrl(_value=twitch_url_str)
        video_id = "averylongchannelnameeee"  # 23文字
        resolved_url = "https://example.com/stream.m3u8"

        mock_repository.find_by_video_id.return_value = None
        mock_twitch_resolver.resolve_url.return_value = ResolvedUrlResultDto(
            resolved_url=resolved_url, ttl_seconds=3600
        )

        # Act
        result = await usecase.execute(twitch_url)

        # Assert
        assert result == resolved_url
        mock_repository.find_by_video_id.assert_called_once_with(
            video_id, hls=True, platform="twitch"
        )
