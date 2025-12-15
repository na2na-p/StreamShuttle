# syntax=docker/dockerfile:1

FROM python:3.14.1-slim AS base

ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        PATH="/app/.venv/bin:$PATH" \
        PYTHONPATH="/app/src"

# Deno: yt-dlpのYouTube完全サポートに必要（https://github.com/yt-dlp/yt-dlp/issues/15012）
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        curl \
        unzip \
        && rm -rf /var/lib/apt/lists/* \
        && curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh

RUN pip install --no-cache-dir uv

WORKDIR /app

FROM base AS builder

COPY pyproject.toml uv.lock* ./

RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --frozen --no-dev --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --frozen --no-dev --no-editable

FROM base AS development

RUN useradd -m -u 1000 appuser

COPY --chown=appuser:appuser pyproject.toml uv.lock* ./

RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --frozen --no-install-project

COPY --chown=appuser:appuser . .

RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --frozen

RUN chown -R appuser:appuser /app/.venv && \
        chmod +x entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--reload"]

FROM base AS production

RUN useradd -m -u 1000 appuser

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

COPY --chown=appuser:appuser . .

RUN chmod +x entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD []
