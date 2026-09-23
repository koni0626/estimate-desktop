# 8. Windowsインストーラーの設計

## 8.1 配布物

`scripts/build_desktop.ps1`がPyInstallerのフォルダー型実行版を作り、`scripts/build_installer.ps1`が`installer/EstimateDesktop.iss`をInno Setup 6でコンパイルする。出力は`deliverables/EstimateDesktop-Setup-1.0.0.exe`。インストーラーには`Estimate2.exe`、`_internal`、操作マニュアル、アイコンを含める。SQLiteファイル、`.env`、仮想環境、Node.jsの開発ファイルは含めない。

## 8.2 インストールとデータ分離

ユーザー単位で`%LOCALAPPDATA%\Programs\EstimateDesktop`へ配置し、スタートメニューのショートカットを作る。デスクトップのショートカットは任意。業務データは`%LOCALAPPDATA%\Estimate2\estimate2.sqlite3`に置く。アップデート・アンインストールで業務データとバックアップを削除しない。Windows 10以降の64ビット環境とMicrosoft Edge WebView2 Runtimeが前提で、Runtimeはこのインストーラーに同梱しない。

## 8.3 受入条件

1. インストーラーがコンパイルでき、署名なしの単一EXEになる。
2. 標準ユーザー権限でインストールでき、インストール先からアプリが起動する。
3. スタートメニューのショートカットが作られ、任意のデスクトップショートカットを選択できる。
4. アンインストールでプログラムは消えるが、利用者のSQLiteデータは残る。
5. 実行版から空DBへAlembicが適用され、React画面とAPIが起動する。

開発中の現時点でインストーラーにコード署名は付けていない。商用配布前には署名、配布規約、Inno Setupの[商用利用に関する案内](https://jrsoftware.org/isorder.php)を確認する。
