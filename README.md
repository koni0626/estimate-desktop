# 見積管理システム — Windowsデスクトップ版・設計書・ソースコード

このフォルダーは、デスクトップアプリのソース・設計書・配布用実行ファイル・Windowsインストーラーをまとめた独立プロジェクトです。通常の利用は[インストーラー](deliverables/EstimateDesktop-Setup-1.0.0.exe)から始めます。インストール方法、保存先、アンインストール時の扱いは[インストーラーの説明](docs/installer.md)を参照してください。

個人事業主・小規模チーム向けのWindowsデスクトップ版見積管理システムです。見積書の作成、会社・部・課別の閲覧権限、会社ごとの承認なし／多段階承認、日本語PDFの発行を中心に、案件・要望、受注、請求、全額入金確認まで操作できます。

設計と実装の対応を確認するには、まず [設計書セット](docs/design/README.md) を読んでください。[実装対応表](docs/design/implementation-map.md) からコードとテストを追えます。デスクトップ版の導入は [使い方](docs/desktop.md)、画面操作は [操作マニュアル](docs/manual/ja/01-first-steps.md) にあります。[note掲載用の商品説明案](docs/note-sales-page.md) も用意しています。

**設計書だけをCodexへ渡して新規実装する**場合は、[Codex向け再実装仕様書](docs/design/06-codex-rebuild-spec.md) から始めます。`scripts/package_spec.py` で設計書・API定義・DBスキーマ・マニュアルだけのZIPを作れます。

## すぐに使う（Windowsデスクトップ版）

`deliverables/EstimateDesktop-Setup-1.0.0.exe`を実行してインストールします。ZIPから起動したい場合は`deliverables/estimate2-windows-desktop.zip`を展開し、`Estimate2/Estimate2.exe`をダブルクリックします。Python、Node.js、DBサーバーを利用者側で起動する必要はありません。WindowsのMicrosoft Edge WebView2 Runtimeが必要です。空DBでは事業者名と自分の名前だけを登録し、次回からはログイン画面なしで開きます。既存DBの利用者が複数いる場合は従来のログイン画面を使います。業務データは`%LOCALAPPDATA%\Estimate2\estimate2.sqlite3`に保存されます。ウィンドウの「ファイル → データをバックアップ」からバックアップできます。詳しくは[デスクトップ版の使い方](docs/desktop.md)を参照してください。

## 開発環境とブラウザー版

- Windows PowerShell、Python 3.14、Node.js。SQLiteはPythonに同梱
- FastAPI / SQLAlchemy 2 / Alembic / React / TypeScript / Vite
- 開発用Web: `http://127.0.0.1:5185` / API仕様: `http://127.0.0.1:8005/docs`
- ソース起動時のDBは`.env`の`DATABASE_URL`に従います。配布EXEはユーザー別のアプリデータ領域に保存します。WebとAPIのポート、Cookie名は旧アプリと分離しています。

## ソースからの初回セットアップ

PostgreSQLなどのDBサーバーは不要です。

```powershell
cd E:\app\estimate-desktop
Copy-Item .env.example .env
.\scripts\setup.ps1
.\scripts\start.ps1
```

ブラウザーで `http://127.0.0.1:5185` を開くと、空のDBでは初回セットアップ画面が表示されます。事業者名・屋号、自分の名前、ユーザー名、12文字以上のパスワードを登録してください。最初の会社管理者として自動ログインします。登録後は初回セットアップを再実行できません。パスワードとDBファイルは自分で安全に管理してください。

ソースからデスクトップウィンドウで試す場合は、`requirements-desktop.txt`をインストールし、`frontend`で`npm run build`した後、`.\.venv\Scripts\pythonw.exe desktop.py`を実行します。EXEを再作成する場合は`.\scripts\build_desktop.ps1`を実行します。

デモを試す場合だけ、空DBで `.\scripts\setup.ps1 -Demo` を実行します。`-Demo` は架空のサンプル会社・ユーザー・取引先を投入し、初回セットアップ画面は表示されません。既存DBにデータがあればseedは上書きしません。サンプルデータは実際の取引ではありません。

