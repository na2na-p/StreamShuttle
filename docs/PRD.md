## 概要

「StreamShuttle」は、YouTubeのURLを解決し、直接的なメディアストリームURLを提供するWebアプリケーションおよびプロキシサービスを開発する。本製品は、シンプルなWeb UIを通じた動画ダウンロード機能と、VRChat等の外部アプリケーションから利用可能なAPIエンドポイントの2つの機能を提供する。

## 背景

現在、VRChatのビデオプレイヤーでYouTube動画を視聴する際、多くのユーザーが再生エラーに直面している。これは、VRChatに同梱されているURL解決ライブラリ（yt-dlp）のバージョンが古く、YouTube側の頻繁な仕様変更に追随できていないことが主な原因である 1。

この問題を解決するため、ユーザーは手動でライブラリを最新版に更新したり、認証情報を設定したりする必要があるが、この作業は技術的な知識を要し、非常に煩雑である 2。

この問題を解決し、技術的な知識がないユーザーでも安定して動画を視聴できる環境を提供するため、常に最新の状態に保たれた中央集権的なURL解決プロキシサービスを開発する。また、同様の技術を用いて、シンプルなWeb UIから動画をダウンロードできる機能も併せて提供する。

## Scientific Merits

本製品の導入による直接的な売上への影響を定量的に示すことは難しい。しかし、副次的なメリットとして、ユーザーがyt-dlpのメンテナンスに費やす時間の削減が挙げられる。仮に1ユーザーあたり月10分のメンテナンス時間が発生していると仮定し、1,000人のユーザーが本サービスを利用した場合、組織全体で月あたり約166時間分の非生産的な時間を削減できる可能性がある。

定性的には、VRChatユーザーの体験を大幅に向上させ、技術的な障壁なくコンテンツを楽しめるようにすることが最大のメリットである。これにより、プラットフォーム全体の活性化にも寄与できる可能性がある。

## Design Doc

本製品の技術設計は、これまでの議論に基づき、Python (FastAPI) をバックエンドフレームワークとして採用し、Kubernetes上にDeploymentリソースとしてデプロイする。

フロントエンド（Web UI）は、プレゼンテーション層としてFastAPIのJinja2テンプレート機能を使用する。本サービスはシンプルなフォームベースのUIを提供するため、React等のSPAフレームワークは採用せず、サーバーサイドレンダリングによる軽量な実装とする。

HTMLテンプレートは `src/streamshuttle/templates/` に配置し、静的アセット（CSS/JS）は `src/streamshuttle/static/` に配置する。

詳細な技術要件は後述の「技術的要求」セクションを参照すること。

## 参考ドキュメント

