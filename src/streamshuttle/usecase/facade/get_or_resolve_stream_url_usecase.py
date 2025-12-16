"""
キャッシュ優先ストリームURL取得UseCaseモジュール

キャッシュからの取得とyt-dlpによる解決を統合したファサードUseCaseを定義します。
"""

import logging
from dataclasses import dataclass

from streamshuttle.domain.model.youtube_url import YoutubeUrl
from streamshuttle.shared.exceptions import InvalidUrlError, InvalidVideoIdError
from streamshuttle.usecase.command.resolve_youtube_url_usecase import (
    ResolveYoutubeUrlUseCase,
)
from streamshuttle.usecase.query.get_cached_format_url_usecase import (
    GetCachedFormatUrlUseCase,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GetOrResolveStreamUrlUseCase:
    """キャッシュ優先でストリームURLを取得するUseCase

    format_idが指定されている場合はキャッシュを確認し、
    キャッシュミスの場合はyt-dlpで解決します。
    format_idが未指定の場合はキャッシュ確認をスキップして直接yt-dlpで解決します。
    """

    cached_url_use_case: GetCachedFormatUrlUseCase
    resolve_use_case: ResolveYoutubeUrlUseCase

    async def execute(self, url: str, format_id: str | None = None) -> str:
        """
        キャッシュを優先しつつ、ミス時にはyt-dlpで解決してURLを取得

        Args:
            url: YouTube URL
            format_id: フォーマットID（指定時はキャッシュを確認）

        Returns:
            str: 解決済みストリームURL

        Raises:
            InvalidUrlError: URLが無効な形式の場合
            InvalidVideoIdError: video_idの抽出に失敗した場合
            YouTubeResolverError: YouTube APIへのアクセスに失敗した場合
        """
        if format_id:
            youtube_url = YoutubeUrl(_value=url)
            video_id = youtube_url.extract_video_id()

            try:
                cached_url = await self.cached_url_use_case.execute(str(video_id), format_id)
                if cached_url:
                    logger.info(
                        f"Using cached URL for format: "
                        f"video_id={str(video_id)}, format_id={format_id}"
                    )
                    return cached_url
            except (InvalidUrlError, InvalidVideoIdError) as e:
                logger.warning(
                    f"Failed to get cached URL: url={url}, format_id={format_id}, error={e}"
                )

        logger.info(f"Cache miss, resolving URL with yt-dlp: url={url}, format_id={format_id}")
        youtube_url_for_resolve = YoutubeUrl(_value=url)
        return await self.resolve_use_case.execute(youtube_url_for_resolve, format_id)
