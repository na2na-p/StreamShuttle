"""yt-dlpオプション生成ファクトリー

yt-dlpの共通オプションと用途別オプションを生成する。
"""

from streamshuttle.shared.config import config

# YouTubeの既定プレイヤークライアントは音声+映像の結合済みフォーマットを返さないことがある。
# androidは結合済みMP4(format 18)を安定して返し、URLも認証なしで再生できるため、
# 既定クライアントで失敗した場合に限って使う。他のクライアントは同じformat 18でも403になる
FALLBACK_PLAYER_CLIENTS: tuple[str, ...] = ("android",)


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
    def create_format_extraction_options(player_clients: tuple[str, ...] | None = None) -> dict:
        """フォーマット情報取得用オプションを生成

        動画フォーマット一覧を取得するためのオプション。

        Args:
            player_clients: 使用するYouTubeプレイヤークライアント。
                Noneの場合はyt-dlpの既定に任せる

        Returns:
            dict: yt-dlpオプション辞書
        """
        options = YtDlpOptionsFactory.create_base_options()
        # 一覧取得ではフォーマット選択は不要。"best"だと音声+映像の結合済みフォーマットが
        # 存在しない動画で選択に失敗し、一覧自体が取得できなくなるため"all"を指定する
        options.update(
            {
                "format": "all",
                "skip_download": True,
            }
        )
        YtDlpOptionsFactory._apply_player_clients(options, player_clients)
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
    def create_url_resolution_options(
        format_spec: str,
        hls: bool = False,
        player_clients: tuple[str, ...] | None = None,
    ) -> dict:
        """URL解決用オプションを生成

        指定されたフォーマットでストリームURLを解決するためのオプション。

        Args:
            format_spec: yt-dlpのフォーマット指定文字列
            hls: HLS形式を使用するかどうか
            player_clients: 使用するYouTubeプレイヤークライアント。
                Noneの場合はyt-dlpの既定に任せる

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

        YtDlpOptionsFactory._apply_player_clients(options, player_clients)
        return options

    @staticmethod
    def _apply_player_clients(options: dict, player_clients: tuple[str, ...] | None) -> None:
        """player_clientsが指定されている場合のみextractor_argsへ反映する"""
        if player_clients is not None:
            options["extractor_args"]["youtube"]["player_client"] = list(player_clients)

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
