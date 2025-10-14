"""
FormatId ValueObjectのユニットテスト

FormatId ValueObjectの正常系と異常系のテストを提供します。
"""

import pytest

from streamshuttle.domain.model.video_format.format_id import FormatId


def test_format_id_creation_with_valid_id():
    """
    正常系: 有効なフォーマットIDでFormatIdを生成できることを確認

    Arrange: 有効なフォーマットID文字列を準備
    Act: FormatIdを生成
    Assert: valueプロパティで元の文字列が取得できることを確認
    """
    # Arrange
    valid_id = "137"

    # Act
    format_id = FormatId(_value=valid_id)

    # Assert
    assert format_id.value == valid_id


def test_format_id_creation_with_alphanumeric_id():
    """
    正常系: 英数字を含むフォーマットIDでFormatIdを生成できることを確認

    Arrange: 英数字を含むフォーマットID文字列を準備
    Act: FormatIdを生成
    Assert: valueプロパティで元の文字列が取得できることを確認
    """
    # Arrange
    valid_id = "hls-1080p"

    # Act
    format_id = FormatId(_value=valid_id)

    # Assert
    assert format_id.value == valid_id


def test_format_id_raises_exception_for_empty_string():
    """
    異常系: 空文字列でFormatIdを生成するとValueErrorが発生することを確認

    Arrange: 空文字列を準備
    Act & Assert: FormatId生成時にValueErrorが発生することを確認
    """
    # Arrange
    empty_id = ""

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        FormatId(_value=empty_id)

    assert "フォーマットIDが空です" in str(exc_info.value)


def test_format_id_immutability():
    """
    正常系: FormatIdが不変であることを確認

    frozen=Trueのdataclassとして定義されているため、
    生成後にvalueを変更できないことを確認します。

    Arrange: 有効なフォーマットID文字列を準備
    Act: FormatIdを生成し、valueを変更しようとする
    Assert: 変更がエラーになることを確認
    """
    # Arrange
    valid_id = "137"
    format_id = FormatId(_value=valid_id)

    # Act & Assert
    with pytest.raises(Exception):  # FrozenInstanceErrorまたはAttributeError
        format_id._value = "248"  # noqa: F841


def test_format_id_equality():
    """
    正常系: 同じフォーマットIDを持つFormatIdインスタンスが等価であることを確認

    Arrange: 同じフォーマットID文字列から2つのFormatIdを生成
    Act: 等価比較
    Assert: 等価であることを確認
    """
    # Arrange
    valid_id = "137"
    format_id_1 = FormatId(_value=valid_id)
    format_id_2 = FormatId(_value=valid_id)

    # Act & Assert
    assert format_id_1 == format_id_2


def test_format_id_inequality():
    """
    正常系: 異なるフォーマットIDを持つFormatIdインスタンスが等価でないことを確認

    Arrange: 異なるフォーマットID文字列から2つのFormatIdを生成
    Act: 等価比較
    Assert: 等価でないことを確認
    """
    # Arrange
    format_id_1 = FormatId(_value="137")
    format_id_2 = FormatId(_value="248")

    # Act & Assert
    assert format_id_1 != format_id_2
