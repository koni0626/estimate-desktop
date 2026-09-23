"""Package a code-free specification bundle for a fresh Codex task."""

from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "deliverables" / "estimate2-spec-for-codex.zip"
SOURCE_DIRS = (ROOT / "docs" / "design", ROOT / "docs" / "manual" / "ja")
ALLOWED_SUFFIXES = {".md", ".json", ".sql"}

files = sorted(
    item
    for directory in SOURCE_DIRS
    for item in directory.rglob("*")
    if item.is_file() and item.suffix in ALLOWED_SUFFIXES
)
files.append(ROOT / "docs" / "desktop.md")
files.append(ROOT / "docs" / "installer.md")
if not files or not any(item.name == "06-codex-rebuild-spec.md" for item in files):
    raise RuntimeError("The Codex implementation specification is missing")

DESTINATION.parent.mkdir(parents=True, exist_ok=True)
manifest = []
with ZipFile(DESTINATION, "w", ZIP_DEFLATED, compresslevel=6) as archive:
    for item in files:
        relative = item.relative_to(ROOT).as_posix()
        content = item.read_bytes()
        archive.writestr(f"estimate2-spec/{relative}", content)
        manifest.append(f"{sha256(content).hexdigest()}  {relative}")
    archive.writestr("estimate2-spec/MANIFEST.sha256", "\n".join(manifest) + "\n")

print(
    f"Created {DESTINATION.name}: {len(files)} specification files, "
    f"{DESTINATION.stat().st_size:,} bytes"
)
