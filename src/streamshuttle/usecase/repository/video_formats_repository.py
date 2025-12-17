"""
ビデオフォーマットRepository Protocolモジュール

ビデオフォーマット情報のキャッシュ保存を行うRepositoryインターフェースを定義します。
"""

from typing import Protocol

from streamshuttle.usecase.dto.video_formats_dto import VideoFormatsDto


class VideoFormatsRepository(Protocol):
    """
    ビデオフォーマットRepository Protocol

    ビデオフォーマット情報をキャッシュに保存するためのインターフェースです。
    CQRS原則に従い、Command（書き込み）操作を担当します。

    実装クラスはInfrastructure層に配置されます。
    """

    async def save(self, video_id: str, video_formats: VideoFormatsDto) -> None:
        """
        ビデオフォーマット情報をキャッシュに保存します

        Args:
            video_id: YouTube動画ID
            video_formats: 保存するビデオフォーマット情報

        Raises:
            CacheException: キャッシュ操作に失敗した場合
        """
        ...
