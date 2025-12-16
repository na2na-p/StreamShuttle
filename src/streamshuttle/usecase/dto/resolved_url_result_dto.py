"""URL解決結果DTO"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedUrlResultDto:
    """
    URL解決結果を表すDTO

    YoutubeResolverが返すURL解決結果をカプセル化します。
    tuple[str, int]のプリミティブ型を避け、型安全性と可読性を向上させます。

    Attributes:
        resolved_url: 解決済みの直接ストリームURL
        ttl_seconds: URLの有効期限（秒）
    """

    resolved_url: str
    ttl_seconds: int
