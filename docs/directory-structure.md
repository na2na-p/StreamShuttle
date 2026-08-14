# StreamShuttle ディレクトリ構造設計書

## 概要

本ドキュメントは、StreamShuttleプロジェクトのディレクトリ構造を定義します。本プロジェクトはドメイン駆動設計（DDD）アーキテクチャに基づき、Handler層、UseCase層、Domain層、Infrastructure層の4層構造を採用しています。

## アーキテクチャ原則

### カプセル化の原則

- 各レイヤー、各モジュールは「1つの目的」に対して「1つのモジュール」を対応させること
- モジュールには、対応する目的達成に必要十分なコードをカプセル化すること
- 目的ごとに不変条件が異なるため、関心の分離を徹底すること

### レイヤー間の依存関係

```
Handler → UseCase → Domain ← Infrastructure
Template（クライアント側） → Handler（バックエンドAPI）
```

- **Handler層**: 上位目的（呼び出す側）。FastAPIのエンドポイントを定義し、UseCaseを呼び出す
- **UseCase層**: ビジネスロジックを実装。RepositoryやQueryServiceのインターフェースに依存
- **Domain層**: ビジネスルールを表現。外部依存を持たない純粋なドメインモデル
- **Infrastructure層**: 下位目的（呼び出される側）。外部サービス（DB、API等）との実際の接続を実装
- **Template/Static層**: プレゼンテーション層。Handler層と同等の位置づけで、バックエンドAPIを呼び出すクライアント

## ディレクトリ構造

