"""
VideoId ValueObjectのユニットテスト

VideoId ValueObjectの正常系と異常系のテストを提供します。
"""

import pytest

from streamshuttle.domain.model.stream_url.video_id import VideoId
from streamshuttle.shared.exceptions import InvalidVideoIdError


def test_video_id_creation_with_valid_id():
    """
    正常系: 11文字の有効なビデオIDでVideoIdを生成できることを確認

    Arrange: 有効なビデオID文字列を準備
    Act: VideoIdを生成
    Assert: valueプロパティで元の文字列が取得できることを確認
    """
    # Arrange
    valid_id = "dQw4w9WgXcQ"

    # Act
    video_id = VideoId(_value=valid_id)

    # Assert
    assert video_id.value == valid_id


def test_video_id_with_hyphen_and_underscore():
    """
    正常系: ハイフンとアンダースコアを含む11文字のビデオIDが有効であることを確認

    YouTubeビデオIDは英数字に加えて - と _ を含むことができます。

    Arrange: ハイフンとアンダースコアを含む有効なビデオID文字列を準備
    Act: VideoIdを生成
    Assert: valueプロパティで元の文字列が取得できることを確認
    """
    # Arrange
    valid_id = "abc-123_XYZ"

    # Act
    video_id = VideoId(_value=valid_id)

    # Assert
    assert video_id.value == valid_id


def test_video_id_raises_exception_for_empty_string():
    """
    異常系: 空文字列でVideoIdを生成するとInvalidVideoIdErrorが発生することを確認

    Arrange: 空文字列を準備
    Act & Assert: VideoId生成時にInvalidVideoIdErrorが発生することを確認
    """
    # Arrange
    empty_id = ""

    # Act & Assert
    with pytest.raises(InvalidVideoIdError) as exc_info:
        VideoId(_value=empty_id)

    assert "ビデオIDが空です" in str(exc_info.value)


def test_video_id_raises_exception_for_short_id():
    """
    異常系: 10文字のビデオIDでVideoIdを生成するとInvalidVideoIdErrorが発生することを確認

    Arrange: 10文字のビデオID文字列を準備
    Act & Assert: VideoId生成時にInvalidVideoIdErrorが発生することを確認
    """
    # Arrange
    short_id = "dQw4w9WgXc"  # 10文字

    # Act & Assert
    with pytest.raises(InvalidVideoIdError) as exc_info:
        VideoId(_value=short_id)

    assert "11文字である必要があります" in str(exc_info.value)


def test_video_id_raises_exception_for_long_id():
    """
    異常系: 12文字のビデオIDでVideoIdを生成するとInvalidVideoIdErrorが発生することを確認

    Arrange: 12文字のビデオID文字列を準備
    Act & Assert: VideoId生成時にInvalidVideoIdErrorが発生することを確認
    """
    # Arrange
    long_id = "dQw4w9WgXcQQ"  # 12文字

    # Act & Assert
    with pytest.raises(InvalidVideoIdError) as exc_info:
        VideoId(_value=long_id)

    assert "11文字である必要があります" in str(exc_info.value)


def test_video_id_raises_exception_for_invalid_characters():
    """
    異常系: 不正な文字を含むビデオIDでVideoIdを生成すると
    InvalidVideoIdErrorが発生することを確認

    YouTubeビデオIDは英数字、ハイフン、アンダースコアのみ有効です。
    記号（@、!、#など）は無効です。

    Arrange: 不正な文字を含む11文字のビデオID文字列を準備
    Act & Assert: VideoId生成時にInvalidVideoIdErrorが発生することを確認
    """
    # Arrange
    invalid_id = "dQw4w9W@XcQ"  # @記号を含む

    # Act & Assert
    with pytest.raises(InvalidVideoIdError) as exc_info:
        VideoId(_value=invalid_id)

    assert "ビデオIDの形式が不正です" in str(exc_info.value)


def test_video_id_raises_exception_for_space():
    """
    異常系: スペースを含むビデオIDでVideoIdを生成すると
    InvalidVideoIdErrorが発生することを確認

    Arrange: スペースを含む11文字のビデオID文字列を準備
    Act & Assert: VideoId生成時にInvalidVideoIdErrorが発生することを確認
    """
    # Arrange
    invalid_id = "dQw4w9W XcQ"  # スペースを含む

    # Act & Assert
    with pytest.raises(InvalidVideoIdError) as exc_info:
        VideoId(_value=invalid_id)

    assert "ビデオIDの形式が不正です" in str(exc_info.value)


def test_video_id_immutability():
    """
    正常系: VideoIdが不変であることを確認

    frozen=Trueのdataclassとして定義されているため、
    生成後にvalueを変更できないことを確認します。

    Arrange: 有効なビデオID文字列を準備
    Act: VideoIdを生成し、valueを変更しようとする
    Assert: 変更がエラーになることを確認
    """
    # Arrange
    valid_id = "dQw4w9WgXcQ"
    video_id = VideoId(_value=valid_id)

    # Act & Assert
    with pytest.raises(Exception):  # FrozenInstanceErrorまたはAttributeError
        video_id._value = "newvalue123"  # noqa: F841


def test_video_id_equality():
    """
    正常系: 同じビデオIDを持つVideoIdインスタンスが等価であることを確認

    dataclassのfrozen=Trueにより、同じ値を持つインスタンスは等価と判定されます。

    Arrange: 同じビデオID文字列から2つのVideoIdを生成
    Act: 等価比較
    Assert: 等価であることを確認
    """
    # Arrange
    valid_id = "dQw4w9WgXcQ"
    video_id_1 = VideoId(_value=valid_id)
    video_id_2 = VideoId(_value=valid_id)

    # Act & Assert
    assert video_id_1 == video_id_2


def test_video_id_inequality():
    """
    正常系: 異なるビデオIDを持つVideoIdインスタンスが等価でないことを確認

    Arrange: 異なるビデオID文字列から2つのVideoIdを生成
    Act: 等価比較
    Assert: 等価でないことを確認
    """
    # Arrange
    video_id_1 = VideoId(_value="dQw4w9WgXcQ")
    video_id_2 = VideoId(_value="abcdefghijk")

    # Act & Assert
    assert video_id_1 != video_id_2


def test_video_id_str():
    """
    正常系: str()でビデオID文字列が取得できることを確認

    Arrange: 有効なビデオID文字列を準備
    Act: VideoIdを生成し、str()で文字列変換
    Assert: 元の文字列と一致することを確認
    """
    # Arrange
    valid_id = "dQw4w9WgXcQ"
    video_id = VideoId(_value=valid_id)

    # Act
    result = str(video_id)

    # Assert
    assert result == valid_id
