"""CorsConfigのユニットテスト"""

import pytest

from streamshuttle.shared.config.cors_config import CorsConfig


@pytest.mark.parametrize(
    "env_vars, expected_origins",
    [
        pytest.param({}, [], id="正常系: デフォルト値が使用される（空リスト）"),
        pytest.param(
            {"CORS_ALLOWED_ORIGINS_RAW": "http://localhost:3000"},
            ["http://localhost:3000"],
            id="正常系: 単一のオリジンが設定される",
        ),
        pytest.param(
            {"CORS_ALLOWED_ORIGINS_RAW": "http://localhost:3000,http://127.0.0.1:3000"},
            ["http://localhost:3000", "http://127.0.0.1:3000"],
            id="正常系: 複数のオリジンがカンマ区切りで設定される",
        ),
        pytest.param(
            {"CORS_ALLOWED_ORIGINS_RAW": "http://localhost:3000, http://127.0.0.1:3000"},
            ["http://localhost:3000", "http://127.0.0.1:3000"],
            id="正常系: カンマの後にスペースがある場合も正しく処理される",
        ),
        pytest.param(
            {"CORS_ALLOWED_ORIGINS_RAW": "http://localhost:3000,,http://127.0.0.1:3000"},
            ["http://localhost:3000", "http://127.0.0.1:3000"],
            id="正常系: 空の要素は無視される",
        ),
    ],
)
def test_cors_config_initialization(
    env_vars: dict[str, str], expected_origins: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """CorsConfigが環境変数から正しく初期化されることを確認"""
    # Arrange
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Act
    config = CorsConfig()

    # Assert
    assert config.allowed_origins == expected_origins


def test_cors_config_is_frozen() -> None:
    """CorsConfigがfrozenであることを確認"""
    # Arrange
    config = CorsConfig()

    # Act & Assert
    with pytest.raises(Exception):  # pydantic.ValidationError
        config.allowed_origins = ["http://example.com"]  # type: ignore


def test_cors_config_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """環境変数のプレフィックスCORS_が正しく適用されることを確認"""
    # Arrange
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS_RAW", "http://localhost:3000")
    monkeypatch.setenv(
        "ALLOWED_ORIGINS_RAW", "http://wrong.com"
    )  # プレフィックスなしは無視されるべき

    # Act
    config = CorsConfig()

    # Assert
    assert config.allowed_origins == ["http://localhost:3000"]
