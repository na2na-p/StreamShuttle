"""
セキュリティヘッダーミドルウェア

Webアプリケーションのセキュリティを強化するため、
各種セキュリティヘッダーをHTTPレスポンスに追加します。
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    セキュリティヘッダーを自動的に追加するミドルウェア

    すべてのHTTPレスポンスに以下のセキュリティヘッダーを追加します：
    - Content-Security-Policy: XSS攻撃対策
    - X-Content-Type-Options: MIME type sniffing対策
    - X-Frame-Options: クリックジャッキング対策
    - Referrer-Policy: Referer情報の制御
    - Permissions-Policy: ブラウザ機能の制限
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        リクエストを処理し、レスポンスにセキュリティヘッダーを追加します

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェアまたはエンドポイント

        Returns:
            Response: セキュリティヘッダーが追加されたHTTPレスポンス
        """
        response = await call_next(request)

        # Content Security Policy (CSP)
        # 同一オリジンのリソースのみ許可し、XSS攻撃を防止
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "  # Jinja2テンプレートのインラインスタイル許可
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        # X-Content-Type-Options
        # ブラウザによるMIME type sniffingを防止
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options
        # iframe内での表示を禁止し、クリックジャッキング攻撃を防止
        response.headers["X-Frame-Options"] = "DENY"

        # Referrer-Policy
        # Referer情報を同一オリジンまたはHTTPS→HTTPSの場合のみ送信
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (旧Feature-Policy)
        # 不要なブラウザ機能を無効化
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        return response
