"""Run the existing application inside a native Windows WebView2 window.

The development launcher keeps the DATABASE_URL from .env. A frozen build uses
LOCALAPPDATA/Estimate2/estimate2.sqlite3 unless --database is specified.
"""

import argparse
import ctypes
import os
import secrets
import socket
import sqlite3
import sys
import threading
import time
import traceback
from contextlib import closing
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote


APP_NAME = "Estimate2"
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def data_directory() -> Path:
    base = os.getenv("LOCALAPPDATA")
    return (Path(base) if base else Path.home() / "AppData" / "Local") / APP_NAME


def configure_database(database: Path | None) -> Path | None:
    if database is None and getattr(sys, "frozen", False):
        database = data_directory() / "estimate2.sqlite3"
    if database is not None:
        database = database.expanduser().resolve()
        database.parent.mkdir(parents=True, exist_ok=True)
        os.environ["DATABASE_URL"] = f"sqlite:///{database.as_posix()}"
    return database


def backup_database(source: Path, *, before_upgrade: bool = False) -> Path:
    backup_dir = source.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    label = "estimate2-before-upgrade" if before_upgrade else "estimate2"
    target = backup_dir / f"{label}-{datetime.now():%Y%m%d-%H%M%S-%f}.sqlite3"
    try:
        with closing(sqlite3.connect(source)) as current, closing(
            sqlite3.connect(target)
        ) as backup:
            current.backup(backup)
            if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("バックアップの整合性確認に失敗しました。")
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return target


def migrate_database(config, database: Path, engine) -> Path | None:
    """Back up an existing SQLite database before applying pending revisions."""
    from alembic import command
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    existed = database.is_file()
    target_heads = set(ScriptDirectory.from_config(config).get_heads())
    with engine.connect() as connection:
        current_heads = set(MigrationContext.configure(connection).get_current_heads())
    if current_heads == target_heads:
        return None

    backup = backup_database(database, before_upgrade=True) if existed else None
    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            try:
                command.upgrade(config, "head")
            finally:
                config.attributes.pop("connection", None)
    except Exception as exc:
        if backup is not None:
            raise RuntimeError(
                "データベースの更新に失敗しました。アプリを終了し、"
                f"バックアップ {backup} を確認してください。元のエラー: {exc}"
            ) from exc
        raise
    return backup


def prepare_application(database: Path | None):
    configure_database(database)
    os.chdir(BUNDLE_ROOT)
    if not (BUNDLE_ROOT / "frontend" / "dist" / "index.html").is_file():
        raise RuntimeError("Reactのビルドがありません。frontendで npm run build を実行してください。")
    if not (BUNDLE_ROOT / "backend" / "assets" / "NotoSansJP.ttf").is_file():
        raise RuntimeError("日本語PDFフォントがありません。scripts/setup.ps1 を実行してください。")
    from alembic.config import Config
    from backend.app.db import database_path, engine

    migrate_database(Config(str(BUNDLE_ROOT / "alembic.ini")), database_path, engine)
    from backend.app.main import app

    return app


def start_server(app):
    import uvicorn

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    os.environ["ESTIMATE2_DESKTOP_ORIGIN"] = url
    os.environ["ESTIMATE2_DESKTOP_TOKEN"] = secrets.token_urlsafe(40)
    server = uvicorn.Server(
        uvicorn.Config(app, log_level="warning", access_log=False, log_config=None)
    )
    worker = threading.Thread(
        target=server.run, kwargs={"sockets": [listener]}, daemon=True
    )
    worker.start()
    deadline = time.monotonic() + 15
    while not server.started and worker.is_alive() and time.monotonic() < deadline:
        time.sleep(0.05)
    if not server.started:
        server.should_exit = True
        worker.join(timeout=3)
        listener.close()
        raise RuntimeError("アプリ内APIを起動できませんでした。")
    return server, worker, url


def run(database: Path | None, smoke_test: bool) -> None:
    app = prepare_application(database)
    server, worker, url = start_server(app)
    try:
        if smoke_test:
            with urlopen(f"{url}/api/health", timeout=5) as response:
                if response.status != 200:
                    raise RuntimeError("APIヘルスチェックに失敗しました。")
            with urlopen(url, timeout=5) as response:
                if response.status != 200 or b"<html" not in response.read().lower():
                    raise RuntimeError("画面の読み込みに失敗しました。")
            print(f"Desktop smoke test passed: {url}")
            return

        import webview
        from webview.menu import Menu, MenuAction
        from backend.app.db import engine

        current_database = Path(engine.url.database)

        def inform(message: str, error: bool = False) -> None:
            ctypes.windll.user32.MessageBoxW(
                None, message, "見積管理システム", 0x10 if error else 0x40
            )

        def make_backup() -> None:
            try:
                target = backup_database(current_database)
                inform(f"バックアップを保存しました。\n{target}")
            except Exception as exc:
                inform(f"バックアップに失敗しました。\n{exc}", error=True)

        def open_data_folder() -> None:
            os.startfile(current_database.parent)

        profile = data_directory() / "webview"
        profile.mkdir(parents=True, exist_ok=True)
        launch_url = f"{url}/api/desktop/launch?token={quote(os.environ['ESTIMATE2_DESKTOP_TOKEN'])}"
        webview.create_window(
            "見積管理システム",
            launch_url,
            width=1440,
            height=900,
            min_size=(900, 620),
            background_color="#f4f2eb",
            menu=[
                Menu(
                    "ファイル",
                    [
                        MenuAction("データをバックアップ", make_backup),
                        MenuAction("データフォルダーを開く", open_data_folder),
                    ],
                )
            ],
        )
        webview.start(
            gui="edgechromium",
            icon=str(BUNDLE_ROOT / "desktop-assets" / "Estimate2.ico"),
            private_mode=False,
            storage_path=str(profile),
        )
    finally:
        server.should_exit = True
        worker.join(timeout=10)
        from backend.app.db import engine

        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="見積管理システムのデスクトップ版")
    parser.add_argument("--database", type=Path, help="使用するSQLiteファイル")
    parser.add_argument("--smoke-test", action="store_true", help="ウィンドウを開かず起動確認")
    args = parser.parse_args()
    try:
        run(args.database, args.smoke_test)
    except Exception as exc:
        log_dir = data_directory()
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "desktop-error.log").write_text(
            traceback.format_exc(), encoding="utf-8"
        )
        if sys.platform == "win32" and not args.smoke_test:
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, str(exc), "見積管理システム 起動エラー", 0x10)
        else:
            print(f"起動エラー: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
