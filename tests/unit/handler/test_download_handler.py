"""
DownloadHandler ユニットテスト

DownloadHandlerのエンドポイント動作を検証するユニットテストです。
FastAPI TestClientを使用して、HTTPリクエスト/レスポンスの動作を検証します。
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from streamshuttle.di.container import (
    get_or_resolve_stream_url_use_case,
    get_redis_dao,
    get_video_formats_use_case,
)
from streamshuttle.handler.download_handler import router
from streamshuttle.infrastructure.dao.redis_dao import RedisDao
from streamshuttle.shared.csrf_token import generate_csrf_token
from streamshuttle.shared.exceptions import (
    InvalidUrlError,
    InvalidVideoIdError,
    YouTubeResolverError,
)
from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto
from streamshuttle.usecase.facade.get_or_resolve_stream_url_usecase import (
    GetOrResolveStreamUrlUseCase,
)
from streamshuttle.usecase.query.get_video_formats_usecase import GetVideoFormatsUseCase


@pytest.fixture
def app():
    """
    テスト用FastAPIアプリケーションを作成します

    Returns:
        FastAPI: DownloadHandlerのルーターを含むFastAPIアプリケーション
    """
    from streamshuttle.shared.rate_limiter import limiter

    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(router)
    limiter.enabled = False
    return app


@pytest.fixture
def mock_get_formats_use_case():
    """
    モックされたGetVideoFormatsUseCaseを作成します

    Returns:
        AsyncMock: GetVideoFormatsUseCaseのモック
    """
    return AsyncMock(spec=GetVideoFormatsUseCase)


@pytest.fixture
def mock_get_or_resolve_use_case():
    """
    モックされたGetOrResolveStreamUrlUseCaseを作成します

    Returns:
        AsyncMock: GetOrResolveStreamUrlUseCaseのモック
    """
    return AsyncMock(spec=GetOrResolveStreamUrlUseCase)


@pytest.fixture
def mock_redis_dao():
    """
    モックされたRedisDAOを作成します

    Returns:
        AsyncMock: RedisDAOのモック
    """
    return AsyncMock(spec=RedisDao)


@pytest.fixture
def client(
    app,
    mock_get_formats_use_case,
    mock_get_or_resolve_use_case,
    mock_redis_dao,
):
    """
    テスト用クライアントを作成します

    依存性オーバーライドを使用して、UseCaseとDAOをモックに置き換えます。

    Args:
        app: FastAPIアプリケーション
        mock_get_formats_use_case: モックされたGetVideoFormatsUseCase
        mock_get_or_resolve_use_case: モックされたGetOrResolveStreamUrlUseCase
        mock_redis_dao: モックされたRedisDAO

    Returns:
        TestClient: FastAPI TestClient
    """
    app.dependency_overrides[get_video_formats_use_case] = lambda: mock_get_formats_use_case
    app.dependency_overrides[get_or_resolve_stream_url_use_case] = lambda: (
        mock_get_or_resolve_use_case
    )
    app.dependency_overrides[get_redis_dao] = lambda: mock_redis_dao
    return TestClient(app)


def test_get_formats_success(client, mock_get_formats_use_case):
    """
    正常系: フォーマット一覧の取得が成功し、JSON形式で返されることを検証します

    UseCaseが正常にフォーマット一覧を返す場合、
    エンドポイントは200 OKを返し、
    JSON形式でフォーマット一覧が含まれることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    video_info = VideoInfoDto(
        video_id="dQw4w9WgXcQ", title="Test Video", thumbnail_url="https://example.com/thumb.jpg"
    )
    formats = [
        VideoFormatDto(
            format_id="137",
            quality="1080p",
            codec="avc1",
            url="https://example.com/video1.mp4",
            has_audio=False,
            has_video=True,
        ),
        VideoFormatDto(
            format_id="136",
            quality="720p",
            codec="avc1",
            url="https://example.com/video2.mp4",
            has_audio=False,
            has_video=True,
        ),
    ]
    mock_get_formats_use_case.execute.return_value = (video_info, formats)

    # Act
    response = client.get(f"/formats?url={youtube_url}")

    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert "formats" in json_data
    assert len(json_data["formats"]) == 2
    assert json_data["formats"][0]["format_id"] == "137"
    assert json_data["formats"][0]["quality"] == "1080p"
    assert json_data["formats"][0]["codec"] == "avc1"
    assert json_data["formats"][0]["url"] == "https://example.com/video1.mp4"
    assert json_data["formats"][1]["format_id"] == "136"
    assert json_data["formats"][1]["quality"] == "720p"
    mock_get_formats_use_case.execute.assert_called_once_with(youtube_url)