* yt-dlp GitHub Repository: [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) 6
* VRChat Ask Forum (Video Player関連スレッド): [https://ask.vrchat.com/](https://ask.vrchat.com/) 7

## 製品原則

* yt-dlpの複雑なメンテナンスを抽象化し、ユーザーにメンテナンスフリーで安定したURL解決機能を提供すること。

この原則は、本製品の核心的価値である。ユーザーは「プロキシのURLをビデオプレイヤーに設定するだけ」で、YouTube側の仕様変更やyt-dlpのアップデートを一切意識することなく、常に機能するサービスを享受できるべきである。

## やること/やらないこと

### やること

* Web UIを通じたYouTube動画のダウンロード機能の実装。
* VRChatのビデオプレイヤー（YamaPlayer, IwaSync等）と互換性のあるプロキシAPIエンドポイントの実装 11。
* サーバーサイドでの解決済みURLのキャッシング機能（Redis利用）の実装。
* yt-dlpライブラリを自動で最新版に更新するCI/CDパイプラインの構築。

### やらないこと

* サーバー側での動画コンテンツの再ストリーミング（中継）
  理由: 法的リスクの増大とサーバーリソースの膨大な消費を避けるため。本サービスはURLを解決し、クライアントを直接ストリームURLへリダイレクトする方式に限定する。
* ユーザーアカウント機能およびダウンロード履歴の保存
  理由: プロジェクトのスコープを最小限に保ち、プライバシーに関する懸念を排除するため。
* YouTube以外の動画サイトへの対応
  理由: まずは最も需要の高いYouTubeに特化し、サービスの安定性を確立することを優先する。

## 対象ユーザ

* VRChatユーザー: VRChat内のビデオプレイヤーで安定してYouTube動画を視聴したいエンドユーザー。
* 一般Webユーザー: 手軽にYouTube動画をダウンロードしたいエンドユーザー。
* 運用・開発チーム: 本サービスを安定して運用・保守する社内メンバー。

## ユースケース

### VRChatを利用するエンドユーザー

#### プロキシを利用して動画を再生する

ユーザーはVRChat内のビデオプレイヤー（例: YamaPlayer）のURL入力欄に、以下のような形式でURLを入力する。
https://streamshuttle.na2na.dev/resolve?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ
入力後、ビデオプレイヤーは問題なく動画の再生を開始する。ユーザーは、YouTube側の仕様変更やyt-dlpのバージョンを意識することなく、常に安定した視聴体験を得られる。

（UIモック: VRChatのビデオプレイヤーにURLが入力されている画像）

### Web UIを利用するエンドユーザー

#### 動画をダウンロードする

1. ユーザーはWebブラウザで本サービスのトップページ（https://streamshuttle.na2na.dev）にアクセスする。ページにはURL入力欄とボタンが表示されている。
   （UIモック: シンプルな入力フォームの画面）
2. ユーザーはYouTubeの動画URLを入力し、「フォーマット取得」ボタンを押す。
3. 画面にダウンロード可能なフォーマット（例: MP4 1080p, MP4 720p, MP3）がラジオボタン形式で表示される。
   （UIモック: フォーマット選択肢が表示された画面）
4. ユーザーは希望のフォーマットを選択し、「ダウンロード」ボタンを押す。
5. ブラウザのダウンロード機能が起動し、ファイルの保存が開始される。

### 運用・開発チームのメンバー

#### サービスの稼働状況を監視する

yt-dlpでのURL解決エラー率が一定の閾値を超えた場合、監視システム（例: Sentry, Datadog）がSlack等を通じてアラートを通知する。開発者はこの通知を受け、YouTube側の仕様変更があったことを即座に把握し、yt-dlpの更新状況を確認する。

## 市場分析

類似のYouTubeダウンロードサイトは多数存在するが、その多くは広告表示が多く、ユーザー体験を損なっている。また、VRChatユーザー向けのURL解決サービスという点では、コミュニティベースでの自助努力（手動でのファイル更新など）が主流であり、安定したマネージドサービスは存在しない。本サービスは、このニッチな市場において、信頼性と利便性で差別化を図ることができる。

## 競合分析

### VRChat-YT-DLP-Fix (GitHub)

2

* ユーザーのPC上で動作し、VRChatが使用するyt-dlp.exeを自動で最新版に置き換えるクライアントサイドのツール。
* 導入には一定の技術的知識が必要であり、ユーザーごとに設定が必要。
* 本サービスはサーバーサイドで問題を解決するため、ユーザーはクライアント側に何もインストールする必要がない。URLを指定するだけで誰でも同じ安定したサービスを利用できる点で優位性がある。

## 機能要求

### プロキシAPI

* GET /resolve エンドポイントを実装する。
* url クエリパラメータで対象のYouTube URLを受け取る。
* URL解決に成功した場合、HTTPステータスコード 302 Found と Location ヘッダーに解決済みのストリームURLを設定して応答する。
* URL解決に失敗した場合、400番台または500番台のステータスコードと、エラー内容を示すJSONを返す。
* **実装上の考慮事項**:
  - VRChatのyt-dlpとの互換性のため、302 Foundリダイレクトを使用している。（307 Temporary Redirectは一部の古いyt-dlpバージョンで適切に処理されず、プレーンテキストレスポンスはyt-dlpがURLを抽出できないため）
  - Unity Video PlayerはHLS (.m3u8) 非対応のため、yt-dlpのフォーマット選択でプログレッシブMP4を優先する。これにより、Unity Video PlayerとAVPro Video Playerの両方で再生可能なURLを提供する。

### バックエンド

* Redisをキャッシュストアとして利用する。解決済みのURLを動画IDをキーとしてキャッシュし、TTL（Time-To-Live）を1〜2時間に設定する。
* CI/CDパイプラインを構築し、yt-dlpの新しいリリースを検知して自動でコンテナイメージを再ビルド・デプロイする。

## 技術的要求

### アーキテクチャ

* バックエンド: Python 3.11+, FastAPI 14
* コアライブラリ: yt-dlp (Pythonライブラリとして直接インポート) 17
* フロントエンド: Jinja2テンプレート + Vanilla JavaScript
* 静的ファイル配置: `src/streamshuttle/templates/` (HTML), `src/streamshuttle/static/` (CSS/JS)
* テンプレートエンジン: FastAPIの `Jinja2Templates` および `StaticFiles` を使用
* インフラ: Kubernetes, Redis
* デプロイメント: Kubernetes Deployment リソースを使用し、HorizontalPodAutoscaler (HPA) による自動スケーリングを設定する。

### 可用性

サービスは24時間365日利用可能であることを目標とする。ただし、YouTube側の仕様変更とyt-dlpの対応の間に生じるタイムラグによる一時的な機能停止は許容範囲とする。

### セキュリティ

* アプリケーションは動画データを一切中継せず、リダイレクト方式に徹する。
* APIエンドポイントには、IPアドレスに基づいたレートリミットを導入し、DoS攻撃からサービスを保護する。

## 決まっていないこと

* 法的リスクの最終評価: 本サービスの運用は、YouTubeの利用規約および日本の著作権法に抵触する可能性がある 19。サービスの公開範囲（一般公開、限定公開など）を決定する前に、インターネット法を専門とする弁護士による正式な法的見解を取得する必要がある。
* Cookie認証の導入要否: YouTubeからのブロックが頻発し、IPアドレスの変更等で回避できない場合、yt-dlpのCookie利用機能 2 をサーバーサイドで実装するかを検討する。これにはアカウント管理やセキュリティ上の追加リスクが伴うため、慎重な判断が必要である。

## リリーススケジュールおよびマイルストーン

* 2025/11: PRD, Design Doc のFIX & 法的リスク評価の開始
* 2026/01: プロキシAPIのコア機能開発完了、Kubernetesへの初期デプロイ
* 2026/02: Web UIの開発と統合完了
* 2026/03: 関係者によるクローズドβテスト、監視・自動化機能の強化
* 2026/04: (法的評価の結果に基づき) リリース判断

上記スケジュールは暫定的なものであり、法的評価の結果や開発の進捗に応じて変更される可能性がある。

## コストと予算

* インフラ費用: Kubernetesクラスタ、Redisインスタンス、および関連するネットワーク費用（クラウドプロバイダーの料金体系に準ずる）。
* 開発人件費: 別途見積もり。

## マーケティング計画

法的リスク評価が完了し、サービスの公開が承認されるまでは、積極的なマーケティング活動は行わない。承認後、VRChat関連のコミュニティ（X, Discord, Reddit等）を中心に、サービスの安定性と利便性を訴求する告知を行う。

## 引用文献

1. I'm having issues with video players in VRChat, 10月 13, 2025にアクセス、 [https://help.vrchat.com/hc/en-us/articles/1500002378742-I-m-having-issues-with-video-players-in-VRChat](https://help.vrchat.com/hc/en-us/articles/1500002378742-I-m-having-issues-with-video-players-in-VRChat)
2. ShizCalev/VRChat-YT-DLP-Fix \- GitHub, 10月 13, 2025にアクセス、 [https://github.com/ShizCalev/VRChat-YT-DLP-Fix](https://github.com/ShizCalev/VRChat-YT-DLP-Fix)
3. Video players having issues \- Help\! \- VRChat Ask Forum, 10月 13, 2025にアクセス、 [https://ask.vrchat.com/t/video-players-having-issues/34472](https://ask.vrchat.com/t/video-players-having-issues/34472)
4. Videoplayer issues \- Help\! \- VRChat Ask Forum, 10月 13, 2025にアクセス、 [https://ask.vrchat.com/t/videoplayer-issues/41025](https://ask.vrchat.com/t/videoplayer-issues/41025)
5. how do I fix yt-dlp Errors? instructions unclear to fix them with VRchat specifically. \- Reddit, 10月 13, 2025にアクセス、 [https://www.reddit.com/r/VRchat/comments/1k97p1n/how\_do\_i\_fix\_ytdlp\_errors\_instructions\_unclear\_to/](https://www.reddit.com/r/VRchat/comments/1k97p1n/how_do_i_fix_ytdlp_errors_instructions_unclear_to/)
6. yt-dlp/yt-dlp: A feature-rich command-line audio/video downloader \- GitHub, 10月 13, 2025にアクセス、 [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
7. Specifically Youtube videos not playing as of yesterday \- Help\! \- VRChat Ask Forum, 10月 13, 2025にアクセス、 [https://ask.vrchat.com/t/specifically-youtube-videos-not-playing-as-of-yesterday/41893](https://ask.vrchat.com/t/specifically-youtube-videos-not-playing-as-of-yesterday/41893)
8. Youtube links dont work for me anymore across platforms \- Help\! \- VRChat Ask Forum, 10月 13, 2025にアクセス、 [https://ask.vrchat.com/t/youtube-links-dont-work-for-me-anymore-across-platforms/41760](https://ask.vrchat.com/t/youtube-links-dont-work-for-me-anymore-across-platforms/41760)
9. URL Videos not loading in any world's video players \- Help\! \- VRChat Ask Forum, 10月 13, 2025にアクセス、 [https://ask.vrchat.com/t/url-videos-not-loading-in-any-worlds-video-players/28199](https://ask.vrchat.com/t/url-videos-not-loading-in-any-worlds-video-players/28199)
10. Problem with video players that use URLs \- Help\! \- VRChat Ask Forum, 10月 13, 2025にアクセス、 [https://ask.vrchat.com/t/problem-with-video-players-that-use-urls/23692](https://ask.vrchat.com/t/problem-with-video-players-that-use-urls/23692)
11. koorimizuw/YamaPlayer: Modern video player for VRChat. \- GitHub, 10月 13, 2025にアクセス、 [https://github.com/koorimizuw/YamaPlayer](https://github.com/koorimizuw/YamaPlayer)
12. What URL links work in the VRChat video player besides YouTube? \- Reddit, 10月 13, 2025にアクセス、 [https://www.reddit.com/r/VRchat/comments/tkdlxb/what\_url\_links\_work\_in\_the\_vrchat\_video\_player/](https://www.reddit.com/r/VRchat/comments/tkdlxb/what_url_links_work_in_the_vrchat_video_player/)
13. Natsumi-sama/VRChat-YouTube-dl-stub \- GitHub, 10月 13, 2025にアクセス、 [https://github.com/Natsumi-sama/VRChat-YouTube-dl-stub](https://github.com/Natsumi-sama/VRChat-YouTube-dl-stub)
14. FastAPI, 10月 13, 2025にアクセス、 [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
15. Some Useful Patterns for Go's os/exec | DoltHub Blog, 10月 13, 2025にアクセス、 [https://www.dolthub.com/blog/2022-11-28-go-os-exec-patterns/](https://www.dolthub.com/blog/2022-11-28-go-os-exec-patterns/)
16. Next.js \+ FastAPI Tutorial: Track Every YouTube Video Event\!, 10月 13, 2025にアクセス、 [https://www.youtube.com/watch?v=7fIvHuqiLws](https://www.youtube.com/watch?v=7fIvHuqiLws)
17. yt-dlp \- PyPI, 10月 13, 2025にアクセス、 [https://pypi.org/project/yt-dlp/](https://pypi.org/project/yt-dlp/)
18. How to embed subtitles using Python version of yt-dlp ? \#6267 \- GitHub, 10月 13, 2025にアクセス、 [https://github.com/yt-dlp/yt-dlp/issues/6267](https://github.com/yt-dlp/yt-dlp/issues/6267)
19. www.tldrlegal.com, 10月 13, 2025にアクセス、 [https://www.tldrlegal.com/license/youtube-terms-of-service\#:\~:text=You%20may%20access%20Content%20for,the%20Service%20for%20that%20Content.](https://www.tldrlegal.com/license/youtube-terms-of-service#:~:text=You%20may%20access%20Content%20for,the%20Service%20for%20that%20Content.)
20. YouTube Terms of Service Explained in Plain English \- TLDRLegal, 10月 13, 2025にアクセス、 [https://www.tldrlegal.com/license/youtube-terms-of-service](https://www.tldrlegal.com/license/youtube-terms-of-service)
21. How to Download YouTube Videos Legally \- TechSmith, 10月 13, 2025にアクセス、 [https://www.techsmith.com/blog/download-youtube-videos/](https://www.techsmith.com/blog/download-youtube-videos/)
22. Japan introduces tough new copyright law \- JURIST Legal News, 10月 13, 2025にアクセス、 [https://www.jurist.org/news/2012/10/japan-introduces-tough-new-copyright-law/](https://www.jurist.org/news/2012/10/japan-introduces-tough-new-copyright-law/)
23. Japan to make illegal downloading of music, videos punishable with jail terms \- GaijinPot, 10月 13, 2025にアクセス、 [https://injapan.gaijinpot.com/uncategorized/2012/06/27/japan-to-make-illegal-downloading-of-music-videos-punishable-with-jail-terms/](https://injapan.gaijinpot.com/uncategorized/2012/06/27/japan-to-make-illegal-downloading-of-music-videos-punishable-with-jail-terms/)
24. en.wikipedia.org, 10月 13, 2025にアクセス、 [https://en.wikipedia.org/wiki/File\_sharing\_in\_Japan\#:\~:text=Unlike%20most%20other%20countries%2C%20filesharing,to%20two%20years%20for%20downloading.](https://en.wikipedia.org/wiki/File_sharing_in_Japan#:~:text=Unlike%20most%20other%20countries%2C%20filesharing,to%20two%20years%20for%20downloading.)
25. Terms of Service \- YouTube, 10月 13, 2025にアクセス、 [https://www.youtube.com/static?gl=FI\&template=terms](https://www.youtube.com/static?gl=FI&template=terms)
26. File-system conventions: route.js | Next.js, 10月 13, 2025にアクセス、 [https://nextjs.org/docs/app/api-reference/file-conventions/route](https://nextjs.org/docs/app/api-reference/file-conventions/route)
27. Video players don't work properly : r/VRchat \- Reddit, 10月 13, 2025にアクセス、 [https://www.reddit.com/r/VRchat/comments/1k1vn8r/video\_players\_dont\_work\_properly/](https://www.reddit.com/r/VRchat/comments/1k1vn8r/video_players_dont_work_properly/)
28. Actions · GitHub Marketplace \- Setup yt-dlp, 10月 13, 2025にアクセス、 [https://github.com/marketplace/actions/setup-yt-dlp](https://github.com/marketplace/actions/setup-yt-dlp)
