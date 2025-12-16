"""キャッシュ操作用Repositoryインターフェース"""

from typing import Protocol


class CacheRepository(Protocol):
    """キャッシュ操作用Repositoryインターフェース

    Domain層で定義されるインターフェース。
    Infrastructure層がこのインターフェースを実装する。
    読み書き両方の操作を持つため、Repositoryとして配置される。
    """

    async def get(self, key: str) -> str | None:
        """キャッシュから値を取得

        Args:
            key: キャッシュキー

        Returns:
            str | None: キャッシュ値。存在しない場合はNone
        """
        ...

    async def set(self, key: str, value: str, ttl: int) -> None:
        """キャッシュに値を保存

        Args:
            key: キャッシュキー
            value: 保存する値
            ttl: 有効期限（秒）
        """
        ...