def test_get_formats_with_empty_list(client, mock_get_formats_use_case):
    """
    正常系: フォーマット一覧が空の場合でも正常にレスポンスが返されることを検証します

    UseCaseが空のリストを返す場合でも、
    エンドポイントは200 OKを返し、
    空の配列が含まれることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    video_info = VideoInfoDto(
        video_id="dQw4w9WgXcQ", title="Test Video", thumbnail_url="https://example.com/thumb.jpg"
    )
    mock_get_formats_use_case.execute.return_value = (video_info, [])

    # Act
    response = client.get(f"/formats?url={youtube_url}")

    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert "formats" in json_data
    assert len(json_data["formats"]) == 0


def test_get_formats_with_error(client, mock_get_formats_use_case):
    """
    異常系: UseCase失敗時、500 Internal Server Errorが返されることを検証します

    UseCaseが例外を投げる場合、
    エンドポイントは500 Internal Server Errorを返し、
    エラーメッセージが含まれることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_get_formats_use_case.execute.side_effect = Exception("Failed to fetch formats")

    # Act
    response = client.get(f"/formats?url={youtube_url}")

    # Assert
    assert response.status_code == 500
    assert "An internal error occurred. Please try again later." in response.json()["detail"]


def test_get_formats_missing_url_parameter(client):
    """
    異常系: URLパラメータが不足している場合、422 Unprocessable Entityが返されることを検証します

    必須パラメータが不足している場合、
    FastAPIは自動的に422 Unprocessable Entityを返します。
    """
    # Act
    response = client.get("/formats")

    # Assert
    assert response.status_code == 422


def test_download_success(client, mock_get_or_resolve_use_case):
    """
    正常系: ダウンロードURLの取得が成功し、307リダイレクトが返されることを検証します

    UseCaseが正常に解決されたURLを返す場合、
    エンドポイントは307 Temporary Redirectを返し、
    Locationヘッダーに解決済みURLが設定されることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    resolved_url = "https://rr1---sn-example.googlevideo.com/videoplayback?..."
    mock_get_or_resolve_use_case.execute.return_value = resolved_url
    csrf_token = generate_csrf_token()

    # Act
    response = client.get(
        f"/download?url={youtube_url}&csrf_token={csrf_token}",
        headers={"referer": "http://testserver/"},
        follow_redirects=False,
    )

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == resolved_url
    mock_get_or_resolve_use_case.execute.assert_called_once_with(youtube_url, None)


def test_download_with_error(client, mock_get_or_resolve_use_case):
    """
    異常系: UseCase失敗時、500 Internal Server Errorが返されることを検証します

    UseCaseが例外を投げる場合、
    エンドポイントは500 Internal Server Errorを返し、
    エラーメッセージが含まれることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_get_or_resolve_use_case.execute.side_effect = Exception("Failed to resolve URL")
    csrf_token = generate_csrf_token()

    # Act
    response = client.get(
        f"/download?url={youtube_url}&csrf_token={csrf_token}",
        headers={"referer": "http://testserver/"},
    )

    # Assert
    assert response.status_code == 500
    assert "An internal error occurred. Please try again later." in response.json()["detail"]


def test_download_missing_url_parameter(client):
    """
    異常系: URLパラメータが不足している場合、422 Unprocessable Entityが返されることを検証します

    必須パラメータが不足している場合、
    FastAPIは自動的に422 Unprocessable Entityを返します。
    """
    # Act
    response = client.get("/download")

    # Assert
    assert response.status_code == 422


