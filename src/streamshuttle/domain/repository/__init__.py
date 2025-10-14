"""
Repositoryインターフェースパッケージ

Domain層のRepositoryインターフェースをエクスポートします。
"""

from streamshuttle.domain.repository.stream_url_repository import StreamUrlRepository

__all__ = [
    "StreamUrlRepository",
]
