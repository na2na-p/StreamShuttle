"""
YouTube Resolver External実装モジュール

UseCase層で定義されたYoutubeResolverインターフェースの実装クラスを定義します。
"""

import asyncio
from urllib.parse import urlparse

import yt_dlp

from streamshuttle.shared.exceptions import InvalidUrlError, YouTubeResolverError
from streamshuttle.usecase.external.youtube_resolver import (
    YoutubeResolver as YoutubeResolverInterface,
)


class YoutubeResolver(YoutubeResolverInterface):
    """
    YouTube Resolver External実装クラス

    YoutubeResolverインターフェースのyt-dlp実装です。
    yt-dlpを使用してYouTube動画URLを直接ストリームURLに解決します。

    このExternalは外部API（YouTube）への直接呼び出しを行います。

    実装の詳細:
        - yt-dlpは同期処理のため、asyncio.to_threadで非同期化
        - 'best'フォーマットで最適な品質を選択
        - download=Falseで動画をダウンロードせずメタデータのみ取得
        - quiet=Trueでログ出力を抑制
    """

    async def resolve_url(self, youtube_url: str) -> str:
        """
        YouTube動画URLを直接ストリームURLに解決します

        yt-dlpを使用してYouTube動画URLから直接アクセス可能なストリームURLを取得します。
        最適な品質（'best'フォーマット）のURLを選択して返します。

        Args:
            youtube_url: YouTube動画URL（https://www.youtube.com/watch?v=xxxxx形式）

        Returns:
            str: 解決済みの直接ストリームURL

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
                "www.youtu.be"
            )
            if parsed_url.hostname not in allowed_domains:
                raise InvalidUrlError(f"YouTube URLのみサポートしています: {youtube_url}")

            # yt-dlpは同期処理のため、asyncio.to_threadで非同期化
            resolved_url = await asyncio.to_thread(self._resolve_url_sync, youtube_url)
        except InvalidUrlError:
            # URL検証エラーはそのまま再送出（クライアント側のエラー）
            raise
        except yt_dlp.utils.DownloadError as e:
            raise YouTubeResolverError(
                f"YouTube URLの解決に失敗しました: {youtube_url}"
            ) from e
        except Exception as e:
            raise YouTubeResolverError(
                f"予期しないエラーが発生しました: {youtube_url}"
            ) from e

        return resolved_url

    def _resolve_url_sync(self, youtube_url: str) -> str:
        """
        yt-dlpを使用してYouTube URLを解決します（同期処理）

        この内部メソッドはasyncio.to_threadから呼び出され、
        yt-dlpの同期処理を実行します。

        Args:
            youtube_url: YouTube動画URL

        Returns:
            str: 解決済みの直接ストリームURL

        Raises:
            yt_dlp.utils.DownloadError: URL解決に失敗した場合
            YouTubeResolverError: URLが取得できなかった場合
        """
        # yt-dlpオプション（Public利用を前提としたセキュリティ設定）
        ydl_opts = {
            # 基本設定
            "format": "best",  # 最適な品質を選択
            "quiet": True,  # ログ出力を抑制
            "no_warnings": True,  # 警告を抑制
            # セキュリティ設定
            "nocheckcertificate": False,  # SSL証明書を検証（デフォルト動作を明示）
            "no_color": True,  # カラー出力を無効化（ログインジェクション対策）
            "no_call_home": True,  # yt-dlpの更新チェックを無効化（不要な外部通信を防止）
            "socket_timeout": 30,  # タイムアウト設定（30秒）：長時間リクエストを防止
            "extract_flat": "in_playlist",  # プレイリストの平坦化
            "noplaylist": True,  # プレイリストダウンロードを無効化（単一動画のみ処理）
            # HTTPヘッダー設定（User-Agentを明示）
            "http_headers": {"User-Agent": "StreamShuttle/0.1.0"},
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

        # URLを取得
        if info is None or "url" not in info:
            raise YouTubeResolverError(
                f"YouTube URLの解決に失敗しました（URLが取得できませんでした）: {youtube_url}"
            )

        return info["url"]
