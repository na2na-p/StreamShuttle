"""
プレイリストHandlerモジュール

Web UIのプレイヤー用エンドポイントを提供します。
プレイリストの動画一覧取得と、再生対象動画のストリームURL解決の
2つのエンドポイントを提供します。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from streamshuttle.di.container import (
    get_playlist_use_case,
    get_resolve_youtube_url_use_case,
)
from streamshuttle.domain.model.stream_url.youtube_video_id import YouTubeVideoId
from streamshuttle.domain.model.youtube_url import YoutubeUrl
from streamshuttle.handler.response.playlist_response import PlaylistResponse
from streamshuttle.handler.response.stream_url_response import StreamUrlResponse
from streamshuttle.shared.config import config
from streamshuttle.shared.exceptions import (
    InvalidPlaylistIdError,
    InvalidUrlError,
    InvalidVideoIdError,
    PlaylistNotFoundError,
    YouTubeResolverError,
)
from streamshuttle.shared.rate_limiter import limiter
from streamshuttle.shared.validators.url_validator import UrlValidator
from streamshuttle.usecase.command.resolve_youtube_url_usecase import (
    ResolveYoutubeUrlUseCase,
)
from streamshuttle.usecase.query.get_playlist_usecase import GetPlaylistUseCase

router = APIRouter()
logger = logging.getLogger(__name__)
url_validator = UrlValidator(max_length=config.security.max_url_length)


@router.get("/playlist")
@limiter.limit(config.rate_limit.playlist)
async def get_playlist(
    request: Request,
    url: str = Query(..., description="YouTube公開プレイリストURL"),
    use_case: GetPlaylistUseCase = Depends(get_playlist_use_case),
) -> PlaylistResponse:
    """
    YouTube公開プレイリストの動画一覧を取得します

    プレイリストURL（listパラメータを含むURL）を受け取り、含まれる動画の
    ID・タイトル・長さ・サムネイルの一覧を返します。
    各動画のストリームURLはこの時点では解決せず、再生時に
    GET /playlist/stream で個別に解決します。

    非公開・削除済みの動画は再生できないため一覧から除外されます。
    動画数が上限（SECURITY_MAX_PLAYLIST_ITEMS）を超える場合は切り捨てられ、
    playlist_info.truncated が true になります。

    レート制限: IPアドレスごとに5リクエスト/分

    Args:
        request: FastAPI Request（レート制限用）
        url: YouTubeプレイリストURL（必須クエリパラメータ）
        use_case: GetPlaylistUseCase（DIコンテナから注入）

    Returns:
        PlaylistResponse: プレイリスト情報と動画一覧

    Raises:
        HTTPException: 以下の場合にHTTPエラーを返します
            - 400 Bad Request: URLまたはプレイリストIDが無効、または長さ制限を超過
            - 404 Not Found: プレイリストが存在しない、非公開、
              または再生可能な動画を含まない
            - 429 Too Many Requests: レート制限を超過
            - 502 Bad Gateway: YouTubeへのアクセス失敗
            - 500 Internal Server Error: その他の予期しないエラー
    """
    try:
        url_validator.validate_length(url)

        playlist_info, items = await use_case.execute(url)

        return PlaylistResponse(playlist_info=playlist_info, items=items)
    except InvalidPlaylistIdError:
        logger.warning(f"Invalid playlist ID: url={url}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Invalid playlist URL. The URL must contain a public playlist (list=...).",
        )
    except InvalidUrlError:
        logger.warning(f"Invalid URL in get_playlist: url={url}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid URL format.")
    except PlaylistNotFoundError:
        logger.warning(f"Playlist not found: url={url}", exc_info=True)
        raise HTTPException(
            status_code=404,
            detail="Playlist not found, is private, or contains no playable videos.",
        )
    except YouTubeResolverError:
        logger.error(f"Failed to fetch playlist: url={url}", exc_info=True)
        raise HTTPException(status_code=502, detail="Failed to fetch playlist from YouTube.")
    except Exception:
        logger.error(f"Unexpected error in get_playlist: url={url}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An internal error occurred. Please try again later."
        )


@router.get("/playlist/stream")
@limiter.limit(config.rate_limit.playlist_stream)
async def get_playlist_stream(
    request: Request,
    video_id: str = Query(..., description="YouTube動画ID（11文字）"),
    use_case: ResolveYoutubeUrlUseCase = Depends(get_resolve_youtube_url_use_case),
) -> StreamUrlResponse:
    """
    プレイヤーで再生する動画のストリームURLを解決します

    GET /resolve と同じ解決結果を、リダイレクトではなくJSONで返します。
    プレイヤーは取得したURLを<video>要素に直接設定するため、シーク時の
    レンジリクエストが本サービスを経由せず、レート制限を消費しません。

    解決済みURLはRedisにキャッシュされ、有効期限内は再解決されません。

    レート制限: IPアドレスごとに30リクエスト/分

    Args:
        request: FastAPI Request（レート制限用）
        video_id: YouTube動画ID（必須クエリパラメータ）
        use_case: ResolveYoutubeUrlUseCase（DIコンテナから注入）

    Returns:
        StreamUrlResponse: 動画IDと解決済みストリームURL

    Raises:
        HTTPException: 以下の場合にHTTPエラーを返します
            - 400 Bad Request: 動画IDが無効な形式
            - 429 Too Many Requests: レート制限を超過
            - 502 Bad Gateway: YouTubeへのアクセス失敗、URL解決失敗
            - 500 Internal Server Error: その他の予期しないエラー
    """
    try:
        validated_video_id = YouTubeVideoId(_value=video_id)
        youtube_url = YoutubeUrl(_value=f"https://www.youtube.com/watch?v={validated_video_id}")

        stream_url = await use_case.execute(youtube_url)

        return StreamUrlResponse(video_id=validated_video_id.value, stream_url=stream_url)
    except InvalidVideoIdError:
        logger.warning(f"Invalid video ID in get_playlist_stream: video_id={video_id}")
        raise HTTPException(status_code=400, detail="Invalid video ID format.")
    except InvalidUrlError:
        logger.warning(f"Invalid URL in get_playlist_stream: video_id={video_id}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid URL format.")
    except YouTubeResolverError:
        logger.error(f"Failed to resolve URL: video_id={video_id}", exc_info=True)
        raise HTTPException(status_code=502, detail="Failed to resolve URL.")
    except Exception:
        logger.error(f"Unexpected error in get_playlist_stream: video_id={video_id}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An internal error occurred. Please try again later."
        )
