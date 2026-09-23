# Windowsデスクトップ版の使い方

通常のインストールは[Windowsインストーラー](installer.md)を使う。以下はZIPを展開して直接実行する場合の手順。

## 起動

配布ZIPを展開し、`Estimate2/Estimate2.exe` をダブルクリックする。ブラウザーやDBサーバーの起動は不要。空のDBでは初回に事業者名・自分の名前だけを登録する。次回からはログイン画面なしで開く。既存DBに有効な利用者が1人だけいる場合も自動で開く。複数ユーザーのDBでは従来のログイン画面を表示する。アプリを閉じてもデータは残る。

デスクトップ版はReact画面をWindowsのネイティブウィンドウ（WebView2）に表示し、同じプロセス内でFastAPIを`127.0.0.1`の空きポートに起動する。ポートは毎回変わり、外部インターフェースには待ち受けない。画面のログイン入力は省くが、アプリが起動ごとに生成する秘密値でローカルAPIへの接続を限定する。サーバーはウィンドウを閉じると終了する。WindowsにMicrosoft Edge WebView2 Runtimeが必要。

## データとバックアップ

配布版のSQLiteデータは `%LOCALAPPDATA%\Estimate2\estimate2.sqlite3` に保存され、EXEの更新や配布フォルダーの入れ替えでは消えない。「ファイル → データフォルダーを開く」で保存先を確認できる。「ファイル → データをバックアップ」で同じフォルダーの`backups`に時刻付きの整合したSQLiteコピーを作る。重要なデータはこのバックアップを別の媒体にも保管する。

新しい版でDBの変更が必要な場合、最初の起動時に`backups\estimate2-before-upgrade-*.sqlite3`を自動作成して整合性を確認し、その後でAlembicの更新を適用する。DB変更がない起動時には自動バックアップは作らない。更新に失敗した場合は起動を中止し、画面のエラーと`desktop-error.log`にバックアップ先を示す。

バックアップを復元するときはアプリを終了し、現在のDBを別名に退避してから、バックアップファイルを`estimate2.sqlite3`としてコピーする。DBと同じ場所に`estimate2.sqlite3-wal`や`estimate2.sqlite3-shm`が残っていれば、DBと一緒に別名で退避する。間違ったDBを上書きしないようにファイル名と更新日時を確認する。旧版アプリを使う場合は、その版で作成された更新前バックアップを復元する。`webview`サブフォルダーは画面のブラウザープロファイルで、業務データの正本ではない。

起動できない場合は `%LOCALAPPDATA%\Estimate2\desktop-error.log` を確認する。PDFと案件添付はDBに入るため、DBのバックアップに含まれる。

デスクトップ版はWindowsアカウントにログイン済みの本人が使う前提。共有PCではWindowsアカウントを分け、画面ロックとディスクの保護を使う。新規デスクトップDBの所有者には通常ログイン用パスワードを設定しないため、そのDBをブラウザー版で使うときは追加のアカウント設定が必要になる。

## ソースから起動・ビルド

Python 3.14、Node.js、PowerShellを使う。作業フォルダーで次を実行する。

```powershell
Copy-Item .env.example .env
.\scripts\setup.ps1
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
cd frontend
npm run build
cd ..
.\.venv\Scripts\pythonw.exe desktop.py
```

ソース起動では`.env`の`DATABASE_URL`を使う。配布版と同じDBを明示して試す場合は`desktop.py --database C:\path\to\estimate2.sqlite3`を指定する。`.env`や実データは配布ZIPに含まれない。

EXEの作成は`.\scripts\build_desktop.ps1`。出力は`deliverables\desktop\Estimate2\Estimate2.exe`。フォルダー全体を配布し、EXEだけ抜き出さない。`deliverables\estimate2-windows-desktop.zip`もビルド時に作成する。ビルドはWindows上で実行する。開発時だけ、従来の`start.ps1`によるブラウザー版も使用できる。

## 対象範囲

見積・承認・受注・請求・PDFなどの業務機能はブラウザー版と同じAPIを使う。ローカルの個人利用・小規模チーム利用が対象で、他のPCから接続するサーバーとして公開する仕様ではない。新しいインストーラーの適用は手動で行う。インストーラーとDB更新前の自動バックアップはあるが、コード署名は含まない。
