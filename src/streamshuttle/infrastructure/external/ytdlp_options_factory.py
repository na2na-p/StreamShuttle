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
                    "player_client": ["android", "web"],
                    "skip": ["hls", "dash"],
                    "remote_components": ["ejs:github"],
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
    def create_url_resolution_options(format_spec: str, use_hls: bool = False) -> dict:
        """URL解決用オプションを生成

        指定されたフォーマットでストリームURLを解決するためのオプション。

        Args:
            format_spec: yt-dlpのフォーマット指定文字列
            use_hls: HLS形式を使用するかどうか

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

        if use_hls:
            options["extractor_args"]["youtube"]["skip"] = ["dash"]

        return options
