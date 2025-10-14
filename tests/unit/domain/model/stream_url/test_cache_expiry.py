"""
CacheExpiry ValueObjectのユニットテスト

CacheExpiry ValueObjectの正常系と異常系のテストを提供します。
"""

from datetime import UTC, datetime, timedelta

import pytest

from streamshuttle.domain.model.stream_url.cache_expiry import CacheExpiry


def test_cache_expiry_creation_with_timezone_aware_datetime():
    """
    正常系: タイムゾーン付きdatetimeでCacheExpiryを生成できることを確認

    Arrange: タイムゾーン付きdatetimeを準備
    Act: CacheExpiryを生成
    Assert: expiry_atプロパティで元のdatetimeが取得できることを確認
    """
    # Arrange
    expiry_at = datetime.now(UTC) + timedelta(hours=6)

    # Act
    cache_expiry = CacheExpiry(_expiry_at=expiry_at)

    # Assert
    assert cache_expiry.expiry_at == expiry_at


def test_cache_expiry_raises_exception_for_timezone_naive_datetime():
    """
    異常系: タイムゾーンなしdatetimeでCacheExpiryを生成すると
    ValueErrorが発生することを確認

    Arrange: タイムゾーンなしdatetimeを準備
    Act & Assert: CacheExpiry生成時にValueErrorが発生することを確認
    """
    # Arrange
    naive_datetime = datetime.now()  # タイムゾーンなし

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        CacheExpiry(_expiry_at=naive_datetime)

    assert "タイムゾーン情報を持つ必要があります" in str(exc_info.value)


def test_cache_expiry_is_expired_returns_false_for_future_expiry():
    """
    正常系: 有効期限が未来の場合、is_expired()がFalseを返すことを確認

    Arrange: 未来の日時でCacheExpiryを生成
    Act: is_expired()を呼び出す
    Assert: Falseが返されることを確認
    """
    # Arrange
    expiry_at = datetime.now(UTC) + timedelta(hours=1)
    cache_expiry = CacheExpiry(_expiry_at=expiry_at)

    # Act
    is_expired = cache_expiry.is_expired()

    # Assert
    assert is_expired is False


def test_cache_expiry_is_expired_returns_true_for_past_expiry():
    """
    正常系: 有効期限が過去の場合、is_expired()がTrueを返すことを確認

    Arrange: 過去の日時でCacheExpiryを生成
    Act: is_expired()を呼び出す
    Assert: Trueが返されることを確認
    """
    # Arrange
    expiry_at = datetime.now(UTC) - timedelta(hours=1)
    cache_expiry = CacheExpiry(_expiry_at=expiry_at)

    # Act
    is_expired = cache_expiry.is_expired()

    # Assert
    assert is_expired is True


def test_cache_expiry_is_expired_returns_true_for_current_time():
    """
    正常系: 有効期限が現在時刻と同じ場合、is_expired()がTrueを返すことを確認

    現在時刻以降は期限切れと判定されます。

    Arrange: 現在時刻でCacheExpiryを生成
    Act: is_expired()を呼び出す
    Assert: Trueが返されることを確認
    """
    # Arrange
    expiry_at = datetime.now(UTC)
    cache_expiry = CacheExpiry(_expiry_at=expiry_at)

    # Act
    is_expired = cache_expiry.is_expired()

    # Assert
    assert is_expired is True


def test_cache_expiry_ttl_seconds_returns_positive_value():
    """
    正常系: 有効期限が未来の場合、ttl_seconds()が正の値を返すことを確認

    Arrange: 1時間後の日時でCacheExpiryを生成
    Act: ttl_seconds()を呼び出す
    Assert: 3600秒前後の値が返されることを確認
    """
    # Arrange
    expiry_at = datetime.now(UTC) + timedelta(hours=1)
    cache_expiry = CacheExpiry(_expiry_at=expiry_at)

    # Act
    ttl = cache_expiry.ttl_seconds()

    # Assert
    assert 3590 <= ttl <= 3600  # 実行時間を考慮して少し幅を持たせる


def test_cache_expiry_ttl_seconds_returns_zero_for_past_expiry():
    """
    正常系: 有効期限が過去の場合、ttl_seconds()が0を返すことを確認

    Arrange: 過去の日時でCacheExpiryを生成
    Act: ttl_seconds()を呼び出す
    Assert: 0が返されることを確認
    """
    # Arrange
    expiry_at = datetime.now(UTC) - timedelta(hours=1)
    cache_expiry = CacheExpiry(_expiry_at=expiry_at)

    # Act
    ttl = cache_expiry.ttl_seconds()

    # Assert
    assert ttl == 0


def test_cache_expiry_ttl_seconds_returns_zero_for_current_time():
    """
    正常系: 有効期限が現在時刻の場合、ttl_seconds()が0を返すことを確認

    Arrange: 現在時刻でCacheExpiryを生成
    Act: ttl_seconds()を呼び出す
    Assert: 0が返されることを確認
    """
    # Arrange
    expiry_at = datetime.now(UTC)
    cache_expiry = CacheExpiry(_expiry_at=expiry_at)

    # Act
    ttl = cache_expiry.ttl_seconds()

    # Assert
    assert ttl == 0


def test_cache_expiry_immutability():
    """
    正常系: CacheExpiryが不変であることを確認

    frozen=Trueのdataclassとして定義されているため、
    生成後にexpiry_atを変更できないことを確認します。

    Arrange: タイムゾーン付きdatetimeでCacheExpiryを生成
    Act: expiry_atを変更しようとする
    Assert: 変更がエラーになることを確認
    """
    # Arrange
    expiry_at = datetime.now(UTC) + timedelta(hours=6)
    cache_expiry = CacheExpiry(_expiry_at=expiry_at)

    # Act & Assert
    with pytest.raises(Exception):  # FrozenInstanceErrorまたはAttributeError
        new_expiry = datetime.now(UTC) + timedelta(hours=12)
        cache_expiry._expiry_at = new_expiry  # noqa: F841


def test_cache_expiry_equality():
    """
    正常系: 同じ有効期限を持つCacheExpiryインスタンスが等価であることを確認

    dataclassのfrozen=Trueにより、同じ値を持つインスタンスは等価と判定されます。

    Arrange: 同じdatetimeから2つのCacheExpiryを生成
    Act: 等価比較
    Assert: 等価であることを確認
    """
    # Arrange
    expiry_at = datetime.now(UTC) + timedelta(hours=6)
    cache_expiry_1 = CacheExpiry(_expiry_at=expiry_at)
    cache_expiry_2 = CacheExpiry(_expiry_at=expiry_at)

    # Act & Assert
    assert cache_expiry_1 == cache_expiry_2


def test_cache_expiry_inequality():
    """
    正常系: 異なる有効期限を持つCacheExpiryインスタンスが等価でないことを確認

    Arrange: 異なるdatetimeから2つのCacheExpiryを生成
    Act: 等価比較
    Assert: 等価でないことを確認
    """
    # Arrange
    expiry_at_1 = datetime.now(UTC) + timedelta(hours=6)
    expiry_at_2 = datetime.now(UTC) + timedelta(hours=12)
    cache_expiry_1 = CacheExpiry(_expiry_at=expiry_at_1)
    cache_expiry_2 = CacheExpiry(_expiry_at=expiry_at_2)

    # Act & Assert
    assert cache_expiry_1 != cache_expiry_2
