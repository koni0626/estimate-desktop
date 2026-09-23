"""Download the same allowlisted Markdown files that are bundled in the UI."""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from .db import ROOT
from .security import current_member

router = APIRouter(prefix="/api/manual", dependencies=[Depends(current_member)])
MANUAL = ROOT / "docs" / "manual" / "ja"


@router.get("/{article_id}/download")
def download_article(article_id: str):
    index = json.loads((MANUAL / "index.json").read_text(encoding="utf-8"))
    article = next((a for a in index["items"] if a["id"] == article_id), None)
    if article is None:
        raise HTTPException(404, "記事が見つかりません。")
    return FileResponse(
        MANUAL / article["path"],
        media_type="text/markdown; charset=utf-8",
        filename=article["path"],
    )
