"""
RefererValidatorユニットテスト

RefererValidatorの検証ロジックをテストします。
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request

from streamshuttle.shared.validators.referer_validator import RefererValidator


@pytest.fixture
def mock_request():
    """モックリクエストを生成するfixture"""
    request = MagicMock(spec=Request)
    request.base_url = "http://testserver/"
    return request


class TestRefererValidator:
    """RefererValidatorのテストクラス"""

    @pytest.mark.parametrize(
        "referer,base_url,allowed_origins,forwarded_host,forwarded_proto",
        [
            pytest.param(
                "http://testserver/formats",
                "http://testserver/",
                [],
                None,
                None,
                id="正常系: base_urlからのRefererが許可される",
            ),
            pytest.param(
                "https://example.com/page",
                "http://testserver/",
                ["https://example.com"],
                None,
                None,
                id="正常系: 許可リストのオリジンからのRefererが許可される",
            ),
            pytest.param(
                "https://forwarded-host.com/page",
                "http://testserver/",
                [],
                "forwarded-host.com",
                "https",
                id="正常系: X-Forwarded-Hostからのオリジンが許可される",
            ),
            pytest.param(
                "https://forwarded-host.com/page",
                "http://testserver/",
                [],
                "forwarded-host.com",
                None,
                id="正常系: X-Forwarded-Host（プロトコルなし）からのオリジンが許可される",
            ),
        ],
    )
    def test_validate_success(
        self,
        mock_request,
        referer,
        base_url,
        allowed_origins,
        forwarded_host,
        forwarded_proto,
    ):
        """Refererが有効な場合、例外が発生しないことを検証"""
        # Arrange
        mock_request.base_url = base_url

        def get_header(name: str) -> str | None:
            headers = {
                "referer": referer,
                "x-forwarded-host": forwarded_host,
                "x-forwarded-proto": forwarded_proto,
            }
            return headers.get(name)

        mock_request.headers.get = get_header

        validator = RefererValidator(allowed_origins=allowed_origins)

        # Act & Assert
        validator.validate(mock_request)

    @pytest.mark.parametrize(
        "referer,allowed_origins,expected_status,expected_detail",
        [
            pytest.param(
                None,
                [],
                403,
                "Invalid request origin.",
                id="異常系: Refererヘッダーがない場合に403を返す",
            ),
            pytest.param(
                "",
                [],
                403,
                "Invalid request origin.",
                id="異常系: Refererが空文字の場合に403を返す",
            ),
            pytest.param(
                "https://malicious-site.com/page",
                [],
                403,
                "Invalid request origin.",
                id="異常系: 許可されていないオリジンからのRefererの場合に403を返す",
            ),
            pytest.param(
                "https://malicious-site.com/page",
                ["https://example.com"],
                403,
                "Invalid request origin.",
                id="異常系: 許可リストに存在しないオリジンからのRefererの場合に403を返す",
            ),
        ],
    )
    def test_validate_failure(
        self,
        mock_request,
        referer,
        allowed_origins,
        expected_status,
        expected_detail,
    ):
        """Refererが無効な場合、HTTPExceptionが発生することを検証"""
        # Arrange
        mock_request.base_url = "http://testserver/"

        def get_header(name: str) -> str | None:
            headers = {
                "referer": referer,
                "x-forwarded-host": None,
                "x-forwarded-proto": None,
            }
            return headers.get(name)

        mock_request.headers.get = get_header

        validator = RefererValidator(allowed_origins=allowed_origins)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validator.validate(mock_request)

        assert exc_info.value.status_code == expected_status
        assert exc_info.value.detail == expected_detail

    def test_build_allowed_origins_with_multiple_sources(self, mock_request):
        """複数のソースから許可オリジンリストが正しく構築されることを検証"""
        # Arrange
        mock_request.base_url = "http://testserver/"

        def get_header(name: str) -> str | None:
            headers = {
                "referer": "http://testserver/page",
                "x-forwarded-host": "forwarded.example.com",
                "x-forwarded-proto": "https",
            }
            return headers.get(name)

        mock_request.headers.get = get_header

        validator = RefererValidator(allowed_origins=["https://allowed.example.com"])

        # Act
        origins = validator._build_allowed_origins(mock_request)

        # Assert
        assert "http://testserver/" in origins
        assert "https://forwarded.example.com" in origins
        assert "https://allowed.example.com" in origins
        assert len(origins) == 3
