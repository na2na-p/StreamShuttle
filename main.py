"""
StreamShuttle FastAPIアプリケーション

YouTube URL解決とプロキシサービスのメインエントリーポイント。
VRChat動画プレイヤー向けのストリームURL解決サービスを提供します。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from streamshuttle.di.container import get_redis_dao
from streamshuttle.handler.download_handler import router as download_router
from streamshuttle.handler.resolve_handler import router as resolve_router
from streamshuttle.shared.config import config
from streamshuttle.shared.logging_config import setup_logging
from streamshuttle.shared.rate_limiter import limiter
from streamshuttle.shared.security_headers import SecurityHeadersMiddleware

# ログ設定を初期化（FastAPIアプリケーション作成の前に実行）
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションのライフサイクル管理

    アプリケーション起動時と終了時に実行される処理を定義します。
    主にRedis接続などのリソースの適切なクリーンアップを行います。

    Args:
        app: FastAPIアプリケーションインスタンス

    Yields:
        None: アプリケーション実行中

    Note:
        メモリリーク対策として、Redis接続を適切にクローズします。
        これにより、アプリケーション終了時のリソースリークを防ぎます。
    """
    # Startup: 起動時の処理（現在は特になし）
    yield
    # Shutdown: 終了時の処理
    redis_dao = get_redis_dao()
    await redis_dao.close()


app = FastAPI(
    title="StreamShuttle",
    description="YouTube URL resolver and proxy service for VRChat video players",
    version="0.1.0",
    lifespan=lifespan,
)

# レート制限設定
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# セキュリティヘッダーミドルウェア設定
app.add_middleware(SecurityHeadersMiddleware)

# CORSミドルウェア設定
# 本サービスはJinja2テンプレートによるSSRを採用しており、フロントエンドとバックエンドが
# 同一オリジンで動作するため、基本的にCORSは不要です。
# ALLOWED_ORIGINS環境変数が設定されている場合のみ、外部オリジンからのアクセスを許可します。
# （開発環境での利用や、特定の外部サービスとの連携が必要な場合を想定）
if config.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.ALLOWED_ORIGINS,  # 環境変数で明示的に許可されたオリジンのみ
        allow_credentials=False,  # クッキーを使用しないため無効化
        allow_methods=["GET", "POST"],  # 必要最小限のHTTPメソッドのみ許可
        allow_headers=["Content-Type", "Accept"],  # 必要最小限のヘッダーのみ許可
    )

# Jinja2テンプレート設定
templates = Jinja2Templates(directory="src/streamshuttle/templates")

# ルーター登録
app.include_router(resolve_router, tags=["Proxy API"])
app.include_router(download_router, tags=["Download API"])

# 静的ファイル配信
app.mount("/static", StaticFiles(directory="src/streamshuttle/static"), name="static")


@app.get("/")
async def index(request: Request):
    """
    Web UIのトップページを表示します

    YouTube動画のダウンロード機能を提供するシンプルなフォームUIをレンダリングします。
    ユーザーはYouTube URLを入力し、利用可能なフォーマットを取得した後、
    希望のフォーマットを選択してダウンロードできます。

    Args:
        request: FastAPIのRequestオブジェクト（Jinja2テンプレートレンダリングに必要）

    Returns:
        TemplateResponse: index.htmlテンプレートをレンダリングしたレスポンス
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/healthz")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}
