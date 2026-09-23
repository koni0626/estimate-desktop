"""Create a source + design distribution without local credentials or build output."""

from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "deliverables" / "estimate2-design-source.zip"
SKIP_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", "node_modules", "dist"}


def tree(path: str):
    directory = ROOT / path
    for item in sorted(directory.rglob("*")):
        if item.is_file() and not any(part in SKIP_PARTS for part in item.relative_to(ROOT).parts):
            yield item


files = [
    ROOT / name
    for name in (
        ".env.example",
        ".gitignore",
        "README.md",
        "alembic.ini",
        "requirements.lock.txt",
        "requirements-migrate.txt",
        "requirements-desktop.txt",
        "desktop.py",
        "desktop-assets/Estimate2.ico",
        "desktop-assets/Estimate2-preview.png",
        "docs/note-sales-page.md",
        "docs/desktop.md",
        "docs/installer.md",
        "installer/EstimateDesktop.iss",
        "frontend/index.html",
        "frontend/package.json",
        "frontend/package-lock.json",
        "frontend/tsconfig.json",
        "frontend/vite.config.ts",
        "frontend/project-dashboard.test.mjs",
    )
]
for directory in (
    "backend",
    "tests",
    "frontend/src",
    "frontend/public",
    "docs/design",
    "docs/manual/ja",
):
    files.extend(tree(directory))
for name in (
    "import_postgres.py",
    "backup.py",
    "prepare_font.py",
    "package_spec.py",
    "package_desktop.py",
    "make_icon.py",
    "build_desktop.ps1",
    "build_installer.ps1",
    "setup.ps1",
    "start.ps1",
    "stop.ps1",
    "package.py",
):
    files.append(ROOT / "scripts" / name)

if len(files) != len(set(files)) or not all(item.is_file() for item in files):
    raise RuntimeError("Distribution file list contains duplicates or missing files")

DESTINATION.parent.mkdir(parents=True, exist_ok=True)
manifest = []
with ZipFile(DESTINATION, "w", ZIP_DEFLATED, compresslevel=6) as archive:
    for item in files:
        relative = item.relative_to(ROOT).as_posix()
        content = item.read_bytes()
        archive.writestr(f"estimate2/{relative}", content)
        manifest.append(f"{sha256(content).hexdigest()}  {relative}")
    archive.writestr("estimate2/MANIFEST.sha256", "\n".join(manifest) + "\n")

print(f"Created {DESTINATION.name}: {len(files)} files, {DESTINATION.stat().st_size:,} bytes")
