# Windowsインストーラー

`deliverables/EstimateDesktop-Setup-1.0.1.exe`を実行すると、見積管理システムを現在のWindowsユーザーの`%LOCALAPPDATA%\Programs\EstimateDesktop`にインストールする。管理者権限は不要。スタートメニューにショートカットを作り、デスクトップのショートカットは必要な場合だけ選べる。インストールの最後にアプリを起動できる。

業務データはプログラムとは別の`%LOCALAPPDATA%\Estimate2\estimate2.sqlite3`に保存する。アプリの更新やアンインストールではこのDBを削除しない。削除が必要な場合は、バックアップを確認してから利用者自身が判断する。

同じアプリの新しいインストーラーで更新すると、次の起動時にDBの適用済み版と同梱のAlembicマイグレーションを比較する。更新が必要で既存DBがある場合は、先に`%LOCALAPPDATA%\Estimate2\backups\estimate2-before-upgrade-*.sqlite3`へSQLiteの一貫したコピーを作り、整合性を確認してからマイグレーションを実行する。更新が不要な起動時にはバックアップを増やさない。バックアップ作成やマイグレーションに失敗した場合はアプリの起動を止め、エラーとバックアップ先を表示する。

復元するときはアプリを終了し、[デスクトップ版の使い方](desktop.md)の手順でDBを退避・復元する。古いアプリを再インストールするだけではDBスキーマは戻らない。新しい版を配布する際は`AppId`を維持し、`AppVersion`を上げ、DB変更ごとに新しいAlembicリビジョンを同梱する。

Windows 10以降の64ビット環境とMicrosoft Edge WebView2 Runtimeが必要。現在のインストーラーにWebView2 Runtimeは同梱しない。配布前に対象PCで動作確認する。このインストーラーにはコード署名を付けていない。広く配布する場合は署名も検討する。

## ソースから再ビルド

PowerShellでこのフォルダーのルートに移動し、Python 3.14、Node.js、Inno Setup 6を用意する。

```powershell
.\scripts\setup.ps1
.\scripts\build_desktop.ps1
.\scripts\build_installer.ps1
```

Inno Setupが未導入なら`winget install --id JRSoftware.InnoSetup --exact --scope user`で導入できる。既存のデスクトップ実行版からインストーラーだけ作り直す場合は、最後の`build_installer.ps1`だけを実行する。スクリプトと設定はそれぞれ`scripts/build_installer.ps1`と`installer/EstimateDesktop.iss`。
