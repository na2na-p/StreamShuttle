"""
Twitch Resolver External実装モジュール

UseCase層で定義されたTwitchResolverインターフェースの実装クラスを定義します。
"""

import asyncio

import yt_dlp

from streamshuttle.domain.model.twitch_url.twitch_url import TwitchUrl
from streamshuttle.infrastructure.external.ytdlp_options_factory import YtDlpOptionsFactory
from streamshuttle.shared.exceptions import InvalidUrlError, TwitchResolverError
from streamshuttle.usecase.dto.resolved_url_result_dto import ResolvedUrlResultDto


class TwitchResolver:
    """
    Twitch Resolver External実装クラス

    TwitchResolverインターフェースのyt-dlp実装です。
    yt-dlpを使用してTwitch動画URLを直接ストリームURLに解決します。

    このExternalは外部API（Twitch）への直接呼び出しを行います。

    実装の詳細:
        - yt-dlpは同期処理のため、asyncio.to_threadで非同期化
        - 'best'フォーマットで最適な品質を選択
        - download=Falseで動画をダウンロードせずメタデータのみ取得
        - quiet=Trueでログ出力を抑制
    """

    async def resolve_url(
        self, twitch_url: str, format_id: str | None = None
    ) -> ResolvedUrlResultDto:
        """
        Twitch動画URLを直接ストリームURLに解決します

        yt-dlpを使用してTwitch動画URLから直接アクセス可能なストリームURLを取得します。
        format_idが指定されている場合は指定されたフォーマットの単一ストリームURLを返し、
        指定されていない場合は最適な品質（'best'フォーマット）のURLを選択して返します。

        Args:
            twitch_url: Twitch動画URL（https://www.twitch.tv/videos/xxxxx形式など）
            format_id: フォーマットID（オプショナル）

        Returns:
            ResolvedUrlResultDto: 解決済みURL情報（URL、TTL秒数を含む）

        Raises:
            TwitchResolverError: Twitch APIへのアクセスまたはURL解決に失敗した場合
            InvalidUrlError: 無効なURLが指定された場合
        """
        try:
            # URL検証はTwitchUrl ValueObjectに委譲
            validated_url = TwitchUrl(_value=twitch_url)

            resolved_url = await asyncio.to_thread(
                self._resolve_url_sync, validated_url.value, format_id
            )

            # TwitchのURLにはexpireパラメータがないため、デフォルトTTLを使用
            from streamshuttle.shared.config import config

            ttl_seconds = config.cache.ttl_seconds

        except InvalidUrlError:
            raise
        except yt_dlp.utils.DownloadError as e:
            raise TwitchResolverError(f"Twitch URLの解決に失敗しました: {twitch_url}") from e
        except Exception as e:
            raise TwitchResolverError(f"予期しないエラーが発生しました: {twitch_url}") from e

        return ResolvedUrlResultDto(resolved_url=resolved_url, ttl_seconds=ttl_seconds)

    def _resolve_url_sync(
        self, twitch_url: str, format_id: str | None = None
    ) -> str:
        """
        yt-dlpを使用してTwitch URLを解決します（同期処理）

        この内部メソッドはasyncio.to_threadから呼び出され、
        yt-dlpの同期処理を実行します。

        format_idが指定された場合、そのフォーマットの単一ストリームURLを返します。
        format_idが指定されていない場合は、bestフォーマットを使用します。

        TwitchはHLS形式のみをサポートするため、HLS URLが返されます。

        Args:
            twitch_url: Twitch動画URL
            format_id: フォーマットID（オプショナル）

        Returns:
            str: 解決済みの直接ストリームURL

        Raises:
            yt_dlp.utils.DownloadError: URL解決に失敗した場合
            TwitchResolverError: URLが取得できなかった場合
        """
        if format_id:
            format_spec = format_id
        else:
            format_spec = "best"

        ydl_opts = YtDlpOptionsFactory.create_twitch_options(format_spec)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(twitch_url, download=False)

        if info is None or "url" not in info:
            raise TwitchResolverError(
                f"Twitch URLの解決に失敗しました（URLが取得できませんでした）: {twitch_url}"
            )

        return info["url"]