```
/Users/na2na/repos/na2na-p/StreamShuttle/
├── .cursor/                          # Cursorエディタ設定（既存）
│   └── rules/                        # DDDアーキテクチャルール定義
├── .dockerignore
├── .gitignore
├── .tool-versions
├── Dockerfile
├── README.md
├── docker-compose.yml
├── pyproject.toml                    # Pythonプロジェクト設定
├── uv.lock                           # 依存関係ロックファイル
├── main.py                           # FastAPIアプリケーションエントリーポイント
│
├── src/                              # ソースコードルート
│   └── streamshuttle/                # メインパッケージ
│       ├── __init__.py
│       │
│       ├── handler/                  # Handler層: FastAPIエンドポイント
│       │   ├── __init__.py
│       │   ├── resolve_handler.py    # URL解決エンドポイント（GET /resolve）
│       │   └── download_handler.py   # ダウンロード関連エンドポイント（Web UI用）
│       │
│       ├── usecase/                  # UseCase層: ビジネスロジック
│       │   ├── __init__.py
│       │   │
│       │   ├── command/              # コマンド系UseCase（更新操作）
│       │   │   ├── __init__.py
│       │   │   └── cache_stream_url_use_case.py  # ストリームURLキャッシュ登録UseCase
│       │   │
│       │   ├── query/                # クエリ系UseCase（参照操作）
│       │   │   ├── __init__.py
│       │   │   ├── resolve_youtube_url_use_case.py      # YouTube URL解決UseCase
│       │   │   └── get_available_formats_use_case.py    # 利用可能フォーマット取得UseCase
│       │   │
│       │   ├── dto/                  # データ転送オブジェクト
│       │   │   ├── __init__.py
│       │   │   ├── stream_url_dto.py              # ストリームURL情報DTO
│       │   │   └── video_format_dto.py            # 動画フォーマット情報DTO
│       │   │
│       │   ├── query_service/        # QueryServiceインターフェース
│       │   │   ├── __init__.py
│       │   │   ├── stream_url_query_service.py    # ストリームURL取得インターフェース
│       │   │   └── video_format_query_service.py  # 動画フォーマット取得インターフェース
│       │   │
│       │   └── external/             # Externalインターフェース
│       │       ├── __init__.py
│       │       └── youtube_resolver.py            # YouTube URL解決インターフェース
│       │
│       ├── domain/                   # Domain層: ドメインモデル
│       │   ├── __init__.py
│       │   │
│       │   ├── model/                # ドメインモデル
│       │   │   ├── __init__.py
│       │   │   │
│       │   │   ├── stream_url/       # StreamUrl Aggregate
│       │   │   │   ├── __init__.py
│       │   │   │   ├── stream_url.py              # StreamUrl Aggregate
│       │   │   │   ├── video_id.py                # VideoId ValueObject
│       │   │   │   ├── resolved_url.py            # ResolvedUrl ValueObject
│       │   │   │   └── cache_expiry.py            # CacheExpiry ValueObject
│       │   │   │
│       │   │   └── video_format/     # VideoFormat Aggregate
│       │   │       ├── __init__.py
│       │   │       ├── video_format.py            # VideoFormat Aggregate
│       │   │       ├── format_id.py               # FormatId ValueObject
│       │   │       ├── quality.py                 # Quality ValueObject
│       │   │       └── codec.py                   # Codec ValueObject
│       │   │
│       │   └── repository/           # Repositoryインターフェース
│       │       ├── __init__.py
│       │       └── stream_url_repository.py       # StreamUrl Repository インターフェース
│       │
│       ├── infrastructure/           # Infrastructure層: 外部依存実装
│       │   ├── __init__.py
│       │   │
│       │   ├── repository/           # Repository実装
│       │   │   ├── __init__.py
│       │   │   └── stream_url_repository.py       # Redis実装のStreamUrlRepository
│       │   │
│       │   ├── query_service/        # QueryService実装
│       │   │   ├── __init__.py
│       │   │   ├── stream_url_query_service.py    # Redis参照実装
│       │   │   └── video_format_query_service.py  # yt-dlp利用フォーマット取得実装
│       │   │
│       │   ├── external/             # External実装（外部API連携）
│       │   │   ├── __init__.py
│       │   │   └── youtube_resolver.py            # yt-dlp利用のYouTube解決実装
│       │   │
│       │   └── dao/                  # データアクセスオブジェクト
│       │       ├── __init__.py
│       │       └── redis_dao.py                   # Redis接続・操作DAO
│       │
│       ├── templates/                # Jinja2テンプレート（HTML）
│       │   ├── base.html             # ベーステンプレート
│       │   └── index.html            # トップページ（Web UI）
│       │
│       ├── static/                   # 静的ファイル
│       │   ├── css/
│       │   │   └── style.css         # スタイルシート
│       │   └── js/
│       │       └── app.js            # クライアントサイドロジック
│       │
│       ├── shared/                   # 共通ユーティリティ
│       │   ├── __init__.py
│       │   ├── exceptions.py         # カスタム例外定義
│       │   ├── config.py             # 設定管理
│       │   └── logging_config.py     # ロギング設定
│       │
│       └── di/                       # 依存性注入設定
│           ├── __init__.py
│           └── container.py          # DIコンテナ設定
│
├── tests/                            # テストコード
│   ├── __init__.py
│   ├── unit/                         # ユニットテスト
│   │   ├── __init__.py
│   │   ├── handler/
│   │   ├── usecase/
│   │   ├── domain/
│   │   └── infrastructure/
│   │
│   ├── integration/                  # 統合テスト
│   │   ├── __init__.py
│   │   └── api/
│   │
│   └── e2e/                          # E2Eテスト
│       ├── __init__.py
│       └── test_resolve_flow.py
│
└── docs/                             # ドキュメント
    ├── PRD.md                        # 製品要求仕様書（既存）
    └── directory-structure.md        # 本ドキュメント
```

## 各ディレクトリの役割

### Handler層 (`src/streamshuttle/handler/`)

**役割**: FastAPIのエンドポイント定義とHTTPリクエスト/レスポンス処理

- FastAPIの `APIRouter` を利用したルーティング定義
- HTTPリクエストパラメータのバリデーションと変換
- UseCaseの呼び出しとHTTPレスポンスの生成
- エラーハンドリングとHTTPステータスコードの設定

**命名規則**:
- ファイル名: `{リソース名}_handler.py`
- クラス名: 使用せず、関数ベースのハンドラーを推奨（FastAPIの慣習に従う）

