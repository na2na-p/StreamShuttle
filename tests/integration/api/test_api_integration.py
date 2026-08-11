"""
API統合テスト

全コンポーネントが統合された状態でFastAPIアプリケーションが正常に動作することを確認します。
fakeredisを使用してRedis接続をモックし、実際のRedisサーバーなしでテストを実行します。
"""

from unittest.mock import patch

import pytest
from fakeredis import FakeRedis
from fastapi.testclient import TestClient

from main import app
from streamshuttle.di import container


@pytest.fixture
def fake_redis():
    """
    fakeredisを使用したRedisモックのフィクスチャ

    テスト用のインメモリRedisインスタンスを提供します。

    Returns:
        FakeRedis: テスト用のRedisモックインスタンス
    """
    return FakeRedis()


@pytest.fixture
def client(fake_redis):
    """
    TestClientのフィクスチャ

    DIコンテナのRedis依存関係をfakeredisに差し替えて、
    テスト用のFastAPIクライアントを提供します。

    Args:
        fake_redis: fakeredisインスタンス

    Returns:
        TestClient: FastAPIテストクライアント
    """

    # DIコンテナのget_redis_daoをfakeredisを返すようにモック
    def mock_get_redis_dao():
        from streamshuttle.infrastructure.dao.redis_dao import RedisDao

        dao = RedisDao(host="localhost", port=6379, db=0)
        dao._client = fake_redis  # 内部のRedisクライアントをfakeredisに差し替え
        return dao

    with patch.object(container, "get_redis_dao", mock_get_redis_dao):
        # グローバルなシングルトンインスタンスをリセット
        container._redis_dao = None
        with TestClient(app) as test_client:
            yield test_client
        # テスト後にクリーンアップ
        container._redis_dao = None


def test_app_starts_successfully(client):
    """
    アプリケーションが正常に起動することを確認

    Args:
        client: TestClientインスタンス
    """
    # アプリケーションが正常に起動している場合、clientが取得できる
    assert client is not None


def test_root_endpoint(client):
    """
    ルートエンドポイント（GET /）が正常に動作することを確認

    Web UIのHTMLページが正しく返されることをテストします。

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/")
    assert response.status_code == 200

    # HTMLレスポンスであることを確認
    assert response.headers["content-type"].startswith("text/html")

    # HTMLの基本的な要素が含まれていることを確認
    html_content = response.text
    assert "<!DOCTYPE html>" in html_content
    assert "<html" in html_content
    assert "StreamShuttle" in html_content


def test_health_check(client):
    """
    ヘルスチェックエンドポイント（GET /healthz）が正常に動作することを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/healthz")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"


def test_resolve_endpoint_requires_url_parameter(client):
    """
    /resolveエンドポイントがURLパラメータを要求することを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/resolve")
    # urlパラメータがない場合は422エラー
    assert response.status_code == 422


def test_resolve_endpoint_with_invalid_url(client):
    """
    /resolveエンドポイントに不正なURLを渡した場合のエラーハンドリングを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/resolve?url=invalid_url")
    # 不正なURLの場合は400 Bad Requestまたは502エラー
    assert response.status_code in [400, 502, 500]


@pytest.mark.skip(reason="実際のYouTube APIを呼び出すため統合テストではスキップ")
def test_resolve_endpoint_with_real_youtube_url(client):
    """
    /resolveエンドポイントが実際のYouTube URLで動作することを確認（スキップ）

    このテストは実際のYouTube APIを呼び出すため、CI環境では実行をスキップします。
    手動テストやE2Eテストで使用することを想定しています。

    Args:
        client: TestClientインスタンス
    """
    response = client.get(
        "/resolve?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ", follow_redirects=False
    )

    # 307 Temporary Redirectまたはエラーが返されることを確認
    assert response.status_code in [307, 400, 502, 500]


def test_formats_endpoint_requires_url_parameter(client):
    """
    /formatsエンドポイントがURLパラメータを要求することを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/formats")
    # urlパラメータがない場合は422エラー
    assert response.status_code == 422


def test_formats_endpoint_with_invalid_url(client):
    """
    /formatsエンドポイントに不正なURLを渡した場合のエラーハンドリングを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/formats?url=invalid_url")
    # 不正なURLの場合は400 Bad Request
    assert response.status_code == 400


def test_download_endpoint_requires_url_parameter(client):
    """
    /downloadエンドポイントがURLパラメータを要求することを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/download")
    # urlパラメータがない場合は422エラー
    assert response.status_code == 422


def test_download_endpoint_with_invalid_url(client):
    """
    /downloadエンドポイントに不正なURLを渡した場合のエラーハンドリングを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/download?url=invalid_url")
    # csrf_tokenパラメータが必須なので422 Unprocessable Entity、
    # またはURLが不正な場合は400 Bad Request、502エラー
    assert response.status_code in [400, 422, 502, 500]


@pytest.mark.skip(reason="実際のYouTube APIを呼び出すため統合テストではスキップ")
def test_download_endpoint_with_real_youtube_url(client):
    """
    /downloadエンドポイントが実際のYouTube URLで動作することを確認（スキップ）

    このテストは実際のYouTube APIを呼び出すため、CI環境では実行をスキップします。
    手動テストやE2Eテストで使用することを想定しています。

    Args:
        client: TestClientインスタンス
    """
    response = client.get(
        "/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ", follow_redirects=False
    )

    # 307 Temporary Redirectまたはエラーが返されることを確認
    assert response.status_code in [307, 400, 502, 500]


def test_player_page(client):
    """
    プレイヤーページ（GET /player）が正常に動作することを確認

    プレイヤーUIのHTMLページが正しく返されることをテストします。

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/player")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    html_content = response.text
    assert "<!DOCTYPE html>" in html_content
    assert "playlist-url-input" in html_content
    # プレイヤーページではプレイヤー用のスクリプトのみ読み込む
    assert "/static/js/player.js" in html_content
    assert "/static/js/app.js" not in html_content


def test_player_page_allows_stream_media_in_csp(client):
    """
    プレイヤーが解決済みストリームを再生できるCSPが設定されていることを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/player")

    csp = response.headers["content-security-policy"]
    assert "media-src 'self' https://*.googlevideo.com" in csp


def test_playlist_endpoint_requires_url_parameter(client):
    """
    /playlistエンドポイントがURLパラメータを要求することを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/playlist")
    # urlパラメータがない場合は422エラー
    assert response.status_code == 422


def test_playlist_endpoint_with_invalid_url(client):
    """
    /playlistエンドポイントに不正なURLを渡した場合のエラーハンドリングを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/playlist?url=invalid_url")
    # 不正なURLの場合は400 Bad Request
    assert response.status_code == 400


def test_playlist_endpoint_without_list_parameter(client):
    """
    /playlistエンドポイントにlistパラメータのないURLを渡した場合の動作を確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/playlist?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    # プレイリストIDが抽出できない場合は400 Bad Request
    assert response.status_code == 400


def test_playlist_stream_endpoint_requires_video_id_parameter(client):
    """
    /playlist/streamエンドポイントがvideo_idパラメータを要求することを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/playlist/stream")
    # video_idパラメータがない場合は422エラー
    assert response.status_code == 422


def test_playlist_stream_endpoint_with_invalid_video_id(client):
    """
    /playlist/streamエンドポイントに不正な動画IDを渡した場合のエラーハンドリングを確認

    Args:
        client: TestClientインスタンス
    """
    response = client.get("/playlist/stream?video_id=invalid")
    # 動画ID形式が不正な場合は400 Bad Request
    assert response.status_code == 400
