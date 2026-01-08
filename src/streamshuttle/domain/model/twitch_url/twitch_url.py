"""Twitch URL ValueObjectモジュール"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from streamshuttle.domain.model.twitch_url.twitch_video_id import TwitchVideoId
from streamshuttle.shared.exceptions import InvalidUrlError, InvalidVideoIdError


@dataclass(frozen=True)
class TwitchUrl:
    """Twitch URLを表すValueObject

    Twitch URLの検証と video_id の抽出機能を提供する。
    """

    _value: str

    ALLOWED_DOMAINS = (
        "twitch.tv",
        "www.twitch.tv",
        "m.twitch.tv",
        "clips.twitch.tv",
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
        return self._value

    def extract_video_id(self) -> TwitchVideoId:
        """URLからvideo_idを抽出する

        Returns:
            TwitchVideoId: 抽出された動画ID

        Raises:
            InvalidVideoIdError: video_idが抽出できない、または不正な形式の場合
        """
        parsed = urlparse(self._value)
        path_parts = [p for p in parsed.path.split("/") if p]

        # clips.twitch.tv/{clip_slug}
        if parsed.hostname == "clips.twitch.tv":
            if path_parts:
                return TwitchVideoId(_value=path_parts[0])

        # twitch.tv/videos/{video_id} (VOD)
        if len(path_parts) >= 2 and path_parts[0] == "videos":
            return TwitchVideoId(_value=path_parts[1])

        # twitch.tv/{channel}/clip/{clip_slug}
        if len(path_parts) >= 3 and path_parts[1] == "clip":
            return TwitchVideoId(_value=path_parts[2])

        # twitch.tv/{channel} (ライブストリーム)
        if len(path_parts) == 1:
            return TwitchVideoId(_value=path_parts[0])

        raise InvalidVideoIdError(f"Could not extract video ID from URL: {self._value}")

    def __str__(self) -> str:
        return self._value