def test_download_calls_use_case_with_correct_params(client, mock_get_or_resolve_use_case):
    """
    UseCaseが正しいパラメータで呼び出されることを検証します

    エンドポイントに渡されたURLパラメータが、
    そのままUseCaseに渡されることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=test123"
    resolved_url = "https://example.com/video.mp4"
    mock_get_or_resolve_use_case.execute.return_value = resolved_url
    csrf_token = generate_csrf_token()

    # Act
    client.get(
        f"/download?url={youtube_url}&csrf_token={csrf_token}",
        headers={"referer": "http://testserver/"},
        follow_redirects=False,
    )

    # Assert
    mock_get_or_resolve_use_case.execute.assert_called_once_with(youtube_url, None)


def test_download_with_invalid_video_id(app):
    """
    /downloadエンドポイントで不正なビデオIDが渡された場合、
    400 Bad Requestが返されることを検証
    """
    # Arrange
    mock_use_case = AsyncMock()
    mock_use_case.execute.side_effect = InvalidVideoIdError("Invalid video ID")
    app.dependency_overrides[get_or_resolve_stream_url_use_case] = lambda: mock_use_case
    client = TestClient(app)
    csrf_token = generate_csrf_token()

    # Act
    response = client.get(
        f"/download?url=https://www.youtube.com/watch?v=invalid&csrf_token={csrf_token}",
        headers={"referer": "http://testserver/"},
    )

    # Assert
    assert response.status_code == 400
    assert "Invalid video ID" in response.json()["detail"]


def test_download_with_invalid_url(app):
    """
    /downloadエンドポイントで不正なURLが渡された場合、
    400 Bad Requestが返されることを検証
    """
    # Arrange
    mock_use_case = AsyncMock()
    mock_use_case.execute.side_effect = InvalidUrlError("Invalid URL")
    app.dependency_overrides[get_or_resolve_stream_url_use_case] = lambda: mock_use_case
    client = TestClient(app)
    csrf_token = generate_csrf_token()

    # Act
    response = client.get(
        f"/download?url=invalid-url&csrf_token={csrf_token}",
        headers={"referer": "http://testserver/"},
    )

    # Assert
    assert response.status_code == 400
    assert "Invalid URL" in response.json()["detail"]


def test_download_with_youtube_resolver_error(client, mock_get_or_resolve_use_case):
    """
    /downloadエンドポイントでYouTube解決に失敗した場合、
    502 Bad Gatewayが返されることを検証
    """
    # Arrange
    mock_get_or_resolve_use_case.execute.side_effect = YouTubeResolverError("Failed to resolve")
    csrf_token = generate_csrf_token()

    # Act
    response = client.get(
        f"/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&csrf_token={csrf_token}",
        headers={"referer": "http://testserver/"},
    )

    # Assert
    assert response.status_code == 502
    assert "Failed to resolve URL from YouTube." in response.json()["detail"]


def test_download_with_invalid_csrf_token(client, mock_get_or_resolve_use_case):
    """
    /downloadエンドポイントで無効なCSRFトークンが渡された場合、
    403 Forbiddenが返されることを検証
    """
    # Arrange
    mock_get_or_resolve_use_case.execute.return_value = "https://example.com/video.mp4"

    # Act
    response = client.get(
        "/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&csrf_token=invalid_token",
        headers={"referer": "http://testserver/"},
    )

    # Assert
    assert response.status_code == 403
    assert "Invalid or expired CSRF token." in response.json()["detail"]


def test_download_without_csrf_token(app):
    """
    /downloadエンドポイントでCSRFトークンなしの場合、
    422 Unprocessable Entityが返されることを検証
    """
    # Arrange
    mock_use_case = AsyncMock()
    app.dependency_overrides[get_or_resolve_stream_url_use_case] = lambda: mock_use_case
    client = TestClient(app)

    # Act
    response = client.get(
        "/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        headers={"referer": "http://testserver/"},
    )

    # Assert
    assert response.status_code == 422


def test_download_with_missing_referer(client, mock_get_or_resolve_use_case):
    """
    /downloadエンドポイントでRefererヘッダーがない場合、
    403 Forbiddenが返されることを検証
    """
    # Arrange
    mock_get_or_resolve_use_case.execute.return_value = "https://example.com/video.mp4"
    csrf_token = generate_csrf_token()

    # Act
    response = client.get(
        f"/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&csrf_token={csrf_token}"
    )

    # Assert
    assert response.status_code == 403
    assert "Invalid request origin." in response.json()["detail"]


def test_download_with_invalid_referer(client, mock_get_or_resolve_use_case):
    """
    /downloadエンドポイントで不正なRefererヘッダーの場合、
    403 Forbiddenが返されることを検証
    """
    # Arrange
    mock_get_or_resolve_use_case.execute.return_value = "https://example.com/video.mp4"
    csrf_token = generate_csrf_token()

    # Act
    response = client.get(
        f"/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&csrf_token={csrf_token}",
        headers={"referer": "https://malicious-site.com/"},
    )

    # Assert
    assert response.status_code == 403
    assert "Invalid request origin." in response.json()["detail"]


def test_get_formats_returns_csrf_token(client, mock_get_formats_use_case, mock_redis_dao):
    """
    /formatsエンドポイントがCSRFトークンを返すことを検証
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    video_info = VideoInfoDto(
        video_id="dQw4w9WgXcQ", title="Test Video", thumbnail_url="https://example.com/thumb.jpg"
    )
    mock_formats = [
        VideoFormatDto(
            format_id="137",
            quality="1080p",
            codec="avc1.640028",
            url="https://example.com/video1.mp4",
            has_audio=False,
            has_video=True,
        )
    ]
    mock_get_formats_use_case.execute.return_value = (video_info, mock_formats)
    mock_redis_dao.set.return_value = None

    # Act
    response = client.get(f"/formats?url={youtube_url}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "csrf_token" in data
    assert isinstance(data["csrf_token"], str)
    assert len(data["csrf_token"]) > 0


def test_download_with_format_id(client, mock_get_or_resolve_use_case):
    """
    正常系: format_idパラメータが渡された場合、UseCaseに正しく渡されることを検証します

    format_idが指定された場合、
    エンドポイントは307 Temporary Redirectを返し、
    UseCaseにformat_idが正しく渡されることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    format_id = "137"
    resolved_url = "https://rr1---sn-example.googlevideo.com/videoplayback?..."
    mock_get_or_resolve_use_case.execute.return_value = resolved_url
    csrf_token = generate_csrf_token()

    # Act
    response = client.get(
        f"/download?url={youtube_url}&format_id={format_id}&csrf_token={csrf_token}",
        headers={"referer": "http://testserver/"},
        follow_redirects=False,
    )

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == resolved_url
    mock_get_or_resolve_use_case.execute.assert_called_once_with(youtube_url, format_id)
