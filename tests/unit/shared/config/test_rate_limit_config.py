"""RateLimitConfigのユニットテスト"""

import pytest

from streamshuttle.shared.config.rate_limit_config import RateLimitConfig


@pytest.mark.parametrize(
    "env_vars, expected_resolve, expected_formats, expected_download",
    [
        pytest.param(
            {},
            "10/minute",
            "5/minute",
            "5/minute",
            id="正常系: デフォルト値が使用される",
        ),
        pytest.param(
            {
                "RATE_LIMIT_RESOLVE": "20/minute",
                "RATE_LIMIT_FORMATS": "10/minute",
                "RATE_LIMIT_DOWNLOAD": "10/minute",
            },
            "20/minute",
            "10/minute",
            "10/minute",
            id="正常系: 環境変数から値が読み込まれる",
        ),
        pytest.param(
            {"RATE_LIMIT_RESOLVE": "30/minute"},
            "30/minute",
            "5/minute",
            "5/minute",
            id="正常系: 一部の環境変数のみ設定された場合、残りはデフォルト値",
        ),
    ],
)
def test_rate_limit_config_initialization(
    env_vars: dict[str, str],
    expected_resolve: str,
    expected_formats: str,
    expected_download: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RateLimitConfigが環境変数から正しく初期化されることを確認"""
    # Arrange
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Act
    config = RateLimitConfig()

    # Assert
    assert config.resolve == expected_resolve
    assert config.formats == expected_formats
    assert config.download == expected_download


def test_rate_limit_config_is_frozen() -> None:
    """RateLimitConfigがfrozenであることを確認"""
    # Arrange
    config = RateLimitConfig()

    # Act & Assert
    with pytest.raises(Exception):  # pydantic.ValidationError
        config.resolve = "100/minute"  # type: ignore


def test_rate_limit_config_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """環境変数のプレフィックスRATE_LIMIT_が正しく適用されることを確認"""
    # Arrange
    monkeypatch.setenv("RATE_LIMIT_RESOLVE", "15/minute")
    monkeypatch.setenv("RESOLVE", "999/minute")  # プレフィックスなしの環境変数は無視されるべき

    # Act
    config = RateLimitConfig()

    # Assert
    assert config.resolve == "15/minute"
