"""
StreamUrlRepository インターフェース

StreamUrl Aggregateの永続化を担当するRepositoryインターフェースを定義します。
"""

from typing import Protocol

from streamshuttle.domain.model.stream_url import StreamUrl, VideoId


class StreamUrlRepository(Protocol):
    """
    StreamUrlRepository インターフェース

    StreamUrl Aggregateの永続化操作を定義するプロトコルです。
    このインターフェースはDomain層に配置され、Infrastructure層で実装されます。

    CQRS原則に基づき、更新系UseCaseからAggregate単位でのキャッシュ取得が可能です。
    参照系UseCase向けのDTO取得はQueryServiceで行います。
    """

    async def save(self, stream_url: StreamUrl, hls: bool = False) -> None:
        """
        StreamUrlを保存します

        StreamUrl Aggregateをデータストア（Redis等）に永続化します。
        既に同じVideoIdのStreamUrlが存在する場合は上書きします。

        hlsパラメータはキャッシュキーの一部として使用され、
        同じvideo_idでもhlsの値が異なれば別のエントリとして保存されます。

        Args:
            stream_url: 保存するStreamUrl Aggregate
            hls: HLS形式の使用フラグ（デフォルト: False）

        Raises:
            CacheException: データストアへの保存に失敗した場合
        """
        ...

    async def delete(self, video_id: VideoId) -> None:
        """
        VideoIdに紐づくStreamUrlを削除します

        指定されたVideoIdに対応するStreamUrlをデータストアから削除します。
        該当するStreamUrlが存在しない場合でもエラーとしません。

        Args:
            video_id: 削除対象のVideoId

        Raises:
            CacheException: データストアからの削除に失敗した場合
        """
        ...

    async def find_by_video_id(self, video_id: str, hls: bool = False) -> StreamUrl | None:
        """
        VideoIdに紐づくStreamUrlを取得します

        指定されたVideoIdに対応するStreamUrl Aggregateをデータストアから取得します。
        該当するStreamUrlが存在しない場合はNoneを返します。

        hlsパラメータによってキャッシュキーが異なるため、同じvideo_idでも
        hlsの値によって異なる結果が返される可能性があります。

        Args:
            video_id: YouTube動画ID（11桁の英数字）
            hls: HLS形式の使用フラグ（デフォルト: False）

        Returns:
            StreamUrl | None:
                キャッシュが存在する場合はStreamUrl Aggregate、存在しない場合はNone

        Raises:
            CacheException: データストアからの取得に失敗した場合
        """
        ...
