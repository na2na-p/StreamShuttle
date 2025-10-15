"""
ResolveHandler ユニットテスト

ResolveHandlerのエンドポイント動作を検証するユニットテストです。
FastAPI TestClientを使用して、HTTPリクエスト/レスポンスの動作を検証します。
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from streamshuttle.di.container import get_resolve_youtube_url_use_case
from streamshuttle.handler.resolve_handler import router
from streamshuttle.shared.exceptions import (
    InvalidUrlError,
    InvalidVideoIdError,
    YouTubeResolverError,
)
from streamshuttle.usecase.command.resolve_youtube_url_usecase import ResolveYoutubeUrlUseCase


@pytest.fixture
def app():
    """
    テスト用FastAPIアプリケーションを作成します

    Returns:
        FastAPI: ResolveHandlerのルーターを含むFastAPIアプリケーション
    """
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def mock_use_case():
    """
    モックされたResolveYoutubeUrlUseCaseを作成します

    Returns:
        AsyncMock: ResolveYoutubeUrlUseCaseのモック
    """
    return AsyncMock(spec=ResolveYoutubeUrlUseCase)


@pytest.fixture
def client(app, mock_use_case):
    """
    テスト用クライアントを作成します

    依存性オーバーライドを使用して、UseCaseをモックに置き換えます。

    Args:
        app: FastAPIアプリケーション
        mock_use_case: モックされたUseCase

    Returns:
        TestClient: FastAPI TestClient
    """
    app.dependency_overrides[get_resolve_youtube_url_use_case] = lambda: mock_use_case
    return TestClient(app)


def test_resolve_url_success(client, mock_use_case):
    """
    正常系: YouTube URLの解決が成功し、307リダイレクトが返されることを検証します

    UseCaseが正常に解決されたURLを返す場合、
    エンドポイントは307 Temporary Redirectを返し、
    Locationヘッダーに解決済みURLが設定されることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    resolved_url = "https://rr1---sn-example.googlevideo.com/videoplayback?..."
    mock_use_case.execute.return_value = resolved_url

    # Act
    response = client.get(f"/resolve?url={youtube_url}", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == resolved_url
    mock_use_case.execute.assert_called_once_with(youtube_url)


def test_resolve_url_with_invalid_video_id(client, mock_use_case):
    """
    異常系: 無効なビデオIDの場合、400 Bad Requestが返されることを検証します

    UseCaseがInvalidVideoIdErrorを投げる場合、
    エンドポイントは400 Bad Requestを返し、
    エラーメッセージが含まれることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=invalid"
    mock_use_case.execute.side_effect = InvalidVideoIdError("ビデオIDが無効です")

    # Act
    response = client.get(f"/resolve?url={youtube_url}")

    # Assert
    assert response.status_code == 400
    assert "Invalid video ID" in response.json()["detail"]


def test_resolve_url_with_invalid_url(client, mock_use_case):
    """
    異常系: 無効なURLの場合、400 Bad Requestが返されることを検証します

    UseCaseがInvalidUrlErrorを投げる場合、
    エンドポイントは400 Bad Requestを返し、
    エラーメッセージが含まれることを確認します。
    """
    # Arrange
    invalid_url = "not-a-valid-url"
    mock_use_case.execute.side_effect = InvalidUrlError("URLが無効です")

    # Act
    response = client.get(f"/resolve?url={invalid_url}")

    # Assert
    assert response.status_code == 400
    assert "Invalid URL" in response.json()["detail"]


def test_resolve_url_with_youtube_resolver_error(client, mock_use_case):
    """
    異常系: YouTube解決エラーの場合、502 Bad Gatewayが返されることを検証します

    UseCaseがYouTubeResolverErrorを投げる場合、
    エンドポイントは502 Bad Gatewayを返し、
    エラーメッセージが含まれることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_use_case.execute.side_effect = YouTubeResolverError(
        "YouTube APIへのアクセスに失敗しました"
    )

    # Act
    response = client.get(f"/resolve?url={youtube_url}")

    # Assert
    assert response.status_code == 502
    assert "Failed to resolve URL" in response.json()["detail"]


def test_resolve_url_with_unexpected_error(client, mock_use_case):
    """
    異常系: 予期しないエラーの場合、500 Internal Server Errorが返されることを検証します

    UseCaseが想定外の例外を投げる場合、
    エンドポイントは500 Internal Server Errorを返し、
    エラーメッセージが含まれることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_use_case.execute.side_effect = RuntimeError("Unexpected error occurred")

    # Act
    response = client.get(f"/resolve?url={youtube_url}")

    # Assert
    assert response.status_code == 500
    assert "An internal error occurred. Please try again later." in response.json()["detail"]


def test_resolve_url_calls_use_case_with_correct_params(client, mock_use_case):
    """
    UseCaseが正しいパラメータで呼び出されることを検証します

    エンドポイントに渡されたURLパラメータが、
    そのままUseCaseに渡されることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=test123"
    resolved_url = "https://example.com/video.mp4"
    mock_use_case.execute.return_value = resolved_url

    # Act
    client.get(f"/resolve?url={youtube_url}")

    # Assert
    mock_use_case.execute.assert_called_once_with(youtube_url)


def test_resolve_url_missing_url_parameter(client):
    """
    異常系: URLパラメータが不足している場合、422 Unprocessable Entityが返されることを検証します

    必須パラメータが不足している場合、
    FastAPIは自動的に422 Unprocessable Entityを返します。
    """
    # Act
    response = client.get("/resolve")

    # Assert
    assert response.status_code == 422