|ユーザー名|会社・役割|デモパスワード|
|---|---|---|
|`solo`|個人事業・承認なし|`demo1234`|
|`staff`|チーム・一般担当者|`demo1234`|
|`manager`|チーム・課長、第1承認者|`demo1234`|
|`director`|チーム・部長、第2承認者|`demo1234`|
|`admin`|チーム・会社管理者|`demo1234`|
|`sales`|チーム・別課の担当者|`demo1234`|

停止は `.\scripts\stop.ps1`。SQLiteファイルは保持します。ローカルの `.env`、仮想環境、node_modules、DBデータは配布物に含めません。

作業データのバックアップは `.\.venv\Scripts\python.exe scripts\backup.py` で作成できます。SQLiteのバックアップAPIを使い、WAL上の変更も含む整合したファイルを `data/backups/` に保存します。このフォルダーも配布ZIPには含めません。

## 動作を確かめる

デスクトップの個人利用は初回設定後すぐに見積を作成し、「発行」からPDFを取得します。デモ投入時は `solo` で個人利用を、`staff` で申請して `manager`、`director` の順に承認するチーム利用を試せます。発行済みの見積は改版で新しい下書きを作れます。案件から要望を見積へ結び、発行後に受注・請求・入金まで試せます。

```powershell
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe -m pytest tests -q
cd frontend
npm run build
```

pytestは一時SQLiteファイルを作成・削除します。通常の `data/estimate2.sqlite3` はテストで変更しません。実行した結果は [検証記録](docs/design/verification-results.md) に記します。

旧PostgreSQL版のデータがある場合は、[移行手順](docs/design/05-verification-operation.md#55-postgresql版からの一回限りの移行) を参照してください。この環境では57行をSQLiteへコピーし、PDF等のバイナリのハッシュと外部キーを照合しました。PostgreSQL側のDBは残しています。

ソース付き配布用ZIPは `.\.venv\Scripts\python.exe scripts\package.py` で再生成できます。出力先は `deliverables/estimate2-design-source.zip`。ローカルの `.env`、仮想環境、依存パッケージの展開物、テストDBは含めず、ZIP内の `MANIFEST.sha256` に各ファイルのハッシュを記録します。Windows実行版ZIPは`build_desktop.ps1`で生成します。

設計書のみの配布ZIPは `.\.venv\Scripts\python.exe scripts\package_spec.py` で `deliverables/estimate2-spec-for-codex.zip` に出力します。アプリのソースコードとDBは含めません。

## 実装範囲と限界

実装済み：デスクトップ個人利用のログイン不要な初期設定・自動再開、ブラウザー開発版のユーザー名・パスワード認証、会社・部・課の閲覧分離、顧客・案件・要望・複数添付、見積作成／計算／多段階承認／PDF／改版／任意の印鑑画像、受注、請求書PDF、全額入金記録、操作履歴。

対象外：SSO、初回以外の公開ユーザー登録、招待・パスワード再設定、メール送付、発注・外注費、部分入金、決済、会計連携、本番用の試行制限・監視・バックアップ・負荷試験。デモデータ投入機能を含むローカル学習サンプルなので、そのまま外部公開しないでください。設計過程の古い検討資料は作業フォルダーの `docs/` 直下に残し、配布ZIPには含めません。販売・実装範囲の正本は `docs/design/` です。

## 主なディレクトリ

```text
backend/app/            API、モデル、認証、PDF、案件・受注・添付
backend/migrations/     AlembicのDB変更履歴
frontend/src/           React画面とAPIクライアント
docs/design/            現行実装に対応した設計書
docs/manual/ja/         操作マニュアル
tests/                  SQLiteの一時DBを使う統合テスト
scripts/                セットアップ、起動、停止
desktop.py              Windowsデスクトップ版の起動点
```

本プロジェクトは旧アプリの見積・業務機能を独立した教材として再構成したものです。日本語フォントのライセンスは `backend/assets/OFL.txt` に同梱しています。
