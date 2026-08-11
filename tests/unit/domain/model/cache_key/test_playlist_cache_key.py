"""
PlaylistCacheKey ValueObject ユニットテスト

プレイリストキャッシュキーの生成を検証します。
"""

from streamshuttle.domain.model.cache_key import PlaylistCacheKey
from streamshuttle.domain.model.youtube_playlist import YouTubePlaylistId


def test_playlist_cache_key_generates_prefixed_key():
    """
    正常系: プレイリストIDからキャッシュキーが生成されることを確認

    Arrange: YouTubePlaylistIdを準備
    Act: PlaylistCacheKeyを生成
    Assert: 「playlist:プレイリストID」形式のキーが返される
    """
    # Arrange
    playlist_id = YouTubePlaylistId(_value="PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf")

    # Act
    cache_key = PlaylistCacheKey(_playlist_id=playlist_id)

    # Assert
    assert cache_key.value == "playlist:PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
    assert str(cache_key) == "playlist:PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"


def test_playlist_cache_key_differs_by_playlist_id():
    """
    正常系: プレイリストIDが異なればキャッシュキーも異なることを確認

    Arrange: 異なる2つのプレイリストIDを準備
    Act: それぞれPlaylistCacheKeyを生成
    Assert: キーが一致しない
    """
    # Arrange
    first = YouTubePlaylistId(_value="PLaaaaaaaaaaaa")
    second = YouTubePlaylistId(_value="PLbbbbbbbbbbbb")

    # Act
    first_key = PlaylistCacheKey(_playlist_id=first)
    second_key = PlaylistCacheKey(_playlist_id=second)

    # Assert
    assert first_key.value != second_key.value
