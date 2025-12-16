import os


def pytest_configure(config):
    """
    pytest設定時に実行されるフック関数

    テスト実行前に必要な環境変数を設定します。
    このフックはpytestの起動時、モジュールのインポート前に実行されます。
    """
    os.environ["SECURITY_CSRF_SECRET_KEY"] = "test-secret-key-for-testing-only"
