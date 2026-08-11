"""
プレイリストRepository実装モジュール

PlaylistRepository Protocolの実装クラスを定義します。
"""

from streamshuttle.domain.model.cache_key.playlist_cache_key import PlaylistCacheKey
from streamshuttle.domain.model.youtube_playlist import YouTubePlaylistId
from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.shared.config import config
from streamshuttle.usecase.dto.playlist_dto import PlaylistDto


class PlaylistRepository:
    """
    プレイリストRepository実装クラス

    PlaylistRepository Protocolの実装です。
    RedisDaoを使用してプレイリスト情報をキャッシュに保存します。

    エラーハンドリング:
        キャッシュ保存に失敗してもシステム全体のエラーにはせず、
        処理を継続します（ベストエフォート）。
    """

    def __init__(self, redis_dao: RedisDao) -> None:
        """
        PlaylistRepositoryを初期化します

        Args:
            redis_dao: Redis操作を行うDAOインスタンス
        """
        self._redis_dao = redis_dao

    async def save(self, playlist_id: str, playlist: PlaylistDto) -> None:
        """
        プレイリスト情報をキャッシュに保存します

        PlaylistDtoをJSON形式でシリアライズし、Redisにキャッシュします。
        TTLはconfig.cache.ttl_secondsで設定された値を使用します。

        Args:
            playlist_id: YouTubeプレイリストID
            playlist: 保存するプレイリスト情報

        Note:
            キャッシュ保存に失敗した場合でも例外を投げません。
            これにより、キャッシュ障害がサービス全体に影響しないようにします。
        """
        try:
            cache_key = PlaylistCacheKey(_playlist_id=YouTubePlaylistId(_value=playlist_id))
            json_data = playlist.model_dump_json()

            await self._redis_dao.set(
                key=cache_key.value,
                value=json_data,
                ttl=config.cache.ttl_seconds,
            )
        except Exception:
            pass
