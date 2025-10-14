"""
キャッシュされたストリームURL取得UseCaseモジュール

キャッシュからストリームURL情報を取得するUseCaseを定義します。
"""

from streamshuttle.usecase.dto.stream_url_dto import StreamUrlDto
from streamshuttle.usecase.query_service.stream_url_query_service import StreamUrlQueryService


class GetCachedStreamUrlUseCase:
    """
    キャッシュされたストリームURL取得UseCase

    video_idをキーとして、キャッシュされたストリームURL情報を取得します。
    このUseCaseは参照系（Query）処理であり、データの更新は行いません。

    キャッシュに該当するデータが存在しない場合はNoneを返します。
    有効期限切れのチェックは呼び出し側（Handler層）で行います。
    """

    def __init__(self, query_service: StreamUrlQueryService) -> None:
        """
        GetCachedStreamUrlUseCaseを初期化します

        Args:
            query_service: StreamUrl参照用QueryService
        """
        self._query_service = query_service

    async def execute(self, video_id: str) -> StreamUrlDto | None:
        """
        video_idからキャッシュされたストリームURL情報を取得します

        Args:
            video_id: YouTube動画ID（11桁の英数字）

        Returns:
            StreamUrlDto | None:
                キャッシュが存在する場合はStreamUrlDto、存在しない場合はNone

        Raises:
            CacheException: キャッシュ操作に失敗した場合
        """
        return await self._query_service.find_by_video_id(video_id)
