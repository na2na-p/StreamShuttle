"""
Codec ValueObjectのユニットテスト

Codec ValueObjectの正常系と異常系のテストを提供します。
"""

import pytest

from streamshuttle.domain.model.video_format.codec import Codec


def test_codec_creation_with_valid_value():
    """
    正常系: 有効なコーデック情報でCodecを生成できることを確認

    Arrange: 有効なコーデック文字列を準備
    Act: Codecを生成
    Assert: valueプロパティで元の文字列が取得できることを確認
    """
    # Arrange
    valid_codec = "h264"

    # Act
    codec = Codec(_value=valid_codec)

    # Assert
    assert codec.value == valid_codec


def test_codec_creation_with_vp9():
    """
    正常系: "vp9"コーデック情報でCodecを生成できることを確認

    Arrange: "vp9"文字列を準備
    Act: Codecを生成
    Assert: valueプロパティで"vp9"が取得できることを確認
    """
    # Arrange
    vp9_codec = "vp9"

    # Act
    codec = Codec(_value=vp9_codec)

    # Assert
    assert codec.value == vp9_codec


def test_codec_raises_exception_for_empty_string():
    """
    異常系: 空文字列でCodecを生成するとValueErrorが発生することを確認

    Arrange: 空文字列を準備
    Act & Assert: Codec生成時にValueErrorが発生することを確認
    """
    # Arrange
    empty_codec = ""

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        Codec(_value=empty_codec)

    assert "コーデック情報が空です" in str(exc_info.value)


def test_codec_immutability():
    """
    正常系: Codecが不変であることを確認

    frozen=Trueのdataclassとして定義されているため、
    生成後にvalueを変更できないことを確認します。

    Arrange: 有効なコーデック文字列を準備
    Act: Codecを生成し、valueを変更しようとする
    Assert: 変更がエラーになることを確認
    """
    # Arrange
    valid_codec = "h264"
    codec = Codec(_value=valid_codec)

    # Act & Assert
    with pytest.raises(Exception):  # FrozenInstanceErrorまたはAttributeError
        codec._value = "vp9"  # noqa: F841


def test_codec_equality():
    """
    正常系: 同じコーデック情報を持つCodecインスタンスが等価であることを確認

    Arrange: 同じコーデック文字列から2つのCodecを生成
    Act: 等価比較
    Assert: 等価であることを確認
    """
    # Arrange
    valid_codec = "h264"
    codec_1 = Codec(_value=valid_codec)
    codec_2 = Codec(_value=valid_codec)

    # Act & Assert
    assert codec_1 == codec_2


def test_codec_inequality():
    """
    正常系: 異なるコーデック情報を持つCodecインスタンスが等価でないことを確認

    Arrange: 異なるコーデック文字列から2つのCodecを生成
    Act: 等価比較
    Assert: 等価でないことを確認
    """
    # Arrange
    codec_1 = Codec(_value="h264")
    codec_2 = Codec(_value="vp9")

    # Act & Assert
    assert codec_1 != codec_2
