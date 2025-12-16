"""RedisConfigのユニットテスト"""

import pytest

from streamshuttle.shared.config.redis_config import RedisConfig


@pytest.mark.parametrize(
    "env_vars, expected_host, expected_port, expected_db",
    [
        pytest.param({}, "localhost", 6379, 0, id="正常系: デフォルト値が使用される"),
        pytest.param(
            {"REDIS_HOST": "redis.example.com", "REDIS_PORT": "6380", "REDIS_DB": "1"},
            "redis.example.com",
            6380,
            1,
            id="正常系: 環境変数から値が読み込まれる",
        ),
        pytest.param(
            {"REDIS_HOST": "custom-redis"},
            "custom-redis",
            6379,
            0,
            id="正常系: 一部の環境変数のみ設定された場合、残りはデフォルト値",
        ),
    ],
)
def test_redis_config_initialization(
    env_vars: dict[str, str],
    expected_host: str,
    expected_port: int,
    expected_db: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RedisConfigが環境変数から正しく初期化されることを確認"""
    # Arrange
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Act
    config = RedisConfig()

    # Assert
    assert config.host == expected_host
    assert config.port == expected_port
    assert config.db == expected_db


def test_redis_config_is_frozen() -> None:
    """RedisConfigがfrozenであることを確認"""
    # Arrange
    config = RedisConfig()

    # Act & Assert
    with pytest.raises(Exception):  # pydantic.ValidationError
        config.host = "new-host"  # type: ignore


def test_redis_config_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """環境変数のプレフィックスREDIS_が正しく適用されることを確認"""
    # Arrange
    monkeypatch.setenv("REDIS_HOST", "prefix-test-host")
    monkeypatch.setenv("HOST", "wrong-host")  # プレフィックスなしの環境変数は無視されるべき

    # Act
    config = RedisConfig()

    # Assert
    assert config.host == "prefix-test-host"
