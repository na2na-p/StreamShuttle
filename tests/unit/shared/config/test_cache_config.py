"""CacheConfigのユニットテスト"""

import pytest

from streamshuttle.shared.config.cache_config import CacheConfig


@pytest.mark.parametrize(
    "env_vars, expected_ttl",
    [
        pytest.param({}, 21600, id="正常系: デフォルト値が使用される（6時間）"),
        pytest.param(
            {"CACHE_TTL_SECONDS": "3600"}, 3600, id="正常系: 環境変数から値が読み込まれる（1時間）"
        ),
        pytest.param(
            {"CACHE_TTL_SECONDS": "7200"}, 7200, id="正常系: カスタム値が設定される（2時間）"
        ),
    ],
)
def test_cache_config_initialization(
    env_vars: dict[str, str], expected_ttl: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CacheConfigが環境変数から正しく初期化されることを確認"""
    # Arrange
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Act
    config = CacheConfig()

    # Assert
    assert config.ttl_seconds == expected_ttl


def test_cache_config_is_frozen() -> None:
    """CacheConfigがfrozenであることを確認"""
    # Arrange
    config = CacheConfig()

    # Act & Assert
    with pytest.raises(Exception):  # pydantic.ValidationError
        config.ttl_seconds = 9999  # type: ignore


def test_cache_config_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """環境変数のプレフィックスCACHE_が正しく適用されることを確認"""
    # Arrange
    monkeypatch.setenv("CACHE_TTL_SECONDS", "1800")
    monkeypatch.setenv("TTL_SECONDS", "9999")  # プレフィックスなしの環境変数は無視されるべき

    # Act
    config = CacheConfig()

    # Assert
    assert config.ttl_seconds == 1800