**例**:
```python
# resolve_handler.py
from fastapi import APIRouter, Query, Depends
from streamshuttle.usecase.query.resolve_youtube_url_use_case import ResolveYoutubeUrlUseCase

router = APIRouter()


@router.get("/resolve")
async def resolve_url(url: str = Query(...), use_case: ResolveYoutubeUrlUseCase = Depends()):
    result = await use_case.execute(url)
    return RedirectResponse(url=result.stream_url, status_code=307)
```

### テンプレート層 (`src/streamshuttle/templates/`)

**役割**: Jinja2テンプレートによるHTMLレンダリング

- FastAPIの `Jinja2Templates` を利用したサーバーサイドレンダリング
- シンプルなフォームベースのUI提供
- バックエンドAPIエンドポイント（/formats, /download）と連携
- ベーステンプレートによる共通レイアウト管理

**命名規則**:
- ファイル名: `{ページ名}.html`
- ベーステンプレート: `base.html`

**例**:
```html
<!-- templates/index.html -->
{% extends "base.html" %}
{% block content %}
<form id="download-form">
  <input type="text" name="url" placeholder="YouTube URL" required>
  <button type="button" id="fetch-formats">フォーマット取得</button>
</form>
<div id="formats-container"></div>
<div id="download-link"></div>
{% endblock %}
```

**ベーステンプレート構造**:
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}StreamShuttle{% endblock %}</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
  {% block content %}{% endblock %}
  <script src="/static/js/app.js"></script>
</body>
</html>
```

### 静的ファイル層 (`src/streamshuttle/static/`)

**役割**: CSS、JavaScript等の静的アセット配信

- FastAPIの `StaticFiles` でマウント（例: `app.mount("/static", StaticFiles(directory="static"), name="static")`）
- クライアントサイドのフォーム操作、APIコール処理
- スタイリング（CSS）
- 非同期通信（Fetch API）によるバックエンドAPIとの連携

**命名規則**:
- CSS: `style.css`, `{機能名}.css`
- JS: `app.js`, `{機能名}.js`

**例（JavaScript）**:
```javascript
// static/js/app.js
document.getElementById('fetch-formats').addEventListener('click', async () => {
  const url = document.querySelector('input[name="url"]').value;

  // バックエンドAPI（/formats）を呼び出し
  const response = await fetch(`/api/formats?url=${encodeURIComponent(url)}`);
  const formats = await response.json();

  // フォーマット一覧を表示
  const container = document.getElementById('formats-container');
  container.innerHTML = formats.map(f =>
    `<button data-format="${f.format_id}">${f.quality} - ${f.codec}</button>`
  ).join('');
});
```

**例（CSS）**:
```css
/* static/css/style.css */
body {
  font-family: sans-serif;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

#download-form input {
  width: 70%;
  padding: 10px;
}

#download-form button {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  cursor: pointer;
}
```

### UseCase層 (`src/streamshuttle/usecase/`)

**役割**: ビジネスロジックの実装とユースケースフローの制御

#### Command (`usecase/command/`)
- 更新系の操作を実装（CQRSのCommand側）
- Repository（書き込み）とExternalインターフェースに依存
- トランザクション境界を定義
- **必ずAggregateのメソッドを経由してドメインロジックを実行すること**
- Aggregateの不変条件を維持するため、直接Repositoryに保存せず、Aggregateで検証後に保存

**命名規則**:
- ファイル名: `{動詞}_{対象}_use_case.py` (例: `cache_stream_url_use_case.py`)
- クラス名: `{動詞}{対象}UseCase` (例: `CacheStreamUrlUseCase`)

#### Query (`usecase/query/`)
- 参照系の操作を実装（CQRSのQuery側）
- QueryServiceとExternalインターフェースに依存
- ドメインモデルを経由せず、DTOで直接データを返す

**命名規則**:
- ファイル名: `{動詞}_{対象}_use_case.py` (例: `resolve_youtube_url_use_case.py`)
- クラス名: `{動詞}{対象}UseCase` (例: `ResolveYoutubeUrlUseCase`)

#### DTO (`usecase/dto/`)
- QueryServiceの戻り値として使用
- イミュータブルなデータ構造
- Pydantic `BaseModel` を利用してシリアライズ可能に

**命名規則**:
- ファイル名: `{モデル名}_dto.py` (例: `stream_url_dto.py`)
- クラス名: `{モデル名}Dto` (例: `StreamUrlDto`)

#### QueryService (`usecase/query_service/`)
- データベースからの参照専用インターフェース
- DTOを返すメソッドのみ定義

**命名規則**:
- ファイル名: `{対象}_query_service.py` (例: `stream_url_query_service.py`)
- クラス名: `{対象}QueryService` (例: `StreamUrlQueryService`)

#### External (`usecase/external/`)
- 外部サービス連携用のインターフェース
- yt-dlpなどの外部ライブラリ呼び出しを抽象化

**命名規則**:
- ファイル名: `{サービス名}_resolver.py` (例: `youtube_resolver.py`)
- クラス名: `{サービス名}Resolver` (例: `YoutubeResolver`)

### Domain層 (`src/streamshuttle/domain/`)

**役割**: ビジネスルールの表現と整合性の維持

#### Model (`domain/model/`)

Domain層の中核。以下の要素で構成：

**Aggregate**:
- トランザクション境界を表す
- 必ずIDを持つ
- ValueObjectやEntityを保持
- フィールド間の整合性を維持するドメインロジックを実装

**Entity**:
- IDを持つドメインオブジェクト
- Aggregateのフィールドとして存在
- ライフサイクルを通じて同一性を保つ

**ValueObject**:
- IDを持たないドメインオブジェクト
- イミュータブル
- 値による等価性判定

**命名規則**:
- Aggregateディレクトリ: `{aggregate名}/` (例: `stream_url/`)
- Aggregateファイル: `{aggregate名}.py` (例: `stream_url.py`)
- Aggregateクラス: `{Aggregate名}` (例: `StreamUrl`)
- ValueObjectファイル: `{value_object名}.py` (例: `video_id.py`)
- ValueObjectクラス: `{ValueObject名}` (例: `VideoId`)

**例**:
```python
# domain/model/stream_url/stream_url.py
from dataclasses import dataclass
from .video_id import VideoId
from .resolved_url import ResolvedUrl
from .cache_expiry import CacheExpiry


@dataclass(frozen=True)
class StreamUrl:
    """StreamUrl Aggregate"""

    _video_id: VideoId
    _resolved_url: ResolvedUrl
    _cache_expiry: CacheExpiry

    @property
    def video_id(self) -> VideoId:
        """VideoIDを取得"""
        return self._video_id

    @property
    def resolved_url(self) -> ResolvedUrl:
        """解決済みURLを取得"""
        return self._resolved_url

    @property
    def cache_expiry(self) -> CacheExpiry:
        """キャッシュ期限を取得"""
        return self._cache_expiry

    def is_expired(self) -> bool:
        """キャッシュが期限切れかを判定"""
        return self._cache_expiry.is_expired()
```

#### Repository (`domain/repository/`)

- Aggregate単位でのデータ永続化インターフェース
- 1 Aggregate = 1 Repository
- CommandUseCaseからのみ呼び出される

**重要**: Repositoryは更新系（Command）専用です。参照系の操作（find_by_*など）は`QueryService`に実装してください。

**命名規則**:
- ファイル名: `{aggregate名}_repository.py` (例: `stream_url_repository.py`)
- クラス名: `{Aggregate名}Repository` (例: `StreamUrlRepository`)

**例**:
```python
# domain/repository/stream_url_repository.py
from abc import ABC, abstractmethod
from ..model.stream_url.stream_url import StreamUrl


class StreamUrlRepository(ABC):
    """StreamUrl Repository インターフェース（更新系専用）"""

    @abstractmethod
    async def save(self, stream_url: StreamUrl) -> None:
        """StreamUrlを保存"""
        pass

    # find_by_video_idメソッドは削除（QueryServiceに移動）
