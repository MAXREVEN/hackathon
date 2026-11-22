import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .. import ai
from ..config import MAX_AUDIO_BYTES
from ..db import get_db
from ..deps import current_user
from ..models import Summary, User, now_ms

router = APIRouter(prefix="/api", tags=["lost"])
FORMATS = {"paragraph", "roadmap", "spider"}
KEEP = 30   # keep the 30 newest summaries per student (same as the front used to)
MAX_TEXT_CHARS = 20000   # longest message we accept from the page (the ntfy text)


@router.post("/lost")
async def i_am_lost(
    format: str = Form("paragraph"),
    text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """The big button.

    - text  -> the latest ntfy message fetched by the page; saved as real content (not a sample).
    - audio -> Gemini (untested).
    - neither -> sample content (flagged).
    """
    if format not in FORMATS:
        raise HTTPException(422, "format must be paragraph, roadmap or spider")

    text = (text or "").strip()
    is_sample = True
    if text:
        if len(text) > MAX_TEXT_CHARS:
            raise HTTPException(413, "The message is too long")
        content = {"t": (title or "").strip()[:200] or "Latest message", "p": text,
                   "steps": [], "root": "", "nodes": []}
        is_sample = False
    elif audio is not None and audio.filename:
        data = await audio.read(MAX_AUDIO_BYTES + 1)
        if len(data) > MAX_AUDIO_BYTES:
            raise HTTPException(413, "Audio is too large")
        mime = (audio.content_type or "audio/webm").split(";")[0].strip()
        if not mime.startswith("audio/"):
            raise HTTPException(415, "Upload an audio file")
        try:
            content = await ai.gemini_summary(data, mime)
        except ai.AIError as exc:
            raise HTTPException(502, str(exc))
        is_sample = False            # audio is processed in memory and discarded, never stored
    else:
        content = ai.sample_summary()

    item = Summary(user_id=user.id, id=uuid.uuid4().hex[:12], title=content["t"][:200], format=format,
                   created_at=now_ms(), content=json.dumps(content), is_sample=is_sample)
    db.add(item)
    db.commit()

    old = list(db.scalars(select(Summary.id).where(Summary.user_id == user.id)
                          .order_by(Summary.created_at.desc()).offset(KEEP)))
    if old:
        db.execute(delete(Summary).where(Summary.user_id == user.id, Summary.id.in_(old)))
        db.commit()

    return {"id": item.id, "t": item.title, "f": item.format, "d": item.created_at, "c": content, "s": is_sample}
