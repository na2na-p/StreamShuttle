"""
ResolveHandler ユニットテスト

ResolveHandlerのエンドポイント動作を検証するユニットテストです。
FastAPI TestClientを使用して、HTTPリクエスト/レスポンスの動作を検証します。
"""

import asyncio
from unittest.mock import AsyncMock

import pytest
import yt_dlp
from fastapi import FastAPI
from fastapi.testclient import TestClient

from streamshuttle.di.container import (
    get_resolve_twitch_url_use_case,
    get_resolve_youtube_url_use_case,
)
from streamshuttle.domain.model.hls_mode import HlsMode
from streamshuttle.domain.model.twitch_url.twitch_url import TwitchUrl
from streamshuttle.domain.model.youtube_url.youtube_url import YoutubeUrl
from streamshuttle.handler.resolve_handler import router
from streamshuttle.infrastructure.external.youtube_resolver import YoutubeResolver
from streamshuttle.shared.exceptions import (
    HlsMasterUnavailableError,
    HlsNotSupportedError,
    InvalidUrlError,
    InvalidVideoIdError,
    TwitchResolverError,
    VideoUnavailableError,
    YouTubeResolverError,
)
from streamshuttle.usecase.command.resolve_twitch_url_usecase import ResolveTwitchUrlUseCase
from streamshuttle.usecase.command.resolve_youtube_url_usecase import ResolveYoutubeUrlUseCase


class _EmptyStreamUrlRepository:
    async def find_by_video_id(self, _video_id, _hls):
        return None

    async def save(self, _stream_url, _hls):
        pass


class _RecordingYoutubeUseCase:
    def __init__(self, use_case):
        self._use_case = use_case
        self.error = None

    async def execute(self, *args, **kwargs):
        try:
            return await self._use_case.execute(*args, **kwargs)
        except Exception as error:
            self.error = error
            raise


def _real_youtube_client(app):
    use_case = _RecordingYoutubeUseCase(
        ResolveYoutubeUrlUseCase(_EmptyStreamUrlRepository(), YoutubeResolver())
    )
    app.dependency_overrides[get_resolve_youtube_url_use_case] = lambda: use_case
    return TestClient(app), use_case


def _replace_extract_info(monkeypatch, outcomes):
    calls = []
    outcome_iterator = iter(outcomes)

    def extract_info(self, _url, download):
        calls.append(self.params)
        outcome = next(outcome_iterator)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(yt_dlp.YoutubeDL, "extract_info", extract_info)
    return calls


@pytest.fixture
def app():
    """
    テスト用FastAPIアプリケーションを作成します

    Returns:
        FastAPI: ResolveHandlerのルーターを含むFastAPIアプリケーション
    """
    from streamshuttle.shared.rate_limiter import limiter

    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(router)
    limiter.enabled = False
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
def mock_twitch_use_case():
    """
    モックされたResolveTwitchUrlUseCaseを作成します

    Returns:
        AsyncMock: ResolveTwitchUrlUseCaseのモック
    """
    return AsyncMock(spec=ResolveTwitchUrlUseCase)


@pytest.fixture
def client(app, mock_use_case, mock_twitch_use_case):
    """
    テスト用クライアントを作成します

    依存性オーバーライドを使用して、UseCaseをモックに置き換えます。

    Args:
        app: FastAPIアプリケーション
        mock_use_case: モックされたYouTube UseCase
        mock_twitch_use_case: モックされたTwitch UseCase

    Returns:
        TestClient: FastAPI TestClient
    """
    app.dependency_overrides[get_resolve_youtube_url_use_case] = lambda: mock_use_case
    app.dependency_overrides[get_resolve_twitch_url_use_case] = lambda: mock_twitch_use_case
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
    mock_use_case.execute.assert_called_once_with(YoutubeUrl(youtube_url), hls=HlsMode.DISABLED)


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


