"""yt-dlpオプション生成ファクトリー

yt-dlpの共通オプションと用途別オプションを生成する。
"""

from streamshuttle.shared.config import config


class YtDlpOptionsFactory:
    """yt-dlpオプション生成ファクトリー"""

    @staticmethod
    def create_base_options() -> dict:
        """共通の基本オプションを生成

        セキュリティ設定とタイムアウト設定を含む。

        Returns:
            dict: yt-dlpオプション辞書
        """
        return {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": False,
            "no_color": True,
            "no_call_home": True,
            "socket_timeout": 30,
            "extract_flat": "in_playlist",
            "noplaylist": True,
            "http_headers": {
                "User-Agent": f"StreamShuttle/{config.app_version}",
            },
            "compat_opts": ["prefer-legacy-http-handler"],
            "extractor_args": {
                "youtube": {
                    "skip": ["hls"],
                }
            },
        }

    @staticmethod
    def create_format_extraction_options() -> dict:
        """フォーマット情報取得用オプションを生成

        動画フォーマット一覧を取得するためのオプション。

        Returns:
            dict: yt-dlpオプション辞書
        """
        options = YtDlpOptionsFactory.create_base_options()
        options.update(
            {
                "format": "best",
                "skip_download": True,
            }
        )
        return options

    @staticmethod
    def create_playlist_extraction_options(playlist_end: int) -> dict:
        """プレイリスト情報取得用オプションを生成

        プレイリストに含まれる動画一覧をフラット抽出するためのオプション。
        各動画のフォーマット解決は行わず、ID・タイトル・長さのみを取得するため、
        大きなプレイリストでも高速に一覧を取得できる。

        Args:
            playlist_end: 取得を打ち切る位置（yt-dlpのplaylistendに対応）

        Returns:
            dict: yt-dlpオプション辞書
        """
        options = YtDlpOptionsFactory.create_base_options()
        options.update(
            {
                "extract_flat": True,
                "noplaylist": False,
                "playlistend": playlist_end,
                "skip_download": True,
            }
        )
        return options

    @staticmethod
    def create_url_resolution_options(format_spec: str, hls: bool = False) -> dict:
        """URL解決用オプションを生成

        指定されたフォーマットでストリームURLを解決するためのオプション。

        Args:
            format_spec: yt-dlpのフォーマット指定文字列
            hls: HLS形式を使用するかどうか

        Returns:
            dict: yt-dlpオプション辞書
        """
        options = YtDlpOptionsFactory.create_base_options()
        options.update(
            {
                "format": format_spec,
                "skip_download": True,
                "no_get_comments": True,
                "writesubtitles": False,
                "writethumbnail": False,
            }
        )

        if hls:
            options["extractor_args"]["youtube"]["skip"] = ["dash"]

        return options

    @staticmethod
    def create_twitch_options(format_spec: str) -> dict:
        """Twitch用オプションを生成

        TwitchはHLS形式のみをサポートするため、HLS対応の設定を行う。

        Args:
            format_spec: yt-dlpのフォーマット指定文字列

        Returns:
            dict: yt-dlpオプション辞書
        """
        options = {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": False,
            "no_color": True,
            "no_call_home": True,
            "socket_timeout": 30,
            "noplaylist": True,
            "http_headers": {
                "User-Agent": f"StreamShuttle/{config.app_version}",
            },
            "format": format_spec,
            "skip_download": True,
            "no_get_comments": True,
            "writesubtitles": False,
            "writethumbnail": False,
        }

        return options
