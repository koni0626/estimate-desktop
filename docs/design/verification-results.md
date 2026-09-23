# 検証記録

実施日：2026-09-23。対象：`E:\app\estimate-desktop` のSQLite版Windowsデスクトップ実装。依存関係の導入、画面・EXE・インストーラーの再ビルドと44件のテストをこのフォルダーで実行した。

|確認|結果|
|---|---|
|SQLite `data/estimate2.sqlite3` にAlembic初期マイグレーション適用|成功|
|旧PostgreSQLからの一回限りの移行|19テーブル・57行をコピー。PDF等のバイナリハッシュと外部キーを照合し成功。旧DBは保持|
|`python -m alembic check`|モデルとSQLiteスキーマの差分なし|
|`python -m pytest tests -q`|**44件成功**、失敗0件。初回セットアップ、再登録拒否、同時登録の1件制限、外部Origin拒否、デスクトップ無入力再開・複数利用者の自動選択拒否・DBバックアップを含む。通常DBは変更しない|
|`node --test frontend/project-dashboard.test.mjs`|案件ダッシュボードの集計3件成功|
|`npm run build`|TypeScriptコンパイル、Vite本番ビルド成功|
|`ruff check backend tests scripts --select E4,E7,E9,F --ignore E402`|成功。E402はルーター登録時の遅延importを除外|
|SQLite版の画面・API起動|Web 5185、API 8005で起動。healthが`sqlite`を返した|
|SQLite版のAPI操作|`solo`ログイン、見積7件取得、PDF取得200 / `application/pdf`|
|`scripts/setup.ps1` と `scripts/start.ps1`|PostgreSQLサーバーを使わず成功|
|設計書のみの配布ZIP|26ファイル。Codex向け再実装仕様書、デスクトップ・インストーラー設計、OpenAPI定義、SQLiteスキーマ、操作マニュアルを含み、アプリソースとDBを含まない|
|ソース付き配布ZIP|100ファイル。ローカルDB、接続情報、展開済み依存パッケージを含まない|
|`scripts/backup.py`|稼働中SQLiteからバックアップを作成し、`PRAGMA integrity_check`成功|
|Windowsデスクトップビルド|PyInstaller onedirの`Estimate2.exe`と878ファイルの配布ZIPを生成。画面と同じ深緑のアイコンをEXEに埋め込み、ZIPの整合性検査に成功|
|配布EXEの空DB起動|`--smoke-test --database`で終了コード0。Alembic適用、20テーブル、SQLite整合性ok|
|配布EXEの既存DB起動|専用ウィンドウが起動し、既存の1人用DBをログイン入力なしで開けた。画面でアトリエ・見積書等のメニューを確認|
|デスクトップAPIのOrigin検査|同一Originのログイン失敗は401、外部Originは403を確認|
|Windowsインストーラー|Inno Setup 6.7.3で日本語インストーラーを作成。一時フォルダーにサイレントインストールしてEXE起動成功。アンインストール後はプログラムが消え、別保存のSQLiteデータが同一ハッシュで残ることを確認|

統合テストには会社間・課間の認可、承認と差戻し、同時発行、PDF、受注・請求、案件・添付を含む。依存ライブラリ由来の非推奨警告が2件ある。既存のコードには全Ruffルールでスタイル等の指摘が残るため、静的チェックは主要な構文・未定義名のルールに限定した。

外部公開、負荷、バックアップ復元、実取引での運用は未検証。専用ウィンドウ内の全業務操作の手動通し試験は未実施。
