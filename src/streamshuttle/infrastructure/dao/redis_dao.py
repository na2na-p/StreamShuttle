"""
RedisDao モジュール

Redisへの接続とデータ操作を抽象化するDAOクラスを定義します。
"""

import redis.asyncio as redis

from streamshuttle.shared.exceptions import CacheError


class RedisDao:
    """
    RedisDao クラス

    Redisへの非同期データアクセスを提供するDAOクラスです。
    基本的なキーバリュー操作（set、get、delete、exists）を抽象化し、
    Redis接続の管理とエラーハンドリングを担当します。

    このDAOはRepository実装内で使用され、直接ドメイン層に公開されません。

    Attributes:
        _redis: Redis非同期クライアントインスタンス
    """

    def __init__(self, host: str, port: int, db: int) -> None:
        """
        RedisDaoを初期化します

        Args:
            host: Redisサーバーのホスト名またはIPアドレス
            port: Redisサーバーのポート番号
            db: 使用するRedisデータベース番号（0-15）
        """
        self._redis: redis.Redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,  # 自動的に文字列にデコード
        )

    async def set(self, key: str, value: str, ttl: int) -> None:
        """
        キーバリューをTTL付きでRedisに保存します

        Args:
            key: 保存するキー
            value: 保存する値
            ttl: Time To Live（秒単位）

        Raises:
            CacheError: Redis操作に失敗した場合
        """
        try:
            await self._redis.setex(name=key, time=ttl, value=value)
        except redis.RedisError as e:
            raise CacheError(f"Redisへの保存に失敗しました: key={key}") from e

    async def get(self, key: str) -> str | None:
        """
        キーから値を取得します

        Args:
            key: 取得するキー

        Returns:
            str | None: キーに対応する値。存在しない場合はNone

        Raises:
            CacheError: Redis操作に失敗した場合
        """
        try:
            result = await self._redis.get(name=key)
            return result
        except redis.RedisError as e:
            raise CacheError(f"Redisからの取得に失敗しました: key={key}") from e

    async def delete(self, key: str) -> None:
        """
        キーを削除します

        キーが存在しない場合でもエラーとしません。

        Args:
            key: 削除するキー

        Raises:
            CacheError: Redis操作に失敗した場合
        """
        try:
            await self._redis.delete(key)
        except redis.RedisError as e:
            raise CacheError(f"Redisからの削除に失敗しました: key={key}") from e

    async def exists(self, key: str) -> bool:
        """
        キーの存在を確認します

        Args:
            key: 確認するキー

        Returns:
            bool: キーが存在する場合True、存在しない場合False

        Raises:
            CacheError: Redis操作に失敗した場合
        """
        try:
            result = await self._redis.exists(key)
            return bool(result)
        except redis.RedisError as e:
            raise CacheError(f"Redisの存在確認に失敗しました: key={key}") from e

    async def close(self) -> None:
        """
        Redis接続をクローズします

        アプリケーション終了時やクリーンアップ時に呼び出されます。
        """
        await self._redis.aclose()
