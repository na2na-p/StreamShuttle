"""
DIコンテナモジュール

依存性注入のためのファクトリー関数を提供します。
インスタンスのライフサイクルを管理し、アプリケーション全体で一貫した依存関係を提供します。
"""

from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.infrastructure.external.youtube_resolver import YoutubeResolver
from streamshuttle.infrastructure.query_service.stream_url_query_service import (
    StreamUrlQueryService,
)
from streamshuttle.infrastructure.query_service.video_format_query_service import (
    VideoFormatQueryService,
)
from streamshuttle.infrastructure.repository.redis_cache_repository import (
    RedisCacheRepository,
)
from streamshuttle.infrastructure.repository.stream_url_repository import (
    StreamUrlRepository,
)
from streamshuttle.shared.config import config
from streamshuttle.usecase.command.resolve_youtube_url_usecase import (
    ResolveYoutubeUrlUseCase,
)
from streamshuttle.usecase.facade.get_or_resolve_stream_url_usecase import (
    GetOrResolveStreamUrlUseCase,
)
from streamshuttle.usecase.query.get_cached_format_url_usecase import (
    GetCachedFormatUrlUseCase,
)
from streamshuttle.usecase.query.get_cached_stream_url_usecase import (
    GetCachedStreamUrlUseCase,
)
from streamshuttle.usecase.query.get_video_formats_usecase import GetVideoFormatsUseCase

# グローバルインスタンス（シングルトン）
_redis_dao: RedisDao | None = None


def get_redis_dao() -> RedisDao:
    """
    RedisDaoのシングルトンインスタンスを取得

    アプリケーション全体で単一のRedis接続プールを共有します。
    初回呼び出し時にインスタンスを作成し、以降は同じインスタンスを返します。

    Returns:
        RedisDao: 初期化済みのRedisDaoインスタンス
    """
    global _redis_dao
    if _redis_dao is None:
        _redis_dao = RedisDao(host=config.redis.host, port=config.redis.port, db=config.redis.db)
    return _redis_dao


def get_cache_repository() -> RedisCacheRepository:
    """
    CacheRepositoryインスタンスを生成

    CacheRepositoryに必要なRedisDaoを注入して生成します。

    Returns:
        RedisCacheRepository: 初期化済みのCacheRepositoryインスタンス
    """
    return RedisCacheRepository(redis_dao=get_redis_dao())


def get_stream_url_repository() -> StreamUrlRepository:
    """
    StreamUrlRepositoryインスタンスを生成

    StreamUrlRepositoryに必要なRedisDaoを注入して生成します。

    Returns:
        StreamUrlRepository: 初期化済みのRepositoryインスタンス
    """
    return StreamUrlRepository(redis_dao=get_redis_dao())


def get_stream_url_query_service() -> StreamUrlQueryService:
    """
    StreamUrlQueryServiceインスタンスを生成

    StreamUrlQueryServiceに必要なRedisDaoを注入して生成します。

    Returns:
        StreamUrlQueryService: 初期化済みのQueryServiceインスタンス
    """
    return StreamUrlQueryService(redis_dao=get_redis_dao())


def get_video_format_query_service() -> VideoFormatQueryService:
    """
    VideoFormatQueryServiceインスタンスを生成

    VideoFormatQueryServiceは依存関係がないため、単純に新規インスタンスを生成します。

    Returns:
        VideoFormatQueryService: 初期化済みのQueryServiceインスタンス
    """
    return VideoFormatQueryService()


def get_youtube_resolver() -> YoutubeResolver:
    """
    YoutubeResolverインスタンスを生成

    YoutubeResolverは依存関係がないため、単純に新規インスタンスを生成します。

    Returns:
        YoutubeResolver: 初期化済みのYoutubeResolverインスタンス
    """
    return YoutubeResolver()


def get_resolve_youtube_url_use_case() -> ResolveYoutubeUrlUseCase:
    """
    ResolveYoutubeUrlUseCaseインスタンスを生成

    必要な依存関係をすべて注入して生成します。

    Returns:
        ResolveYoutubeUrlUseCase: 初期化済みのUseCaseインスタンス
    """
    return ResolveYoutubeUrlUseCase(
        repository=get_stream_url_repository(),
        query_service=get_stream_url_query_service(),
        youtube_resolver=get_youtube_resolver(),
    )


def get_cached_stream_url_use_case() -> GetCachedStreamUrlUseCase:
    """
    GetCachedStreamUrlUseCaseインスタンスを生成

    必要な依存関係を注入して生成します。

    Returns:
        GetCachedStreamUrlUseCase: 初期化済みのUseCaseインスタンス
    """
    return GetCachedStreamUrlUseCase(query_service=get_stream_url_query_service())


def get_video_formats_use_case() -> GetVideoFormatsUseCase:
    """
    GetVideoFormatsUseCaseインスタンスを生成

    必要な依存関係を注入して生成します。

    Returns:
        GetVideoFormatsUseCase: 初期化済みのUseCaseインスタンス
    """
    return GetVideoFormatsUseCase(query_service=get_video_format_query_service())


def get_cached_format_url_use_case() -> GetCachedFormatUrlUseCase:
    """
    GetCachedFormatUrlUseCaseインスタンスを生成

    必要な依存関係を注入して生成します。

    Returns:
        GetCachedFormatUrlUseCase: 初期化済みのUseCaseインスタンス
    """
    return GetCachedFormatUrlUseCase(cache_repository=get_cache_repository())


def get_or_resolve_stream_url_use_case() -> GetOrResolveStreamUrlUseCase:
    """
    GetOrResolveStreamUrlUseCaseインスタンスを生成

    キャッシュ取得とyt-dlp解決を統合したファサードUseCaseを生成します。

    Returns:
        GetOrResolveStreamUrlUseCase: 初期化済みのUseCaseインスタンス
    """
    return GetOrResolveStreamUrlUseCase(
        cached_url_use_case=get_cached_format_url_use_case(),
        resolve_use_case=get_resolve_youtube_url_use_case(),
    )
