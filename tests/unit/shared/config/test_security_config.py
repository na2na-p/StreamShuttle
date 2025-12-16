"""SecurityConfigのユニットテスト"""

import pytest

from streamshuttle.shared.config.security_config import SecurityConfig


@pytest.mark.parametrize(
    "env_vars, expected_max_url_length, expected_expiry",
    [
        pytest.param(
            {"SECURITY_CSRF_SECRET_KEY": "test-secret-key"},
            2000,
            600,
            id="正常系: デフォルト値が使用される",
        ),
        pytest.param(
            {
                "SECURITY_CSRF_SECRET_KEY": "test-secret-key",
                "SECURITY_MAX_URL_LENGTH": "3000",
                "SECURITY_CSRF_TOKEN_EXPIRY_SECONDS": "1200",
            },
            3000,
            1200,
            id="正常系: 環境変数から値が読み込まれる",
        ),
        pytest.param(
            {"SECURITY_CSRF_SECRET_KEY": "test-secret-key", "SECURITY_MAX_URL_LENGTH": "1500"},
            1500,
            600,
            id="正常系: 一部の環境変数のみ設定された場合、残りはデフォルト値",
        ),
    ],
)
def test_security_config_initialization(
    env_vars: dict[str, str],
    expected_max_url_length: int,
    expected_expiry: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SecurityConfigが環境変数から正しく初期化されることを確認"""
    # Arrange
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Act
    config = SecurityConfig()

    # Assert
    assert config.max_url_length == expected_max_url_length
    assert config.csrf_secret_key == "test-secret-key"
    assert config.csrf_token_expiry_seconds == expected_expiry


def test_security_config_is_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    """SecurityConfigがfrozenであることを確認"""
    # Arrange
    monkeypatch.setenv("SECURITY_CSRF_SECRET_KEY", "test-secret-key")
    config = SecurityConfig()

    # Act & Assert
    with pytest.raises(Exception):  # pydantic.ValidationError
        config.max_url_length = 9999  # type: ignore


def test_security_config_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """環境変数のプレフィックスSECURITY_が正しく適用されることを確認"""
    # Arrange
    monkeypatch.setenv("SECURITY_CSRF_SECRET_KEY", "correct-secret")
    monkeypatch.setenv("CSRF_SECRET_KEY", "wrong-secret")  # プレフィックスなしは無視されるべき

    # Act
    config = SecurityConfig()

    # Assert
    assert config.csrf_secret_key == "correct-secret"


def test_security_config_raises_error_when_csrf_secret_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SecurityConfigがCSRF秘密鍵未設定時にバリデーションエラーを発生させることを確認"""
    from pydantic import ValidationError

    # Arrange: 環境変数をクリア
    monkeypatch.delenv("SECURITY_CSRF_SECRET_KEY", raising=False)

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        SecurityConfig()

    # エラーメッセージにcsrf_secret_keyが含まれることを確認
    assert "csrf_secret_key" in str(exc_info.value)
