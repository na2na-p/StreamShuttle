"""
ストリームURL QueryServiceインターフェース定義モジュール

キャッシュされたストリームURL情報を取得するQueryServiceのインターフェースを定義します。
"""

from typing import Protocol

from streamshuttle.usecase.dto.stream_url_dto import StreamUrlDto


class StreamUrlQueryService(Protocol):
    """
    ストリームURL QueryServiceインターフェース

    YouTube動画IDに対応するキャッシュされたストリームURL情報を取得するための
    インターフェースです。このインターフェースは参照系（GET）処理からのみ呼び出され、
    実装クラスはRedisキャッシュからのデータ取得のみを行います。

    実装クラスはInfrastructure層に配置されます。
    """

    async def find_by_video_id(self, video_id: str, use_hls: bool = False) -> StreamUrlDto | None:
        """
        YouTube動画IDでストリームURL情報を取得します

        Redisキャッシュから指定された動画IDに対応するストリームURL情報を取得します。
        キャッシュに存在しない場合はNoneを返します。

        use_hlsパラメータによってキャッシュキーが異なるため、同じvideo_idでも
        use_hlsの値によって異なる結果が返される可能性があります。

        Args:
            video_id: YouTube動画ID（11桁の英数字）
            use_hls: HLS形式の使用フラグ（デフォルト: False）

        Returns:
            StreamUrlDto | None:
                キャッシュが存在する場合はStreamUrlDto、存在しない場合はNone

        Raises:
            CacheException: キャッシュ操作に失敗した場合
        """
        ...
