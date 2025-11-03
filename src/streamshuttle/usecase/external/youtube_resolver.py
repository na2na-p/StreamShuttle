"""
YouTube Resolver Externalインターフェース定義モジュール

YouTube URLを直接ストリームURLに解決するExternalのインターフェースを定義します。
"""

from abc import ABC, abstractmethod


class YoutubeResolver(ABC):
    """
    YouTube Resolver Externalインターフェース

    YouTube動画URLをyt-dlpを使用して直接ストリームURLに解決するための
    インターフェースです。このインターフェースの実装クラスは外部API（YouTube）への
    直接呼び出しを行います。

    実装クラスはInfrastructure層に配置されます。
    """

    @abstractmethod
    async def resolve_url(
        self, youtube_url: str, format_id: str | None = None, use_hls: bool = False
    ) -> tuple[str, int]:
        """
        YouTube動画URLを直接ストリームURLに解決します

        yt-dlpを使用してYouTube動画URLから直接アクセス可能なストリームURLを取得します。
        format_idが指定されている場合は指定されたフォーマットの単一ストリームURLを返し、
        指定されていない場合は最適な品質（'best'フォーマット）のURLを選択して返します。

        Args:
            youtube_url: YouTube動画URL（https://www.youtube.com/watch?v=xxxxx形式）
            format_id: フォーマットID（オプショナル）
            use_hls: HLS形式の使用（デフォルト: False）

        Returns:
            tuple[str, int]: (解決済みの直接ストリームURL, TTL秒数)

        Raises:
            YouTubeResolverException: YouTube APIへのアクセスまたはURL解決に失敗した場合
            InvalidUrlException: 無効なURLが指定された場合
        """
        pass
