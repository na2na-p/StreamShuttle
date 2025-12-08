# syntax=docker/dockerfile:1

# ベースイメージ: Python 3.14のスリム版（.tool-versionsの要件に準拠）
FROM python:3.14.1-slim AS base

# Python環境設定
# - PYTHONUNBUFFERED: 標準出力のバッファリングを無効化（ログの即座出力）
# - PYTHONDONTWRITEBYTECODE: .pycファイルの生成を無効化（イメージサイズの削減）
# - PATH: プロジェクトの.venvディレクトリを優先（uvのデフォルト動作）
ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        PATH="/app/.venv/bin:$PATH" \
        PYTHONPATH="/app/src"

# ビルドツール、ffmpeg、Denoのインストール
# - build-essential: C拡張モジュール（uvloop等）のビルドに必要
# - ffmpeg: メディアのマージやトランスコードに必要
# - curl, unzip: Denoのインストールに必要
# - Deno: yt-dlpのYouTube完全サポートに必要なJavaScriptランタイム
#   (参照: https://github.com/yt-dlp/yt-dlp/issues/15012)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        curl \
        unzip \
        && rm -rf /var/lib/apt/lists/* \
        && curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh

# uvパッケージマネージャーのインストール（高速な依存関係解決）
RUN pip install --no-cache-dir uv

WORKDIR /app

# ビルダーステージ: 本番環境用の依存関係のみをインストール
FROM base AS builder

COPY pyproject.toml uv.lock* ./

# キャッシュマウントを使用して外部依存関係のみをインストール（プロジェクトパッケージは除外）
RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --frozen --no-dev --no-install-project

# アプリケーションコードをコピー
COPY . .

# プロジェクトパッケージをインストール
RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --frozen --no-dev --no-editable

# 開発ステージ: 開発用依存関係を含むすべての依存関係をインストール
FROM base AS development

COPY pyproject.toml uv.lock* ./

# キャッシュマウントを使用して外部依存関係のみをインストール（プロジェクトパッケージは除外）
RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --frozen --no-install-project

# アプリケーションコードをコピー
COPY . .

# プロジェクトパッケージをeditable modeでインストール
RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --frozen

# セキュリティ向上: 非rootユーザーで実行
RUN useradd -m -u 1000 appuser && \
        chmod +x entrypoint.sh && \
        chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# 開発サーバー起動（ホットリロード有効、ログ形式は環境変数で制御）
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--reload"]

# 本番ステージ: 最適化されたイメージ（開発用依存関係なし）
FROM base AS production

# ビルダーステージから本番用依存関係のみをコピー
COPY --from=builder /app/.venv /app/.venv

COPY . .

# セキュリティ向上: 非rootユーザーで実行
RUN useradd -m -u 1000 appuser && \
        chmod +x entrypoint.sh && \
        chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# 本番サーバー起動（ホットリロードなし、ログ形式は環境変数で制御）
ENTRYPOINT ["/app/entrypoint.sh"]
CMD []
