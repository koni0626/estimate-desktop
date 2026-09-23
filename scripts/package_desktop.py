"""Package the built Windows desktop directory, excluding all user data."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "deliverables" / "desktop" / "Estimate2"
DESTINATION = ROOT / "deliverables" / "estimate2-windows-desktop.zip"

if not (APP_DIR / "Estimate2.exe").is_file():
    raise RuntimeError("Run scripts/build_desktop.ps1 first")

files = sorted(path for path in APP_DIR.rglob("*") if path.is_file())
for path in files:
    if path.suffix.lower() in {".sqlite3", ".db"} or path.name == ".env":
        raise RuntimeError(f"User data must not be packaged: {path}")

with ZipFile(DESTINATION, "w", ZIP_DEFLATED, compresslevel=6) as archive:
    for path in files:
        archive.write(path, path.relative_to(APP_DIR.parent).as_posix())

with ZipFile(DESTINATION) as archive:
    if archive.testzip() is not None:
        raise RuntimeError("Desktop ZIP integrity check failed")

print(f"Created {DESTINATION.name}: {len(files)} files, {DESTINATION.stat().st_size:,} bytes")
