"""Referer検証モジュール"""

from dataclasses import dataclass
from urllib.parse import urlsplit

from fastapi import HTTPException, Request

_DEFAULT_PORTS = {"http": 80, "https": 443}


@dataclass(frozen=True)
class RefererValidator:
    """Refererヘッダーを検証するバリデータ

    HTTPリクエストのRefererヘッダーを検証し、
    許可されたオリジンからのリクエストのみを受け入れます。
    """

    allowed_origins: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """デフォルト値の設定"""
        if self.allowed_origins is None:
            object.__setattr__(self, "allowed_origins", [])

    def validate(self, request: Request) -> None:
        """
        Refererヘッダーのオリジンが許可オリジンのいずれかと一致することを検証

        オリジンはスキーム・ホスト名・ポートの組で比較し、パス・クエリ・
        フラグメントは比較対象に含めない。userinfoを含むReferer、
        http/https以外のスキーム、ホスト名のないReferer、不正なポートを
        持つRefererは拒否する。

        Args:
            request: FastAPI Requestオブジェクト

        Raises:
            HTTPException: Refererが無効な場合（status_code=403）
        """
        referer = request.headers.get("referer")
        if not referer:
            raise HTTPException(status_code=403, detail="Invalid request origin.")

        allowed_origins = self._build_allowed_origins(request)

        if not self._matches_any_origin(referer, allowed_origins):
            raise HTTPException(status_code=403, detail="Invalid request origin.")

    @staticmethod
    def _matches_any_origin(referer: str, allowed_origins: list[str]) -> bool:
        """Refererのオリジンが許可オリジンのいずれかと一致するかを判定

        Args:
            referer: Refererヘッダーの値
            allowed_origins: 許可オリジンのリスト

        Returns:
            bool: 一致する許可オリジンがあればTrue
        """
        # 文字列の前方一致では "https://example.com.evil.net" や
        # "https://example.com@evil.net" のような類似ホストを許してしまうため、
        # 解析済みのオリジン同士を等価比較する
        referer_origin = _parse_origin(referer)
        if referer_origin is None:
            return False
        return any(_parse_origin(origin) == referer_origin for origin in allowed_origins)

    def _build_allowed_origins(self, request: Request) -> list[str]:
        """許可オリジンリストを構築

        Args:
            request: FastAPI Requestオブジェクト

        Returns:
            list[str]: 許可されるオリジンのリスト
        """
        origins = [str(request.base_url)]

        forwarded_host = request.headers.get("x-forwarded-host")
        if forwarded_host:
            forwarded_proto = request.headers.get("x-forwarded-proto") or "https"
            origins.append(f"{forwarded_proto}://{forwarded_host}")

        origins.extend(self.allowed_origins)
        return origins


def _parse_origin(url: str) -> tuple[str, str, int] | None:
    """URLからオリジン（スキーム・ホスト名・ポート）を取り出す

    Args:
        url: 解析対象のURL

    Returns:
        tuple[str, str, int] | None: 正規化済みの (スキーム, ホスト名, ポート)。
            オリジンとして扱えないURLの場合はNone
    """
    try:
        parts = urlsplit(url)
        # SplitResult.port は不正なポートで ValueError を送出するため、
        # 例外を伝播させず（500 にせず）オリジンなしとして扱う
        port = parts.port
    except ValueError:
        return None

    scheme = parts.scheme.lower()
    default_port = _DEFAULT_PORTS.get(scheme)
    if default_port is None:
        return None
    if parts.username is not None or parts.password is not None:
        return None
    if not parts.hostname:
        return None
    return scheme, parts.hostname, port if port is not None else default_port
