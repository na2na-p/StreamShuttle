"""HLS 解決モードを表す ValueObject。"""

from enum import Enum


class HlsMode(Enum):
    """ストリーム解決時の HLS 選択を表す。"""

    DISABLED = "False"
    ENABLED = "True"
    MASTER = "master"

    @classmethod
    def from_query(cls, value: str | None) -> "HlsMode":
        """HTTP クエリ値を HLS モードへ変換する。"""
        if value is None:
            return cls.DISABLED

        if not value.isascii():
            raise ValueError("unsupported hls mode")

        normalized_value = value.lower()
        if normalized_value in {"false", "0", "f", "no", "n", "off"}:
            return cls.DISABLED
        if normalized_value in {"true", "1", "t", "yes", "y", "on"}:
            return cls.ENABLED
        if value == cls.MASTER.value:
            return cls.MASTER
        raise ValueError("unsupported hls mode")

    @property
    def uses_hls(self) -> bool:
        """yt-dlp で HLS を許可するモードかを返す。"""
        return self is not HlsMode.DISABLED

    @property
    def is_master(self) -> bool:
        """HLS マスターマニフェストを要求するモードかを返す。"""
        return self is HlsMode.MASTER

    @property
    def uses_path_expire(self) -> bool:
        """URL path の expire を TTL に使うモードかを返す。"""
        return self is HlsMode.MASTER

    @property
    def cache_key_value(self) -> str:
        """既存キーと互換性のあるキャッシュキー値を返す。"""
        return self.value
