"""URL検証モジュール"""

from dataclasses import dataclass

from streamshuttle.shared.exceptions import InvalidUrlError


@dataclass(frozen=True)
class UrlValidator:
    """URL検証を提供するバリデータ

    URLのバリデーションに関するロジックをカプセル化します。
    DoS対策としてのURL長制限チェックなどを提供します。
    """

    max_length: int = 2000

    def validate_length(self, url: str) -> None:
        """
        URLの長さを検証する

        Args:
            url: 検証対象のURL

        Raises:
            InvalidUrlError: URL長が制限を超える場合
        """
        if len(url) > self.max_length:
            raise InvalidUrlError(
                f"URL長が制限({self.max_length}文字)を超えています: {len(url)}文字"
            )
