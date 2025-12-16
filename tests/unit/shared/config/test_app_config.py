"""AppConfigのユニットテスト"""

import pytest

from streamshuttle.shared.config.app_config import AppConfig


def test_app_config_initialization_with_defaults() -> None:
    """AppConfigがデフォルト値で正しく初期化されることを確認

    NOTE: csrf_secret_keyは環境変数必須のため、conftest.pyで設定されたテスト用の値が使用される
    """
    # Act
    config = AppConfig()

    # Assert
    assert config.redis.host == "localhost"
    assert config.redis.port == 6379
    assert config.redis.db == 0
    assert config.cache.ttl_seconds == 21600
    assert config.cors.allowed_origins == []
    assert config.rate_limit.resolve == "10/minute"
    assert config.rate_limit.formats == "5/minute"
    assert config.rate_limit.download == "5/minute"
    assert config.security.max_url_length == 2000
    # csrf_secret_keyは環境変数必須（conftest.pyで設定されたテスト用の値）
    assert config.security.csrf_secret_key == "test-secret-key-for-testing-only"
    assert config.security.csrf_token_expiry_seconds == 600
    assert config.log.level == "INFO"
    assert config.log.format == "json"
    assert config.app_version == "1.0.0"


def test_app_config_initialization_with_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """AppConfigが環境変数から正しく初期化されることを確認"""
    # Arrange
    monkeypatch.setenv("REDIS_HOST", "redis.example.com")
    monkeypatch.setenv("REDIS_PORT", "6380")
    monkeypatch.setenv("CACHE_TTL_SECONDS", "3600")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS_RAW", "http://localhost:3000")
    monkeypatch.setenv("RATE_LIMIT_RESOLVE", "20/minute")
    monkeypatch.setenv("SECURITY_CSRF_SECRET_KEY", "production-secret")
    monkeypatch.setenv("SECURITY_MAX_URL_LENGTH", "3000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("APP_VERSION", "2.0.0")

    # Act
    config = AppConfig()

    # Assert
    assert config.redis.host == "redis.example.com"
    assert config.redis.port == 6380
    assert config.cache.ttl_seconds == 3600
    assert config.cors.allowed_origins == ["http://localhost:3000"]
    assert config.rate_limit.resolve == "20/minute"
    assert config.security.csrf_secret_key == "production-secret"
    assert config.security.max_url_length == 3000
    assert config.log.level == "DEBUG"
    assert config.app_version == "2.0.0"


def test_app_config_is_frozen() -> None:
    """AppConfigがfrozenであることを確認"""
    # Arrange
    config = AppConfig()

    # Act & Assert
    with pytest.raises(Exception):  # pydantic.ValidationError
        config.app_version = "3.0.0"  # type: ignore


def test_app_config_nested_configs_are_frozen() -> None:
    """AppConfigのネストされた設定もfrozenであることを確認"""
    # Arrange
    config = AppConfig()

    # Act & Assert
    with pytest.raises(Exception):  # pydantic.ValidationError
        config.redis.host = "new-host"  # type: ignore


def test_app_config_requires_csrf_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """AppConfigがCSRF秘密鍵未設定時にバリデーションエラーを発生させることを確認"""
    from pydantic import ValidationError

    # Arrange: 環境変数をクリア
    monkeypatch.delenv("SECURITY_CSRF_SECRET_KEY", raising=False)

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        AppConfig()

    # エラーメッセージにcsrf_secret_keyが含まれることを確認
    assert "csrf_secret_key" in str(exc_info.value)
