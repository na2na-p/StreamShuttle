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

    DDD原則に従い、参照系メソッド（find_by_*等）はQueryServiceに分離されます。
    このRepositoryはコマンド（書き込み）操作のみを定義します。
    """

    async def save(self, stream_url: StreamUrl, use_hls: bool = False) -> None:
        """
        StreamUrlを保存します

        StreamUrl Aggregateをデータストア（Redis等）に永続化します。
        既に同じVideoIdのStreamUrlが存在する場合は上書きします。

        use_hlsパラメータはキャッシュキーの一部として使用され、
        同じvideo_idでもuse_hlsの値が異なれば別のエントリとして保存されます。

        Args:
            stream_url: 保存するStreamUrl Aggregate
            use_hls: HLS形式の使用フラグ（デフォルト: False）

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
