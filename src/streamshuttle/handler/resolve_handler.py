"""
URL解決Handlerモジュール

FastAPIのエンドポイントを提供し、YouTube/Twitch URLを解決してストリームURLへリダイレクトします。
このHandlerはプロキシAPIのメインエンドポイントとして機能します。
proxyパラメータを使用することで、リダイレクトの代わりにプロキシ方式でストリーミングできます。
"""

import logging
from collections.abc import AsyncIterator
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, StreamingResponse

from streamshuttle.di.container import (
    get_resolve_twitch_url_use_case,
    get_resolve_youtube_url_use_case,
)
from streamshuttle.domain.model.twitch_url import TwitchUrl
from streamshuttle.domain.model.youtube_url import YoutubeUrl
from streamshuttle.shared.config import config
from streamshuttle.shared.exceptions import (
    HlsNotSupportedError,
    InvalidUrlError,
    InvalidVideoIdError,
    TwitchResolverError,
    YouTubeResolverError,
)
from streamshuttle.shared.rate_limiter import limiter
from streamshuttle.shared.validators.url_validator import UrlValidator
from streamshuttle.usecase.command.resolve_twitch_url_usecase import (
    ResolveTwitchUrlUseCase,
)
from streamshuttle.usecase.command.resolve_youtube_url_usecase import (
    ResolveYoutubeUrlUseCase,
)

router = APIRouter()
logger = logging.getLogger(__name__)
url_validator = UrlValidator(max_length=config.security.max_url_length)

YOUTUBE_DOMAINS = ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be")
TWITCH_DOMAINS = ("twitch.tv", "www.twitch.tv", "m.twitch.tv", "clips.twitch.tv")

PROXY_CHUNK_SIZE = 64 * 1024  # 64KB chunks for streaming
PROXY_TIMEOUT = httpx.Timeout(30.0, connect=10.0)

# Headers to forward from upstream response
FORWARDED_HEADERS = (
    "content-type",
    "content-length",
    "accept-ranges",
    "content-range",
)


def _get_url_domain(url: str) -> str | None:
    """URLからドメインを取得する"""
    try:
        parsed = urlparse(url)
        return parsed.hostname
    except Exception:
        return None


@router.get("/resolve")
@limiter.limit(config.rate_limit.resolve)
async def resolve_url(
    request: Request,
    url: str = Query(..., description="YouTube/Twitch動画URL"),
    hls: bool = Query(False, description="HLS形式の使用（デフォルト: false、Twitchでは無視）"),
    youtube_use_case: ResolveYoutubeUrlUseCase = Depends(get_resolve_youtube_url_use_case),
    twitch_use_case: ResolveTwitchUrlUseCase = Depends(get_resolve_twitch_url_use_case),
) -> RedirectResponse:
    """
    動画URLを解決し、ストリームURLへリダイレクトします

    VRChat動画プレイヤー（YamaPlayer等）専用のエンドポイントです。
    YouTube/Twitch動画URLを受け取り、yt-dlpを使用して直接ストリームURLを解決し、
    HTTPステータスコード307 Temporary Redirectで解決済みストリームURLへリダイレクトします。

    URLのドメインから自動的にYouTube/Twitchを判別します。

    キャッシュが有効な場合はキャッシュから返され、期限切れの場合は再解決されます。

    注意: TwitchはHLS形式のみをサポートするため、AVPro Video Player対応のワールドが必要です。

    レート制限: IPアドレスごとに10リクエスト/分

    Args:
        request: FastAPI Request（レート制限用）
        url: YouTube/Twitch動画URL（必須クエリパラメータ）
        hls: HLS形式を使用するか（デフォルト: false、Twitchでは無視）
            - true: HLS形式を使用
            - false: プログレッシブダウンロードのみ使用（YouTubeのみ）
        youtube_use_case: ResolveYoutubeUrlUseCase（DIコンテナから注入）
        twitch_use_case: ResolveTwitchUrlUseCase（DIコンテナから注入）

    Returns:
        RedirectResponse: 解決済みストリームURLへの307 Temporary Redirectリダイレクト

    Raises:
        HTTPException: 以下の場合にHTTPエラーを返します
            - 400 Bad Request: ビデオIDまたはURLが無効な形式、または長さ制限を超過、HLS形式拒否
            - 429 Too Many Requests: レート制限を超過
            - 502 Bad Gateway: APIへのアクセス失敗、URL解決失敗
            - 500 Internal Server Error: その他の予期しないエラー
    """
    try:
        url_validator.validate_length(url)

        domain = _get_url_domain(url)

        if domain in TWITCH_DOMAINS:
            twitch_url = TwitchUrl(_value=url)
            resolved_url = await twitch_use_case.execute(twitch_url)
        elif domain in YOUTUBE_DOMAINS:
            youtube_url = YoutubeUrl(_value=url)
            resolved_url = await youtube_use_case.execute(youtube_url, hls=hls)
        else:
            raise InvalidUrlError(f"Unsupported domain: {domain}")

        return RedirectResponse(url=resolved_url, status_code=307)
    except InvalidVideoIdError:
        logger.warning(f"Invalid video ID: url={url}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid video ID format.")
    except InvalidUrlError:
        logger.warning(f"Invalid URL: url={url}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid URL format.")
    except HlsNotSupportedError:
        logger.warning(f"HLS format rejected: url={url}, hls=False")
        raise HTTPException(
            status_code=400,
            detail="This video requires HLS support. Set hls=true or use a compatible player.",
        )
    except (YouTubeResolverError, TwitchResolverError):
        logger.error(f"Failed to resolve URL: url={url}", exc_info=True)
        raise HTTPException(status_code=502, detail="Failed to resolve URL.")
    except Exception:
        logger.error(f"Unexpected error in resolve_url: url={url}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An internal error occurred. Please try again later."
        )
