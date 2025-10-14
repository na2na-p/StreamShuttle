"""
ResolvedUrl ValueObjectのユニットテスト

ResolvedUrl ValueObjectの正常系と異常系のテストを提供します。
"""

import pytest

from streamshuttle.domain.model.stream_url.resolved_url import ResolvedUrl
from streamshuttle.shared.exceptions import InvalidUrlError


def test_resolved_url_creation_with_https_url():
    """
    正常系: HTTPSスキームを持つ有効なURLでResolvedUrlを生成できることを確認

    Arrange: HTTPSスキームを持つ有効なURL文字列を準備
    Act: ResolvedUrlを生成
    Assert: valueプロパティで元の文字列が取得できることを確認
    """
    # Arrange
    valid_url = "https://example.com/video.m3u8"

    # Act
    resolved_url = ResolvedUrl(_value=valid_url)

    # Assert
    assert resolved_url.value == valid_url


def test_resolved_url_creation_with_http_url():
    """
    正常系: HTTPスキームを持つ有効なURLでResolvedUrlを生成できることを確認

    Arrange: HTTPスキームを持つ有効なURL文字列を準備
    Act: ResolvedUrlを生成
    Assert: valueプロパティで元の文字列が取得できることを確認
    """
    # Arrange
    valid_url = "http://example.com/video.mp4"

    # Act
    resolved_url = ResolvedUrl(_value=valid_url)

    # Assert
    assert resolved_url.value == valid_url


def test_resolved_url_with_query_parameters():
    """
    正常系: クエリパラメータを含むURLでResolvedUrlを生成できることを確認

    Arrange: クエリパラメータを含む有効なURL文字列を準備
    Act: ResolvedUrlを生成
    Assert: valueプロパティで元の文字列が取得できることを確認
    """
    # Arrange
    valid_url = "https://example.com/video.m3u8?token=abc123&expires=3600"

    # Act
    resolved_url = ResolvedUrl(_value=valid_url)

    # Assert
    assert resolved_url.value == valid_url


def test_resolved_url_with_port_number():
    """
    正常系: ポート番号を含むURLでResolvedUrlを生成できることを確認

    Arrange: ポート番号を含む有効なURL文字列を準備
    Act: ResolvedUrlを生成
    Assert: valueプロパティで元の文字列が取得できることを確認
    """
    # Arrange
    valid_url = "https://example.com:8080/video.m3u8"

    # Act
    resolved_url = ResolvedUrl(_value=valid_url)

    # Assert
    assert resolved_url.value == valid_url


def test_resolved_url_raises_exception_for_empty_string():
    """
    異常系: 空文字列でResolvedUrlを生成するとInvalidUrlErrorが発生することを確認

    Arrange: 空文字列を準備
    Act & Assert: ResolvedUrl生成時にInvalidUrlErrorが発生することを確認
    """
    # Arrange
    empty_url = ""

    # Act & Assert
    with pytest.raises(InvalidUrlError) as exc_info:
        ResolvedUrl(_value=empty_url)

    assert "URLが空です" in str(exc_info.value)


def test_resolved_url_raises_exception_for_invalid_scheme():
    """
    異常系: HTTP/HTTPS以外のスキームを持つURLでResolvedUrlを生成すると
    InvalidUrlErrorが発生することを確認

    Arrange: ftpスキームを持つURL文字列を準備
    Act & Assert: ResolvedUrl生成時にInvalidUrlErrorが発生することを確認
    """
    # Arrange
    invalid_url = "ftp://example.com/video.mp4"

    # Act & Assert
    with pytest.raises(InvalidUrlError) as exc_info:
        ResolvedUrl(_value=invalid_url)

    assert "HTTP/HTTPSスキームを持つ必要があります" in str(exc_info.value)


def test_resolved_url_raises_exception_for_no_scheme():
    """
    異常系: スキームを持たないURLでResolvedUrlを生成すると
    InvalidUrlErrorが発生することを確認

    Arrange: スキームを持たないURL文字列を準備
    Act & Assert: ResolvedUrl生成時にInvalidUrlErrorが発生することを確認
    """
    # Arrange
    invalid_url = "example.com/video.mp4"

    # Act & Assert
    with pytest.raises(InvalidUrlError) as exc_info:
        ResolvedUrl(_value=invalid_url)

    assert "HTTP/HTTPSスキームを持つ必要があります" in str(exc_info.value)


def test_resolved_url_raises_exception_for_no_host():
    """
    異常系: ホスト名を持たないURLでResolvedUrlを生成すると
    InvalidUrlErrorが発生することを確認

    Arrange: ホスト名を持たないURL文字列を準備
    Act & Assert: ResolvedUrl生成時にInvalidUrlErrorが発生することを確認
    """
    # Arrange
    invalid_url = "https:///path/to/video.mp4"

    # Act & Assert
    with pytest.raises(InvalidUrlError) as exc_info:
        ResolvedUrl(_value=invalid_url)

    assert "ホスト名が含まれていません" in str(exc_info.value)


def test_resolved_url_raises_exception_for_scheme_only():
    """
    異常系: スキームのみのURLでResolvedUrlを生成すると
    InvalidUrlErrorが発生することを確認

    Arrange: スキームのみのURL文字列を準備
    Act & Assert: ResolvedUrl生成時にInvalidUrlErrorが発生することを確認
    """
    # Arrange
    invalid_url = "https://"

    # Act & Assert
    with pytest.raises(InvalidUrlError) as exc_info:
        ResolvedUrl(_value=invalid_url)

    assert "ホスト名が含まれていません" in str(exc_info.value)


def test_resolved_url_immutability():
    """
    正常系: ResolvedUrlが不変であることを確認

    frozen=Trueのdataclassとして定義されているため、
    生成後にvalueを変更できないことを確認します。

    Arrange: 有効なURL文字列を準備
    Act: ResolvedUrlを生成し、valueを変更しようとする
    Assert: 変更がエラーになることを確認
    """
    # Arrange
    valid_url = "https://example.com/video.m3u8"
    resolved_url = ResolvedUrl(_value=valid_url)

    # Act & Assert
    with pytest.raises(Exception):  # FrozenInstanceErrorまたはAttributeError
        resolved_url._value = "https://new-url.com/video.mp4"  # noqa: F841


def test_resolved_url_equality():
    """
    正常系: 同じURLを持つResolvedUrlインスタンスが等価であることを確認

    dataclassのfrozen=Trueにより、同じ値を持つインスタンスは等価と判定されます。

    Arrange: 同じURL文字列から2つのResolvedUrlを生成
    Act: 等価比較
    Assert: 等価であることを確認
    """
    # Arrange
    valid_url = "https://example.com/video.m3u8"
    resolved_url_1 = ResolvedUrl(_value=valid_url)
    resolved_url_2 = ResolvedUrl(_value=valid_url)

    # Act & Assert
    assert resolved_url_1 == resolved_url_2


def test_resolved_url_inequality():
    """
    正常系: 異なるURLを持つResolvedUrlインスタンスが等価でないことを確認

    Arrange: 異なるURL文字列から2つのResolvedUrlを生成
    Act: 等価比較
    Assert: 等価でないことを確認
    """
    # Arrange
    resolved_url_1 = ResolvedUrl(_value="https://example.com/video1.m3u8")
    resolved_url_2 = ResolvedUrl(_value="https://example.com/video2.m3u8")

    # Act & Assert
    assert resolved_url_1 != resolved_url_2
