"""
ビデオフォーマットキャッシュQueryService Protocolモジュール

キャッシュからビデオフォーマット情報を取得するQueryServiceインターフェースを定義します。
"""

from typing import Protocol

from streamshuttle.usecase.dto.video_formats_dto import VideoFormatsDto


class VideoFormatsCacheQueryService(Protocol):
    """
    ビデオフォーマットキャッシュQueryService Protocol

    キャッシュからビデオフォーマット情報を取得するためのインターフェースです。
    CQRS原則に従い、Query（読み取り）操作を担当します。

    実装クラスはInfrastructure層に配置されます。
    """

    async def find_by_video_id(self, video_id: str) -> VideoFormatsDto | None:
        """
        動画IDでビデオフォーマット情報を取得します

        キャッシュから指定された動画IDに対応するビデオフォーマット情報を取得します。
        キャッシュに存在しない場合はNoneを返します。

        Args:
            video_id: YouTube動画ID

        Returns:
            VideoFormatsDto | None: キャッシュが存在する場合はVideoFormatsDto、存在しない場合はNone

        Note:
            キャッシュ取得に失敗した場合やJSON破損時は例外を投げず、Noneを返します。
            これにより、キャッシュミスとして扱われ、通常のyt-dlp処理にフォールバックします。
        """
        ...
