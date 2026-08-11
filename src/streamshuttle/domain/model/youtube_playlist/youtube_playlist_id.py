"""
YouTubePlaylistId ValueObjectモジュール

YouTubeプレイリストIDを表現するValueObjectを定義します。
"""

import re
from dataclasses import dataclass

from streamshuttle.shared.exceptions import InvalidPlaylistIdError


@dataclass(frozen=True)
class YouTubePlaylistId:
    """
    YouTubeプレイリストIDを表現するValueObject

    プレイリストIDは英数字・ハイフン・アンダースコアで構成され、
    プレフィックスによって種別が異なります（PL: ユーザー作成、UU: チャンネルアップロード、
    OLAK5uy_: 自動生成アルバム、RD: ミックス等）。
    プレフィックスの種類は将来増減しうるため、文字種と長さのみを検証し、
    本サービスが扱えない非公開プレイリスト（WL: 後で見る、LL: 高く評価した動画）のみ
    明示的に拒否します。

    このValueObjectは不変であり、生成時にプレイリストID形式の妥当性を検証します。

    Attributes:
        _value: YouTubeプレイリストID文字列（プライベートフィールド）
    """

    _value: str

    MIN_LENGTH = 2
    MAX_LENGTH = 64
    # 認証が必要で公開プレイリストとして解決できないID
    PRIVATE_PLAYLIST_IDS = ("WL", "LL")

    @property
    def value(self) -> str:
        """
        プレイリストIDの値を取得します

        Returns:
            str: YouTubeプレイリストID文字列
        """
        return self._value

    def __post_init__(self) -> None:
        """
        インスタンス生成後のバリデーション

        YouTubeプレイリストIDの形式を検証します。
        - 空でないこと
        - 2文字以上64文字以下であること
        - 英数字、ハイフン、アンダースコアのみで構成されていること
        - 非公開プレイリスト（WL、LL）でないこと

        Raises:
            InvalidPlaylistIdError: プレイリストIDの形式が不正な場合
        """
        if not self._value:
            raise InvalidPlaylistIdError("プレイリストIDが空です")

        if not self.MIN_LENGTH <= len(self._value) <= self.MAX_LENGTH:
            raise InvalidPlaylistIdError(
                f"プレイリストIDは{self.MIN_LENGTH}文字以上{self.MAX_LENGTH}文字以下である"
                f"必要があります: {self._value}"
            )

        if not re.match(r"^[a-zA-Z0-9_-]+$", self._value):
            raise InvalidPlaylistIdError(f"プレイリストIDの形式が不正です: {self._value}")

        if self._value in self.PRIVATE_PLAYLIST_IDS:
            raise InvalidPlaylistIdError(
                f"非公開プレイリストは再生できません: {self._value}。"
                f"公開プレイリストのURLを指定してください。"
            )

    def __str__(self) -> str:
        """プレイリストIDの文字列表現を返す"""
        return self._value
