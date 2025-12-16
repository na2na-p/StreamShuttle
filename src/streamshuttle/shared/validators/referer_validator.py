"""Referer検証モジュール"""

from dataclasses import dataclass

from fastapi import HTTPException, Request


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
        Refererヘッダーが許可オリジンから始まることを検証

        Args:
            request: FastAPI Requestオブジェクト

        Raises:
            HTTPException: Refererが無効な場合（status_code=403）
        """
        referer = request.headers.get("referer")
        if not referer:
            raise HTTPException(status_code=403, detail="Invalid request origin.")

        allowed_origins = self._build_allowed_origins(request)

        if not any(referer.startswith(origin) for origin in allowed_origins):
            raise HTTPException(status_code=403, detail="Invalid request origin.")

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
