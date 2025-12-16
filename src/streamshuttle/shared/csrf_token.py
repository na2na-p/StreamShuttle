"""
CSRFトークン生成・検証モジュール

ステートレストークン方式のCSRF対策を提供します。
トークンは有効期限付きで、HMAC-SHA256で署名されます。
"""

import hashlib
import hmac
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode

from streamshuttle.shared.config import config


def generate_csrf_token() -> str:
    """
    CSRFトークンを生成します

    タイムスタンプと署名を含むトークンを生成します。
    トークンはURLセーフなBase64エンコードされます。

    Returns:
        str: 生成されたCSRFトークン
    """
    timestamp = str(int(time.time()))

    signature = hmac.new(
        config.security.csrf_secret_key.encode(), timestamp.encode(), hashlib.sha256
    ).hexdigest()

    token_data = f"{timestamp}:{signature}"
    token = urlsafe_b64encode(token_data.encode()).decode()

    return token


def verify_csrf_token(token: str) -> bool:
    """
    CSRFトークンを検証します

    トークンの署名と有効期限を検証します。

    Args:
        token: 検証するCSRFトークン

    Returns:
        bool: トークンが有効な場合True、無効な場合False
    """
    try:
        token_data = urlsafe_b64decode(token.encode()).decode()
        timestamp_str, signature = token_data.split(":")

        expected_signature = hmac.new(
            config.security.csrf_secret_key.encode(), timestamp_str.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return False

        timestamp = int(timestamp_str)
        current_time = int(time.time())

        if current_time - timestamp > config.security.csrf_token_expiry_seconds:
            return False

        return True
    except Exception:
        return False
