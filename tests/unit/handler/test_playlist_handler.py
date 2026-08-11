"""
PlaylistHandler ユニットテスト

PlaylistHandlerのエンドポイント動作を検証するユニットテストです。
FastAPI TestClientを使用して、HTTPリクエスト/レスポンスの動作を検証します。
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from streamshuttle.di.container import (
    get_playlist_use_case,
    get_resolve_youtube_url_use_case,
)
from streamshuttle.handler.playlist_handler import router
from streamshuttle.shared.exceptions import (
    InvalidPlaylistIdError,
    InvalidUrlError,
    PlaylistNotFoundError,
    YouTubeResolverError,
)
from streamshuttle.usecase.command.resolve_youtube_url_usecase import (
    ResolveYoutubeUrlUseCase,
)
from streamshuttle.usecase.dto.playlist_info_dto import PlaylistInfoDto
from streamshuttle.usecase.dto.playlist_item_dto import PlaylistItemDto
from streamshuttle.usecase.query.get_playlist_usecase import GetPlaylistUseCase

PLAYLIST_ID = "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
PLAYLIST_URL = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"


@pytest.fixture
def app():
    """
    テスト用FastAPIアプリケーションを作成します

    Returns:
        FastAPI: PlaylistHandlerのルーターを含むFastAPIアプリケーション
    """
    from streamshuttle.shared.rate_limiter import limiter

    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(router)
    limiter.enabled = False
    return app


@pytest.fixture
def mock_get_playlist_use_case():
    """モックされたGetPlaylistUseCase"""
    return AsyncMock(spec=GetPlaylistUseCase)


@pytest.fixture
def mock_resolve_use_case():
    """モックされたResolveYoutubeUrlUseCase"""
    return AsyncMock(spec=ResolveYoutubeUrlUseCase)


@pytest.fixture
def client(app, mock_get_playlist_use_case, mock_resolve_use_case):
    """
    テスト用クライアントを作成します

    依存性オーバーライドを使用して、UseCaseをモックに置き換えます。

    Returns:
        TestClient: FastAPI TestClient
    """
    app.dependency_overrides[get_playlist_use_case] = lambda: mock_get_playlist_use_case
    app.dependency_overrides[get_resolve_youtube_url_use_case] = lambda: mock_resolve_use_case
    return TestClient(app)


@pytest.fixture
def playlist_result():
    """UseCaseが返すプレイリスト情報と動画一覧"""
    playlist_info = PlaylistInfoDto(
        playlist_id=PLAYLIST_ID,
        title="テストプレイリスト",
        uploader="テストチャンネル",
        item_count=2,
        truncated=False,
    )
    items = [
        PlaylistItemDto(
            video_id="dQw4w9WgXcQ",
            title="1曲目",
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            duration_seconds=120,
            thumbnail_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
        ),
        PlaylistItemDto(
            video_id="9bZkp7q19f0",
            title="2曲目",
            url="https://www.youtube.com/watch?v=9bZkp7q19f0",
            duration_seconds=None,
            thumbnail_url="https://i.ytimg.com/vi/9bZkp7q19f0/mqdefault.jpg",
        ),
    ]
    return playlist_info, items


def test_get_playlist_success(client, mock_get_playlist_use_case, playlist_result):
    """
    正常系: プレイリスト一覧の取得が成功し、JSON形式で返されることを検証します
    """
    # Arrange
    mock_get_playlist_use_case.execute.return_value = playlist_result

    # Act
    response = client.get(f"/playlist?url={PLAYLIST_URL}")

    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["playlist_info"]["playlist_id"] == PLAYLIST_ID
    assert json_data["playlist_info"]["title"] == "テストプレイリスト"
    assert json_data["playlist_info"]["item_count"] == 2
    assert json_data["playlist_info"]["truncated"] is False
    assert len(json_data["items"]) == 2
    assert json_data["items"][0]["video_id"] == "dQw4w9WgXcQ"
    assert json_data["items"][1]["duration_seconds"] is None
    mock_get_playlist_use_case.execute.assert_called_once_with(PLAYLIST_URL)


def test_get_playlist_requires_url_parameter(client):
    """
    異常系: urlパラメータがない場合、422 Unprocessable Entityが返されることを検証します
    """
    # Act
    response = client.get("/playlist")

    # Assert
    assert response.status_code == 422


@pytest.mark.parametrize(
    "error, expected_status",
    [
        pytest.param(InvalidPlaylistIdError(), 400, id="異常系: プレイリストID不正で400"),
        pytest.param(InvalidUrlError(), 400, id="異常系: URL不正で400"),
        pytest.param(PlaylistNotFoundError(), 404, id="異常系: プレイリスト未検出で404"),
        pytest.param(YouTubeResolverError(), 502, id="異常系: YouTube接続失敗で502"),
        pytest.param(Exception("unexpected"), 500, id="異常系: 予期しないエラーで500"),
    ],
)
def test_get_playlist_error_responses(client, mock_get_playlist_use_case, error, expected_status):
    """
    異常系: UseCaseの例外が適切なHTTPステータスコードに変換されることを検証します
    """
    # Arrange
    mock_get_playlist_use_case.execute.side_effect = error

    # Act
    response = client.get(f"/playlist?url={PLAYLIST_URL}")

    # Assert
    assert response.status_code == expected_status
    assert "detail" in response.json()


def test_get_playlist_rejects_too_long_url(client, mock_get_playlist_use_case):
    """
    異常系: 長さ制限を超えるURLが400 Bad Requestで拒否されることを検証します
    """
    # Arrange
    long_url = f"{PLAYLIST_URL}{'a' * 3000}"

    # Act
    response = client.get("/playlist", params={"url": long_url})

    # Assert
    assert response.status_code == 400
    mock_get_playlist_use_case.execute.assert_not_called()


def test_get_playlist_stream_success(client, mock_resolve_use_case):
    """
    正常系: ストリームURLの解決が成功し、JSON形式で返されることを検証します
    """
    # Arrange
    mock_resolve_use_case.execute.return_value = "https://example.googlevideo.com/videoplayback"

    # Act
    response = client.get("/playlist/stream?video_id=dQw4w9WgXcQ")

    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["video_id"] == "dQw4w9WgXcQ"
    assert json_data["stream_url"] == "https://example.googlevideo.com/videoplayback"

    # 動画IDから組み立てたYouTube URLでUseCaseが呼ばれることを確認
    called_url = mock_resolve_use_case.execute.call_args.args[0]
    assert called_url.value == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_get_playlist_stream_rejects_invalid_video_id(client, mock_resolve_use_case):
    """
    異常系: 不正な形式の動画IDが400 Bad Requestで拒否されることを検証します
    """
    # Act
    response = client.get("/playlist/stream?video_id=invalid")

    # Assert
    assert response.status_code == 400
    mock_resolve_use_case.execute.assert_not_called()


@pytest.mark.parametrize(
    "error, expected_status",
    [
        pytest.param(YouTubeResolverError(), 502, id="異常系: URL解決失敗で502"),
        pytest.param(Exception("unexpected"), 500, id="異常系: 予期しないエラーで500"),
    ],
)
def test_get_playlist_stream_error_responses(client, mock_resolve_use_case, error, expected_status):
    """
    異常系: UseCaseの例外が適切なHTTPステータスコードに変換されることを検証します
    """
    # Arrange
    mock_resolve_use_case.execute.side_effect = error

    # Act
    response = client.get("/playlist/stream?video_id=dQw4w9WgXcQ")

    # Assert
    assert response.status_code == expected_status
    assert "detail" in response.json()
