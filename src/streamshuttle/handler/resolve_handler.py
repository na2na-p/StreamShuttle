"""
YouTube URL解決Handlerモジュール

FastAPIのエンドポイントを提供し、YouTube URLを解決してストリームURLへリダイレクトします。
このHandlerはプロキシAPIのメインエンドポイントとして機能します。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from streamshuttle.di.container import get_resolve_youtube_url_use_case
from streamshuttle.shared.config import config
from streamshuttle.shared.exceptions import (
    InvalidUrlError,
    InvalidVideoIdError,
    YouTubeResolverError,
)
from streamshuttle.shared.rate_limiter import limiter
from streamshuttle.usecase.command.resolve_youtube_url_usecase import (
    ResolveYoutubeUrlUseCase,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/resolve")
@limiter.limit(config.RATE_LIMIT_RESOLVE)
async def resolve_url(
    request: Request,
    url: str = Query(..., description="YouTube動画URL"),
    use_case: ResolveYoutubeUrlUseCase = Depends(get_resolve_youtube_url_use_case),
) -> RedirectResponse:
    """
    YouTube URLを解決し、ストリームURLへリダイレクトします

    VRChat動画プレイヤー（YamaPlayer等）専用のエンドポイントです。
    YouTube動画URLを受け取り、yt-dlpを使用して直接ストリームURLを解決し、
    HTTPステータスコード307 Temporary Redirectで解決済みストリームURLへリダイレクトします。

    キャッシュが有効な場合はキャッシュから返され、期限切れの場合は再解決されます。

    レート制限: IPアドレスごとに10リクエスト/分

    Args:
        request: FastAPI Request（レート制限用）
        url: YouTube動画URL（必須クエリパラメータ）
        use_case: ResolveYoutubeUrlUseCase（DIコンテナから注入）

    Returns:
        RedirectResponse: 解決済みストリームURLへの307 Temporary Redirectリダイレクト

    Raises:
        HTTPException: 以下の場合にHTTPエラーを返します
            - 400 Bad Request: ビデオIDまたはURLが無効な形式、または長さ制限を超過
            - 429 Too Many Requests: レート制限を超過
            - 502 Bad Gateway: YouTube APIへのアクセス失敗、URL解決失敗
            - 500 Internal Server Error: その他の予期しないエラー
    """
    try:
        # URL長制限チェック（DoS攻撃対策）
        if len(url) > config.MAX_URL_LENGTH:
            logger.warning(
                f"URL length exceeds maximum: url_length={len(url)}, max={config.MAX_URL_LENGTH}"
            )
            raise InvalidUrlError(f"URL長が制限を超えています（最大: {config.MAX_URL_LENGTH}文字）")

        resolved_url = await use_case.execute(url)
        return RedirectResponse(url=resolved_url, status_code=307)
    except InvalidVideoIdError:
        # ログに詳細を記録
        logger.warning(f"Invalid video ID: url={url}", exc_info=True)
        # クライアントには簡潔なメッセージ
        raise HTTPException(status_code=400, detail="Invalid video ID format.")
    except InvalidUrlError:
        # ログに詳細を記録
        logger.warning(f"Invalid URL: url={url}", exc_info=True)
        # クライアントには簡潔なメッセージ
        raise HTTPException(status_code=400, detail="Invalid URL format.")
    except YouTubeResolverError:
        # ログに詳細を記録（外部サービスエラーの詳細は内部のみ）
        logger.error(f"Failed to resolve URL: url={url}", exc_info=True)
        # クライアントには汎用メッセージ（外部サービスの詳細を露出しない）
        raise HTTPException(status_code=502, detail="Failed to resolve URL from YouTube.")
    except Exception:
        # ログには詳細を記録（本番環境ではログ管理システムで確認）
        logger.error(f"Unexpected error in resolve_url: url={url}", exc_info=True)
        # クライアントには汎用メッセージのみ（内部構造の露出を防ぐ）
        raise HTTPException(
            status_code=500, detail="An internal error occurred. Please try again later."
        )
