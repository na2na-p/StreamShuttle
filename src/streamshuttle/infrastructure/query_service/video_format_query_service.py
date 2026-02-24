"""
ビデオフォーマット QueryService実装モジュール

UseCase層で定義されたVideoFormatQueryServiceインターフェースの実装クラスを定義します。
"""

import asyncio

import yt_dlp

from streamshuttle.domain.model.youtube_url.youtube_url import YoutubeUrl
from streamshuttle.infrastructure.external.ytdlp_options_factory import YtDlpOptionsFactory
from streamshuttle.shared.exceptions import InvalidUrlError, YouTubeResolverError
from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto


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

        # フォーマット情報が存在しない場合
        if "formats" not in info:
            return video_info, []

        # フォーマット情報をDTOに変換
        format_dtos: list[VideoFormatDto] = []
        for fmt in info["formats"]:
            # 必須フィールドが存在しない場合はスキップ
            if not all(key in fmt for key in ["format_id", "url"]):
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
        ydl_opts = YtDlpOptionsFactory.create_format_extraction_options()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

        return info
