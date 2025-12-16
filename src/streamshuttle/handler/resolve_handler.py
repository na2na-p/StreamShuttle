"""
YouTube URL解決Handlerモジュール

FastAPIのエンドポイントを提供し、YouTube URLを解決してストリームURLへリダイレクトします。
このHandlerはプロキシAPIのメインエンドポイントとして機能します。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from streamshuttle.di.container import get_resolve_youtube_url_use_case
from streamshuttle.domain.model.youtube_url import YoutubeUrl
from streamshuttle.shared.config import config
from streamshuttle.shared.exceptions import (
    HlsNotSupportedError,
    InvalidUrlError,
    InvalidVideoIdError,
    YouTubeResolverError,
)
from streamshuttle.shared.rate_limiter import limiter
from streamshuttle.shared.validators.url_validator import UrlValidator
from streamshuttle.usecase.command.resolve_youtube_url_usecase import (
    ResolveYoutubeUrlUseCase,
)

router = APIRouter()
logger = logging.getLogger(__name__)
url_validator = UrlValidator(max_length=config.security.max_url_length)


@router.get("/resolve")
@limiter.limit(config.rate_limit.resolve)
async def resolve_url(
    request: Request,
    url: str = Query(..., description="YouTube動画URL"),
    use_hls: bool = Query(False, description="HLS形式の使用（デフォルト: false）"),
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
        use_hls: HLS形式を使用するか（デフォルト: false）
            - true: HLS形式を使用
            - false: プログレッシブダウンロードのみ使用
        use_case: ResolveYoutubeUrlUseCase（DIコンテナから注入）

    Returns:
        RedirectResponse: 解決済みストリームURLへの307 Temporary Redirectリダイレクト

    Raises:
        HTTPException: 以下の場合にHTTPエラーを返します
            - 400 Bad Request: ビデオIDまたはURLが無効な形式、または長さ制限を超過、HLS形式拒否
            - 429 Too Many Requests: レート制限を超過
            - 502 Bad Gateway: YouTube APIへのアクセス失敗、URL解決失敗
            - 500 Internal Server Error: その他の予期しないエラー
    """
    try:
        url_validator.validate_length(url)

        youtube_url = YoutubeUrl(_value=url)
        resolved_url = await use_case.execute(youtube_url, use_hls=use_hls)
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
    except HlsNotSupportedError:
        # ログに詳細を記録
        logger.warning(f"HLS format rejected: url={url}, use_hls=False")
        # クライアントには具体的なメッセージ
        raise HTTPException(
            status_code=400,
            detail="This video requires HLS support. Set use_hls=true or use a compatible player.",
        )
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
