"""
ダウンロードHandlerモジュール

Web UIからの動画ダウンロード用エンドポイントを提供します。
フォーマット一覧取得とダウンロードURL取得の2つのエンドポイントを提供します。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from streamshuttle.di.container import (
    get_cached_format_url_use_case,
    get_resolve_youtube_url_use_case,
    get_video_formats_use_case,
)
from streamshuttle.domain.model.youtube_url import YoutubeUrl
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
from streamshuttle.usecase.query.get_cached_format_url_usecase import (
    GetCachedFormatUrlUseCase,
)
from streamshuttle.usecase.query.get_video_formats_usecase import GetVideoFormatsUseCase

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/formats")
@limiter.limit(config.rate_limit.formats)
async def get_formats(
    request: Request,
    url: str = Query(..., description="YouTube動画URL"),
    use_case: GetVideoFormatsUseCase = Depends(get_video_formats_use_case),
):
    """
    YouTube動画の利用可能なフォーマット一覧と動画情報を取得します

    指定されたYouTube動画URLの利用可能なフォーマット一覧と、
    動画のタイトル・サムネイルなどの基本情報を取得します。
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
                "video_info": {
                    "video_id": "dQw4w9WgXcQ",
                    "title": "動画タイトル",
                    "thumbnail_url": "https://i.ytimg.com/vi/..."
                },
                "formats": [
                    {
                        "format_id": "137",
                        "quality": "1080p",
                        "codec": "avc1",
                        "url": "https://...",
                        "has_audio": false,
                        "has_video": true
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
        if len(url) > config.security.max_url_length:
            logger.warning(
                f"URL length exceeds maximum in get_formats: "
                f"url_length={len(url)}, max={config.security.max_url_length}"
            )
            raise InvalidUrlError(
                f"URL長が制限を超えています（最大: {config.security.max_url_length}文字）"
            )

        video_info, formats = await use_case.execute(url)

        csrf_token = generate_csrf_token()
        return {
            "video_info": video_info.model_dump(),
            "formats": [f.model_dump() for f in formats],
            "csrf_token": csrf_token,
        }
    except InvalidUrlError:
        # ログに詳細を記録
        logger.warning(f"Invalid URL in get_formats: url={url}", exc_info=True)
        # クライアントには簡潔なメッセージ
        raise HTTPException(status_code=400, detail="Invalid URL format.")
    except Exception:
        # ログには詳細を記録（本番環境ではログ管理システムで確認）
        logger.error(f"Unexpected error in get_formats: url={url}", exc_info=True)
        # クライアントには汎用メッセージのみ（内部構造の露出を防ぐ）
        raise HTTPException(
            status_code=500, detail="An internal error occurred. Please try again later."
        )


@router.get("/download")
@limiter.limit(config.rate_limit.download)
async def download(
    request: Request,
    url: str = Query(..., description="YouTube動画URL"),
    csrf_token: str = Query(..., description="CSRFトークン"),
    format_id: str | None = Query(None, description="フォーマットID（オプショナル）"),
    resolve_use_case: ResolveYoutubeUrlUseCase = Depends(get_resolve_youtube_url_use_case),
    cached_url_use_case: GetCachedFormatUrlUseCase = Depends(get_cached_format_url_use_case),
) -> RedirectResponse:
    """
    ダウンロード用のYouTube URLを解決し、ストリームURLへリダイレクトします

    レート制限: IPアドレスごとに5リクエスト/分

    Args:
        request: FastAPI Request（レート制限用）
        url: YouTube動画URL
        csrf_token: CSRFトークン
        format_id: フォーマットID（オプショナル）
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
        # X-Forwarded-Hostヘッダーからオリジンを構築
        forwarded_host = request.headers.get("x-forwarded-host")
        if forwarded_host:
            forwarded_proto = request.headers.get("x-forwarded-proto", "https")
            forwarded_origin = f"{forwarded_proto}://{forwarded_host}/"
            allowed_origins = [
                str(request.base_url),
                forwarded_origin,
                *config.cors.allowed_origins,
            ]
        else:
            allowed_origins = [str(request.base_url), *config.cors.allowed_origins]

        referer = request.headers.get("referer", "")
        if not referer or not any(referer.startswith(origin) for origin in allowed_origins):
            logger.warning(
                f"Invalid referer in download: referer={referer}, "
                f"allowed_origins={allowed_origins}, url={url}"
            )
            raise HTTPException(status_code=403, detail="Invalid request origin.")

        # URL長制限チェック（DoS攻撃対策）
        if len(url) > config.security.max_url_length:
            logger.warning(
                f"URL length exceeds maximum in download: "
                f"url_length={len(url)}, max={config.security.max_url_length}"
            )
            raise InvalidUrlError(
                f"URL長が制限を超えています（最大: {config.security.max_url_length}文字）"
            )

        # まずキャッシュからURLを取得（format_idが指定されている場合のみ）
        resolved_url = None
        if format_id:
            try:
                youtube_url_obj = YoutubeUrl(_value=url)
                video_id = youtube_url_obj.extract_video_id()
                cached_url = await cached_url_use_case.execute(str(video_id), format_id)

                if cached_url:
                    logger.info(
                        f"Using cached URL for format: "
                        f"video_id={str(video_id)}, format_id={format_id}"
                    )
                    resolved_url = cached_url
            except (InvalidUrlError, InvalidVideoIdError) as e:
                # キャッシュ取得失敗はログのみ（フォールバックで処理）
                logger.warning(
                    f"Failed to get cached URL: url={url}, format_id={format_id}, error={e}"
                )

        # キャッシュミスの場合はyt-dlpで解決（フォールバック）
        if not resolved_url:
            logger.info(f"Cache miss, resolving URL with yt-dlp: url={url}, format_id={format_id}")
            youtube_url_for_resolve = YoutubeUrl(_value=url)
            resolved_url = await resolve_use_case.execute(youtube_url_for_resolve, format_id)

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
        logger.error(f"Unexpected error in download: url={url}", exc_info=True)
        # クライアントには汎用メッセージのみ（内部構造の露出を防ぐ）
        raise HTTPException(
            status_code=500, detail="An internal error occurred. Please try again later."
        )
