"""
Twitch Resolver Externalインターフェース定義モジュール

Twitch URLを直接ストリームURLに解決するExternalのインターフェースを定義します。
"""

from typing import Protocol

from streamshuttle.usecase.dto.resolved_url_result_dto import ResolvedUrlResultDto


class TwitchResolver(Protocol):
    """
    Twitch Resolver Externalインターフェース

    Twitch動画URLをyt-dlpを使用して直接ストリームURLに解決するための
    インターフェースです。このインターフェースの実装クラスは外部API（Twitch）への
    直接呼び出しを行います。

    実装クラスはInfrastructure層に配置されます。
    """

    async def resolve_url(
        self, twitch_url: str, format_id: str | None = None
    ) -> ResolvedUrlResultDto:
        """
        Twitch動画URLを直接ストリームURLに解決します

        yt-dlpを使用してTwitch動画URLから直接アクセス可能なストリームURLを取得します。
        format_idが指定されている場合は指定されたフォーマットの単一ストリームURLを返し、
        指定されていない場合は最適な品質（'best'フォーマット）のURLを選択して返します。

        Args:
            twitch_url: Twitch動画URL（https://www.twitch.tv/videos/xxxxx形式など）
            format_id: フォーマットID（オプショナル）

        Returns:
            ResolvedUrlResultDto: 解決済みURL情報（URL、TTL秒数を含む）

        Raises:
            TwitchResolverError: Twitch APIへのアクセスまたはURL解決に失敗した場合
            InvalidUrlError: 無効なURLが指定された場合
        """
        ...
