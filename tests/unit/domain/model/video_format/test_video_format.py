"""
VideoFormat Aggregateのユニットテスト

VideoFormat Aggregateの正常系と異常系のテストを提供します。
"""

import pytest

from streamshuttle.domain.model.video_format.codec import Codec
from streamshuttle.domain.model.video_format.format_id import FormatId
from streamshuttle.domain.model.video_format.quality import Quality
from streamshuttle.domain.model.video_format.video_format import VideoFormat


def test_video_format_creation_with_valid_parameters():
    """
    正常系: 有効なパラメータでVideoFormatを生成できることを確認

    Arrange: 有効なFormatId、Quality、Codecを準備
    Act: VideoFormatを生成
    Assert: 各プロパティで値が取得できることを確認
    """
    # Arrange
    format_id = FormatId(_value="137")
    quality = Quality(_value="1080p")
    codec = Codec(_value="h264")

    # Act
    video_format = VideoFormat(_format_id=format_id, _quality=quality, _codec=codec)

    # Assert
    assert video_format.format_id == format_id
    assert video_format.quality == quality
    assert video_format.codec == codec


def test_video_format_properties_are_accessible():
    """
    正常系: VideoFormatのプロパティ（format_id, quality, codec）が
    アクセス可能であることを確認

    Arrange: 有効なパラメータでVideoFormatを生成
    Act: 各プロパティにアクセス
    Assert: それぞれのValueObjectが取得できることを確認
    """
    # Arrange
    format_id = FormatId(_value="248")
    quality = Quality(_value="1080p")
    codec = Codec(_value="vp9")
    video_format = VideoFormat(_format_id=format_id, _quality=quality, _codec=codec)

    # Act & Assert
    assert video_format.format_id.value == "248"
    assert video_format.quality.value == "1080p"
    assert video_format.codec.value == "vp9"


def test_video_format_immutability():
    """
    正常系: VideoFormatが不変であることを確認

    frozen=Trueのdataclassとして定義されているため、
    生成後にプロパティを変更できないことを確認します。

    Arrange: 有効なパラメータでVideoFormatを生成
    Act: プロパティを変更しようとする
    Assert: 変更がエラーになることを確認
    """
    # Arrange
    video_format = VideoFormat(
        _format_id=FormatId(_value="137"),
        _quality=Quality(_value="1080p"),
        _codec=Codec(_value="h264"),
    )

    # Act & Assert
    with pytest.raises(Exception):  # FrozenInstanceErrorまたはAttributeError
        video_format._format_id = FormatId(_value="248")  # noqa: F841


def test_video_format_equality():
    """
    正常系: 同じ値を持つVideoFormatインスタンスが等価であることを確認

    dataclassのfrozen=Trueにより、同じ値を持つインスタンスは等価と判定されます。

    Arrange: 同じパラメータから2つのVideoFormatを生成
    Act: 等価比較
    Assert: 等価であることを確認
    """
    # Arrange
    format_id = FormatId(_value="137")
    quality = Quality(_value="1080p")
    codec = Codec(_value="h264")

    video_format_1 = VideoFormat(_format_id=format_id, _quality=quality, _codec=codec)
    video_format_2 = VideoFormat(_format_id=format_id, _quality=quality, _codec=codec)

    # Act & Assert
    assert video_format_1 == video_format_2


def test_video_format_inequality():
    """
    正常系: 異なる値を持つVideoFormatインスタンスが等価でないことを確認

    Arrange: 異なるパラメータから2つのVideoFormatを生成
    Act: 等価比較
    Assert: 等価でないことを確認
    """
    # Arrange
    video_format_1 = VideoFormat(
        _format_id=FormatId(_value="137"),
        _quality=Quality(_value="1080p"),
        _codec=Codec(_value="h264"),
    )
    video_format_2 = VideoFormat(
        _format_id=FormatId(_value="248"),
        _quality=Quality(_value="1080p"),
        _codec=Codec(_value="vp9"),
    )

    # Act & Assert
    assert video_format_1 != video_format_2
