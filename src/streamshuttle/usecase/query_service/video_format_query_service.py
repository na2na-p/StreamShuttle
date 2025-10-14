"""
ビデオフォーマット QueryServiceインターフェース定義モジュール

YouTube動画の利用可能なフォーマット情報を取得するQueryServiceのインターフェースを定義します。
"""

from abc import ABC, abstractmethod

from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto


class VideoFormatQueryService(ABC):
    """
    ビデオフォーマット QueryServiceインターフェース

    YouTube動画URLから利用可能なフォーマット情報を取得するためのインターフェースです。
    このインターフェースは参照系（GET）処理からのみ呼び出され、
    実装クラスはyt-dlpを使用してYouTubeから動画フォーマット情報を取得します。

    実装クラスはInfrastructure層に配置されます。
    """

    @abstractmethod
    async def get_available_formats(self, youtube_url: str) -> list[VideoFormatDto]:
        """
        YouTube動画URLから利用可能なフォーマット一覧を取得します

        yt-dlpを使用してYouTube動画の利用可能なフォーマット情報を取得し、
        VideoFormatDtoのリストとして返します。

        Args:
            youtube_url: YouTube動画URL（https://www.youtube.com/watch?v=xxxxx形式）

        Returns:
            list[VideoFormatDto]: 利用可能なフォーマット情報のリスト

        Raises:
            YouTubeResolverException: YouTube APIへのアクセスまたはURL解決に失敗した場合
            InvalidUrlException: 無効なURLが指定された場合
        """
        pass
