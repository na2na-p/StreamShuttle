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
    このUseCaseは参照系（Query）処理であり、データの更新は行いません。

    取得されるフォーマット情報には、フォーマットID、品質、コーデック、URLが含まれます。
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
        video_info, formats = await self._query_service.get_available_formats(youtube_url)
        return video_info, formats
