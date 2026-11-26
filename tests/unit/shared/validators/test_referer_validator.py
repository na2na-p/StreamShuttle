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
            pytest.param(
                "https://example.com",
                "http://testserver/",
                ["https://example.com"],
                None,
                None,
                id="正常系: パスなしのRefererでもオリジンが一致すれば許可される",
            ),
            pytest.param(
                "https://EXAMPLE.com:443/page",
                "http://testserver/",
                ["https://example.com"],
                None,
                None,
                id="正常系: ホスト名の大文字小文字と既定ポートの明示は同一オリジンとして扱われる",
            ),
            pytest.param(
                "http://testserver/other",
                "http://testserver/app/",
                [],
                None,
                None,
                id="正常系: base_urlにroot_pathがあってもオリジンが一致すればパスは問わない",
            ),
            pytest.param(
                "https://forwarded-host.com/page",
                "http://testserver/",
                [],
                "forwarded-host.com",
                "HTTPS",
                id="正常系: X-Forwarded-Protoが大文字でもオリジンが一致すれば許可される",
            ),
            pytest.param(
                "https://example.com:8443/page",
                "http://testserver/",
                [],
                "example.com:8443",
                "https",
                id="正常系: ポート付きX-Forwarded-Hostとポートが一致するRefererが許可される",
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

    @pytest.mark.parametrize(
        "referer,base_url,allowed_origins,forwarded_host,forwarded_proto",
        [
            pytest.param(
                "https://example.com.evil.net/page",
                "http://testserver/",
                ["https://example.com"],
                None,
                None,
                id="異常系: 許可オリジンを前方一致で含む別ホストのRefererの場合に403を返す",
            ),
            pytest.param(
                "https://example.com@evil.net/",
                "http://testserver/",
                ["https://example.com"],
                None,
                None,
                id="異常系: 許可オリジンを前方一致で含むuserinfo付き別ホストのRefererで403を返す",
            ),
            pytest.param(
                "https://user@example.com/",
                "http://testserver/",
                ["https://example.com"],
                None,
                None,
                id="異常系: ホストが一致してもユーザー名付きのRefererの場合に403を返す",
            ),
            pytest.param(
                "https://user:pw@example.com/",
                "http://testserver/",
                ["https://example.com"],
                None,
                None,
                id="異常系: ホストが一致してもユーザー名とパスワード付きのRefererの場合に403を返す",
            ),
            pytest.param(
                "https://example.com:8443/",
                "http://testserver/",
                ["https://example.com"],
                None,
                None,
                id="異常系: ポートが異なるRefererの場合に403を返す",
            ),
            pytest.param(
                "http://localhost:30001/",
                "http://testserver/",
                ["http://localhost:3000"],
                None,
                None,
                id="異常系: 許可ポートを前方一致で含む別ポートのRefererの場合に403を返す",
            ),
            pytest.param(
                "https://forwarded-host.com.evil.net/",
                "http://testserver/",
                [],
                "forwarded-host.com",
                "https",
                id="異常系: X-Forwarded-Hostを前方一致で含む別ホストのRefererの場合に403を返す",
            ),
            pytest.param(
                "http://testserver.evil.net/",
                "http://testserver/",
                [],
                None,
                None,
                id="異常系: base_urlのホストを前方一致で含む別ホストのRefererの場合に403を返す",
            ),
            pytest.param(
                "https://example.com:abc/",
                "http://testserver/",
                ["https://example.com"],
                None,
                None,
                id="異常系: ポートが不正なRefererの場合に403を返す",
            ),
            pytest.param(
                "javascript://example.com/",
                "http://testserver/",
                ["https://example.com"],
                None,
                None,
                id="異常系: http/https以外のスキームのRefererの場合に403を返す",
            ),
            pytest.param(
                "ftp://forwarded-host.com/",
                "http://testserver/",
                [],
                "forwarded-host.com",
                "ftp",
                id="異常系: 許可オリジンと一致してもhttp/https以外のスキームの場合に403を返す",
            ),
            pytest.param(
                "https:///page",
                "http://testserver/",
                ["https://"],
                None,
                None,
                id="異常系: 許可オリジンと一致してもホスト名がないRefererの場合に403を返す",
            ),
        ],
    )
    def test_validate_failure_origin_mismatch(
        self,
        mock_request,
        referer,
        base_url,
        allowed_origins,
        forwarded_host,
        forwarded_proto,
    ):
        """Refererがオリジンとして受理できない、または許可オリジンと一致しない場合、403が発生することを検証"""
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
        with pytest.raises(HTTPException) as exc_info:
            validator.validate(mock_request)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Invalid request origin."

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
