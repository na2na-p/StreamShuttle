"""
ダウンロードHandlerモジュール

Web UIからの動画ダウンロード用エンドポイントを提供します。
フォーマット一覧取得とダウンロードURL取得の2つのエンドポイントを提供します。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from streamshuttle.di.container import (
    get_or_resolve_stream_url_use_case,
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
from streamshuttle.shared.validators.referer_validator import RefererValidator
from streamshuttle.shared.validators.url_validator import UrlValidator
from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto
from streamshuttle.usecase.facade.get_or_resolve_stream_url_usecase import (
    GetOrResolveStreamUrlUseCase,
)
from streamshuttle.usecase.query.get_video_formats_usecase import GetVideoFormatsUseCase


class VideoFormatsResponse(BaseModel):
    video_info: VideoInfoDto = Field(..., description="動画基本情報")
    formats: list[VideoFormatDto] = Field(..., description="利用可能なフォーマット一覧")
    csrf_token: str = Field(..., description="CSRFトークン")

router = APIRouter()
logger = logging.getLogger(__name__)
url_validator = UrlValidator(max_length=config.security.max_url_length)
referer_validator = RefererValidator(allowed_origins=config.cors.allowed_origins)


@router.get("/formats", response_model=VideoFormatsResponse)
@limiter.limit(config.rate_limit.formats)
async def get_formats(
    request: Request,
    url: str = Query(..., description="YouTube動画URL"),
    use_case: GetVideoFormatsUseCase = Depends(get_video_formats_use_case),
) -> VideoFormatsResponse:
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
        url_validator.validate_length(url)

        video_info, formats = await use_case.execute(url)

        csrf_token = generate_csrf_token()
        return VideoFormatsResponse(
            video_info=video_info,
            formats=formats,
            csrf_token=csrf_token,
        )
    except InvalidUrlError:
        logger.warning(f"Invalid URL in get_formats: url={url}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid URL format.")
    except Exception:
        logger.error(f"Unexpected error in get_formats: url={url}", exc_info=True)
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
    use_case: GetOrResolveStreamUrlUseCase = Depends(get_or_resolve_stream_url_use_case),
) -> RedirectResponse:
    """
    ダウンロード用のYouTube URLを解決し、ストリームURLへリダイレクトします

    レート制限: IPアドレスごとに5リクエスト/分

    Args:
        request: FastAPI Request（レート制限用）
        url: YouTube動画URL
        csrf_token: CSRFトークン
        format_id: フォーマットID（オプショナル）
        use_case: GetOrResolveStreamUrlUseCase（DIコンテナから注入）

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
        # バリデーション（各バリデータに委譲）
        if not verify_csrf_token(csrf_token):
            logger.warning(f"Invalid CSRF token in download: url={url}")
            raise HTTPException(status_code=403, detail="Invalid or expired CSRF token.")

        referer_validator.validate(request)
        url_validator.validate_length(url)

        # ビジネスロジック（UseCaseに委譲）
        resolved_url = await use_case.execute(url, format_id)

        # レスポンス生成
        return RedirectResponse(url=resolved_url, status_code=307)
    except HTTPException:
        raise
    except InvalidVideoIdError:
        logger.warning(f"Invalid video ID: url={url}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid video ID format.")
    except InvalidUrlError:
        logger.warning(f"Invalid URL: url={url}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid URL format.")
    except YouTubeResolverError:
        logger.error(f"Failed to resolve URL: url={url}", exc_info=True)
        raise HTTPException(status_code=502, detail="Failed to resolve URL from YouTube.")
    except Exception:
        logger.error(f"Unexpected error in download: url={url}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An internal error occurred. Please try again later."
        )