```

### Infrastructure層 (`src/streamshuttle/infrastructure/`)

**役割**: 外部依存の実装詳細

#### Repository (`infrastructure/repository/`)

- Domain層のRepositoryインターフェースを実装
- Redis、RDBMSなどへの実際の永続化処理
- DAOを利用してデータアクセス

**命名規則**:
- ファイル名: `{aggregate名}_repository.py` (実装するインターフェースと同名)
- クラス名: `{Aggregate名}Repository` (実装するインターフェースと同名)

**例**:
```python
# infrastructure/repository/stream_url_repository.py
from streamshuttle.domain.repository.stream_url_repository import StreamUrlRepository
from streamshuttle.infrastructure.dao.redis_dao import RedisDao


class StreamUrlRepository(StreamUrlRepository):
    """Redis実装のStreamUrlRepository"""

    def __init__(self, redis_dao: RedisDao):
        self._redis_dao = redis_dao

    async def save(self, stream_url: StreamUrl) -> None:
        # AggregateをRedisに保存
        await self._redis_dao.set(
            key=stream_url.video_id.value,
            value=stream_url.resolved_url.value,
            ttl=stream_url.cache_expiry.ttl_seconds,
        )
```

#### QueryService (`infrastructure/query_service/`)

- UseCase層のQueryServiceインターフェースを実装
- データベースからの参照専用実装
- DTOを直接生成して返す

**命名規則**:
- ファイル名: `{対象}_query_service.py` (実装するインターフェースと同名)
- クラス名: `{対象}QueryService` (実装するインターフェースと同名)

#### External (`infrastructure/external/`)

- UseCase層のExternalインターフェースを実装
- 外部API、外部ライブラリの直接呼び出し
- yt-dlp、YouTube API等の具体的な実装

**命名規則**:
- ファイル名: `{サービス名}_resolver.py` (実装するインターフェースと同名)
- クラス名: `{サービス名}Resolver` (実装するインターフェースと同名)

**例**:
```python
# infrastructure/external/youtube_resolver.py
import yt_dlp
from streamshuttle.usecase.external.youtube_resolver import YoutubeResolver


