"""
YouTubePlaylistId ValueObject ユニットテスト

プレイリストIDのバリデーションを検証します。
"""

import pytest

from streamshuttle.domain.model.youtube_playlist import YouTubePlaylistId
from streamshuttle.shared.exceptions import InvalidPlaylistIdError


@pytest.mark.parametrize(
    "playlist_id",
    [
        pytest.param("PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf", id="正常系: PL始まりのプレイリストID"),
        pytest.param("UUrAXtmErZgOeiKm4sgNOknGv", id="正常系: チャンネルアップロード"),
        pytest.param("OLAK5uy_kFVjPxbFOWnDJnRLXcAZL8_nSMHfLQqLo", id="正常系: 自動生成アルバム"),
        pytest.param("RDdQw4w9WgXcQ", id="正常系: ミックス"),
        pytest.param("PL-_abc123", id="正常系: ハイフンとアンダースコアを含む"),
    ],
)
def test_youtube_playlist_id_accepts_valid_id(playlist_id):
    """
    正常系: 有効なプレイリストIDでValueObjectが生成できることを確認

    Arrange: 有効なプレイリストIDを準備
    Act: YouTubePlaylistIdを生成
    Assert: valueが入力値と一致する
    """
    # Act
    result = YouTubePlaylistId(_value=playlist_id)

    # Assert
    assert result.value == playlist_id
    assert str(result) == playlist_id


@pytest.mark.parametrize(
    "playlist_id",
    [
        pytest.param("", id="異常系: 空文字"),
        pytest.param("P", id="異常系: 1文字（短すぎる）"),
        pytest.param("PL" + "a" * 63, id="異常系: 65文字（長すぎる）"),
        pytest.param("PL!nvalid", id="異常系: 記号を含む"),
        pytest.param("PL abc", id="異常系: 空白を含む"),
        pytest.param("PL/../etc", id="異常系: パス区切りを含む"),
    ],
)
def test_youtube_playlist_id_rejects_invalid_id(playlist_id):
    """
    異常系: 不正な形式のプレイリストIDが拒否されることを確認

    Arrange: 不正な形式のプレイリストIDを準備
    Act: YouTubePlaylistIdを生成
    Assert: InvalidPlaylistIdErrorが送出される
    """
    # Act & Assert
    with pytest.raises(InvalidPlaylistIdError):
        YouTubePlaylistId(_value=playlist_id)


@pytest.mark.parametrize(
    "playlist_id",
    [
        pytest.param("WL", id="異常系: 後で見る（非公開）"),
        pytest.param("LL", id="異常系: 高く評価した動画（非公開）"),
    ],
)
def test_youtube_playlist_id_rejects_private_playlist(playlist_id):
    """
    異常系: 非公開プレイリストが拒否されることを確認

    Arrange: 認証が必要な非公開プレイリストIDを準備
    Act: YouTubePlaylistIdを生成
    Assert: InvalidPlaylistIdErrorが送出される
    """
    # Act & Assert
    with pytest.raises(InvalidPlaylistIdError):
        YouTubePlaylistId(_value=playlist_id)
