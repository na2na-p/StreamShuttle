"""
プレイリスト QueryService実装モジュール

UseCase層で定義されたPlaylistQueryServiceインターフェースの実装クラスを定義します。
"""

import asyncio

import yt_dlp

from streamshuttle.domain.model.youtube_playlist import YoutubePlaylistUrl
from streamshuttle.infrastructure.external.ytdlp_options_factory import YtDlpOptionsFactory
from streamshuttle.shared.exceptions import (
    InvalidUrlError,
    PlaylistNotFoundError,
    YouTubeResolverError,
)
from streamshuttle.usecase.dto.playlist_info_dto import PlaylistInfoDto
from streamshuttle.usecase.dto.playlist_item_dto import PlaylistItemDto

# 再生できない項目（非公開・削除済み動画）のタイトルとしてyt-dlpが返す文字列
UNAVAILABLE_TITLES = (
    "[Private video]",
    "[Deleted video]",
    "[Unavailable video]",
)

# プレイリスト自体が利用できないことを示すyt-dlpのエラーメッセージ断片
# （通信障害などのサービス側起因のエラーと区別し、404として扱うために使用する）
PLAYLIST_UNAVAILABLE_MARKERS = (
    "does not exist",
    "is private",
    "not found",
    "no longer available",
)


class PlaylistQueryService:
    """
    プレイリスト QueryService実装クラス

    PlaylistQueryServiceインターフェースのyt-dlp実装です。
    yt-dlpのフラット抽出（extract_flat）を使用して、プレイリストに含まれる
    動画のID・タイトル・長さのみを取得します。

    実装の詳細:
        - yt-dlpは同期処理のため、asyncio.to_threadで非同期化
        - extract_flat=Trueで各動画のフォーマット解決を行わず高速に一覧取得
        - 非公開・削除済みの動画は再生できないため一覧から除外
        - プレイリストの不存在・非公開（404）と、通信障害等（502）を区別
        - max_items件を超えるプレイリストは切り捨て（truncated=True）
    """

    def __init__(self, max_items: int) -> None:
        """
        PlaylistQueryServiceを初期化します

        Args:
            max_items: 取得する動画の最大件数（DoS対策の上限）
        """
        self._max_items = max_items

    async def get_playlist(
        self, playlist_url: str
    ) -> tuple[PlaylistInfoDto, list[PlaylistItemDto]]:
        """
        プレイリストURLからプレイリスト情報と動画一覧を取得します

        Args:
            playlist_url: YouTubeプレイリストURL

        Returns:
            tuple[PlaylistInfoDto, list[PlaylistItemDto]]: プレイリスト情報と動画一覧

        Raises:
            InvalidUrlError: 無効なURLが指定された場合
            PlaylistNotFoundError: プレイリストが存在しない、非公開、
                または再生可能な動画を含まない場合
            YouTubeResolverError: YouTubeへのアクセスに失敗した場合
        """
        try:
            # URL検証はYoutubePlaylistUrl ValueObjectに委譲
            validated_url = YoutubePlaylistUrl(_value=playlist_url)

            # yt-dlpは同期処理のため、asyncio.to_threadで非同期化
            info = await asyncio.to_thread(self._extract_info, validated_url.value)
        except InvalidUrlError:
            # URL検証エラーはそのまま再送出（クライアント側のエラー）
            raise
        except yt_dlp.utils.DownloadError as e:
            # 存在しない・非公開のプレイリストはクライアント側の誤りとして扱い、
            # 通信障害などサービス側起因のエラーと区別する
            if self._is_playlist_unavailable(str(e)):
                raise PlaylistNotFoundError(
                    f"プレイリストが存在しないか、非公開です: {playlist_url}"
                ) from e
            raise YouTubeResolverError(
                f"プレイリスト情報の取得に失敗しました: {playlist_url}"
            ) from e
        except Exception as e:
            raise YouTubeResolverError(f"予期しないエラーが発生しました: {playlist_url}") from e

        if info is None or not info.get("entries"):
            raise PlaylistNotFoundError(
                f"プレイリストが見つからないか、動画が含まれていません: {playlist_url}"
            )

        entries = list(info["entries"])
        truncated = len(entries) > self._max_items
        items = self._to_items(entries[: self._max_items])

        if not items:
            raise PlaylistNotFoundError(
                f"再生可能な動画がプレイリストに含まれていません: {playlist_url}"
            )

        playlist_info = PlaylistInfoDto(
            playlist_id=info.get("id", "unknown"),
            title=info.get("title", "Unknown Playlist"),
            uploader=info.get("uploader") or info.get("channel") or "",
            item_count=len(items),
            truncated=truncated,
        )

        return playlist_info, items

    def _is_playlist_unavailable(self, error_message: str) -> bool:
        """
        yt-dlpのエラーメッセージがプレイリストの不存在・非公開を示すかを判定します

        Args:
            error_message: yt-dlpのエラーメッセージ

        Returns:
            bool: プレイリスト自体が利用できないことを示す場合True
        """
        lowered = error_message.lower()
        return any(marker in lowered for marker in PLAYLIST_UNAVAILABLE_MARKERS)

    def _to_items(self, entries: list) -> list[PlaylistItemDto]:
        """
        yt-dlpのエントリー一覧をPlaylistItemDtoのリストに変換します

        再生できない項目（Noneエントリー、ID欠落、非公開・削除済み動画）は除外します。

        Args:
            entries: yt-dlpから取得したエントリーのリスト

        Returns:
            list[PlaylistItemDto]: 再生可能な動画のDTOリスト
        """
        items: list[PlaylistItemDto] = []

        for entry in entries:
            # 取得できなかったエントリーはNoneになることがある
            if not entry:
                continue

            video_id = entry.get("id")
            if not video_id:
                continue

            title = entry.get("title") or "Unknown Title"
            if title in UNAVAILABLE_TITLES:
                continue

            duration = entry.get("duration")

            items.append(
                PlaylistItemDto(
                    video_id=video_id,
                    title=title,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    duration_seconds=int(duration) if duration else None,
                    # サムネイルはCSPで許可済みのi.ytimg.comに正規化する
                    thumbnail_url=f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
                )
            )

        return items

    def _extract_info(self, playlist_url: str) -> dict:
        """
        yt-dlpを使用してプレイリスト情報を抽出します（同期処理）

        この内部メソッドはasyncio.to_threadから呼び出され、
        yt-dlpの同期処理を実行します。

        上限を超えたかどうかを判定するため、max_items + 1件まで取得します。

        Args:
            playlist_url: YouTubeプレイリストURL

        Returns:
            dict: yt-dlpから取得したプレイリスト情報辞書

        Raises:
            yt_dlp.utils.DownloadError: プレイリスト情報の取得に失敗した場合
        """
        ydl_opts = YtDlpOptionsFactory.create_playlist_extraction_options(
            playlist_end=self._max_items + 1
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

        return info