class YoutubeResolver(YoutubeResolver):
    """yt-dlp実装のYoutubeResolver"""

    async def resolve_url(self, youtube_url: str) -> str:
        ydl_opts = {"format": "best"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info["url"]
```

#### DAO (`infrastructure/dao/`)

- データベース接続とクエリ実行
- ORM（SQLAlchemyなど）やRedisクライアントのラッパー
- Repositoryから呼び出される

**命名規則**:
- ファイル名: `{データストア名}_dao.py` (例: `redis_dao.py`)
- クラス名: `{データストア名}Dao` (例: `RedisDao`)

### 共通層 (`src/streamshuttle/shared/`)

**役割**: 全レイヤーで共通利用されるユーティリティ

- `exceptions.py`: カスタム例外クラス
- `config.py`: 環境変数読み込み、設定管理
- `logging_config.py`: ロギング設定（JSON形式の構造化ログ、テキスト形式ログの切り替え）

### 依存性注入 (`src/streamshuttle/di/`)

**役割**: DIコンテナの設定とインスタンス管理

- FastAPIの `Depends` を利用した依存性注入
- インターフェースと実装のバインディング
- ライフサイクル管理（シングルトン、リクエストスコープ等）

### テスト (`tests/`)

**構造**:
- `unit/`: ユニットテスト（モック使用、レイヤー別）
- `integration/`: 統合テスト（実際のDB、Redis使用）
- `e2e/`: エンドツーエンドテスト（API経由のシナリオテスト）

**命名規則**:
- ファイル名: `test_{テスト対象}.py`
- テスト関数: `test_{機能名}`

## ファイル命名規則まとめ

### Python命名規則（PEP 8準拠）

- **ファイル名**: `snake_case.py`
- **クラス名**: `PascalCase`
- **関数/メソッド名**: `snake_case`
- **定数**: `UPPER_SNAKE_CASE`
- **プライベート**: `_leading_underscore`

### レイヤー別命名パターン

| レイヤー | ファイル名パターン | クラス名パターン |
|---------|------------------|----------------|
| Handler | `{リソース}_handler.py` | 関数ベース推奨 |
| Template | `{ページ名}.html` | - |
| Static (CSS) | `style.css`, `{機能名}.css` | - |
| Static (JS) | `app.js`, `{機能名}.js` | - |
| CommandUseCase | `{動詞}_{対象}_use_case.py` | `{動詞}{対象}UseCase` |
| QueryUseCase | `{動詞}_{対象}_use_case.py` | `{動詞}{対象}UseCase` |
| DTO | `{モデル名}_dto.py` | `{モデル名}Dto` |
| QueryService | `{対象}_query_service.py` | `{対象}QueryService` |
| External | `{サービス名}_resolver.py` | `{サービス名}Resolver` |
| Aggregate | `{aggregate名}.py` | `{Aggregate名}` |
| Entity | `{entity名}.py` | `{Entity名}` |
| ValueObject | `{value_object名}.py` | `{ValueObject名}` |
| Repository (interface) | `{aggregate名}_repository.py` | `{Aggregate名}Repository` |
| Repository (impl) | `{aggregate名}_repository.py` | `{Aggregate名}Repository` |
| DAO | `{データストア名}_dao.py` | `{データストア名}Dao` |

## DDDアーキテクチャとの対応関係

### レイヤー間依存フロー

```
[Handler層]
    ↓ 呼び出し
[UseCase層] ← インターフェース定義
    ↓ 実装
[Domain層] ← ビジネスルール
    ↑ 実装
[Infrastructure層] ← 技術詳細
```

### CQRS（Command Query Responsibility Segregation）適用

- **Command（更新系）**: CommandUseCase → Repository → Aggregate
- **Query（参照系）**: QueryUseCase → QueryService → DTO

CommandとQueryで経路を分離し、参照はAggregateを経由せず高速化。

### 依存性逆転の原則（DIP）適用箇所

1. **UseCase → Repository**: Domain層にインターフェース、Infrastructure層に実装
2. **UseCase → QueryService**: UseCase層にインターフェース、Infrastructure層に実装
3. **UseCase → External**: UseCase層にインターフェース、Infrastructure層に実装

これにより、ビジネスロジックが技術詳細に依存しない設計を実現。

## Python/FastAPI固有の注意事項

### 1. Pydanticとの統合

- **DTO**: Pydantic `BaseModel` を継承し、自動シリアライズを活用
- **ValueObject**: `@dataclass` または Pydantic `BaseModel` を使用し、バリデーションを実装

### 2. 非同期処理

- FastAPIは非同期処理（async/await）をサポート
- Repository、QueryService、Externalの実装は `async def` で定義
- Redis、DBアクセスには非同期クライアント（`aioredis`、`asyncpg`等）を使用

### 3. 依存性注入

- FastAPIの `Depends` を活用
- `di/container.py` でインスタンス生成ロジックを集約
- ライフサイクル管理（`yield` によるクリーンアップ）

### 4. パッケージ構成

- `src/streamshuttle/` をメインパッケージとし、`main.py` はルートに配置
- `pyproject.toml` の `[tool.setuptools]` で `src` レイアウトを指定

### 5. テスト実行

- `pytest` を使用
- `tests/` ディレクトリは `src/` と並列配置
- `pytest.ini` または `pyproject.toml` で設定管理

### 6. 型ヒント

- Python 3.11+ の型ヒント機能を最大限活用
- `mypy` による静的型チェックを推奨

### 7. イミュータビリティ

- Aggregateは `@dataclass(frozen=True)` でイミュータブル化
- ValueObjectも `frozen=True` を使用

## StreamShuttle機能要件との対応

### 主要機能とDDD要素のマッピング

#### 1. プロキシAPI（GET /resolve）

- **Handler**: `resolve_handler.py`
- **UseCase**: `ResolveYoutubeUrlUseCase` (Query)
- **QueryService**: `StreamUrlQueryService` (キャッシュ参照)
- **External**: `YoutubeResolver` (yt-dlp実行)
- **Aggregate**: `StreamUrl` (キャッシュデータ)

**フロー**:
1. Handler がリクエスト受信
2. QueryUseCase がキャッシュをQueryServiceで確認
3. キャッシュミス時、External（yt-dlp）で解決
4. CommandUseCase でAggregateを生成し、ドメインロジック実行後、Repositoryでキャッシュに保存（非同期）
5. Handler が307リダイレクトレスポンス

#### 2. Web UIダウンロード機能

- **Template**: `index.html` (フォームUI)
- **Static**: `app.js` (クライアントサイドロジック), `style.css`
- **Handler**: `download_handler.py`
- **UseCase**:
  - `GetAvailableFormatsUseCase` (フォーマット取得)
  - `ResolveYoutubeUrlUseCase` (ダウンロードURL取得)
- **External**: `YoutubeResolver`
- **DTO**: `VideoFormatDto`

**フロー**:
1. ユーザーがブラウザで `index.html` を表示（Jinja2テンプレートレンダリング）
2. JavaScript（`app.js`）がフォーマット取得ボタンクリックを検知
3. Fetch APIでバックエンドAPI（`GET /api/formats?url=...`）を呼び出し
4. Handler がリクエスト受信、QueryUseCase がyt-dlpから利用可能フォーマット取得
5. Handler がフォーマット一覧（JSON）をレスポンス
6. JavaScript がフォーマット選択UIを動的生成
7. ユーザーがフォーマット選択後、ダウンロードURL取得API（`GET /api/download?url=...&format=...`）を呼び出し
8. Handler がストリームURLへ307リダイレクト、またはダウンロードリンクを返す

#### 3. Redisキャッシング

- **Repository**: `StreamUrlRepository` (キャッシュ書き込み)
- **QueryService**: `StreamUrlQueryService` (キャッシュ読み込み)
- **DAO**: `RedisDao` (Redis接続)
- **Aggregate**: `StreamUrl` (TTL付きURL情報)

### ドメインモデル設計

#### StreamUrl Aggregate

```python
StreamUrl (Aggregate)
├── video_id: VideoId (ValueObject) - YouTubeビデオID
├── resolved_url: ResolvedUrl (ValueObject) - 解決済みストリームURL
└── cache_expiry: CacheExpiry (ValueObject) - キャッシュ有効期限
```

#### VideoFormat Aggregate（拡張時）

```python
VideoFormat (Aggregate)
├── format_id: FormatId (ValueObject) - フォーマットID
├── quality: Quality (ValueObject) - 画質（1080p, 720p等）
└── codec: Codec (ValueObject) - コーデック情報
```

## 決まっていないこと

### フロントエンド関連

#### 1. HTMLファイルのインデント設定
現状の `.editorconfig` にはHTMLファイル用のインデント設定が含まれていません。以下の追加を検討する必要があります：

```ini
[*.html]
indent_style = space
indent_size = 2
```

#### 2. JavaScriptファイルのフォーマット設定
JavaScriptのコーディング規約（セミコロン有無、クォートスタイル等）が未定義です。シンプルなアプリケーションのため、Prettier等の導入は不要と思われますが、基本的なスタイルガイドの策定が望ましいです。

#### 3. CSSフレームワークの採用有無
現状は素のCSSを想定していますが、簡易的なスタイリングのため、CDN経由でのシンプルなCSSフレームワーク（例: Pico.css, Water.css）の採用も検討可能です。

## まとめ

本ディレクトリ構造は、以下の原則に基づいています：

1. **DDDアーキテクチャの厳格な適用**: `.cursor/rules/ddd/` のルールに完全準拠
2. **責務の明確な分離**: 各レイヤーが独立した責務を持ち、疎結合を実現
3. **Python/FastAPIベストプラクティス**: 非同期処理、型ヒント、Pydantic活用
4. **テスタビリティ**: 依存性注入により、モック可能な設計
5. **拡張性**: 新機能追加時も既存コードへの影響を最小化
6. **シンプルなフロントエンド**: Jinja2テンプレート + Vanilla JavaScript による軽量なWeb UI

この構造により、StreamShuttleは保守性・拡張性・テスタビリティを兼ね備えた堅牢なアプリケーションとして実装可能です。
