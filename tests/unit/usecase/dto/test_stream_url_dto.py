"""
StreamUrlDtoのユニットテスト

StreamUrlDtoの各機能をテストします。
"""

from datetime import UTC, datetime, timedelta

import pytest

from streamshuttle.usecase.dto.stream_url_dto import StreamUrlDto


class TestStreamUrlDto:
    """StreamUrlDtoのテストクラス"""

    @pytest.mark.parametrize(
        "expiry_offset_hours, expected_is_valid",
        [
            pytest.param(
                1,
                True,
                id="正常系: 有効期限が1時間後の場合、is_valid()はTrueを返す",
            ),
            pytest.param(
                24,
                True,
                id="正常系: 有効期限が24時間後の場合、is_valid()はTrueを返す",
            ),
            pytest.param(
                -1,
                False,
                id="異常系: 有効期限が1時間前の場合、is_valid()はFalseを返す",
            ),
            pytest.param(
                -24,
                False,
                id="異常系: 有効期限が24時間前の場合、is_valid()はFalseを返す",
            ),
        ],
    )
    def test_is_valid(self, expiry_offset_hours: int, expected_is_valid: bool) -> None:
        """is_valid()が有効期限に基づいて正しく判定することをテスト"""
        # Arrange
        video_id = "dQw4w9WgXcQ"
        resolved_url = "https://example.com/stream.m3u8"
        expiry_at = datetime.now(UTC) + timedelta(hours=expiry_offset_hours)

        dto = StreamUrlDto(
            video_id=video_id,
            resolved_url=resolved_url,
            expiry_at=expiry_at,
        )

        # Act
        result = dto.is_valid()

        # Assert
        assert result is expected_is_valid

    @pytest.mark.parametrize(
        "expiry_offset_hours, expected_is_expired",
        [
            pytest.param(
                1,
                False,
                id="正常系: 有効期限が1時間後の場合、is_expired()はFalseを返す",
            ),
            pytest.param(
                -1,
                True,
                id="異常系: 有効期限が1時間前の場合、is_expired()はTrueを返す",
            ),
        ],
    )
    def test_is_expired(self, expiry_offset_hours: int, expected_is_expired: bool) -> None:
        """is_expired()が有効期限に基づいて正しく判定することをテスト"""
        # Arrange
        video_id = "dQw4w9WgXcQ"
        resolved_url = "https://example.com/stream.m3u8"
        expiry_at = datetime.now(UTC) + timedelta(hours=expiry_offset_hours)

        dto = StreamUrlDto(
            video_id=video_id,
            resolved_url=resolved_url,
            expiry_at=expiry_at,
        )

        # Act
        result = dto.is_expired()

        # Assert
        assert result is expected_is_expired
