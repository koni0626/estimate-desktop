# 5. 検証・運用設計

配布版はWindowsの`Estimate2.exe`を起動します。既定データは`%LOCALAPPDATA%\Estimate2\estimate2.sqlite3`に保存され、アプリの「ファイル → データをバックアップ」で整合したコピーを作れます。[デスクトップ版の操作](../desktop.md)を参照。以下の`start.ps1`と5185/8005はソース開発用ブラウザー版の手順です。

## 5.1 初回セットアップと再現

Windows PowerShellの例。Python 3.14とNode.jsを用意する。SQLiteはPythonに同梱されており、DBサーバーは不要。データファイルは `data/estimate2.sqlite3` に作成される。

```powershell
cd E:\app\estimate-desktop
Copy-Item .env.example .env
.\scripts\setup.ps1
.\scripts\start.ps1
```

画面 `http://127.0.0.1:5185`、API仕様 `http://127.0.0.1:8005/docs`。空DBでは初回セットアップ画面で事業者・最初の管理者を登録する。停止は `.\scripts\stop.ps1`。旧アプリが使う5173/8000と重ならない。デモデータを使う場合のみ、空DBで `setup.ps1 -Demo` を実行する。既存DBには初回セットアップ画面を表示せず、データを保持する。

## 5.2 受入シナリオ

|ID|手順|期待結果|
|---|---|---|
|AT-01|`solo` で見積下書きを作り発行|承認なしで番号・PDFが付き、再取得できる|
|AT-02|`staff` で見積を作り申請、`manager`、`director` の順に承認|途中では発行不可。全承認後に発行可|
|AT-03|承認中に現在担当でない利用者で操作|403または状態競合で拒否|
|AT-04|別会社または別課の見積ID・PDF URLを指定|閲覧・変更・取得不可|
|AT-05|発行済みを改版、会社情報や印鑑を変更|旧PDFは同じ内容で残り、新版だけ下書き|
|AT-06|`0.29 × 50` の明細を作成|明細15円、10%税1円、合計16円|
|AT-07|発行済み見積から受注、請求、入金|元版・金額が保持され、入金状態が更新|
|AT-08|案件へ複数ファイルをドラッグ＆ドロップ|会社・案件権限内で取得、上限超過は拒否|
|AT-09|空DBで初回管理者を登録し、同時に別の登録を試す|一人だけ登録され自動ログイン、二度目は409で拒否|

## 5.3 自動検証

```powershell
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe -m pytest tests -q
cd frontend
npm run build
```

pytest は毎回 `data/` 内に一時SQLiteファイルを作り、全マイグレーションを適用する。通常の `data/estimate2.sqlite3` はテストで書き換えない。詳細な結果はこのディレクトリの `verification-results.md` に記録する。

## 5.4 運用・移行

スキーマ変更時はSQLAlchemyモデルだけを変えず、Alembic revisionを追加し、空DBへの初期化と既存DBからの移行を両方確認する。発行済みPDF、会社印、案件添付はDBファイル内にある。WAL利用中のファイルをそのままコピーせず、`.\.venv\Scripts\python.exe scripts\backup.py` で一貫したコピーを作り、別環境で復元できることを確認する。バックアップは `data/backups/` に作成され、配布ZIPには含まれない。デモデータは実際の会社・取引の代わりに使わない。

このサンプルはローカル動作の根拠を示すもの。インターネット公開前には、デモアカウント削除、ログイン試行制限、公開用の認証・パスワード再設定、HTTPS、Cookie/Origin設定、運用ログ、監視、バックアップ、容量見積、性能・脆弱性試験を追加する。

## 5.5 PostgreSQL版からの一回限りの移行

旧版のデータを使う場合のみ行う。アプリを停止し、旧 `.env` を `data/postgres-source.env` に退避してから、`.env` をSQLite用へ変更する。`data/postgres-source.env` はGit・配布ZIPの対象外であり、パスワードが含まれるため共有しない。

```powershell
.\scripts\stop.ps1
Copy-Item .env data\postgres-source.env
Copy-Item .env.example .env -Force
.\.venv\Scripts\python.exe -m pip install -r requirements-migrate.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\import_postgres.py
.\scripts\start.ps1
```

移行先SQLiteが空でない場合、インポートは中止する。テーブル件数、PDF・印鑑・添付などのバイナリハッシュ、外部キー整合性を照合してから確定する。旧PostgreSQLのDBは削除しない。移行確認後、退避した接続ファイルは利用者自身の秘密情報管理方針に従って扱う。
