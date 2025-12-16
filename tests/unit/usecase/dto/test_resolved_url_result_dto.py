"""ResolvedUrlResultDtoのユニットテスト"""

import pytest

from streamshuttle.usecase.dto.resolved_url_result_dto import ResolvedUrlResultDto


class TestResolvedUrlResultDto:
    """ResolvedUrlResultDtoのテストクラス"""

    @pytest.mark.parametrize(
        "resolved_url, ttl_seconds",
        [
            pytest.param(
                "https://example.com/stream/abc123",
                3600,
                id="正常系: 標準的なURL解決結果",
            ),
            pytest.param(
                "https://rr1---sn-abc.googlevideo.com/videoplayback?expire=123",
                7200,
                id="正常系: YouTubeストリームURL形式",
            ),
            pytest.param(
                "https://example.com/stream",
                0,
                id="正常系: TTLが0の場合",
            ),
        ],
    )
    def test_create_dto_with_valid_values(self, resolved_url: str, ttl_seconds: int) -> None:
        """有効な値でDTOを作成できることを確認する"""
        # Act
        dto = ResolvedUrlResultDto(
            resolved_url=resolved_url,
            ttl_seconds=ttl_seconds,
        )

        # Assert
        assert dto.resolved_url == resolved_url
        assert dto.ttl_seconds == ttl_seconds

    def test_dto_is_immutable(self) -> None:
        """DTOが不変であることを確認する"""
        # Arrange
        dto = ResolvedUrlResultDto(
            resolved_url="https://example.com/stream",
            ttl_seconds=3600,
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            dto.resolved_url = "https://other.com/stream"  # type: ignore[misc]

        with pytest.raises(AttributeError):
            dto.ttl_seconds = 1800  # type: ignore[misc]

    def test_dto_equality(self) -> None:
        """同じ値を持つDTOが等価であることを確認する"""
        # Arrange
        dto1 = ResolvedUrlResultDto(
            resolved_url="https://example.com/stream",
            ttl_seconds=3600,
        )
        dto2 = ResolvedUrlResultDto(
            resolved_url="https://example.com/stream",
            ttl_seconds=3600,
        )

        # Assert
        assert dto1 == dto2

    def test_dto_inequality(self) -> None:
        """異なる値を持つDTOが等価でないことを確認する"""
        # Arrange
        dto1 = ResolvedUrlResultDto(
            resolved_url="https://example.com/stream1",
            ttl_seconds=3600,
        )
        dto2 = ResolvedUrlResultDto(
            resolved_url="https://example.com/stream2",
            ttl_seconds=3600,
        )
        dto3 = ResolvedUrlResultDto(
            resolved_url="https://example.com/stream1",
            ttl_seconds=1800,
        )

        # Assert
        assert dto1 != dto2
        assert dto1 != dto3
