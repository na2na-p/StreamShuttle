"""
YouTube Resolver External実装モジュール

UseCase層で定義されたYoutubeResolverインターフェースの実装クラスを定義します。
"""

import asyncio
import logging
import re
from urllib.parse import parse_qs, urlparse

import yt_dlp

from streamshuttle.domain.model.hls_mode import HlsMode
from streamshuttle.domain.model.youtube_url.youtube_url import YoutubeUrl
from streamshuttle.infrastructure.external.ytdlp_options_factory import (
    FALLBACK_PLAYER_CLIENTS,
    YtDlpOptionsFactory,
)
from streamshuttle.shared.exceptions import (
    HlsMasterUnavailableError,
    InvalidUrlError,
    InvalidVideoIdError,
    VideoUnavailableError,
    YouTubeResolverError,
)
from streamshuttle.usecase.dto.resolved_url_result_dto import ResolvedUrlResultDto

logger = logging.getLogger(__name__)

# yt-dlpが結合済みフォーマットを見つけられなかったときのエラーメッセージ。
# 認証エラーやネットワークエラーはクライアントを替えても解決しないため、
# このメッセージの場合だけを再試行の条件にする
_FORMAT_UNAVAILABLE_MESSAGE = "Requested format is not available"
_YTDLP_ERROR_CLASSIFICATION_RULES = (
    (
        "temporary",
        (
            "try again later",
            "rate-limit",
            "rate limited",
            "rate-limited",
            "temporar",
            "http error 429",
            "too many requests",
            "captcha",
            "confirm you are not a bot",
        ),
    ),
    (
        "video_unavailable",
        (
            "private video",
            "video has been removed",
            "video unavailable",
            "this video is unavailable",
            "this video is not available",
            "has been terminated",
            "available in your country",
            "available in your region",
            "available in your location",
            "has been made private",
        ),
    ),
    ("hls_master_unavailable", (_FORMAT_UNAVAILABLE_MESSAGE.lower(),)),
)
_HLS_MANIFEST_HOSTNAMES = ("manifest.googlevideo.com",)
_HLS_MANIFEST_PATH_PREFIX = "/api/manifest/hls_variant/"


def _classify_ytdlp_error_message(message: str) -> str:
    matches = _matching_ytdlp_error_classifications(message)

    for classification, _ in _YTDLP_ERROR_CLASSIFICATION_RULES:
        if classification in matches:
            return classification
    return "other"


def _matching_ytdlp_error_classifications(message: str) -> set[str]:
    normalized_message = message.lower()
    return {
        classification
        for classification, signals in _YTDLP_ERROR_CLASSIFICATION_RULES
        if any(signal in normalized_message for signal in signals)
    }


def _classify_ytdlp_error(error: BaseException) -> str:
    """再試行の失敗を、最後の試行を基準に分類する。"""
    current_error: BaseException | None = error
    visited_error_ids = set()

    while current_error is not None and id(current_error) not in visited_error_ids:
        visited_error_ids.add(id(current_error))
        if "temporary" in _matching_ytdlp_error_classifications(str(current_error)):
            return "temporary"
        current_error = current_error.__cause__

    return _classify_ytdlp_error_message(str(error))


def _has_ytdlp_error_classification(error: BaseException, classification: str) -> bool:
    return classification in _matching_ytdlp_error_classifications(str(error))


