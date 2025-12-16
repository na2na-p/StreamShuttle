"""
キャッシュされたフォーマットURLを取得するUseCaseモジュール

キャッシュから特定のフォーマットURLを取得します。
"""

from streamshuttle.domain.repository.cache_repository import CacheRepository


class GetCachedFormatUrlUseCase:
    """
    キャッシュされたフォーマットURLを取得するUseCase

    指定されたvideo_idとformat_idに対応するフォーマットURLを
    キャッシュから取得します。
    """

    def __init__(self, cache_repository: CacheRepository) -> None:
        """
        GetCachedFormatUrlUseCaseを初期化します

        Args:
            cache_repository: Cache Repository
        """
        self._cache_repository = cache_repository

    async def execute(self, video_id: str, format_id: str) -> str | None:
        """
        キャッシュからフォーマットURLを取得する

        Args:
            video_id: YouTube動画ID
            format_id: フォーマットID

        Returns:
            str | None: キャッシュされたURL。存在しない場合はNone
        """
        cache_key = f"format_url:{video_id}:{format_id}"
        cached_url = await self._cache_repository.get(cache_key)
        return cached_url
