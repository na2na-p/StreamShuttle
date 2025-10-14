"""
Quality ValueObjectのユニットテスト

Quality ValueObjectの正常系と異常系のテストを提供します。
"""

import pytest

from streamshuttle.domain.model.video_format.quality import Quality


def test_quality_creation_with_valid_value():
    """
    正常系: 有効な画質情報でQualityを生成できることを確認

    Arrange: 有効な画質文字列を準備
    Act: Qualityを生成
    Assert: valueプロパティで元の文字列が取得できることを確認
    """
    # Arrange
    valid_quality = "1080p"

    # Act
    quality = Quality(_value=valid_quality)

    # Assert
    assert quality.value == valid_quality


def test_quality_creation_with_audio():
    """
    正常系: "audio"画質情報でQualityを生成できることを確認

    Arrange: "audio"文字列を準備
    Act: Qualityを生成
    Assert: valueプロパティで"audio"が取得できることを確認
    """
    # Arrange
    audio_quality = "audio"

    # Act
    quality = Quality(_value=audio_quality)

    # Assert
    assert quality.value == audio_quality


def test_quality_raises_exception_for_empty_string():
    """
    異常系: 空文字列でQualityを生成するとValueErrorが発生することを確認

    Arrange: 空文字列を準備
    Act & Assert: Quality生成時にValueErrorが発生することを確認
    """
    # Arrange
    empty_quality = ""

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        Quality(_value=empty_quality)

    assert "画質情報が空です" in str(exc_info.value)


def test_quality_immutability():
    """
    正常系: Qualityが不変であることを確認

    frozen=Trueのdataclassとして定義されているため、
    生成後にvalueを変更できないことを確認します。

    Arrange: 有効な画質文字列を準備
    Act: Qualityを生成し、valueを変更しようとする
    Assert: 変更がエラーになることを確認
    """
    # Arrange
    valid_quality = "1080p"
    quality = Quality(_value=valid_quality)

    # Act & Assert
    with pytest.raises(Exception):  # FrozenInstanceErrorまたはAttributeError
        quality._value = "720p"  # noqa: F841


def test_quality_equality():
    """
    正常系: 同じ画質情報を持つQualityインスタンスが等価であることを確認

    Arrange: 同じ画質文字列から2つのQualityを生成
    Act: 等価比較
    Assert: 等価であることを確認
    """
    # Arrange
    valid_quality = "1080p"
    quality_1 = Quality(_value=valid_quality)
    quality_2 = Quality(_value=valid_quality)

    # Act & Assert
    assert quality_1 == quality_2


def test_quality_inequality():
    """
    正常系: 異なる画質情報を持つQualityインスタンスが等価でないことを確認

    Arrange: 異なる画質文字列から2つのQualityを生成
    Act: 等価比較
    Assert: 等価でないことを確認
    """
    # Arrange
    quality_1 = Quality(_value="1080p")
    quality_2 = Quality(_value="720p")

    # Act & Assert
    assert quality_1 != quality_2
