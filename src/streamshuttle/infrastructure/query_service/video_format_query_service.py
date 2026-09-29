"""
ビデオフォーマット QueryService実装モジュール

UseCase層で定義されたVideoFormatQueryServiceインターフェースの実装クラスを定義します。
"""

import asyncio
import logging

import yt_dlp

from streamshuttle.domain.model.youtube_url.youtube_url import YoutubeUrl
from streamshuttle.infrastructure.external.ytdlp_options_factory import (
    FALLBACK_PLAYER_CLIENTS,
    YtDlpOptionsFactory,
)
from streamshuttle.shared.exceptions import InvalidUrlError, YouTubeResolverError
from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto

logger = logging.getLogger(__name__)


class VideoFormatQueryService:
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
        既定クライアントの結果に音声+映像の結合済みフォーマットが無い場合は、
        androidクライアントで再取得し、結合済みフォーマットのみを末尾に追加します。
        動画情報は既定クライアントの結果を使います。

        Args:
            youtube_url: YouTube動画URL（https://www.youtube.com/watch?v=xxxxx形式）

        Returns:
            tuple[VideoInfoDto, list[VideoFormatDto]]: 動画情報とフォーマット情報のリスト

        Raises:
            YouTubeResolverError: YouTube APIへのアクセスまたはURL解決に失敗した場合
            InvalidUrlError: 無効なURLが指定された場合
        """
        try:
            # URL検証はYoutubeUrl ValueObjectに委譲
            validated_url = YoutubeUrl(_value=youtube_url)

            # yt-dlpは同期処理のため、asyncio.to_threadで非同期化
            info = await asyncio.to_thread(self._extract_info, validated_url.value)
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

        format_dtos = self._to_format_dtos(info)

        if not any(dto.has_audio and dto.has_video for dto in format_dtos):
            format_dtos = await self._append_combined_formats_from_fallback(
                validated_url.value, format_dtos
            )

        return video_info, format_dtos

    async def _append_combined_formats_from_fallback(
        self, youtube_url: str, format_dtos: list[VideoFormatDto]
    ) -> list[VideoFormatDto]:
        """
        フォールバッククライアントで取得した結合済みフォーマットを一覧の末尾に追加します

        既定クライアントは音声+映像の結合済みフォーマットを返さないことがあるため、
        androidクライアントで再取得して結合済みフォーマットだけを補います。
        フォールバックの失敗は一覧取得全体の失敗にせず、元の一覧をそのまま返します。

        Args:
            youtube_url: 検証済みのYouTube動画URL
            format_dtos: 既定クライアントで取得したフォーマット一覧

        Returns:
            list[VideoFormatDto]: 結合済みフォーマットを補った一覧（失敗時は元の一覧）
        """
        logger.info(
            "結合済みフォーマットが無いためフォールバックします: url=%s clients=%s",
            youtube_url,
            ",".join(FALLBACK_PLAYER_CLIENTS),
        )
        try:
            fallback_info = await asyncio.to_thread(
                self._extract_info, youtube_url, FALLBACK_PLAYER_CLIENTS
            )
        except Exception:
            logger.warning(
                "フォールバックでのフォーマット取得に失敗しました: url=%s clients=%s",
                youtube_url,
                ",".join(FALLBACK_PLAYER_CLIENTS),
                exc_info=True,
            )
            return format_dtos

        known_ids = {dto.format_id for dto in format_dtos}
        combined = [
            dto
            for dto in self._to_format_dtos(fallback_info)
            if dto.has_audio and dto.has_video and dto.format_id not in known_ids
        ]
        return [*format_dtos, *combined]

    @staticmethod
    def _to_format_dtos(info: dict) -> list[VideoFormatDto]:
        """
        yt-dlpの動画情報からVideoFormatDtoのリストを生成します

        必須フィールド（format_id, url）が無いフォーマットとHLS(m3u8)は除外します。

        Args:
            info: yt-dlpから取得した動画情報辞書

        Returns:
            list[VideoFormatDto]: フォーマット情報のリスト
        """
        format_dtos: list[VideoFormatDto] = []
        for fmt in info.get("formats", []):
            if not all(key in fmt for key in ["format_id", "url"]):
                continue

            protocol = fmt.get("protocol", "")
            if protocol in ("m3u8", "m3u8_native", "m3u8_native+http"):
                continue

            acodec = fmt.get("acodec", "none")
            vcodec = fmt.get("vcodec", "none")

            format_dtos.append(
                VideoFormatDto(
                    format_id=fmt["format_id"],
                    quality=fmt.get("format_note", "unknown"),
                    codec=vcodec if vcodec != "none" else "unknown",
                    url=fmt["url"],
                    has_audio=acodec != "none",
                    has_video=vcodec != "none",
                )
            )

        return format_dtos

    def _extract_info(
        self, youtube_url: str, player_clients: tuple[str, ...] | None = None
    ) -> dict:
        """
        yt-dlpを使用してYouTube動画情報を抽出します（同期処理）

        この内部メソッドはasyncio.to_threadから呼び出され、
        yt-dlpの同期処理を実行します。

        Args:
            youtube_url: YouTube動画URL
            player_clients: 使用するプレイヤークライアント（Noneならyt-dlpの既定）

        Returns:
            dict: yt-dlpから取得した動画情報辞書

        Raises:
            yt_dlp.utils.DownloadError: 動画情報の取得に失敗した場合
        """
        ydl_opts = YtDlpOptionsFactory.create_format_extraction_options(
            player_clients=player_clients
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

        return info
