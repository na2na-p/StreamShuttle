"""UrlValidator のユニットテスト"""

import pytest

from streamshuttle.shared.exceptions import InvalidUrlError
from streamshuttle.shared.validators.url_validator import UrlValidator


class TestUrlValidator:
    """UrlValidator クラスのテスト"""

    @pytest.mark.parametrize(
        "url, max_length",
        [
            pytest.param(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                2000,
                id="正常系: 通常のYouTube URL（デフォルト制限内）",
            ),
            pytest.param(
                "https://youtu.be/dQw4w9WgXcQ",
                2000,
                id="正常系: 短縮YouTube URL（デフォルト制限内）",
            ),
            pytest.param(
                "a" * 2000,
                2000,
                id="正常系: 最大長ちょうどのURL",
            ),
            pytest.param(
                "a" * 100,
                100,
                id="正常系: カスタム最大長ちょうどのURL",
            ),
            pytest.param(
                "",
                2000,
                id="正常系: 空のURL",
            ),
        ],
    )
    def test_validate_length_passes_for_valid_urls(self, url: str, max_length: int) -> None:
        """URL長が制限内の場合、例外を発生させないことを検証"""
        # Arrange
        validator = UrlValidator(max_length=max_length)

        # Act & Assert - 例外が発生しないことを確認
        validator.validate_length(url)

    @pytest.mark.parametrize(
        "url, max_length, expected_url_length",
        [
            pytest.param(
                "a" * 2001,
                2000,
                2001,
                id="異常系: デフォルト最大長を1文字超過",
            ),
            pytest.param(
                "a" * 3000,
                2000,
                3000,
                id="異常系: デフォルト最大長を大幅に超過",
            ),
            pytest.param(
                "a" * 101,
                100,
                101,
                id="異常系: カスタム最大長を1文字超過",
            ),
        ],
    )
    def test_validate_length_raises_error_for_too_long_urls(
        self, url: str, max_length: int, expected_url_length: int
    ) -> None:
        """URL長が制限を超える場合、InvalidUrlErrorが発生することを検証"""
        # Arrange
        validator = UrlValidator(max_length=max_length)

        # Act & Assert
        with pytest.raises(InvalidUrlError) as exc_info:
            validator.validate_length(url)

        # エラーメッセージに制限値と実際の長さが含まれることを確認
        assert str(max_length) in str(exc_info.value)
        assert str(expected_url_length) in str(exc_info.value)

    def test_default_max_length_is_2000(self) -> None:
        """デフォルトのmax_lengthが2000であることを検証"""
        # Arrange & Act
        validator = UrlValidator()

        # Assert
        assert validator.max_length == 2000

    def test_validator_is_immutable(self) -> None:
        """UrlValidatorがイミュータブルであることを検証"""
        # Arrange
        validator = UrlValidator(max_length=1000)

        # Act & Assert - frozen=Trueにより属性変更が不可
        with pytest.raises(AttributeError):
            validator.max_length = 2000  # type: ignore[misc]
