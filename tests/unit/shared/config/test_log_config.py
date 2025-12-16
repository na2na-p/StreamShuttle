"""LogConfigのユニットテスト"""

import pytest

from streamshuttle.shared.config.log_config import LogConfig


@pytest.mark.parametrize(
    "env_vars, expected_level, expected_format",
    [
        pytest.param({}, "INFO", "json", id="正常系: デフォルト値が使用される"),
        pytest.param(
            {"LOG_LEVEL": "DEBUG", "LOG_FORMAT": "text"},
            "DEBUG",
            "text",
            id="正常系: 環境変数から値が読み込まれる",
        ),
        pytest.param(
            {"LOG_LEVEL": "WARNING"},
            "WARNING",
            "json",
            id="正常系: 一部の環境変数のみ設定された場合、残りはデフォルト値",
        ),
        pytest.param(
            {"LOG_FORMAT": "text"},
            "INFO",
            "text",
            id="正常系: フォーマットのみ設定される",
        ),
    ],
)
def test_log_config_initialization(
    env_vars: dict[str, str],
    expected_level: str,
    expected_format: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """LogConfigが環境変数から正しく初期化されることを確認"""
    # Arrange
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Act
    config = LogConfig()

    # Assert
    assert config.level == expected_level
    assert config.format == expected_format


def test_log_config_is_frozen() -> None:
    """LogConfigがfrozenであることを確認"""
    # Arrange
    config = LogConfig()

    # Act & Assert
    with pytest.raises(Exception):  # pydantic.ValidationError
        config.level = "ERROR"  # type: ignore


def test_log_config_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """環境変数のプレフィックスLOG_が正しく適用されることを確認"""
    # Arrange
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LEVEL", "ERROR")  # プレフィックスなしの環境変数は無視されるべき

    # Act
    config = LogConfig()

    # Assert
    assert config.level == "DEBUG"
