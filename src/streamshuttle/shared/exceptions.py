"""
カスタム例外定義モジュール

StreamShuttleアプリケーション全体で使用するカスタム例外クラスを定義します。
各例外は特定のエラー種別を表現し、適切なエラーハンドリングを可能にします。
"""


class StreamShuttleError(Exception):
    """
    StreamShuttle基底例外クラス

    StreamShuttleアプリケーション内で発生するすべてのカスタム例外の基底クラスです。
    この例外を継承することで、アプリケーション固有の例外を統一的に扱えます。
    """

    def __init__(self, message: str = "StreamShuttleでエラーが発生しました") -> None:
        """
        基底例外を初期化します

        Args:
            message: エラーメッセージ（デフォルト: "StreamShuttleでエラーが発生しました"）
        """
        self.message = message
        super().__init__(self.message)


class YouTubeResolverError(StreamShuttleError):
    """
    YouTube URL解決エラー例外クラス

    YouTube URLからストリームURLを解決する際に発生するエラーを表現します。
    yt-dlpによる解決失敗、無効なURL、アクセス権限エラーなどが該当します。
    """

    def __init__(self, message: str = "YouTube URLの解決に失敗しました") -> None:
        """
        YouTube URL解決エラーを初期化します

        Args:
            message: エラーメッセージ（デフォルト: "YouTube URLの解決に失敗しました"）
        """
        super().__init__(message)


class CacheError(StreamShuttleError):
    """
    キャッシュ操作エラー例外クラス

    Redisキャッシュへの読み書き操作時に発生するエラーを表現します。
    Redis接続エラー、タイムアウト、データ不整合などが該当します。
    """

    def __init__(self, message: str = "キャッシュ操作に失敗しました") -> None:
        """
        キャッシュ操作エラーを初期化します

        Args:
            message: エラーメッセージ（デフォルト: "キャッシュ操作に失敗しました"）
        """
        super().__init__(message)


class InvalidVideoIdError(StreamShuttleError):
    """
    不正なビデオIDエラー例外クラス

    YouTubeビデオIDが無効な形式または存在しない場合に発生するエラーを表現します。
    ビデオIDの形式チェック失敗、存在しないビデオへのアクセスなどが該当します。
    """

    def __init__(self, message: str = "ビデオIDが無効です") -> None:
        """
        不正なビデオIDエラーを初期化します

        Args:
            message: エラーメッセージ（デフォルト: "ビデオIDが無効です"）
        """
        super().__init__(message)


class InvalidUrlError(StreamShuttleError):
    """
    不正なURL例外クラス

    URLが無効な形式の場合に発生するエラーを表現します。
    HTTP/HTTPSスキームを持たないURL、不正なURL形式などが該当します。
    """

    def __init__(self, message: str = "URLが無効です") -> None:
        """
        不正なURLエラーを初期化します

        Args:
            message: エラーメッセージ（デフォルト: "URLが無効です"）
        """
        super().__init__(message)


class HlsNotSupportedError(StreamShuttleError):
    """
    HLS形式が要求されたが、hls=falseで拒否された場合

    ニコニコ動画はHLS専用形式のため、hls=falseの場合に発生します。
    """

    def __init__(self, message: str = "HLS形式がサポートされていません") -> None:
        """
        HLS非サポートエラーを初期化します

        Args:
            message: エラーメッセージ（デフォルト: "HLS形式がサポートされていません"）
        """
        super().__init__(message)


class TwitchResolverError(StreamShuttleError):
    """
    Twitch URL解決エラー例外クラス

    Twitch URLからストリームURLを解決する際に発生するエラーを表現します。
    yt-dlpによる解決失敗、無効なURL、アクセス権限エラーなどが該当します。
    """

    def __init__(self, message: str = "Twitch URLの解決に失敗しました") -> None:
        """
        Twitch URL解決エラーを初期化します

        Args:
            message: エラーメッセージ（デフォルト: "Twitch URLの解決に失敗しました"）
        """
        super().__init__(message)
