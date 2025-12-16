"""YtDlpOptionsFactory のユニットテスト"""

import pytest

from streamshuttle.infrastructure.external.ytdlp_options_factory import YtDlpOptionsFactory
from streamshuttle.shared.config import config


class TestYtDlpOptionsFactory:
    """YtDlpOptionsFactory のテストクラス"""

    @pytest.mark.parametrize(
        "method_name, expected_keys",
        [
            pytest.param(
                "create_base_options",
                [
                    "quiet",
                    "no_warnings",
                    "nocheckcertificate",
                    "no_color",
                    "no_call_home",
                    "socket_timeout",
                    "extract_flat",
                    "noplaylist",
                    "http_headers",
                    "compat_opts",
                    "extractor_args",
                ],
                id="正常系: 基本オプションに必要なキーが全て含まれる",
            ),
        ],
    )
    def test_create_base_options_returns_required_keys(self, method_name, expected_keys):
        """基本オプション生成メソッドが必要なキーを全て含むことを確認"""
        # Act
        options = YtDlpOptionsFactory.create_base_options()

        # Assert
        for key in expected_keys:
            assert key in options, f"必須キー '{key}' が含まれていません"

    @pytest.mark.parametrize(
        "key, expected_value",
        [
            pytest.param("quiet", True, id="正常系: quietがTrueである"),
            pytest.param("no_warnings", True, id="正常系: no_warningsがTrueである"),
            pytest.param("nocheckcertificate", False, id="正常系: nocheckcertificateがFalseである"),
            pytest.param("no_color", True, id="正常系: no_colorがTrueである"),
            pytest.param("no_call_home", True, id="正常系: no_call_homeがTrueである"),
            pytest.param("socket_timeout", 30, id="正常系: socket_timeoutが30である"),
            pytest.param(
                "extract_flat", "in_playlist", id="正常系: extract_flatが'in_playlist'である"
            ),
            pytest.param("noplaylist", True, id="正常系: noplaylistがTrueである"),
        ],
    )
    def test_create_base_options_has_correct_security_settings(self, key, expected_value):
        """基本オプションのセキュリティ設定が正しいことを確認"""
        # Act
        options = YtDlpOptionsFactory.create_base_options()

        # Assert
        assert options[key] == expected_value

    def test_create_base_options_has_user_agent_from_config(self):
        """基本オプションのUser-Agentが設定から取得されることを確認"""
        # Act
        options = YtDlpOptionsFactory.create_base_options()

        # Assert
        assert "http_headers" in options
        assert "User-Agent" in options["http_headers"]
        expected_user_agent = f"StreamShuttle/{config.app_version}"
        assert options["http_headers"]["User-Agent"] == expected_user_agent

    def test_create_base_options_has_compat_opts(self):
        """基本オプションにcompat_optsが正しく設定されることを確認"""
        # Act
        options = YtDlpOptionsFactory.create_base_options()

        # Assert
        assert "compat_opts" in options
        assert isinstance(options["compat_opts"], list)
        assert "prefer-legacy-http-handler" in options["compat_opts"]

    @pytest.mark.parametrize(
        "extractor, args_key",
        [
            pytest.param("youtube", "skip", id="正常系: youtubeエクストラクタにskipが設定される"),
            pytest.param(
                "youtube",
                "remote_components",
                id="正常系: youtubeエクストラクタにremote_componentsが設定される",
            ),
        ],
    )
    def test_create_base_options_has_extractor_args(self, extractor, args_key):
        """基本オプションのextractor_argsが正しく設定されることを確認"""
        # Act
        options = YtDlpOptionsFactory.create_base_options()

        # Assert
        assert "extractor_args" in options
        assert extractor in options["extractor_args"]
        assert args_key in options["extractor_args"][extractor]

    def test_create_base_options_has_remote_components_github(self):
        """基本オプションのremote_componentsに'ejs:github'が含まれることを確認"""
        # Act
        options = YtDlpOptionsFactory.create_base_options()

        # Assert
        assert "extractor_args" in options
        assert "youtube" in options["extractor_args"]
        assert "remote_components" in options["extractor_args"]["youtube"]
        assert isinstance(options["extractor_args"]["youtube"]["remote_components"], list)
        assert "ejs:github" in options["extractor_args"]["youtube"]["remote_components"]

    def test_create_format_extraction_options_inherits_base_options(self):
        """フォーマット抽出オプションが基本オプションを継承することを確認"""
        # Act
        base_options = YtDlpOptionsFactory.create_base_options()
        format_options = YtDlpOptionsFactory.create_format_extraction_options()

        # Assert - 基本オプションのキーが全て含まれる
        for key in base_options.keys():
            assert key in format_options

    @pytest.mark.parametrize(
        "key, expected_value",
        [
            pytest.param("format", "best", id="正常系: formatがbestである"),
            pytest.param("skip_download", True, id="正常系: skip_downloadがTrueである"),
        ],
    )
    def test_create_format_extraction_options_has_specific_settings(self, key, expected_value):
        """フォーマット抽出オプションに固有の設定が含まれることを確認"""
        # Act
        options = YtDlpOptionsFactory.create_format_extraction_options()

        # Assert
        assert options[key] == expected_value

    @pytest.mark.parametrize(
        "format_spec, use_hls, expected_format",
        [
            pytest.param(
                "best[ext=mp4]",
                False,
                "best[ext=mp4]",
                id="正常系: 指定されたフォーマット仕様が設定される（HLS無効）",
            ),
            pytest.param(
                "137+140",
                True,
                "137+140",
                id="正常系: 指定されたフォーマット仕様が設定される（HLS有効）",
            ),
        ],
    )
    def test_create_url_resolution_options_sets_format_spec(
        self, format_spec, use_hls, expected_format
    ):
        """URL解決オプションにフォーマット仕様が正しく設定されることを確認"""
        # Act
        options = YtDlpOptionsFactory.create_url_resolution_options(
            format_spec=format_spec, use_hls=use_hls
        )

        # Assert
        assert options["format"] == expected_format

    @pytest.mark.parametrize(
        "format_spec, use_hls, expected_skip",
        [
            pytest.param(
                "best",
                False,
                ["hls"],
                id="正常系: HLS無効時はhlsをスキップ",
            ),
            pytest.param(
                "best",
                True,
                ["dash"],
                id="正常系: HLS有効時はdashのみスキップ",
            ),
        ],
    )
    def test_create_url_resolution_options_configures_extractor_args_for_hls(
        self, format_spec, use_hls, expected_skip
    ):
        """URL解決オプションのextractor_argsがHLSフラグに応じて設定されることを確認"""
        # Act
        options = YtDlpOptionsFactory.create_url_resolution_options(
            format_spec=format_spec, use_hls=use_hls
        )

        # Assert
        assert "extractor_args" in options
        assert "youtube" in options["extractor_args"]
        assert options["extractor_args"]["youtube"]["skip"] == expected_skip

    def test_create_url_resolution_options_inherits_base_options(self):
        """URL解決オプションが基本オプションを継承することを確認"""
        # Act
        base_options = YtDlpOptionsFactory.create_base_options()
        url_options = YtDlpOptionsFactory.create_url_resolution_options(format_spec="best")

        # Assert - 基本オプションのキーが全て含まれる
        for key in base_options.keys():
            assert key in url_options

    def test_create_url_resolution_options_has_skip_download(self):
        """URL解決オプションにskip_downloadが含まれることを確認"""
        # Act
        options = YtDlpOptionsFactory.create_url_resolution_options(format_spec="best")

        # Assert
        assert "skip_download" in options
        assert options["skip_download"] is True

    @pytest.mark.parametrize(
        "key, expected_value",
        [
            pytest.param("no_get_comments", True, id="正常系: no_get_commentsがTrueである"),
            pytest.param("writesubtitles", False, id="正常系: writesubtitlesがFalseである"),
            pytest.param("writethumbnail", False, id="正常系: writethumbnailがFalseである"),
        ],
    )
    def test_create_url_resolution_options_has_additional_flags(self, key, expected_value):
        """URL解決オプションに追加のフラグが正しく設定されることを確認"""
        # Act
        options = YtDlpOptionsFactory.create_url_resolution_options(format_spec="best")

        # Assert
        assert key in options
        assert options[key] == expected_value