def test_resolve_url_with_youtube_resolver_error(
    client, mock_use_case, caplog, capsys, monkeypatch
):
    """
    異常系: YouTube解決エラーの場合、502 Bad Gatewayが返されることを検証します

    UseCaseがYouTubeResolverErrorを投げる場合、
    エンドポイントは502 Bad Gatewayを返し、
    エラーメッセージが含まれることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    secret = "signature=synthetic-secret-token"

    def report_error(self, _url, download):
        self.report_error(f"synthetic yt-dlp error: {secret}")

    monkeypatch.setattr(yt_dlp.YoutubeDL, "extract_info", report_error)
    with pytest.raises(YouTubeResolverError) as exc_info:
        asyncio.run(YoutubeResolver().resolve_url(youtube_url))

    resolver_error = exc_info.value
    mock_use_case.execute.side_effect = resolver_error

    # Act
    with caplog.at_level("ERROR"):
        response = client.get(f"/resolve?url={youtube_url}")

    # Assert
    assert response.status_code == 502
    assert "Failed to resolve URL" in response.json()["detail"]
    captured = capsys.readouterr()
    assert secret not in captured.out
    assert secret not in captured.err
    assert secret not in caplog.text
    assert secret not in response.text
    assert "platform=youtube" in caplog.text
    assert "video_id=dQw4w9WgXcQ" in caplog.text


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
    mock_use_case.execute.assert_called_once_with(YoutubeUrl(youtube_url), hls=HlsMode.DISABLED)


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


def test_resolve_url_with_hls_true(client, mock_use_case):
    """
    正常系: hls=trueの場合、UseCaseにhls=Trueが渡されることを検証します

    hlsパラメーターがtrueの場合、
    UseCaseのexecuteメソッドにhls=Trueが渡されることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    resolved_url = "https://rr1---sn-example.googlevideo.com/videoplayback?..."
    mock_use_case.execute.return_value = resolved_url

    # Act
    response = client.get(f"/resolve?url={youtube_url}&hls=true", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == resolved_url
    mock_use_case.execute.assert_called_once_with(YoutubeUrl(youtube_url), hls=HlsMode.ENABLED)


def test_resolve_url_with_hls_false(client, mock_use_case):
    """
    正常系: hls=falseの場合、UseCaseにhls=Falseが渡されることを検証します

    hlsパラメーターがfalseの場合（またはデフォルト）、
    UseCaseのexecuteメソッドにhls=Falseが渡されることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    resolved_url = "https://rr1---sn-example.googlevideo.com/videoplayback?..."
    mock_use_case.execute.return_value = resolved_url

    # Act
    response = client.get(f"/resolve?url={youtube_url}&hls=false", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == resolved_url
    mock_use_case.execute.assert_called_once_with(YoutubeUrl(youtube_url), hls=HlsMode.DISABLED)


@pytest.mark.parametrize(
    ("hls", "expected_mode"),
    [
        pytest.param("true", HlsMode.ENABLED, id="true"),
        pytest.param("1", HlsMode.ENABLED, id="1"),
        pytest.param("t", HlsMode.ENABLED, id="t"),
        pytest.param("yes", HlsMode.ENABLED, id="yes"),
        pytest.param("y", HlsMode.ENABLED, id="y"),
        pytest.param("on", HlsMode.ENABLED, id="on"),
        pytest.param("TRUE", HlsMode.ENABLED, id="大文字 true"),
        pytest.param("T", HlsMode.ENABLED, id="大文字 t"),
        pytest.param("Y", HlsMode.ENABLED, id="大文字 y"),
        pytest.param("false", HlsMode.DISABLED, id="false"),
        pytest.param("0", HlsMode.DISABLED, id="0"),
        pytest.param("f", HlsMode.DISABLED, id="f"),
        pytest.param("no", HlsMode.DISABLED, id="no"),
        pytest.param("n", HlsMode.DISABLED, id="n"),
        pytest.param("off", HlsMode.DISABLED, id="off"),
        pytest.param("FALSE", HlsMode.DISABLED, id="大文字 false"),
        pytest.param("F", HlsMode.DISABLED, id="大文字 f"),
        pytest.param("N", HlsMode.DISABLED, id="大文字 n"),
    ],
)
def test_resolve_url_preserves_preexisting_boolean_hls_values(
    client, mock_use_case, hls, expected_mode
):
    mock_use_case.execute.return_value = "https://example.com/video.mp4"

    response = client.get(
        f"/resolve?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&hls={hls}",
        follow_redirects=False,
    )

    assert response.status_code == 307
    mock_use_case.execute.assert_called_once_with(
        YoutubeUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), hls=expected_mode
    )


def test_resolve_url_with_hls_master_redirects_to_hls_master(client, mock_use_case):
    manifest_url = "https://manifest.googlevideo.com/api/manifest/hls_variant/expire/4102444800"
    mock_use_case.execute.return_value = manifest_url

    response = client.get(
        "/resolve?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&hls=master",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == manifest_url
    mock_use_case.execute.assert_called_once_with(
        YoutubeUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), hls=HlsMode.MASTER
    )


def test_resolve_url_with_hls_master_does_not_retry_temporary_format_error(app, monkeypatch):
    client, use_case = _real_youtube_client(app)
    calls = _replace_extract_info(
        monkeypatch,
        [
            yt_dlp.utils.DownloadError(
                "Requested format is not available. HTTP Error 429: Too Many Requests"
            ),
            yt_dlp.utils.DownloadError("Requested format is not available"),
        ],
    )

    response = client.get(
        "/resolve?url=https://www.youtube.com/watch?v=CbdWElnmJIY&hls=master",
        follow_redirects=False,
    )

    assert response.status_code == 502
    assert type(use_case.error) is YouTubeResolverError
    assert len(calls) == 1


def test_resolve_url_with_hls_master_returns_bad_gateway_for_captcha(app, monkeypatch):
    client, use_case = _real_youtube_client(app)
    calls = _replace_extract_info(
        monkeypatch,
        [
            yt_dlp.utils.DownloadError(
                "Video unavailable. YouTube is requiring a captcha challenge before playback"
            )
        ],
    )

    response = client.get(
        "/resolve?url=https://www.youtube.com/watch?v=CbdWElnmJIY&hls=master",
        follow_redirects=False,
    )

    assert response.status_code == 502
    assert type(use_case.error) is YouTubeResolverError
    assert len(calls) == 1


def test_resolve_url_with_hls_master_keeps_second_temporary_error_as_bad_gateway(app, monkeypatch):
    client, _ = _real_youtube_client(app)
    calls = _replace_extract_info(
        monkeypatch,
        [
            yt_dlp.utils.DownloadError("Requested format is not available"),
            yt_dlp.utils.DownloadError(
                "Requested format is not available. HTTP Error 429: Too Many Requests"
            ),
        ],
    )

    response = client.get(
        "/resolve?url=https://www.youtube.com/watch?v=CbdWElnmJIY&hls=master",
        follow_redirects=False,
    )

    assert response.status_code == 502
    assert len(calls) == 2


@pytest.mark.parametrize(
    ("second_error_message", "status_code", "detail"),
    [
        pytest.param(
            "ERROR: Unable to download API page: <urlopen error timed out>",
            502,
            "Failed to resolve URL.",
            id="最後がタイムアウト",
        ),
        pytest.param(
            "Sign in to confirm you are not a bot",
            502,
            "Failed to resolve URL.",
            id="最後が認証失敗",
        ),
        pytest.param(
            "Video unavailable. YouTube is requiring a captcha challenge before playback",
            502,
            "Failed to resolve URL.",
            id="最後がCAPTCHA要求",
        ),
        pytest.param(
            "Requested format is not available",
            404,
            "hls_master_unavailable",
            id="最後が形式不足",
        ),
        pytest.param(
            "Private video. Sign in if you've been granted access to this video",
            404,
            "video_unavailable",
            id="最後が恒久的な動画取得不能",
        ),
        pytest.param(
            "This video has been removed",
            404,
            "video_unavailable",
            id="最後が削除済み動画",
        ),
    ],
)
def test_resolve_url_with_hls_master_classifies_fallback_failure_by_last_attempt(
    app, monkeypatch, second_error_message, status_code, detail
):
    client, _ = _real_youtube_client(app)
    calls = _replace_extract_info(
        monkeypatch,
        [
            yt_dlp.utils.DownloadError("Requested format is not available"),
            yt_dlp.utils.DownloadError(second_error_message),
        ],
    )

    response = client.get(
        "/resolve?url=https://www.youtube.com/watch?v=CbdWElnmJIY&hls=master",
        follow_redirects=False,
    )

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}
    assert len(calls) == 2


def test_resolve_url_with_hls_master_redirects_after_format_fallback(app, monkeypatch):
    client, _ = _real_youtube_client(app)
    manifest_url = "https://manifest.googlevideo.com/api/manifest/hls_variant/expire/4102444800"
    calls = _replace_extract_info(
        monkeypatch,
        [
            yt_dlp.utils.DownloadError("Requested format is not available"),
            {"manifest_url": manifest_url},
        ],
    )

    response = client.get(
        "/resolve?url=https://www.youtube.com/watch?v=CbdWElnmJIY&hls=master",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == manifest_url
    assert len(calls) == 2


@pytest.mark.parametrize(
    ("first_error_message", "hls_query", "expected_url"),
    [
        pytest.param(
            "Requested format is not available",
            "",
            "https://example.com/default.mp4",
            id="hlsなし・形式不足",
        ),
        pytest.param(
            "Requested format is not available",
            "&hls=true",
            "https://example.com/enabled.m3u8",
            id="hls=true・形式不足",
        ),
        pytest.param(
            "Requested format is not available. HTTP Error 429: Too Many Requests",
            "",
            "https://example.com/default-temporary.mp4",
            id="hlsなし・形式不足と一時エラーの混在",
        ),
        pytest.param(
            "Requested format is not available. HTTP Error 429: Too Many Requests",
            "&hls=true",
            "https://example.com/enabled-temporary.m3u8",
            id="hls=true・形式不足と一時エラーの混在",
        ),
    ],
)
def test_resolve_url_preserves_existing_format_fallback_behavior(
    app, monkeypatch, first_error_message, hls_query, expected_url
):
    client, _ = _real_youtube_client(app)
    calls = _replace_extract_info(
        monkeypatch,
        [
            yt_dlp.utils.DownloadError(first_error_message),
            {"url": expected_url},
        ],
    )

    response = client.get(
        f"/resolve?url=https://www.youtube.com/watch?v=CbdWElnmJIY{hls_query}",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == expected_url
    assert len(calls) == 2


@pytest.mark.parametrize(
    "query",
    [
        "hls=abc&hls=master",
        "hls=master&hls=abc",
        "hls=master&hls=true",
        "hls=true&hls=master",
    ],
)
def test_resolve_url_rejects_duplicate_hls_values(client, mock_use_case, query):
    response = client.get(
        f"/resolve?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&{query}",
        follow_redirects=False,
    )

    assert response.status_code == 400
    mock_use_case.execute.assert_not_called()


def test_resolve_url_leaves_lower_layer_value_error_as_internal_error(
    client, mock_use_case, caplog
):
    mock_use_case.execute.side_effect = ValueError("unexpected lower layer failure")

    with caplog.at_level("ERROR"):
        response = client.get(
            "/resolve?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&hls=master",
            follow_redirects=False,
        )

    assert response.status_code == 500
    assert "An internal error occurred" in response.json()["detail"]
    assert "Unexpected error in resolve_url" in caplog.text


@pytest.mark.parametrize("hls", ["abc", "", "Master"])
def test_resolve_url_rejects_unsupported_hls_value_with_400(client, mock_use_case, hls):
    response = client.get(
        f"/resolve?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&hls={hls}",
        follow_redirects=False,
    )

    assert response.status_code == 400
    mock_use_case.execute.assert_not_called()


def test_resolve_url_returns_hls_master_unavailable(client, mock_use_case):
    mock_use_case.execute.side_effect = HlsMasterUnavailableError()

    response = client.get(
        "/resolve?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&hls=master",
        follow_redirects=False,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "hls_master_unavailable"}


def test_resolve_url_returns_video_unavailable_for_hls_master(client, mock_use_case):
    mock_use_case.execute.side_effect = VideoUnavailableError()

    response = client.get(
        "/resolve?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&hls=master",
        follow_redirects=False,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "video_unavailable"}


@pytest.mark.parametrize(
    ("hls_query", "message"),
    [
        pytest.param(
            "",
            "Private video. Sign in if you've been granted access to this video",
            id="hlsなし・非公開",
        ),
        pytest.param(
            "&hls=false",
            "Private video. Sign in if you've been granted access to this video",
            id="hls=false・非公開",
        ),
        pytest.param(
            "&hls=true",
            "Private video. Sign in if you've been granted access to this video",
            id="hls=true・非公開",
        ),
        pytest.param("", "This video has been removed", id="hlsなし・削除済み"),
        pytest.param("&hls=false", "This video has been removed", id="hls=false・削除済み"),
        pytest.param("&hls=true", "This video has been removed", id="hls=true・削除済み"),
    ],
)
def test_resolve_url_keeps_permanent_video_errors_as_bad_gateway_outside_hls_master(
    app, monkeypatch, hls_query, message
):
    client, _ = _real_youtube_client(app)
    _replace_extract_info(
        monkeypatch,
        [yt_dlp.utils.DownloadError(message)],
    )

    response = client.get(
        f"/resolve?url=https://www.youtube.com/watch?v=CbdWElnmJIY{hls_query}",
        follow_redirects=False,
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Failed to resolve URL."}


def test_resolve_url_with_hls_not_supported_error(client, mock_use_case):
    """
    異常系: HLS形式が拒否された場合、400 Bad Requestが返されることを検証します

    UseCaseがHlsNotSupportedErrorを投げる場合、
    エンドポイントは400 Bad Requestを返し、
    エラーメッセージが含まれることを確認します。
    """
    # Arrange
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_use_case.execute.side_effect = HlsNotSupportedError("HLS形式がサポートされていません")

    # Act
    response = client.get(f"/resolve?url={youtube_url}&hls=false")

    # Assert
    assert response.status_code == 400
    assert "HLS support" in response.json()["detail"]
    assert "hls=true" in response.json()["detail"]


def test_resolve_twitch_url_success(client, mock_twitch_use_case):
    """
    正常系: Twitch URLの解決が成功し、307リダイレクトが返されることを検証します

    UseCaseが正常に解決されたURLを返す場合、
    エンドポイントは307 Temporary Redirectを返し、
    Locationヘッダーに解決済みURLが設定されることを確認します。
    """
    # Arrange
    twitch_url = "https://www.twitch.tv/ninja"
    resolved_url = "https://video-weaver.example.hls.ttvnw.net/v1/playlist/..."
    mock_twitch_use_case.execute.return_value = resolved_url

    # Act
    response = client.get(f"/resolve?url={twitch_url}", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == resolved_url
    mock_twitch_use_case.execute.assert_called_once_with(TwitchUrl(_value=twitch_url))


def test_resolve_twitch_url_with_resolver_error(client, mock_twitch_use_case):
    """
    異常系: Twitch解決エラーの場合、502 Bad Gatewayが返されることを検証します

    UseCaseがTwitchResolverErrorを投げる場合、
    エンドポイントは502 Bad Gatewayを返し、
    エラーメッセージが含まれることを確認します。
    """
    # Arrange
    twitch_url = "https://www.twitch.tv/ninja"
    mock_twitch_use_case.execute.side_effect = TwitchResolverError(
        "Twitch APIへのアクセスに失敗しました"
    )

    # Act
    response = client.get(f"/resolve?url={twitch_url}")

    # Assert
    assert response.status_code == 502
    assert "Failed to resolve URL" in response.json()["detail"]


def test_resolve_url_with_unsupported_domain(client):
    """
    異常系: サポートされていないドメインの場合、400 Bad Requestが返されることを検証します

    YouTube/Twitch以外のドメインが指定された場合、
    エンドポイントは400 Bad Requestを返し、
    エラーメッセージが含まれることを確認します。
    """
    # Arrange
    unsupported_url = "https://vimeo.com/123456789"

    # Act
    response = client.get(f"/resolve?url={unsupported_url}")

    # Assert
    assert response.status_code == 400
    assert "Invalid URL" in response.json()["detail"]
