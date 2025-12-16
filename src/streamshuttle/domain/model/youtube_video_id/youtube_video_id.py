"""YouTube動画ID ValueObjectモジュール"""

from __future__ import annotations

import re
from dataclasses import dataclass

from streamshuttle.shared.exceptions import InvalidVideoIdError


@dataclass(frozen=True)
class YoutubeVideoId:
    """YouTube動画IDを表すValueObject

    YouTube動画IDは11文字の英数字、ハイフン、アンダースコアから構成される。
    """

    _value: str

    def __post_init__(self) -> None:
        """video_idのバリデーション"""
        if not re.match(r"^[a-zA-Z0-9_-]{11}$", self._value):
            raise InvalidVideoIdError(
                f"Invalid video ID format: {self._value}. "
                "Video ID must be 11 characters of alphanumeric, hyphen, or underscore."
            )

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value
