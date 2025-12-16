"""
YouTube Resolver External実装モジュール

UseCase層で定義されたYoutubeResolverインターフェースの実装クラスを定義します。
"""

import asyncio

import yt_dlp

from streamshuttle.domain.model.youtube_url.youtube_url import YoutubeUrl
from streamshuttle.infrastructure.external.ytdlp_options_factory import YtDlpOptionsFactory
from streamshuttle.shared.exceptions import InvalidUrlError, YouTubeResolverError
from streamshuttle.usecase.dto.resolved_url_result_dto import ResolvedUrlResultDto


class YoutubeResolver:
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
    ) -> ResolvedUrlResultDto:
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
            ResolvedUrlResultDto: 解決済みURL情報（URL、TTL秒数を含む）

        Raises:
            YouTubeResolverError: YouTube APIへのアクセスまたはURL解決に失敗した場合
            InvalidUrlError: 無効なURLが指定された場合
        """
        try:
            # URL検証はYoutubeUrl ValueObjectに委譲
            validated_url = YoutubeUrl(_value=youtube_url)

            resolved_url = await asyncio.to_thread(
                self._resolve_url_sync, validated_url.value, format_id, use_hls
            )

            try:
                ttl_seconds = self._extract_ttl_from_url(resolved_url)
            except (ValueError, KeyError, IndexError):
                from streamshuttle.shared.config import config

                ttl_seconds = config.cache.ttl_seconds

        except InvalidUrlError:
            raise
        except yt_dlp.utils.DownloadError as e:
            raise YouTubeResolverError(f"YouTube URLの解決に失敗しました: {youtube_url}") from e
        except Exception as e:
            raise YouTubeResolverError(f"予期しないエラーが発生しました: {youtube_url}") from e

        return ResolvedUrlResultDto(resolved_url=resolved_url, ttl_seconds=ttl_seconds)

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
                format_spec = "best"
            else:
                format_spec = "best[protocol^=http][protocol!*=m3u8][ext=mp4]/best[ext=mp4]/best"

        ydl_opts = YtDlpOptionsFactory.create_url_resolution_options(
            format_spec=format_spec, use_hls=use_hls
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

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
