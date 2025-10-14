"""
レート制限モジュール

slowapiのLimiterインスタンスをアプリケーション全体で共有するために提供します。
IPアドレスベースのレート制限を実装しています。
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# IPアドレスベースのグローバルLimiterインスタンス
limiter = Limiter(key_func=get_remote_address)
