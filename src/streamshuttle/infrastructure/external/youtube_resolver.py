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

    async def resolve_url(
        self, youtube_url: str, format_id: str | None = None, use_hls: bool = False
    ) -> tuple[str, int]:
        """
        YouTube動画URLを直接ストリームURLに解決します

        yt-dlpを使用してYouTube動画URLから直接アクセス可能なストリームURLを取得します。
        format_idが指定されている場合は指定されたフォーマットの単一ストリームURLを返し、
        指定されていない場合は最適な品質（'best'フォーマット）のURLを選択して返します。

        Args:
            youtube_url: YouTube動画URL（https://www.youtube.com/watch?v=xxxxx形式）
            format_id: フォーマットID（オプショナル）
            use_hls: HLS形式の使用（デフォルト: False）
                注意: YouTubeはプログレッシブMP4を優先するため、
                このパラメーターは既存動作に影響を与えません（後方互換性を維持）

        Returns:
            tuple[str, int]: (解決済みの直接ストリームURL, TTL秒数)

        Raises:
            YouTubeResolverError: YouTube APIへのアクセスまたはURL解決に失敗した場合
            InvalidUrlError: 無効なURLが指定された場合
        """
        try:
            if not youtube_url.startswith(("http://", "https://")):
                raise InvalidUrlError(f"無効なURLです: {youtube_url}")

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

            resolved_url = await asyncio.to_thread(self._resolve_url_sync, youtube_url, format_id, use_hls)

            try:
                ttl_seconds = self._extract_ttl_from_url(resolved_url)
            except (ValueError, KeyError, IndexError):
                from streamshuttle.shared.config import config

                ttl_seconds = config.CACHE_TTL_SECONDS

        except InvalidUrlError:
            raise
        except yt_dlp.utils.DownloadError as e:
            raise YouTubeResolverError(f"YouTube URLの解決に失敗しました: {youtube_url}") from e
        except Exception as e:
            raise YouTubeResolverError(f"予期しないエラーが発生しました: {youtube_url}") from e

        return resolved_url, ttl_seconds

    def _resolve_url_sync(
        self, youtube_url: str, format_id: str | None = None, use_hls: bool = False
    ) -> str:
        """
        yt-dlpを使用してYouTube URLを解決します（同期処理）

        この内部メソッドはasyncio.to_threadから呼び出され、
        yt-dlpの同期処理を実行します。

        format_idが指定された場合、そのフォーマットの単一ストリームURLを返します。
        video onlyフォーマットが指定された場合は動画のみ、audio+videoフォーマットが
        指定された場合は音声付きのURLを返します。

        format_idが指定されていない場合は、use_hlsパラメーターに応じて
        フォーマットを選択します：

        use_hls=False（デフォルト）の場合：
        1. プログレッシブHTTPダウンロード（HLS m3u8を除外）のMP4形式
        2. 上記が利用できない場合、MP4形式全般
        3. 最終的に最適なフォーマット（bestフォーマット）

        use_hls=Trueの場合：
        - HLS形式を許可（bestフォーマット）

        Args:
            youtube_url: YouTube動画URL
            format_id: フォーマットID（オプショナル）
            use_hls: HLS形式の使用（デフォルト: False）

        Returns:
            str: 解決済みの直接ストリームURL

        Raises:
            yt_dlp.utils.DownloadError: URL解決に失敗した場合
            YouTubeResolverError: URLが取得できなかった場合
        """
        if format_id:
            format_spec = format_id
        else:
            if use_hls:
                # HLS形式を許可（bestフォーマット）
                format_spec = "best"
            else:
                # プログレッシブMP4を優先（HLS除外）
                format_spec = "best[protocol^=http][protocol!*=m3u8][ext=mp4]/best[ext=mp4]/best"

        # yt-dlpオプション（Public利用を前提としたセキュリティ設定）
        ydl_opts = {
            # 基本設定
            "format": format_spec,
            "quiet": True,
            "no_warnings": True,
            # セキュリティ設定
            "nocheckcertificate": False,
            "no_color": True,
            "no_call_home": True,
            "socket_timeout": 30,
            "extract_flat": "in_playlist",
            "noplaylist": True,
            # HTTPヘッダー設定（User-Agentを明示）
            "http_headers": {"User-Agent": "StreamShuttle/1.0.0"},
            # メモリリーク対策（yt-dlp Issue #8922）
            # requestsハンドラーのメモリリークを回避するためlegacy handlerを使用
            "compat_opts": ["prefer-legacy-http-handler"],
            # メタデータ取得の最適化（メモリ効率改善）
            "skip_download": True,  # ダウンロードは常にスキップ
            "no_get_comments": True,  # コメント取得を無効化（不要なメタデータ削減）
            "writesubtitles": False,  # 字幕を取得しない
            "writethumbnail": False,  # サムネイルを取得しない
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

        # URLを取得
        if info is None or "url" not in info:
            raise YouTubeResolverError(
                f"YouTube URLの解決に失敗しました（URLが取得できませんでした）: {youtube_url}"
            )

        return info["url"]

    def _extract_ttl_from_url(self, url: str) -> int:
        """
        URLからexpireパラメータを抽出してTTL秒数を計算します

        Args:
            url: YouTube動画URL（expireパラメータ含む）

        Returns:
            int: TTL秒数（現在時刻からexpireまでの秒数）

        Raises:
            ValueError: expireパラメータが見つからない、または無効な場合
        """
        from datetime import UTC, datetime
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        if "expire" not in query_params:
            raise ValueError("expire parameter not found in URL")

        expire_timestamp = int(query_params["expire"][0])
        expire_datetime = datetime.fromtimestamp(expire_timestamp, tz=UTC)
        now = datetime.now(UTC)

        ttl = (expire_datetime - now).total_seconds()
        return max(0, int(ttl))
