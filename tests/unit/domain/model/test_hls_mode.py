"""HLS モード ValueObject のテストモジュール。"""

import pytest

from streamshuttle.domain.model.hls_mode import HlsMode


@pytest.mark.parametrize(
    ("raw_value", "expected_mode"),
    [
        pytest.param(None, HlsMode.DISABLED, id="パラメータなしは無効"),
        pytest.param("false", HlsMode.DISABLED, id="false は無効"),
        pytest.param("0", HlsMode.DISABLED, id="0 は無効"),
        pytest.param("f", HlsMode.DISABLED, id="f は無効"),
        pytest.param("no", HlsMode.DISABLED, id="no は無効"),
        pytest.param("n", HlsMode.DISABLED, id="n は無効"),
        pytest.param("off", HlsMode.DISABLED, id="off は無効"),
        pytest.param("FALSE", HlsMode.DISABLED, id="大文字 false は無効"),
        pytest.param("F", HlsMode.DISABLED, id="大文字 f は無効"),
        pytest.param("N", HlsMode.DISABLED, id="大文字 n は無効"),
        pytest.param("true", HlsMode.ENABLED, id="true は有効"),
        pytest.param("1", HlsMode.ENABLED, id="1 は有効"),
        pytest.param("t", HlsMode.ENABLED, id="t は有効"),
        pytest.param("yes", HlsMode.ENABLED, id="yes は有効"),
        pytest.param("y", HlsMode.ENABLED, id="y は有効"),
        pytest.param("on", HlsMode.ENABLED, id="on は有効"),
        pytest.param("TRUE", HlsMode.ENABLED, id="大文字 true は有効"),
        pytest.param("T", HlsMode.ENABLED, id="大文字 t は有効"),
        pytest.param("Y", HlsMode.ENABLED, id="大文字 y は有効"),
        pytest.param("master", HlsMode.MASTER, id="master はマスター要求"),
    ],
)
def test_from_query_preserves_boolean_compatibility_and_accepts_master(raw_value, expected_mode):
    assert HlsMode.from_query(raw_value) is expected_mode


@pytest.mark.parametrize("raw_value", ["abc", "", "Master", "yeſ"])
def test_from_query_rejects_unsupported_values(raw_value):
    with pytest.raises(ValueError):
        HlsMode.from_query(raw_value)


def test_cache_key_values_preserve_existing_boolean_keys_and_add_master_key():
    assert HlsMode.DISABLED.cache_key_value == "False"
    assert HlsMode.ENABLED.cache_key_value == "True"
    assert HlsMode.MASTER.cache_key_value == "master"


def test_only_master_mode_uses_path_expire_for_cache_ttl():
    assert HlsMode.DISABLED.uses_path_expire is False
    assert HlsMode.ENABLED.uses_path_expire is False
    assert HlsMode.MASTER.uses_path_expire is True
