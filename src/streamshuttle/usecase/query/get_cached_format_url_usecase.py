"""
キャッシュされたフォーマットURLを取得するUseCaseモジュール

QueryServiceを通じてキャッシュから特定のフォーマットURL情報を取得します。
"""

from streamshuttle.usecase.dto.format_url_dto import FormatUrlDto
from streamshuttle.usecase.query_service.format_url_query_service import (
    FormatUrlQueryService,
)


class GetCachedFormatUrlUseCase:
    """
    キャッシュされたフォーマットURLを取得するUseCase

    指定されたvideo_idとformat_idに対応するフォーマットURL情報を
    QueryServiceを通じてキャッシュから取得します。
    """

    def __init__(self, query_service: FormatUrlQueryService) -> None:
        """
        GetCachedFormatUrlUseCaseを初期化します

        Args:
            query_service: FormatUrl QueryService
        """
        self._query_service = query_service

    async def execute(self, video_id: str, format_id: str) -> FormatUrlDto | None:
        """
        キャッシュからフォーマットURL情報を取得する

        Args:
            video_id: YouTube動画ID
            format_id: フォーマットID

        Returns:
            FormatUrlDto | None: キャッシュされたフォーマットURL情報。存在しない場合はNone
        """
        return await self._query_service.find_by_video_and_format_id(video_id, format_id)
