"""
フォーマットURL QueryServiceインターフェース定義モジュール

キャッシュされたフォーマットURL情報を取得するQueryServiceのインターフェースを定義します。
"""

from typing import Protocol

from streamshuttle.usecase.dto.format_url_dto import FormatUrlDto


class FormatUrlQueryService(Protocol):
    """
    フォーマットURL QueryServiceインターフェース

    video_idとformat_idに対応するキャッシュされたフォーマットURL情報を取得するための
    インターフェースです。このインターフェースは参照系（GET）処理からのみ呼び出され、
    実装クラスはRedisキャッシュからのデータ取得のみを行います。

    実装クラスはInfrastructure層に配置されます。
    """

    async def find_by_video_and_format_id(
        self, video_id: str, format_id: str
    ) -> FormatUrlDto | None:
        """
        video_idとformat_idでフォーマットURL情報を取得します

        Redisキャッシュから指定されたvideo_idとformat_idに対応するフォーマットURL情報を
        取得します。キャッシュに存在しない場合はNoneを返します。

        Args:
            video_id: YouTube動画ID
            format_id: フォーマットID

        Returns:
            FormatUrlDto | None:
                キャッシュが存在する場合はFormatUrlDto、存在しない場合はNone

        Raises:
            CacheException: キャッシュ操作に失敗した場合
        """
        ...
