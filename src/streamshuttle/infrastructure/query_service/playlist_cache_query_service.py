"""
プレイリストキャッシュQueryService実装モジュール

PlaylistCacheQueryService Protocolの実装クラスを定義します。
"""

from pydantic import ValidationError

from streamshuttle.domain.model.cache_key.playlist_cache_key import PlaylistCacheKey
from streamshuttle.domain.model.youtube_playlist import YouTubePlaylistId
from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.usecase.dto.playlist_dto import PlaylistDto


class PlaylistCacheQueryService:
    """
    プレイリストキャッシュQueryService実装クラス

    PlaylistCacheQueryService Protocolの実装です。
    RedisDaoを使用してキャッシュからプレイリスト情報を取得します。

    エラーハンドリング:
        キャッシュ取得に失敗した場合やJSON破損時はNoneを返します。
        これにより、キャッシュミスとして扱われ、通常のyt-dlp処理にフォールバックします。
    """

    def __init__(self, redis_dao: RedisDao) -> None:
        """
        PlaylistCacheQueryServiceを初期化します

        Args:
            redis_dao: Redis操作を行うDAOインスタンス
        """
        self._redis_dao = redis_dao

    async def find_by_playlist_id(self, playlist_id: str) -> PlaylistDto | None:
        """
        プレイリストIDでプレイリスト情報を取得します

        Args:
            playlist_id: YouTubeプレイリストID

        Returns:
            PlaylistDto | None: キャッシュが存在する場合はPlaylistDto、
                                存在しない場合やエラー時はNone
        """
        try:
            cache_key = PlaylistCacheKey(_playlist_id=YouTubePlaylistId(_value=playlist_id))
            cached_json = await self._redis_dao.get(key=cache_key.value)

            if cached_json is None:
                return None

            return PlaylistDto.model_validate_json(cached_json)

        except ValidationError:
            return None
        except Exception:
            return None
