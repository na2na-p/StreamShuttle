"""
ビデオフォーマット一覧取得UseCaseモジュール

YouTube動画の利用可能なフォーマット一覧を取得するUseCaseを定義します。
"""

from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto
from streamshuttle.usecase.query_service.video_format_query_service import VideoFormatQueryService


class GetVideoFormatsUseCase:
    """
    ビデオフォーマット一覧取得UseCase

    YouTube動画URLから利用可能なフォーマット一覧を取得します。
    CQRS原則に準拠した参照専用のUseCaseです。
    """

    def __init__(self, query_service: VideoFormatQueryService) -> None:
        """
        GetVideoFormatsUseCaseを初期化します

        Args:
            query_service: VideoFormat参照用QueryService
        """
        self._query_service = query_service

    async def execute(self, youtube_url: str) -> tuple[VideoInfoDto, list[VideoFormatDto]]:
        """
        YouTube動画URLから利用可能なフォーマット一覧と動画情報を取得します

        Args:
            youtube_url: YouTube動画URL（https://www.youtube.com/watch?v=xxxxx形式）

        Returns:
            tuple[VideoInfoDto, list[VideoFormatDto]]: 動画情報とフォーマット情報のリスト

        Raises:
            YouTubeResolverException: YouTube APIへのアクセスまたはURL解決に失敗した場合
            InvalidUrlException: 無効なURLが指定された場合
        """
        return await self._query_service.get_available_formats(youtube_url)
