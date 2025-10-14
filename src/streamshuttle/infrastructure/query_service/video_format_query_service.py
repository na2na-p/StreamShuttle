"""
ビデオフォーマット QueryService実装モジュール

UseCase層で定義されたVideoFormatQueryServiceインターフェースの実装クラスを定義します。
"""

import asyncio
from urllib.parse import urlparse

import yt_dlp

from streamshuttle.shared.exceptions import InvalidUrlError, YouTubeResolverError
from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto
from streamshuttle.usecase.query_service.video_format_query_service import (
    VideoFormatQueryService as VideoFormatQueryServiceInterface,
)


class VideoFormatQueryService(VideoFormatQueryServiceInterface):
    """
    ビデオフォーマット QueryService実装クラス

    VideoFormatQueryServiceインターフェースのyt-dlp実装です。
    yt-dlpを使用してYouTube動画の利用可能なフォーマット情報を取得します。

    このQueryServiceは参照系（GET）処理からのみ呼び出され、
    外部API（YouTube）からのデータ取得のみを行います。

    実装の詳細:
        - yt-dlpは同期処理のため、asyncio.to_threadで非同期化
        - download=Falseで動画をダウンロードせずメタデータのみ取得
        - quiet=Trueでログ出力を抑制
    """

    async def get_available_formats(
        self, youtube_url: str
    ) -> tuple[VideoInfoDto, list[VideoFormatDto]]:
        """
        YouTube動画URLから利用可能なフォーマット一覧と動画情報を取得します

        yt-dlpを使用してYouTube動画の利用可能なフォーマット情報と基本情報を取得し、
        VideoInfoDtoとVideoFormatDtoのリストのタプルとして返します。

        Args:
            youtube_url: YouTube動画URL（https://www.youtube.com/watch?v=xxxxx形式）

        Returns:
            tuple[VideoInfoDto, list[VideoFormatDto]]: 動画情報とフォーマット情報のリスト

        Raises:
            YouTubeResolverError: YouTube APIへのアクセスまたはURL解決に失敗した場合
            InvalidUrlError: 無効なURLが指定された場合
        """
        try:
            # 強化されたURL検証（Public利用を前提としたセキュリティ対策）
            # 1. HTTPスキームのみ許可（file://, data:, javascript: などの危険なスキームを拒否）
            if not youtube_url.startswith(("http://", "https://")):
                raise InvalidUrlError(f"無効なURLです: {youtube_url}")

            # 2. YouTubeドメインのみ許可（他のドメインへのアクセスを防止）
            parsed_url = urlparse(youtube_url)
            allowed_domains = (
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
                "youtu.be",
                "www.youtu.be",
            )
            if parsed_url.hostname not in allowed_domains:
                raise InvalidUrlError(f"YouTube URLのみサポートしています: {youtube_url}")

            # yt-dlpは同期処理のため、asyncio.to_threadで非同期化
            info = await asyncio.to_thread(self._extract_info, youtube_url)
        except InvalidUrlError:
            # URL検証エラーはそのまま再送出（クライアント側のエラー）
            raise
        except yt_dlp.utils.DownloadError as e:
            raise YouTubeResolverError(f"YouTube動画情報の取得に失敗しました: {youtube_url}") from e
        except Exception as e:
            raise YouTubeResolverError(f"予期しないエラーが発生しました: {youtube_url}") from e

        # 動画情報を取得（適切なデフォルト値を設定）
        video_info = VideoInfoDto(
            video_id=info.get("id", "unknown"),
            title=info.get("title", "Unknown Title"),
            thumbnail_url=info.get("thumbnail", ""),
        )

        # フォーマット情報が存在しない場合
        if "formats" not in info:
            return video_info, []

        # フォーマット情報をDTOに変換
        format_dtos: list[VideoFormatDto] = []
        for fmt in info["formats"]:
            # 必須フィールドが存在しない場合はスキップ
            if not all(key in fmt for key in ["format_id", "url"]):
                continue

            # HLSフォーマット（m3u8）を除外
            protocol = fmt.get("protocol", "")
            if protocol in ("m3u8", "m3u8_native", "m3u8_native+http"):
                continue

            # 音声と動画の有無を確認
            acodec = fmt.get("acodec", "none")
            vcodec = fmt.get("vcodec", "none")
            has_audio = acodec != "none"
            has_video = vcodec != "none"

            format_dtos.append(
                VideoFormatDto(
                    format_id=fmt["format_id"],
                    quality=fmt.get("format_note", "unknown"),
                    codec=vcodec if vcodec != "none" else "unknown",
                    url=fmt["url"],
                    has_audio=has_audio,
                    has_video=has_video,
                )
            )

        return video_info, format_dtos

    def _extract_info(self, youtube_url: str) -> dict:
        """
        yt-dlpを使用してYouTube動画情報を抽出します（同期処理）

        この内部メソッドはasyncio.to_threadから呼び出され、
        yt-dlpの同期処理を実行します。

        Args:
            youtube_url: YouTube動画URL

        Returns:
            dict: yt-dlpから取得した動画情報辞書

        Raises:
            yt_dlp.utils.DownloadError: 動画情報の取得に失敗した場合
        """
        # yt-dlpオプション（Public利用を前提としたセキュリティ設定）
        ydl_opts = {
            # 基本設定
            "quiet": True,  # ログ出力を抑制
            "no_warnings": True,  # 警告を抑制
            "extract_flat": False,  # 完全な情報を取得（フォーマット一覧取得に必要）
            # セキュリティ設定
            "nocheckcertificate": False,  # SSL証明書を検証（デフォルト動作を明示）
            "no_color": True,  # カラー出力を無効化（ログインジェクション対策）
            "no_call_home": True,  # yt-dlpの更新チェックを無効化（不要な外部通信を防止）
            "socket_timeout": 30,  # タイムアウト設定（30秒）：長時間リクエストを防止
            "noplaylist": True,  # プレイリストダウンロードを無効化（単一動画のみ処理）
            # HTTPヘッダー設定（User-Agentを明示）
            "http_headers": {"User-Agent": "StreamShuttle/0.1.0"},
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

        return info
