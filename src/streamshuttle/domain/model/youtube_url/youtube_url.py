"""YouTube URL ValueObjectモジュール"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from streamshuttle.domain.model.stream_url.youtube_video_id import YouTubeVideoId
from streamshuttle.shared.exceptions import InvalidUrlError, InvalidVideoIdError


@dataclass(frozen=True)
class YoutubeUrl:
    """YouTube URLを表すValueObject

    YouTube URLの検証と video_id の抽出機能を提供する。
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
        return self._value

    def extract_video_id(self) -> YouTubeVideoId:
        """URLからvideo_idを抽出する

        Returns:
            VideoId: 抽出された動画ID

        Raises:
            InvalidVideoIdError: video_idが抽出できない、または不正な形式の場合
        """
        parsed = urlparse(self._value)

        if parsed.hostname in ("youtube.com", "www.youtube.com", "m.youtube.com"):
            if parsed.path == "/watch":
                query_params = parse_qs(parsed.query)
                video_id = query_params.get("v", [None])[0]
                if video_id:
                    return YouTubeVideoId(_value=video_id)

            elif parsed.path.startswith("/embed/"):
                video_id = parsed.path.split("/embed/")[1].split("/")[0].split("?")[0]
                if video_id:
                    return YouTubeVideoId(_value=video_id)

            elif parsed.path.startswith("/live/"):
                video_id = parsed.path.split("/live/")[1].split("/")[0].split("?")[0]
                if video_id:
                    return YouTubeVideoId(_value=video_id)

        elif parsed.hostname in ("youtu.be", "www.youtu.be"):
            video_id = parsed.path.lstrip("/").split("/")[0].split("?")[0]
            if video_id:
                return YouTubeVideoId(_value=video_id)

        raise InvalidVideoIdError(f"Could not extract video ID from URL: {self._value}")

    def __str__(self) -> str:
        return self._value
