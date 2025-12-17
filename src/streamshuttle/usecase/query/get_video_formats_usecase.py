"""
ビデオフォーマット一覧取得UseCaseモジュール

YouTube動画の利用可能なフォーマット一覧を取得するUseCaseを定義します。
"""

from streamshuttle.domain.model.youtube_url.youtube_url import YoutubeUrl
from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_formats_dto import VideoFormatsDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto
from streamshuttle.usecase.query_service.video_format_query_service import (
    VideoFormatQueryService,
)
from streamshuttle.usecase.query_service.video_formats_cache_query_service import (
    VideoFormatsCacheQueryService,
)
from streamshuttle.usecase.repository.video_formats_repository import VideoFormatsRepository


class GetVideoFormatsUseCase:
    """
    ビデオフォーマット一覧取得UseCase

    YouTube動画URLから利用可能なフォーマット一覧を取得します。
    Redisキャッシュを活用し、2回目以降のリクエストを高速化します。
    CQRS原則に準拠した参照専用のUseCaseです。
    """

    def __init__(
        self,
        query_service: VideoFormatQueryService,
        repository: VideoFormatsRepository,
        cache_query_service: VideoFormatsCacheQueryService,
    ) -> None:
        """
        GetVideoFormatsUseCaseを初期化します

        Args:
            query_service: VideoFormat参照用QueryService（yt-dlp呼び出し）
            repository: VideoFormatsキャッシュ保存用Repository
            cache_query_service: VideoFormatsキャッシュ取得用QueryService
        """
        self._query_service = query_service
        self._repository = repository
        self._cache_query_service = cache_query_service

    async def execute(self, youtube_url: str) -> tuple[VideoInfoDto, list[VideoFormatDto]]:
        """
        YouTube動画URLから利用可能なフォーマット一覧と動画情報を取得します

        1回目のリクエスト: yt-dlpで情報取得 → Redisにキャッシュ → 返却
        2回目以降: Redisキャッシュから取得 → 返却（50-100ms）

        Args:
            youtube_url: YouTube動画URL（https://www.youtube.com/watch?v=xxxxx形式）

        Returns:
            tuple[VideoInfoDto, list[VideoFormatDto]]: 動画情報とフォーマット情報のリスト

        Raises:
            YouTubeResolverException: YouTube APIへのアクセスまたはURL解決に失敗した場合
            InvalidUrlException: 無効なURLが指定された場合
        """
        # 1. YouTube URLからvideo_idを抽出
        validated_url = YoutubeUrl(_value=youtube_url)
        video_id = validated_url.extract_video_id().value

        # 2. キャッシュチェック
        cached_formats = await self._cache_query_service.find_by_video_id(video_id)
        if cached_formats is not None:
            # キャッシュヒット: VideoFormatsDtoを分解して返す
            return cached_formats.video_info, cached_formats.formats

        # 3. キャッシュミス: yt-dlpで取得
        video_info, formats = await self._query_service.get_available_formats(youtube_url)

        # 4. キャッシュに保存
        video_formats_dto = VideoFormatsDto(video_info=video_info, formats=formats)
        await self._repository.save(video_id=video_id, video_formats=video_formats_dto)

        # 5. 結果を返す
        return video_info, formats
