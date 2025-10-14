"""
ダウンロードHandlerモジュール

Web UIからの動画ダウンロード用エンドポイントを提供します。
フォーマット一覧取得とダウンロードURL取得の2つのエンドポイントを提供します。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from streamshuttle.di.container import (
    get_resolve_youtube_url_use_case,
    get_video_formats_use_case,
)
from streamshuttle.shared.config import config
from streamshuttle.shared.csrf_token import generate_csrf_token, verify_csrf_token
from streamshuttle.shared.exceptions import (
    InvalidUrlError,
    InvalidVideoIdError,
    YouTubeResolverError,
)
from streamshuttle.shared.rate_limiter import limiter
from streamshuttle.usecase.command.resolve_youtube_url_usecase import (
    ResolveYoutubeUrlUseCase,
)
from streamshuttle.usecase.query.get_video_formats_usecase import GetVideoFormatsUseCase

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/formats")
@limiter.limit(config.RATE_LIMIT_FORMATS)
async def get_formats(
    request: Request,
    url: str = Query(..., description="YouTube動画URL"),
    use_case: GetVideoFormatsUseCase = Depends(get_video_formats_use_case),
):
    """
    YouTube動画の利用可能なフォーマット一覧を取得します

    指定されたYouTube動画URLの利用可能なフォーマット一覧を取得します。
    各フォーマットにはフォーマットID、品質、コーデック、URLが含まれます。
    この情報をもとに、クライアント側で適切なフォーマットを選択できます。

    レート制限: IPアドレスごとに5リクエスト/分

    Args:
        request: FastAPI Request（レート制限用）
        url: YouTube動画URL（必須クエリパラメータ）
        use_case: GetVideoFormatsUseCase（DIコンテナから注入）

    Returns:
        dict: 以下の形式のJSON
            {
                "formats": [
                    {
                        "format_id": "137",
                        "quality": "1080p",
                        "codec": "avc1",
                        "url": "https://..."
                    },
                    ...
                ],
                "csrf_token": "生成されたCSRFトークン"
            }

    Raises:
        HTTPException: 以下の場合にHTTPエラーを返します
            - 400 Bad Request: URLが無効な形式、または長さ制限を超過
            - 429 Too Many Requests: レート制限を超過
            - 500 Internal Server Error: フォーマット取得に失敗
    """
    try:
        # URL長制限チェック（DoS攻撃対策）
        if len(url) > config.MAX_URL_LENGTH:
            logger.warning(
                f"URL length exceeds maximum in get_formats: "
                f"url_length={len(url)}, max={config.MAX_URL_LENGTH}"
            )
            raise InvalidUrlError(
                f"URL長が制限を超えています（最大: {config.MAX_URL_LENGTH}文字）"
            )

        formats = await use_case.execute(url)
        csrf_token = generate_csrf_token()
        return {
            "formats": [f.model_dump() for f in formats],
            "csrf_token": csrf_token
        }
    except InvalidUrlError:
        # ログに詳細を記録
        logger.warning(f"Invalid URL in get_formats: url={url}", exc_info=True)
        # クライアントには簡潔なメッセージ
        raise HTTPException(status_code=400, detail="Invalid URL format.")
    except Exception:
        # ログには詳細を記録（本番環境ではログ管理システムで確認）
        logger.error(
            f"Unexpected error in get_formats: url={url}",
            exc_info=True
        )
        # クライアントには汎用メッセージのみ（内部構造の露出を防ぐ）
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Please try again later."
        )


@router.get("/download")
@limiter.limit(config.RATE_LIMIT_DOWNLOAD)
async def download(
    request: Request,
    url: str = Query(..., description="YouTube動画URL"),
    csrf_token: str = Query(..., description="CSRFトークン"),
    use_case: ResolveYoutubeUrlUseCase = Depends(get_resolve_youtube_url_use_case),
) -> RedirectResponse:
    """
    ダウンロード用のYouTube URLを解決し、ストリームURLへリダイレクトします

    レート制限: IPアドレスごとに5リクエスト/分

    Args:
        request: FastAPI Request（レート制限用）
        url: YouTube動画URL
        csrf_token: CSRFトークン
        use_case: ResolveYoutubeUrlUseCase（DIコンテナから注入）

    Returns:
        RedirectResponse: 解決済みストリームURLへの307リダイレクト

    Raises:
        HTTPException: 以下の場合にHTTPエラーを返します
            - 400 Bad Request: ビデオIDまたはURLが無効な形式、または長さ制限を超過
            - 403 Forbidden: CSRFトークンが無効または期限切れ、リクエスト元が不正
            - 429 Too Many Requests: レート制限を超過
            - 502 Bad Gateway: YouTube APIへのアクセス失敗、URL解決失敗
            - 500 Internal Server Error: その他の予期しないエラー
    """
    try:
        # CSRFトークン検証
        if not verify_csrf_token(csrf_token):
            logger.warning(f"Invalid CSRF token in download: url={url}")
            raise HTTPException(status_code=403, detail="Invalid or expired CSRF token.")

        # Refererチェック
        referer = request.headers.get("referer", "")
        if not referer or not any(
            referer.startswith(origin) for origin in [
                str(request.base_url),
                *config.ALLOWED_ORIGINS
            ]
        ):
            logger.warning(f"Invalid referer in download: referer={referer}, url={url}")
            raise HTTPException(status_code=403, detail="Invalid request origin.")

        # URL長制限チェック（DoS攻撃対策）
        if len(url) > config.MAX_URL_LENGTH:
            logger.warning(
                f"URL length exceeds maximum in download: "
                f"url_length={len(url)}, max={config.MAX_URL_LENGTH}"
            )
            raise InvalidUrlError(
                f"URL長が制限を超えています（最大: {config.MAX_URL_LENGTH}文字）"
            )

        resolved_url = await use_case.execute(url)
        return RedirectResponse(url=resolved_url, status_code=307)
    except HTTPException:
        raise
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
        logger.error(
            f"Unexpected error in download: url={url}",
            exc_info=True
        )
        # クライアントには汎用メッセージのみ（内部構造の露出を防ぐ）
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Please try again later."
        )
