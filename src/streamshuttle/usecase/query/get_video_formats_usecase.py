"""
ビデオフォーマット一覧取得UseCaseモジュール

YouTube動画の利用可能なフォーマット一覧を取得するUseCaseを定義します。
"""

import logging

from streamshuttle.domain.repository.cache_repository import CacheRepository
from streamshuttle.shared.exceptions import CacheError
from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto
from streamshuttle.usecase.query_service.video_format_query_service import VideoFormatQueryService

logger = logging.getLogger(__name__)


class GetVideoFormatsUseCase:
    """
    ビデオフォーマット一覧取得UseCase

    YouTube動画URLから利用可能なフォーマット一覧を取得し、
    各フォーマットのURLをキャッシュに保存します。
    """

    def __init__(
        self, query_service: VideoFormatQueryService, cache_repository: CacheRepository
    ) -> None:
        """
        GetVideoFormatsUseCaseを初期化します

        Args:
            query_service: VideoFormat参照用QueryService
            cache_repository: Cache Repository
        """
        self._query_service = query_service
        self._cache_repository = cache_repository

    async def execute(self, youtube_url: str) -> tuple[VideoInfoDto, list[VideoFormatDto]]:
        """
        YouTube動画URLから利用可能なフォーマット一覧と動画情報を取得し、キャッシュに保存します

        Args:
            youtube_url: YouTube動画URL（https://www.youtube.com/watch?v=xxxxx形式）

        Returns:
            tuple[VideoInfoDto, list[VideoFormatDto]]: 動画情報とフォーマット情報のリスト

        Raises:
            YouTubeResolverException: YouTube APIへのアクセスまたはURL解決に失敗した場合
            InvalidUrlException: 無効なURLが指定された場合
        """
        video_info, formats = await self._query_service.get_available_formats(youtube_url)

        # フォーマットURLをキャッシュに保存
        if formats:
            video_id = video_info.video_id
            for format_dto in formats:
                cache_key = f"format_url:{video_id}:{format_dto.format_id}"
                try:
                    await self._cache_repository.set(
                        key=cache_key,
                        value=format_dto.url,
                        ttl=3600,
                    )
                except CacheError as e:
                    logger.warning(f"Failed to cache format URL: {cache_key}, error={e}")

        return video_info, formats