class _SafeYtDlpLogger:
    def __init__(self, platform: str, video_id: str) -> None:
        self._platform = platform
        self._video_id = video_id

    def debug(self, message: str) -> None:
        self._log(logging.DEBUG, message)

    def info(self, message: str) -> None:
        self._log(logging.INFO, message)

    def warning(self, message: str) -> None:
        self._log(logging.WARNING, message)

    def error(self, message: str) -> None:
        self._log(logging.ERROR, message)

    def _log(self, level: int, message: str) -> None:
        logger.log(
            level,
            "yt-dlp output: classification=%s platform=%s video_id=%s",
            _classify_ytdlp_error_message(message),
            self._platform,
            self._video_id,
        )


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
        - yt-dlpの出力を安全な分類ログに変換し、生メッセージは記録しない
    """

    async def resolve_url(
        self,
        youtube_url: str,
        format_id: str | None = None,
        hls: HlsMode = HlsMode.DISABLED,
    ) -> ResolvedUrlResultDto:
        """
        YouTube動画URLを直接ストリームURLに解決します

        yt-dlpを使用してYouTube動画URLから直接アクセス可能なストリームURLを取得します。
        format_idが指定されている場合は指定されたフォーマットの単一ストリームURLを返し、
        指定されていない場合は最適な品質（'best'フォーマット）のURLを選択して返します。

        Args:
            youtube_url: YouTube動画URL（https://www.youtube.com/watch?v=xxxxx形式）
            format_id: フォーマットID（オプショナル）
            hls: HLS形式の使用（デフォルト: False）
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
                self._resolve_url_sync, validated_url.value, format_id, hls
            )

            try:
                ttl_seconds = self._extract_ttl_from_url(resolved_url, hls)
            except (ValueError, KeyError, IndexError):
                from streamshuttle.shared.config import config

                ttl_seconds = 0 if hls.is_master else config.cache.ttl_seconds

        except (HlsMasterUnavailableError, InvalidUrlError, VideoUnavailableError):
            raise
        except yt_dlp.utils.DownloadError as e:
            if hls.is_master:
                classification = _classify_ytdlp_error(e)
                if classification == "video_unavailable":
                    raise VideoUnavailableError() from e
                if classification == "hls_master_unavailable":
                    raise HlsMasterUnavailableError() from e
            raise YouTubeResolverError(f"YouTube URLの解決に失敗しました: {youtube_url}") from e
        except Exception as e:
            raise YouTubeResolverError(f"予期しないエラーが発生しました: {youtube_url}") from e

        return ResolvedUrlResultDto(resolved_url=resolved_url, ttl_seconds=ttl_seconds)

    def _resolve_url_sync(
        self,
        youtube_url: str,
        format_id: str | None = None,
        hls: HlsMode = HlsMode.DISABLED,
    ) -> str:
        """
        yt-dlpを使用してYouTube URLを解決します（同期処理）

        この内部メソッドはasyncio.to_threadから呼び出され、
        yt-dlpの同期処理を実行します。

        format_idが指定された場合、そのフォーマットの単一ストリームURLを返します。
        video onlyフォーマットが指定された場合は動画のみ、audio+videoフォーマットが
        指定された場合は音声付きのURLを返します。

        format_idが指定されていない場合は、hlsパラメーターに応じて
        フォーマットを選択します：

        hls=False（デフォルト）の場合：
        1. プログレッシブHTTPダウンロード（HLS m3u8を除外）のMP4形式
        2. 上記が利用できない場合、MP4形式全般
        3. 最終的に最適なフォーマット（bestフォーマット）

        hls=Trueの場合：
        - HLS形式を許可（bestフォーマット）

        既定のプレイヤークライアントで「Requested format is not available」となった場合は、
        同じフォーマット指定のままandroidクライアントで1回だけ再試行します。
        それ以外のエラー、および再試行でも失敗した場合はそのまま送出します。

        Args:
            youtube_url: YouTube動画URL
            format_id: フォーマットID（オプショナル）
            hls: HLS形式の使用（デフォルト: False）

        Returns:
            str: 解決済みの直接ストリームURL

        Raises:
            yt_dlp.utils.DownloadError: URL解決に失敗した場合（再試行の失敗を含む）
            YouTubeResolverError: URLが取得できなかった場合
        """
        if format_id:
            format_spec = format_id
        else:
            if hls.uses_hls:
                format_spec = "best"
            else:
                format_spec = "best[protocol^=http][protocol!*=m3u8][ext=mp4]/best[ext=mp4]/best"

        try:
            return self._extract_stream_url(youtube_url, format_spec, hls)
        except yt_dlp.utils.DownloadError as first_error:
            if hls.is_master:
                should_retry = _classify_ytdlp_error(first_error) == "hls_master_unavailable"
            else:
                should_retry = _has_ytdlp_error_classification(
                    first_error, "hls_master_unavailable"
                )

            if not should_retry:
                raise
            logger.warning(
                "既定のプレイヤークライアントでフォーマットを取得できなかったため"
                "フォールバックします: url=%s format_id=%s clients=%s",
                youtube_url,
                format_id,
                ",".join(FALLBACK_PLAYER_CLIENTS),
            )
            try:
                return self._extract_stream_url(
                    youtube_url, format_spec, hls, player_clients=FALLBACK_PLAYER_CLIENTS
                )
            except yt_dlp.utils.DownloadError as retry_error:
                raise retry_error from first_error

    def _extract_stream_url(
        self,
        youtube_url: str,
        format_spec: str,
        hls: HlsMode,
        player_clients: tuple[str, ...] | None = None,
    ) -> str:
        """
        yt-dlpによる1回分の抽出を実行してストリームURLを返します（同期処理）

        Args:
            youtube_url: YouTube動画URL
            format_spec: yt-dlpのフォーマット指定文字列
            hls: HLS形式の使用
            player_clients: 使用するプレイヤークライアント（Noneならyt-dlpの既定）

        Returns:
            str: 解決済みの直接ストリームURL

        Raises:
            yt_dlp.utils.DownloadError: 抽出に失敗した場合
            YouTubeResolverError: URLが取得できなかった場合
        """
        ydl_opts = YtDlpOptionsFactory.create_url_resolution_options(
            format_spec=format_spec, hls=hls.uses_hls, player_clients=player_clients
        )
        ydl_opts["logger"] = _SafeYtDlpLogger(
            platform="youtube", video_id=self._extract_video_id_for_logging(youtube_url)
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

        if info is None:
            raise YouTubeResolverError(
                f"YouTube URLの解決に失敗しました（URLが取得できませんでした）: {youtube_url}"
            )

        if hls.is_master:
            return self._extract_hls_manifest_url(info)

        if "url" not in info:
            raise YouTubeResolverError(
                f"YouTube URLの解決に失敗しました（URLが取得できませんでした）: {youtube_url}"
            )

        return info["url"]

    @staticmethod
    def _extract_hls_manifest_url(info: dict) -> str:
        manifest_urls = [info.get("manifest_url")]

        for key in ("requested_formats", "formats"):
            formats = info.get(key, [])
            if not isinstance(formats, list):
                continue
            for video_format in formats:
                if not isinstance(video_format, dict):
                    continue
                manifest_urls.append(video_format.get("manifest_url"))

        for manifest_url in manifest_urls:
            if isinstance(manifest_url, str) and YoutubeResolver._is_valid_hls_manifest_url(
                manifest_url
            ):
                return manifest_url

        raise HlsMasterUnavailableError()

    @staticmethod
    def _extract_video_id_for_logging(youtube_url: str) -> str:
        try:
            return str(YoutubeUrl(_value=youtube_url).extract_video_id())
        except (InvalidUrlError, InvalidVideoIdError):
            return "unknown"

    @staticmethod
    def _is_valid_hls_manifest_url(url: str) -> bool:
        parsed = urlparse(url)
        try:
            return (
                parsed.scheme == "https"
                and parsed.hostname in _HLS_MANIFEST_HOSTNAMES
                and parsed.port in (None, 443)
                and parsed.username is None
                and parsed.password is None
                and parsed.path.startswith(_HLS_MANIFEST_PATH_PREFIX)
            )
        except ValueError:
            return False

    def _extract_ttl_from_url(self, url: str, hls: HlsMode = HlsMode.DISABLED) -> int:
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

        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        expire_values = query_params.get("expire", [])
        if expire_values:
            expire_timestamp = int(expire_values[0])
        elif hls.uses_path_expire:
            path_expire = re.search(r"/expire/(\d+)(?:/|$)", parsed.path)
            if path_expire is None:
                raise ValueError("expire parameter not found in URL")
            expire_timestamp = int(path_expire.group(1))
        else:
            raise ValueError("expire parameter not found in URL")

        if expire_timestamp < 0:
            raise ValueError("expire parameter not found in URL")

        expire_datetime = datetime.fromtimestamp(expire_timestamp, tz=UTC)
        now = datetime.now(UTC)

        ttl = (expire_datetime - now).total_seconds()
        return max(0, int(ttl))
