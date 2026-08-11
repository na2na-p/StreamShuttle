"""YouTube プレイリストURL ValueObjectモジュール"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from streamshuttle.domain.model.youtube_playlist.youtube_playlist_id import (
    YouTubePlaylistId,
)
from streamshuttle.shared.exceptions import InvalidPlaylistIdError, InvalidUrlError


@dataclass(frozen=True)
class YoutubePlaylistUrl:
    """YouTubeプレイリストURLを表すValueObject

    プレイリストURLの検証と playlist_id の抽出機能を提供する。

    対応する形式:
        - https://www.youtube.com/playlist?list=PLxxxx
        - https://www.youtube.com/watch?v=xxxxx&list=PLxxxx（再生中URLからの取り込み）
        - https://youtu.be/xxxxx?list=PLxxxx

    Attributes:
        _value: プレイリストURL文字列（プライベートフィールド）
    """

    _value: str

    ALLOWED_DOMAINS = (
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "www.youtu.be",
    )

    def __post_init__(self) -> None:
        """URLのバリデーション"""
        if not self._value.startswith(("http://", "https://")):
            raise InvalidUrlError(
                f"Invalid URL scheme: {self._value}. Only HTTP/HTTPS are allowed."
            )

        parsed = urlparse(self._value)
        if parsed.hostname not in self.ALLOWED_DOMAINS:
            raise InvalidUrlError(
                f"Invalid domain: {parsed.hostname}. "
                f"Allowed domains: {', '.join(self.ALLOWED_DOMAINS)}"
            )

    @property
    def value(self) -> str:
        """プレイリストURLの値を取得します"""
        return self._value

    def extract_playlist_id(self) -> YouTubePlaylistId:
        """URLからplaylist_idを抽出する

        listクエリパラメータからプレイリストIDを抽出します。

        Returns:
            YouTubePlaylistId: 抽出されたプレイリストID

        Raises:
            InvalidPlaylistIdError: playlist_idが抽出できない、または不正な形式の場合
        """
        parsed = urlparse(self._value)
        query_params = parse_qs(parsed.query)
        playlist_id = query_params.get("list", [None])[0]

        if not playlist_id:
            raise InvalidPlaylistIdError(
                f"Could not extract playlist ID from URL: {self._value}. "
                f"URLに list パラメータが含まれている必要があります。"
            )

        return YouTubePlaylistId(_value=playlist_id)

    def to_canonical_url(self) -> str:
        """プレイリストIDのみを含む正規化済みURLを返す

        watch URLに list パラメータが付いている場合でも、動画単体ではなく
        プレイリスト全体を取得できる形式（/playlist?list=...）へ正規化します。

        Returns:
            str: https://www.youtube.com/playlist?list={playlist_id} 形式のURL

        Raises:
            InvalidPlaylistIdError: playlist_idが抽出できない、または不正な形式の場合
        """
        playlist_id = self.extract_playlist_id()
        return f"https://www.youtube.com/playlist?list={playlist_id.value}"

    def __str__(self) -> str:
        return self._value
